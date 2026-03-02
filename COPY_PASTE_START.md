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

Your image will be saved here:
- `output/solis_latest.png`

## 4) Generate with your own prompt (optional)
```bash
./run.sh --prompt "A bright solar-powered city, cinematic lighting"
```

## 5) Use a smaller image on Raspberry Pi (faster)
```bash
./run.sh --prompt "Wind turbines over the ocean" --width 512 --height 512
```
