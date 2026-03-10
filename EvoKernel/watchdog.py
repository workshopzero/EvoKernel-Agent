import subprocess
import time
import os
import sys
import glob
import json
from config import Config

def get_msg(key, **kwargs):
    """从 prompt_templates.json 读取对应语言的提示信息"""
    try:
        if os.path.exists(Config.PROMPT_FILE):
            with open(Config.PROMPT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            lang = data.get("active_language", "zh_CN")
            
            # 尝试获取对应语言包
            texts = data.get("templates", {}).get(lang, {}).get("watchdog", {})
            # 如果没找到，降级使用英文
            if not texts and lang != "en_US":
                texts = data.get("templates", {}).get("en_US", {}).get("watchdog", {})
                
            msg = texts.get(key, key)
            return msg.format(**kwargs)
    except:
        pass
    return key # 如果读取失败，直接返回键名作为保底

def restore_latest_backup():
    """从 backups 目录恢复最近一次的 kernel.py"""
    backups = sorted(glob.glob(os.path.join(Config.BACKUP_DIR, "bk_*.py")))
    if not backups:
        print(get_msg("no_backups"))
        return False
    
    latest = backups[-1]
    filename = os.path.basename(latest)
    print(get_msg("rolling_back", file=filename))
    
    try:
        with open(latest, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open("kernel.py", 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(get_msg("restore_fail", error=str(e)))
        return False

def start_system():
    crash_count = 0
    
    while True:
        print(f"\n{get_msg('starting')}")
        # 启动主进程
        p = subprocess.Popen([sys.executable, "main.py"])
        
        try:
            # 等待进程结束
            exit_code = p.wait()
        except KeyboardInterrupt:
            p.terminate()
            print(get_msg("stopping"))
            break
        
        # --- 处理退出码 ---
        
        if exit_code == 0:
            print(get_msg("exited"))
            break
            
        elif exit_code == 1:
            print(get_msg("restart_req"))
            time.sleep(2)
            crash_count = 0 # 重置崩溃计数
            continue 
            
        else:
            # 异常崩溃 (Code != 0, != 1)
            crash_count += 1
            print(get_msg("crashed", code=exit_code, count=crash_count))
            
            # 简单的死循环保护
            if crash_count >= 5:
                print(get_msg("too_many_crashes"))
                time.sleep(60)
                crash_count = 0

            print(get_msg("analyzing"))
            
            # 检查 kernel.py 语法
            try:
                subprocess.check_call([sys.executable, "-m", "py_compile", "kernel.py"])
                print(get_msg("syntax_ok"))
            except subprocess.CalledProcessError:
                print(get_msg("corrupted"))
                if restore_latest_backup():
                    print(get_msg("rollback_ok"))
                else:
                    print(get_msg("fatal_error"))
                    break
            
            time.sleep(3)

if __name__ == "__main__":
    start_system()
