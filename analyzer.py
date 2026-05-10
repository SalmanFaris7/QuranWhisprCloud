"""
analyzer.py
===========
Compares a transcription against the matched Quran verse
and produces word-level error annotations.
"""

import re
import difflib
from typing import Optional

from quran_corpus import QuranCorpus, _normalise, _strip_diacritics


# ── Common tajweed / phonetic substitution patterns ───────────────────────────
# These are simplified heuristics; a full tajweed engine is a separate project.
TAJWEED_HINTS = {
    # Idgham / Ikhfa pairs (letters that should merge/nasalise)
    ("ن", "م"): "Idgham – the noon should merge into the meem (غنّة)",
    ("ن", "ن"): "Idgham mutamaathilayn – double noon merges with ghunna",
    ("ا", "ء"): "Hamza confusion – check the seat of the hamza",
    # Common letter substitutions beginners make
    ("ث", "س"): "ث (Tha) ≠ س (Sin) – place tongue between teeth for ث",
    ("ذ", "ز"): "ذ (Dhal) ≠ ز (Zain) – tongue-tip vs. blade",
    ("ص", "س"): "ص (Saad) is heavy/emphatic; س (Sin) is light",
    ("ض", "د"): "ض (Daad) is emphatic and unique to Arabic",
    ("ظ", "ذ"): "ظ (Dhaa) is emphatic; ذ (Dhal) is light",
    ("ق", "ك"): "ق (Qaaf) is deeper in the throat than ك (Kaaf)",
    ("ع", "ا"): "ع (Ain) requires constriction of the pharynx",
    ("ح", "ه"): "ح (Haa) is a pharyngeal consonant – not a simple ه (Ha)",
    ("خ", "ك"): "خ (Khaa) has friction; ك (Kaaf) is a stop",
}


def _first_letter(word: str) -> str:
    """Return the first Arabic letter of a word (skip hamza seats etc.)."""
    for ch in word:
        if '\u0600' <= ch <= '\u06FF':
            return ch
    return ""


def _get_tajweed_hint(recited: str, expected: str) -> Optional[str]:
    r1 = _strip_diacritics(recited)
    e1 = _strip_diacritics(expected)
    if r1 == e1:
        return None
    pair = (_first_letter(r1), _first_letter(e1))
    return TAJWEED_HINTS.get(pair)


def _tokenise(text: str) -> list[str]:
    """Split Arabic text into word tokens, removing empty strings."""
    return [w for w in re.split(r'\s+', text.strip()) if w]


class RecitationAnalyzer:
    def __init__(self, corpus: QuranCorpus):
        self.corpus = corpus

    def analyze(
        self,
        transcription: str,
        hint_surah: Optional[int] = None,
        hint_ayah:  Optional[int] = None,
    ) -> dict:
        """
        1. Match transcription to best verse.
        2. Compute word-level diff (opcodes).
        3. Annotate each mismatch with type + tajweed hint.
        """
        # ── 1. Find best verse ─────────────────────────────────────────────────
        verse, score = self.corpus.best_match(
            transcription,
            surah_hint=hint_surah,
            ayah_hint=hint_ayah,
        )

        if not verse:
            return {
                "surah": 0, "ayah": 0, "surah_name": "Unknown",
                "transcription": transcription,
                "expected_text": "",
                "match_score": 0.0,
                "errors": [],
                "is_correct": False,
                "message": "Could not match recitation to any verse.",
            }

        expected_text = verse["text"]

        # ── 2. Tokenise (strip diacritics for comparison) ──────────────────────
        rec_words  = _tokenise(_strip_diacritics(transcription))
        exp_words  = _tokenise(_strip_diacritics(expected_text))
        exp_original = _tokenise(expected_text)          # keep diacritics for display

        # ── 3. Sequence diff ───────────────────────────────────────────────────
        sm      = difflib.SequenceMatcher(None, rec_words, exp_words, autojunk=False)
        errors  = []

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue

            if tag == "replace":
                # Align pairs; handle length mismatches
                for k in range(max(i2-i1, j2-j1)):
                    rec_w = rec_words[i1+k]  if (i1+k) < i2 else ""
                    exp_w = exp_words[j1+k]  if (j1+k) < j2 else ""
                    exp_d = exp_original[j1+k] if (j1+k) < len(exp_original) else exp_w
                    hint  = _get_tajweed_hint(rec_w, exp_w)
                    errors.append({
                        "position": j1 + k,
                        "recited":  rec_w,
                        "expected": exp_d,
                        "type":     "tajweed" if hint else "substitution",
                        "hint":     hint or f'Expected "{exp_d}", got "{rec_w}"',
                    })

            elif tag == "insert":
                # Words missing from the recitation
                for k in range(j2 - j1):
                    exp_d = exp_original[j1+k] if (j1+k) < len(exp_original) else exp_words[j1+k]
                    errors.append({
                        "position": j1 + k,
                        "recited":  "",
                        "expected": exp_d,
                        "type":     "deletion",
                        "hint":     f'Missing word: "{exp_d}"',
                    })

            elif tag == "delete":
                # Extra words the reciter added
                for k in range(i2 - i1):
                    errors.append({
                        "position": j1,
                        "recited":  rec_words[i1+k],
                        "expected": "",
                        "type":     "insertion",
                        "hint":     f'Extra word: "{rec_words[i1+k]}" should not be here',
                    })

        # ── 4. Build response ──────────────────────────────────────────────────
        is_correct = score >= 0.95 and len(errors) == 0

        if is_correct:
            msg = "ما شاء الله – Excellent recitation! 🌟"
        elif score >= 0.80:
            msg = f"Good recitation with {len(errors)} error(s). Keep practising!"
        elif score >= 0.50:
            msg = f"Partial match ({round(score*100)}%). Please recite more clearly."
        else:
            msg = "Could not confidently match this recitation. Please try again."

        return {
            "surah":         verse["surah"],
            "ayah":          verse["ayah"],
            "surah_name":    verse["surah_name"],
            "transcription": transcription,
            "expected_text": expected_text,
            "match_score":   round(score, 4),
            "errors":        errors,
            "is_correct":    is_correct,
            "message":       msg,
        }
