# Copy/Paste Start (Beginner Friendly)

Run these commands exactly in this order.

## 1) Go to the SOLIS folder
```bash
cd /Users/alexander.bertoni/Documents/GitHub/SOLIS
```

## 2) Install everything (one time)
```bash
./setup.sh
```
- This step installs Python packages and downloads the local model into `models/segmind-tiny-sd`.

## 3) Generate one image
```bash
./run.sh
```
- You will be asked for a prompt.
- Press Enter to use the default prompt.
- Fullscreen opens immediately.
- You can watch the image being generated live.
- Press `Esc` or `q` to close fullscreen.
- Setup may be slower the first time because model files download.

Your image will be saved here:
- `output/solis_YYYYMMDD_HHMMSS_microseconds_<prompt>_s<seed>_<styleid>_<id>.png`
- `output/solis_latest.png` (copy of newest image)

## 4) Generate with your own prompt (optional)
```bash
./run.sh --prompt "a picture of a dog and a cat"
```

## 5) Use a smaller image on Raspberry Pi (faster)
```bash
./run.sh --prompt "a picture of a dog and a cat" --width 512 --height 512 --steps 15
```

## 6) If model files ever break, repair them
```bash
rm -rf models/segmind-tiny-sd
./setup.sh
```
