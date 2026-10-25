import os
import sys
import time
import subprocess
import threading
import webbrowser

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

# ANSI color codes for single terminal output
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Enable VT100 colors in Windows console
if sys.platform == "win32":
    os.system("color")

def stream_logs(pipe, tag, color):
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            # Clean trailing newline and print with tag
            clean_line = line.rstrip("\r\n")
            print(f"{color}[{tag}]{RESET} {clean_line}", flush=True)
    except Exception:
        pass

def kill_process_tree(pid: int):
    if not pid:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(
                f"taskkill /F /T /PID {pid}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            os.killpg(os.getpgid(pid), 9)
    except Exception:
        pass

def main():
    print(f"\n{CYAN}{'='*62}{RESET}")
    print(f"{CYAN}  Literate Lamp - All-in-One Console{RESET}")
    print(f"{CYAN}  Backend  : http://localhost:8000{RESET}")
    print(f"{CYAN}  Frontend : http://localhost:5173{RESET}")
    print(f"{YELLOW}  Tekan Ctrl+C di jendela ini untuk mematikan semua layanan{RESET}")
    print(f"{CYAN}{'='*62}{RESET}\n")

    # 1. Start Backend
    print(f"{BLUE}[SYSTEM] Memulai Backend (FastAPI + Uvicorn)...{RESET}")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )

    # 2. Start Frontend
    print(f"{MAGENTA}[SYSTEM] Memulai Frontend (Vite + React)...{RESET}")
    npm_bin = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_proc = subprocess.Popen(
        [npm_bin, "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )

    # Start threads to stream logs to this single console
    t_back = threading.Thread(target=stream_logs, args=(backend_proc.stdout, "BACKEND", BLUE), daemon=True)
    t_front = threading.Thread(target=stream_logs, args=(frontend_proc.stdout, "FRONTEND", MAGENTA), daemon=True)
    t_back.start()
    t_front.start()

    # Automatically open default browser after services spin up
    def open_browser():
        time.sleep(3.0)
        webbrowser.open("http://localhost:5173")

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        while True:
            time.sleep(0.5)
            if backend_proc.poll() is not None:
                print(f"\n{YELLOW}[SYSTEM] Backend terhenti (exit code {backend_proc.returncode}).{RESET}")
                break
            if frontend_proc.poll() is not None:
                print(f"\n{YELLOW}[SYSTEM] Frontend terhenti (exit code {frontend_proc.returncode}).{RESET}")
                break
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}[SYSTEM] Menghentikan semua layanan...{RESET}")
    finally:
        kill_process_tree(backend_proc.pid)
        kill_process_tree(frontend_proc.pid)
        print(f"{GREEN}[SYSTEM] Semua layanan berhasil dimatikan dengan aman.{RESET}\n")

if __name__ == "__main__":
    main()
