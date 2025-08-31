# Ableton Cracker

An open-source, Python-based patch and key generator for Ableton Live, mirroring the functionality of Team R2R's tools. This project provides a streamlined, cross-platform solution for patching and authorizing Ableton Live.

## Features

- **All-in-One Script:** A single command is all you need to start the process.
- **No Manual Setup:** The script automatically handles all configurations.
- **Cross-Platform:** Fully compatible with Windows, macOS, and Linux (via Wine).
- **Auto-Detect Installations:** Automatically finds your Ableton Live application.
- **Reversible:** Includes a simple unpatcher to restore the original executable at any time.

## Getting Started

You can run the patcher instantly with a one-line command or by downloading the script manually. Python 3 must be installed on your system.

### Method 1: Quick Run (Recommended)

Open your terminal and quick run this command.

```bash
curl -sS https://raw.githubusercontent.com/jesvijonathan/Ableton_Cracker/master/run.py | python3
```

### Method 2: Manual Download

1. Download the `run.py` file from this repository.
2. Open your terminal or command prompt in the folder where you saved the file.
3. Run the script:

- Windows:

```powershell
python run.py
```

- macOS / Linux:

```bash
sudo python3 run.py
```

## Usage Flow

After starting the script, follow these steps (_Not required if auto-detection is successful_):

### 1. Find Your Hardware ID (HWID)

You need this unique ID from your computer to generate the correct authorization file.

1. Open Ableton Live.
2. Go to **Preferences → Licenses & Updates**.
3. Click the **Authorize Offline** button.
4. Your Hardware ID will be displayed. Copy this ID and keep it ready.

### 2. Configure the `config.json` File

1. The first time you run the script, it will download a `config.json` file into the same directory.
2. Open `config.json` with any text editor.
3. Replace the placeholder hwid (`"1111-..."`) with your own HWID.
4. Optionally, change the edition and version to match your installation.

### 3. Patch Ableton

1. Go back to the script running in your terminal.
2. Choose option `1. Patch` from the menu.
3. The script will find your Ableton installation(s). If you have multiple, select the one you want to patch.
4. It will patch the application and generate an `Authorize.auz` file.

### 4. Authorize Live

1. Open Ableton Live.
2. Drag and drop the generated `Authorize.auz` file onto the Ableton window.
3. You're done! Your Ableton Live is now fully authorized.

## 🔧 Compatibility

| Platform | Supported | Notes                                  |
| -------- | --------- | -------------------------------------- |
| Windows  | ✅        | Works on all modern versions.          |
| macOS    | ✅        | Works on both Intel and Apple Silicon. |
| Linux    | ✅        | Requires Wine to run Ableton Live.     |

- **Ableton Versions:** 9, 10, 11, 12
- **Ableton Editions:** Lite, Intro, Standard, Suite

## Download Ableton Installers

You can download official Ableton Live installers directly from their servers:

[StaticAbletonDownloader](#)

## Disclaimer

This script is for **educational purposes only**. It is not the result of reverse engineering Ableton Live, and its output will not circumvent the protection on an unmodified copy of Ableton Live.

## Credits

- **rufoa**
- **jesvijonathan**
- **devilAPI**
- **drmext**
