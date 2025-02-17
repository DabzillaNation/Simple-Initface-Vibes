# Simple-Initface-Vibes
Connects to Initface and activates vibe at 100% on key/mouse press

# Install Setup (Executable)
Download the executable from the releases tab on this page and just run it.

# Setup For Python Script
If you don't trust a random exe file, you can install python, clone this repo, install the dependencies to look through the code and run it yourself 
## Install Dependencies (for python script)
Only needed if you want to edit and work with the script on your own
```
pip install -r requirements.txt
```
## Run Script
Navigate the terminal to where you have the python script, then run:
```
python AppV3.py
```

## To build (For windows):
``` bash
python -m venv .venv  # Creates a folder named ".venv" #Creates virtual env
.venv\Scripts\activate # Activates virtual env
pip install -r requirements.txt # installs requirements
pip install pyinstaller # Installs builder
pyinstaller --onefile --noconsole --name "IntifaceHapticApp" AppV3.py --add-data="./icon.ico;." # Builds app
# The app will be in the dist folder, the build folder is just temp files you can delete
```

# Notes:
The AppV1 and V2 are just older worse versions of the app incase you wanted to see them for some reason.
