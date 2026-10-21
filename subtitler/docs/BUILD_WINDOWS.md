# Build and run the Windows release

## Download a release

1. Download `Subtitler-windows-x64.zip` from the GitHub Release assets.
2. Unzip it to a writable folder.
3. Copy `.env.example` to `.env` and add the API keys you use.
4. Run `Subtitler.exe`. A console window shows logs and the Gradio UI opens in your browser.

The release includes `ffmpeg.exe` and `ffprobe.exe` in the `ffmpeg/` folder, so a separate FFmpeg installation is not required.

## Build locally

On Windows with Python 3.11 or newer, from the repository root run:

```bat
build_windows.bat
```

The script creates `.venv`, installs the application requirements and PyInstaller, downloads the static FFmpeg essentials build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/), and writes the onedir application to `dist\Subtitler`.

You can then run `dist\Subtitler\Subtitler.exe`. Copy `.env.example` to `dist\Subtitler\.env` first if you need API keys.

## Security note

The executable is unsigned. Windows SmartScreen or antivirus software may show a warning or a false positive for PyInstaller-built executables. Verify the release source and checksum where available, and only allow/run a build you trust.
