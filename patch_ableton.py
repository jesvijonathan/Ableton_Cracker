import json
import re
import os
import platform
import sys
import ctypes
import subprocess
from random import randint
from importlib.util import find_spec

def ensure_dependencies(modules=("requests", "cryptography")):
    missing = [m for m in modules if find_spec(m) is None]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "--quiet"])
ensure_dependencies()

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.hashes import SHA1
import requests

def is_admin():
    """Check if the script is running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    """Relaunch the script with administrator privileges"""
    script = os.path.abspath(sys.argv[0])
    params = subprocess.list2cmdline(sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    sys.exit(0)

def load_config(filename: str):
    try:
        if not os.path.exists(filename):
            print(f"Config file {filename} not found. Downloading...")
            url = "https://raw.githubusercontent.com/jesvijonathan/Ableton_Cracker/master/config.json"
            response = requests.get(url)
            response.raise_for_status()
            with open(filename, 'w') as f:
                f.write(response.text)

        with open(filename, 'r') as f:
            data = json.load(f)

            # Extract values from JSON
            file_path = data.get("file_path")
            old_signkey = data.get("old_signkey")
            new_signkey = data.get("new_signkey")
            hwid = data.get('hwid', '').upper()
            edition = data.get('edition', 'Suite')
            version = data.get('version', 12)
            authorize_file_output = data.get('authorize_file_output', 'Authorize.auz')
            dsa_params = data.get('dsa_parameters')

            # Validate essential keys
            if not file_path or not old_signkey or not new_signkey:
                raise ValueError("JSON file must contain 'file_path', 'old_signkey', and 'new_signkey'.")
            if len(hwid) == 24:
                hwid = "-".join(hwid[i:i+4] for i in range(0, 24, 4))
            assert re.fullmatch(r"([0-9A-F]{4}-){5}[0-9A-F]{4}", hwid), f"Expected hardware ID like 1111-1111-1111-1111-1111-1111, not {hwid}"

            if not dsa_params:
                raise ValueError("DSA parameters are missing in the config file.")

            return file_path, old_signkey, new_signkey, hwid, edition, version, authorize_file_output, dsa_params
    
    except FileNotFoundError:
        print(f"The JSON file {filename} was not found.")
        raise
    except json.JSONDecodeError:
        print(f"Error parsing the JSON file {filename}.")
        raise

def construct_key(dsa_params) -> dsa.DSAPrivateKey:
    p = int(dsa_params['p'], 16)
    q = int(dsa_params['q'], 16)
    g = int(dsa_params['g'], 16)
    y = int(dsa_params['y'], 16)
    x = int(dsa_params['x'], 16)

    params = dsa.DSAParameterNumbers(p, q, g)
    pub = dsa.DSAPublicNumbers(y, params)
    priv = dsa.DSAPrivateNumbers(x, pub)
    return priv.private_key(backend=default_backend())

def replace_signkey_in_file(file_path, old_signkey, new_signkey):
    if len(old_signkey) != len(new_signkey):
        raise ValueError("The new signkey must be the same length as the old signkey.")

    if old_signkey.startswith("0x"):
        old_signkey = old_signkey[2:]
    if new_signkey.startswith("0x"):
        new_signkey = new_signkey[2:]

    if not re.fullmatch(r'[0-9a-fA-F]+', old_signkey):
        raise ValueError("The old signkey is not valid.")
    if not re.fullmatch(r'[0-9a-fA-F]+', new_signkey):
        raise ValueError("The new signkey is not valid.")

    try:
        with open(file_path, 'rb') as file:
            content = file.read()

        old_signkey_bytes = bytes.fromhex(old_signkey)
        new_signkey_bytes = bytes.fromhex(new_signkey)

        if old_signkey_bytes not in content:
            if new_signkey_bytes in content:
                print(f"The new signkey \n'{new_signkey}' \nis already present in the file. Ableton is already patched.")
            else:
                print(f"Neither the old nor the new signkey was found in the file. You may be running an unsupported version or a different patch.")
        else:
            print(f"The old signkey '{old_signkey}' was found. Replacing...")

            content = content.replace(old_signkey_bytes, new_signkey_bytes)

            with open(file_path, 'wb') as file:
                file.write(content)

            # Verify replacement
            if old_signkey_bytes in content:
                print("Error: The old signkey is still present in the file.")
            else:
                print("Signkey successfully replaced.")
    
    except PermissionError:
        print("\nPermission denied! Try running the script as Administrator.")
        if platform.system() == "Windows":
            print("Relaunching with admin privileges...")
            run_as_admin()
        else:
            print("On Linux/macOS, try running with sudo.")
            raise
    except FileNotFoundError:
        print(f"The file '{file_path}' was not found.")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

def sign(k: dsa.DSAPrivateKey, m: str) -> str:
    """P1363 format sig over m as a string of hex digits"""
    assert k.key_size == 1024
    sig = k.sign(m.encode(), SHA1())
    r, s = decode_dss_signature(sig)
    return "{:040X}{:040X}".format(r, s)

def fix_group_checksum(group_number: int, n: int) -> int:
    checksum = n >> 4 & 0xf ^ \
               n >> 5 & 0x8 ^ \
               n >> 9 & 0x7 ^ \
               n >> 11 & 0xe ^ \
               n >> 15 & 0x1 ^ \
               group_number
    return n & 0xfff0 | checksum

def overall_checksum(groups: list[int]) -> int:
    r = 0
    for i in range(20):
        g, digit = divmod(i, 4)
        v = groups[g] >> (digit * 8) & 0xff
        r ^= v << 8
        for _ in range(8):
            r <<= 1
            if r & 0x10000:
                r ^= 0x8005
    return r & 0xffff

def random_serial():
    """
    3xxc-xxxc-xxxc-xxxc-xxxc-dddd
    x is random
    c is a checksum over each group
    d is a checksum over all groups
    """
    groups = [randint(0x3000, 0x3fff),
              randint(0x0000, 0xffff),
              randint(0x0000, 0xffff),
              randint(0x0000, 0xffff),
              randint(0x0000, 0xffff)]
    for i in range(5):
        groups[i] = fix_group_checksum(i, groups[i])
    d = overall_checksum(groups)
    return "{:04X}-{:04X}-{:04X}-{:04X}-{:04X}-{:04X}".format(*groups, d)

def generate_single(k: dsa.DSAPrivateKey, id1: int, id2: int, hwid: str) -> str:
    f = "{},{:02X},{:02X},Standard,{}"
    serial = random_serial()
    msg = f.format(serial, id1, id2, hwid)
    sig = sign(k, msg)
    return f.format(serial, id1, id2, sig)

def generate_all(k: dsa.DSAPrivateKey, edition: str, version: int, hwid: str) -> str:
    yield generate_single(k, EDITIONS[edition], version << 4, hwid)
    for i in range(0x40, 0xff + 1):
        yield generate_single(k, i, 0x10, hwid)
    for i in range(0x8000, 0x80ff + 1):
        yield generate_single(k, i, 0x10, hwid)

# Mapping for the editions
EDITIONS = {
    "Lite": 4,
    "Intro": 3,
    "Standard": 0,
    "Suite": 2,
}

# Installation detection functions
def get_user_config_dir():
    system = platform.system()
    if system == "Windows":
        return os.getenv('APPDATA')
    elif system == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:  # Linux and others
        return os.getenv('XDG_CONFIG_HOME', os.path.join(os.path.expanduser("~"), ".config"))

def find_installations():
    system = platform.system()
    installations = []
    
    if system == "Windows":
        base_dir = "C:\\ProgramData\\Ableton"
        if not os.path.exists(base_dir):
            return installations
            
        for entry in os.listdir(base_dir):
            if "Live" in entry:
                entry_path = os.path.join(base_dir, entry)
                if os.path.isdir(entry_path):
                    program_dir = os.path.join(entry_path, "Program")
                    if os.path.exists(program_dir):
                        for file in os.listdir(program_dir):
                            if file.endswith(".exe") and "Live" in file:
                                exe_path = os.path.join(program_dir, file)
                                installations.append((exe_path, entry))

    elif system == "Linux":
        wine_base = os.path.expanduser("~/.wine/drive_c/ProgramData/Ableton")
        if os.path.isdir(wine_base):
            for entry in os.listdir(wine_base):
                program_dir = os.path.join(wine_base, entry, "Program")
                if os.path.isdir(program_dir):
                    for file in os.listdir(program_dir):
                        if file.endswith(".exe") and "Live" in file:
                            installations.append((os.path.join(program_dir, file), entry))
    
    elif system == "Darwin":
        base_dir = "/Applications"
        if not os.path.exists(base_dir):
            return installations
            
        for entry in os.listdir(base_dir):
            if entry.endswith(".app") and "Ableton Live" in entry:
                app_path = os.path.join(base_dir, entry)
                exe_path = os.path.join(app_path, "Contents", "MacOS", "Live")
                if os.path.exists(exe_path):
                    name = entry.replace(".app", "")
                    installations.append((exe_path, name))
    
    return installations

def find_installation_data():
    config_dir = get_user_config_dir()
    base_dir = os.path.join(config_dir, "Ableton")
    data_dirs = []
    
    if not os.path.exists(base_dir):
        return data_dirs
        
    for entry in os.listdir(base_dir):
        entry_path = os.path.join(base_dir, entry)
        if os.path.isdir(entry_path) and "Live" in entry:
            # Check if Unlock directory exists or can be created
            data_dirs.append((entry_path, entry))
    
    return data_dirs

def main():
    # Request admin on Windows if needed
    if platform.system() == "Windows" and not is_admin():
        print("\nThis operation requires administrator privileges on Windows.")
        print("Relaunching with admin rights...")
        run_as_admin()
        return
    
    # Load configuration
    config_file = 'config.json'

    try:
        file_path, old_signkey, new_signkey, hwid, edition, version, authorize_file_output, dsa_params = load_config(config_file)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        input("Press Enter to exit...")
        sys.exit(1)


    # Auto-detect installations if needed
    if file_path.lower() == "auto":
        installations = find_installations()
        if not installations:
            print("\nNo Ableton Live installations found. Please specify the path manually.")
            input("Press Enter to exit...")
            sys.exit(1)

        print("\nFound Ableton installations:")
        for i, (path, name) in enumerate(installations):
            print(f"{i+1}. {name} at '{path}'")

        try:
            selection = int(input("\nSelect installation to patch: ")) - 1
            if selection < 0 or selection >= len(installations):
                print("Invalid selection. Using first installation.")
                selection = 0
            file_path = installations[selection][0]
            print(f"Selected: {file_path}")
        except ValueError:
            print("Invalid input. Using first installation found.")
            file_path = installations[0][0]
    
    # Fixed authorization file location
    authorize_file_output = os.path.join(os.path.dirname(file_path), "Authorize.auz")

    # Construct the key from the loaded parameters
    try:
        team_r2r_key = construct_key(dsa_params)
    except Exception as e:
        print(f"Error constructing DSA key: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

    # Generate keys and save the authorize file
    print("\nGenerating authorization keys...")
    try:
        lines = list(generate_all(team_r2r_key, edition, version, hwid))
        with open(authorize_file_output, "w", newline="\n") as f:
            f.write("\n".join(lines))
        print(f"Authorization file created: {authorize_file_output}")
        system = platform.system()
        if system == "Windows":
            os.system(f'explorer /select,"{authorize_file_output}"')
        elif system == "Darwin":
            subprocess.run(["open", "-R", authorize_file_output])
        else:
            subprocess.run(["xdg-open", os.path.dirname(authorize_file_output)])
    except Exception as e:
        print(f"Error generating authorization keys: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

    # Replace the signkey in the binary file
    print("\nPatching executable...")
    try:
        replace_signkey_in_file(file_path, old_signkey, new_signkey)
        print("\nPatch completed successfully!")
        print("\nJust drag & drop the authorization file into Ableton's registration window")
        input("\nPress Enter to exit...")
    except Exception as e:
        print(f"\nPatch failed: {e}")
        input("\nPress Enter to exit...")
    sys.exit(1)


if __name__ == "__main__":
    main()