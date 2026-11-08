"""Patch upstream chatterbox 0.1.7 (archived, unmaintained): librosa loads the
reference clip as float64, which breaks the s3tokenizer STFT and the voice
encoder LSTM ("expected scalar type Double but found Float"). Cast to float32
at the two entry points. Idempotent; fails the build if the anchors move."""
import pathlib, sys, chatterbox
root = pathlib.Path(chatterbox.__file__).parent
edits = [
    (root / "tts_turbo.py",
     "        ref_16k_wav = librosa.resample(s3gen_ref_wav, orig_sr=S3GEN_SR, target_sr=S3_SR)\n",
     "        s3gen_ref_wav = s3gen_ref_wav.astype(\"float32\")\n"
     "        ref_16k_wav = librosa.resample(s3gen_ref_wav, orig_sr=S3GEN_SR, target_sr=S3_SR).astype(\"float32\")\n"),
    (root / "models" / "s3tokenizer" / "s3tokenizer.py",
     "        audio = audio.to(self.device)\n",
     "        audio = audio.to(self.device, dtype=torch.float32)\n"),
]
for path, old, new in edits:
    src = path.read_text()
    if new in src:
        continue
    if old not in src:
        sys.exit(f"patch anchor not found in {path}")
    path.write_text(src.replace(old, new, 1))
print("chatterbox float32 patch applied")
