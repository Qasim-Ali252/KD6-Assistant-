# PyAudio Installation Script for Python 3.14 on Windows

Write-Host "Installing PyAudio for Python 3.14..." -ForegroundColor Green

# Download the unofficial PyAudio wheel for Python 3.14
$url = "https://github.com/intxcc/pyaudio_portaudio/releases/download/v19.7.1/PyAudio-0.2.14-cp314-cp314-win_amd64.whl"
$output = "PyAudio-0.2.14-cp314-cp314-win_amd64.whl"

Write-Host "Downloading PyAudio wheel..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $url -OutFile $output

Write-Host "Installing PyAudio..." -ForegroundColor Yellow
pip install $output

Write-Host "Installing SpeechRecognition..." -ForegroundColor Yellow
pip install speechrecognition

Write-Host "Cleaning up..." -ForegroundColor Yellow
Remove-Item $output

Write-Host "`nInstallation complete!" -ForegroundColor Green
Write-Host "You can now use voice input with KD6." -ForegroundColor Green
