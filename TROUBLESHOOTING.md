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
sudo apt install -y build-essential libjpeg-dev zlib1g-dev libopenjp2-7
./setup.sh
```

## Dependency mismatch errors
If you see errors mentioning `transformers`, `torchvision`, or `torchaudio`:
```bash
rm -rf .venv
./setup.sh
```

## First run is slow
This is expected. The model downloads and initializes on first run.

## `Model load failed` or `Local model snapshot is incomplete`
Repair the local model snapshot:
```bash
rm -rf models/segmind-tiny-sd
./setup.sh
```

Then run again:
```bash
./run.sh
```

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

If viewer was skipped because no display was available, run from desktop session:
```bash
export DISPLAY=:0
export XAUTHORITY="$HOME/.Xauthority"
./run.sh
```

If needed, open it manually:
```bash
xdg-open "/absolute/path/to/your/new/image.png"
```

## Verify local model folder exists
```bash
ls models/segmind-tiny-sd
```
If that folder is missing, run `./setup.sh` again.
