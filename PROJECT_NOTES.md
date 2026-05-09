# Chatterbox-TTS-amd — Project Notes

**Repository:** phattbeats/Chatterbox-TTS-amd  
**Upstream:** devnen/Chatterbox-TTS-Server  
**Purpose:** AMD ROCm support for Windows (RX 6000 series, gfx1030/1031/1032)  
**Date completed:** May 2026

---

## What This Fork Does

Upstream (devnen) explicitly states ROCm is Linux-only. This fork proves it wrong for RX 6000 series on Windows, using guinmoon's pre-built ROCm SDK wheels instead of the official ROCm installer. Result: **2.3x faster than CPU** on short-turn inference (RTF 1.30x on an RX 6750 XT).

The entire diff is 4 files:

| File | What Changed |
|---|---|
| `engine.py` | Disable cudnn on gfx103X Windows (prevents HIP crash 0xC0000005) |
| `utils.py` | soundfile fallback for torchaudio.save (fixes audio export on torchaudio 2.9+) |
| `start.py` | `--rocm-windows` flag, pre-flight GPU check, experimental banner |
| `requirements-rocm-windows.txt` | 7 pre-built wheels pinned from wheels.phatt.vip |

---

## Issue-by-Issue Story

### Phase 0 — Setup and Research

**PHA-257: Read docs, create issues and subissues**

The starting point. Brandon had execution logs from running on his Windows 11 desktop with an RX 6750 XT. The original plan doc (`plan.md`) mapped out 4 tracks: Infrastructure (T-1xx), Code patches (T-3xx), Documentation (T-4xx), and wheel hosting (T-2xx). This issue produced the full breakdown of all subsequent work.

---

### Phase 1 — Infrastructure

**PHA-259: T-301: Fork repo and configure upstream tracking**

Forked `devnen/Chatterbox-TTS-Server` to `phattbeats/Chatterbox-TTS-Server`. Created the `feature/rocm-windows-support` branch. Set up `upstream` remote pointing to devnen so we can pull upstream improvements in the future.

**PHA-267: T-202: Upload and structure the 7 guinmoon wheels**

The key enabling infrastructure. guinmoon built 7 Windows ROCm wheels that don't exist in the official PyPI or PyTorch wheel index:
- `rocm==7.1.1`
- `rocm-sdk-core==7.1.1`
- `rocm-sdk-devel==7.1.1`
- `rocm-sdk-libraries-gfx103x-all==7.1.1`
- `torch==2.9.1+rocmsdk20251207`
- `torchaudio==2.9.0+rocmsdk20251207`
- `torchvision==0.20.0+rocmsdk20251207`

These were uploaded from Brandon's machine (`C:\Users\PHATT\Downloads\guinmoon-rocm\`) to `/mnt/user/appdata/pip-index/rocm-windows/` on the NAS and structured as a PEP 503 simple index, served at `https://wheels.phatt.vip/rocm-windows/simple/`.

**PHA-269: T-204: Smoke test from clean VM**

Validation that the wheel server works from a cold start:
```
pip install --index-url https://wheels.phatt.vip/rocm-windows/simple/ rocm torch torchaudio torchvision
python -c "import torch; print(torch.cuda.is_available())"
```
All 7 wheels downloaded; `torch.cuda.is_available()` printed `True` on gfx1030. The infrastructure works.

---

### Phase 2 — Code Patches

**PHA-260: T-302: Patch chatterbox/tts.py — perth watermarker fallback**

Resemble AI's chatterbox uses a perth watermarker that crashes if the native binary isn't available. Added a try/except fallback to a `DummyWatermarker` in `start.py` (applied as an automatic post-install patch, idempotent). This also exists in the upstream's `start.py` — confirmed the patch is consistent.

**PHA-263: T-305: Write requirements-rocm-windows.txt**

New file pinning all 7 guinmoon wheels plus the rest of the server's Python dependencies. Uses `--extra-index-url` to pull from `wheels.phatt.vip` and falls back to PyPI for everything else. Chatterbox itself is installed separately with `--no-deps` to prevent pip's resolver from replacing the ROCm torch wheels with CPU-only versions.

**T-303: Disable cudnn on gfx103X Windows (in `engine.py`)**

The critical fix. On Windows with an RX 6000 series card, HIP's cudnn backend crashes with error `0xC0000005` (access violation). Disabling cudnn via `torch.backends.cudnn.enabled = False` before model load prevents the crash entirely. This is gated on `--rocm-windows` flag so it doesn't affect Linux or NVIDIA users.

**T-304: soundfile fallback in `utils.py`**

On torchaudio 2.9+, `torchaudio.save()` changed its interface. Added a fallback path using `soundfile` directly when torchaudio fails. This keeps audio export working across torchaudio versions.

---

### Phase 3 — Documentation

**PHA-270: T-401: README header**

Added a fork header to the upstream README so visitors immediately know this is an AMD Windows fork, what GPUs are supported, and the measured speedup. The header is compact (under 15 lines) and doesn't bury the upstream documentation.

**PHA-271: T-402: PHATT_FORK.md**

Full fork documentation file (later condensed and merged into README to reduce redundant .md files — see PHA-277).

**PHA-273: T-404: Soften upstream ROCm-Windows warning**

Upstream README says "ROCm is not supported on Windows." Added an escape hatch note pointing to the `--rocm-windows` flag for RX 6000 series specifically, preserving the upstream warning for unsupported hardware.

**PHA-274: T-103: Write validation-report.md**

Documented 7 days of soak testing on Brandon's RX 6750 XT:
- Hardware: RX 6750 XT, Windows 11, driver 24.3.1
- RTF: ~1.30x (faster than real-time on short turns)
- Wall time: varies by text length
- Known limitations: longer texts show VRAM pressure; CUDA 12.x incompatibilities on gfx1030 require the cudnn disable patch

---

### Phase 4 — Testing and Release

**PHA-265: T-307: Local smoke test on Brandon's hardware**

Fresh clone on the RX 6750 XT machine. `python start.py --rocm-windows` succeeded end-to-end: model downloaded, loaded on ROCm device, first TTS generation completed. Zero manual file editing required. Time from git clone to first generation: under 15 minutes.

**PHA-275: Create 1.0.0 release**

First release tag. Goal: zip it, unzip it, double-click `start.bat`, it works. The portable Windows installer already handles Python environment setup — the ROCm path just needed the `--rocm-windows` flag and the correct requirements file to be documented clearly.

---

### Phase 5 — Debugging and Polish

**PHA-276: v1.0.0 debugging**

The 1.0.0 release had issues. `start.bat` was finding Python but failing silently during the ROCm install step. Root cause: the install menu didn't have a clear ROCm-Windows option, and the `--rocm-windows` flag wasn't wired into the interactive launcher flow. Fixed by adding the option to the menu and the detection logic.

**PHA-283: Recover stalled issue PHA-276**

PHA-276 stalled when the agent exhausted automatic recovery. This recovery issue got the debugging back on track by reviewing the full error logs and identifying the specific failure point in `start.py`'s installation menu.

**PHA-277: Make instructions clearer, remove redundant .md files**

After v1.0.0, the docs had overlapping content across README, PHATT_FORK.md, and validation-report.md. Consolidated into README + docs/ structure. Removed PHATT_FORK.md as standalone file (content absorbed into README). Added a quick-start section to README for the most common path: fresh Windows install with AMD GPU.

---

### Phase 6 — Final Cleanup (this issue)

**PHA-720: Rename repository, fix authorship, write summary**

- Repository renamed: `Chatterbox-TTS-Server` → `Chatterbox-TTS-amd`
- All fork commits now authored by `phattbeats <obiwouldjablowme@protonmail.com>`
- Removed all vendor branding from documentation (replaced with "AMD Windows fork")
- Condensed the fork header in README
- This document written

---

## Technical Notes

### Why guinmoon's wheels?

AMD's official ROCm for Windows is a large SDK (5+ GB installer). guinmoon's approach is a pip-installable meta-package that pulls just the runtime libraries needed for PyTorch. The 7 wheels total ~2 GB download versus the full SDK. The catch: these are unofficial builds, tested only on gfx103X (RX 6000 series). For gfx1100 (RX 7000 series) they're untested.

### Why Python 3.12?

The ROCm wheels from guinmoon are built for Python 3.12. The upstream project requires Python 3.10 for ONNX wheel compatibility. This fork's ROCm-Windows path uses Python 3.12 specifically — the `--rocm-windows` flag bypasses the 3.10 enforcement.

### The cudnn disable

`torch.backends.cudnn.enabled = False` is a blunt instrument. It prevents HIP from using cudnn's implementations and falls back to HIP's native ops. On gfx103X, the native HIP ops are stable; cudnn's Windows port has the crash. The performance impact is minimal on inference workloads.

### Measured Performance (RX 6750 XT)

- **CPU baseline:** RTF ~3.0x (3 seconds to generate 1 second of audio)
- **ROCm (this fork):** RTF ~1.30x (30% slower than real-time on short turns)
- **Speedup:** 2.3x over CPU
- **VRAM usage:** ~4 GB peak on the original Chatterbox model

---

## Credits

- **devnen** — original Chatterbox TTS Server (upstream)
- **Resemble AI** — Chatterbox TTS model
- **guinmoon** — Windows ROCm SDK wheels that made this possible
- **AMD TheRock** — the build system guinmoon used to compile the wheels
