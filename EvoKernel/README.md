\# 🧠 EvoKernel (Evo-Cognition Kernel)



> \*\*A Python-driven Autonomous Agent with Physical Memory, Local-First Fallback, and Self-Modification.\*\*

> 

> \*这不是一个简单的大模型“套壳”对话框，而是一个将 Python 作为主导大脑，将 LLM 降级为“语义处理模块”的控制论实体。\*



!\[Python](https://img.shields.io/badge/Python-3.10+-blue.svg)

!\[License](https://img.shields.io/badge/License-MIT-green.svg)

!\[Local-First](https://img.shields.io/badge/Architecture-Local--First-orange.svg)



\## ✨ 核心特性 (Core Features)



\- 🧬 \*\*自编码与技能固化 (Procedural Memory)\*\*：当遇到新任务时，系统会自动编写 Python 脚本并在本地沙盒中运行排错。成功后，技能将永久固化在硬盘 (`genome\_db/`) 中，下次直接调用，无需重复思考。

\- 📚 \*\*实体知识库 (Semantic Memory)\*\*：不仅能记住上下文，还能将设定的事实、规则提取并保存为物理 `.md` 文件 (`knowledge\_db/`)，基于向量检索，彻底告别上下文长度限制。

\- 🔄 \*\*智能降级与双轨大脑 (Failover Routing)\*\*：优先使用本地开源模型（如 Ollama/Qwen）保护隐私。当本地模型断网或算力不足时，自动无缝降级至云端大模型（如 Gemini / DeepSeek）。

\- ⚠️ \*\*自我修改与自愈 (Self-Modification)\*\*：系统拥有极高的权限，可以通过自然语言指令重写自身的 `kernel.py` 源码。配备独立的 `watchdog.py` 守护进程，如果新代码引发崩溃，系统会自动重启并回滚到上一个健康版本。

\- 🌐 \*\*原生多语言 (i18n)\*\*：底层架构自带 `zh\_CN` 和 `en\_US` 模板，从控制台提示到系统思考链路，支持一键切换语言。



\## ⚙️ 系统架构图



```text

User Input 

&nbsp;  │

&nbsp;  ▼

\[意图路由 (Cognitive Router)] ──▶ (Chat / Memorize / Query / Execute)

&nbsp;  │

&nbsp;  ├─▶ 记忆指令 ──▶ 提取知识 ──▶ 存入 physical .md (knowledge\_db)

&nbsp;  ├─▶ 查询指令 ──▶ 向量检索 ──▶ 结合记忆回答

&nbsp;  └─▶ 执行指令 ──▶ 检索 genome\_db

&nbsp;                      ├── 命中 ──▶ \[直觉系统] 直接执行 .py 脚本

&nbsp;                      └── 未命中 ──▶ \[逻辑系统] 动态编写代码 ──▶ 运行/排错 ──▶ 保存新技能

