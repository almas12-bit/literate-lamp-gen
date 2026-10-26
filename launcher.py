import os
import sys
import time
import subprocess
import threading
import webbrowser
import shutil

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

def find_npm():
    # 1. Standard which
    npm_path = shutil.which("npm.cmd" if sys.platform == "win32" else "npm")
    if npm_path:
        return npm_path
    
    # 2. Check standard Windows paths
    if sys.platform == "win32":
        candidates = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "nodejs", "npm.cmd"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "nodejs", "npm.cmd"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "nodejs", "npm.cmd"),
            os.path.join(os.environ.get("APPDATA", ""), "npm", "npm.cmd"),
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return c
    return "npm.cmd" if sys.platform == "win32" else "npm"

def stream_logs(pipe, tag, color):
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
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

    # Pre-flight check: backend dependencies
    try:
        import uvicorn
        import fastapi
    except ImportError:
        print(f"\n{YELLOW}[ERROR] Dependensi backend (uvicorn / fastapi) belum terinstall.{RESET}")
        print(f"{YELLOW}[ERROR] Menjalankan instalasi otomatis via setup-python.bat disarankan.{RESET}\n")
        input("Tekan Enter untuk keluar...")
        sys.exit(1)

    # Pre-flight check: node_modules
    npm_bin = find_npm()
    is_win = sys.platform == "win32"
    node_modules_dir = os.path.join(FRONTEND_DIR, "node_modules")
    if not os.path.exists(node_modules_dir):
        print(f"{MAGENTA}[SYSTEM] node_modules frontend belum ada. Memasang via npm install...{RESET}")
        subprocess.run([npm_bin, "install"], cwd=FRONTEND_DIR, shell=is_win)

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
    frontend_proc = subprocess.Popen(
        [npm_bin, "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        shell=is_win
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
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}\n")
        import traceback
        traceback.print_exc()
        input("\nTekan Enter untuk keluar...")
