# Troubleshooting

## `./run.sh`: Permission denied
```bash
chmod +x run.sh
```

## Not enough space on Raspberry Pi
Check free space:
```bash
df -h
```
Free package and pip cache:
```bash
sudo apt clean
sudo apt autoremove -y
rm -rf ~/.cache/pip
```
Rebuild virtual environment:
```bash
rm -rf .venv
./run.sh
```

## Install is too large
- `torch` and `diffusers` are large by design.
- Use a larger SD card (64 GB recommended for smoother operation).
- Keep extra free space for model cache growth.

## No fullscreen window appears
- Make sure a monitor is connected before app launch.
- If you are connected over SSH, run from the local desktop session.

## App exits immediately
Check Python:
```bash
python3 --version
```
Use Python 3.10 or newer.

## First run is very slow
First run downloads model assets and builds local caches. Later runs are faster.
