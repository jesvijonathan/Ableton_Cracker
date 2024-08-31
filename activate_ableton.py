import json
import re
from random import randint
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.hashes import SHA1

def load_config(filename: str):
    try:
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
            print(f"The old signkey '{old_signkey}' was not found in the file.")
        else:
            print(f"The old signkey '{old_signkey}' was found. Replacing...")

            content = content.replace(old_signkey_bytes, new_signkey_bytes)

            with open(file_path, 'wb') as file:
                file.write(content)

            if old_signkey_bytes in content:
                print("Error: The old signkey is still present in the file.")
            else:
                print("Signkey successfully replaced.")
    
    except FileNotFoundError:
        print(f"The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

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

# Load configuration
config_file = 'config.json'
file_path, old_signkey, new_signkey, hwid, edition, version, authorize_file_output, dsa_params = load_config(config_file)

# Construct the key from the loaded parameters
team_r2r_key = construct_key(dsa_params)

# Generate keys and save the authorize file
lines = generate_all(team_r2r_key, edition, version, hwid)
with open(authorize_file_output, mode="w", newline="\n") as f:
    f.write("\n".join(lines))

# Replace the signkey in the binary file
replace_signkey_in_file(file_path, old_signkey, new_signkey)
