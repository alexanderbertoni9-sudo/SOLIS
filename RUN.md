# Run SOLIS

## 1) Install once
```bash
./setup.sh
```
- First run may still take longer while model files download.

## 2) Generate an image
```bash
./run.sh
```
- This asks for a prompt.
- It saves the image and opens it in fullscreen on Raspberry Pi desktop.
- Press `Esc` or `q` to close fullscreen.
- During generation, Terminal shows live progress percentages.
- If no GUI display is available in that terminal session, the image is still generated and you will get an exact `xdg-open` command to run from desktop session.
- On Linux remote terminals, SOLIS now attempts to auto-attach to desktop display (`:0`) before skipping viewer.

## Optional: custom prompt
```bash
./run.sh --prompt "a picture of a dog and a cat"
```

## Optional: select model
```bash
./run.sh --model "segmind/tiny-sd" --prompt "a red fox in snow"
```

## Optional: lower memory usage
```bash
./run.sh --width 512 --height 512 --steps 15
```

## Output
- `output/solis_YYYYMMDD_HHMMSS_microseconds_<prompt>_s<seed>_<styleid>_<id>.png` (new image each run)
- `output/solis_latest.png` (latest copy)
