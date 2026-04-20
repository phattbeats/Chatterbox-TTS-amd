# PHATT TECH Fork — AMD ROCm for Windows

**Unofficial fork of [devnen/Chatterbox-TTS-Server](https://github.com/devnen/Chatterbox-TTS-Server)**
Adds AMD Radeon RX 6000 series GPU support to Chatterbox TTS Server on Windows 11.

> **RTF 1.30x** on RX 6750 XT — 2.3x faster than CPU (measured April 2026)

---

## Prerequisites

Before installing, make sure your system has:

| | |
|---|---|
| **GPU** | AMD Radeon RX 6700 / 6750 XT / 6800 XT (gfx1030/gfx1031/gfx1032) |
| **OS** | Windows 11 (22H2 or later) |
| **AMD Driver** | Latest from [amd.com/support](https://www.amd.com/en/support) |
| **AMD ROCm** | Install from [amd.com/rocm](https://rocm.docs.amd.com/en/latest/deploy/windows/quick-start.html) — required for GPU inference |
| **Python** | 3.10 or later (installer will find it; [python.org/downloads](https://www.python.org/downloads/) if missing) |

### Unsupported

- NVIDIA GPUs — use the [upstream Chatterbox TTS Server](https://github.com/devnen/Chatterbox-TTS-Server) instead
- AMD RX 7000 series (gfx1100+) — may work, unconfirmed
- Windows 10

---

## Quick Start

### One-click install + run

**Double-click `start.bat`** — this runs the full install automatically.

On first run it will:
1. Detect your AMD GPU
2. Download ROCm + PyTorch wheel files (~2.4 GB from GitHub)
3. Install everything into a virtual environment
4. Start the server at `http://localhost:8000`

That's it. You don't need to install Python manually, download wheels separately, or run any commands.

### After first install

Just double-click `start.bat` again to launch. It will skip the download and start the server directly.

### `start-rocm.bat` — same thing

`start-rocm.bat` is an alias for the same launcher. Use whichever you prefer.

---

## How It Works

This fork makes four changes to the upstream Chatterbox TTS Server:

1. **AMD GPU detection (Windows)** — upstream uses `rocm-smi` which only runs on Linux. This fork detects AMD GPUs using Windows-native tools (Vulkan ICD + registry), no ROCm runtime required for detection.

2. **ROCm wheel install** — downloads pre-built ROCm + PyTorch wheels from the [v0.1.0-rocm-wheels release](https://github.com/phattbeats/Chatterbox-TTS-Server/releases/tag/v0.1.0-rocm-wheels) (~2.4 GB) and installs from local files. No pip index lookup needed.

3. **HIP crash fix** — AMD HIP convolutions crash (`0xC0000005`) on gfx103X GPUs under Windows ROCm. This fork disables `torch.backends.cudnn.enabled` when an AMD gfx103X GPU is detected on Windows.

4. **Audio export** — `torchaudio.save()` requires FFmpeg DLLs on Windows. The fork falls back to `soundfile` automatically when torchaudio cannot save.

---

## Troubleshooting

### "AMD GPU: Not detected"

Your AMD GPU is not visible to the detection script. Check:
- AMD driver is installed and up to date at [amd.com/support](https://www.amd.com/en/support)
- AMD ROCm is installed (required for GPU inference, not just detection)
- Your GPU is RX 6000 series — other AMD GPUs are not confirmed working

### Server starts but is slow

GPU acceleration is not active. Verify ROCm is working:

```cmd
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

If it returns `False`, ROCm is not installed or not recognized. Reinstall ROCm from [amd.com/rocm](https://rocm.docs.amd.com/en/latest/deploy/windows/quick-start.html).

### Wheel download fails or is slow

The launcher downloads ~2.4 GB from GitHub. If your connection is slow or interrupted:
- The downloaded wheels are cached in the `wheels/` folder — re-running `start.bat` will skip already-downloaded files
- If you need to start fresh, delete the `wheels/` folder and run `start.bat` again

### "ROCm wheel install had issues" warning

The PyTorch/ROCm wheels failed to install. This is most commonly caused by:
1. Python version mismatch — make sure you have Python 3.10 or 3.12 (not 3.11)
2. Insufficient disk space (~5 GB free needed for the full install)

---

## Upstream

This fork tracks `devnen/Chatterbox-TTS-Server`. To rebase on latest upstream:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Credits

- **guinmoon (AMD TheRock)** — pre-built ROCm wheels for Windows
- **devnen** — upstream [Chatterbox TTS Server](https://github.com/devnen/Chatterbox-TTS-Server)
- **PHATT TECH** — fork integration and validation

Full attribution in [NOTICE](./NOTICE).
