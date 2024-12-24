@echo off

echo Building Splinter...
python -m venv .venv

echo Activating virtual environment...
call .venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Building executable...
pyinstaller --onefile --noconsole --icon=assets\logo.ico Splinter

echo Deactivating virtual environment...
deactivate

echo Building complete!