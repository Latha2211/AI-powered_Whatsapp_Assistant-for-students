"""
WhatsApp AI Bot - Main Entry Point
Educational support bot for Texila American University students
"""

import os
import sys
import threading
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import core modules
from src.bot_manager import BotManager
from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger
from src.config.settings import BOT_CONFIGS, validate_environment

# Setup logger
logger = setup_logger("main")


def initialize_system():
    """Initialize system components"""
    try:
        logger.info("🚀 Initializing WhatsApp AI Bot System...")
        
        # Validate environment variables
        if not validate_environment():
            logger.error("❌ Environment validation failed")
            sys.exit(1)
        
        # Initialize database
        db_manager = DatabaseManager()
        if not db_manager.test_connection():
            logger.error("❌ Database connection failed")
            sys.exit(1)
        
        logger.info("✅ System initialization complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ System initialization failed: {e}")
        return False


def main():
    """Main application entry point"""
    try:
        print("=" * 60)
        print("WhatsApp AI Bot - Educational Support System")
        print("Texila American University")
        print("=" * 60)
        
        # Initialize system
        if not initialize_system():
            return
        
        # Initialize bot manager
        bot_manager = BotManager()
        
        # Start bots based on configuration
        active_bots = []
        for bot_name, config in BOT_CONFIGS.items():
            if config.get("enabled", True):
                logger.info(f"🤖 Starting bot: {bot_name}")
                bot_thread = threading.Thread(
                    target=bot_manager.start_bot,
                    args=(bot_name, config),
                    daemon=False
                )
                bot_thread.start()
                active_bots.append((bot_name, bot_thread))
        
        logger.info(f"✅ {len(active_bots)} bot(s) started successfully")
        
        # Keep main thread alive
        try:
            for bot_name, thread in active_bots:
                thread.join()
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown signal received...")
            bot_manager.stop_all_bots()
            logger.info("✅ All bots stopped gracefully")
        
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
