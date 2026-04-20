# ROCm Windows Installation Guide

This page explains how to install ROCm-enabled PyTorch wheels on Windows from the PHATT TECH release.

## Prerequisites

- Windows 10/11 (64-bit)
- AMD GPU: RX 6000 series (gfx1030/gfx1031/gfx1032) — **required for ROCm**
- AMD ROCm SDK installed (see wheels below)
- Python 3.12
- pip updated: `python -m pip install --upgrade pip`

## Download Wheels

Wheels are hosted as GitHub Release assets at:

**https://github.com/phattbeats/Chatterbox-TTS-Server/releases/tag/v0.1.0-rocm-wheels**

Download all 7 files to a local folder, e.g. `C:\Users\PHATT\Downloads\guinmoon-wheels\`:

| File | Size | Purpose |
|------|------|---------|
| `rocm-7.1.1.tar.gz` | 16 KB | ROCm runtime |
| `rocm_sdk_core-7.1.1-py3-none-win_amd64.whl` | 621 MB | ROCm SDK core |
| `rocm_sdk_devel-7.1.1-py3-none-win_amd64.whl` | 1.26 GB | ROCm SDK dev libraries |
| `rocm_sdk_libraries_gfx103x_all-7.1.1-py3-none-win_amd64.whl` | 202 MB | gfx103X-specific libs |
| `torch-2.9.1+rocmsdk20251207-cp312-cp312-win_amd64.whl` | 513 MB | PyTorch with ROCm support |
| `torchaudio-2.9.0+rocmsdk20251207-cp312-cp312-win_amd64.whl` | 503 KB | Torchaudio |
| `torchvision-0.24.0+rocmsdk20251207-cp312-cp312-win_amd64.whl` | 1.7 MB | Torchvision |

**Total: ~2.1 GB**

## Install Order

Install wheels in this exact order using `pip install <file>` from an elevated PowerShell or Command Prompt:

```powershell
cd C:\Users\PHATT\Downloads\guinmoon-wheels

pip install rocm-7.1.1.tar.gz

pip install rocm_sdk_core-7.1.1-py3-none-win_amd64.whl
pip install rocm_sdk_devel-7.1.1-py3-none-win_amd64.whl
pip install rocm_sdk_libraries_gfx103x_all-7.1.1-py3-none-win_amd64.whl

pip install torch-2.9.1+rocmsdk20251207-cp312-cp312-win_amd64.whl
pip install torchaudio-2.9.0+rocmsdk20251207-cp312-cp312-win_amd64.whl
pip install torchvision-0.24.0+rocmsdk20251207-cp312-cp312-win_amd64.whl
```

> ⚠️ Install `torch` **last** within its group — pip will resolve CUDA/cuDNN dependencies from the ROCm SDK wheels already installed.

## Verify Installation

```powershell
python -c "import torch; print(torch.__version__); print('ROCm' if torch.version.hip else 'CUDA', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No GPU')"
```

Expected output: `2.9.1+rocmsdk20251207` with ROCm and your AMD GPU name.

## Launch Chatterbox TTS Server

After installing the wheels, run the server:

```powershell
python -m chatterbox_tts
```

Or using the PHATT TECH fork directly:

```powershell
git clone https://github.com/phattbeats/Chatterbox-TTS-Server.git
cd Chatterbox-TTS-Server
pip install -e .
python -m chatterbox_tts
```

## Troubleshooting

### `HIP error 0xC0000005` on startup or generation

This is caused by MIOpen convolution kernels crashing on gfx103X under Windows ROCm. The fix is already applied in the `engine.py` of the PHATT TECH fork — it disables `cudnn` when a gfx103X AMD GPU is detected on Windows.

If you are using an older install, set this **before** importing torch:

```powershell
$env:PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True"
```

Or in Python before `import torch`:

```python
import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import torch
torch.backends.cudnn.enabled = False  # Required for gfx103X on Windows ROCm
```

### GPU not detected

1. Verify ROCm is installed: `rocm-smi` in Command Prompt
2. Verify GPU is visible: `torch.cuda.is_available()` returns `True`
3. If using WSL2, ensure GPU passthrough is enabled in Windows features

### pip install fails with "not a supported wheel on this platform"

Ensure you are using **Python 3.12** (`python --version`). These wheels are built for `cp312-cp312-win_amd64`.

## Wheels Structure

These wheels follow [PEP 503](https://peps.python.org/pep-0503/) naming conventions and can be installed via pip with `--find-links`:

```powershell
pip install torch --find-links="C:\Users\PHATT\Downloads\guinmoon-wheels"
```

This is useful for CI/CD or repeated installs — pip will prefer local wheels over PyPI.
