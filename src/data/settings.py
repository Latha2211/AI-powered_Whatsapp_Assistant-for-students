"""
Application Settings - Centralized configuration management
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================
# Bot Configuration
# ============================================

BOT_CONFIGS = {
    "Bot_Primary": {
        "name": os.getenv("BOT_1_NAME", "Bot_Primary"),
        "user_data_path": os.getenv("BOT_1_USER_DATA_PATH", "C:/WhatsApp_UserData/Bot1"),
        "enabled": os.getenv("BOT_1_ENABLED", "true").lower() == "true"
    },
    "Bot_Secondary": {
        "name": os.getenv("BOT_2_NAME", "Bot_Secondary"),
        "user_data_path": os.getenv("BOT_2_USER_DATA_PATH", "C:/WhatsApp_UserData/Bot2"),
        "enabled": os.getenv("BOT_2_ENABLED", "false").lower() == "true"
    }
}


# ============================================
# Database Configuration
# ============================================

DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "database": os.getenv("DB_NAME", "whatsapp_bot_db"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "charset": os.getenv("DB_CHARSET", "utf8mb4")
}


# ============================================
# OpenAI/LLM Configuration
# ============================================

LLM_CONFIG = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    "temperature": float(os.getenv("RESPONSE_TEMPERATURE", "0.3")),
    "max_tokens": int(os.getenv("MAX_RESPONSE_LENGTH", "1000"))
}


# ============================================
# RAG Configuration
# ============================================

RAG_CONFIG = {
    "faiss_index_path": os.getenv("FAISS_INDEX_PATH", "data/faiss_index"),
    "faq_csv_path": os.getenv("FAQ_CSV_PATH", "data/faq_database.csv"),
    "chunk_size": int(os.getenv("CHUNK_SIZE", "1000")),
    "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "200")),
    "retrieval_top_k": int(os.getenv("RETRIEVAL_TOP_K", "4")),
    "similarity_threshold": float(os.getenv("SIMILARITY_THRESHOLD", "0.65"))
}


# ============================================
# WhatsApp Automation Configuration
# ============================================

WHATSAPP_CONFIG = {
    "chrome_driver_path": os.getenv("CHROME_DRIVER_PATH", "C:/chromedriver/chromedriver.exe"),
    "timeout_seconds": int(os.getenv("TIMEOUT_SECONDS", "300")),
    "idle_interval_seconds": int(os.getenv("IDLE_CHECK_INTERVAL_SECONDS", "10")),
    "anti_lock_interval": int(os.getenv("ANTI_LOCK_INTERVAL_SECONDS", "240")),
    "max_messages_per_minute": int(os.getenv("MAX_MESSAGES_PER_MINUTE", "10"))
}


# ============================================
# File Paths Configuration
# ============================================

PATHS_CONFIG = {
    "temp_download_dir": os.getenv("TEMP_DOWNLOAD_DIR", "C:/temp/whatsapp_downloads"),
    "log_dir": os.getenv("LOG_DIR", "logs"),
    "responses_csv": os.getenv("RESPONSES_CSV", "data/responses.csv"),
    "keywords_config": os.getenv("KEYWORDS_CONFIG_PATH", "config/keywords.json")
}


# ============================================
# Email Configuration
# ============================================

EMAIL_CONFIG = {
    "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "smtp_user": os.getenv("SMTP_USER", ""),
    "smtp_password": os.getenv("SMTP_PASSWORD", ""),
    "finance_email": os.getenv("FINANCE_EMAIL", "finance@tauedu.org")
}


# ============================================
# TConnect API Configuration
# ============================================

TCONNECT_CONFIG = {
    "api_url": os.getenv("TCONNECT_API_URL", "https://api.tconnect.com"),
    "api_key": os.getenv("TCONNECT_API_KEY", "")
}


# ============================================
# Logging Configuration
# ============================================

LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "enable_debug_screenshots": os.getenv("ENABLE_DEBUG_SCREENSHOTS", "false").lower() == "true"
}


# ============================================
# Security Configuration
# ============================================

SECURITY_CONFIG = {
    "allowed_contact_prefixes": os.getenv("ALLOWED_CONTACT_PREFIXES", "+91,+1").split(","),
    "enable_message_encryption": os.getenv("ENABLE_MESSAGE_ENCRYPTION", "false").lower() == "true"
}


# ============================================
# Validation Functions
# ============================================

def validate_environment() -> bool:
    """
    Validate required environment variables are set
    
    Returns:
        True if all required variables are present
    """
    required_vars = [
        "OPENAI_API_KEY",
        "DB_HOST",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "CHROME_DRIVER_PATH"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True


def get_all_config() -> Dict[str, Any]:
    """
    Get all configuration as a single dictionary
    
    Returns:
        Combined configuration dictionary
    """
    return {
        "bots": BOT_CONFIGS,
        "database": DATABASE_CONFIG,
        "llm": LLM_CONFIG,
        "rag": RAG_CONFIG,
        "whatsapp": WHATSAPP_CONFIG,
        "paths": PATHS_CONFIG,
        "email": EMAIL_CONFIG,
        "tconnect": TCONNECT_CONFIG,
        "logging": LOGGING_CONFIG,
        "security": SECURITY_CONFIG
    }


def print_config_summary():
    """Print configuration summary (without sensitive data)"""
    print("=" * 60)
    print("Configuration Summary")
    print("=" * 60)
    
    print("\n🤖 Bots:")
    for bot_name, config in BOT_CONFIGS.items():
        status = "✅ Enabled" if config["enabled"] else "❌ Disabled"
        print(f"  {bot_name}: {status}")
    
    print("\n🗄️  Database:")
    print(f"  Host: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
    print(f"  Database: {DATABASE_CONFIG['database']}")
    
    print("\n🧠 LLM:")
    print(f"  Model: {LLM_CONFIG['model']}")
    print(f"  Embedding: {LLM_CONFIG['embedding_model']}")
    print(f"  Temperature: {LLM_CONFIG['temperature']}")
    
    print("\n🔍 RAG:")
    print(f"  Index Path: {RAG_CONFIG['faiss_index_path']}")
    print(f"  Chunk Size: {RAG_CONFIG['chunk_size']}")
    print(f"  Similarity Threshold: {RAG_CONFIG['similarity_threshold']}")
    
    print("\n📱 WhatsApp:")
    print(f"  Driver: {WHATSAPP_CONFIG['chrome_driver_path']}")
    print(f"  Timeout: {WHATSAPP_CONFIG['timeout_seconds']}s")
    
    print("\n📋 Logging:")
    print(f"  Level: {LOGGING_CONFIG['level']}")
    print(f"  Log Dir: {PATHS_CONFIG['log_dir']}")
    
    print("=" * 60)


# ============================================
# Environment-Specific Settings
# ============================================

ENV = os.getenv("ENVIRONMENT", "development")

if ENV == "production":
    # Production-specific settings
    LOGGING_CONFIG["level"] = "WARNING"
    WHATSAPP_CONFIG["max_messages_per_minute"] = 5
elif ENV == "development":
    # Development-specific settings
    LOGGING_CONFIG["level"] = "DEBUG"
    LOGGING_CONFIG["enable_debug_screenshots"] = True
elif ENV == "testing":
    # Testing-specific settings
    DATABASE_CONFIG["database"] = "whatsapp_bot_test_db"
    WHATSAPP_CONFIG["timeout_seconds"] = 30
