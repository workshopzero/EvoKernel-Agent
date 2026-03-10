import sys
import traceback

try:
    # 尝试导入候选内核
    # 注意：这时候文件应该叫 kernel_candidate.py
    from kernel_candidate import NeuralCore
    
    print("Syntax Check: OK")
    
    # 尝试实例化 (检查 __init__ 是否有逻辑错误)
    # 我们加上 try-except 避免真正的模型连接（省时间），只测逻辑
    try:
        brain = NeuralCore()
        print("Initialization Check: OK")
    except Exception as e:
        # 如果是因为缺 Key 或者 API 连不上，这不算代码逻辑错误，可以放行
        # 但如果是 NameError, AttributeError，那是代码写错了
        err_msg = str(e)
        if "API" in err_msg or "Connect" in err_msg:
            print("Initialization Warning (Ignored):", err_msg)
        else:
            raise e

    print("Integrity Check PASSED")
    sys.exit(0)

except Exception:
    # 捕获所有错误并打印
    traceback.print_exc()
    sys.exit(1)
