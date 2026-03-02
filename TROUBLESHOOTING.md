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

## Pillow install failed on Raspberry Pi
Install build tools and try setup again:
```bash
sudo apt update
sudo apt install -y libjpeg-dev zlib1g-dev libopenjp2-7
./setup.sh
```

## Regenerate environment from scratch
```bash
rm -rf .venv
./setup.sh
```

## Python version check
```bash
python3 --version
```
Use Python 3.9 or newer.
