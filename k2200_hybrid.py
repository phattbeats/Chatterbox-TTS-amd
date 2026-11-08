"""Run full Chatterbox-Turbo on a 4 GB Maxwell card (Quadro K2200, sm_50).

Turbo in fp32 is ~3 GB of weights plus activations: it does not fit.
Turbo in fp16 end to end fits but the S3Gen vocoder/flow garbles speech.
What works (verified 2026-11-07, ASR-clean, peak ~3.4 GB, RTF ~2.4):
  * T3 (the GPT-2-medium speech LM, where the expression lives): fp16 on GPU
  * S3Gen flow + HiFT vocoder: fp32 on GPU
  * S3Gen speech tokenizer (only used to prepare a voice prompt): fp32 on CPU
Voice-prompt prep (prepare_conditionals) runs on CPU, then the conditionals
are moved to the GPU with matching dtypes, and cached per prompt path."""
import logging, torch

log = logging.getLogger(__name__)
H = torch.float16


def _conds_to_gpu(model):
    model.conds.t3 = model.conds.t3.to(device="cuda", dtype=H)
    model.conds.gen = {k: (v.to("cuda") if torch.is_tensor(v) else v) for k, v in model.conds.gen.items()}


def apply(model):
    """Patch a loaded (CPU) ChatterboxTurboTTS in place into the hybrid layout."""
    model.t3 = model.t3.to("cuda", dtype=H)
    g = model.s3gen
    g.to("cuda")
    g.tokenizer.to("cpu")
    # S3Gen reports its device from the tokenizer; force it to report cuda so the
    # flow/vocoder inputs land on the GPU.
    g.__class__ = type("S3GenK2200", (type(g),), {"device": property(lambda s: torch.device("cuda"))})
    model.device = "cuda"
    if model.conds is not None:
        _conds_to_gpu(model)

    cpu_prepare = model.prepare_conditionals
    cache = {}

    def prepare_conditionals(wav_fpath, exaggeration=0.0, norm_loudness=True):
        key = (str(wav_fpath), norm_loudness)
        if key in cache:
            model.conds = cache[key]
            return
        # run the prompt prep on CPU: tokenizer, voice encoder and resampling
        g.__class__.device = property(lambda s: torch.device("cpu"))
        model.device = "cpu"
        g.to("cpu")
        try:
            cpu_prepare(wav_fpath, exaggeration=exaggeration, norm_loudness=norm_loudness)
        finally:
            g.to("cuda"); g.tokenizer.to("cpu")
            g.__class__.device = property(lambda s: torch.device("cuda"))
            model.device = "cuda"
        _conds_to_gpu(model)
        cache[key] = model.conds

    model.prepare_conditionals = prepare_conditionals
    torch.cuda.empty_cache()
    log.info("K2200 hybrid layout applied: T3 fp16 GPU, S3Gen fp32 GPU, tokenizer CPU. VRAM %d MB",
             torch.cuda.memory_allocated() // 2**20)
    return model
