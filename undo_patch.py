import json
import re

def read_config_from_json(json_file_path):
    try:
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
            file_path = data.get("file_path")
            new_signkey = data.get("old_signkey")
            old_signkey = data.get("new_signkey")

            if not file_path or not old_signkey or not new_signkey:
                raise ValueError("JSON file must contain 'file_path', 'old_signkey', and 'new_signkey'.")

            return file_path, old_signkey, new_signkey
    
    except FileNotFoundError:
        print(f"The JSON file {json_file_path} was not found.")
        raise
    except json.JSONDecodeError:
        print(f"Error parsing the JSON file {json_file_path}.")
        raise



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

json_file_path = 'config.json'

try:
    file_path, old_signkey, new_signkey = read_config_from_json(json_file_path)
    replace_signkey_in_file(file_path, old_signkey, new_signkey)
except Exception as e:
    print(f"Error: {e}")
