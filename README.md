# 🧠 Evo-Cognition Kernel (ECK) V1.1

🌍 **[中文文档请点击这里 (Chinese Version)](README_zh.md)**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

> 🤖 **Special Thanks: The core architecture and foundational code of this project were designed and generated with the assistance of Google Gemini.**

**ECK (Evo-Cognition Kernel)** is a geek-oriented, "life-like" AI Agent infrastructure. By completely abandoning heavy wrapper frameworks like LangChain, ECK builds a pure, closed-loop cognitive system from scratch using native Python.

This project explores the boundaries of an AI Agent's "autonomy" and "security." It not only understands commands to write code but also **dreams** while idle, **reflects** upon encountering errors, **triggers a circuit breaker** when detecting malicious code, and can even **modify its own kernel source code** upon your authorization (which is also the reason for choosing Python).

---

## 🌟 Core System Architecture

### 1. 🧠 4D Memory System
ECK categorizes memory into four strict biological dimensions:
*   **Short-Term Memory (STM)**: Maintained via `short_term_memory.json` for conversational context. Exceeding dialogue thresholds triggers subconscious compression into a short summary.
*   **Semantic Knowledge**: Long-term memory for facts and personas. Implements lightweight Vector Retrieval (RAG) using native Numpy arrays, saving facts as `.md` files.
*   **Procedural Genome (Tools)**: Muscle memory. Successfully executed Python scripts are permanently solidified in `genome_db` as fundamental tools for future tasks.
*   **Cognitive Schema**: High-level abstraction. The system extracts execution steps of successful tasks into generic logical graphs with variable slots (e.g., `$TARGET`). When facing similar problems, it executes purely on "intuition".

### 2. 💤 Subconscious Dreaming Engine
Operates via an independent `background_worker` daemon thread. When host CPU usage is low and no user commands are given, the system enters "sleep mode":
*   **Divergent Mutation**: Randomly extracts memory concepts and existing skills to forcefully combine and invent bizarre new tools.
*   **Focused Learning**: If a specific `Focus` area is set, the system explores deeply within that domain.
*   All code generated in dreams is placed in a quarantine zone (`pending_skills`), awaiting human review via the `/review` command in the morning.

### 3. 🛡️ AST Sandbox & Anomaly Detection
Code needs a cage.
*   **Static Analysis (AST)**: Scans Abstract Syntax Trees before execution to block dangerous operations like `rm -rf`, `os.system`, or `eval`.
*   **Dynamic Circuit Breaker**: Runs a separate subprocess sandbox that monitors memory usage (preventing memory leaks/cancer) and CPU load. It auto-kills processes caught in silent infinite loops (e.g., 15s of no output with high CPU).

### 4. 🔁 Dynamic Failover Routing
Connects to both a primary model and a fallback model. If network issues or Cloud API crashes occur, the cognitive router seamlessly fails over to the fallback model to ensure task continuity.

### 5. 🧬 Auto-Reflection & Self-Modification
*   **Double-Layer Healing Loop**: Tasks consist of a "Logic Validation Layer" and a "Physical Sandbox Layer." If code crashes (e.g., missing library, syntax error), the system reads the Traceback to rewrite the code and silently auto-installs missing dependencies.
*   **Source Code Mutation**: Using the `/update` command, the LLM can read and modify its own `kernel.py` source code. `watchdog.py` validates syntax and logic upon restart, automatically rolling back to a backup if corruption is detected.

---

## 🚀 Quick Start

### 1. Environment Setup
```bash
git clone https://github.com/workshopzero/EvoKernel-Agent.git
cd EvoKernel-Agent
pip install -r requirements.txt

2. Configure Credentials

Duplicate .env.example, rename it to .env.

    Primary Cloud Model: Insert your GCP Project ID (for Google Gemini).
    Fallback/Local Model: The system utilizes the standard OpenAI SDK client, meaning it supports ANY API compatible with the OpenAI format. You can use local deployment engines like Ollama, vLLM, or LM Studio, or even third-party online endpoints (e.g., DeepSeek, Qwen). Just fill in your API Base URL and Key accordingly.

3. Start the Watchdog

Highly Recommended: ALWAYS launch via watchdog.py! This activates crash auto-restart and self-modification rollback protections.

python watchdog.py

🕹️ Full CLI Commands

At the Command > prompt, you can type the following system controls:

    /set_model <name> : Hot-swap the fallback/local model (e.g., qwen2.5:7b).
    /set_temp <0.0-1.0> : Adjust LLM temperature (higher = more creative).
    /set_mode <auto|local|cloud|offline> : Force the execution routing mode.
    /set_lang <code_str> : Switch UI language and trigger LLM auto-translation of config files.
    /set_focus <domain> : Direct the subconscious dreaming engine to focus on a specific field (e.g., web scraping).
    /toggle_cloud <on|off> : Physically sever or restore Cloud API connections.
    /toggle_human <on|off> : Toggle Human Auth Lock (requires typing 'y' before executing LLM code).
    /toggle_reflect <on|off> : Toggle Auto-Reflection (auto-fix bugs vs. give up on crash).
    /review : Review mutated tools invented by the subconscious to approve/reject them.
    /update <req> : HIGH RISK! Command the system to modify its own kernel.py source code.
    exit or quit : Safely shutdown. (Use Ctrl+C to interrupt if it spam-dreams without closing the app).

📜 License

This project is licensed under the MIT License. You are free to use, modify, and distribute it, provided the original copyright notice is retained.