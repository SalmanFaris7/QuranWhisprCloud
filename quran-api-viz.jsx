import { useState } from "react";

const FLOW_STEPS = [
  { id: 1, icon: "🎙️", label: "Audio Input", desc: "WAV · MP3 · M4A", color: "#C8A96E" },
  { id: 2, icon: "🤖", label: "Whisper ASR", desc: "Arabic large-v3 or tarteel-ai", color: "#7EB8A0" },
  { id: 3, icon: "📖", label: "Verse Matching", desc: "Fuzzy search · 6,236 verses", color: "#8BA7D4" },
  { id: 4, icon: "🔍", label: "Error Analysis", desc: "Word diff · Tajweed rules", color: "#C47B7B" },
  { id: 5, icon: "✅", label: "JSON Response", desc: "Errors · Score · Hints", color: "#A87BC4" },
];

const ENDPOINTS = [
  { method: "POST", path: "/recite", desc: "Upload audio → full analysis", badge: "main" },
  { method: "POST", path: "/analyze", desc: "Send text → error check (for on-device ASR)", badge: "" },
  { method: "GET",  path: "/verses/{surah}/{ayah}", desc: "Fetch a verse", badge: "" },
  { method: "GET",  path: "/search?q=", desc: "Find verse by Arabic text", badge: "" },
];

const ERROR_TYPES = [
  { type: "substitution", color: "#E8A0A0", example: "Said سِين instead of صَاد", icon: "↔" },
  { type: "deletion",     color: "#A0C4E8", example: "Skipped a word entirely", icon: "−" },
  { type: "insertion",    color: "#A0E8C4", example: "Added an extra word", icon: "+" },
  { type: "tajweed",      color: "#E8D5A0", example: "Wrong madd length or ghunna", icon: "~" },
];

const SAMPLE = {
  surah: 1, ayah: 1, surah_name: "Al-Fatihah",
  transcription: "بسم الله الرحمان الرحيم",
  expected_text: "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
  match_score: 0.94,
  errors: [
    { position: 2, recited: "الرحمان", expected: "الرَّحْمَٰنِ", type: "tajweed",
      hint: "Elongate the alif (madd 4-harakaat): الرَّحْمَٰن" }
  ],
  is_correct: false,
  message: "Good recitation with 1 error. Keep practising!"
};

export default function App() {
  const [activeTab, setActiveTab] = useState("arch");
  const [showJson, setShowJson] = useState(false);

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0F0E0C",
      color: "#E8E0D0",
      fontFamily: "'Georgia', 'Times New Roman', serif",
      padding: "0",
    }}>
      {/* Header */}
      <div style={{
        borderBottom: "1px solid #2A2820",
        padding: "32px 40px 24px",
        background: "linear-gradient(180deg, #1A1810 0%, #0F0E0C 100%)",
      }}>
        <div style={{ maxWidth: 900, margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 16, marginBottom: 8 }}>
            <span style={{ fontSize: 28 }}>☽</span>
            <h1 style={{ margin: 0, fontSize: 26, fontWeight: 400, letterSpacing: "0.04em", color: "#C8A96E" }}>
              Quran Recitation API
            </h1>
            <span style={{
              fontSize: 11, letterSpacing: "0.12em", color: "#6A6458",
              textTransform: "uppercase", alignSelf: "center",
            }}>v1.0</span>
          </div>
          <p style={{ margin: 0, color: "#8A8070", fontSize: 14, lineHeight: 1.6 }}>
            Whisper-powered speech recognition · Verse matching across 6,236 ayaat · Word-level Tajweed correction
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ borderBottom: "1px solid #2A2820", padding: "0 40px" }}>
        <div style={{ maxWidth: 900, margin: "0 auto", display: "flex", gap: 0 }}>
          {[["arch","Architecture"], ["endpoints","Endpoints"], ["response","Sample Response"]].map(([id, label]) => (
            <button key={id} onClick={() => setActiveTab(id)} style={{
              background: "none", border: "none", cursor: "pointer",
              padding: "14px 20px",
              fontSize: 13, letterSpacing: "0.06em",
              color: activeTab === id ? "#C8A96E" : "#6A6458",
              borderBottom: activeTab === id ? "2px solid #C8A96E" : "2px solid transparent",
              marginBottom: -1, transition: "all 0.2s",
            }}>{label}</button>
          ))}
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: "0 auto", padding: "32px 40px" }}>

        {/* Architecture Tab */}
        {activeTab === "arch" && (
          <div>
            {/* Flow */}
            <div style={{ display: "flex", alignItems: "center", gap: 0, marginBottom: 48, flexWrap: "wrap" }}>
              {FLOW_STEPS.map((step, i) => (
                <div key={step.id} style={{ display: "flex", alignItems: "center" }}>
                  <div style={{
                    background: "#1A1810",
                    border: `1px solid ${step.color}33`,
                    borderRadius: 8,
                    padding: "16px 20px",
                    textAlign: "center",
                    minWidth: 130,
                  }}>
                    <div style={{ fontSize: 24, marginBottom: 6 }}>{step.icon}</div>
                    <div style={{ color: step.color, fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{step.label}</div>
                    <div style={{ color: "#5A5448", fontSize: 11 }}>{step.desc}</div>
                  </div>
                  {i < FLOW_STEPS.length - 1 && (
                    <div style={{ color: "#3A3428", fontSize: 20, margin: "0 4px" }}>→</div>
                  )}
                </div>
              ))}
            </div>

            {/* Error Types */}
            <h2 style={{ fontSize: 14, letterSpacing: "0.1em", textTransform: "uppercase", color: "#6A6458", marginBottom: 16 }}>
              Error Classification
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 48 }}>
              {ERROR_TYPES.map(e => (
                <div key={e.type} style={{
                  background: "#1A1810", border: "1px solid #2A2820",
                  borderRadius: 8, padding: "14px 16px",
                  display: "flex", gap: 12, alignItems: "flex-start",
                }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: 6,
                    background: e.color + "22", color: e.color,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 16, flexShrink: 0, fontFamily: "monospace",
                  }}>{e.icon}</div>
                  <div>
                    <div style={{ color: e.color, fontSize: 12, fontWeight: 600, marginBottom: 2 }}>{e.type}</div>
                    <div style={{ color: "#5A5448", fontSize: 12 }}>{e.example}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Models */}
            <h2 style={{ fontSize: 14, letterSpacing: "0.1em", textTransform: "uppercase", color: "#6A6458", marginBottom: 16 }}>
              Recommended ASR Models
            </h2>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #2A2820", color: "#6A6458", textAlign: "left" }}>
                  {["Model", "Size", "Quran WER", "Best For"].map(h => (
                    <th key={h} style={{ padding: "8px 12px", fontWeight: 400, letterSpacing: "0.06em", fontSize: 11, textTransform: "uppercase" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  ["whisper base",        "74M",   "~18%", "Fast testing"],
                  ["whisper large-v3",    "1.5GB", "~5%",  "High accuracy"],
                  ["tarteel-ai (★ recommended)", "74M", "~3%", "Production – Quran fine-tuned"],
                ].map(([m, s, w, b], i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #1A1810", color: i === 2 ? "#C8A96E" : "#A09080" }}>
                    <td style={{ padding: "10px 12px", fontFamily: "monospace", fontSize: 12 }}>{m}</td>
                    <td style={{ padding: "10px 12px" }}>{s}</td>
                    <td style={{ padding: "10px 12px" }}>{w}</td>
                    <td style={{ padding: "10px 12px", color: "#6A6458" }}>{b}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Endpoints Tab */}
        {activeTab === "endpoints" && (
          <div>
            <div style={{ marginBottom: 32 }}>
              {ENDPOINTS.map((ep, i) => (
                <div key={i} style={{
                  background: "#1A1810", border: "1px solid #2A2820",
                  borderRadius: 8, padding: "16px 20px", marginBottom: 10,
                  display: "flex", alignItems: "center", gap: 16,
                }}>
                  <span style={{
                    fontFamily: "monospace", fontSize: 11,
                    background: ep.method === "POST" ? "#C8A96E22" : "#7EB8A022",
                    color: ep.method === "POST" ? "#C8A96E" : "#7EB8A0",
                    padding: "3px 8px", borderRadius: 4, fontWeight: 700, minWidth: 44, textAlign: "center",
                  }}>{ep.method}</span>
                  <code style={{ color: "#E8E0D0", fontSize: 14, fontFamily: "monospace", flex: 1 }}>
                    {ep.path}
                  </code>
                  {ep.badge && (
                    <span style={{ background: "#C8A96E22", color: "#C8A96E", fontSize: 10, padding: "2px 6px", borderRadius: 3, letterSpacing: "0.08em" }}>
                      MAIN
                    </span>
                  )}
                  <span style={{ color: "#5A5448", fontSize: 12 }}>{ep.desc}</span>
                </div>
              ))}
            </div>

            {/* Quick start */}
            <h2 style={{ fontSize: 14, letterSpacing: "0.1em", textTransform: "uppercase", color: "#6A6458", marginBottom: 12 }}>
              Quick Start
            </h2>
            <pre style={{
              background: "#1A1810", border: "1px solid #2A2820",
              borderRadius: 8, padding: 20, fontSize: 12,
              color: "#A09080", lineHeight: 1.8, overflowX: "auto",
            }}>{`# Install
pip install -r requirements.txt

# Run
uvicorn main:app --reload --port 8000

# Test with curl
curl -X POST http://localhost:8000/recite \\
  -F "audio=@fatiha.wav" \\
  -F "surah=1" \\
  -F "ayah=1"

# Text-only (if you have a transcription already)
curl -X POST http://localhost:8000/analyze \\
  -H "Content-Type: application/json" \\
  -d '{"text":"بسم الله الرحمن الرحيم","surah":1,"ayah":1}'`}</pre>
          </div>
        )}

        {/* Sample Response Tab */}
        {activeTab === "response" && (
          <div>
            <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
              <button onClick={() => setShowJson(false)} style={{
                background: !showJson ? "#C8A96E22" : "none",
                border: `1px solid ${!showJson ? "#C8A96E44" : "#2A2820"}`,
                color: !showJson ? "#C8A96E" : "#6A6458",
                padding: "6px 14px", borderRadius: 6, cursor: "pointer", fontSize: 12,
              }}>Visual</button>
              <button onClick={() => setShowJson(true)} style={{
                background: showJson ? "#C8A96E22" : "none",
                border: `1px solid ${showJson ? "#C8A96E44" : "#2A2820"}`,
                color: showJson ? "#C8A96E" : "#6A6458",
                padding: "6px 14px", borderRadius: 6, cursor: "pointer", fontSize: 12,
              }}>Raw JSON</button>
            </div>

            {!showJson ? (
              <div>
                <div style={{ background: "#1A1810", border: "1px solid #2A2820", borderRadius: 8, padding: 20, marginBottom: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
                    <div>
                      <span style={{ color: "#C8A96E", fontSize: 18 }}>Al-Fatihah</span>
                      <span style={{ color: "#5A5448", marginLeft: 12, fontSize: 13 }}>1:1</span>
                    </div>
                    <div style={{
                      background: "#E8D5A022", color: "#E8D5A0",
                      padding: "4px 12px", borderRadius: 20, fontSize: 12,
                    }}>94% match</div>
                  </div>
                  <div style={{ borderBottom: "1px solid #2A2820", paddingBottom: 14, marginBottom: 14 }}>
                    <div style={{ fontSize: 11, color: "#5A5448", marginBottom: 6, letterSpacing: "0.08em" }}>RECITED</div>
                    <div style={{ fontSize: 20, direction: "rtl", lineHeight: 2, fontFamily: "serif" }}>
                      بسم الله{" "}
                      <span style={{ background: "#E8A0A022", borderRadius: 4, padding: "0 4px", border: "1px solid #E8A0A044" }}>
                        الرحمان
                      </span>{" "}
                      الرحيم
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: "#5A5448", marginBottom: 6, letterSpacing: "0.08em" }}>EXPECTED</div>
                    <div style={{ fontSize: 20, direction: "rtl", lineHeight: 2, fontFamily: "serif", color: "#7EB8A0" }}>
                      بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
                    </div>
                  </div>
                </div>

                {SAMPLE.errors.map((e, i) => (
                  <div key={i} style={{
                    background: "#1A1810", border: "1px solid #E8D5A033",
                    borderRadius: 8, padding: 16, display: "flex", gap: 14,
                  }}>
                    <div style={{
                      width: 32, height: 32, borderRadius: 6,
                      background: "#E8D5A022", color: "#E8D5A0",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 14, flexShrink: 0,
                    }}>~</div>
                    <div>
                      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                        <span style={{ background: "#E8D5A022", color: "#E8D5A0", fontSize: 11, padding: "2px 6px", borderRadius: 3 }}>tajweed</span>
                        <span style={{ color: "#5A5448", fontSize: 12 }}>position {e.position}</span>
                      </div>
                      <div style={{ fontSize: 13, color: "#A09080" }}>{e.hint}</div>
                    </div>
                  </div>
                ))}

                <div style={{ marginTop: 12, background: "#1A1810", border: "1px solid #2A2820", borderRadius: 8, padding: 14 }}>
                  <span style={{ color: "#E8D5A0" }}>{SAMPLE.message}</span>
                </div>
              </div>
            ) : (
              <pre style={{
                background: "#1A1810", border: "1px solid #2A2820",
                borderRadius: 8, padding: 20, fontSize: 12,
                color: "#A09080", lineHeight: 1.8, overflowX: "auto",
              }}>{JSON.stringify(SAMPLE, null, 2)}</pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
