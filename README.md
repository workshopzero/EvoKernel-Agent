# 🧠 EvoKernel (Evo-Cognition Kernel)

> **A Python-driven Autonomous Agent with Physical Memory, Local-First Fallback, and Self-Modification.**
> 
> *这不是一个简单的大模型“套壳”对话框，而是一个将 Python 作为主导大脑，将 LLM 降级为“语义处理模块”的控制论实体。*

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Local-First](https://img.shields.io/badge/Architecture-Local--First-orange.svg)

## ✨ 核心特性 (Core Features)

- 🧬 **自编码与技能固化 (Procedural Memory)**：当遇到新任务时，系统会自动编写 Python 脚本并在本地沙盒中运行排错。成功后，技能将永久固化在硬盘 (`genome_db/`) 中，下次直接调用，无需重复思考。
- 📚 **实体知识库 (Semantic Memory)**：不仅能记住上下文，还能将设定的事实、规则提取并保存为物理 `.md` 文件 (`knowledge_db/`)，基于向量检索，彻底告别上下文长度限制。
- 🔄 **智能降级与双轨大脑 (Failover Routing)**：优先使用本地开源模型（如 Ollama/Qwen）保护隐私。当本地模型断网或算力不足时，自动无缝降级至云端大模型（如 Gemini / DeepSeek）。
- ⚠️ **自我修改与自愈 (Self-Modification)**：系统拥有极高的权限，可以通过自然语言指令重写自身的 `kernel.py` 源码。配备独立的 `watchdog.py` 守护进程，如果新代码引发崩溃，系统会自动重启并回滚到上一个健康版本。
- 🌐 **原生多语言 (i18n)**：底层架构自带 `zh_CN` 和 `en_US` 模板，从控制台提示到系统思考链路，支持一键切换语言。

## ⚙️ 系统架构图

```text
User Input 
   │
   ▼
[意图路由 (Cognitive Router)] ──▶ (Chat / Memorize / Query / Execute)
   │
   ├─▶ 记忆指令 ──▶ 提取知识 ──▶ 存入 physical .md (knowledge_db)
   ├─▶ 查询指令 ──▶ 向量检索 ──▶ 结合记忆回答
   └─▶ 执行指令 ──▶ 检索 genome_db
                       ├── 命中 ──▶ [直觉系统] 直接执行 .py 脚本
                       └── 未命中 ──▶ [逻辑系统] 动态编写代码 ──▶ 运行/排错 ──▶ 保存新技能

🚀 快速开始 (Quick Start)
1. 克隆仓库

git clone https://github.com/<你的GitHub用户名>/EvoKernel-Agent.git
cd EvoKernel-Agent

2. 安装依赖

pip install -r requirements.txt

3. 配置环境变量

复制环境模板并填入你的配置：

cp .env.example .env

修改 .env 文件（支持接入任何兼容 OpenAI 格式的 API，如 Ollama, DeepSeek, 通义千问等）：

# 云端模型 (保底算力)
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_LOCATION=us-central1
GOOGLE_MODEL_NAME=gemini-2.5-flash

# 本地/兼容大模型 (优先调用)
HOST_LLM_API_BASE=http://127.0.0.1:11434/v1
HOST_LLM_API_KEY=ollama
LOCAL_MODEL_NAME=qwen2.5:7b

# 系统默认设置
DEFAULT_EXECUTION_MODE=auto  # auto / local / cloud
DEFAULT_TEMPERATURE=0.5

4. 唤醒系统

请始终通过守护进程启动系统（提供防崩溃和自愈能力）：

python watchdog.py

🎯 玩法演示 (Showcase)

启动后，在 Command > 提示符下输入自然语言即可触发不同的认知分支：

1. 自动化执行与学习 (Execute)

    "写一个Python脚本，获取当前电脑的内存使用率并打印出来。"
    系统将自动写代码 -> 运行报错 -> 读取报错信息 -> 修正代码 -> 运行成功 -> 永久保存为技能。

2. 建立实体记忆 (Memorize)

    "记住我的设定：我是一个喜欢赛博朋克风格的程序员，以后回答尽量带点极客色彩。"
    系统会在 knowledge_db/ 生成 Markdown 建立档案。

3. 知识检索 (Query)

    "根据你的记忆，我喜欢什么风格？"
    系统进行混合检索（向量+文本重合度），突破大模型的“客服人设”并准确回答。

4. 内核自我修改 (Update - 高危)

    "/update 请修改 think 函数，让系统每次打印内容前都加一句 'Master: '。"
    系统将读取自身源码，修改并生成候选版本，通过完整性检测后自动重启应用新法则。

🛠️ 显式控制指令

在对话框中直接输入以下指令控制底层行为：

    /set_model <name> : 实时切换本地模型 (例: /set_model deepseek-chat)
    /set_mode <mode> : 强制指定运行模式 (auto 智能降级 / local 断网隐私 / cloud 强制云端)
    /set_temp <0-1> : 调整发散度

فلس 哲学与愿景 (Philosophy)

目前的 AI 应用大多是 "LLM as the Brain"。而 EvoKernel 坚信 "Python as the Brain, LLM as the Calculator"。
系统的心智流、记忆读取、代码执行、逻辑判断全部由确定性的 Python if/else 与主循环掌控，仅在需要语义转换时调用 LLM。这极大降低了幻觉，提升了 Agent 系统的工程健壮性。
📜 许可证

MIT License