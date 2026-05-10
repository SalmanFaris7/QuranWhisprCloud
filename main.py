"""
Quran Recitation API
====================
Accepts audio of Quran recitation, transcribes with Tarteel AI,
matches against the Quran corpus, and returns word-level error analysis.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import tempfile, os, re, subprocess
import difflib
import librosa

# ── ASR Model (Tarteel AI - Quran-tuned) ──────────────────────────────────────
try:
    from transformers import (
        pipeline,
        GenerationConfig,
        WhisperForConditionalGeneration,
        AutoProcessor,
    )

    model = WhisperForConditionalGeneration.from_pretrained("tarteel-ai/whisper-base-ar-quran")
    model.generation_config = GenerationConfig.from_pretrained("openai/whisper-base")

    processor = AutoProcessor.from_pretrained("tarteel-ai/whisper-base-ar-quran")

    asr = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        device="cpu",
    )
    ASR_AVAILABLE = True
    print("[quran-api] ✅ Tarteel ASR model loaded")

except ImportError:
    asr = None
    ASR_AVAILABLE = False
    print("[quran-api] ⚠️ ASR not available (install transformers + torch)")

from quran_corpus import QuranCorpus
from analyzer import RecitationAnalyzer

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Quran Recitation API",
    description="Transcribe & error-correct Quran recitation audio",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

corpus   = QuranCorpus()
analyzer = RecitationAnalyzer(corpus)

# ── Schemas ────────────────────────────────────────────────────────────────────
class WordError(BaseModel):
    position: int
    recited: str
    expected: str
    type: str
    hint: Optional[str]

class RecitationResult(BaseModel):
    surah: int
    ayah: int
    surah_name: str
    transcription: str
    expected_text: str
    match_score: float
    errors: list[WordError]
    is_correct: bool
    message: str

class VerseResponse(BaseModel):
    surah: int
    ayah: int
    surah_name: str
    text: str
    transliteration: Optional[str]
    translation: Optional[str]

class AnalyzeTextRequest(BaseModel):
    text: str
    surah: int
    ayah: int

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "Quran Recitation API"}

@app.get("/verses/{surah}/{ayah}", response_model=VerseResponse, tags=["Quran"])
def get_verse(surah: int, ayah: int):
    verse = corpus.get_verse(surah, ayah)
    if not verse:
        raise HTTPException(404, f"Verse {surah}:{ayah} not found")
    return verse

@app.get("/search", tags=["Quran"])
def search_verse(q: str = Query(..., description="Arabic text to search for")):
    results = corpus.search(q, top_k=5)
    return {"query": q, "results": results}

@app.post("/recite", response_model=RecitationResult, tags=["Recitation"])
async def recite(
    audio: UploadFile = File(...),
    surah: Optional[int] = Query(None),
    ayah:  Optional[int] = Query(None),
):
    if not ASR_AVAILABLE:
        raise HTTPException(503, "ASR not available. Run: pip install transformers torch")

    suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        tmp.flush()
        tmp_path = tmp.name

    wav_path = tmp_path + ".wav"

    try:
        # Convert any format → 16kHz mono WAV
        subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_path, "-vn", "-ar", "16000", "-ac", "1", wav_path],
            capture_output=True,
            check=True,
        )

        # Load as numpy array
        audio_array, sr = librosa.load(wav_path, sr=16000, mono=True)

        # Transcribe
        audio_array, sr = librosa.load(wav_path, sr=16000, mono=True)
        duration = len(audio_array) / sr

        if duration > 30:
            # Long audio → chunked processing
            result = asr(
                audio_array,
                return_timestamps=True,
                chunk_length_s=30,
                stride_length_s=[6, 0],
            )
        else:
            # Short audio → single pass (faster)
            result = asr(audio_array, return_timestamps=False)

        transcription = result["text"].strip()

    except subprocess.CalledProcessError as e:
        raise HTTPException(400, f"ffmpeg conversion failed: {e.stderr.decode()}")
    except Exception as e:
        raise HTTPException(400, f"Transcription failed: {str(e)}")

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if os.path.exists(wav_path):
            os.unlink(wav_path)

    return analyzer.analyze(transcription, hint_surah=surah, hint_ayah=ayah)

@app.post("/analyze", response_model=RecitationResult, tags=["Recitation"])
def analyze_text(req: AnalyzeTextRequest):
    return analyzer.analyze(req.text, hint_surah=req.surah, hint_ayah=req.ayah)