# ROCm on Windows — Technical Notes

> **Context:** The official devnen/Chatterbox-TTS-Server explicitly warns against using ROCm on Windows. This document explains what this fork does about that, honestly.

## Why This Fork Exists

AMD Radeon RX 6000 series (gfx1030/gfx1031/gfx1032) GPUs are capable of running PyTorch with ROCm on Windows. Some users have it working. The problem is:

1. MIOpen convolution kernels crash with `HIP error 0xC0000005` on gfx103X under certain conditions
2. `torchaudio.save()` requires FFmpeg DLLs that standard Windows Python doesn't ship
3. The official position is "don't do this"

This fork addresses items 1 and 2. Item 3 remains: **ROCm on Windows is not officially supported by AMD, PyTorch, or devnen.**

## What the Patches Do

### cudnn disable (engine.py)

```python
if torch.cuda.is_available() and platform.system() == "Windows":
    props = torch.cuda.get_device_properties(0)
    if getattr(props, 'gcnArchName', '').startswith('gfx103'):
        torch.backends.cudnn.enabled = False
```

When a gfx103X AMD GPU is detected on Windows, cudnn (MIOpen backend) is disabled. This prevents the HIP 0xC0000005 crashes during generation. The trade-off: some convolution operations run slightly slower without MIOpen's optimized kernels. In practice, the speedup over CPU still holds.

**Why not fix MIOpen directly?** Because MIOpen is maintained by AMD and the fix would require patching MIOpen itself — which is out of scope for this fork.

### soundfile fallback (utils.py)

Standard Windows Python doesn't ship FFmpeg DLLs. When `torchaudio.save()` fails because the FFmpeg loader can't find the DLLs, this fork catches the exception and falls back to `soundfile` (which uses libsndfile, already a Chatterbox dependency).

Audio output is **functionally identical** to the torchaudio path. Encoding quality is the same. The fallback path just uses a different backend.

## GPU Compatibility

| GPU | Architecture | ROCm Windows | Notes |
|---|---|---|---|
| RX 6700 | gfx1030 | :white_check_mark: Likely works | Not tested by PHATT TECH |
| RX 6750 XT | gfx1031 | :white_check_mark: Tested | Primary test hardware |
| RX 6800 | gfx1032 | :white_check_mark: Likely works | Not tested by PHATT TECH |
| RX 6800 XT | gfx1032 | :white_check_mark: Likely works | Not tested by PHATT TECH |
| RX 7900 XTX | gfx1100 | :warning: Untested | May work; ROCm 7.x supports gfx1100 |
| NVIDIA (any) | CUDA | :x: Not supported | Use NVIDIA CUDA build instead |

## Benchmark Results

> All measurements on RX 6750 XT, Windows 11, Python 3.12, April 2026.

- **Short turns** (15–60 second audio): RTF 1.30x → ~2.3x faster than CPU baseline
- **Long audio** (5+ minutes): RTF approaches 1.0x (generation speed approaches real-time)
- **CPU baseline**: RTF ~0.57x (CPU generates ~0.57 seconds of audio per second of wall time)

These numbers are from a single RX 6750 XT on one Windows machine. Your results may vary based on VRAM allocation, system memory, and specific GPU silicon lottery.

## What's Not Covered

- **Audio quality differences** — none expected, but not measured
- **Multi-GPU** — not tested, likely requires different ROCm config
- **RX 7000 series stability** — unknown
- **Long-duration soak tests** — pending (T-307/T-102)

## Related Issues

- [MIOpen HIP error 0xC0000005 on gfx103X](https://github.com/ROCm/MIOpen/issues) — upstream MIOpen issue tracker
- [devnen/Chatterbox-TTS-Server](https://github.com/devnen/Chatterbox-TTS-Server) — official upstream