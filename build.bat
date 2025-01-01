@echo off

pip show demucs >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing demucs...
    pip install demucs
    if %ERRORLEVEL% neq 0 (
        echo *********ERROR*********: Error installing demucs.
        exit /b 1
    )
)

where ffmpeg >nul 2>&1

if %ERRORLEVEL% neq 0 (
    echo Installing ffmpeg...
    
    curl -L https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip -o ffmpeg.zip
    if %ERRORLEVEL% neq 0 (
        echo *********ERROR*********: Failed downloading ffmpeg.zip.
        exit /b 1
    )

    tar -xf ffmpeg.zip
    if %ERRORLEVEL% neq 0 (
        echo *********ERROR*********: Error extracting ffmpeg.zip.
        del ffmpeg.zip
        exit /b 1
    )

    for /d %%i in (ffmpeg-*) do move "%%i" "C:\ffmpeg"
    if %ERRORLEVEL% neq 0 (
        echo *********ERROR*********: Error moving ffmpeg to C:\ffmpeg.
        del ffmpeg.zip
        exit /b 1
    )

    setx /M PATH "%PATH%;C:\ffmpeg\bin"
    if %ERRORLEVEL% neq 0 (
        echo *********ERROR*********: Error adding ffmpeg to PATH. Run this file as administrator.
        exit /b 1
    )

    del ffmpeg.zip

    ffmpeg -version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo *********ERROR*********: ffmpeg installation failed.
        exit /b 1
    )
)

echo Setting up environment...
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt

echo Building executable...
pyinstaller --onefile --noconfirm --name=Splinter --paths=src\ src\Splinter.py

echo Building complete!