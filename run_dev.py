import os
import sys
import subprocess
import time

def run_dev():
    print("Starting AI Decision-Tree Agent Development Servers...")
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")

    # Start FastAPI Backend
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"]
    backend_proc = subprocess.Popen(backend_cmd, cwd=backend_dir)
    print(f"Backend started on http://localhost:8000 (PID {backend_proc.pid})")

    # Start Vite Frontend
    frontend_cmd = ["npm.cmd" if os.name == "nt" else "npm", "run", "dev"]
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=frontend_dir)
    print(f"Frontend started on http://localhost:3000 (PID {frontend_proc.pid})")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping development servers...")
        backend_proc.terminate()
        frontend_proc.terminate()

if __name__ == "__main__":
    run_dev()
