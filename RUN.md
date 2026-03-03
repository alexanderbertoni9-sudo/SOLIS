# Run SOLIS

## 1) Install once
```bash
./setup.sh
```
- Setup may take longer due one-time model download/verification.

## 2) Generate an image
```bash
./run.sh
```
- A built-in prompt is selected randomly each run.
- Opens fullscreen and shows live generation previews.
- `Esc` or `q` cancels generation if still running, or closes final image.

## Optional: select model
```bash
./run.sh --model "segmind/tiny-sd"
```

## Optional: use a specific local model directory
```bash
./run.sh --model "segmind/tiny-sd" --model-dir "./models/segmind-tiny-sd"
```

## Optional: use remote model id (advanced)
If you pass a non-default model id and no `--model-dir`, runtime may download that model:
```bash
./run.sh --model "runwayml/stable-diffusion-v1-5"
```

## Optional: lower memory usage
```bash
./run.sh --width 512 --height 512 --steps 15
```

## Optional: deterministic output
```bash
./run.sh --seed 1234
```

## Output
- `output/solis_YYYYMMDD_HHMMSS_microseconds_<prompt>_s<seed>_<styleid>_<id>.png` (new image each run)
- `output/solis_latest.png` (latest copy)

## Repair model snapshot
```bash
rm -rf models/segmind-tiny-sd
./setup.sh
```
