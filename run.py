import sys
import os
import subprocess
import tempfile
import atexit
import importlib.util

repo = "jesvijonathan/Ableton_Cracker"

if os.name == "nt":
    import ctypes

TEMP_SCRIPT_PATH = None
def cleanup():
    if TEMP_SCRIPT_PATH and os.path.exists(TEMP_SCRIPT_PATH):
        try:
            os.remove(TEMP_SCRIPT_PATH)
        except OSError:
            pass
atexit.register(cleanup)

def ensure_dependencies(modules=("requests", "cryptography")):
    missing = [m for m in modules if importlib.util.find_spec(m) is None]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "--quiet"])

def detect_run_method():
    return "direct" if sys.stdin.isatty() else "piped"

def run_as_admin():
    script = os.path.abspath(sys.argv[0])
    params = subprocess.list2cmdline(sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)

def elevate_windows():
    if detect_run_method() == "piped":
        cmd = (
            '/k python -c "import tempfile, os, sys, subprocess, requests; '
            'f=tempfile.NamedTemporaryFile(delete=False,suffix=\'.py\'); '
            f'f.write(requests.get(\\\"https://raw.githubusercontent.com/{repo}/master/run.py\\\").content); '
            'f.close(); subprocess.run([sys.executable,f.name]); os.remove(f.name)" & exit'
        )
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", cmd, None, 1)
        sys.exit(0)
    if not ctypes.windll.shell32.IsUserAnAdmin():
        run_as_admin()
        sys.exit(0)

def run_tmp_script(url):
    import requests
    global TEMP_SCRIPT_PATH
    raw_url = f"https://raw.githubusercontent.com/{repo}/master/{url}"
    print(f"[DEBUG] Fetching: {raw_url}")
    resp = requests.get(raw_url, timeout=10)
    resp.raise_for_status()
    fd, TEMP_SCRIPT_PATH = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(resp.text)
    exec(compile(resp.text, url, "exec"), globals())

def main_menu():
    options = {
        "1": ("Patch", "patch_ableton.py"),
        "2": ("Unpatch", "undo_patch.py"),
        "3": ("Quit", None),
    }

    print(f"\nAbleton Cracker [https://github.com/{repo}]\n")
    for k, (desc, _) in options.items():
        print(f"{k}. {desc}")

    while True:
        try:
            choice = input("\nSelect an option: ").strip()
            if choice not in options:
                print("[!] Invalid choice.")
                continue
            _, script = options[choice]

            if script:
                run_tmp_script(script)

        except KeyboardInterrupt:
            print("\n[!] Exiting.")
            sys.exit(1)

def main():
    ensure_dependencies()
    if os.name == "nt":
        elevate_windows()
    main_menu()

if __name__ == "__main__":
    main()
