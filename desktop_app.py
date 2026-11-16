import os
import sys
import time
import socket
import threading
import webbrowser
import logging

# Ensure root & backend directories are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.config import APP_DIR, BIN_DIR
from backend.main import app
import uvicorn

# ANSI colors for Windows console
if sys.platform == "win32":
    os.system("color")

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def find_free_port(start_port: int = 8000, max_tries: int = 20) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


def open_browser_delayed(url: str, delay: float = 1.5):
    """Wait briefly for Uvicorn to initialize, then open browser."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"{YELLOW}[WARN] Gagal membuka browser otomatis: {e}{RESET}")


def main():
    port = find_free_port(8000)
    app_url = f"http://localhost:{port}"

    print(f"\n{CYAN}{'='*64}{RESET}")
    print(f"{CYAN}  Literate Lamp - AI Stock Media Metadata Generator{RESET}")
    print(f"{CYAN}  Versi    : 2.0.0 (Standalone Desktop){RESET}")
    print(f"{GREEN}  URL      : {app_url}{RESET}")
    if os.path.isdir(BIN_DIR):
        print(f"{CYAN}  Binari   : Portabel ({BIN_DIR}){RESET}")
    print(f"{YELLOW}  Browser akan terbuka otomatis. Tekan Ctrl+C untuk mematikan.{RESET}")
    print(f"{CYAN}{'='*64}{RESET}\n")

    # Start browser launcher thread
    threading.Thread(target=open_browser_delayed, args=(app_url,), daemon=True).start()

    # Run Uvicorn server directly
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            log_level="info",
            access_log=False
        )
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[SYSTEM] Aplikasi dihentikan oleh pengguna.{RESET}\n")
    except Exception as e:
        print(f"\n{YELLOW}[ERROR] Gagal menjalankan server: {e}{RESET}\n")
        input("Tekan Enter untuk keluar...")


if __name__ == "__main__":
    main()

