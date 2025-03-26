![top-stats-aio-banner](https://github.com/user-attachments/assets/d413569d-ecb1-4618-936e-5f6fa071ba0c)

Your one stop shop for generating top stats  
![image](https://github.com/user-attachments/assets/d5482ea4-7de8-4d78-90f0-88e11e6b2223)

## Compiling EXE

To compile the Python script into an executable (`.exe`), follow these steps:

1. **Install PyInstaller**  
Open a terminal or command prompt and install PyInstaller using `pip`:
```bash
pip install pyinstaller
```
2. **Compile the Script**
Navigate to the directory containing main.py and run the following command:
```bash
pyinstaller --onefile --noconsole --name TopStatsAIO --distpath . --add-data "config.json;." --add-data "themes;themes" --icon "top-stats-aio.ico" main.py
```
