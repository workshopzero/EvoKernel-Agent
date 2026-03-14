import sys
import re
from kernel import NeuralCore
from colorama import Fore, Style
from config import Config
import threading
import time
import math
import os
import colorama

colorama.init(autoreset=True)

last_active_time = time.time()
idle_intervals = [60, 60, 60]  # 默认初始间隔（秒）

def background_worker(brain):
    """潜意识守护线程"""
    global last_active_time, idle_intervals
    while True:
        time.sleep(10) # 每10秒偷看一次
        
        # 1. 动态计算统计学阈值 (Mean + 2σ)
        mean_idle = sum(idle_intervals) / len(idle_intervals)
        variance = sum((x - mean_idle) ** 2 for x in idle_intervals) / len(idle_intervals)
        std_dev = math.sqrt(variance)
        dynamic_threshold = mean_idle + (2 * std_dev)
        dynamic_threshold = max(60, min(dynamic_threshold, 1800)) # 强制限幅在 1分钟到30分钟间
        
        current_idle = time.time() - last_active_time
        
        if current_idle > dynamic_threshold:
            if brain.check_subconscious_gates():
                # 通过了三级大门，开始做梦！
                brain.subconscious_dream()
                # 做完一次梦，强制睡一会，防止榨干电脑
                time.sleep(300) 

def main():
    brain = NeuralCore()
    
    bg_thread = threading.Thread(target=background_worker, args=(brain,), daemon=True)
    bg_thread.start()
    
    # ==========================================
    # 动态生成横幅与状态
    # ==========================================
    active_models = []
    if brain.cloud_ready: 
        active_models.append(f"{brain.get_text('banner_cloud')}: {brain.state.get('google_model_name')}")
    if brain.local_ready: 
        active_models.append(f"{brain.get_text('banner_local')}: {brain.state.get('local_model_name')}")
    model_display = " | ".join(active_models) if active_models else f"{brain.get_text('banner_offline')}"
    
    req_human = brain.state.get("require_human", Config.REQUIRE_HUMAN_CONFIRMATION)
    ena_refl = brain.state.get("enable_reflection", Config.ENABLE_INTERNAL_REFLECTION)
    human_status = f"{Fore.GREEN}ON{Style.RESET_ALL}" if req_human else f"{Fore.RED}OFF{Style.RESET_ALL}"
    refl_status = f"{Fore.GREEN}ON{Style.RESET_ALL}" if ena_refl else f"{Fore.RED}OFF{Style.RESET_ALL}"

    print(f"{Fore.MAGENTA}=========================================={Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}   Evo-Cognition Kernel (ECK) V1.1        {Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}   {brain.get_text('banner_title')} {Style.RESET_ALL}")
    print(f"{Fore.CYAN}   [{brain.get_text('banner_active')}] {model_display}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}   [{brain.get_text('banner_lang')}] {brain.prompts.get('active_language')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}   [{brain.get_text('banner_security')}] {brain.get_text('human_auth')}: {human_status} | {brain.get_text('geek_reflect')}: {refl_status}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}=========================================={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{brain.get_text('menu_title')}:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}/set_model <模型名>{Style.RESET_ALL} - {brain.get_text('cmd_model')}")
    print(f"  {Fore.GREEN}/set_temp <0.0-1.0>{Style.RESET_ALL} - {brain.get_text('cmd_temp')}")
    print(f"  {Fore.GREEN}/set_mode <auto|local|cloud|offline>{Style.RESET_ALL} - {brain.get_text('cmd_mode')}")
    print(f"  {Fore.GREEN}/set_lang <代码>{Style.RESET_ALL} - {brain.get_text('cmd_lang')}")
    print(f"  {Fore.GREEN}/set_focus <领域>{Style.RESET_ALL} - {brain.get_text('cmd_focus')}")
    print(f"  {Fore.GREEN}/toggle_cloud <on|off>{Style.RESET_ALL} - 物理切断/恢复云端大模型连接") 
    print(f"  {Fore.GREEN}/toggle_human <on|off>{Style.RESET_ALL} - {brain.get_text('cmd_human')}")
    print(f"  {Fore.GREEN}/toggle_reflect <on|off>{Style.RESET_ALL} - {brain.get_text('cmd_reflect')}")
    print(f"  {Fore.GREEN}/review{Style.RESET_ALL} - {brain.get_text('cmd_review')}")
    print(f"  {Fore.GREEN}/update <需求>{Style.RESET_ALL} - {brain.get_text('cmd_update')}")
    print(f"  {Fore.GREEN}exit 或 quit{Style.RESET_ALL} - {brain.get_text('cmd_exit')}")
    print(f"{Fore.MAGENTA}=========================================={Style.RESET_ALL}")
    
    while True:
        try:
            global last_active_time, idle_intervals
            user_input = input(f"\n{Fore.BLUE}Command > {Style.RESET_ALL}").strip()
            pause_time = time.time() - last_active_time
            if pause_time > 5 and pause_time < 3600: # 剔除乱敲和真睡着的极端数据
                idle_intervals.append(pause_time)
                if len(idle_intervals) > 20: idle_intervals.pop(0) # 只记最近20次
            
            last_active_time = time.time()
            if not user_input: continue
            if user_input.lower() in ['exit', 'quit']: break
            
            # ==========================================
            # 显式指令拦截
            # ==========================================
            if user_input.startswith("/set_mode "):
                mode_val = user_input.replace("/set_mode ", "").strip().lower()
                if mode_val in ["auto", "local", "cloud", "offline"]:
                    print(f"{Fore.GREEN}{brain.update_state('execution_mode', mode_val)}{Style.RESET_ALL}")
                else: 
                    print(f"{Fore.RED}错误: 模式只能是 auto, local, cloud 或 offline。{Style.RESET_ALL}")
                continue
            
            if user_input.startswith("/set_model "):
                model_name = user_input.replace("/set_model ", "").strip()
                print(f"{Fore.GREEN}{brain.update_state('local_model_name', model_name)}{Style.RESET_ALL}")
                continue
                
            if user_input.startswith("/set_focus "):
                focus = user_input.replace("/set_focus ", "").strip()
                print(f"{Fore.GREEN}{brain.update_state('focus_area', focus)}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}潜意识定向学习目标已锁定为: {}{Style.RESET_ALL}")
                continue
            
            if user_input.startswith("/set_temp "):
                try:
                    val = float(user_input.replace("/set_temp ", "").strip())
                    print(f"{Fore.GREEN}{brain.update_state('dynamic_temperature', val)}{Style.RESET_ALL}")
                except: pass
                continue
            
            if user_input.startswith("/toggle_human "):
                val = user_input.replace("/toggle_human ", "").strip().lower() == "on"
                print(f"{Fore.GREEN}{brain.update_state('require_human', val)}{Style.RESET_ALL}")
                continue
            
            if user_input.startswith("/toggle_cloud "):
                val = user_input.replace("/toggle_cloud ", "").strip().lower()
                if val in ["on", "off"]:
                    is_on = (val == "on")
                    brain.cloud_ready = is_on 
                    status_text = "云端网络已重新连接。" if is_on else "云端网络已被物理切断（Air-gapped）。"
                    print(f"{Fore.GREEN}{status_text}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}错误: 只能输入 on 或 off。{Style.RESET_ALL}")
                continue
            
            if user_input.startswith("/toggle_reflect "):
                val = user_input.replace("/toggle_reflect ", "").strip().lower() == "on"
                print(f"{Fore.GREEN}{brain.update_state('enable_reflection', val)}{Style.RESET_ALL}")
                continue
            
            if user_input.startswith("/set_lang "):
                lang_code = user_input.replace("/set_lang ", "").strip()
                brain.update_state("lang_locked", True) # 锁死语言
                brain.auto_translate_ui(lang_code)
                continue
            
            if user_input.startswith("/update "):
                res = brain.modify_self(user_input.replace("/update ", ""))
                print(res)
                if "RESTART REQUIRED" in res: sys.exit(1)
                continue
            
            if user_input == "/review":
                import glob
                pending_files = glob.glob(os.path.join(Config.PENDING_DIR, "*.py"))
                if not pending_files:
                    print(f"{Fore.YELLOW}隔离区暂无待审批的潜意识技能。{Style.RESET_ALL}")
                    continue
                for pf in pending_files:
                    print(f"\n{Fore.MAGENTA}待审批技能: {pf}{Style.RESET_ALL}")
                    with open(pf, 'r', encoding='utf-8') as f: print(f.read())
                    ans = input(f"{Fore.YELLOW}是否批准此技能并入主脑？[y/n]: {Style.RESET_ALL}").strip()
                    if ans.lower() == 'y':
                        # 批准后，转移到主基因库并保存
                        new_path = pf.replace(Config.PENDING_DIR, Config.GENOME_DIR)
                        os.rename(pf, new_path)
                        brain.save_skill("由潜意识自主发明的技能", new_path)
                        print(f"{Fore.GREEN}技能已成功转正！{Style.RESET_ALL}")
                    else:
                        os.remove(pf)
                        print(f"{Fore.RED}已将该突变基因销毁。{Style.RESET_ALL}")
                continue
            
            # ==========================================
            # 预处理：多模态雷达与惰性语言检测
            # ==========================================
            path_pattern = r'([a-zA-Z]:\\[^\s"<>|]+|/[^\s"<>|]+)'
            media_paths = re.findall(path_pattern, user_input)
            clean_input = re.sub(path_pattern, '', user_input).strip()
            if media_paths and not clean_input: 
                clean_input = "请读取并分析我提供的文件。"
                
            if media_paths:
                print(f"{Fore.MAGENTA}[多模态雷达] 捕获本地文件: {media_paths}{Style.RESET_ALL}")
                clean_input += f"\n[附带文件路径]: {', '.join(media_paths)}"
            
            brain.manage_stm("user", clean_input)

            context = brain.get_stm_context()
            plan = brain.generate_plan(clean_input, context)
            
            ena_refl = brain.state.get("enable_reflection", Config.ENABLE_INTERNAL_REFLECTION)
            use_mode = "smart" if Config.ENABLE_DYNAMIC_ROUTING else "fast"
            
            for step in plan:
                opcode = step.get("opcode", "")
                
                # ------------------------------------
                # 分支 1：直接回复 (闲聊/答疑)
                # ------------------------------------
                if opcode == "DIRECT_REPLY":
                    reply = step.get("content", "我明白了。")
                    brain.express(reply)
                    brain.manage_stm("assistant", reply)

                # ------------------------------------
                # 分支 2：刻入记忆 (设定/知识)
                # ------------------------------------
                elif opcode == "SAVE_MEMORY":
                    concept = step.get("concept", "未命名概念")
                    brain.save_knowledge(concept, clean_input)
                    reply = f"💾 已将记忆刻入底层架构：{concept}"
                    brain.express(reply)
                    brain.manage_stm("assistant", reply)

                # ------------------------------------
                # 分支 3：检索记忆 (回忆)
                # ------------------------------------
                elif opcode == "QUERY_MEMORY":
                    keyword = step.get("keyword", clean_input)
                    fact_text, sim = brain.recall_knowledge(keyword)
                    
                    if fact_text and sim > 0.25:
                        prompt = f"【最高指令】请根据以下绝对真实的档案回答问题。\n[档案]：\n{fact_text}\n[提问]：{clean_input}"
                        reply = brain.think(prompt, mode=use_mode)
                    else:
                        reply = brain.think(f"记忆库中无相关记录，请以你的常识回答：{clean_input}", mode=use_mode)
                        
                    brain.express(reply)
                    brain.manage_stm("assistant", reply)

                # ------------------------------------
                # 分支 4：操作系统与环境交互 (极客执行)
                # ------------------------------------
                elif opcode == "PYTHON_EXEC":
                    req = step.get("requirement", clean_input)
                    brain.express(f"▶️ 正在执行核心任务: {req}")

                    # === 1. 尝试唤醒肌肉记忆 (Schema) ===
                    schema, schema_conf = brain.recall_schema(req)
                    if schema and schema_conf > 0.85:
                        brain.express("⚡ 触发内化肌肉记忆，按既定范式执行...")
                        sub_plan = schema['plan']
                    else:
                        sub_plan = [{"step": 1, "action": req}]

                    ena_refl = brain.state.get("enable_reflection", Config.ENABLE_INTERNAL_REFLECTION)
                    max_logic = 2 if ena_refl else 1  # 逻辑验收重试次数
                    max_run = 3 if ena_refl else 1    # 物理报错重写次数

                    overall_success = False
                    final_output = ""

                    # === 外层循环：逻辑层验收（批评家验证） ===
                    for logic_attempt in range(max_logic):
                        final_output = ""
                        physical_success = True  # 标记整个动作链是否顺畅

                        # 遍历任务步骤
                        for sub_step in sub_plan:
                            action = sub_step.get('action', req)
                            # 初始生成代码
                            current_path = brain.evolve_tool(f"目标：{action}\n", "")

                            # === 内层循环：物理层沙盒执行（代码报错自愈） ===
                            for run_try in range(max_run):
                                with open(current_path, 'r', encoding='utf-8') as f: 
                                    gen_code = f.read()

                                # A. AST 语法与安全拦截
                                ast_ok, ast_msg = brain._ast_security_check(gen_code)
                                if not ast_ok:
                                    print(f"{Fore.RED}[安全拦截] {ast_msg}{Style.RESET_ALL}")
                                    if ena_refl and run_try < max_run - 1:
                                        print(f"{Fore.YELLOW}触发极客反思，正在重写以绕过安全策略...{Style.RESET_ALL}")
                                        current_path = brain.evolve_tool(action, f"被安全系统拦截，原因:\n{ast_msg}\n请换一种安全的方法实现。")
                                        continue
                                    else:
                                        physical_success = False
                                        break # 物理执行绝望，跳出物理重试

                                # B. 人工确权
                                if brain.state.get("require_human", Config.REQUIRE_HUMAN_CONFIRMATION):
                                    print(f"\n{Fore.MAGENTA}=== [安全确权] ==={Style.RESET_ALL}\n{gen_code}\n{Fore.MAGENTA}==============={Style.RESET_ALL}")
                                    ans = input(f"{Fore.YELLOW}执行该代码？[y/n]: {Style.RESET_ALL}").strip()
                                    if ans.lower() != 'y': 
                                        physical_success = False
                                        break # 人类拒绝，掐断

                                # C. 丢入沙盒执行
                                success, output = brain.run_script(current_path)
                                if success:
                                    final_output += f"步骤[{action}]成功:\n{output}\n"
                                    brain.save_skill(action, current_path)
                                    break # 物理执行成功，跳出物理重试
                                else:
                                    print(f"{Fore.RED}[执行报错] {output}{Style.RESET_ALL}")
                                    
                                    # 静默安装缺失库的特殊逻辑
                                    if "ModuleNotFoundError" in output:
                                        missing_lib = re.search(r"No module named '([^']+)'", output)
                                        if missing_lib:
                                            lib_name = missing_lib.group(1)
                                            print(f"{Fore.YELLOW}🔧 发现缺失库 '{lib_name}'，自动静默安装...{Style.RESET_ALL}")
                                            subprocess.run([sys.executable, "-m", "pip", "install", lib_name], capture_output=True)
                                            continue 
                                    
                                    if ena_refl and run_try < max_run - 1:
                                        print(f"{Fore.YELLOW}触发极客反思，正在分析报错并修复代码...{Style.RESET_ALL}")
                                        current_path = brain.evolve_tool(action, f"运行报错了，请修复代码并返回完整新代码:\n{output}")
                                    else:
                                        physical_success = False
                                        break # 物理报错绝望

                            # 如果中间某个步骤物理层垮了，直接中断动作链
                            if not physical_success:
                                break

                        # ==========================================
                        # 内层循环结束，准备进入批评家验收阶段
                        # ==========================================
                        if not physical_success:
                            brain.express("物理链路中断或代码无可救药，任务终止。")
                            overall_success = False
                            break # 彻底跳出大循环

                        # 物理层跑通了，给批评家看
                        critic_prompt = brain._get_prompt("critic", task=req, output=final_output)
                        eval_res = brain.think("评估结果", critic_prompt, mode=use_mode).strip()

                        if "SUCCESS" in eval_res.upper():
                            brain.express(f"✅ 执行通关！\n{final_output}")
                            overall_success = True
                            
                            # === 2. 成功后保存认知范式 (Schema) ===
                            if not schema or schema_conf <= 0.85:
                                brain.save_schema(req, sub_plan)
                        
                            break # 逻辑物理双通关，跳出大循环
                        else:
                            brain.express(f"❌ 批评家驳回：{eval_res}")
                            if logic_attempt == max_logic - 1: 
                                brain.express("尝试多次，逻辑中枢判定任务未达标，最终校验失败。")
                        
        except KeyboardInterrupt:
            # 捕获 Ctrl+C：不退出系统，而是作为“唤醒/打断”信号
            print(f"\n{Fore.YELLOW}⚡ [强制唤醒] 已打断当前操作，返回命令模式。{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}（若潜意识正在做梦，它会在当前思考结束后自动挂起。若要彻底退出系统，请输入 exit）{Style.RESET_ALL}")
            
            # 核心机制：强行刷新活跃时间，迫使潜意识认为主人回来了，立刻去睡觉
            last_active_time = time.time()
            continue  # 继续循环，重新打印 Command > 提示符
        except Exception as e:
            print(f"{Fore.RED}[系统崩溃] {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
