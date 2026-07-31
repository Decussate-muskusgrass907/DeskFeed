import customtkinter as ctk
import subprocess
import threading
import queue
import json
import os
import sys
import signal
import re
import time
import socket
import zipfile
import io
import shutil
import urllib.request
import urllib.error
from pathlib import Path

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

if getattr(sys, 'frozen', False):
    EXE_DIR = Path(sys.executable).resolve().parent
    ROOT_DIR = EXE_DIR.parent.parent
    CTRL_DIR = EXE_DIR.parent
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent
    CTRL_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "DeskFeed Backend"
AGENT_DIR = ROOT_DIR / "DeskFeed Agent"
NGROK_DIR = CTRL_DIR / "ngrok"
NGROK_EXE = NGROK_DIR / "ngrok.exe"
CONFIG_PATH = CTRL_DIR / "config.json"

NGROK_DOWNLOAD = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"

def _detect_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def _get_python_path():
    if not getattr(sys, 'frozen', False):
        return sys.executable
    for p in [r"C:\Program Files\Python314\python.exe",
              r"C:\Program Files\Python313\python.exe",
              r"C:\Python314\python.exe",
              r"C:\Python313\python.exe",
              shutil.which("python"),
              shutil.which("python.exe")]:
        if p and os.path.exists(p):
            return p
    return "python.exe"

def _get_config(key, default=None):
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                return json.load(f).get(key, default)
        except Exception:
            pass
    return default

def _save_config(**kwargs):
    cfg = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
        except Exception:
            pass
    cfg.update(kwargs)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def _ensure_ngrok():
    if NGROK_EXE.exists():
        return True
    NGROK_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = NGROK_DIR / "ngrok.zip"
    try:
        resp = urllib.request.urlopen(NGROK_DOWNLOAD, timeout=30)
        with open(zip_path, "wb") as f:
            f.write(resp.read())
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(NGROK_DIR)
        zip_path.unlink()
        return NGROK_EXE.exists()
    except Exception:
        if zip_path.exists():
            zip_path.unlink()
        return False

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DeskFeed Controller")
        self.geometry("740x660")
        self.minsize(700, 600)
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.processes = {}
        self.proc_info = {}
        self.log_queue = queue.Queue()
        self.running = False
        self.auto_scroll = True
        self.tunnel_url = None
        self.ngrok_ready = NGROK_EXE.exists()
        self.ngrok_token = _get_config("ngrok_token", "")

        self._build_ui()
        self._poll_logs()
        self._update_uptime_loop()
        self.after(3000, self._poll_processes)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, pady=(15, 5), padx=20, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(header, text="DeskFeed Controller",
                     font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="by Mohammad Liaquat Ali",
                     font=ctk.CTkFont(size=11), text_color="#888").grid(row=1, column=0, sticky="w")
        self.status_badge = ctk.CTkLabel(header, text=" ● Stopped ",
                                          font=ctk.CTkFont(size=12),
                                          fg_color="#3d1a1a", text_color="#e74c3c", corner_radius=8)
        self.status_badge.grid(row=0, column=1, padx=(10, 0), sticky="e")

        self.tab_view = ctk.CTkTabview(self, segmented_button_font=ctk.CTkFont(size=13))
        self.tab_view.grid(row=1, column=0, pady=(10, 0), padx=15, sticky="nsew")
        self._build_dashboard_tab()
        self._build_pairing_tab()
        self._build_console_tab()

    def _build_dashboard_tab(self):
        tab = self.tab_view.add("  Dashboard  ")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Server Control", font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, pady=(12, 4), padx=10, sticky="w")

        ctrl = ctk.CTkFrame(tab)
        ctrl.grid(row=1, column=0, pady=(0, 8), padx=10, sticky="ew")
        ctrl.grid_columnconfigure(1, weight=1)

        self.toggle_btn = ctk.CTkButton(ctrl, text="  Start Servers  ",
                                         command=self._toggle_servers, height=42,
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         fg_color="#1a7a2e", hover_color="#145c22")
        self.toggle_btn.grid(row=0, column=0, padx=(12, 15), pady=12, sticky="w")

        info = ctk.CTkFrame(ctrl, fg_color="transparent")
        info.grid(row=0, column=1, pady=8, sticky="ew")
        info.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(info, text="Status:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w")
        self.status_text = ctk.CTkLabel(info, text="All stopped", font=ctk.CTkFont(size=12))
        self.status_text.grid(row=0, column=1, padx=(5, 0), sticky="w")
        ctk.CTkLabel(info, text="Uptime:", font=ctk.CTkFont(size=12)).grid(row=1, column=0, sticky="w")
        self.uptime_label = ctk.CTkLabel(info, text="--", font=ctk.CTkFont(size=12))
        self.uptime_label.grid(row=1, column=1, padx=(5, 0), sticky="w")
        self._start_time = None

        sep = ctk.CTkFrame(tab, height=1, fg_color="#333")
        sep.grid(row=2, column=0, pady=4, padx=10, sticky="ew")

        ctk.CTkLabel(tab, text="Tunnel (Remote Access)", font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=3, column=0, pady=(8, 4), padx=10, sticky="w")

        tun_frame = ctk.CTkFrame(tab)
        tun_frame.grid(row=4, column=0, pady=(0, 8), padx=10, sticky="ew")
        tun_frame.grid_columnconfigure(2, weight=1)

        self.tun_btn = ctk.CTkButton(tun_frame, text=" Start Tunnel ",
                                       command=self._toggle_tunnel, height=34,
                                       font=ctk.CTkFont(size=12),
                                       fg_color="#8e44ad", hover_color="#6c3483")
        self.tun_btn.grid(row=0, column=0, padx=(10, 6), pady=8)

        self.tun_dot = ctk.CTkLabel(tun_frame, text="●", font=ctk.CTkFont(size=16), text_color="#555")
        self.tun_dot.grid(row=0, column=1, padx=2)

        self.tun_status = ctk.CTkLabel(tun_frame, text="Not started", font=ctk.CTkFont(size=11), text_color="#888")
        self.tun_status.grid(row=0, column=2, sticky="w")

        self.tun_url_label = ctk.CTkLabel(tun_frame, text="", font=ctk.CTkFont(size=11))
        self.tun_url_label.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 6), sticky="w")

        if not self.ngrok_ready:
            self.tun_btn.configure(state="disabled", text=" ngrok missing ")
            ctk.CTkLabel(tun_frame, text="Click 'Setup Tunnel' to download ngrok",
                         font=ctk.CTkFont(size=10), text_color="#e74c3c"
                         ).grid(row=2, column=0, columnspan=3, padx=10, pady=(0, 6), sticky="w")

        sep2 = ctk.CTkFrame(tab, height=1, fg_color="#333")
        sep2.grid(row=5, column=0, pady=4, padx=10, sticky="ew")

        ctk.CTkLabel(tab, text="Service Status", font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=6, column=0, pady=(4, 4), padx=10, sticky="sw")

        cards = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        cards.grid(row=7, column=0, pady=(0, 10), padx=10, sticky="nsew")
        cards.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(7, weight=1)

        self.creds_poller = None
        self.cards = {}
        for key, label, check_file in [
            ("backend", "Backend", BACKEND_DIR / "package.json"),
            ("agent", "Agent", AGENT_DIR / "main.py"),
            ("tunnel", "Tunnel", NGROK_EXE),
        ]:
            card = ctk.CTkFrame(cards, height=32)
            card.grid(row=len(self.cards), column=0, pady=2, sticky="ew")
            card.grid_columnconfigure(2, weight=1)
            card.grid_propagate(False)
            dot = ctk.CTkLabel(card, text="●", font=ctk.CTkFont(size=14), text_color="#555")
            dot.grid(row=0, column=0, padx=(8, 4))
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12, weight="bold")
                         ).grid(row=0, column=1, padx=(0, 6), sticky="w")
            sl = ctk.CTkLabel(card, text="Stopped", font=ctk.CTkFont(size=11), text_color="#888")
            sl.grid(row=0, column=2, sticky="w")
            pl = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=9), text_color="#666")
            pl.grid(row=0, column=3, padx=(0, 6), sticky="e")
            exists = check_file.exists()
            ctk.CTkLabel(card, text="✓" if exists else "✗",
                         font=ctk.CTkFont(size=11),
                         text_color="#2ecc71" if exists else "#e74c3c"
                         ).grid(row=0, column=4, padx=(0, 8))
            self.cards[key] = {"dot": dot, "status": sl, "pid": pl}

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=8, column=0, pady=(0, 8), padx=10, sticky="ew")
        self.setup_btn = None
        self.auth_btn = None
        if not self.ngrok_ready:
            self.setup_btn = ctk.CTkButton(btn_frame, text=" Setup Tunnel (ngrok) ",
                                            command=self._setup_ngrok, height=32,
                                            font=ctk.CTkFont(size=11))
            self.setup_btn.grid(row=0, column=0, padx=4)
        if not self.ngrok_token:
            self.auth_btn = ctk.CTkButton(btn_frame, text=" Set ngrok Auth Token ",
                                           command=self._prompt_token, height=32,
                                           font=ctk.CTkFont(size=11))
            self.auth_btn.grid(row=0, column=1, padx=4)

    def _build_pairing_tab(self):
        tab = self.tab_view.add("  Pairing Info  ")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Mobile App Pairing Info", font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, pady=(15, 4), padx=10, sticky="w")
        ctk.CTkLabel(tab, text="Start servers and tunnel, then copy these to the mobile app.",
                     font=ctk.CTkFont(size=12), text_color="#999"
                     ).grid(row=1, column=0, pady=(0, 12), padx=10, sticky="w")

        box = ctk.CTkFrame(tab)
        box.grid(row=2, column=0, pady=(0, 12), padx=30, sticky="ew")
        box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(box, text="Server URL", font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=0, column=0, padx=(15, 8), pady=(14, 4), sticky="w")
        self.pair_url = ctk.CTkEntry(box, font=ctk.CTkFont(size=13), height=30)
        self.pair_url.grid(row=0, column=1, padx=(0, 10), pady=(12, 2), sticky="ew")
        self.pair_url.insert(0, f"http://{_detect_ip()}:3000")

        ctk.CTkLabel(box, text="Device ID", font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=1, column=0, padx=(15, 8), pady=4, sticky="w")
        self.pair_devid = ctk.CTkEntry(box, font=ctk.CTkFont(size=13), height=30)
        self.pair_devid.grid(row=1, column=1, padx=(0, 10), pady=(2, 4), sticky="ew")
        self.pair_devid.insert(0, "—")

        ctk.CTkLabel(box, text="Pairing PIN", font=ctk.CTkFont(size=12, weight="bold")
                     ).grid(row=2, column=0, padx=(15, 8), pady=4, sticky="w")
        self.pair_pin = ctk.CTkEntry(box, font=ctk.CTkFont(size=16, weight="bold"), height=30)
        self.pair_pin.grid(row=2, column=1, padx=(0, 10), pady=(2, 4), sticky="ew")
        self.pair_pin.insert(0, "—")

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=3, column=0, pady=10, padx=10)
        self.gen_btn = ctk.CTkButton(btn_frame, text=" Generate Credentials ",
                                       command=self._generate_credentials, height=34,
                                       font=ctk.CTkFont(size=12),
                                       fg_color="#1a7a2e", hover_color="#145c22")
        self.gen_btn.grid(row=0, column=0, padx=4)
        self.copy_btn = ctk.CTkButton(btn_frame, text=" Copy to Clipboard ",
                                        command=self._copy_pairing_info, height=34,
                                        font=ctk.CTkFont(size=12))
        self.copy_btn.grid(row=0, column=1, padx=4)

        self.pair_status = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=12))
        self.pair_status.grid(row=4, column=0, pady=4)
        ctk.CTkLabel(tab, text="Step 1: Start Servers & Tunnel on Dashboard\nStep 2: Click 'Generate Credentials'\nStep 3: Copy and paste into mobile app settings",
                     font=ctk.CTkFont(size=11), text_color="#666", justify="left"
                     ).grid(row=5, column=0, pady=(8, 0), padx=40, sticky="w")

    def _build_console_tab(self):
        tab = self.tab_view.add("  Console  ")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, pady=(8, 4), padx=5, sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(toolbar, text="Live Process Logs", font=ctk.CTkFont(size=14, weight="bold")
                     ).grid(row=0, column=0, sticky="w")
        self.auto_scroll_btn = ctk.CTkSwitch(toolbar, text="Auto-scroll", onvalue=True, offvalue=False,
                                              command=lambda: setattr(self, 'auto_scroll', self.auto_scroll_btn.get()),
                                              switch_width=36, font=ctk.CTkFont(size=11))
        self.auto_scroll_btn.select()
        self.auto_scroll_btn.grid(row=0, column=1, padx=6)
        ctk.CTkButton(toolbar, text="Clear", width=60, height=26, font=ctk.CTkFont(size=11),
                       command=self._clear_logs, fg_color="#444", hover_color="#555"
                       ).grid(row=0, column=2, padx=4)
        self.log_text = ctk.CTkTextbox(tab, wrap="word", state="disabled",
                                        font=ctk.CTkFont(size=11), spacing3=1)
        self.log_text.grid(row=1, column=0, pady=(0, 12), padx=5, sticky="nsew")
        self.log_text.tag_config("info", foreground="#aaa")
        self.log_text.tag_config("ok", foreground="#2ecc71")
        self.log_text.tag_config("err", foreground="#e74c3c")
        self.log_text.tag_config("warn", foreground="#f39c12")

    def _log(self, msg, tag=None):
        self.log_queue.put((msg, tag))

    def _write_log(self, msg, tag=None):
        self.log_text.configure(state="normal")
        if tag:
            self.log_text.insert("end", msg + "\n", tag)
        else:
            self.log_text.insert("end", msg + "\n")
        if self.auto_scroll:
            self.log_text.see("end")
        self.log_text.configure(state="disabled")
        m = re.search(r'Device registered! ID:\s*(\S+)', msg)
        if m:
            self._set_pairing_info(device_id=m.group(1))
        m = re.search(r'PAIRING PIN:\s*(\d{6})', msg)
        if m:
            self._set_pairing_info(pairing_pin=m.group(1))

    def _clear_logs(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("0.0", "end")
        self.log_text.configure(state="disabled")
        self._log("Console cleared", "info")

    def _poll_logs(self):
        while not self.log_queue.empty():
            try:
                m, t = self.log_queue.get_nowait()
                self._write_log(m, t)
            except queue.Empty:
                break
        self.after(100, self._poll_logs)

    def _update_uptime_loop(self):
        if self.running and self._start_time:
            e = int(time.time() - self._start_time)
            h, r = divmod(e, 3600)
            m, s = divmod(r, 60)
            self.uptime_label.configure(text=f"{h}h {m}m {s}s" if h else f"{m}m {s}s")
        self.after(1000, self._update_uptime_loop)

    def _poll_processes(self):
        for key in list(self.processes.keys()):
            proc = self.processes[key]
            if proc and proc.poll() is not None:
                self._log(f"[{key}] Process died unexpectedly (exit code: {proc.returncode})", "err")
                del self.processes[key]
                self._update_card(key, False)
        self.after(3000, self._poll_processes)

    def _update_status(self, running, detail=""):
        self.running = running
        if running:
            self.status_badge.configure(text=" ● Running ", fg_color="#1a3d1a", text_color="#2ecc71")
            self.toggle_btn.configure(text="  Stop Servers  ", fg_color="#c0392b", hover_color="#962d22")
        else:
            self.status_badge.configure(text=" ● Stopped ", fg_color="#3d1a1a", text_color="#e74c3c")
            self.toggle_btn.configure(text="  Start Servers  ", fg_color="#1a7a2e", hover_color="#145c22")
        self.status_text.configure(text=detail)

    def _update_card(self, key, active, pid=None):
        c = self.cards.get(key)
        if not c:
            return
        if active:
            c["dot"].configure(text_color="#2ecc71")
            c["status"].configure(text="Running", text_color="#2ecc71")
            c["pid"].configure(text=f"PID: {pid}" if pid else "")
        else:
            c["dot"].configure(text_color="#555")
            c["status"].configure(text="Stopped", text_color="#888")
            c["pid"].configure(text="")

    def _set_pairing_info(self, device_id=None, pairing_pin=None):
        if device_id:
            self.pair_devid.delete(0, "end")
            self.pair_devid.insert(0, device_id)
        if pairing_pin:
            self.pair_pin.delete(0, "end")
            self.pair_pin.insert(0, pairing_pin)
            self.pair_status.configure(text="Pairing info detected! Copy it to your mobile app.", text_color="#2ecc71")

    def _copy_pairing_info(self):
        url = self.tunnel_url or self.pair_url.get()
        did = self.pair_devid.get()
        pin = self.pair_pin.get()
        if did == "—" or pin == "—":
            self.pair_status.configure(text="Generate credentials first", text_color="#f39c12")
            return
        text = f"Server URL: {url}\nDevice ID: {did}\nPairing PIN: {pin}"
        self.clipboard_clear()
        self.clipboard_append(text)
        self.pair_status.configure(text="Copied to clipboard ✅", text_color="#2ecc71")
        self._log("Pairing info copied to clipboard", "ok")

    def _wait_for_creds(self, tries=0):
        creds_path = CTRL_DIR / "credentials.json"
        if creds_path.exists():
            try:
                with open(creds_path) as f:
                    data = json.load(f)
                if data.get("deviceId") and data.get("pairingPin"):
                    self._set_pairing_info(device_id=data["deviceId"], pairing_pin=data["pairingPin"])
                    self._log("[ctrl] Agent credentials detected — auto-populated Pairing Info", "ok")
                    return
            except Exception:
                pass
        if tries < 15 and self.running:
            self.after(2000, lambda: self._wait_for_creds(tries + 1))
        elif tries >= 15:
            self._log("[ctrl] Agent did not register within 30s. Check Console tab for errors.", "err")

    def _generate_credentials(self):
        creds_path = CTRL_DIR / "credentials.json"
        if creds_path.exists():
            try:
                with open(creds_path) as f:
                    data = json.load(f)
                did = data.get("deviceId", "")
                pin = data.get("pairingPin", "")
                if did and pin:
                    self._set_pairing_info(device_id=did, pairing_pin=pin)
                    self.pair_status.configure(text="Credentials loaded! Copy to mobile app.", text_color="#2ecc71")
                    self._log(f"[ctrl] Device ID: {did}  PIN: {pin}", "ok")
                    return
            except Exception as e:
                self._log(f"[ctrl] Error reading creds file: {e}", "err")

        if not self.running:
            self.pair_status.configure(text="Start servers on Dashboard tab first", text_color="#f39c12")
            return

        base = self.tunnel_url or self.pair_url.get()
        base = base.rstrip("/")
        url = f"{base}/api/auth/register-device"
        body = json.dumps({"name": "DeskFeed-Viewer"}).encode()
        self.pair_status.configure(text="Registering via backend...", text_color="#f39c12")
        self._log(f"[ctrl] Fallback: registering device via backend...", "info")
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                did = data.get("deviceId", "")
                pin = data.get("pairingPin", "")
                if did and pin:
                    self._set_pairing_info(device_id=did, pairing_pin=pin)
                    self.pair_status.configure(text="Credentials generated! Copy to mobile app.", text_color="#2ecc71")
                    self._log(f"[ctrl] Device ID: {did}  PIN: {pin}", "ok")
                else:
                    self.pair_status.configure(text="Unexpected response", text_color="#e74c3c")
        except urllib.error.HTTPError as e:
            self.pair_status.configure(text=f"HTTP {e.code}", text_color="#e74c3c")
            self._log(f"[ctrl] HTTP {e.code}: {e.read().decode()}", "err")
        except urllib.error.URLError as e:
            self.pair_status.configure(text=f"Cannot reach backend at {base}", text_color="#e74c3c")
            self._log(f"[ctrl] {e.reason}", "err")
        except Exception as e:
            self.pair_status.configure(text=str(e)[:50], text_color="#e74c3c")
            self._log(f"[ctrl] {e}", "err")

    def _setup_ngrok(self):
        self._log("[ctrl] Downloading ngrok... (check Console tab)", "info")
        if self.setup_btn:
            self.setup_btn.configure(state="disabled", text=" Downloading... ")
        threading.Thread(target=self._download_ngrok, daemon=True).start()

    def _download_ngrok(self):
        ok = _ensure_ngrok()
        self.after(0, lambda: self._on_ngrok_downloaded(ok))

    def _on_ngrok_downloaded(self, ok):
        if ok:
            self.ngrok_ready = True
            self._log("[ctrl] ngrok downloaded successfully!", "ok")
            self.tun_btn.configure(state="normal", text=" Start Tunnel ")
            if self.setup_btn:
                self.setup_btn.configure(text=" ngrok Ready ✓ ", state="disabled",
                                         fg_color="#2c3e50")
        else:
            self._log("[ctrl] Failed to download ngrok. Try manually from https://ngrok.com/download", "err")
            if self.setup_btn:
                self.setup_btn.configure(text=" Retry Download ", state="normal")

    def _prompt_token(self):
        dlg = ctk.CTkInputDialog(text="Enter your ngrok auth token\n(Get one free at https://dashboard.ngrok.com/signup)", title="ngrok Auth Token")
        token = dlg.get_input()
        if token and token.strip():
            self.ngrok_token = token.strip()
            _save_config(ngrok_token=self.ngrok_token)
            subprocess.run([str(NGROK_EXE), "config", "add-authtoken", self.ngrok_token],
                           capture_output=True, cwd=str(NGROK_DIR))
            self._log("[ctrl] ngrok auth token saved", "ok")

    def _toggle_tunnel(self):
        if "tunnel" in self.processes:
            self._stop_process("tunnel")
            self.tun_dot.configure(text_color="#555")
            self.tun_status.configure(text="Stopped")
            self.tun_url_label.configure(text="")
            self.tun_btn.configure(text=" Start Tunnel ")
        else:
            self._start_ngrok()

    def _start_ngrok(self):
        if not self.ngrok_ready:
            self._log("[tunnel] ngrok not installed. Click 'Setup Tunnel (ngrok)'", "err")
            return
        if not self.ngrok_token:
            self._log("[tunnel] ngrok auth token required", "warn")
            self._prompt_token()
            if not self.ngrok_token:
                return
        self._log("[tunnel] Starting ngrok tunnel on port 3000...", "info")
        ok = self._start_process("tunnel", NGROK_DIR,
                                 f'"{NGROK_EXE}" http 3000 --log=stdout')
        if ok:
            self.tun_btn.configure(text=" Stop Tunnel ")
            self.tun_dot.configure(text_color="#f39c12")
            self.tun_status.configure(text="Connecting...")
            self.after(2000, self._poll_ngrok_url)

    def _poll_ngrok_url(self):
        if "tunnel" not in self.processes:
            return
        try:
            req = urllib.request.Request("http://127.0.0.1:4040/api/tunnels")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                for t in data.get("tunnels", []):
                    if t.get("public_url", "").startswith("https"):
                        self.tunnel_url = t["public_url"]
                        self.pair_url.delete(0, "end")
                        self.pair_url.insert(0, self.tunnel_url)
                        self.tun_dot.configure(text_color="#2ecc71")
                        self.tun_status.configure(text="Online")
                        self.tun_url_label.configure(
                            text=f"Tunnel URL: {self.tunnel_url}",
                            text_color="#2ecc71")
                        self._log(f"[tunnel] Online: {self.tunnel_url}", "ok")
                        return
        except Exception:
            pass
        self.after(2000, self._poll_ngrok_url)

    def _reader_thread(self, pipe, label):
        try:
            for line in iter(pipe.readline, ""):
                if not line:
                    break
                text = line.rstrip("\n\r")
                if text:
                    tag = "err" if any(w in text.lower() for w in ["error", "fail", "warn"]) else None
                    self._log(f"[{label}] {text}", tag)
        except Exception as e:
            self._log(f"[{label}] Reader error: {e}", "err")
        finally:
            try:
                pipe.close()
            except Exception:
                pass

    def _start_process(self, key, cwd, command, shell=True, env=None):
        try:
            proc = subprocess.Popen(
                command, cwd=str(cwd), shell=shell,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            self.processes[key] = proc
            self.proc_info[key] = {"pid": proc.pid, "start": time.time()}
            self._update_card(key, True, proc.pid)
            t = threading.Thread(target=self._reader_thread, args=(proc.stdout, key), daemon=True)
            t.start()
            self._log(f"[{key}] Started (PID: {proc.pid})", "ok")
            return True
        except Exception as e:
            self._log(f"[{key}] Failed: {e}", "err")
            self._update_card(key, False)
            return False

    def _stop_process(self, key):
        proc = self.processes.pop(key, None)
        if proc is None:
            return
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                               capture_output=True, timeout=5)
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=5)
            self._log(f"[{key}] Terminated (PID: {proc.pid})", "warn")
        except Exception as e:
            self._log(f"[{key}] Kill error: {e}", "err")
            try:
                proc.kill()
                proc.wait(timeout=3)
            except Exception:
                pass
        self._update_card(key, False)
        if key == "tunnel":
            self.tunnel_url = None
            self.tun_dot.configure(text_color="#555")
            self.tun_status.configure(text="Stopped")
            self.tun_url_label.configure(text="")
            self.tun_btn.configure(text=" Start Tunnel ")

    def _toggle_servers(self):
        if self.running:
            self._stop_all()
        else:
            self._start_all()

    def _wait_backend_ready(self, python, env, results):
        """Poll backend health endpoint in a thread, then start agent once it responds."""
        def poll():
            for attempt in range(30):
                try:
                    req = urllib.request.Request("http://localhost:3000/api/health", method="GET")
                    with urllib.request.urlopen(req, timeout=2) as resp:
                        if resp.status == 200:
                            self.after(0, lambda a=attempt: self._on_backend_ready(python, env, results, a))
                            return
                except Exception:
                    pass
                self.after(0, lambda a=attempt: self._log(f"[health] Waiting for backend... ({a + 1}/30)", "info"))
                time.sleep(2)
            self.after(0, lambda: self._log("[health] Backend not ready after 60s. Starting agent anyway.", "warn"))
            self.after(0, lambda: self._on_backend_ready(python, env, results, -1))
        threading.Thread(target=poll, daemon=True).start()

    def _on_backend_ready(self, python, env, results, attempt):
        if attempt >= 0:
            self._log(f"[health] Backend ready after ~{(attempt + 1) * 2}s", "ok")
        if AGENT_DIR.exists() and (AGENT_DIR / "main.py").exists():
            env["PYTHONUNBUFFERED"] = "1"
            results.append(("Agent", self._start_process("agent", AGENT_DIR,
                                                          f'"{python}" main.py', env=env)))
        else:
            self._log("[agent] Skipped", "warn")
        ok = sum(1 for _, v in results if v)
        if ok:
            self._update_status(True, f"{ok}/{len(results)} running")
            self._log(f"Servers running ({ok}/{len(results)})", "ok")
        else:
            self._log("No servers started", "err")
        self._log("=" * 44, "info")
        if "tunnel" not in self.processes:
            self._log("Auto-starting tunnel for remote access...", "info")
            self._start_ngrok()
        self.after(2000, self._wait_for_creds)

    def _start_all(self):
        self._log("=" * 44, "info")
        self._log("Starting servers...", "info")
        self._start_time = time.time()
        results = []
        if BACKEND_DIR.exists() and (BACKEND_DIR / "package.json").exists():
            npm_cmd = shutil.which("npm") or shutil.which("npm.cmd") or "npm"
            be_env = os.environ.copy()
            node_dir = r"C:\Program Files\nodejs"
            if os.path.isdir(node_dir) and node_dir not in be_env.get("PATH", ""):
                be_env["PATH"] = node_dir + ";" + be_env.get("PATH", "")
            results.append(("Backend", self._start_process("backend", BACKEND_DIR, f'"{npm_cmd}" start', env=be_env)))
        else:
            self._log("[backend] Skipped", "warn")
        python = _get_python_path()
        env = os.environ.copy()
        self.after(1000, lambda: self._wait_backend_ready(python, env, results))

    def _stop_all(self):
        self._log("Stopping all processes...", "info")
        for key in list(self.processes.keys()):
            self._stop_process(key)
        self._update_status(False, "All stopped")
        self._start_time = None
        self.uptime_label.configure(text="--")
        self._log("All processes stopped", "warn")
        self._log("=" * 44, "info")

    def _on_close(self):
        self._stop_all()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
