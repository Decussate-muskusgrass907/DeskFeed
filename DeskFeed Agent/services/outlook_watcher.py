import win32com.client
import pythoncom
import time
from datetime import datetime
from .logger import setup_logger

logger = setup_logger()

class OutlookWatcher:
    def __init__(self, poll_interval=3):
        self.poll_interval = poll_interval
        self.last_email_time = None
        self.outlook = None
        self.namespace = None
        self.inbox = None
        self._initialize_outlook()

    def _initialize_outlook(self):
        try:
            pythoncom.CoInitialize()
            self.outlook = win32com.client.Dispatch("Outlook.Application")
            self.namespace = self.outlook.GetNamespace("MAPI")
            self.inbox = self.namespace.GetDefaultFolder(6)
            logger.info("Outlook initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Outlook: {e}")
            logger.warning("Outlook alerts will be disabled. Install Outlook or check permissions.")

    def check_for_new_email(self):
        if not self.outlook or not self.inbox:
            return None

        try:
            messages = self.inbox.Items
            messages.Sort("[ReceivedTime]", True)
            latest = messages.GetFirst()

            if latest is None:
                return None

            received_time = latest.ReceivedTime
            if isinstance(received_time, str):
                from datetime import datetime
                received_time = datetime.strptime(received_time[:19], '%Y-%m-%d %H:%M:%S')

            if self.last_email_time is None:
                self.last_email_time = received_time
                return None

            if received_time > self.last_email_time:
                self.last_email_time = received_time
                return {
                    'subject': latest.Subject,
                    'sender': latest.SenderName or latest.SenderEmailAddress or 'Unknown',
                    'timestamp': received_time.isoformat() if hasattr(received_time, 'isoformat') else str(received_time),
                }

            return None

        except Exception as e:
            logger.error(f"Error checking Outlook: {e}")
            return None
