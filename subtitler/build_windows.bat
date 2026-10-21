@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
set "FFMPEG_ZIP=%TEMP%\subtitler-ffmpeg.zip"
set "FFMPEG_TMP=%TEMP%\subtitler-ffmpeg"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%FFMPEG_ZIP%'"
if errorlevel 1 exit /b 1
if exist "%FFMPEG_TMP%" rmdir /s /q "%FFMPEG_TMP%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%FFMPEG_ZIP%' -DestinationPath '%FFMPEG_TMP%' -Force"
if errorlevel 1 exit /b 1

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
python -m PyInstaller --clean --noconfirm subtitler.spec
if errorlevel 1 exit /b 1
mkdir dist\Subtitler\ffmpeg
for /r "%FFMPEG_TMP%" %%F in (ffmpeg.exe) do copy /y "%%F" dist\Subtitler\ffmpeg\ffmpeg.exe >nul & goto :ffmpeg_done
:ffmpeg_done
for /r "%FFMPEG_TMP%" %%F in (ffprobe.exe) do copy /y "%%F" dist\Subtitler\ffmpeg\ffprobe.exe >nul & goto :ffprobe_done
:ffprobe_done
copy /y .env.example dist\Subtitler\.env.example >nul

echo Build complete: dist\Subtitler\Subtitler.exe
endlocal
