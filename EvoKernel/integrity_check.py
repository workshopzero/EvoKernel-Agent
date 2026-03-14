import sys
import traceback
import os

def run_inspection():
    try:
        print("[质检] 正在导入内核克隆体...")
        # 强制从当前目录导入候选内核
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
        from kernel_candidate import NeuralCore
        print("[质检] 语法结构完整。")

        print("[质检] 正在实例化克隆大脑...")
        brain = NeuralCore()
        print("[质检] 实例化成功。")

        print("[质检] 正在进行认知逻辑测试...")
        # 给克隆大脑喂一条测试意图，看它能不能正常提取 JSON
        test_intent = brain.generate_plan("你好，这是一次测试", "")
        
        if isinstance(test_intent, list) and len(test_intent) > 0 and "opcode" in test_intent[0]:
            print("[质检] 认知路由运转正常！内核验证通过！")
            sys.exit(0)
        else:
            print("[质检] 致命错误：认知路由返回的数据结构损坏！")
            sys.exit(1)

    except Exception as e:
        print("[质检] 灾难性崩溃！克隆体无法运行。")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_inspection()
