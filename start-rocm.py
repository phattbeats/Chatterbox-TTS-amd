#!/usr/bin/env python3
"""
PHATT TECH Chatterbox TTS Server - ROCm Windows Launcher
=======================================================

ROCm-specific launcher for AMD GPUs on Windows.
Handles the two-step install: ROCm wheels first, then dependencies.

Usage:
    Windows: Double-click start-rocm.bat
    Manual:  python start-rocm.py

Requirements:
    - Python 3.10+ installed and in PATH
    - AMD GPU (RX 6000 series recommended)
    - AMD ROCm SDK installed
    - Windows OS
"""

import datetime
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

# ==================== CONFIGURATION ====================

SERVER_STARTUP_TIMEOUT = 180
PORT_CHECK_INTERVAL = 0.5
BROWSER_DELAY = 2.0

VENV_FOLDER = "venv"
INIT_REQUIREMENTS = "requirements-rocm-init.txt"
REQUIREMENTS_FILE = "requirements-rocm.txt"

VERBOSE_LOGGING = False

# =========================================================

_server_process = None


def print_banner():
    print()
    print("=" * 60)
    print("   PHATT TECH Chatterbox TTS Server - ROCm Edition")
    print("=" * 60)
    print()


def print_step(step, total, message):
    print(f"[{step}/{total}] {message}")


def print_substep(message, status="info"):
    icons = {"done": "OK", "error": "XX", "warning": "!!", "info": ">>"}
    icon = icons.get(status, ">>")
    print(f"      {icon} {message}")


def print_status_box(host, port):
    display_host = "localhost" if host == "0.0.0.0" else host
    url = f"http://{display_host}:{port}"
    print()
    print("=" * 60)
    print("   PHATT TECH Chatterbox TTS Server is running!")
    print()
    print(f"   Web Interface:  {url}")
    print(f"   API Docs:       {url}/docs")
    if host == "0.0.0.0":
        print("   (Also accessible on your local network)")
    print()
    print("   Press Ctrl+C to stop the server.")
    print("=" * 60)
    print()


def check_python_version():
    if sys.version_info < (3, 10):
        print_substep(f"Python 3.10+ required. Found: {sys.version}", status="error")
        sys.exit(1)
    print_substep(f"Python {sys.version_info.major}.{sys.version_info.minor} detected", status="done")


def check_port_in_use(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        check_host = "127.0.0.1" if host == "0.0.0.0" else host
        result = sock.connect_ex((check_host, port))
        sock.close()
        return result == 0
    except socket.error:
        return False


def wait_for_server(host, port):
    print_substep("Waiting for server to start (model loading may take 60-120 seconds)...")
    start_time = time.time()
    check_host = "127.0.0.1" if host == "0.0.0.0" else host
    sys.stdout.write("      ")
    sys.stdout.flush()
    dots = 0
    last_dot = start_time
    while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((check_host, port))
            sock.close()
            if result == 0:
                sys.stdout.write("\n")
                elapsed = time.time() - start_time
                print_substep(f"Server ready! (took {elapsed:.1f}s)", status="done")
                return True
        except socket.error:
            pass
        if time.time() - last_dot >= 2:
            sys.stdout.write(".")
            sys.stdout.flush()
            dots += 1
            last_dot = time.time()
            if dots % 30 == 0:
                sys.stdout.write("\n      ")
                sys.stdout.flush()
        time.sleep(PORT_CHECK_INTERVAL)
    sys.stdout.write("\n")
    print_substep(f"Timeout after {SERVER_STARTUP_TIMEOUT}s", status="error")
    return False


def run_command(command, cwd=None, capture=False, show_output=False):
    try:
        if capture:
            result = subprocess.check_output(command, shell=True, cwd=cwd, stderr=subprocess.STDOUT)
            return result.decode().strip()
        if show_output or VERBOSE_LOGGING:
            subprocess.check_call(command, shell=True, cwd=cwd)
        else:
            subprocess.check_call(command, shell=True, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        if VERBOSE_LOGGING:
            print(f"      [DEBUG] Command failed: {command}")
            print(f"      [DEBUG] Error: {e}")
        return None if capture else False


def ensure_venv(root_dir, venv_dir):
    venv_python = venv_dir / "Scripts" / "python.exe"
    venv_pip = venv_dir / "Scripts" / "pip.exe"
    if not venv_dir.exists():
        print_substep("Creating virtual environment...")
        success = run_command(f'"{sys.executable}" -m venv "{venv_dir}"')
        if not success:
            print_substep("Failed to create virtual environment!", status="error")
            sys.exit(1)
        print_substep("Virtual environment created", status="done")
    else:
        print_substep("Virtual environment found", status="done")
    return str(venv_python), str(venv_pip)


def check_dependencies_installed(venv_pip):
    try:
        result = run_command(f'"{venv_pip}" show fastapi torch', capture=True)
        return result is not None and "Name: fastapi" in result
    except Exception:
        return False


def install_dependencies(root_dir, venv_python, venv_pip, install_flag):
    if install_flag.exists():
        print_substep("Dependencies already installed", status="done")
        return False
    if check_dependencies_installed(venv_pip):
        print_substep("Dependencies already installed (existing venv)", status="done")
        try:
            install_flag.parent.mkdir(parents=True, exist_ok=True)
            install_flag.write_text(f"Verified {datetime.datetime.now().isoformat()}\n")
        except Exception:
            pass
        return False

    print_substep("First-time setup - installing dependencies...", status="info")
    print_substep("This may take 10-20 minutes on first run...", status="info")

    print_substep("Upgrading pip...")
    run_command(f'"{venv_python}" -m pip install --upgrade pip')

    # Step 1: Install ROCm PyTorch wheels
    init_req = root_dir / INIT_REQUIREMENTS
    if init_req.exists():
        print_substep("Installing ROCm PyTorch wheels (step 1 of 2)...")
        print_substep("This is a large download (~2GB) - please wait...")
        ok = run_command(f'"{venv_pip}" install -r "{init_req}"', show_output=False)
        if not ok:
            print_substep("ROCm wheel install had issues - continuing...", status="warning")
    else:
        print_substep(f"{INIT_REQUIREMENTS} not found!", status="error")
        print_substep("Make sure you downloaded all release assets.", status="info")

    # Step 2: Install remaining dependencies
    req_file = root_dir / REQUIREMENTS_FILE
    if req_file.exists():
        print_substep("Installing remaining dependencies (step 2 of 2)...")
        ok = run_command(f'"{venv_pip}" install -r "{req_file}"', show_output=False)
        if not ok:
            print_substep("Some dependencies may have failed", status="warning")
    else:
        print_substep(f"{REQUIREMENTS_FILE} not found!", status="error")
        sys.exit(1)

    try:
        install_flag.parent.mkdir(parents=True, exist_ok=True)
        install_flag.write_text(f"Completed {datetime.datetime.now().isoformat()}\n")
    except Exception:
        pass
    print_substep("Dependencies installed", status="done")
    return True


def read_config(root_dir):
    config_file = root_dir / "config.yaml"
    host = "0.0.0.0"
    port = 8004
    auto_open = False
    if config_file.exists():
        try:
            import yaml
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            if config and "server" in config:
                host = config["server"].get("host", host)
                port = config["server"].get("port", port)
            print_substep(f"Loaded config: {host}:{port}", status="done")
        except ImportError:
            print_substep("PyYAML not available - using defaults", status="info")
        except Exception as e:
            print_substep(f"Could not read config.yaml: {e}", status="warning")
    else:
        print_substep("config.yaml not found - using defaults", status="info")
    return host, port, auto_open


def launch_server(root_dir, venv_python, host, port):
    server_script = root_dir / "server.py"
    if not server_script.exists():
        print_substep("server.py not found!", status="error")
        sys.exit(1)
    print_substep(f"Starting server on {host}:{port}...")
    process = subprocess.Popen(
        [venv_python, str(server_script)],
        cwd=str(root_dir),
        creationflags=0,
    )
    return process


def cleanup_server(process):
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
    except Exception:
        pass


def main():
    global _server_process
    if sys.platform != "win32":
        print()
        print("=" * 60)
        print("   This launcher is for Windows with AMD ROCm only.")
        print("=" * 60)
        print()
        print("   For Linux/Mac, use Docker or run server.py directly.")
        print()
        sys.exit(0)

    root_dir = Path(__file__).parent.absolute()
    venv_dir = root_dir / VENV_FOLDER
    install_flag = venv_dir / ".install_complete"

    print_banner()

    print_step(1, 4, "Checking Python installation...")
    check_python_version()

    print()
    print_step(2, 4, "Setting up virtual environment...")
    venv_python, venv_pip = ensure_venv(root_dir, venv_dir)

    print()
    print_step(3, 4, "Checking dependencies...")
    install_dependencies(root_dir, venv_python, venv_pip, install_flag)

    print()
    print_step(4, 4, "Launching PHATT TECH Chatterbox TTS Server...")

    host, port, auto_open = read_config(root_dir)

    if check_port_in_use(host, port):
        print_substep(f"Port {port} is already in use!", status="error")
        print_substep("Stop the existing process or change port in config.yaml", status="info")
        sys.exit(1)

    _server_process = launch_server(root_dir, venv_python, host, port)
    server_ready = wait_for_server(host, port)

    if not server_ready:
        print_substep("Server failed to start", status="error")
        print_substep("Common issues:", status="info")
        print_substep("  - AMD ROCm not installed or not in PATH", status="info")
        print_substep("  - GPU not detected - check ROCm is working", status="info")
        print_substep("  - Insufficient GPU memory", status="info")
        cleanup_server(_server_process)
        sys.exit(1)

    print_status_box(host, port)
    if auto_open and server_ready:
        display_host = "localhost" if host == "0.0.0.0" else host
        print(f"Opening browser to http://{display_host}:{port}...")
        threading.Thread(target=lambda: (time.sleep(BROWSER_DELAY), webbrowser.open(f"http://{display_host}:{port}")), daemon=True).start()

    try:
        while True:
            if _server_process.poll() is not None:
                print()
                print_substep(f"Server exited with code {_server_process.returncode}", status="warning")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("Shutting down PHATT TECH Chatterbox TTS Server...")
        cleanup_server(_server_process)
        print("Server stopped. Goodbye!")
        sys.exit(0)

    cleanup_server(_server_process)
    sys.exit(_server_process.returncode if _server_process.returncode else 0)


if __name__ == "__main__":
    main()
