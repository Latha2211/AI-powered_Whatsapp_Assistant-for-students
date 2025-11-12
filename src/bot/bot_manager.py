"""
Bot Manager - Manages multiple bot instances and their lifecycle
"""

import threading
from typing import Dict
from datetime import datetime
from collections import defaultdict

from src.bot.whatsapp_automation import WhatsAppBot
from src.utils.logger import setup_logger

logger = setup_logger("bot_manager")


class BotManager:
    """Manages multiple WhatsApp bot instances"""
    
    def __init__(self):
        self.bots: Dict[str, WhatsAppBot] = {}
        self.bot_threads: Dict[str, threading.Thread] = {}
        self.stop_events: Dict[str, threading.Event] = {}
        self.bot_statuses = defaultdict(lambda: {
            "name": "",
            "status": "Stopped",
            "start_time": None,
            "stop_time": None,
            "processed_count": 0,
            "unread_count": 0,
            "logs": []
        })
    
    def start_bot(self, bot_name: str, config: Dict) -> bool:
        """
        Start a bot instance
        
        Args:
            bot_name: Unique bot identifier
            config: Bot configuration dict
        
        Returns:
            True if started successfully
        """
        try:
            if bot_name in self.bots and self.bots[bot_name].is_running():
                logger.warning(f"⚠️ Bot {bot_name} is already running")
                return False
            
            logger.info(f"🚀 Starting bot: {bot_name}")
            
            # Create stop event
            stop_event = threading.Event()
            self.stop_events[bot_name] = stop_event
            
            # Initialize bot status
            self.bot_statuses[bot_name].update({
                "name": bot_name,
                "status": "Starting",
                "start_time": datetime.now(),
                "stop_time": None,
                "processed_count": 0
            })
            
            # Create bot instance
            bot = WhatsAppBot(
                bot_name=bot_name,
                user_data_path=config.get("user_data_path"),
                stop_event=stop_event,
                bot_statuses=self.bot_statuses
            )
            
            self.bots[bot_name] = bot
            
            # Start bot in separate thread
            bot_thread = threading.Thread(
                target=bot.run,
                name=f"Thread-{bot_name}",
                daemon=False
            )
            bot_thread.start()
            self.bot_threads[bot_name] = bot_thread
            
            logger.info(f"✅ Bot {bot_name} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot {bot_name}: {e}")
            self.bot_statuses[bot_name]["status"] = "Error"
            return False
    
    def stop_bot(self, bot_name: str, timeout: int = 30) -> bool:
        """
        Stop a specific bot
        
        Args:
            bot_name: Bot identifier
            timeout: Seconds to wait for graceful shutdown
        
        Returns:
            True if stopped successfully
        """
        try:
            if bot_name not in self.bots:
                logger.warning(f"⚠️ Bot {bot_name} not found")
                return False
            
            logger.info(f"🛑 Stopping bot: {bot_name}")
            
            # Signal stop
            if bot_name in self.stop_events:
                self.stop_events[bot_name].set()
            
            # Wait for thread to finish
            if bot_name in self.bot_threads:
                thread = self.bot_threads[bot_name]
                thread.join(timeout=timeout)
                
                if thread.is_alive():
                    logger.warning(f"⚠️ Bot {bot_name} did not stop gracefully")
                    return False
            
            # Update status
            self.bot_statuses[bot_name].update({
                "status": "Stopped",
                "stop_time": datetime.now()
            })
            
            # Cleanup
            if bot_name in self.bots:
                del self.bots[bot_name]
            if bot_name in self.bot_threads:
                del self.bot_threads[bot_name]
            
            logger.info(f"✅ Bot {bot_name} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to stop bot {bot_name}: {e}")
            return False
    
    def stop_all_bots(self, timeout: int = 30) -> bool:
        """
        Stop all running bots
        
        Args:
            timeout: Seconds to wait for each bot
        
        Returns:
            True if all stopped successfully
        """
        logger.info("🛑 Stopping all bots...")
        
        all_stopped = True
        for bot_name in list(self.bots.keys()):
            if not self.stop_bot(bot_name, timeout):
                all_stopped = False
        
        if all_stopped:
            logger.info("✅ All bots stopped successfully")
        else:
            logger.warning("⚠️ Some bots did not stop gracefully")
        
        return all_stopped
    
    def restart_bot(self, bot_name: str, config: Dict) -> bool:
        """
        Restart a specific bot
        
        Args:
            bot_name: Bot identifier
            config: Bot configuration
        
        Returns:
            True if restarted successfully
        """
        logger.info(f"🔄 Restarting bot: {bot_name}")
        
        # Stop if running
        if bot_name in self.bots:
            if not self.stop_bot(bot_name):
                return False
        
        # Start again
        return self.start_bot(bot_name, config)
    
    def get_bot_status(self, bot_name: str) -> Dict:
        """Get status of a specific bot"""
        return dict(self.bot_statuses.get(bot_name, {}))
    
    def get_all_statuses(self) -> Dict[str, Dict]:
        """Get status of all bots"""
        return {name: dict(status) for name, status in self.bot_statuses.items()}
    
    def is_bot_running(self, bot_name: str) -> bool:
        """Check if a bot is running"""
        return (
            bot_name in self.bots and 
            bot_name in self.bot_threads and 
            self.bot_threads[bot_name].is_alive()
        )
    
    def get_active_bots(self) -> list:
        """Get list of active bot names"""
        return [
            name for name in self.bots.keys() 
            if self.is_bot_running(name)
        ]
    
    def add_bot_log(self, bot_name: str, message: str, level: str = "info"):
        """
        Add log entry to bot status
        
        Args:
            bot_name: Bot identifier
            message: Log message
            level: Log level (info, success, warning, error)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        
        # Keep last 50 logs
        logs = self.bot_statuses[bot_name]["logs"]
        logs.append(log_entry)
        if len(logs) > 50:
            logs.pop(0)
    
    def update_bot_status(
        self, 
        bot_name: str, 
        status: str, 
        unread_count: int = None
    ):
        """
        Update bot status
        
        Args:
            bot_name: Bot identifier
            status: Status string
            unread_count: Optional unread message count
        """
        self.bot_statuses[bot_name]["status"] = status
        
        if unread_count is not None:
            self.bot_statuses[bot_name]["unread_count"] = unread_count
    
    def increment_processed_count(self, bot_name: str):
        """Increment processed message count for a bot"""
        self.bot_statuses[bot_name]["processed_count"] += 1
