# Run SOLIS

## 1) Install once
```bash
./setup.sh
```

## 2) Generate an image
```bash
./run.sh
```
- This asks for a prompt.
- It saves the image and opens it in fullscreen on Raspberry Pi desktop.
- Press `Esc` or `q` to close fullscreen.

## Optional: custom prompt
```bash
./run.sh --prompt "A clean energy city at sunset"
```

## Output
- `output/solis_YYYYMMDD_HHMMSS_microseconds_<prompt>_s<seed>_<styleid>_<id>.png` (new image each run)
- `output/solis_latest.png` (latest copy)
