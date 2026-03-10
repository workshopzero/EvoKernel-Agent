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
            self.local_client = OpenAI(base_url=Config.LOCAL_API_BASE, api_key=Config.LOCAL_API_KEY)
            self.local_client.models.list()
            self.local_ready = True
            self.print_log("init_local_conn", model=self.state.get("local_model_name", Config.LOCAL_MODEL_NAME), color=Fore.CYAN)
        except:
            self.print_log("init_local_fail", color=Fore.YELLOW)
            self.local_ready = False

    def think(self, prompt, system_prompt="", mode="smart"):
        lang_instruction = self._get_prompt("language_instruction")
        full_prompt = f"{system_prompt}{lang_instruction}\n\n{prompt}"
        
        # --- 状态读取 ---
        # 优先读取系统自己进化出的动态性格，如果没有，则读取 .env 赋予的出厂设定
        dynamic_temp = self.state.get("dynamic_temperature", Config.DEFAULT_TEMPERATURE)
        execution_mode = self.state.get("execution_mode", Config.DEFAULT_EXECUTION_MODE)

        # --- 1. 运行模式覆写层 ---
        if execution_mode == "cloud":
            mode = "smart"  # 强制使用云端
        elif execution_mode == "local":
            mode = "fast"   # 强制使用本地，切断外网
        elif execution_mode == "auto":
            # 智能降级逻辑：想用本地，但本地断网，平滑切换给云端
            if mode == "fast" and not self.local_ready:
                mode = "smart"

        # --- 2. 物理执行层: Local (本地小模型) ---
        if mode == "fast":
            if not self.local_ready:
                return "CRITICAL: 强制使用本地模型，但本地离线，已拒绝请求以保障隐私。"
            try:
                resp = self.local_client.chat.completions.create(
                    model=self.state.get("local_model_name", Config.LOCAL_MODEL_NAME),
                    messages=[{"role": "user", "content": full_prompt}],
                    temperature=dynamic_temp
                )
                return resp.choices[0].message.content
            except Exception as e: 
                # 只有在 auto 模式下本地崩溃，才允许偷偷转移给云端
                if execution_mode == "auto":
                    mode = "smart" 
                else:
                    return f"Error: 本地模型执行失败，报错: {str(e)}"

        # --- 3. 物理执行层: Cloud (云端大模型) ---
        if mode == "smart":
            if not self.cloud_ready:
                return "CRITICAL: 云端模型不可用，且没有本地模型可降级。"
            try:
                resp = self.cloud_model.generate_content(
                    full_prompt,
                    generation_config=GenerationConfig(temperature=dynamic_temp)
                )
                return resp.text
            except Exception as e: 
                return f"Error: 云端模型执行失败。报错: {str(e)}"
                
        return "CRITICAL: 没有匹配的模型执行该任务。"

    def extract_json(self, text):
        """最无敌的 JSON 提取器：物理截取大括号"""
        try:
            import json
            # 找到第一个左大括号和最后一个右大括号的位置
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                json_str = text[start:end+1]
                return json.loads(json_str)
        except Exception as e:
            self.log("error", f"JSON提取失败: {str(e)} | 原文: {text}")
        
        return {} 

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
        
    # --- 认知中枢：意图路由 ---
    def evaluate_intent(self, user_input):
        context_str = "\n".join([f"{m['role']}: {m['content']}" for m in self.stm])
        sys_prompt = self._get_prompt("router", context=context_str, input=user_input)
        
        raw_response = self.think(user_input, sys_prompt, mode="fast")
        intent_data = self.extract_json(raw_response)
        
        if not intent_data or "intent" not in intent_data:
            return {"intent": "chat", "parameters": {}}
        return intent_data

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

    def save_knowledge(self, raw_text):
        prompt = self._get_prompt("extractor", input=raw_text)
        raw_json = self.think("执行知识提取", prompt, mode="fast")
        data = self.extract_json(raw_json)
        
        concept = data.get("concept", "Unnamed Fact")
        desc = data.get("description", raw_text)
        
        file_path = os.path.join(Config.KNOWLEDGE_DIR, f"fact_{uuid.uuid4().hex[:6]}.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {concept}\n\n{desc}")
            
        with self.lock:
            key = uuid.uuid4().hex
            self.knowledge[key] = {
                'vector': self.encode(concept + " " + desc).tolist(),
                'filepath': file_path,
                'concept': concept,
                'timestamp': str(datetime.now())
            }
            export = {k: {**v, 'vector': v['vector']} for k,v in self.knowledge.items()}
            self.atomic_write(Config.KNOWLEDGE_INDEX, export)
        self.print_log("knowledge_saved", concept=concept, color=Fore.GREEN)
        return concept

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
            export = {k: {**v, 'vector': v['vector']} for k,v in self.memory.items()}
            self.atomic_write(Config.MEMORY_FILE, export)

    def evolve_tool(self, task, feedback=""):
        self.print_log("evo_start", task=task, color=Fore.YELLOW)
        sys_prompt = self._get_prompt("evolution")
        raw_response = self.think(f"Task: {task}\nErr: {feedback}", sys_prompt, mode="smart")
        code = self.extract_code(raw_response)
        
        path = os.path.join(Config.GENOME_DIR, f"gene_{uuid.uuid4().hex[:6]}.py")
        with open(path, 'w', encoding='utf-8') as f: f.write(code)
        return path

    def run_script(self, path):
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            res = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=60, env=env, encoding='utf-8')
            return res.returncode == 0, res.stdout + res.stderr
        except Exception as e: 
            return False, str(e)

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
        
        if not os.path.exists("integrity_check.py"):
            with open("integrity_check.py","w") as f: f.write("try:\n from kernel_candidate import NeuralCore\n print('OK')\nexcept: exit(1)")
            
        res = subprocess.run([sys.executable, "integrity_check.py"], capture_output=True)
        if res.returncode == 0:
            shutil.copy("kernel.py", os.path.join(Config.BACKUP_DIR, f"bk_{datetime.now().strftime('%Y%m%d%H%M')}.py"))
            shutil.move("kernel_candidate.py", "kernel.py")
            if os.path.exists("integrity_check.py"): os.remove("integrity_check.py")
            return "Success. RESTART REQUIRED."
        return f"Check Failed: {res.stderr}"
