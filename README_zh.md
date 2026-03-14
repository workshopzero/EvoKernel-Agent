# 🧠 Evo-Cognition Kernel (ECK) V1.1

🌍 **[Click here for English Version](README.md)**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

> 🤖 **特别致谢：本项目的核心架构理念与基础代码由 Google Gemini 辅助设计与生成。**

**ECK (Evo-Cognition Kernel)** 是一个极客向的、具有“类生命体征”的 AI Agent 底层架构。它彻底抛弃了 LangChain 等臃肿的包装框架，从零开始（From Scratch）使用原生 Python 构建了一套纯粹的闭环认知系统。

本项目旨在探索 AI Agent 的“自主性”与“安全性”边界。它不仅能听懂指令写代码，还能在闲置时**做梦**、在报错时**反思**、在遇到危险代码时**自我熔断**，甚至能在你的授权下**修改它自己的内核源码**（这也是选择 Python 的原因）。

---

## 🌟 核心系统架构 (Architecture)

### 1. 🧠 四维记忆切片 (4D Memory System)
ECK 将记忆严格划分为四个不同的生理维度：
*   **工作记忆 (STM)**：基于 `short_term_memory.json`，用于维持当前对话的上下文。当对话轮数达到阈值时，会触发潜意识压缩，将历史记录蒸馏为几十个字的摘要。
*   **语义知识 (Knowledge)**：长期记忆，用于保存客观事实与人物设定。基于原生 Numpy 矩阵实现轻量级向量检索（RAG），以 `.md` 格式落盘存档。
*   **程序基因库 (Genome)**：肌肉记忆，系统成功编写并跑通的 Python 脚本会被永久固化在 `genome_db` 中，作为未来的基础工具。
*   **认知范式 (Schema)**：高阶抽象，系统会将成功任务的执行步骤抽象为带有变量槽位（如 `$TARGET`）的通用逻辑图谱，下次遇到同类问题直接“凭直觉”执行。

### 2. 💤 潜意识做梦引擎 (Subconscious Dreaming)
通过独立的 `background_worker` 守护线程实现。当系统检测到宿主机 CPU 占用低于阈值，且主人长时间未下达指令时，系统会进入“睡眠状态”：
*   **发散突变**：随机抽取记忆概念与现有技能进行强行融合，发明千奇百怪的新工具。
*   **定向学习**：若主人锁定了 Focus 领域，系统会在该领域内进行深度探索。
*   所有梦境中写出的代码都会放入隔离区 (`pending_skills`)，等待主人早晨醒来通过 `/review` 指令验收转正。

### 3. 🛡️ 物理沙盒与 AST 安全拦截 (Sandbox & Security)
代码写得再好，也需要关在笼子里跑。
*   **静态分析 (AST)**：在执行任何代码前，通过抽象语法树扫描，拦截 `rm -rf`、`os.system`、`eval` 等危险操作。
*   **动态熔断**：启动独立的子进程沙盒，实时监控内存使用率（防止内存泄漏/癌变）与 CPU 占用率。若触发 `15秒无输出且CPU满载`，直接判定为死循环并击杀进程。

### 4. 🔁 双轨制降级路由 (Dynamic Failover Routing)
同时挂载主模型与备用模型。当遇到网络波动或主 API 崩溃时，认知路由会自动无缝降级到备用模型继续执行任务，保障系统高可用性。

### 5. 🧬 极客反思与自我修改 (Auto-Reflection & Self-Mod)
*   **双层自愈循环**：执行任务时包含“逻辑验收层”与“物理沙盒层”。若代码报错（如缺少库、语法错误），系统会自动读取 Traceback 报错信息并重写代码；自动静默安装缺失依赖。
*   **源码突变**：通过 `/update` 指令，可直接要求大模型读取并修改 `kernel.py` 的源码。修改后会自动进行语法与实例化逻辑检查，若崩溃则由守护进程 `watchdog.py` 自动回滚至上一个备份版本。

---

## 🚀 快速开始

### 1. 环境准备
```bash
git clone https://github.com/workshopzero/EvoKernel-Agent.git
cd EvoKernel-Agent
pip install -r requirements.txt

2. 配置环境变量

将项目根目录的 .env.example 复制并重命名为 .env。

    云端主模型：填入你的 GCP Project ID (用于 Google Gemini)。
    备用/本地模型：系统底层使用了标准的 OpenAI SDK 客户端，这意味着它支持任何兼容 OpenAI 格式的 API。你不仅可以填入本地的 Ollama、vLLM 或 LM Studio 地址，甚至可以填入 DeepSeek、千问等线上第三方大模型的 API 接口和 Key。

3. 启动守护进程

强烈建议：永远通过 watchdog.py 启动系统！ 只有这样，才能激活崩溃自动重启和代码修改回滚保护机制。

python watchdog.py

🕹️ 控制台指令大全 (Commands)

在 Command > 提示符下，可随时输入以下系统指令：

    /set_model <模型名> : 动态热切换备用/本地模型（如 qwen2.5:7b）。
    /set_temp <0.0-1.0> : 调整大模型的发散度（温度），数值越高越有创造力。
    /set_mode <auto|local|cloud|offline> : 强制指定运行模式（默认 auto 自动路由）。
    /set_lang <语言代码> : 强制切换系统 UI 语言并由 LLM 自动翻译底层配置。
    /set_focus <领域> : 设定系统潜意识在后台做梦时的定向学习目标（如：爬虫、数据分析）。
    /toggle_cloud <on|off> : 物理切断/恢复云端大模型的连接测试。
    /toggle_human <on|off> : 开关“人工确权锁”（开启时，执行它写的代码前必须输入 y 同意）。
    /toggle_reflect <on|off> : 开关极客反思（开启时，代码报错它会自己修；关闭时，报错直接放弃）。
    /review : 审查潜意识后台发明的突变技能，决定是否将其并入主基因库。
    /update <需求> : 高危操作！命令系统直接修改自己的 kernel.py 源码。
    exit 或 quit : 安全退出系统。(如果在其做梦刷屏时想打断，可直接按 Ctrl+C)

📜 许可证 (License)

本项目采用 MIT License。你可以自由使用、修改和分发，但需保留原始版权声明。