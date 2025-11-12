"""
WhatsApp Web Automation - Selenium-based WhatsApp interaction
"""

import os
import time
import threading
from datetime import datetime
from typing import List, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    StaleElementReferenceException,
    NoSuchElementException
)

from src.bot.message_processor import MessageProcessor
from src.database.student_repository import StudentRepository
from src.utils.logger import setup_logger
from src.utils.message_helpers import extract_contact_name, is_unsaved_contact

logger = setup_logger("whatsapp_automation")


class WhatsAppBot:
    """WhatsApp Web automation bot"""
    
    def __init__(
        self, 
        bot_name: str,
        user_data_path: str,
        stop_event: threading.Event,
        bot_statuses: dict
    ):
        self.bot_name = bot_name
        self.user_data_path = user_data_path
        self.stop_event = stop_event
        self.bot_statuses = bot_statuses
        
        self.driver = None
        self.message_processor = MessageProcessor()
        self.student_repo = StudentRepository()
        
        # Configuration
        self.chrome_driver_path = os.getenv("CHROME_DRIVER_PATH")
        self.timeout = int(os.getenv("TIMEOUT_SECONDS", "300"))
        self.idle_interval = int(os.getenv("IDLE_CHECK_INTERVAL_SECONDS", "10"))
    
    def is_running(self) -> bool:
        """Check if bot is running"""
        return self.driver is not None and not self.stop_event.is_set()
    
    def run(self):
        """Main bot execution loop"""
        try:
            logger.info(f"🚀 {self.bot_name} starting...")
            self._update_status("Initializing")
            
            # Initialize WebDriver
            if not self._initialize_driver():
                logger.error(f"❌ {self.bot_name} failed to initialize driver")
                return
            
            # Navigate to WhatsApp Web
            if not self._open_whatsapp_web():
                logger.error(f"❌ {self.bot_name} failed to open WhatsApp Web")
                return
            
            # Main processing loop
            self._process_loop()
            
        except Exception as e:
            logger.error(f"❌ {self.bot_name} fatal error: {e}")
            self._update_status("Error")
        
        finally:
            self._cleanup()
    
    def _initialize_driver(self) -> bool:
        """Initialize Chrome WebDriver"""
        try:
            logger.info(f"🔧 {self.bot_name} initializing Chrome driver...")
            
            options = Options()
            options.add_argument(f"--user-data-dir={self.user_data_path}")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-notifications")
            options.add_argument("--log-level=3")
            
            # Preferences
            prefs = {
                "profile.default_content_setting_values.automatic_downloads": 1,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            options.add_experimental_option("prefs", prefs)
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            # Create service
            service = Service(self.chrome_driver_path)
            
            # Retry mechanism
            for attempt in range(3):
                try:
                    self.driver = webdriver.Chrome(service=service, options=options)
                    logger.info(f"✅ {self.bot_name} driver initialized (attempt {attempt + 1})")
                    return True
                except Exception as e:
                    logger.warning(f"⚠️ Driver init attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        time.sleep(5)
                    else:
                        raise
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Driver initialization failed: {e}")
            return False
    
    def _open_whatsapp_web(self) -> bool:
        """Navigate to WhatsApp Web and handle login"""
        try:
            logger.info(f"🌐 {self.bot_name} opening WhatsApp Web...")
            self._update_status("Opening WhatsApp Web")
            
            self.driver.get("https://web.whatsapp.com/")
            
            # Wait for page load
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.ID, "pane-side"))
                )
                logger.info(f"✅ {self.bot_name} WhatsApp Web loaded")
                return True
            
            except TimeoutException:
                # Check for QR code
                if self._handle_qr_code():
                    return True
                else:
                    logger.error(f"❌ {self.bot_name} failed to load WhatsApp Web")
                    return False
        
        except Exception as e:
            logger.error(f"❌ Error opening WhatsApp Web: {e}")
            return False
    
    def _handle_qr_code(self) -> bool:
        """Handle QR code scanning"""
        try:
            logger.info(f"🔐 {self.bot_name} checking for QR code...")
            
            qr_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//canvas[@aria-label='Scan me!'] | //div[@data-ref]//canvas"
                ))
            )
            
            if qr_element:
                self._update_status("Login Required - Scan QR Code")
                logger.warning(f"⚠️ {self.bot_name} requires QR code scan")
                
                # Wait for scan (5 minutes)
                WebDriverWait(self.driver, 300).until(
                    EC.presence_of_element_located((By.ID, "pane-side"))
                )
                
                logger.info(f"✅ {self.bot_name} QR code scanned successfully")
                return True
        
        except TimeoutException:
            logger.error(f"❌ {self.bot_name} QR code scan timeout")
            return False
        
        except NoSuchElementException:
            logger.info(f"ℹ️ {self.bot_name} no QR code found, already logged in")
            return True
        
        except Exception as e:
            logger.error(f"❌ QR code handling error: {e}")
            return False
    
    def _process_loop(self):
        """Main message processing loop"""
        logger.info(f"🔄 {self.bot_name} entering processing loop")
        
        while not self.stop_event.is_set():
            try:
                # Set filters to unread
                if not self._set_unread_filter():
                    time.sleep(5)
                    continue
                
                # Get unread chats
                unread_chats = self._get_unread_chats()
                
                if not unread_chats:
                    self._update_status("Idle - No unread messages", unread_count=0)
                    logger.info(f"📭 {self.bot_name} no unread messages")
                    
                    # Sleep with stop event check
                    for _ in range(self.idle_interval):
                        if self.stop_event.is_set():
                            break
                        time.sleep(1)
                    continue
                
                # Process each chat
                logger.info(f"🔍 {self.bot_name} found {len(unread_chats)} unread chats")
                self._update_status("Processing messages", unread_count=len(unread_chats))
                
                for chat_idx, chat_element in enumerate(unread_chats):
                    if self.stop_event.is_set():
                        logger.info(f"🛑 {self.bot_name} stop signal received")
                        break
                    
                    try:
                        self._process_chat(chat_element, chat_idx)
                    except Exception as e:
                        logger.error(f"❌ Error processing chat {chat_idx}: {e}")
                        continue
                
                # Return to chat list after processing
                self._return_to_chat_list()
                
            except Exception as e:
                logger.error(f"❌ Error in processing loop: {e}")
                time.sleep(5)
    
    def _set_unread_filter(self) -> bool:
        """Set WhatsApp filter to show only unread messages"""
        try:
            # Click 'All' filter first
            all_filter = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='all-filter']/div/div"))
            )
            all_filter.click()
            time.sleep(1)
            
            # Click 'Unread' filter
            unread_filter = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='unread-filter']/div/div"))
            )
            unread_filter.click()
            time.sleep(2)
            
            return True
        
        except Exception as e:
            logger.warning(f"⚠️ Failed to set unread filter: {e}")
            return False
    
    def _get_unread_chats(self) -> List:
        """Get list of unread chat elements"""
        try:
            chats = self.driver.find_elements(
                By.XPATH, 
                "//*[@id='pane-side']/div/div/div/div"
            )
            return chats
        
        except Exception as e:
            logger.error(f"❌ Error getting unread chats: {e}")
            return []
    
    def _process_chat(self, chat_element, chat_idx: int):
        """Process a single chat"""
        try:
            # Extract contact info
            contact_name = extract_contact_name(chat_element)
            contact_number = ''.join(filter(str.isdigit, contact_name.split('\n')[0])) or contact_name
            
            logger.info(f"📱 Processing chat {chat_idx + 1}: {contact_name}")
            
            # Check if unsaved contact
            if is_unsaved_contact(contact_name, contact_number):
                self._handle_unsaved_contact(chat_element, contact_name, contact_number)
                return
            
            # Get student details
            student_details = self.student_repo.fetch_student_details(
                contact_number, 
                contact_name
            )
            
            # Skip if no application number
            if not student_details.get("ApplicationNumber"):
                logger.info(f"⚠️ No application number for {contact_name}, skipping")
                chat_element.click()
                time.sleep(2)
                self._return_to_chat_list()
                return
            
            # Click chat to open
            chat_element.click()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//div[contains(@class, 'message-in')]"
                ))
            )
            time.sleep(2)
            
            # Get unread messages
            unread_messages = self._get_unread_messages(chat_element)
            
            if not unread_messages:
                logger.info(f"ℹ️ No unread messages in {contact_name}")
                self._return_to_chat_list()
                return
            
            # Process each message
            for msg_idx, msg_element in enumerate(unread_messages):
                if self.stop_event.is_set():
                    break
                
                self._process_message(
                    msg_element,
                    student_details,
                    contact_name,
                    msg_idx
                )
            
        except StaleElementReferenceException:
            logger.warning(f"⚠️ Stale element for chat {chat_idx}, skipping")
        except Exception as e:
            logger.error(f"❌ Error processing chat: {e}")
    
    def _handle_unsaved_contact(self, chat_element, contact_name: str, contact_number: str):
        """Handle messages from unsaved contacts"""
        try:
            chat_element.click()
            time.sleep(2)
            
            greeting = (
                "Greetings! Please confirm whether you are an existing student/graduate "
                "from Texila American University. If yes, share your application number."
            )
            
            self.send_message(greeting)
            
            # Log interaction
            self.student_repo.log_conversation(
                contact_id=contact_number,
                whatsapp_name=contact_name,
                received_message="",
                response_from_bot=greeting,
                message_type="unsaved_contact_greeting",
                category="applied",
                confidence_level=1.0,
                bot_name=self.bot_name
            )
            
            self._return_to_chat_list()
            
        except Exception as e:
            logger.error(f"❌ Error handling unsaved contact: {e}")
    
    def _get_unread_messages(self, chat_element) -> List:
        """Get unread messages from current chat"""
        try:
            # Get unread count from chat element
            unread_badge = chat_element.find_elements(
                By.XPATH, 
                ".//div[2]/div[2]/div[2]/span[1]/div/span"
            )
            
            unread_count = 0
            if unread_badge:
                text = unread_badge[0].text.strip()
                unread_count = int(text) if text.isdigit() else 0
            
            if unread_count == 0:
                return []
            
            # Get all messages
            all_messages = self.driver.find_elements(
                By.XPATH, 
                "//div[contains(@class, 'message-in')]"
            )
            
            # Return last N unread messages
            return all_messages[-unread_count:] if unread_count <= len(all_messages) else all_messages
        
        except Exception as e:
            logger.error(f"❌ Error getting unread messages: {e}")
            return []
    
    def _process_message(
        self, 
        msg_element, 
        student_details: dict,
        contact_name: str,
        msg_idx: int
    ):
        """Process a single message"""
        try:
            # Extract message text
            message_text = self._extract_message_text(msg_element)
            
            if not message_text:
                logger.warning(f"⚠️ Empty message at index {msg_idx}")
                return
            
            logger.info(f"📝 Message {msg_idx + 1}: {message_text[:50]}...")
            
            # Process with message processor
            result = self.message_processor.process_text_message(
                message=message_text,
                contact_id=student_details["ApplicationNumber"],
                contact_name=contact_name,
                salutation=student_details["Salutation"]
            )
            
            # Send response
            if result and result.get("response"):
                self.send_message(result["response"])
                
                # Log to database
                self.student_repo.log_conversation(
                    contact_id=student_details["ApplicationNumber"],
                    whatsapp_name=contact_name,
                    received_message=message_text,
                    response_from_bot=result["response"],
                    message_type=result.get("message_type", "text"),
                    category=result.get("category", "general"),
                    confidence_level=result.get("confidence", 0.0),
                    faq_question=",".join(result.get("sources", [])),
                    bot_name=self.bot_name
                )
                
                # Increment counter
                self.bot_statuses[self.bot_name]["processed_count"] += 1
        
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
    
    def _extract_message_text(self, msg_element) -> str:
        """Extract text from message element"""
        try:
            # Try multiple XPaths
            xpaths = [
                ".//span[@data-testid='msg-text']",
                ".//div[contains(@class, 'copyable-text')]/div",
                ".//span[contains(@class, 'selectable-text')]"
            ]
            
            for xpath in xpaths:
                try:
                    text_element = msg_element.find_element(By.XPATH, xpath)
                    text = text_element.text.strip()
                    if text:
                        return text
                except:
                    continue
            
            # Fallback to element text
            return msg_element.text.strip()
        
        except Exception as e:
            logger.error(f"❌ Error extracting message text: {e}")
            return ""
    
    def send_message(self, message: str) -> bool:
        """Send a WhatsApp message"""
        try:
            # Find message input box
            input_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[@contenteditable='true'][@data-tab='10']"
                ))
            )
            
            # Split long messages
            lines = message.split('\n')
            for line in lines:
                input_box.send_keys(line)
                input_box.send_keys(Keys.SHIFT + Keys.ENTER)
            
            # Send
            input_box.send_keys(Keys.ENTER)
            time.sleep(1)
            
            logger.info(f"✅ Message sent: {message[:50]}...")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return False
    
    def _return_to_chat_list(self):
        """Return to main chat list"""
        try:
            back_button = self.driver.find_element(
                By.XPATH, 
                "//span[@data-icon='back']"
            )
            back_button.click()
            time.sleep(1)
        except:
            # Alternative: press Escape
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
            except:
                pass
    
    def _update_status(self, status: str, unread_count: int = None):
        """Update bot status"""
        self.bot_statuses[self.bot_name]["status"] = status
        if unread_count is not None:
            self.bot_statuses[self.bot_name]["unread_count"] = unread_count
    
    def _cleanup(self):
        """Cleanup resources"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info(f"✅ {self.bot_name} browser closed")
        except:
            pass
        
        self._update_status("Stopped")
        self.bot_statuses[self.bot_name]["stop_time"] = datetime.now()
