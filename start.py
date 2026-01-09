#!/usr/bin/env python3
"""
Start script for Fantasy League History application.
Starts both the backend (FastAPI) and frontend (Vite) servers.
"""

import subprocess
import sys
import signal
import os
from pathlib import Path
import threading

# ANSI color codes for output
BLUE = "\033[94m"
GREEN = "\033[92m"
RESET = "\033[0m"

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
VENV_PYTHON = BACKEND_DIR / "venv" / "bin" / "python"

processes = []


def stream_output(process, prefix, color):
    """Stream output from a process with a colored prefix."""
    for line in iter(process.stdout.readline, ""):
        if line:
            print(f"{color}[{prefix}]{RESET} {line}", end="")
    process.stdout.close()


def start_backend():
    """Start the FastAPI backend server."""
    print(f"{BLUE}[BACKEND]{RESET} Starting FastAPI server on http://localhost:8000")

    env = os.environ.copy()
    process = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "app.main:app", "--reload"],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    processes.append(process)

    thread = threading.Thread(target=stream_output, args=(process, "BACKEND", BLUE))
    thread.daemon = True
    thread.start()

    return process


def start_frontend():
    """Start the Vite frontend dev server."""
    print(f"{GREEN}[FRONTEND]{RESET} Starting Vite server on http://localhost:5173")

    process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append(process)

    thread = threading.Thread(target=stream_output, args=(process, "FRONTEND", GREEN))
    thread.daemon = True
    thread.start()

    return process


def shutdown(signum=None, frame=None):
    """Gracefully shutdown all processes."""
    print(f"\n{RESET}Shutting down...")

    for process in processes:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    print("All processes stopped.")
    sys.exit(0)


def main():
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("=" * 60)
    print("  Fantasy League History - Development Server")
    print("=" * 60)
    print()

    # Check that required directories exist
    if not BACKEND_DIR.exists():
        print(f"Error: Backend directory not found at {BACKEND_DIR}")
        sys.exit(1)

    if not FRONTEND_DIR.exists():
        print(f"Error: Frontend directory not found at {FRONTEND_DIR}")
        sys.exit(1)

    if not VENV_PYTHON.exists():
        print(f"Error: Python virtual environment not found at {VENV_PYTHON}")
        print("Please create it with: cd backend && python -m venv venv")
        sys.exit(1)

    # Start both servers
    backend_process = start_backend()
    frontend_process = start_frontend()

    print()
    print("Press Ctrl+C to stop both servers")
    print()

    # Wait for processes to complete (they won't unless there's an error)
    try:
        while True:
            # Check if either process has died
            if backend_process.poll() is not None:
                print(f"{BLUE}[BACKEND]{RESET} Process exited with code {backend_process.returncode}")
                shutdown()
            if frontend_process.poll() is not None:
                print(f"{GREEN}[FRONTEND]{RESET} Process exited with code {frontend_process.returncode}")
                shutdown()

            # Sleep briefly to avoid busy waiting
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
