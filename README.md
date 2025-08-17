# abletonCracker - What is this?

This is an open-source implementation of the R2R Patch and `R2RLIVE.dll` of Ableton Live, written in Python 3.

Like `R2RLIVE.dll`, this script uses Team R2R's signing key only.

# Disclaimer

This script is not the result of reverse engineering Ableton Live, and the output of this script **will not** circumvent the protection on an **unmodified** copy of Ableton Live.

# Download Ableton Installers

You can download the Ableton Installers directly from Ableton's servers. I made a small HTML file to make this easier for you.

[StaticAbletonDownloader](https://devilapi.github.io/StaticAbletonDownloader)

# Compatibility

- Works on Windows and Linux (with wine)
- Should work for all Ableton Live Versions above Live 9 (9,10,11,12)
- Every Edition works too (Lite, Intro, Standard, Suite)

# How to use

1. Run `pip install cryptography` to install dependencies
2. Find your Ableton HWID, open Ableton, and press "Authorize Ableton offline". You will find your HWID.
2. Open `config.json` and change the variables to fit your Ableton Live installation. Make sure to follow the json language, for example double slash in the file path.
3. Save the file.
4. Run `patch_ableton.py`, your Ableton should be patched and the `Authorize.auz` file should generate.
5. Run Ableton, drag the `Authorize.auz` file into the Window
6. You're done.

If there are any permission erros, its recommended to move the Ableton.exe into the same folder where `patch_ableton.py` is located.

# Credits

The Implementation of the KeyGen was made by [rufoa](https://github.com/rufoa). Go leave a star on his Git page!
