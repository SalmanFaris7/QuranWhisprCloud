"""
quran_corpus.py — Three-tier data loading:
  1. Local cache (~/.quran_api/quran.json) — fastest
  2. CDN download (jsDelivr / unpkg) — full 6,236 verses
  3. Bundled fallback — Al-Fatiha + Al-Baqarah 1-5 for offline testing
"""

import re, json, difflib, pathlib
from typing import Optional

_CACHE_DIR  = pathlib.Path.home() / ".quran_api"
_CACHE_FILE = _CACHE_DIR / "quran.json"

_CDN_URLS = [
    "https://cdn.jsdelivr.net/npm/quran-json@3.1.2/dist/quran.json",
    "https://unpkg.com/quran-json@3.1.2/dist/quran.json",
]

# ── Bundled fallback data (offline / testing) ──────────────────────────────────
_BUNDLED = [
  {"id":1,"name":"Al-Fatihah","transliteration":"Al-Faatiha","verses":[
    {"id":1,"text":"بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ","transliteration":"Bismi Allahi alrrahmani alrraheemi","translation":"In the name of Allah, the Entirely Merciful, the Especially Merciful."},
    {"id":2,"text":"الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ","transliteration":"Alhamdu lillahi rabbi alAAalameena","translation":"[All] praise is [due] to Allah, Lord of the worlds -"},
    {"id":3,"text":"الرَّحْمَٰنِ الرَّحِيمِ","transliteration":"Alrrahmani alrraheemi","translation":"The Entirely Merciful, the Especially Merciful,"},
    {"id":4,"text":"مَالِكِ يَوْمِ الدِّينِ","transliteration":"Maliki yawmi alddeeni","translation":"Sovereign of the Day of Recompense."},
    {"id":5,"text":"إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ","transliteration":"Iyyaka naAAbudu waiyyaka nastaAAeenu","translation":"It is You we worship and You we ask for help."},
    {"id":6,"text":"اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ","transliteration":"Ihdina alssirata almustaqeema","translation":"Guide us to the straight path -"},
    {"id":7,"text":"صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ","transliteration":"Sirata allatheena anAAamta AAalayhim ghayri almaghdoobi AAalayhim wala alddalleena","translation":"The path of those upon whom You have bestowed favor, not of those who have evoked [Your] anger or of those who are astray."},
  ]},
  {"id":2,"name":"Al-Baqarah","transliteration":"Al-Baqara","verses":[
    {"id":1,"text":"الم","transliteration":"Alif Lam Meem","translation":"Alif, Lam, Meem."},
    {"id":2,"text":"ذَٰلِكَ الْكِتَابُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًى لِّلْمُتَّقِينَ","transliteration":"Thalika alkitabu la rayba feehi hudan lilmuttaqeena","translation":"This is the Book about which there is no doubt, a guidance for those conscious of Allah -"},
    {"id":3,"text":"الَّذِينَ يُؤْمِنُونَ بِالْغَيْبِ وَيُقِيمُونَ الصَّلَاةَ وَمِمَّا رَزَقْنَاهُمْ يُنفِقُونَ","transliteration":"Allatheena yuminoona bialghaybi wayuqeemoona alssalata wamimma razaqnahum yunfiqoona","translation":"Who believe in the unseen, establish prayer, and spend out of what We have provided for them,"},
    {"id":4,"text":"وَالَّذِينَ يُؤْمِنُونَ بِمَا أُنزِلَ إِلَيْكَ وَمَا أُنزِلَ مِن قَبْلِكَ وَبِالْآخِرَةِ هُمْ يُوقِنُونَ","transliteration":"Waallatheena yuminoona bima onzila ilayka wama onzila min qablika wabialakhirati hum yooqinoona","translation":"And who believe in what has been revealed to you, [O Muhammad], and what was revealed before you, and of the Hereafter they are certain [in faith]."},
    {"id":5,"text":"أُولَٰئِكَ عَلَىٰ هُدًى مِّن رَّبِّهِمْ ۖ وَأُولَٰئِكَ هُمُ الْمُفْلِحُونَ","transliteration":"Olaika AAala hudan min rabbihim waolaika humu almuflihoona","translation":"Those are upon [right] guidance from their Lord, and it is those who are the successful."},
  ]},
]


def _download_quran() -> list:
    import urllib.request
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for url in _CDN_URLS:
        try:
            print(f"[quran-api] Downloading corpus from {url} ...")
            urllib.request.urlretrieve(url, _CACHE_FILE)
            with open(_CACHE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            print(f"[quran-api] Full corpus cached → {_CACHE_FILE}")
            return data
        except Exception as e:
            print(f"[quran-api] CDN failed ({url}): {e}")
    print("[quran-api] ⚠️  Using bundled fallback (Al-Fatiha + Al-Baqarah 1-5 only).")
    print("[quran-api]    For the full corpus, download quran.json to ~/.quran_api/quran.json")
    return _BUNDLED


def _load_quran() -> list:
    if _CACHE_FILE.exists():
        with open(_CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return _download_quran()


_RAW: list = _load_quran()


# ── Arabic helpers ─────────────────────────────────────────────────────────────
def _strip_diacritics(text: str) -> str:
    return re.sub(r'[\u064B-\u065F\u0670]', '', text)

def _normalise(text: str) -> str:
    return re.sub(r'\s+', ' ', _strip_diacritics(text)).strip()


# ── Corpus class ───────────────────────────────────────────────────────────────
class QuranCorpus:
    def __init__(self):
        self._index: dict[tuple, dict] = {}
        for s in _RAW:
            sid  = int(s.get("id") or s.get("chapter_number", 0))
            name = s.get("name") or s.get("englishName", "")
            for v in (s.get("verses") or s.get("ayahs") or []):
                aid = int(v.get("id") or v.get("number") or v.get("verse_number", 0))
                self._index[(sid, aid)] = {
                    "surah": sid, "ayah": aid, "surah_name": name,
                    "text": v.get("text") or v.get("arabic", ""),
                    "transliteration": v.get("transliteration"),
                    "translation": v.get("translation") or v.get("englishText"),
                }
        print(f"[quran-api] {len(self._index)} verses ready")

    def get_verse(self, surah: int, ayah: int) -> Optional[dict]:
        return self._index.get((surah, ayah))

    def search(self, query: str, top_k: int = 5, surah_hint: int = None) -> list[dict]:
        q_norm     = _normalise(query)
        candidates = list(self._index.values())
        if surah_hint:
            candidates = [v for v in candidates if v["surah"] == surah_hint] or candidates
        scored = sorted(
            ((difflib.SequenceMatcher(None, q_norm, _normalise(v["text"])).ratio(), v)
             for v in candidates),
            key=lambda x: x[0], reverse=True
        )
        return [{**v, "match_score": round(r, 4)} for r, v in scored[:top_k]]

    def best_match(self, query, surah_hint=None, ayah_hint=None):
        if surah_hint and ayah_hint:
            verse = self.get_verse(surah_hint, ayah_hint)
            if verse:
                score = difflib.SequenceMatcher(
                    None, _normalise(query), _normalise(verse["text"])
                ).ratio()
                return verse, score
        results = self.search(query, top_k=1, surah_hint=surah_hint)
        return (results[0], results[0]["match_score"]) if results else (None, 0.0)
