# Copy/Paste Start (Beginner Friendly)

If you are new, run these commands exactly in this order.

## 1) Open Terminal in this SOLIS folder
You should be inside the project folder before running commands.

## 2) Install everything (one time)
```bash
./setup.sh
```

## 3) Generate one image
```bash
./run.sh
```
- You will be asked for a prompt.
- Press Enter to use the default prompt.
- On Raspberry Pi desktop, the image opens in fullscreen.
- Press `Esc` or `q` to close fullscreen.
- If you launched from a terminal without GUI display access, it will still save the image and print the `xdg-open` command for desktop session.
- First run may be slower because the text-to-image model downloads.

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
