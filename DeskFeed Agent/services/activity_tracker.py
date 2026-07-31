import psutil
import win32gui
import win32process
import re
from datetime import datetime
from .logger import setup_logger

logger = setup_logger()

class ActivityTracker:
    def __init__(self):
        self.last_active_window = None
        self.browser_patterns = {
            'chrome.exe': r'^(.*?)\s*-\s*(Google Chrome|Chrome)$',
            'msedge.exe': r'^(.*?)\s*-\s*(Microsoft Edge|Edge)$',
            'firefox.exe': r'^(.*?)\s*[-–]\s*(Mozilla Firefox|Firefox)$',
            'opera.exe': r'^(.*?)\s*[-–]\s*(Opera)$',
            'brave.exe': r'^(.*?)\s*[-–]\s*(Brave)$',
        }

    def get_active_window_info(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            window_title = win32gui.GetWindowText(hwnd)

            try:
                process = psutil.Process(pid)
                app_name = process.name()
                exe_path = process.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                app_name = "Unknown"
                exe_path = ""

            return {
                'appName': app_name,
                'windowTitle': window_title,
                'pid': pid,
                'exePath': exe_path,
            }
        except Exception as e:
            logger.error(f"Error getting active window: {e}")
            return None

    def extract_browser_url(self, window_title, app_name):
        app_lower = app_name.lower()
        if 'chrome' in app_lower or 'edge' in app_lower or 'firefox' in app_lower:
            patterns = [
                r'https?://[^\s]+',
                r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[^\s]*)?',
            ]
            for pattern in patterns:
                match = re.search(pattern, window_title)
                if match:
                    return match.group(0)
        return None

    def extract_folder_path(self, window_title, app_name):
        if 'explorer' in app_name.lower() or 'explorer.exe' in app_name.lower():
            path_match = re.search(r'[A-Za-z]:\\(?:[^\\]+\\)*[^\\]*', window_title)
            if path_match:
                return path_match.group(0)

            folder_match = re.search(r'^(.*?)\s*$', window_title.strip())
            if folder_match and '\\' not in window_title:
                return None
        return None

    def get_current_activity(self):
        win_info = self.get_active_window_info()
        if not win_info:
            return None

        app_name = win_info['appName']
        window_title = win_info['windowTitle']

        activity = {
            'appName': app_name,
            'windowTitle': window_title,
            'browserUrl': None,
            'folderPath': None,
            'timestamp': datetime.now().isoformat(),
        }

        browser_url = self.extract_browser_url(window_title, app_name)
        if browser_url:
            activity['browserUrl'] = browser_url

        folder_path = self.extract_folder_path(window_title, app_name)
        if folder_path:
            activity['folderPath'] = folder_path

        return activity
