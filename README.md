# Simple-Initface-Vibes
Super simple app.
- Connects to Initface and activates vibe on key/mouse press of your choice.
- Works while minimized.
- Can change intensity level.

# Install Setup (Executable)
Download the executable from the releases tab on this page and just run it.
It will show you instructions:
![image](https://github.com/user-attachments/assets/ca2fe19f-9b92-428e-bc4c-eca6e7956731)
![image](https://github.com/user-attachments/assets/f6c77986-b38d-40ca-b9a3-f8377f1cfc1c)
![image](https://github.com/user-attachments/assets/812460b9-aa02-449a-931c-737d6991b495)
![image](https://github.com/user-attachments/assets/af72058e-f2d6-44f0-ab1e-f15d6be8d8d3)
![image](https://github.com/user-attachments/assets/33bf3cd1-3387-4ef5-937a-5157e2e345be)

# Setup For Python Script
If you don't trust a random exe file, you can install python, clone this repo, install the dependencies to look through the code and run it yourself 
## Install Dependencies (for python script)
Only needed if you want to edit and work with the script on your own
```bash
pip install -r requirements.txt
```
## Run Script
Navigate the terminal to where you have the python script, then run:
```bash
python AppV3.py
```

## To build (For windows):
``` bash
python -m venv .venv  # Creates a folder named ".venv" #Creates virtual env
.venv\Scripts\activate # Activates virtual env
pip install -r requirements.txt # installs requirements
pip install pyinstaller # Installs builder
pyinstaller --onefile --noconsole --name "IntifaceHapticApp" AppV3.py --icon="./icon.ico" # Builds app
# The app will be in the dist folder, the build folder is just temp files you can delete
```

# Notes:
The AppV1 and V2 are just older worse versions of the app incase you wanted to see them for some reason.
