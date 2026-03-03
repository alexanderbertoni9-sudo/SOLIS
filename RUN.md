# Run SOLIS

## 1) Install once
```bash
./setup.sh
```
- First run may take longer due model download.

## 2) Generate an image
```bash
./run.sh
```
- Prompts interactively if not provided.
- Opens fullscreen and shows live generation previews.
- Holds final image until `Esc` or `q`.

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

## Optional: deterministic output
```bash
./run.sh --prompt "a cat and a dog" --seed 1234
```

## Output
- `output/solis_YYYYMMDD_HHMMSS_microseconds_<prompt>_s<seed>_<styleid>_<id>.png` (new image each run)
- `output/solis_latest.png` (latest copy)
