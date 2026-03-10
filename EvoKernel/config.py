import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # --- 静态基础设施配置 ---
    
    # Google Vertex AI
    PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
    LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")
    GOOGLE_MODEL_NAME = os.getenv("GOOGLE_MODEL_NAME", "gemini-2.5-flash")
    
    # Local Host LLM
    LOCAL_API_BASE = os.getenv("HOST_LLM_API_BASE")
    LOCAL_API_KEY = os.getenv("HOST_LLM_API_KEY", "xx")
    LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:7b")
    DEFAULT_EXECUTION_MODE = os.getenv("DEFAULT_EXECUTION_MODE", "auto").lower()
    DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.5"))
    
    # --- 核心路径配置 (升级版) ---
    # 1. 程序性记忆 (技能库)
    GENOME_DIR = "genome_db"
    MEMORY_FILE = os.path.join(GENOME_DIR, "memory_index.json")
    
    # 2. 语义性记忆 (知识库)
    KNOWLEDGE_DIR = "knowledge_db"
    KNOWLEDGE_INDEX = os.path.join(KNOWLEDGE_DIR, "knowledge_index.json")
    
    # 3. 短期工作记忆 (上下文)
    STM_FILE = "short_term_memory.json"
    MAX_STM_ROUNDS = 5  # 超过此轮数触发记忆压缩
    
    # 系统状态与配置
    STATE_FILE = "system_state.json" 
    PROMPT_FILE = "prompt_templates.json"
    LOG_FILE = "system.log"
    KERNEL_PATH = "kernel.py"
    BACKUP_DIR = "backups"

    # 日志策略
    LOG_MAX_SIZE = 1 * 1024 * 1024 
    LOG_BACKUP_COUNT = 3

    # 安全开关
    ALLOW_SELF_MOD = os.getenv("ALLOW_SELF_MODIFICATION", "False").lower() == "true"

    # 初始化所有依赖目录
    for d in [GENOME_DIR, BACKUP_DIR, KNOWLEDGE_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)
