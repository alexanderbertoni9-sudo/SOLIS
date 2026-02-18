# SOLIS Troubleshooting

## `./run.sh` says permission denied
```bash
chmod +x run.sh
```

## Out of disk space on Raspberry Pi
```bash
df -h
```
- Remove pip cache: `rm -rf ~/.cache/pip`
- Remove old virtual env and reinstall clean:
```bash
rm -rf .venv
./run.sh
```

## Fullscreen window does not appear
- Confirm display is connected before boot.
- If running via SSH, start from the local desktop session.

## PyTorch / diffusers install is too large
- This is expected on small SD cards.
- Use a larger card (64GB+ recommended).
- Free space before install:
```bash
sudo apt clean
sudo apt autoremove -y
```

## App exits immediately
- Check Python version:
```bash
python3 --version
```
- Recommended: Python 3.10+

## Slow first run
- Initial model download is large and can take several minutes.
- Later runs are faster because assets are cached.
