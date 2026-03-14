# 🧠 Evo-Cognition Kernel (ECK) V1.1

🌍 **[Click here for English Version](README.md)**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

**ECK (Evo-Cognition Kernel)** 是一个极客向的、具有“类生命体征”的 AI Agent 底层架构。它不依赖于庞大的 LangChain 等框架，而是从零构建了一套包含 **动态路由、潜意识做梦、AST 物理沙盒、肌肉记忆、甚至是自我内核修改** 的闭环认知系统。

## 🌟 核心特性
- 🧠 **四维记忆切片**：包含工作记忆、语义知识、程序基因库以及认知范式（肌肉记忆）。
- 💤 **潜意识做梦引擎**：在电脑空闲时，后台基于现有记忆“发散突变”，主动发明新工具。
- 🛡️ **物理沙盒与 AST 拦截**：带有进程级超时、内存癌变监控以及死循环检测的 Python 执行沙盒。
- 🔁 **双轨制降级路由**：同时挂载云端（如 Gemini）与本地模型（如 Ollama），断网自动降级。
- 🧬 **极客反思**：代码执行报错时，自动拿着 traceback 进行反思并重写代码。

## 🚀 快速开始
```bash
git clone https://github.com/workshopzero/EvoKernel-Agent.git
cd EvoKernel-Agent
pip install -r requirements.txt

请将 .env.example 重命名为 .env，并填入你的模型配置。

# 启动守护进程
python watchdog.py

🕹️ 控制台指令

    /set_mode <auto|local|cloud|offline> : 强制更改系统运行模式
    /toggle_human <on|off> : 开关执行代码前的人工确权锁
    /toggle_reflect <on|off> : 开关代码报错自动反思功能
    /review : 审查系统在后台“做梦”发明的突变技能

Created by workshopzero - License: MIT