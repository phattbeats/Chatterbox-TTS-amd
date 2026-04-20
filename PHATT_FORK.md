# PHATT TECH FORK — AMD ROCm for Windows

**Unofficial fork of [devnen/Chatterbox-TTS-Server](https://github.com/devnen/Chatterbox-TTS-Server)**
Adds AMD ROCm support for Windows (AMD Radeon RX 6000 series, gfx1030/gfx1031/gfx1032).

> :zap: **2.3x faster than CPU** on short-turn multi-voice inference (RTF 1.30x on RX 6750 XT, measured April 2026)

---

## Hardware Requirements

| Component | Requirement |
|---|---|
| GPU | AMD Radeon RX 6000 series (gfx1030/gfx1031/gfx1032) — RX 6700, 6750 XT, 6800 XT confirmed |
| VRAM | 8 GB minimum, 12 GB recommended |
| OS | Windows 11 (build 22H2+) |
| Python | 3.12 |
| Driver | AMD ROCm for Windows 6.2+ |

### Unsupported

- NVIDIA GPUs (CUDA path not available on this fork)
- AMD RX 7000 series (gfx1100+) — may work, untested
- Windows 10

---

## Installation

### 1. Install (one-time)

```bash
python start.py --rocm-windows
```

The launcher will:
- Detect your AMD GPU via Vulkan (no ROCm runtime required for detection)
- Download 5 wheel files from GitHub (~2.4 GB total)
- Install PyTorch ROCm + ROCm SDK locally (no pip index needed)
- Patch the Chatterbox watermarker to be gracefully optional
- Print an experimental warning (expected — ROCm on Windows is unofficial)

### 2. Run

```bash
python start.py
```

Server starts on `http://localhost:8000`. GPU acceleration is automatic when AMD GPU is available.

---

## What Changed

### `engine.py` — cudnn/MIOpen disabled on gfx103X Windows

HIP convolutions crash with `0xC0000005` on AMD RX 6000 series under Windows ROCm. This fork disables `torch.backends.cudnn.enabled` automatically when a gfx103X AMD GPU is detected on Windows.

```python
if torch.cuda.is_available() and platform.system() == "Windows":
    props = torch.cuda.get_device_properties(0)
    if getattr(props, 'gcnArchName', '').startswith('gfx103'):
        torch.backends.cudnn.enabled = False
```

No-op on NVIDIA GPUs, Linux ROCm, or non-gfx103X AMD GPUs.

### `utils.py` — soundfile fallback for audio export

`torchaudio.save()` fails on standard Windows Python (requires FFmpeg DLLs). This fork falls back to `soundfile` automatically when torchaudio cannot save.

### `start.py` — `--rocm-windows` flag

New install type that pre-flight checks for AMD gfx103X GPU before installing. Prints experimental banner after install.

---

## Known Limitations

- **ROCm on Windows is experimental.** AMD's official position is that ROCm is not supported on Windows. This fork exists because some users have it working.
- **No commercial support.** For commercial deployment of GPU-accelerated Chatterbox TTS, consult the official devnen repository.
- **RX 7000 series untested.** Your mileage may vary.
- **Audio export uses soundfile fallback** on standard Windows Python — functionally equivalent but slightly different encoding path than the torchaudio path on Linux.

---

## Troubleshooting

### `torch.cuda.is_available()` returns False

1. Verify AMD GPU is detected: `python -c "import torch; print(torch.cuda.get_device_name(0))"`
2. Check AMD driver is current: [amd.com/drive](https://www.amd.com/en/support)
3. Verify ROCm is installed: `rocm-smi` in a command prompt

### Server crashes on generation

Check if it's a HIP/convolution crash (0xC0000005). If so, verify the cudnn disable patch in `engine.py` is applied. The `start.py` launcher patches this automatically.

### Wheels fail to download

The launcher downloads wheel files from GitHub releases. If download fails, check your network connection and try again. If the problem persists, open an issue at [github.com/phattbeats/Chatterbox-TTS-Server](https://github.com/phattbeats/Chatterbox-TTS-Server/issues).

---

## Upstream Tracking

This fork tracks `devnen/Chatterbox-TTS-Server`. To rebase on latest upstream:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

The `feature/rocm-windows-support` branch will be kept up to date with upstream changes.

---

## Credits

- **AMD TheRock (guinmoon)** — pre-built ROCm wheels for Windows
- **PHATT TECH** — packaging, integration testing
- **devnen** — upstream Chatterbox TTS Server

See [NOTICE](./NOTICE) for full attribution.
