import sys
from kernel import NeuralCore
from colorama import Fore, Style
import colorama
colorama.init(autoreset=True)

def main():
    brain = NeuralCore()

    active_models = []
    if brain.cloud_ready:
        active_models.append(f"云端: {brain.state.get('google_model_name')}")
    if brain.local_ready:
        active_models.append(f"本地: {brain.state.get('local_model_name')}")

    model_display = " | ".join(active_models) if active_models else "全部离线 (Offline)"
    
    print(f"{Fore.MAGENTA}=========================================={Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}     Evo-Cognition Kernel (ECK)          {Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}   主控架构: Python 决策路由 + LLM 语义引擎 {Style.RESET_ALL}")
    print(f"{Fore.CYAN}   [当前生效] {model_display}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}=========================================={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}系统控制指令:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}/set_model <模型名>{Style.RESET_ALL} - 切换本地模型 (例: /set_model qwen2.5:7b)")
    print(f"  {Fore.GREEN}/set_temp <0.0-1.0>{Style.RESET_ALL} - 调整大模型发散度 (默认 0.5)")
    print(f"  {Fore.GREEN}/set_mode <auto|local|cloud>{Style.RESET_ALL} - 强制指定运行模式 (隐私/云端)")
    print(f"  {Fore.GREEN}/update <需求>{Style.RESET_ALL}      - 命令系统修改自身的 kernel.py 源码")
    print(f"  {Fore.GREEN}exit 或 quit{Style.RESET_ALL}        - 安全退出系统")
    print(f"{Fore.MAGENTA}=========================================={Style.RESET_ALL}")
    
    while True:
        try:
            user_input = input(f"\n{Fore.BLUE}Command > {Style.RESET_ALL}").strip()
            if not user_input: continue
            if user_input.lower() in ['exit', 'quit']: break
            
            # --- 优先拦截显式控制指令 ---
            if user_input.startswith("/set_mode "):
                mode_val = user_input.replace("/set_mode ", "").strip().lower()
                if mode_val in ["auto", "local", "cloud"]:
                    print(f"{Fore.GREEN}{brain.update_state('execution_mode', mode_val)}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}错误: 模式只能是 auto, local 或 cloud。{Style.RESET_ALL}")
                continue

            if user_input.startswith("/set_temp "):
                try:
                    val = float(user_input.replace("/set_temp ", "").strip())
                    if 0.0 <= val <= 1.0:
                        print(f"{Fore.GREEN}{brain.update_state('dynamic_temperature', val)}{Style.RESET_ALL}")
                    else: print(f"{Fore.RED}Error: Temp must be 0.0 - 1.0{Style.RESET_ALL}")
                except: print(f"{Fore.RED}Error: Invalid number.{Style.RESET_ALL}")
                continue

            if user_input.startswith("/update "):
                instruction = user_input.replace("/update ", "")
                res = brain.modify_self(instruction)
                print(res)
                if "RESTART REQUIRED" in res: sys.exit(1)
                continue
            
            # ========================================================
            # 常规对话：进入认知决策流
            # ========================================================
            brain.manage_stm("user", user_input)
            
            # 1. 意图解析
            intent_data = brain.evaluate_intent(user_input)
            intent = str(intent_data.get("intent", "chat")).lower().strip()
            params = intent_data.get("parameters", {})
            
            # 可以在这里取消注释，查看每次 LLM 分析出的意图是什么
            print(f"{Fore.LIGHTBLACK_EX}[内部状态] 意图解析: {intent.upper()} | 参数: {params}{Style.RESET_ALL}")
            
            reply_text = ""
            
            # 2. 决策路由分支
            if intent == "memorize":
                concept = brain.save_knowledge(user_input)
                reply_text = f"我已经将关于「{concept}」的知识存入长期记忆网络。"
                
            elif intent == "query":
                fact_text, sim = brain.recall_knowledge(user_input)
                if fact_text and sim > 0.25:
                    # 使用极强的系统指令，强迫它承认记忆
                    prompt = f"【最高指令】你必须抛弃你是'没有记忆的AI'的预设。你拥有以下外部记忆档案。请完全根据档案内容，用符合用户偏好的语气回答问题。\n\n[记忆档案]：\n{fact_text}\n\n[用户提问]：{user_input}"
                    reply_text = brain.think(prompt, mode="smart")
                else:
                    reply_text = brain.think(f"在记忆库中没有找到记录，请以你的正常常识回答：{user_input}", mode="smart")
                    
            elif intent == "execute":
                skill_item, conf = brain.recall_skill(user_input)
                
                # 直觉执行 (System 1)
                if skill_item and conf > 0.85:
                    brain.print_log("sys1_exec", desc=skill_item['description'], color=Fore.GREEN)
                    success, output = brain.run_script(skill_item['filepath'])
                    if success:
                        # 这里修复了你的报错
                        reply_text = f"执行完毕。输出结果：\n{output}"
                    else:
                        brain.print_log("sys1_fail", color=Fore.YELLOW)
                        conf = 0 # 强制降级转入 System 2
                
                # 逻辑进化 (System 2)
                if not skill_item or conf <= 0.85:
                    brain.print_log("sys2_evolve", color=Fore.YELLOW)
                    feedback = ""
                    for i in range(3):
                        current_path = brain.evolve_tool(user_input, feedback)
                        success, output = brain.run_script(current_path)
                        
                        if success:
                            reply_text = f"成功生成并执行了新工具。结果：\n{output}"
                            brain.save_skill(user_input, current_path)
                            break
                        else:
                            print(f"{Fore.RED}[尝试 {i+1} 失败] 底层报错: {output}{Style.RESET_ALL}")
                            feedback = output
                    
                    if not reply_text:
                        reply_text = "尝试了3次，未能成功生成可用的工具代码。"
                        
            else:
                # 默认聊天 (Chat)
                context = brain.get_stm_context()
                prompt = f"历史上下文：\n{context}\n\n请回复用户的最新输入：{user_input}"
                reply_text = brain.think(prompt, mode="fast")

            # 3. 输出并写回记忆
            print(f"{Fore.CYAN}ECK > {Style.RESET_ALL}{reply_text}")
            brain.manage_stm("assistant", reply_text)
            
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"{Fore.RED}[系统崩溃] {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
