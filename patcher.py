import json
import re

def read_config_from_json(json_file_path):
    try:
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
            file_path = data.get("file_path")
            old_signkey = data.get("old_signkey")
            new_signkey = data.get("new_signkey")

            if not file_path or not old_signkey or not new_signkey:
                raise ValueError("JSON-Datei muss 'file_path', 'old_signkey' und 'new_signkey' enthalten.")

            return file_path, old_signkey, new_signkey
    
    except FileNotFoundError:
        print(f"Die JSON-Datei {json_file_path} wurde nicht gefunden.")
        raise
    except json.JSONDecodeError:
        print(f"Fehler beim Parsen der JSON-Datei {json_file_path}.")
        raise

def replace_signkey_in_file(file_path, old_signkey, new_signkey):
    if len(old_signkey) != len(new_signkey):
        raise ValueError("Der neue Hex-String muss die gleiche Länge haben wie der alte Hex-String.")

    if old_signkey.startswith("0x"):
        old_signkey = old_signkey[2:]
    if new_signkey.startswith("0x"):
        new_signkey = new_signkey[2:]

    if not re.fullmatch(r'[0-9a-fA-F]+', old_signkey):
        raise ValueError("Der alte Hex-String ist nicht gültig.")
    if not re.fullmatch(r'[0-9a-fA-F]+', new_signkey):
        raise ValueError("Der neue Hex-String ist nicht gültig.")

    try:
        with open(file_path, 'rb') as file:
            content = file.read()

        old_signkey_bytes = bytes.fromhex(old_signkey)
        new_signkey_bytes = bytes.fromhex(new_signkey)

        content = content.replace(old_signkey_bytes, new_signkey_bytes)

        with open(file_path, 'wb') as file:
            file.write(content)
        
        print("Hex-String erfolgreich ersetzt.")
    
    except FileNotFoundError:
        print(f"Die Datei {file_path} wurde nicht gefunden.")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")

json_file_path = 'hex.json'

try:
    file_path, old_signkey, new_signkey = read_config_from_json(json_file_path)
    replace_signkey_in_file(file_path, old_signkey, new_signkey)
except Exception as e:
    print(f"Fehler: {e}")
