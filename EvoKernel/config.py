import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # --- 静态基础设施配置 ---
    PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
    LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")
    GOOGLE_MODEL_NAME = os.getenv("GOOGLE_MODEL_NAME", "gemini-2.5-flash")
    
    LOCAL_API_BASE = os.getenv("HOST_LLM_API_BASE")
    LOCAL_API_KEY = os.getenv("HOST_LLM_API_KEY", "xx")
    LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:7b")

    # --- 核心路径配置 ---
    GENOME_DIR = "genome_db"
    MEMORY_FILE = os.path.join(GENOME_DIR, "memory_index.json")
    KNOWLEDGE_DIR = "knowledge_db"
    KNOWLEDGE_INDEX = os.path.join(KNOWLEDGE_DIR, "knowledge_index.json")
    STM_FILE = "short_term_memory.json"
    STATE_FILE = "system_state.json" 
    PROMPT_FILE = "prompt_templates.json"
    LOG_FILE = "system.log"
    KERNEL_PATH = "kernel.py"
    BACKUP_DIR = "backups"
    
    # --- V1.1~V1.4 新增核心存储路径 ---
    PENDING_DIR = "pending_skills"
    SCHEMA_DIR = "schema_db"
    SCHEMA_FILE = os.path.join(SCHEMA_DIR, "schema_index.json")

    # --- 全局运行开关与默认值 ---
    DEFAULT_EXECUTION_MODE = os.getenv("DEFAULT_EXECUTION_MODE", "auto").lower()
    DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.5"))
    ALLOW_SELF_MOD = os.getenv("ALLOW_SELF_MODIFICATION", "False").lower() == "true"
    
    REQUIRE_HUMAN_CONFIRMATION = os.getenv("REQUIRE_HUMAN_CONFIRMATION", "True").lower() == "true"
    ENABLE_INTERNAL_REFLECTION = os.getenv("ENABLE_INTERNAL_REFLECTION", "False").lower() == "true"
    ENABLE_SUBCONSCIOUS = os.getenv("ENABLE_SUBCONSCIOUS", "False").lower() == "true"
    
    ENABLE_DYNAMIC_ROUTING = os.getenv("ENABLE_DYNAMIC_ROUTING", "True").lower() == "true"
    ENABLE_VOICE_MODULE = os.getenv("ENABLE_VOICE_MODULE", "False").lower() == "true"

    SUBCONSCIOUS_SCHEDULE = os.getenv("SUBCONSCIOUS_SCHEDULE", "OFF").upper()
    MAX_BACKGROUND_CPU_PERCENT = float(os.getenv("MAX_BACKGROUND_CPU_PERCENT", "60"))
    
    LOG_MAX_SIZE = 1 * 1024 * 1024 
    LOG_BACKUP_COUNT = 3
    MAX_STM_ROUNDS = 5 

    # 初始化所有依赖目录 (补全了 PENDING_DIR 和 SCHEMA_DIR)
    for d in [GENOME_DIR, BACKUP_DIR, KNOWLEDGE_DIR, PENDING_DIR, SCHEMA_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)
