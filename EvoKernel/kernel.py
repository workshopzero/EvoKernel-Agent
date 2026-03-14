import os
import json
import numpy as np
import uuid
import subprocess
import sys
import shutil
import hashlib
import re
import threading
import psutil
import time
from datetime import datetime
import warnings

# --- 屏蔽 Google Auth 烦人的配额警告 ---
warnings.filterwarnings("ignore", category=UserWarning, module="google.auth")
warnings.filterwarnings("ignore", category=UserWarning, module="vertexai")

from colorama import Fore, Style
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from openai import OpenAI
from config import Config
import colorama
colorama.init(autoreset=True)

class NeuralCore:
    def __init__(self):
        self.lock = threading.RLock()
        self._init_logger()
        self.log("system", "Booting Cognitive Kernel...")
        
        self.state = self._load_state()
        self.prompts = self._load_prompts()
        
        # 初始化双轨制记忆与工作记忆
        self._init_memory()      # Genome (Tools)
        self._init_knowledge()   # Facts (Knowledge)
        self.stm = self._load_stm() # Context (STM)
        
        self._init_models()
        self.print_log("init_core", color=Fore.GREEN)

    def _init_logger(self):
        if not os.path.exists(Config.LOG_FILE):
            with open(Config.LOG_FILE, 'w', encoding='utf-8') as f:
                f.write(f"--- Log Created at {datetime.now()} ---\n")
                
    def log(self, tag, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{tag.upper()}] {message}\n"
        with self.lock:
            try:
                if os.path.exists(Config.LOG_FILE) and os.path.getsize(Config.LOG_FILE) > Config.LOG_MAX_SIZE:
                    self._rotate_logs()
                with open(Config.LOG_FILE, 'a', encoding='utf-8') as f:
                    f.write(entry)
            except: pass

    def _rotate_logs(self):
        for i in range(Config.LOG_BACKUP_COUNT - 1, 0, -1):
            src, dst = f"{Config.LOG_FILE}.{i}", f"{Config.LOG_FILE}.{i+1}"
            if os.path.exists(src):
                try: os.replace(src, dst)
                except: pass
        try: os.replace(Config.LOG_FILE, f"{Config.LOG_FILE}.1")
        except: pass

    def atomic_write(self, filepath, data):
        temp_path = filepath + ".tmp"
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, filepath)
            return True
        except Exception as e:
            self.log("error", f"Atomic write failed: {e}")
            return False

    def get_text(self, key, **kwargs):
        lang = self.prompts.get("active_language", "zh_CN")
        ui_dict = self.prompts.get("templates", {}).get(lang, {}).get("ui", {})
        if not ui_dict and lang != "en_US":
            ui_dict = self.prompts.get("templates", {}).get("en_US", {}).get("ui", {})
        text = ui_dict.get(key, key)
        try: return text.format(**kwargs)
        except: return text

    def print_log(self, key, color=Fore.WHITE, **kwargs):
        msg = self.get_text(key, **kwargs)
        print(f"{color}{msg}{Style.RESET_ALL}")
        self.log("ui", msg)

    def express(self, text):
        """统一感官输出接口 (V1.3)"""
        # 1. 永远执行的基础动作：视觉打印
        print(f"{Fore.CYAN}ECK > {Style.RESET_ALL}{text}")
        
        # 2. 预留的听觉插槽：TTS 异步发声
        if Config.ENABLE_VOICE_MODULE:
            self.log("sensory", "触发语音输出模块 (待挂载 TTS 引擎)")
            # TODO: threading.Thread(target=self._play_audio, args=(text,)).start()

    def _load_prompts(self):
        if os.path.exists(Config.PROMPT_FILE):
            try:
                with open(Config.PROMPT_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {"active_language": "zh_CN", "templates": {"zh_CN": {"ui": {}}}}

    def _get_prompt(self, key, **kwargs):
        lang = self.prompts.get("active_language", "zh_CN")
        template = self.prompts.get("templates", {}).get(lang, {}).get(key, "")
        try: return template.format(**kwargs)
        except: return template

    def _load_state(self):
        # 基础默认值全部由 config.py (.env) 提供，彻底告别硬编码
        default_state = {
            "dynamic_temperature": Config.DEFAULT_TEMPERATURE,
            "local_model_name": Config.LOCAL_MODEL_NAME,
            "google_model_name": Config.GOOGLE_MODEL_NAME,
            "execution_mode": Config.DEFAULT_EXECUTION_MODE
        }
        if os.path.exists(Config.STATE_FILE):
            try:
                with open(Config.STATE_FILE, 'r', encoding='utf-8') as f:
                    # 如果系统运行中途被用户用 /set_xxx 指令修改过，
                    # 那么 system_state.json 里的值会覆盖 .env 的默认值
                    return {**default_state, **json.load(f)}
            except: pass
        return default_state

    def update_state(self, key, value):
        self.state[key] = value
        self.atomic_write(Config.STATE_FILE, self.state)
        return f"State '{key}' updated."

    def _init_models(self):
        try:
            vertexai.init(project=Config.PROJECT_ID, location=Config.LOCATION)
            self.cloud_model = GenerativeModel(self.state.get("google_model_name", Config.GOOGLE_MODEL_NAME))
            self.cloud_ready = True
        except Exception as e:
            self.print_log("init_vertex_fail", e=e, color=Fore.RED)
            self.cloud_ready = False

        try:
            self.local_client = OpenAI(base_url=Config.LOCAL_API_BASE, api_key=Config.LOCAL_API_KEY,timeout=3.0,max_retries=0)
            self.local_client.models.list()
            self.local_ready = True
            self.print_log("init_local_conn", model=self.state.get("local_model_name", Config.LOCAL_MODEL_NAME), color=Fore.CYAN)
        except:
            self.print_log("init_local_fail", color=Fore.YELLOW)
            self.local_ready = False

    def think(self, prompt, system_prompt="", mode="smart"):
        lang_instruction = self._get_prompt("language_instruction")
        full_prompt = f"{system_prompt}{lang_instruction}\n\n{prompt}"
        
        dynamic_temp = self.state.get("dynamic_temperature", Config.DEFAULT_TEMPERATURE)
        execution_mode = self.state.get("execution_mode", "auto")
        allow_routing = Config.ENABLE_DYNAMIC_ROUTING

        if execution_mode == "offline":
            return self.get_text("offline_reject")

        # 1. 硬性模式覆写
        if execution_mode == "cloud": mode = "smart"
        elif execution_mode == "local": mode = "fast"

        # 2. 核心修复：自动降级逻辑 (Failover)
        # 只要开启了允许路由，且没有被强制锁定为 local
        if allow_routing and execution_mode != "local":
            # 如果想用本地，但本地离线了，强制切换给云端！
            if mode == "fast" and not self.local_ready:
                mode = "smart" 
            # 如果想用云端，但云端离线了，强制切换给本地！
            elif mode == "smart" and not self.cloud_ready:
                mode = "fast"

        # 3. 物理执行
        if mode == "fast":
            if not self.local_ready:
                return "CRITICAL: 本地模型离线，且不允许调用云端（可能是隐私锁定或路由已关），请求已拒绝。"
            try:
                resp = self.local_client.chat.completions.create(
                    model=self.state.get("local_model_name", Config.LOCAL_MODEL_NAME),
                    messages=[{"role": "user", "content": full_prompt}],
                    temperature=dynamic_temp
                )
                return resp.choices[0].message.content
            except Exception as e: 
                # 运行时崩溃的二次降级补救
                if allow_routing and execution_mode != "local": 
                    return self.think(prompt, system_prompt, "smart")
                return f"Error: 本地崩溃且禁止路由。报错: {str(e)}"

        if mode == "smart":
            if not self.cloud_ready:
                return "CRITICAL: 云端模型不可用。"
            try:
                resp = self.cloud_model.generate_content(full_prompt, generation_config=GenerationConfig(temperature=dynamic_temp))
                return resp.text
            except Exception as e: 
                return f"Error: 云端崩溃。报错: {str(e)}"
            
        return "CRITICAL: 未知执行模式。"

    def extract_json(self, text):
        """极其暴力的 JSON 提取器 (专治大模型格式幻觉)"""
        try:
            import json
            import re
            
            # 1. 暴力清理所有 Markdown 标记和首尾空白
            text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
            text = re.sub(r'```\s*', '', text)
            text = text.strip()
            
            # 2. 尝试正则匹配最外层的 [] 或 {}
            match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
            if match:
                extracted = match.group(1)
                parsed = json.loads(extracted)
                
                # 我们的 Master Planner 必须返回数组。如果它返回了单个字典，我们强行把它包成数组
                if isinstance(parsed, dict):
                    return [parsed]
                return parsed
            
            # 3. 终极防守：如果连 {} 都没有，但内容里有 opcode，强行拼接！
            if "opcode" in text:
                self.log("warning", f"大模型未输出标准JSON，正尝试强行修复: {text}")
                # 尝试用正则挖出 opcode 和 requirement/content
                op_match = re.search(r'"opcode"\s*:\s*"([^"]+)"', text)
                req_match = re.search(r'"requirement"\s*:\s*"([^"]+)"', text)
                con_match = re.search(r'"content"\s*:\s*"([^"]+)"', text)
                
                if op_match:
                    opcode = op_match.group(1)
                    if "PYTHON_EXEC" in opcode and req_match:
                        return [{"opcode": "PYTHON_EXEC", "requirement": req_match.group(1)}]
                    elif con_match:
                        return [{"opcode": opcode, "content": con_match.group(1)}]
                        
            return None # 彻底没救了
            
        except Exception as e:
            self.log("error", f"JSON提取灾难失败: {str(e)} | 原文: {text}")
            return None

    def extract_code(self, text):
        """最鲁棒的代码提取器 (基于正则表达式)"""
        try:
            import re
            # 匹配 ```python ... ``` 或者 ``` ... ``` 之间的所有内容
            match = re.search(r'```(?:python)?(.*?)```', text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
            # 如果没有找到反引号，说明 LLM 直接输出的纯代码
            return text.strip()
        except Exception:
            return text.strip()
        
    def generate_plan(self, user_input, context_str):
        """总参谋部：将目标拆解为 OpCodes"""
        sys_prompt = self._get_prompt("master_planner", context=context_str, task=user_input)
        
        # 规划任务必须用最聪明的云端大脑 (如果断网则降级)
        raw_response = self.think("生成OpCode计划", sys_prompt, mode="smart")
        plan_array = self.extract_json(raw_response)
        
        # 兜底容错：如果大模型抽风没输出数组，强制转为直接回复
        if not isinstance(plan_array, list):
            return [{"opcode": "DIRECT_REPLY", "content": "抱歉，我的逻辑中枢刚才发生了一点混乱，请重试。"}]
        return plan_array

    # --- 短期记忆控制 (STM) ---
    def _load_stm(self):
        if os.path.exists(Config.STM_FILE):
            try:
                with open(Config.STM_FILE, 'r', encoding='utf-8') as f: return json.load(f)
            except: pass
        return []

    def manage_stm(self, role, content):
        self.stm.append({"role": role, "content": content})
        if len(self.stm) > Config.MAX_STM_ROUNDS * 2:
            self.print_log("stm_compress", color=Fore.MAGENTA)
            recent = self.stm[-4:] 
            to_compress = self.stm[:-4]
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in to_compress])
            
            summary_prompt = self._get_prompt("compressor", history=history_str)
            summary = self.think("执行压缩", summary_prompt, mode="fast")
            
            self.stm = [{"role": "system", "content": f"先前记忆摘要: {summary}"}] + recent
        self.atomic_write(Config.STM_FILE, self.stm)

    def get_stm_context(self):
        return "\n".join([f"{m['role']}: {m['content']}" for m in self.stm])

    # --- 向量核心 ---
    def encode(self, text):
        if not hasattr(self, 'projection'):
            self.dim = 4096
            np.random.seed(42)
            self.projection = np.random.choice([-1, 1], size=(256, self.dim))
        h = hashlib.sha256(text.encode('utf-8')).digest()
        v = np.zeros(self.dim)
        for i, b in enumerate(h):
            if i >= len(self.projection): break
            v += self.projection[b] * (1 if b%2 else -1)
        return np.sign(v)

    # --- 长期记忆 1：语义知识库 ---
    def _init_knowledge(self):
        self.knowledge = {}
        if os.path.exists(Config.KNOWLEDGE_INDEX):
            try:
                with open(Config.KNOWLEDGE_INDEX, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        v['vector'] = np.array(v['vector'])
                        self.knowledge[k] = v
            except: pass

    def save_knowledge(self, concept, raw_text):
        """直接保存知识，0 Token 消耗"""
        file_path = os.path.join(Config.KNOWLEDGE_DIR, f"fact_{uuid.uuid4().hex[:6]}.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {concept}\n\n{raw_text}")
            
        with self.lock:
            key = uuid.uuid4().hex
            self.knowledge[key] = {
                'vector': self.encode(concept + " " + raw_text).tolist(),
                'filepath': file_path,
                'concept': concept,
                'timestamp': str(datetime.now())
            }
            export = {k: {**v, 'vector': list(v['vector'])} for k,v in self.knowledge.items()}
            self.atomic_write(Config.KNOWLEDGE_INDEX, export)
        self.print_log("knowledge_saved", concept=concept, color=Fore.GREEN)

    def recall_knowledge(self, query_text):
        if not self.knowledge: return None, 0.0
        
        best_score, best_item = -1, None
        # 将用户的提问拆分成单字集合 (去掉标点)
        query_chars = set(query_text.replace("？", "").replace("?", "").replace(" ", ""))
        
        for k, v in self.knowledge.items():
            # 1. 传统的向量相似度 (适合长文本精准匹配)
            q_vec = self.encode(query_text)
            sim = np.dot(q_vec, v['vector']) / (np.linalg.norm(q_vec) * np.linalg.norm(v['vector']))
            
            # 2. 文本重合度打分 (适合自然语言模糊查询)
            content = v['concept']
            try:
                with open(v['filepath'], 'r', encoding='utf-8') as f:
                    content += f.read()
            except: pass
            
            content_chars = set(content)
            # 计算提问里的字，有多少出现在了记忆档案里
            overlap = len(query_chars.intersection(content_chars))
            text_score = overlap / len(query_chars) if query_chars else 0
            
            # 综合打分：取两者最高值
            final_score = max(sim, text_score)
            
            if final_score > best_score: 
                best_score, best_item = final_score, v
        
        # 只要相似度大于 0.25 (门槛降低)，就认为成功唤起记忆
        if best_score > 0.25 and best_item:
            self.print_log("knowledge_recall", concept=best_item['concept'], color=Fore.CYAN)
            try:
                with open(best_item['filepath'], 'r', encoding='utf-8') as f:
                    return f.read(), best_score
            except: pass
        return None, best_score

    # --- 长期记忆 2：程序技能库 ---
    def _init_memory(self):
        self.memory = {}
        if os.path.exists(Config.MEMORY_FILE):
            try:
                with open(Config.MEMORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        v['vector'] = np.array(v['vector'])
                        self.memory[k] = v
            except: pass

    def recall_skill(self, text):
        if not self.memory: return None, 0.0
        q_vec = self.encode(text)
        best_sim, best_item = -1, None
        for k, v in self.memory.items():
            sim = np.dot(q_vec, v['vector']) / (np.linalg.norm(q_vec) * np.linalg.norm(v['vector']))
            if sim > best_sim: best_sim, best_item = sim, v
        return best_item, best_sim

    def save_skill(self, task, path):
        with self.lock:
            key = uuid.uuid4().hex
            self.memory[key] = {
                'vector': self.encode(task).tolist(),
                'filepath': path,
                'description': task,
                'timestamp': str(datetime.now())
            }
            export = {k: {**v, 'vector': list(v['vector'])} for k,v in self.memory.items()}
            self.atomic_write(Config.MEMORY_FILE, export)

    def evolve_tool(self, task, feedback="", is_pending=False):
        self.print_log("evo_start", task=task, color=Fore.YELLOW)
        sys_prompt = self._get_prompt("evolution")
        raw_response = self.think(f"Task: {task}\nErr: {feedback}", sys_prompt, mode="smart")
        code = self.extract_code(raw_response)
        
        # 判断是存入正式库还是隔离区
        target_dir = Config.PENDING_DIR if is_pending else Config.GENOME_DIR
        path = os.path.join(target_dir, f"gene_{uuid.uuid4().hex[:6]}.py")
        
        with open(path, 'w', encoding='utf-8') as f: f.write(code)
        return path
    
    def _ast_security_check(self, code):
        """AST 抽象语法树安全扫描"""
        import ast
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        # 黑名单函数
                        if node.func.attr in ['remove', 'rmtree', 'system', 'Popen']:
                            return False, f"AST拦截: 检测到危险调用 {node.func.attr}"
                    elif isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec']:
                            return False, f"AST拦截: 检测到危险执行 {node.func.id}"
            return True, "AST检查通过"
        except SyntaxError as e:
            return False, f"AST拦截: 语法错误 {str(e)}"
    
    def run_script(self, path):
        """带有死循环与资源癌变监控的终极物理沙盒"""
        import subprocess, psutil, time
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            # 启动子进程
            proc = subprocess.Popen([sys.executable, path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, encoding='utf-8')
            
            try:
                p_obj = psutil.Process(proc.pid)
            except psutil.NoSuchProcess:
                p_obj = None

            start_time = time.time()
            last_output_time = time.time()
            max_silence_seconds = 15  # I/O 沉默断言：15秒不输出且CPU拉满，判定为死循环
            max_memory_mb = 500       # 内存癌变红线：500MB
            
            while proc.poll() is None:
                time.sleep(0.5)
                # 1. 检查总超时 (硬兜底 120 秒)
                if time.time() - start_time > 120:
                    proc.kill()
                    return False, "监控拦截: 任务执行超过120秒，已被强制终止。"
                
                if p_obj:
                    try:
                        # 2. 内存癌变监控
                        mem_mb = p_obj.memory_info().rss / (1024 * 1024)
                        if mem_mb > max_memory_mb:
                            proc.kill()
                            return False, f"监控拦截: 内存泄漏！飙升至 {mem_mb:.1f} MB，已被击杀。"
                        
                        # 3. 死循环沉默监控 (CPU高但无输出)
                        cpu_percent = p_obj.cpu_percent(interval=0.1)
                        if cpu_percent > 80.0 and (time.time() - last_output_time) > max_silence_seconds:
                            proc.kill()
                            return False, "监控拦截: I/O 沉默且 CPU 满载，判定为逻辑死循环，已被击杀。"
                    except psutil.NoSuchProcess:
                        break

            out, err = proc.communicate()
            if out: last_output_time = time.time() # 伪更新，证明有输出
            
            res_text = out + err
            return proc.returncode == 0, res_text
        except Exception as e: 
            return False, f"沙盒灾难崩溃: {str(e)}"

    # --- 保留高阶能力：自我修改 ---
    def modify_self(self, instruction):
        if not Config.ALLOW_SELF_MOD: return "Disabled."
        self.print_log("self_mod_start", color=Fore.MAGENTA)
        try:
            with open("kernel.py",'r',encoding='utf-8') as f: src = f.read()
        except: src=""
        sys_prompt = self._get_prompt("modifier", instruction=instruction, code_len=len(src))
        
        raw_response = self.think(f"Source:\n{src}\n\nReq: {instruction}", sys_prompt, mode="smart")
        new_code = self.extract_code(raw_response)
        
        if not new_code: return "Modification failed."
        with open("kernel_candidate.py",'w',encoding='utf-8') as f: f.write(new_code)
            
        res = subprocess.run([sys.executable, "integrity_check.py"], capture_output=True)
        if res.returncode == 0:
            shutil.copy("kernel.py", os.path.join(Config.BACKUP_DIR, f"bk_{datetime.now().strftime('%Y%m%d%H%M')}.py"))
            shutil.move("kernel_candidate.py", "kernel.py")
            if os.path.exists("integrity_check.py"): os.remove("integrity_check.py")
            return "Success. RESTART REQUIRED."
        return f"Check Failed: {res.stderr}"

    def auto_translate_ui(self, target_lang):
        """自动繁衍新语言包"""
        self.print_log("system", f"检测到新语言 {target_lang}，正在进行系统底层基因重写...")
        source_json = json.dumps(self.prompts['templates']['en_US'], ensure_ascii=False)
        sys_prompt = self._get_prompt("translator", target_lang=target_lang, source_json=source_json)
        
        # 翻译必须用高智商云端模型
        raw_res = self.think("开始翻译", sys_prompt, mode="smart")
        new_lang_dict = self.extract_json(raw_res)
        
        if isinstance(new_lang_dict, dict) and "ui" in new_lang_dict:
            self.prompts['templates'][target_lang] = new_lang_dict
            self.prompts['active_language'] = target_lang
            self.atomic_write(Config.PROMPT_FILE, self.prompts)
            self.express("UI 本地化重写完成。")

    def _init_schemas(self):
        self.schemas = {}
        if os.path.exists(Config.SCHEMA_FILE):
            try:
                with open(Config.SCHEMA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        v['vector'] = np.array(v['vector'])
                        self.schemas[k] = v
            except: pass

    def recall_schema(self, task):
        """肌肉记忆检索"""
        if not hasattr(self, 'schemas'): self._init_schemas()
        if not self.schemas: return None, 0.0
        q_vec = self.encode(task)
        best_sim, best_item = -1, None
        for k, v in self.schemas.items():
            sim = np.dot(q_vec, v['vector']) / (np.linalg.norm(q_vec) * np.linalg.norm(v['vector']))
            if sim > best_sim: best_sim, best_item = sim, v
        return best_item, best_sim

    def save_schema(self, task, plan):
        """认知内化：将成功计划抽象保存"""
        sys_prompt = self._get_prompt("schema_extractor", task=task, plan=json.dumps(plan, ensure_ascii=False))
        abs_json = self.extract_json(self.think("提炼范式", sys_prompt, mode="smart"))
        if not abs_json: return
        
        with self.lock:
            if not hasattr(self, 'schemas'): self._init_schemas()
            key = uuid.uuid4().hex
            self.schemas[key] = {
                'vector': self.encode(abs_json.get('abstract_intent', task)).tolist(),
                'plan': abs_json.get('abstract_plan', plan),
                'timestamp': str(datetime.now())
            }
            export = {k: {**v, 'vector': list(v['vector'])} for k,v in self.schemas.items()}
            self.atomic_write(Config.SCHEMA_FILE, export)

    def check_subconscious_gates(self):
        """检查潜意识三级门控"""
        sched = Config.SUBCONSCIOUS_SCHEDULE
        if sched == "OFF": return False
        
        # 第二道门：资源门
        if psutil.cpu_percent(interval=0.5) > Config.MAX_BACKGROUND_CPU_PERCENT:
            return False
            
        # 第一道门：作息门
        if sched != "ALWAYS":
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            allowed = False
            for period in sched.split(','):
                start, end = period.split('-')
                if start <= current_time <= end:
                    allowed = True; break
            if not allowed: return False
            
        return True

    def subconscious_dream(self):
        """潜意识做梦与突变引擎"""
        import random
        focus = self.state.get("focus_area", "")
        skills = [v.get('description', '') for v in self.memory.values()]
        skill_sample = random.sample(skills, min(len(skills), 3)) if skills else ["无"]
        
        if focus and focus.lower() != "general":
            self.log("subconscious", f"启动主动定向学习，核心: {focus}")
            sys_prompt = self._get_prompt("dream_active", focus=focus, skills=", ".join(skill_sample))
        else:
            self.log("subconscious", "无核心目标，启动被动基因突变...")
            concepts = [v.get('concept', '') for v in self.knowledge.values()]
            concept_sample = random.sample(concepts, min(len(concepts), 2)) if concepts else ["基础逻辑"]
            sys_prompt = self._get_prompt("dream_passive", concepts=", ".join(concept_sample), skills=", ".join(skill_sample))
            
        new_task = self.think("生成任务", sys_prompt, mode="smart").strip()
        
        # --- 核心修复：检测到严重网络错误，直接放弃本次做梦，回去接着睡 ---
        if "CRITICAL:" in new_task or "Error:" in new_task:
            self.log("subconscious", f"系统脑死亡或断网，放弃做梦。报错: {new_task}")
            return
            
        self.log("subconscious", f"构思出新任务: {new_task}")
        
        feedback = ""
        for i in range(3):
            path = self.evolve_tool(new_task, feedback, is_pending=True)
            with open(path, 'r', encoding='utf-8') as f: code = f.read()
            ast_ok, ast_msg = self._ast_security_check(code)
            if not ast_ok:
                feedback = ast_msg; continue
                
            success, output = self.run_script(path)
            if success:
                self.log("subconscious", f"突变成功！已放入隔离区: {path}")
                break
            else:
                feedback = output
