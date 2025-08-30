import sys
import os
import subprocess
import tempfile
import atexit
import importlib.util

# Cleanup temporary script files on exit
TEMP_SCRIPT_PATH = None
def cleanup():
    if TEMP_SCRIPT_PATH and os.path.exists(TEMP_SCRIPT_PATH):
        try:
            os.remove(TEMP_SCRIPT_PATH)
        except OSError:
            pass
atexit.register(cleanup)

# Ensure required Python modules are installed
def ensure_dependencies(modules=("requests", "cryptography")):
    missing = [m for m in modules if importlib.util.find_spec(m) is None]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "--quiet"])

# Windows-specific elevation and launcher
def elevate_windows():
    import ctypes
    if ctypes.windll.shell32.IsUserAnAdmin():
        return  # Already admin

    params = (
        '/k '
        'python -c "import tempfile, os, sys, subprocess, requests; '
        'f=tempfile.NamedTemporaryFile(delete=False,suffix=\'.py\'); '
        'f.write(requests.get(\'https://raw.githubusercontent.com/jesvijonathan/Ableton_Cracker/master/run.py\').content); '
        'f.close(); subprocess.run([sys.executable,f.name]); os.remove(f.name)" & exit'
    )

    ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", params, None, 1)
    sys.exit(0)

# Run a Python script from URL
def run_tmp_script(url):
    import requests
    global TEMP_SCRIPT_PATH
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    fd, TEMP_SCRIPT_PATH = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(resp.text)
    exec(compile(resp.text, url, "exec"), globals())

# Simple menu
def main_menu():
    repo = "jesvijonathan/Ableton_Cracker"
    options = {
        "1": ("Patch", f"https://raw.githubusercontent.com/{repo}/master/patch_ableton.py"),
        "2": ("Unpatch", f"https://raw.githubusercontent.com/{repo}/master/undo_patch.py"),
        "3": ("Quit", None),
    }

    print(f"\nAbleton Cracker [https://github.com/{repo}]\n")
    for key, (desc, _) in options.items():
        print(f"{key}. {desc}")

    while True:
        try:
            choice = input("\nSelect an option: ").strip()
            if choice not in options:
                print("[!] Invalid choice.")
                continue
            _, url = options[choice]
            if url:
                run_tmp_script(url)
            break
        except KeyboardInterrupt:
            break

# Entry point
def main():
    ensure_dependencies()
    if os.name == "nt":
        elevate_windows()
    main_menu()

if __name__ == "__main__":
    main()
