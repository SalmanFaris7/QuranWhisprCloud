# 📖 Quran Recitation API

A Whisper-powered REST API that listens to Quran recitation, matches it against the Quran corpus, and returns word-level error corrections with Tajweed hints.

---

## Architecture

```
Audio (WAV/MP3/M4A)
        │
        ▼
┌───────────────────┐
│  Whisper large-v3 │  ← Arabic ASR (speech → text)
│  (openai-whisper) │
└────────┬──────────┘
         │ transcription (Arabic text)
         ▼
┌───────────────────┐
│  QuranCorpus      │  ← Fuzzy match against 6,236 verses
│  (difflib ratio)  │
└────────┬──────────┘
         │ matched verse + score
         ▼
┌───────────────────┐
│  RecitationAnalyz │  ← Word-level diff (SequenceMatcher)
│  + Tajweed hints  │     + phonetic substitution rules
└────────┬──────────┘
         │
         ▼
     JSON Response
  (errors, hints, score)
```

---

## Setup

```bash
# 1. Clone / copy this folder
cd quran-api

# 2. Create virtualenv
python -m venv venv && source venv/bin/activate

# 3. Install deps
pip install -r requirements.txt

# 4. Run (development)
uvicorn main:app --reload --port 8000
```

Interactive docs → http://localhost:8000/docs

---

## API Endpoints

### `POST /recite`
Upload audio, get full analysis.

**Form params:**
| Param   | Type | Required | Description |
|---------|------|----------|-------------|
| `audio` | file | ✅ | WAV / MP3 / M4A recording |
| `surah` | int  | ❌ | Expected surah (improves matching speed) |
| `ayah`  | int  | ❌ | Expected ayah |

**Response:**
```json
{
  "surah": 1,
  "ayah": 1,
  "surah_name": "Al-Fatihah",
  "transcription": "بسم الله الرحمان الرحيم",
  "expected_text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
  "match_score": 0.94,
  "errors": [
    {
      "position": 2,
      "recited": "الرحمان",
      "expected": "الرَّحْمَٰنِ",
      "type": "tajweed",
      "hint": "Elongate the alif (madd): الرَّحْمَٰن has a 4-harakat madd"
    }
  ],
  "is_correct": false,
  "message": "Good recitation with 1 error(s). Keep practising!"
}
```

---

### `POST /analyze`
If you do ASR on-device (e.g. mobile Whisper), send the text directly.

```json
{
  "text": "بسم الله الرحمن الرحيم",
  "surah": 1,
  "ayah": 1
}
```

---

### `GET /verses/{surah}/{ayah}`
Fetch a verse.

```
GET /verses/1/1
```

---

### `GET /search?q=<arabic>`
Find which verse matches a piece of Arabic text.

---

## Error Types

| Type | Meaning |
|------|---------|
| `substitution` | Wrong word |
| `deletion` | Word was skipped |
| `insertion` | Extra word added |
| `tajweed` | Correct word but phonetic/tajweed issue |

---

## Upgrade Path

| Feature | How |
|---------|-----|
| Better Arabic ASR | Replace `whisper` with `tarteel-ai/whisper-base-ar-quran` (fine-tuned on Quran) |
| Real Tajweed engine | Integrate `quran-tajweed` library |
| Verse-by-verse session | Add `POST /session` + WebSocket streaming |
| Makhraj analysis | Use forced-alignment (wav2vec2) per phoneme |
| Mobile SDK | Wrap `/analyze` for on-device Whisper (iOS/Android) |

---

## Models

| Whisper Model | Size | Arabic WER | RAM |
|---------------|------|------------|-----|
| `tiny`        | 39M  | ~25%       | 1GB |
| `base`        | 74M  | ~18%       | 1GB |
| `medium`      | 769M | ~9%        | 5GB |
| `large-v3`    | 1.5B | ~5%        | 10GB|
| `tarteel-ai/whisper-base-ar-quran` | 74M | ~3% (Quran-specific) | 1GB |

> **Recommendation**: Use `tarteel-ai` model for production – it's fine-tuned on Quran audio and outperforms large-v3 for this specific task.
