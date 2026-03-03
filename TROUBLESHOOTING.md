# Troubleshooting

## `./setup.sh` or `./run.sh`: Permission denied
```bash
chmod +x setup.sh
chmod +x run.sh
```

## `.venv` missing when running `./run.sh`
Run setup first:
```bash
./setup.sh
```

## `python3: command not found`
Install Python 3:
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

## Dependency install failed on Raspberry Pi
Install build tools and try setup again:
```bash
sudo apt update
sudo apt install -y libjpeg-dev zlib1g-dev libopenjp2-7 build-essential
./setup.sh
```

## Error mentions `MT5Tokenizer` or `transformers`
Your environment likely has incompatible package versions. Recreate the venv with pinned versions:
```bash
rm -rf .venv
./setup.sh
```

## First run is slow
This is expected. The model downloads and initializes on first run.

## Regenerate environment from scratch
```bash
rm -rf .venv
./setup.sh
```

## Out of memory or process killed
Use lower settings:
```bash
./run.sh --width 512 --height 512 --steps 15
```

## Python version check
```bash
python3 --version
```
Use Python 3.9 or newer.

## Image did not auto-open on Pi
The image is still saved at:
- `output/solis_latest.png`
- `output/solis_*.png` (new uniquely named files)

If Terminal says viewer was skipped because no display is available, run the printed command from your desktop session.
You can also retry from remote terminal with:
```bash
export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"
./run.sh
```

Install tkinter if fullscreen window does not launch:
```bash
sudo apt update
sudo apt install -y python3-tk
```

If needed, open it manually:
```bash
xdg-open "/absolute/path/to/your/new/image.png"
```
