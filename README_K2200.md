# Chatterbox-Turbo on a 4 GB Maxwell GPU (Quadro K2200, sm_50)

Runs the full **Chatterbox-Turbo** model, with paralinguistic tags (`[angry]`, `[whispering]`, `[chuckle]` and the rest), on an old 4 GB card that the stock setup can't handle.

## Why the stock build fails

| Problem | Cause |
|---|---|
| CUDA kernels missing | CUDA 12.8 PyTorch wheels dropped sm_50. `torch 2.5.1+cu121` is the newest build that still ships Maxwell kernels. |
| Out of memory in fp32 | Turbo's T3 (GPT-2 medium) and S3Gen together don't fit in 4 GB with activations. |
| Garbled speech in fp16 | The S3Gen flow and HiFT vocoder lose intelligibility at half precision. |

## What this build does

`k2200_hybrid.py` splits the model:

- **T3** (the speech language model, where the expression comes from): fp16 on the GPU
- **S3Gen flow + vocoder**: fp32 on the GPU
- **S3Gen speech tokenizer** (only used to prepare a voice prompt): fp32 on the CPU

The voice-prompt prep runs on the CPU and is cached per prompt, so only the first request for a new voice is slow.

Measured on a Quadro K2200: peak VRAM about 2.3 GB (GPT-2 causal masks trimmed to 4096 positions), about 2.4x slower than real time, and ASR-clean output with working tags.

## Build and run

```bash
docker build -f Dockerfile.k2200 -t chatterbox:k2200 .
docker run -d --name chatterbox --runtime=nvidia \
  -e NVIDIA_VISIBLE_DEVICES=all -p 8004:8004 \
  -v $PWD/hf_cache:/app/hf_cache -v $PWD/voices:/app/voices \
  chatterbox:k2200
```

`config.yaml` defaults to `model.repo_id: chatterbox-turbo-k2200`. Other selectors:

- `chatterbox-turbo`: stock Turbo, for cards with more than 4 GB
- `chatterbox-nano`: 110M model. It runs faster than real time on the K2200 in fp32, but its expression is much weaker: it ignores `exaggeration` and `cfg_weight`.

## Notes

- The image is `python:3.10-slim` with GPU torch only, no CPU torch layer, build tools purged and triton removed (it needs sm_70+). It comes to about 6.4 GB.
- `docker/patch_chatterbox_f32.py` fixes a dtype bug in upstream `chatterbox-tts` 0.1.7: the reference clip loads as float64 and breaks the tokenizer and the voice encoder. The patch runs at build time.
- Only `s3gen_meanflow.safetensors` is loaded, so the 1 GB `s3gen.safetensors` is skipped when downloading.
- Upstream Chatterbox is archived and unmaintained, so these fixes live here.
