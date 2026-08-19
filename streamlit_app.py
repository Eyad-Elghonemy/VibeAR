"""
VibeAR — Arabic Sentiment Analysis Console
==========================================
Single-file Streamlit interface for the hosted VibeAR API.
Design: dark, LTR-first English UI with selective Arabic accent lines.

Run:
    pip install streamlit requests pillow
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import base64
import csv
from collections import Counter
import html as _html
import io
import json
import time
from datetime import datetime

import requests
import streamlit as st
from PIL import Image

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

API_BASE = "https://vibear-0eb67d30.fastapicloud.dev"   # built into the page
API_BASE_DEFAULT = API_BASE
_DEMO_KEY = "c0c2d9d05029aed5d5174ff5ff8e6d88"

def _secret(name: str, fallback: str) -> str:
    """Prefers .streamlit/secrets.toml so the key never has to live in the source."""
    try:
        return str(st.secrets[name])
    except Exception:
        return fallback


API_KEY_DEFAULT = _secret("VIBEAR_API_KEY", _DEMO_KEY)

# Brand logo (embedded so the app stays a single file)
LOGO_SVG_B64 = (
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDI0IDEwMjQiIHdpZHRoPSIxMDI0"
    "IiBoZWlnaHQ9IjEwMjQiPgogIDxkZWZzPgogICAgPCEtLSBCYWNrZ3JvdW5kIEdyYWRpZW50IChEYXJrIE1vZGUpIC0tPgogICAg"
    "PGxpbmVhckdyYWRpZW50IGlkPSJiZy1ncmFkIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0"
    "b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iIzBGMTcyQSIgLz4KICAgICAgPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9y"
    "PSIjMDIwNjE3IiAvPgogICAgPC9saW5lYXJHcmFkaWVudD4KCiAgICA8IS0tIFRlYWwgR3JhZGllbnQgKFBvc2l0aXZlIC0gRmFz"
    "dEFQSSBWaWJlKSAtLT4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0idGVhbC1ncmFkIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUi"
    "IHkyPSIwJSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiMxNEI4QTYiIC8+CiAgICAgIDxzdG9wIG9mZnNl"
    "dD0iMTAwJSIgc3RvcC1jb2xvcj0iIzBEOTQ4OCIgLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CgogICAgPCEtLSBPcmFuZ2UgR3Jh"
    "ZGllbnQgKE5lZ2F0aXZlIC0gc2Npa2l0LWxlYXJuIFZpYmUpIC0tPgogICAgPGxpbmVhckdyYWRpZW50IGlkPSJvcmFuZ2UtZ3Jh"
    "ZCIgeDE9IjAlIiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMCUiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIj"
    "Rjk3MzE2IiAvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNFQTU4MEMiIC8+CiAgICA8L2xpbmVhckdy"
    "YWRpZW50PgogIDwvZGVmcz4KCiAgPCEtLSBTcXVhcmUgQ2FudmFzIHdpdGggcm91bmRlZCBjb3JuZXJzIC0tPgogIDxyZWN0IHdp"
    "ZHRoPSIxMDI0IiBoZWlnaHQ9IjEwMjQiIGZpbGw9InVybCgjYmctZ3JhZCkiIHJ4PSIyMjUiIC8+CgogIDwhLS0gQ2xhc3NpZmlj"
    "YXRpb24gUGF0aHMgLS0+CiAgPGc+CiAgICA8IS0tIFBhdGggdG8gTmVnYXRpdmUgKERvd24pIC0tPgogICAgPHBhdGggZD0iTSAz"
    "MjAgNTEyIEMgNTIwIDUxMiwgNTIwIDc2MCwgNjgwIDc2MCIgCiAgICAgICAgICBmaWxsPSJub25lIiAKICAgICAgICAgIHN0cm9r"
    "ZT0idXJsKCNvcmFuZ2UtZ3JhZCkiIAogICAgICAgICAgc3Ryb2tlLXdpZHRoPSI1MCIgCiAgICAgICAgICBzdHJva2UtbGluZWNh"
    "cD0icm91bmQiIC8+CiAgICAgICAgICAKICAgIDwhLS0gUGF0aCB0byBQb3NpdGl2ZSAoVXApIC0tPgogICAgPHBhdGggZD0iTSAz"
    "MjAgNTEyIEMgNTIwIDUxMiwgNTIwIDI2NCwgNjgwIDI2NCIgCiAgICAgICAgICBmaWxsPSJub25lIiAKICAgICAgICAgIHN0cm9r"
    "ZT0idXJsKCN0ZWFsLWdyYWQpIiAKICAgICAgICAgIHN0cm9rZS13aWR0aD0iNTAiIAogICAgICAgICAgc3Ryb2tlLWxpbmVjYXA9"
    "InJvdW5kIiAvPgoKICAgIDwhLS0gSW5wdXQgTm9kZSAoVGhlIFRleHQpIC0tPgogICAgPGNpcmNsZSBjeD0iMzIwIiBjeT0iNTEy"
    "IiByPSI2MCIgZmlsbD0iI0UyRThGMCIgLz4KICAgIDxjaXJjbGUgY3g9IjMyMCIgY3k9IjUxMiIgcj0iMjAiIGZpbGw9IiMwRjE3"
    "MkEiIC8+CgogICAgPCEtLSBQb3NpdGl2ZSBOb2RlIC0tPgogICAgPGNpcmNsZSBjeD0iNzAwIiBjeT0iMjY0IiByPSI3NSIgZmls"
    "bD0idXJsKCN0ZWFsLWdyYWQpIiAvPgogICAgPCEtLSBQbHVzIHNpZ24gZm9yIHBvc2l0aXZlIC0tPgogICAgPHBhdGggZD0iTSA2"
    "NjUgMjY0IEwgNzM1IDI2NCBNIDcwMCAyMjkgTCA3MDAgMjk5IiAKICAgICAgICAgIHN0cm9rZT0iIzBGMTcyQSIgCiAgICAgICAg"
    "ICBzdHJva2Utd2lkdGg9IjE2IiAKICAgICAgICAgIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgLz4KCiAgICA8IS0tIE5lZ2F0aXZl"
    "IE5vZGUgLS0+CiAgICA8Y2lyY2xlIGN4PSI3MDAiIGN5PSI3NjAiIHI9Ijc1IiBmaWxsPSJ1cmwoI29yYW5nZS1ncmFkKSIgLz4K"
    "ICAgIDwhLS0gTWludXMgc2lnbiBmb3IgbmVnYXRpdmUgLS0+CiAgICA8cGF0aCBkPSJNIDY2NSA3NjAgTCA3MzUgNzYwIiAKICAg"
    "ICAgICAgIHN0cm9rZT0iIzBGMTcyQSIgCiAgICAgICAgICBzdHJva2Utd2lkdGg9IjE2IiAKICAgICAgICAgIHN0cm9rZS1saW5l"
    "Y2FwPSJyb3VuZCIgLz4KICA8L2c+Cjwvc3ZnPgo="
)
LOGO_PNG_B64 = (
    "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"
)
LOGO_SVG_URI = "data:image/svg+xml;base64," + LOGO_SVG_B64
LOGO_PNG_URI = "data:image/png;base64," + LOGO_PNG_B64

_FAVICON = Image.open(io.BytesIO(base64.b64decode(LOGO_PNG_B64)))

st.set_page_config(
    page_title="VibeAR · Arabic Sentiment Console",
    page_icon=_FAVICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Design system
# ──────────────────────────────────────────────────────────────────────────────

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=Tajawal:wght@500;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

:root{
  --bg:#06070c;
  --rail:#0a0c12;
  --glass:rgba(255,255,255,.045);
  --glass-2:rgba(255,255,255,.075);
  --stroke:rgba(255,255,255,.10);
  --stroke-2:rgba(255,255,255,.18);
  --txt:#e8ebf5;
  --muted:#8f98b0;
  --faint:#828ba3;
  --cy:#22d3ee;
  --vi:#a78bfa;
  --pk:#f472b6;
  --gr:#34d399;
  --am:#fbbf24;
  --rd:#fb7185;
  --r:18px;
}

/* ── Canvas ─────────────────────────────────────────── */
.stApp{
  direction:ltr;
  background:
    radial-gradient(1100px 620px at 88% -8%, rgba(167,139,250,.18), transparent 60%),
    radial-gradient(950px 560px at 8% 4%, rgba(34,211,238,.14), transparent 62%),
    radial-gradient(800px 500px at 50% 108%, rgba(244,114,182,.11), transparent 60%),
    linear-gradient(180deg,#06070c 0%,#080a11 55%,#06070c 100%);
  background-attachment:fixed;
  color:var(--txt);
  font-family:'Inter',system-ui,sans-serif;
}
.stApp::before{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:linear-gradient(rgba(255,255,255,.02) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(255,255,255,.02) 1px,transparent 1px);
  background-size:52px 52px;
  mask-image:radial-gradient(circle at 50% 20%,#000 12%,transparent 70%);
}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stToolbar"]{display:none !important;}
[data-testid="stMainBlockContainer"]{padding-top:2.1rem;max-width:1180px;}
footer, #MainMenu{visibility:hidden;}

/* ── Arabic accent blocks ───────────────────────────── */
.ar{
  direction:rtl;text-align:right;unicode-bidi:isolate;
  font-family:'Tajawal',sans-serif;font-weight:500;
}
.ar-line{
  max-width:44rem;margin-inline-end:auto;padding:.55rem 1.05rem .55rem 0;
  border-right:2px solid rgba(34,211,238,.45);
  background:linear-gradient(270deg,rgba(34,211,238,.07),transparent 70%);
  border-radius:12px 0 0 12px;
  direction:rtl;text-align:right;unicode-bidi:isolate;
  font-family:'Tajawal',sans-serif;font-weight:700;
  font-size:clamp(1.05rem,1.9vw,1.45rem);line-height:1.95;
  margin:.9rem 0 0;
  background:linear-gradient(100deg,#22d3ee,#7dd3fc,#a78bfa,#22d3ee);
  background-size:320% 100%;
  -webkit-background-clip:text;background-clip:text;
  -webkit-text-fill-color:transparent;
  animation:flow 8s ease-in-out infinite, glow 5s ease-in-out infinite;
}
.ar-note{
  max-width:46rem;margin-inline-end:auto;
  direction:rtl;text-align:right;unicode-bidi:isolate;
  font-family:'Tajawal',sans-serif;font-weight:500;font-size:1.02rem;line-height:2.05;
  color:#cbd3ea;background:linear-gradient(90deg,rgba(167,139,250,.10),rgba(34,211,238,.04));
  border-right:3px solid var(--vi);border-radius:0 14px 14px 0;
  padding:.9rem 1.15rem;margin:1.2rem 0;
  box-shadow:inset 0 0 40px -22px rgba(167,139,250,.7);
}
.ar-note b{color:#e9d9ff;font-weight:800;}

/* ── Inline code inside prose ───────────────────────── */
p code, td code, .tl-b code, .card p code, .ar-note code{
  font-family:'JetBrains Mono',monospace !important;font-size:.82em;
  background:rgba(34,211,238,.10);border:1px solid rgba(34,211,238,.22);
  border-radius:6px;padding:.04em .38em;color:#8ee9f7;
  direction:ltr;display:inline-block;white-space:nowrap;vertical-align:middle;
}

/* ── Icon fonts must not inherit our families ───────── */
[data-testid="stIconMaterial"], .material-icons, .material-symbols-rounded,
span[class*="material-"], [data-testid="stExpanderToggleIcon"]{
  font-family:'Material Symbols Rounded','Material Icons' !important;
}

/* ── Motion ─────────────────────────────────────────── */
@keyframes flow{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes glow{0%,100%{filter:drop-shadow(0 0 8px rgba(34,211,238,.30))}50%{filter:drop-shadow(0 0 22px rgba(167,139,250,.55))}}
@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
@keyframes floaty{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
@keyframes sweep{0%{transform:translateX(-120%)}100%{transform:translateX(220%)}}
@keyframes pulse{0%,100%{opacity:.55;transform:scale(.85)}50%{opacity:1;transform:scale(1.15)}}
@keyframes grow{from{width:0}}
@media (prefers-reduced-motion: reduce){*{animation:none !important;transition:none !important}}

/* ── Headings & hero ───────────────────────────────── */
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif !important;color:var(--txt) !important;letter-spacing:-.4px;}
.neon{
  background:linear-gradient(100deg,#22d3ee,#7dd3fc,#a78bfa,#22d3ee);
  background-size:320% 100%;
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
  animation:flow 8s ease-in-out infinite, glow 5s ease-in-out infinite;
}
.hero-wrap{position:relative;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;padding:.3rem 0 1rem;}
.hero-title{font-family:'Space Grotesk',sans-serif;font-weight:700;
  font-size:clamp(2.3rem,5.4vw,4.1rem);line-height:1.1;margin:0;letter-spacing:-1.4px;}
.hero-sub{font-size:1.02rem;color:var(--muted);margin-top:.85rem;max-width:680px;
  line-height:1.85;font-weight:300;}
.eyebrow{
  display:inline-flex;align-items:center;gap:.55rem;
  font-family:'JetBrains Mono',monospace;font-size:.7rem;letter-spacing:.2em;
  text-transform:uppercase;color:var(--cy);
  background:rgba(34,211,238,.09);border:1px solid rgba(34,211,238,.28);
  padding:.4rem .9rem;border-radius:999px;margin-bottom:1.05rem;
}
.dot{width:7px;height:7px;border-radius:50%;background:var(--gr);
  box-shadow:0 0 12px var(--gr);animation:pulse 1.9s ease-in-out infinite;}

.sec{display:flex;align-items:center;gap:.85rem;margin:2.5rem 0 1.15rem;}
.sec-t{font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:1.32rem;
  margin:0;white-space:nowrap;letter-spacing:-.4px;}
.sec-l{flex:1;height:1px;background:linear-gradient(90deg,rgba(167,139,250,.5),transparent);}
.kicker{color:var(--faint);font-family:'JetBrains Mono',monospace;font-size:.68rem;letter-spacing:.18em;}

/* ── Cards ──────────────────────────────────────────── */
.card{
  position:relative;overflow:hidden;
  background:linear-gradient(160deg,var(--glass-2),var(--glass));
  border:1px solid var(--stroke);border-radius:var(--r);
  padding:1.4rem 1.5rem;backdrop-filter:blur(16px);
  transition:transform .35s cubic-bezier(.2,.7,.2,1),border-color .35s,box-shadow .35s;
  animation:rise .7s cubic-bezier(.2,.7,.2,1) both;height:100%;
}
.card::after{content:"";position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.5),transparent);opacity:.5;}
.card:hover{transform:translateY(-5px);border-color:var(--stroke-2);
  box-shadow:0 22px 60px -24px rgba(167,139,250,.45);}
.card h4{margin:.1rem 0 .55rem;font-size:1.05rem;font-weight:600;line-height:1.35;}
.card p{color:var(--muted);font-size:.9rem;line-height:1.8;margin:0;font-weight:300;}
.ic{font-size:1.15rem;display:block;margin-bottom:.55rem;color:#7fdcea;
  font-family:'JetBrains Mono',monospace;letter-spacing:.06em;
  animation:floaty 5s ease-in-out infinite;}
/* equal-height cards: stretch every Streamlit wrapper that holds a .card */
[data-testid="stHorizontalBlock"]{align-items:stretch;}
[data-testid="stColumn"]:has(.card) > div,
[data-testid="stColumn"]:has(.card) [data-testid="stVerticalBlock"],
[data-testid="stElementContainer"]:has(.card),
[data-testid="stMarkdown"]:has(.card),
[data-testid="stMarkdown"]:has(.card) > div,
[data-testid="stMarkdownContainer"]:has(.card){height:100%;}
.card{display:flex;flex-direction:column;}
.card h4{text-wrap:balance;min-height:2.7em;}
.card p{flex:1 1 auto;}
.card p{text-wrap:pretty;}
.hero-sub, .lead, .tl-b, .kpi-s{text-wrap:pretty;}
.hero-title, .sec-t{text-wrap:balance;}
/* keep the sidebar footer clear of the viewport edge */
[data-testid="stSidebarUserContent"]{padding-bottom:2.6rem;}

/* ── KPI ────────────────────────────────────────────── */
.kpi{
  background:linear-gradient(155deg,rgba(255,255,255,.08),rgba(255,255,255,.028));
  border:1px solid var(--stroke);border-radius:15px;padding:1.05rem 1.2rem;
  animation:rise .7s both;position:relative;overflow:hidden;height:100%;
}
.kpi:hover{border-color:rgba(34,211,238,.4);box-shadow:0 0 32px -14px rgba(34,211,238,.5);}
.kpi-l{color:var(--faint);font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;
  font-family:'JetBrains Mono',monospace;margin-bottom:.45rem;}
.kpi-v{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.95rem;line-height:1;
  font-variant-numeric:tabular-nums;letter-spacing:-1px;}
.kpi-s{color:var(--muted);font-size:.76rem;margin-top:.45rem;font-weight:300;}

/* ── Bars ───────────────────────────────────────────── */
.bar-row{margin:.8rem 0;}
.bar-head{display:flex;justify-content:space-between;font-size:.86rem;margin-bottom:.4rem;
  color:var(--muted);}
.bar-head b{color:var(--txt);font-variant-numeric:tabular-nums;
  font-family:'JetBrains Mono',monospace;font-size:.82rem;}
.track{height:10px;border-radius:99px;background:rgba(255,255,255,.07);overflow:hidden;position:relative;}
.fill{height:100%;border-radius:99px;position:relative;animation:grow 1.1s cubic-bezier(.2,.8,.2,1) both;}
.fill::after{content:"";position:absolute;inset:0;width:45%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.5),transparent);
  animation:sweep 2.4s linear infinite;}
.fill-pos{background:linear-gradient(90deg,#34d399,#22d3ee);box-shadow:0 0 18px rgba(52,211,153,.5);}
.fill-neg{background:linear-gradient(90deg,#fb7185,#f472b6);box-shadow:0 0 18px rgba(251,113,133,.5);}
.fill-nu{background:linear-gradient(90deg,#a78bfa,#22d3ee);box-shadow:0 0 18px rgba(167,139,250,.45);}

/* ── Verdict ────────────────────────────────────────── */
.verdict{border-radius:var(--r);padding:1.45rem 1.6rem;margin:.6rem 0 1rem;
  border:1px solid var(--stroke-2);animation:rise .6s both;position:relative;overflow:hidden;}
.v-pos{background:linear-gradient(140deg,rgba(52,211,153,.16),rgba(34,211,238,.05));
  box-shadow:inset 0 0 60px -22px rgba(52,211,153,.5);}
.v-neg{background:linear-gradient(140deg,rgba(251,113,133,.16),rgba(244,114,182,.05));
  box-shadow:inset 0 0 60px -22px rgba(251,113,133,.5);}
.v-lbl{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.65rem;margin:0;
  letter-spacing:-.6px;}
.v-txt{direction:rtl;text-align:right;unicode-bidi:isolate;font-family:'Tajawal',sans-serif;
  font-weight:500;color:#cfd6ea;font-size:1.05rem;margin-top:.6rem;line-height:1.9;}
.conf{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:var(--faint);
  letter-spacing:.1em;margin-top:.75rem;}

/* ── Timeline ───────────────────────────────────────── */
.tl{position:relative;padding-left:2rem;margin:1.2rem 0;}
.tl::before{content:"";position:absolute;left:7px;top:6px;bottom:6px;width:2px;
  background:linear-gradient(180deg,var(--cy),var(--vi),var(--pk),transparent);}
.tl-i{position:relative;margin-bottom:1.6rem;animation:rise .7s both;}
.tl-i::before{content:"";position:absolute;left:-2rem;top:.45rem;width:15px;height:15px;
  border-radius:50%;background:var(--bg);border:2px solid var(--vi);
  box-shadow:0 0 14px rgba(167,139,250,.8);}
.tl-d{font-family:'JetBrains Mono',monospace;font-size:.66rem;color:var(--cy);
  letter-spacing:.16em;display:block;margin-bottom:.32rem;}
.tl-t{font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:1.02rem;margin:0 0 .32rem;}
.tl-b{color:var(--muted);font-size:.89rem;line-height:1.85;font-weight:300;}

/* ── Tags ───────────────────────────────────────────── */
.tags{display:flex;flex-wrap:wrap;gap:.45rem;margin:.85rem 0;}
.tag{font-family:'JetBrains Mono',monospace;font-size:.68rem;padding:.3rem .65rem;
  border-radius:8px;background:rgba(167,139,250,.11);border:1px solid rgba(167,139,250,.3);
  color:#c8b6ff;transition:.25s;}
.tag:hover{background:rgba(167,139,250,.24);transform:translateY(-2px);}
.tag-c{background:rgba(34,211,238,.11);border-color:rgba(34,211,238,.3);color:#8ee9f7;}
.tag-g{background:rgba(52,211,153,.11);border-color:rgba(52,211,153,.3);color:#8ff0c8;}

/* ── Code ───────────────────────────────────────────── */
.stCodeBlock, pre{font-family:'JetBrains Mono',monospace !important;text-align:left;}
.stCodeBlock{border:1px solid var(--stroke) !important;border-radius:13px !important;}
.ascii{font-family:'JetBrains Mono',monospace;font-size:.76rem;line-height:1.75;
  color:#9fb0d0;background:rgba(0,0,0,.42);border:1px solid var(--stroke);
  border-radius:14px;padding:1.1rem 1.25rem;overflow-x:auto;white-space:pre;text-align:left;}

/* ── SIDEBAR — solid dark rail ──────────────────────── */
[data-testid="stSidebar"]{
  background:var(--rail) !important;
  border-right:1px solid rgba(255,255,255,.07);
  width:266px !important;
}
[data-testid="stSidebar"] > div{background:var(--rail) !important;}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{padding-top:1.1rem;}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,[data-testid="stSidebar"] input,
[data-testid="stSidebar"] summary{font-family:'Inter',sans-serif;}
[data-testid="stSidebar"] [data-testid="stIconMaterial"]{
  font-family:'Material Symbols Rounded' !important;}

.rail-brand{display:flex;align-items:center;gap:.6rem;padding:.15rem .25rem 1.15rem;}
.rail-mark{
  width:36px;height:36px;border-radius:10px;flex:0 0 36px;display:block;
  box-shadow:0 6px 20px -8px rgba(20,184,166,.75);
}
.conn-cap{font-family:'JetBrains Mono',monospace;font-size:.6rem;letter-spacing:.2em;
  text-transform:uppercase;color:#737c94;margin:.1rem 0 .55rem .3rem;}
.conn-base{
  display:block;background:rgba(255,255,255,.035);border:1px solid var(--stroke);
  border-radius:11px;padding:.5rem .6rem;margin:0 0 .1rem;
  font-family:'JetBrains Mono',monospace;font-size:.66rem;line-height:1.5;
  color:#9fb3c8;word-break:break-all;
}
.conn-base b{display:block;color:#737c94;font-size:.56rem;letter-spacing:.16em;
  text-transform:uppercase;margin-bottom:.25rem;font-weight:400;}
.conn-base a,.conn-base a:visited{color:#9fb3c8 !important;text-decoration:none !important;
  border-bottom:0 !important;}
.conn-base a:hover{color:#22d3ee !important;}
.brand-hero{display:flex;align-items:center;gap:.85rem;margin:0 0 1.15rem;}
.brand-hero img{width:62px;height:62px;border-radius:16px;display:block;
  box-shadow:0 14px 38px -16px rgba(20,184,166,.85);}
.brand-hero .bh-n{font-family:'Space Grotesk',sans-serif;font-weight:700;
  font-size:1.5rem;letter-spacing:-.8px;color:#eef1fa;line-height:1.05;}
.brand-hero .bh-s{font-family:'JetBrains Mono',monospace;font-size:.62rem;
  letter-spacing:.18em;text-transform:uppercase;color:var(--faint);margin-top:.3rem;}
.base-chip{display:inline-flex;align-items:center;gap:.6rem;flex-wrap:wrap;
  background:rgba(255,255,255,.035);border:1px solid var(--stroke);
  border-radius:12px;padding:.5rem .85rem;margin:.2rem 0 1.4rem;
  font-family:'JetBrains Mono',monospace;font-size:.74rem;color:#c3cddc;}
.base-chip b{color:#737c94;font-weight:400;font-size:.62rem;letter-spacing:.16em;
  text-transform:uppercase;}
.base-chip i{font-style:normal;color:#5eead4;font-size:.62rem;letter-spacing:.12em;
  text-transform:uppercase;background:rgba(20,184,166,.12);
  border:1px solid rgba(20,184,166,.3);border-radius:6px;padding:.1rem .4rem;}
.src-chip{display:inline-flex;align-items:center;gap:.55rem;
  background:rgba(34,211,238,.08);border:1px solid rgba(34,211,238,.26);
  border-radius:10px;padding:.38rem .75rem;margin:.9rem 0 .2rem;
  font-family:'JetBrains Mono',monospace;font-size:.72rem;color:#bfe9f2;}
.src-chip b{color:#5b7f8c;font-weight:400;font-size:.6rem;letter-spacing:.16em;
  text-transform:uppercase;}
.info-note{direction:ltr;text-align:left;unicode-bidi:isolate;
  background:rgba(34,211,238,.06);border-left:2px solid rgba(34,211,238,.5);
  border-radius:0 11px 11px 0;padding:.65rem .9rem;margin:.9rem 0 .3rem;
  font-family:'Inter',sans-serif;font-size:.86rem;color:#bcc7da;line-height:1.65;}
/* file uploader */
[data-testid="stFileUploaderDropzone"],[data-testid="stFileUploader"] section{
  background:rgba(255,255,255,.03) !important;border:1px dashed rgba(255,255,255,.16) !important;
  border-radius:14px !important;}
[data-testid="stFileUploaderDropzone"]:hover{border-color:rgba(34,211,238,.45) !important;}
[data-testid="stFileUploader"] p,[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] small,[data-testid="stFileUploader"] div{
  color:var(--muted) !important;font-family:'Inter',sans-serif !important;}
[data-testid="stFileUploader"] [data-testid="stIconMaterial"],
[data-testid="stFileUploader"] span[class*="material-"],
[data-testid="stFileUploader"] .material-icons,
[data-testid="stFileUploader"] .material-symbols-rounded{
  font-family:'Material Symbols Rounded','Material Icons' !important;
  color:var(--muted) !important;}
[data-testid="stFileUploaderDropzoneInstructions"] span{color:var(--txt) !important;}
[data-testid="stFileUploader"] button{background:rgba(255,255,255,.07) !important;
  border:1px solid var(--stroke) !important;color:var(--txt) !important;
  border-radius:10px !important;width:auto !important;}
[data-testid="stFileUploader"] [data-testid="stFileUploaderFile"]{
  background:rgba(255,255,255,.03) !important;border-radius:10px !important;}
.rail-name{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.12rem;
  letter-spacing:-.4px;line-height:1.1;color:#eef1fa;}
.rail-sub{font-family:'JetBrains Mono',monospace;font-size:.6rem;letter-spacing:.16em;
  color:var(--faint);text-transform:uppercase;margin-top:.15rem;}
.rail-cap{font-family:'JetBrains Mono',monospace;font-size:.6rem;letter-spacing:.2em;
  text-transform:uppercase;color:#737c94;margin:.2rem 0 .5rem .3rem;}

/* nav items */
[data-testid="stSidebar"] [role="radiogroup"]{gap:.16rem !important;}
[data-testid="stSidebar"] [role="radiogroup"] > label{
  display:flex;align-items:center;width:100%;
  background:transparent;border:1px solid transparent;
  border-radius:10px;padding:.5rem .7rem !important;margin:0 !important;
  transition:background .18s ease, color .18s ease, border-color .18s ease;
  cursor:pointer;
}
[data-testid="stSidebar"] [role="radiogroup"] > label > div > div > div:first-child:not([data-testid]){display:none !important;}
[data-testid="stSidebar"] [role="radiogroup"] > label > div,
[data-testid="stSidebar"] [role="radiogroup"] > label > div > div{width:100%;gap:0 !important;}
[data-testid="stSidebar"] [role="radiogroup"] > label p{
  font-family:'Inter',sans-serif !important;font-size:.855rem !important;
  font-weight:450 !important;color:#8d95ab !important;margin:0 !important;
  letter-spacing:-.1px;transition:color .18s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] > label:hover{
  background:rgba(255,255,255,.045);border-color:rgba(255,255,255,.06);}
[data-testid="stSidebar"] [role="radiogroup"] > label:hover p{color:#d6dcec !important;}
[data-testid="stSidebar"] [role="radiogroup"] > label[data-selected="true"],
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked){
  background:linear-gradient(100deg,rgba(34,211,238,.20),rgba(167,139,250,.16));
  border-color:rgba(34,211,238,.34);
  box-shadow:inset 2px 0 0 0 #22d3ee, 0 6px 18px -12px rgba(34,211,238,.8);
}
[data-testid="stSidebar"] [role="radiogroup"] > label[data-selected="true"] p,
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) p{
  color:#ffffff !important;font-weight:600 !important;}

/* sidebar status chip */
.rail-chip{display:flex;align-items:center;gap:.5rem;font-size:.74rem;
  font-family:'JetBrains Mono',monospace;letter-spacing:.06em;padding:.15rem .3rem;}
.rail-foot{margin-top:1.1rem;color:#787f96;font-size:.66rem;line-height:1.9;
  font-family:'JetBrains Mono',monospace;letter-spacing:.04em;padding-left:.3rem;}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.07);margin:.9rem 0;}
[data-testid="stSidebar"] [data-testid="stExpander"]{
  background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07) !important;
  border-radius:11px !important;}
[data-testid="stSidebar"] [data-testid="stExpander"] summary p{
  font-size:.8rem !important;color:#9aa2b8 !important;}
[data-testid="stSidebar"] label{color:var(--muted) !important;font-size:.78rem !important;}

/* ── Inputs ─────────────────────────────────────────── */
[data-testid="stTextAreaRootElement"],[data-testid="stTextInputRootElement"],
[data-baseweb="textarea"],[data-baseweb="input"],[data-baseweb="base-input"],
[data-baseweb="select"] > div,[data-baseweb="popover"] ul{
  background:#0d1017 !important;
  border-color:var(--stroke) !important;border-radius:13px !important;
}
/* react-aria combobox (selectbox) */
.react-aria-ComboBox [role="group"]{
  background:#0d1017 !important;border:1px solid var(--stroke) !important;
  border-radius:13px !important;
}
.react-aria-ComboBox [role="group"]:focus-within{
  border-color:rgba(34,211,238,.65) !important;
  box-shadow:0 0 0 3px rgba(34,211,238,.14) !important;
}
.react-aria-ComboBox input,.react-aria-ComboBox input[role="combobox"]{
  background:transparent !important;color:var(--txt) !important;
  -webkit-text-fill-color:var(--txt) !important;border:0 !important;
  font-family:'Inter',sans-serif !important;
}
.react-aria-ComboBox button{background:transparent !important;color:var(--muted) !important;}
.react-aria-ComboBox button svg{fill:var(--muted) !important;}
.react-aria-Popover,[role="listbox"]{
  background:#0d1017 !important;border:1px solid var(--stroke) !important;
  border-radius:13px !important;box-shadow:0 18px 40px -18px rgba(0,0,0,.9) !important;
}
[role="option"]{background:transparent !important;color:var(--txt) !important;
  font-family:'Inter',sans-serif !important;}
[role="option"]:hover,[role="option"][data-focused],[role="option"][aria-selected="true"]{
  background:rgba(34,211,238,.16) !important;color:#fff !important;}
[data-testid="stTextAreaRootElement"]:focus-within,
[data-testid="stTextInputRootElement"]:focus-within,
[data-baseweb="textarea"]:focus-within,[data-baseweb="input"]:focus-within{
  border-color:rgba(34,211,238,.65) !important;
  box-shadow:0 0 0 3px rgba(34,211,238,.14) !important;
}
.stTextArea textarea,.stTextInput input,
[data-baseweb="base-input"] textarea,[data-baseweb="base-input"] input{
  background:transparent !important;border:0 !important;
  color:var(--txt) !important;-webkit-text-fill-color:var(--txt) !important;
  font-family:'Tajawal','Inter',sans-serif !important;font-size:1rem !important;
  direction:rtl;text-align:right;
}
.stTextArea textarea::placeholder,.stTextInput input::placeholder{
  color:var(--faint) !important;-webkit-text-fill-color:var(--faint) !important;}
[data-baseweb="select"] *{color:var(--txt) !important;font-family:'Inter',sans-serif !important;}
[data-baseweb="popover"] li{background:rgba(10,12,18,.98) !important;color:var(--txt) !important;}
[data-baseweb="popover"] li:hover{background:rgba(167,139,250,.2) !important;}
.stButton>button{
  width:100%;border:0;border-radius:12px;padding:.62rem 1.2rem;
  font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:.94rem;color:#04060a;
  letter-spacing:-.2px;
  background:linear-gradient(100deg,#22d3ee,#a78bfa);background-size:220% 100%;
  transition:.3s;box-shadow:0 10px 30px -14px rgba(167,139,250,.85);
}
.stButton>button:hover{background-position:100% 50%;transform:translateY(-2px);
  box-shadow:0 16px 40px -14px rgba(34,211,238,.85);}
[data-testid="stSidebar"] .stButton>button{font-size:.8rem;padding:.45rem 1rem;}
.stDownloadButton>button{border-radius:12px;background:var(--glass-2);
  border:1px solid var(--stroke);color:var(--txt);font-family:'Inter',sans-serif;}

/* ── Tabs / expander / tables ───────────────────────── */
.stTabs [data-baseweb="tab-list"]{gap:.4rem;background:transparent;border-bottom:1px solid var(--stroke);}
.stTabs [data-baseweb="tab"]{background:transparent;color:var(--muted);
  font-family:'Space Grotesk',sans-serif;font-weight:500;border-radius:10px 10px 0 0;}
.stTabs [aria-selected="true"]{color:var(--cy) !important;background:rgba(34,211,238,.09) !important;}
[data-testid="stMainBlockContainer"] [data-testid="stExpander"]{
  background:var(--glass);border:1px solid var(--stroke) !important;border-radius:14px !important;}
[data-testid="stExpander"] summary{font-family:'Space Grotesk',sans-serif;font-weight:500;}
.stAlert{border-radius:13px;border:1px solid var(--stroke);}
hr{border-color:var(--stroke);}

.tbl{width:100%;border-collapse:separate;border-spacing:0;margin:.9rem 0;
  font-size:.87rem;background:var(--glass);border:1px solid var(--stroke);
  border-radius:14px;overflow:hidden;}
.tbl th{background:rgba(167,139,250,.12);padding:.7rem .9rem;text-align:left;
  font-family:'Space Grotesk',sans-serif;font-weight:600;color:#d6c9ff;font-size:.8rem;
  letter-spacing:.02em;}
.tbl td{padding:.65rem .9rem;border-top:1px solid var(--stroke);color:var(--muted);
  font-weight:300;line-height:1.7;}
.tbl tr:hover td{background:rgba(255,255,255,.035);color:var(--txt);}
.tbl .num{font-family:'JetBrains Mono',monospace;font-variant-numeric:tabular-nums;font-size:.8rem;}
.tbl .arc{direction:rtl;text-align:right;unicode-bidi:isolate;font-family:'Tajawal',sans-serif;
  font-weight:500;font-size:.95rem;}
.ok{color:var(--gr);} .bad{color:var(--rd);} .warn{color:var(--am);}
.lead{color:var(--muted);font-weight:300;line-height:1.85;font-size:.95rem;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Render helpers
# ──────────────────────────────────────────────────────────────────────────────

def hero(title_html: str, sub: str, ar_line: str = "", eyebrow: str = "") -> None:
    eb = f'<div class="eyebrow"><span class="dot"></span>{eyebrow}</div>' if eyebrow else ""
    ar = f'<p class="ar-line">{ar_line}</p>' if ar_line else ""
    st.markdown(
        f'<div class="hero-wrap">{eb}<h1 class="hero-title">{title_html}</h1>'
        f'<p class="hero-sub">{sub}</p>{ar}</div>',
        unsafe_allow_html=True,
    )


def ar_note(text: str) -> None:
    st.markdown(f'<div class="ar-note">{text}</div>', unsafe_allow_html=True)


def lead(text: str) -> None:
    st.markdown(f'<p class="lead">{text}</p>', unsafe_allow_html=True)


def section(title: str, kicker: str = "") -> None:
    k = f'<span class="kicker">{kicker}</span>' if kicker else ""
    st.markdown(
        f'<div class="sec"><h3 class="sec-t">{title}</h3>{k}<div class="sec-l"></div></div>',
        unsafe_allow_html=True,
    )


def card(icon: str, title: str, body: str, delay: float = 0.0) -> str:
    return (
        f'<div class="card" style="animation-delay:{delay}s">'
        f'<span class="ic">{icon}</span><h4>{title}</h4><p>{body}</p></div>'
    )


def kpi(label: str, value: str, sub: str = "", delay: float = 0.0, color: str = "neon") -> str:
    cls = "kpi-v neon" if color == "neon" else "kpi-v"
    style = "" if color == "neon" else f"color:{color};"
    return (
        f'<div class="kpi" style="animation-delay:{delay}s"><div class="kpi-l">{label}</div>'
        f'<div class="{cls}" style="{style}">{value}</div><div class="kpi-s">{sub}</div></div>'
    )


def bar(label: str, pct: float, kind: str = "nu") -> str:
    return (
        f'<div class="bar-row"><div class="bar-head"><span>{label}</span>'
        f'<b>{pct:.1f}%</b></div><div class="track">'
        f'<div class="fill fill-{kind}" style="width:{max(pct, 1):.1f}%"></div></div></div>'
    )


def tags(items: list[str], kind: str = "") -> str:
    k = f" tag-{kind}" if kind else ""
    return '<div class="tags">' + "".join(f'<span class="tag{k}">{i}</span>' for i in items) + "</div>"


def timeline(items: list[tuple[str, str, str]]) -> str:
    out = '<div class="tl">'
    for i, (step, title, body) in enumerate(items):
        out += (
            f'<div class="tl-i" style="animation-delay:{i * .08:.2f}s">'
            f'<span class="tl-d">{step}</span>'
            f'<div class="tl-t">{title}</div>'
            f'<div class="tl-b">{body}</div></div>'
        )
    return out + "</div>"


def grid(html_items: list[str], cols: int = 3) -> None:
    for i in range(0, len(html_items), cols):
        chunk = html_items[i: i + cols]
        for col, html in zip(st.columns(len(chunk)), chunk):
            col.markdown(html, unsafe_allow_html=True)


def ascii_block(lines: list[str]) -> None:
    st.markdown('<div class="ascii">' + "\n".join(lines) + "</div>", unsafe_allow_html=True)


def esc(value) -> str:
    return _html.escape(str(value))


# ──────────────────────────────────────────────────────────────────────────────
# Training-data parsers
# ──────────────────────────────────────────────────────────────────────────────

FILE_ROW_CAP = 5000
BATCH_ROW_CAP = 300
MIN_PER_CLASS = 2
TEXT_KEYS = {"text", "texts", "tweet", "tweets", "review", "sentence", "content",
             "body", "comment", "message", "phrase", "\u0627\u0644\u0646\u0635"}
LABEL_KEYS = {"label", "labels", "sentiment", "class", "category", "target",
              "polarity", "y", "\u0627\u0644\u062a\u0635\u0646\u064a\u0641"}
WORD_LABEL_MAP = {"positive": "pos", "pos": "pos", "positif": "pos",
                  "\u0645\u0648\u062c\u0628": "pos", "\u0627\u064a\u062c\u0627\u0628\u064a": "pos",
                  "\u0625\u064a\u062c\u0627\u0628\u064a": "pos",
                  "negative": "neg", "neg": "neg", "negatif": "neg",
                  "\u0633\u0627\u0644\u0628": "neg", "\u0633\u0644\u0628\u064a": "neg"}
NUM_LABEL_MAP = {"1": "pos", "+1": "pos", "0": "neg", "-1": "neg"}


def unify_labels(labels: list[str]) -> list[str]:
    """Normalises label spellings for both input modes.

    Numeric labels are only rewritten when the whole column is a binary
    {0,1} / {-1,1} coding. A 1-5 star column is left untouched, because
    there `1` means the worst review rather than a positive one.
    """
    clean = [str(v).strip() for v in labels]
    numeric = {v.lower() for v in clean if v.lstrip("+-").isdigit()}
    binary_numeric = bool(numeric) and numeric <= set(NUM_LABEL_MAP) and len(numeric) <= 2
    out = []
    for v in clean:
        k = v.lower()
        if k in WORD_LABEL_MAP:
            out.append(WORD_LABEL_MAP[k])
        elif binary_numeric and k in NUM_LABEL_MAP:
            out.append(NUM_LABEL_MAP[k])
        else:
            out.append(v)
    return out


def parse_manual(raw: str):
    """Parses the `text ||| label` textarea format."""
    texts, labels, bad = [], [], []
    for i, line in enumerate(raw.split("\n"), 1):
        line = line.strip()
        if not line:
            continue
        if "|||" not in line:
            bad.append(i)
            continue
        t, _, lab = line.rpartition("|||")
        if t.strip() and lab.strip():
            texts.append(t.strip())
            labels.append(lab.strip())
        else:
            bad.append(i)
    return texts, unify_labels(labels), bad


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1256", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _pick_columns(rows: list[list[str]]):
    """Without a header: the label column is short and low-cardinality,
    the text column is the longest one."""
    width = max(len(r) for r in rows)
    sample = rows[:400]
    stats = []
    for c in range(width):
        vals = [r[c].strip() for r in sample if len(r) > c and r[c].strip()]
        if not vals:
            stats.append((c, 0.0, 10 ** 6))
            continue
        avg_len = sum(len(v) for v in vals) / len(vals)
        stats.append((c, avg_len, len(set(vals))))
    text_col = max(stats, key=lambda s: s[1])[0]
    rest = [s for s in stats if s[0] != text_col]
    label_col = min(rest, key=lambda s: (s[2], s[1]))[0] if rest else None
    return text_col, label_col


def parse_tabular(raw: bytes, filename: str):
    """Reads a .csv/.tsv upload and returns (texts, labels, bad_rows, info)."""
    body = _decode(raw)
    name = filename.lower()
    if name.endswith(".tsv"):
        delim = "\t"
    else:
        head = body[:8000]
        delim = max([",", ";", "\t", "|"], key=head.count)
        if head.count(delim) == 0:
            delim = ","

    rows = [r for r in csv.reader(io.StringIO(body), delimiter=delim)
            if any(c.strip() for c in r)]
    if not rows:
        return [], [], [], "That file has no readable rows."
    if max(len(r) for r in rows) < 2:
        return [], [], [], ("Only one column was detected. A csv/tsv with a text "
                            "column and a label column is required.")

    first = [c.strip().lower() for c in rows[0]]
    t_col = l_col = None
    if any(c in TEXT_KEYS for c in first) and any(c in LABEL_KEYS for c in first):
        for i, c in enumerate(first):
            if c in TEXT_KEYS and t_col is None:
                t_col = i
            if c in LABEL_KEYS and l_col is None:
                l_col = i
        rows = rows[1:]
        info = (f"Header detected · text column <code>{esc(first[t_col])}</code>, "
                f"label column <code>{esc(first[l_col])}</code>, delimiter "
                f"<code>{'TAB' if delim == chr(9) else esc(delim)}</code>.")
    else:
        t_col, l_col = _pick_columns(rows)
        info = (f"No header found · using column {t_col + 1} as the text and column "
                f"{(l_col or 0) + 1} as the label, delimiter "
                f"<code>{'TAB' if delim == chr(9) else esc(delim)}</code>.")

    if l_col is None or t_col is None:
        return [], [], [], "The text and label columns could not be identified."

    texts, labels, bad = [], [], []
    for i, r in enumerate(rows, 1):
        if len(r) <= max(t_col, l_col):
            bad.append(i)
            continue
        t = r[t_col].strip()
        lab = r[l_col].strip()
        if not t or not lab:
            bad.append(i)
            continue
        texts.append(t)
        labels.append(lab)
    return texts, unify_labels(labels), bad, info


# ──────────────────────────────────────────────────────────────────────────────
# API layer
# ──────────────────────────────────────────────────────────────────────────────

def api(method: str, path: str, payload: dict | None = None, timeout: int = 45):
    """Returns (ok, data, meta) where meta carries latency and status code."""
    base = st.session_state.get("api_base", API_BASE_DEFAULT).rstrip("/")
    key = st.session_state.get("api_key", API_KEY_DEFAULT)
    headers = {"X-API-Key": key, "Content-Type": "application/json"}
    t0 = time.perf_counter()
    try:
        r = requests.request(method, f"{base}{path}", headers=headers, json=payload, timeout=timeout)
        meta = {"ms": (time.perf_counter() - t0) * 1000, "code": r.status_code}
        if r.status_code >= 400:
            try:
                detail = r.json().get("detail", r.text)
            except Exception:
                detail = r.text[:300]
            return False, str(detail), meta
        return True, r.json(), meta
    except requests.exceptions.Timeout:
        return False, "Request timed out.", {"ms": timeout * 1000, "code": 0}
    except Exception as e:  # noqa: BLE001
        return False, f"Connection failed: {e}", {"ms": 0, "code": 0}


@st.cache_data(ttl=60, show_spinner=False)
def fetch_status(base: str, key: str):
    try:
        r = requests.get(f"{base.rstrip('/')}/status", headers={"X-API-Key": key}, timeout=25)
        if r.status_code >= 400:
            return False, r.text[:200]
        return True, r.json()
    except Exception as e:  # noqa: BLE001
        return False, str(e)


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — solid dark rail
# ──────────────────────────────────────────────────────────────────────────────

PAGES = [
    "◆  Overview",
    "⚡  Live Analysis",
    "▤  Batch Analysis",
    "◈  Train Model",
    "▦  Model Status",
    "◐  Development Journey",
    "⬡  Architecture",
    "◇  Data & Experiments",
    "△  Challenges & Lessons",
    "⟐  API Reference",
    "➜  Roadmap",
]

with st.sidebar:
    st.markdown(
        f'<div class="rail-brand"><img class="rail-mark" src="{LOGO_SVG_URI}" alt="VibeAR">'
        '<div><div class="rail-name">VibeAR</div>'
        '<div class="rail-sub">Arabic Sentiment</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="rail-cap">Navigate</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", PAGES, label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div class="conn-cap">Connection</div>', unsafe_allow_html=True)
    st.session_state["api_base"] = API_BASE
    st.session_state.setdefault("api_key", API_KEY_DEFAULT)
    st.markdown(
        f'<span class="conn-base"><b>Base URL · built in</b>{API_BASE}</span>',
        unsafe_allow_html=True,
    )
    st.session_state["api_key"] = st.text_input(
        "API key", st.session_state["api_key"], type="password"
    )
    if st.button("Re-check connection"):
        fetch_status.clear()
        st.rerun()

    live_ok, live_data = fetch_status(
        st.session_state.get("api_base", API_BASE_DEFAULT),
        st.session_state.get("api_key", API_KEY_DEFAULT),
    )
    if live_ok:
        st.markdown(
            '<div class="rail-chip" style="color:#8ff0c8;">'
            '<span class="dot"></span>API ONLINE</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="rail-chip" style="color:#ffb3bd;">'
            '<span class="dot" style="background:#fb7185;box-shadow:0 0 12px #fb7185"></span>'
            'API UNREACHABLE</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="rail-foot">FastAPI · scikit-learn<br>Streamlit · FastAPI Cloud</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# 1) Overview
# ──────────────────────────────────────────────────────────────────────────────

if page == PAGES[0]:
    st.markdown(
        f'<div class="brand-hero"><img src="{LOGO_SVG_URI}" alt="VibeAR logo">'
        '<div><div class="bh-n">VibeAR</div>'
        '<div class="bh-s">Classical NLP · Arabic Sentiment</div></div></div>',
        unsafe_allow_html=True,
    )
    hero(
        'Sentiment analysis<br>for <span class="neon">Arabic text</span>',
        "VibeAR is a production Arabic sentiment API built with FastAPI and scikit-learn. "
        "It classifies a sentence as positive or negative in single-digit milliseconds, and "
        "lets you retrain the live model on your own data with one call — no downtime.",
        ar_line="نفهم مشاعر العربية قبل ما تتقال بصوت عالي.",
        eyebrow="Live · Arabic Sentiment API",
    )

    st.markdown(tags(["FastAPI", "scikit-learn", "TF-IDF", "LogisticRegression",
                      "Pydantic", "Docker", "Streamlit"], "c"), unsafe_allow_html=True)

    st.markdown(
        f'<div class="base-chip"><b>Base URL</b>{API_BASE}<i>built in</i></div>',
        unsafe_allow_html=True,
    )

    acc = "78.9%"
    if live_ok:
        acc = f"{live_data.get('evaluation', {}).get('accuracy', 0) * 100:.1f}%"

    section("At a glance", "NUMBERS")
    grid([
        kpi("Default accuracy", acc, "held-out test split", 0.0),
        kpi("Training corpus", "58,751", "labelled Arabic tweets", 0.08),
        kpi("Endpoints", "6", "all key-protected", 0.16),
        kpi("Inference", "&lt;10ms", "single prediction, server-side", 0.24),
    ], cols=4)

    section("Core design ideas", "WHY IT WORKS")
    grid([
        card("◈", "Ships with a trained model",
             "The service boots with a model trained on ~58k tweets, so it answers requests from "
             "the very first second. The default artifact lives in its own file that no code path "
             "ever writes over.", 0.0),
        card("◈", "Bring your own data",
             "One call to <code>/train</code> with your texts and labels. Training runs on a "
             "separate thread, so the API keeps serving predictions while it learns.", 0.08),
        card("↩", "Instant rollback",
             "If a fresh model underperforms, <code>/use-default-model</code> restores the "
             "original in one call — no retraining, no redeploy.", 0.16),
        card("⊘", "Auth on every route",
             "Each endpoint requires the <code>X-API-Key</code> header through FastAPI's "
             "dependency injection. There is no unprotected path.", 0.24),
        card("▦", "Full transparency",
             "<code>/status</code> returns the complete evaluation report — precision, recall and "
             "F1 per class — so you always know what the live model is worth.", 0.32),
        card("▤", "Single and batch",
             "<code>/predict</code> for one sentence, <code>/predict-batch</code> for a whole "
             "list in one round trip, with the same structured response shape.", 0.40),
    ])

    section("Try it now", "QUICK DEMO")
    lead("Type any Arabic sentence and hit analyze — the request hits the hosted API and returns "
         "real class probabilities.")
    c1, c2 = st.columns([3, 1])
    quick = c1.text_input("Sample sentence", "الخدمة كانت ممتازة والتوصيل سريع جدا",
                          label_visibility="collapsed")
    go = c2.button("Analyze", key="quick_go")

    if go and quick.strip():
        with st.spinner("Analyzing..."):
            ok, data, meta = api("POST", "/predict", {"text": quick.strip()})
        if ok:
            preds = data.get("predictions", {})
            pos = float(preds.get("pos", 0)) * 100
            neg = float(preds.get("neg", 0)) * 100
            positive = pos >= neg
            st.markdown(
                f'<div class="verdict {"v-pos" if positive else "v-neg"}">'
                f'<p class="v-lbl">{"Positive" if positive else "Negative"} sentiment</p>'
                f'<p class="v-txt">{esc(quick.strip())}</p>'
                f'<div class="conf">CONFIDENCE {max(pos, neg):.1f}% · {meta["ms"]:.0f}ms</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(bar("Positive · pos", pos, "pos") + bar("Negative · neg", neg, "neg"),
                        unsafe_allow_html=True)
        else:
            st.error(f"Request failed: {data}")


# ──────────────────────────────────────────────────────────────────────────────
# 2) Live Analysis
# ──────────────────────────────────────────────────────────────────────────────

elif page == PAGES[1]:
    hero(
        '<span class="neon">Live Analysis</span>',
        "Send a single sentence to /predict and inspect the full probability distribution "
        "across both classes, plus round-trip latency.",
        ar_line="اكتب جملتك بالعربي — فصحى أو عامية — وشوف الموديل شافها إزاي.",
    )

    samples = {
        "Blank — write your own": "",
        "Service praise": "التعامل كان راقي جدا والخدمة فوق الممتازة وربنا يكرمكم",
        "Complaint": "تجربة سيئة جدا، انتظرت ساعتين ومحدش رد عليا خالص",
        "Mixed signals": "المنتج حلو بس السعر غالي والتوصيل اتأخر",
        "Blessing / dua": "ربنا يسعدك ويفتحها في وشك يا رب",
    }
    pick = st.selectbox("Load a sample", list(samples.keys()))
    text = st.text_area("Input text", samples[pick], height=140,
                        placeholder="اكتب هنا بالعربي...")

    if st.button("Analyze sentiment", key="single"):
        if not text.strip():
            st.warning("Enter some text first.")
        else:
            with st.spinner("Analyzing..."):
                ok, data, meta = api("POST", "/predict", {"text": text.strip()})
            if ok:
                preds = data.get("predictions", {})
                pos = float(preds.get("pos", 0)) * 100
                neg = float(preds.get("neg", 0)) * 100
                positive = pos >= neg
                conf = max(pos, neg)
                st.markdown(
                    f'<div class="verdict {"v-pos" if positive else "v-neg"}">'
                    f'<p class="v-lbl">{"Positive" if positive else "Negative"} sentiment</p>'
                    f'<p class="v-txt">{esc(data.get("text", ""))}</p>'
                    f'<div class="conf">CONFIDENCE {conf:.1f}% · LATENCY {meta["ms"]:.0f}ms</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(bar("Positive · pos", pos, "pos") + bar("Negative · neg", neg, "neg"),
                            unsafe_allow_html=True)

                grid([
                    kpi("Verdict", "Positive" if positive else "Negative", "winning class", 0,
                        "#8ff0c8" if positive else "#ffb3bd"),
                    kpi("Confidence", f"{conf:.1f}%", "probability of winning class", 0.08),
                    kpi("Round trip", f"{meta['ms']:.0f}ms", "client to API and back", 0.16),
                ], cols=3)

                if conf < 60:
                    st.info("Low confidence (under 60%). The sentence likely sits on the boundary "
                            "between classes, carries mixed sentiment, or falls outside the "
                            "training distribution.")

                with st.expander("Raw API response"):
                    st.code(json.dumps(data, ensure_ascii=False, indent=2), language="json")
            else:
                st.error(f"Request failed: {data}")


# ──────────────────────────────────────────────────────────────────────────────
# 3) Batch Analysis
# ──────────────────────────────────────────────────────────────────────────────

elif page == PAGES[2]:
    hero(
        '<span class="neon">Batch Analysis</span>',
        "Score a whole list of sentences in a single request. Useful for customer feedback, "
        "support tickets or review dumps where you want the overall mood fast.",
        ar_line="حلّل قائمة كاملة في طلب واحد وشوف المزاج العام بسرعة.",
    )

    default_batch = "\n".join([
        "الخدمة ممتازة والتعامل محترم جدا",
        "التطبيق بطيء وبيقفل لوحده كل شوية",
        "الطعم جميل بس الأسعار مبالغ فيها",
        "أفضل تجربة شراء عملتها من سنة",
        "مش هتعامل معاهم تاني نهائي",
    ])
    section("How it works", "MECHANICS")
    grid([
        card("01", "One request, many rows",
             "Every line becomes an item in a single <code>/predict-batch</code> call, so "
             "network round-trips stay at one no matter how long the list is.", 0.0),
        card("02", f"Up to {BATCH_ROW_CAP} lines",
             "Longer lists are trimmed before sending. Splitting a large dump into several "
             "runs keeps each response inside the request timeout.", 0.08),
        card("03", "Exportable output",
             "The raw JSON of every run is downloadable, so results can move straight into a "
             "spreadsheet or another pipeline.", 0.16),
    ], cols=3)

    section("Your sentences", "INPUT")
    raw = st.text_area("One sentence per line", default_batch, height=190)

    if st.button("Analyze batch", key="batch"):
        texts = [t.strip() for t in raw.split("\n") if t.strip()]
        if len(texts) > BATCH_ROW_CAP:
            st.warning(
                f"{len(texts):,} lines pasted — only the first {BATCH_ROW_CAP} are sent so "
                f"the request stays inside the timeout. Use several smaller runs for more."
            )
            texts = texts[:BATCH_ROW_CAP]
        if not texts:
            st.warning("Add at least one sentence.")
        else:
            with st.spinner(f"Analyzing {len(texts)} sentences..."):
                ok, data, meta = api("POST", "/predict-batch", {"texts": texts})
            if ok and not data.get("predictions"):
                st.warning("The API answered without any predictions. Check Model Status.")
            elif ok:
                rows = data.get("predictions", [])
                pos_n = sum(1 for r in rows
                            if float(r["predictions"].get("pos", 0))
                            >= float(r["predictions"].get("neg", 0)))
                neg_n = len(rows) - pos_n
                avg_conf = (sum(max(float(r["predictions"].get("pos", 0)),
                                    float(r["predictions"].get("neg", 0))) for r in rows)
                            / max(len(rows), 1) * 100)

                section("Summary", "AGGREGATE")
                grid([
                    kpi("Sentences", str(len(rows)), "in one request", 0.0),
                    kpi("Positive", str(pos_n), f"{pos_n / len(rows) * 100:.0f}% of total",
                        0.08, "#8ff0c8"),
                    kpi("Negative", str(neg_n), f"{neg_n / len(rows) * 100:.0f}% of total",
                        0.16, "#ffb3bd"),
                    kpi("Mean confidence", f"{avg_conf:.0f}%", f"request took {meta['ms']:.0f}ms",
                        0.24),
                ], cols=4)

                st.markdown(
                    bar("Positive share", pos_n / len(rows) * 100, "pos")
                    + bar("Negative share", neg_n / len(rows) * 100, "neg"),
                    unsafe_allow_html=True,
                )

                section("Per-sentence breakdown", "DETAIL")
                html = ('<table class="tbl"><tr><th>#</th><th>Text</th><th>Verdict</th>'
                        '<th>pos</th><th>neg</th></tr>')
                for i, r in enumerate(rows, 1):
                    p = float(r["predictions"].get("pos", 0)) * 100
                    n = float(r["predictions"].get("neg", 0)) * 100
                    good = p >= n
                    html += (
                        f'<tr><td class="num">{i}</td>'
                        f'<td class="arc">{esc(r.get("text", ""))}</td>'
                        f'<td class="{"ok" if good else "bad"}">'
                        f'{"Positive" if good else "Negative"}</td>'
                        f'<td class="num ok">{p:.1f}%</td>'
                        f'<td class="num bad">{n:.1f}%</td></tr>'
                    )
                st.markdown(html + "</table>", unsafe_allow_html=True)

                st.download_button(
                    "Download results (JSON)",
                    json.dumps(data, ensure_ascii=False, indent=2),
                    file_name=f"vibear_batch_{datetime.now():%Y%m%d_%H%M}.json",
                    mime="application/json",
                )
            else:
                st.error(f"Request failed: {data}")


# ──────────────────────────────────────────────────────────────────────────────
# 4) Train Model
# ──────────────────────────────────────────────────────────────────────────────

elif page == PAGES[3]:
    hero(
        'Train <span class="neon">your own</span> model',
        "The shipped model is general — it learned from tweets. If your domain differs "
        "(product comments, support tickets, restaurant reviews) retrain the live model on "
        "your own labelled data in a single call.",
        ar_line="التدريب هيستبدل الموديل النشط، بس الأصل محفوظ وترجع له في لحظة.",
    )

    section("How the swap works", "MECHANICS")
    ascii_block([
        "            +-----------------------------+",
        "            |       default_model_*       |   <-- original, never overwritten",
        "            +--------------+--------------+",
        "                           |   loaded as the active model on first boot",
        "                           v",
        "POST /train --------->  +-----------------------+   --->   /predict",
        "                        |    model_pickle.*     |   --->   /predict-batch",
        "                        +----------^------------+",
        "                                   |",
        "POST /use-default-model -----------+   instant restore, no retraining",
    ])
    lead("The default artifact at the top is the source of truth — no code path writes over it. "
         "Training only touches the active model files, and the restore endpoint copies the "
         "original back in place without retraining anything.")

    section("Your labelled data", "INPUT")
    lead("Pick one of the two input modes. Type the examples by hand, or upload a "
         "<code>.csv</code> / <code>.tsv</code> file and let the console detect the "
         "text and label columns for you.")

    demo = "\n".join([
        "الخدمة كانت ممتازة ||| pos",
        "التعامل راقي والتوصيل سريع ||| pos",
        "المنتج وصل بحالة مثالية ||| pos",
        "تجربة سيئة ومحدش رد عليا ||| neg",
        "المنتج مكسور والدعم مستهتر ||| neg",
        "أسوأ خدمة تعاملت معاها ||| neg",
    ])

    tab_manual, tab_file = st.tabs(["Manual text input", "Upload a file"])
    texts, labels, bad = [], [], []
    source_note = ""

    with tab_manual:
        st.markdown(
            '<p class="lead">One example per line, formatted as '
            '<code>text ||| label</code> — for example '
            '<code>الخدمة ممتازة ||| pos</code>.</p>',
            unsafe_allow_html=True,
        )
        train_raw = st.text_area("Training data", demo, height=210)
        m_texts, m_labels, m_bad = parse_manual(train_raw)
        st.caption(f"{len(m_texts)} valid examples parsed from the text box.")

    with tab_file:
        st.markdown(
            '<p class="lead">Upload a <code>.csv</code> or <code>.tsv</code> file. '
            'A header row such as <code>text,label</code> is detected automatically; '
            'without a header the two columns are identified by their content, so the '
            'project\'s own headerless TSV files work as they are.</p>',
            unsafe_allow_html=True,
        )
        up = st.file_uploader("Data file", type=["csv", "tsv"], key="train_file")
        f_texts, f_labels, f_bad, f_info = [], [], [], ""
        if up is not None:
            f_texts, f_labels, f_bad, f_info = parse_tabular(up.getvalue(), up.name)
            if f_info:
                st.markdown(f'<div class="info-note">{f_info}</div>', unsafe_allow_html=True)
            if f_texts:
                if len(f_texts) > FILE_ROW_CAP:
                    st.warning(
                        f"File holds {len(f_texts):,} rows — only the first "
                        f"{FILE_ROW_CAP:,} are sent to keep the request small."
                    )
                    f_texts, f_labels = f_texts[:FILE_ROW_CAP], f_labels[:FILE_ROW_CAP]
                prev = '<table class="tbl"><tr><th>#</th><th>Text</th><th>Label</th></tr>'
                for i, (t, lab) in enumerate(zip(f_texts[:8], f_labels[:8]), 1):
                    cls = "arc" if any("\u0600" <= c <= "\u06ff" for c in t) else ""
                    shown = t if len(t) <= 90 else t[:90] + "…"
                    prev += (f'<tr><td>{i}</td><td class="{cls}">{esc(shown)}</td>'
                             f'<td><code>{esc(lab)}</code></td></tr>')
                st.markdown(prev + "</table>", unsafe_allow_html=True)
                st.caption(f"{len(f_texts):,} rows ready · preview shows the first 8.")
            elif not f_info:
                st.error("No usable text/label pairs were found in that file.")

    if f_texts:
        texts, labels, bad = f_texts, f_labels, f_bad
        source_note = f"Uploaded file · {up.name}"
    else:
        texts, labels, bad = m_texts, m_labels, m_bad
        source_note = "Manual text input"

    st.markdown(
        f'<div class="src-chip"><b>Active source</b>{esc(source_note)}</div>',
        unsafe_allow_html=True,
    )

    grid([
        kpi("Valid examples", str(len(texts)), "after parsing", 0.0),
        kpi("Classes", str(len(set(labels))), " / ".join(sorted(set(labels))) or "—", 0.08),
        kpi("Malformed lines", str(len(bad)),
            ("lines: " + ", ".join(map(str, bad))) if bad else "all lines parsed",
            0.16, "#ffdf94" if bad else "#8ff0c8"),
    ], cols=3)

    st.markdown("<br>", unsafe_allow_html=True)
    a, b = st.columns(2)

    with a:
        if st.button("Start training", key="train"):
            counts = Counter(labels)
            thin = [f"{k} ({v})" for k, v in sorted(counts.items()) if v < MIN_PER_CLASS]
            if len(texts) < 8 or len(counts) < 2:
                st.warning("Need at least 8 examples and 2 distinct classes for a useful run.")
            elif thin:
                st.warning(
                    "Every class needs at least "
                    f"{MIN_PER_CLASS} examples before the data can be split for evaluation. "
                    "Too few: " + ", ".join(thin) + "."
                )
            else:
                with st.spinner("Sending data and starting background training..."):
                    ok, data, meta = api("POST", "/train", {"texts": texts, "labels": labels})
                if ok:
                    st.success(f"Training started — current status: {data.get('status')}")
                    ph = st.empty()
                    polls = 24
                    for i in range(polls):
                        time.sleep(2.0 if i < 8 else 4.0)
                        fetch_status.clear()
                        sok, sdata = fetch_status(st.session_state["api_base"],
                                                  st.session_state["api_key"])
                        if sok and sdata.get("status") == "Model Ready":
                            ph.success("New model is live and serving requests.")
                            ev = sdata.get("evaluation", {})
                            if isinstance(ev.get("accuracy"), (int, float)):
                                st.markdown(
                                    kpi("Your model accuracy", f"{ev['accuracy'] * 100:.1f}%",
                                        "internal test split"),
                                    unsafe_allow_html=True,
                                )
                            break
                        ph.info(
                            f"Training in progress... (check {i + 1}/{polls}) — "
                            "the API is still responding"
                        )
                    else:
                        ph.warning(
                            "Still training after a few minutes. The run keeps going on the "
                            "server — press the button below or open Model Status to see the "
                            "result."
                        )
                        st.session_state["watch_training"] = True
                else:
                    st.error(f"Training failed: {data}")

        if st.session_state.get("watch_training"):
            if st.button("Check training result", key="recheck_train"):
                fetch_status.clear()
                sok, sdata = fetch_status(st.session_state["api_base"],
                                          st.session_state["api_key"])
                if sok and sdata.get("status") == "Model Ready":
                    st.session_state["watch_training"] = False
                    st.success("Training finished — the new model is live.")
                else:
                    st.info(f"Current status: {sdata.get('status') if sok else sdata}")

    with b:
        if st.button("Restore default model", key="reset"):
            with st.spinner("Restoring..."):
                ok, data, meta = api("POST", "/use-default-model")
            if ok:
                fetch_status.clear()
                st.success("Default model restored as the active model.")
                st.code(json.dumps(data, ensure_ascii=False, indent=2)[:900], language="json")
            else:
                st.error(f"Failed: {data}")


# ──────────────────────────────────────────────────────────────────────────────
# 5) Model Status
# ──────────────────────────────────────────────────────────────────────────────

elif page == PAGES[4]:
    hero(
        '<span class="neon">Model Status</span>',
        "A live report straight from the /status endpoint — current state, class labels and the "
        "full evaluation report of whichever model is serving right now.",
        ar_line="الأرقام دي جاية مباشرة من السيرفر، مش محفوظة في الواجهة.",
    )

    if st.button("Refresh", key="refresh_status"):
        fetch_status.clear()
        st.rerun()

    if not live_ok:
        st.error(f"Could not fetch status: {live_data}")
    else:
        ev = live_data.get("evaluation", {})
        acc = ev.get("accuracy", 0)
        ts = live_data.get("timestamp", "")
        grid([
            kpi("State", live_data.get("status", "—"), "active model", 0.0, "#8ff0c8"),
            kpi("Accuracy", f"{acc * 100:.2f}%", "overall", 0.08),
            kpi("Classes", " · ".join(live_data.get("classes", [])), "binary classification", 0.16),
            kpi("Last update", ts[:10] or "—", ts[11:19], 0.24),
        ], cols=4)

        section("Per-class metrics", "EVALUATION")
        names = {"neg": "neg — negative", "pos": "pos — positive"}
        html = ('<table class="tbl"><tr><th>Class</th><th>Precision</th><th>Recall</th>'
                '<th>F1-score</th><th>Support</th></tr>')
        for cls, label in names.items():
            m = ev.get(cls, {})
            if not isinstance(m, dict):
                continue
            html += (
                f'<tr><td class="num">{label}</td>'
                f'<td class="num">{m.get("precision", 0):.3f}</td>'
                f'<td class="num">{m.get("recall", 0):.3f}</td>'
                f'<td class="num">{m.get("f1-score", 0):.3f}</td>'
                f'<td class="num">{int(m.get("support", 0)):,}</td></tr>'
            )
        for key, label in [("macro avg", "macro average"), ("weighted avg", "weighted average")]:
            m = ev.get(key, {})
            if isinstance(m, dict) and m:
                html += (
                    f'<tr><td class="num"><b>{label}</b></td>'
                    f'<td class="num">{m.get("precision", 0):.3f}</td>'
                    f'<td class="num">{m.get("recall", 0):.3f}</td>'
                    f'<td class="num">{m.get("f1-score", 0):.3f}</td>'
                    f'<td class="num">{int(m.get("support", 0)):,}</td></tr>'
                )
        st.markdown(html + "</table>", unsafe_allow_html=True)

        section("Visual read", "CHARTS")
        bars = ""
        for cls, label in names.items():
            m = ev.get(cls, {})
            if isinstance(m, dict) and m:
                bars += bar(f"F1 — {label}", float(m.get("f1-score", 0)) * 100,
                            "pos" if cls == "pos" else "neg")
        bars += bar("Overall accuracy", float(acc) * 100, "nu")
        st.markdown(bars, unsafe_allow_html=True)

        ar_note("الرقمين متقاربين جدًا بين الكلاسين، وده منطقي لأن الداتا متوازنة تقريبًا "
                "(حوالي ٢٩ ألف إيجابي مقابل ٢٩ ألف سلبي) — فمفيش انحياز لكلاس على حساب التاني.")

        with st.expander("Full raw response"):
            st.code(json.dumps(live_data, ensure_ascii=False, indent=2), language="json")


# ──────────────────────────────────────────────────────────────────────────────
# 6) Development Journey
# ──────────────────────────────────────────────────────────────────────────────

elif page == PAGES[5]:
    hero(
        '<span class="neon">Development Journey</span>',
        "Every technical decision behind VibeAR, in order — from an exploratory notebook to a "
        "container running behind Cloudflare, and why each trade-off was accepted.",
        ar_line="من نوتبوك تجارب على الجهاز، لخدمة حقيقية شغّالة على السحابة.",
    )

    t1, t2, t3 = st.tabs(["Experimentation", "Engineering", "Shipping"])

    with t1:
        section("Modelling timeline", "PHASE 1")
        st.markdown(timeline([
            ("STEP 01", "Problem and dataset selection",
             "Started from a measurable, well-scoped problem: binary sentiment classification for "
             "Arabic text. Chose the Arabic Sentiment Twitter Corpus — four pre-split TSV files "
             "(train/test × positive/negative) totalling 58,751 tweets."),
            ("STEP 02", "Loading and exploration",
             "Read the files with pandas using a tab separator and no header, then merged positive "
             "and negative into a single DataFrame with two columns: label and tweet. Wrote a small "
             "row-highlighting helper so samples could be scanned visually — green for positive, "
             "red for negative. A value_counts check confirmed the corpus was near-balanced, which "
             "removed the need for any class-imbalance handling."),
            ("STEP 03", "Baseline first",
             "Deliberately began with the simplest thing that works: CountVectorizer with "
             "max_features=15000 feeding LogisticRegression(max_iter=10000) inside one Pipeline. "
             "The rule from then on: any added complexity has to beat this number or it does not "
             "ship."),
            ("STEP 04", "Character n-gram experiment",
             "Arabic is morphologically rich, so the next attempt used "
             "TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5)) with LinearSVC. Character "
             "n-grams capture roots and affix patterns without a stemmer, and char_wb specifically "
             "prevents n-grams from crossing word boundaries."),
            ("STEP 05", "Final configuration",
             "The shipped configuration is TfidfVectorizer(min_df=2, max_df=0.9, ngram_range=(1,2)) "
             "with LogisticRegression. The deciding factor was not raw accuracy: LogisticRegression "
             "exposes predict_proba directly, while LinearSVC returns a signed distance from the "
             "hyperplane that needs extra calibration. Since the API must return probabilities, the "
             "trade-off favoured LogisticRegression."),
            ("STEP 06", "Persisting the artifact",
             "The full Pipeline — vectorizer plus classifier — is dumped with joblib at compress=9. "
             "Saving the Pipeline instead of two separate objects guarantees identical transform "
             "steps at inference time, which closes the most common source of bugs when deploying "
             "NLP models."),
        ]), unsafe_allow_html=True)

        section("Experiment comparison", "TRADE-OFFS")
        st.markdown(
            '<table class="tbl"><tr><th>Run</th><th>Vectorizer</th><th>Classifier</th>'
            '<th>Strength</th><th>Verdict</th></tr>'
            '<tr><td>Baseline</td><td class="num">CountVectorizer 15k</td>'
            '<td class="num">LogisticRegression</td><td>simple and very fast</td>'
            '<td class="warn">became the reference line</td></tr>'
            '<tr><td>Character</td><td class="num">TF-IDF char_wb (3,5)</td>'
            '<td class="num">LinearSVC</td><td>handles Arabic morphology</td>'
            '<td class="bad">no direct predict_proba</td></tr>'
            '<tr><td><b>Shipped</b></td><td class="num">TF-IDF word (1,2)</td>'
            '<td class="num">LogisticRegression</td><td>probabilities + solid accuracy</td>'
            '<td class="ok">best fit for an API</td></tr>'
            "</table>",
            unsafe_allow_html=True,
        )

    with t2:
        section("From notebook to service", "PHASE 2")
        st.markdown(timeline([
            ("STEP 07", "Layer separation",
             "The first architectural rule: main.py contains zero ML logic. It owns routes, "
             "authentication and CORS only, while everything about training and prediction lives "
             "inside the NLPTrainer class. The model can be replaced without touching the API "
             "layer, and vice versa."),
            ("STEP 08", "Explicit contracts with Pydantic",
             "Request schemas (TrainingData, TestingData, QueryText) and response schemas "
             "(PredictionObject, PredictionObjects, StatusObject) were defined up front. That buys "
             "two things at once: automatic input validation, and a complete Swagger document "
             "without writing any documentation by hand."),
            ("STEP 09", "Training on a background thread",
             "Training over tens of thousands of texts takes real time. Executed inside the request "
             "it would block the event loop and freeze the whole service. So train() returns "
             "immediately with status 'Training' and hands the work to _train_job on a Thread, "
             "while the client polls /status. This was the point where the project stopped being a "
             "script and became a service."),
            ("STEP 10", "The dual-model design",
             "The most important addition. The default model lives in its own pair of files "
             "(default_model_pickle.joblib and default_model_status.json) that no code path "
             "overwrites, and the active model lives in a second pair. On boot: use the active "
             "model if present, otherwise fall back to the default — so the service works from the "
             "first second with no training required."),
            ("STEP 11", "The deepcopy bug",
             "Active state and default state were pointing at the same dictionary in memory, so "
             "mutating one silently corrupted the other — the default model would 'remember' the "
             "evaluation report of a later training run. The fix was copy.deepcopy on every state "
             "copy. A practical reminder that shared mutable state is more dangerous than any "
             "algorithmic mistake."),
            ("STEP 12", "Authentication layer",
             "Key-based auth via APIKeyHeader with Depends(verify_api_key) on every endpoint "
             "without exception, and the key itself loaded from environment variables through "
             "python-dotenv rather than hard-coded."),
            ("STEP 13", "State persistence on disk",
             "Every state transition is written to model_status.json immediately, so a restart "
             "resumes from the last known model instead of resetting to zero."),
        ]), unsafe_allow_html=True)

        ar_note("أخطر مشكلة في المشروع كلّه كانت في الذاكرة مش في الخوارزمية — "
                "قاموسين بيأشّروا على نفس الكائن، فالتعديل على واحد كان بيلوّث التاني بالغلط.")

    with t3:
        section("Deployment and interface", "PHASE 3")
        st.markdown(timeline([
            ("STEP 14", "Pinned dependencies",
             "requirements.txt pins exact versions — most critically scikit-learn==1.6.1, because "
             "joblib artifacts are tied to the library version that produced them. A version drift "
             "between training and loading can break unpickling entirely."),
            ("STEP 15", "Containerisation",
             "A Dockerfile on python:3.12-slim copies requirements and installs first, then copies "
             "the source. That ordering is deliberate: the dependency layer stays cached and is not "
             "rebuilt on every code change."),
            ("STEP 16", "Deployed on FastAPI Cloud",
             "The service runs on fastapicloud.dev behind Cloudflare over HTTP/2. All endpoints are "
             "reachable, Swagger is served at /docs, and any request without a valid key is "
             "rejected before it ever reaches the model."),
            ("STEP 17", "This Streamlit console",
             "A correct API is still invisible. This single-file interface consumes the same live "
             "endpoints — live prediction, batch scoring, training and status — so the project can "
             "be demonstrated and explored without touching curl."),
        ]), unsafe_allow_html=True)

        section("Deployment facts", "NOW")
        grid([
            kpi("Hosting", "FastAPI Cloud", "behind Cloudflare · HTTP/2", 0.0),
            kpi("Auth", "X-API-Key", "every route, no exceptions", 0.08),
            kpi("Docs", "/docs", "auto-generated Swagger", 0.16),
        ], cols=3)


# ──────────────────────────────────────────────────────────────────────────────
# 7) Architecture
# ──────────────────────────────────────────────────────────────────────────────

elif page == PAGES[6]:
    hero(
        '<span class="neon">Architecture</span>',
        "File layout, the path a request takes from the network to the model, and what each "
        "layer is responsible for.",
        ar_line="كل طلب بيمر على أربع بوابات قبل ما يوصل للموديل.",
    )

    section("Project tree", "STRUCTURE")
    ascii_block([
        ".",
        "|-- main.py                         # API layer: routes + auth + CORS",
        "|-- requirements.txt                # pinned dependencies",
        "|-- Dockerfile                      # python:3.12-slim, port 7860",
        "|-- .env.example                    # environment template",
        "|-- streamlit_app.py                # this console",
        "|-- notebook/",
        "|   `-- text_classification.ipynb   # experiments notebook",
        "|-- data/",
        "|   |-- train_Arabic_tweets_positive_20190413.tsv   23,879 rows",
        "|   |-- train_Arabic_tweets_negative_20190413.tsv   23,121 rows",
        "|   |-- test_Arabic_tweets_positive_20190413.tsv     5,970 rows",
        "|   `-- test_Arabic_tweets_negative_20190413.tsv     5,781 rows",
        "`-- src/",
        "    |-- assets/storage/",
        "    |   |-- model_pickle.joblib          # ACTIVE model",
        "    |   |-- model_status.json            # active model status",
        "    |   |-- default_model_pickle.joblib  # DEFAULT, never overwritten",
        "    |   `-- default_model_status.json    # default model status",
        "    |-- controlers/NLPTrainer.py     # training + prediction logic",
        "    |-- helpers/config.py            # env loading + storage paths",
        "    `-- models/",
        "        |-- request.py               # input schemas",
        "        `-- response.py              # output schemas",
    ])

    section("Layer responsibilities", "LAYERS")
    grid([
        card("⊕", "main.py — transport",
             "Creates the FastAPI app, registers CORS, declares the six endpoints and wires key "
             "verification through Depends. It knows nothing about TF-IDF or file paths — it calls "
             "the trainer and wraps the result in a Pydantic schema.", 0.0),
        card("◉", "NLPTrainer — logic",
             "The only class that touches the model: loads it from disk, trains on a thread, "
             "computes the evaluation report, persists with joblib, and manages switching between "
             "the active and default artifacts.", 0.08),
        card("◈", "models/ — contracts",
             "Pydantic schemas are the contract between client and service. Any request that does "
             "not match the shape is rejected before reaching business logic, and Swagger docs are "
             "generated from the same definitions for free.", 0.16),
        card("⚙", "config.py — environment",
             "Loads APP_NAME, VERSION and SECRET_KEY_TOKEN from .env, builds the storage directory "
             "path relatively and ensures it exists — so the project runs on any machine.", 0.24),
        card("▥", "assets/storage — persistence",
             "Four files: one pair for the active model, one pair for the default. That separation "
             "is what turns rollback into a file copy instead of a retraining job.", 0.32),
        card("▤", "notebook — research record",
             "The log of experiments that led to the final configuration. Not part of runtime, but "
             "it documents why this setup and not another.", 0.40),
    ])

    section("Request flow", "PIPELINE")
    ascii_block([
        "CLIENT",
        '  |   POST /predict   { "text": "..." }',
        "  v",
        "[ Cloudflare ] ---> [ Uvicorn ] ---> [ FastAPI Router ]",
        "                                          |",
        "                                          v",
        "                          Depends(verify_api_key)",
        "                            |-- bad key   ---> 401 / 403",
        "                            `-- valid",
        "                                          |",
        "                                          v",
        "                          QueryText  (Pydantic validation)",
        "                            |-- bad body  ---> 422",
        "                            `-- valid",
        "                                          |",
        "                                          v",
        "                          NLPTrainer.predict([text])",
        "                            |-- no model  ---> 503",
        "                            `-- ok",
        "                                          |",
        "                                          v",
        "       TF-IDF (1,2)  --->  LogisticRegression.predict_proba",
        "                                          |",
        "                                          v",
        "            PredictionObject { text, predictions{neg, pos} }",
    ])
    lead("Four gates stand between the network and the model: the API key, the request shape, the "
         "presence of an active model, and only then does text get vectorised and scored.")

    section("Principles applied", "DESIGN RULES")
    st.markdown(tags([
        "Separation of Concerns", "Dependency Injection", "Schema-First Contracts",
        "Fail Fast with Clear Codes", "Immutable Default Artifact",
        "Non-blocking Background Work", "Config via Environment", "Pinned Dependencies",
    ], "g"), unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# 8) Data & Experiments
# ──────────────────────────────────────────────────────────────────────────────

elif page == PAGES[7]:
    hero(
        '<span class="neon">Data & Experiments</span>',
        "Where the corpus came from, what the text actually looks like, and how it is turned "
        "into numbers the classifier can learn from.",
        ar_line="الداتا متوازنة تقريبًا، وده وفّر مرحلة معالجة عدم التوازن بالكامل.",
    )

    section("Dataset", "SOURCE")
    grid([
        kpi("Total tweets", "58,751", "four TSV files", 0.0),
        kpi("Train split", "47,000", "23,879 pos · 23,121 neg", 0.08),
        kpi("Test split", "11,751", "5,970 pos · 5,781 neg", 0.16),
        kpi("On disk", "7 MB", "raw uncompressed text", 0.24),
    ], cols=4)

    lead("Source: the Arabic Sentiment Twitter Corpus — manually labelled Arabic tweets split into "
         "positive and negative, stored as headerless TSV where column one is the label and column "
         "two is the tweet text.")

    st.markdown(bar("Positive share of training data", 50.8, "pos")
                + bar("Negative share of training data", 49.2, "neg"),
                unsafe_allow_html=True)

    section("Character of the text", "OBSERVATIONS")
    grid([
        card("◈", "Mixed register",
         "Modern Standard Arabic sits next to Egyptian and Gulf dialect in the same corpus. That "
         "widens the vocabulary considerably and makes the task harder, but it also moves the "
         "model much closer to real-world usage.", 0.0),
        card("◎", "Emoji carry signal",
             "Many tweets contain emoji that encode sentiment directly. TF-IDF treats them as "
             "ordinary tokens, and several turn out to be among the strongest features in the "
             "model.", 0.08),
        card("▽", "Truncated tweets",
             "Some entries end mid-sentence because the original tweet exceeded the length limit — "
             "ordinary noise in social-media data.", 0.16),
        card("▦", "Rich morphology",
             "Arabic words change with prefixes, suffixes and attached pronouns, so a single root "
             "can appear in dozens of surface forms. That is exactly what motivated the character "
             "n-gram experiment.", 0.24),
    ], cols=4)

    section("Transformation pipeline", "FEATURES")
    ascii_block([
        "RAW ARABIC TEXT",
        "     |",
        "     v",
        "TfidfVectorizer(min_df=2, max_df=0.9, ngram_range=(1,2))",
        "     |    min_df=2    drop tokens seen only once  (noise / typos)",
        "     |    max_df=0.9  drop tokens in >90% of docs (stop-word-like)",
        "     |    (1,2)       unigrams + bigrams (captures negation)",
        "     v",
        "SPARSE TF-IDF MATRIX",
        "     |",
        "     v",
        "LogisticRegression  --->  predict_proba  --->  { neg: 0.41, pos: 0.59 }",
    ])
    ar_note("الفكرة في البايجرام إن الموديل يشوف «مش حلو» كوحدة واحدة، "
            "مش «حلو» لوحدها — وده الفرق بين تصنيف صح وتصنيف مقلوب تمامًا.")

    section("Why these choices", "RATIONALE")
    st.markdown(
        '<table class="tbl"><tr><th>Decision</th><th>Alternative</th><th>Reasoning</th></tr>'
        '<tr><td class="num">TF-IDF</td><td class="num">Word embeddings / BERT</td>'
        '<td>Light, fast, no GPU needed and self-explanatory — the right fit for a '
        'low-latency service</td></tr>'
        '<tr><td class="num">ngram (1,2)</td><td class="num">unigrams only</td>'
        '<td>Bigrams capture negated constructions that unigrams destroy the meaning of</td></tr>'
        '<tr><td class="num">LogisticRegression</td><td class="num">LinearSVC</td>'
        '<td>Returns calibrated probabilities via predict_proba — essential for an interface '
        'that displays confidence</td></tr>'
        '<tr><td class="num">Single Pipeline</td><td class="num">separate artifacts</td>'
        '<td>Guarantees identical transform steps between training and inference</td></tr>'
        '<tr><td class="num">joblib compress=9</td><td class="num">plain pickle</td>'
        '<td>Much smaller on disk and faster to move inside container images</td></tr>'
        "</table>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# 9) Challenges & Lessons
# ──────────────────────────────────────────────────────────────────────────────

elif page == PAGES[8]:
    hero(
        '<span class="neon">Challenges & Lessons</span>',
        "Real problems that surfaced during the build, how each was resolved, and the parts "
        "that are still open work.",
        ar_line="كل مشكلة هنا ظهرت فعلًا وقت البناء، مش سيناريو نظري.",
    )

    section("Solved", "FIXED")
    st.markdown(timeline([
        ("CHALLENGE 01", "Training froze the whole service",
         "Problem: synchronous training inside the request blocked the service from answering "
         "anything else. Fix: move training onto a separate thread and expose a polling endpoint. "
         "Lesson: work measured in seconds has no place inside a request handler."),
        ("CHALLENGE 02", "Two states, one dictionary",
         "Problem: assigning the default status dict straight to the active status meant both "
         "names referred to the same object, so any update polluted the original. Fix: "
         "copy.deepcopy on every state copy. Lesson: in Python, assignment is not copying."),
        ("CHALLENGE 03", "First-run experience required training",
         "Problem: a service that answers 'No Model Found' to its first user is a bad first "
         "impression. Fix: ship a trained default artifact and fall back to it automatically when "
         "no active model exists."),
        ("CHALLENGE 04", "Risk of losing the original model",
         "Problem: if training wrote over the same file, one bad run would destroy the baseline "
         "permanently. Fix: fully separate files for the default artifact that no code path writes "
         "to, plus a dedicated restore endpoint."),
        ("CHALLENGE 05", "joblib is version-coupled",
         "Problem: the artifact is tied to the scikit-learn version that produced it, and loading "
         "it elsewhere can fail. Fix: pin scikit-learn==1.6.1 and record the version inside the "
         "status file itself."),
    ]), unsafe_allow_html=True)

    section("Known limitations", "OPEN")
    grid([
        card("⊟", "Binary only",
             "There is no neutral class. Genuinely neutral text — news, questions, plain facts — "
             "is forced into positive or negative, which shows up as confidence hovering near "
             "50%.", 0.0),
        card("◍", "Sarcasm and figures of speech",
             "Irony is among the hardest problems in sentiment analysis generally, and a linear "
             "model over TF-IDF cannot capture context that inverts meaning.", 0.08),
        card("⊕", "Domain shift",
             "The model learned from 2019 tweets; text from a very different domain will score "
             "worse. That is precisely why the /train endpoint exists.", 0.16),
        card("○", "No Arabic normalisation",
             "Alef and hamza forms, taa marbuta, diacritics and elongation are not normalised, so "
             "the same word written differently becomes separate tokens.", 0.24),
        card("◎", "Race window during training",
             "The active model is cleared at the start of a training run, so a prediction request "
             "in that instant can return 503. Proposed fix: build into a temporary variable and "
             "swap only on success.", 0.32),
        card("▥", "Single model slot",
             "Only one active model exists; each new training run replaces the previous one. "
             "Multi-model storage is a headline item on the roadmap.", 0.40),
    ])

    section("Three takeaways", "SUMMARY")
    st.markdown(
        '<table class="tbl"><tr><th>Lesson</th><th>How it played out here</th></tr>'
        '<tr><td>Start with the simplest model</td>'
        '<td>The plain baseline landed close to more complex configurations, which made it worth '
        'building on rather than discarding</td></tr>'
        '<tr><td>Model choice is not only accuracy</td>'
        '<td>Needing predict_proba decided LogisticRegression over LinearSVC despite comparable '
        'scores</td></tr>'
        '<tr><td>Mutable shared state is a bug factory</td>'
        '<td>The shared-dictionary defect was more damaging than any modelling issue in the '
        'project</td></tr>'
        "</table>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# 10) API Reference
# ──────────────────────────────────────────────────────────────────────────────

elif page == PAGES[9]:
    base = st.session_state.get("api_base", API_BASE_DEFAULT)
    hero(
        '<span class="neon">API Reference</span>',
        f"All six endpoints. Every one requires the X-API-Key header. Base URL: {base} — "
        f"interactive Swagger docs live at {base}/docs.",
        ar_line="كل نقطة بتطلب المفتاح بدون استثناء واحد.",
    )

    endpoints = [
        ("GET", "/", "Health check",
         "Returns the application name and version — a cheap way to confirm the service and your "
         "key both work.",
         None, '{ "App_Name": "VibeAR", "Version": "1.0.0" }'),
        ("GET", "/status", "Model status",
         "Current state, class labels and the full evaluation report of the active model.",
         None,
         '{\n  "status": "Model Ready",\n  "classes": ["neg", "pos"],\n'
         '  "evaluation": { "accuracy": 0.789, "...": "..." }\n}'),
        ("POST", "/train", "Train a new model",
         "Starts training on a background thread and returns immediately with status Training. "
         "Poll /status until it reports Model Ready.",
         '{\n  "texts": ["الخدمة ممتازة", "تجربة سيئة"],\n  "labels": ["pos", "neg"]\n}',
         '{ "status": "Training", "classes": [], "evaluation": {} }'),
        ("POST", "/use-default-model", "Restore default",
         "Makes the shipped default model active again without retraining, and persists the new "
         "state to disk.",
         None, "same shape as the /status response"),
        ("POST", "/predict", "Single prediction",
         "Returns a probability for each class for one sentence.",
         '{ "text": "الخدمة كانت ممتازة جدا" }',
         '{\n  "text": "الخدمة كانت ممتازة جدا",\n'
         '  "predictions": { "neg": 0.417, "pos": 0.583 }\n}'),
        ("POST", "/predict-batch", "Batch prediction",
         "Identical logic applied to a list of sentences in one request.",
         '{ "texts": ["جملة أولى", "جملة تانية"] }',
         '{\n  "predictions": [\n    { "text": "...", "predictions": {...} }\n  ]\n}'),
    ]

    for method, path, title, desc, body, resp in endpoints:
        color = "#8ff0c8" if method == "GET" else "#c8b6ff"
        with st.expander(f"{method}   {path}   —   {title}", expanded=False):
            st.markdown(
                f'<div style="font-family:JetBrains Mono,monospace;font-size:.78rem;'
                f'color:{color};margin-bottom:.7rem;">{method} {base}{path}</div>'
                f'<p class="lead">{desc}</p>',
                unsafe_allow_html=True,
            )
            if body:
                st.markdown("**Request body**")
                st.code(body, language="json")
            st.markdown("**Response**")
            st.code(resp, language="json")

    section("Status codes", "ERRORS")
    st.markdown(
        '<table class="tbl"><tr><th>Code</th><th>Meaning</th><th>Typical cause</th></tr>'
        '<tr><td class="num ok">200</td><td>OK</td><td>Valid request and valid key</td></tr>'
        '<tr><td class="num warn">401</td><td>Missing key header</td>'
        '<td>Request sent without X-API-Key at all</td></tr>'
        '<tr><td class="num warn">403</td><td>Forbidden</td>'
        '<td>Key present but does not match the configured secret</td></tr>'
        '<tr><td class="num bad">422</td><td>Unprocessable entity</td>'
        '<td>JSON body does not match the Pydantic schema</td></tr>'
        '<tr><td class="num bad">503</td><td>Service unavailable</td>'
        '<td>No active model, or an error during training or prediction</td></tr>'
        "</table>",
        unsafe_allow_html=True,
    )

    section("Snippets", "COPY & RUN")
    tb1, tb2 = st.tabs(["cURL", "Python"])
    with tb1:
        st.code(
            f'curl -X POST {base}/predict \\\n'
            f'  -H "X-API-Key: $API_KEY" \\\n'
            f'  -H "Content-Type: application/json" \\\n'
            f"  -d '{{\"text\": \"الخدمة كانت ممتازة\"}}'",
            language="bash",
        )
    with tb2:
        st.code(
            "import requests\n\n"
            f'BASE = "{base}"\n'
            'HEAD = {"X-API-Key": "your-key"}\n\n'
            'r = requests.post(f"{BASE}/predict", headers=HEAD,\n'
            '                  json={"text": "الخدمة كانت ممتازة"})\n'
            "print(r.json())",
            language="python",
        )


# ──────────────────────────────────────────────────────────────────────────────
# 11) Roadmap
# ──────────────────────────────────────────────────────────────────────────────

elif page == PAGES[10]:
    hero(
        '<span class="neon">Roadmap</span>',
        "What comes next, ordered by return on effort — from cheap wins that need no new "
        "modelling to architectural changes.",
        ar_line="أي إضافة لازم تثبت بالأرقام إنها أحسن من الخط الحالي قبل ما تدخل الإنتاج.",
    )

    section("High value, low effort", "QUICK WINS")
    grid([
        card("01", "Arabic text normalisation",
             "Unify alef and hamza variants and taa marbuta, strip diacritics, elongation and "
             "character repetition. The cheapest available accuracy gain, with no change to the "
             "model itself.", 0.0),
        card("02", "Stronger validation in /train",
             "Assert that texts and labels have equal length, that at least two classes are "
             "present, and enforce a minimum example count before any training starts.", 0.08),
        card("03", "Confidence threshold in /predict",
             "Flag low-confidence results with a low_confidence field so callers know the input "
             "sits on the boundary or outside the training domain.", 0.16),
    ], cols=3)

    section("Medium priority", "NEXT UP")
    grid([
        card("04", "Multi-model storage",
             "Keep several trained models with identifiers, add a /models endpoint that lists them "
             "with their evaluation reports, and allow per-request model selection.", 0.0),
        card("05", "Neutral class",
             "Extend to three-way classification. This needs neutral-labelled data, which is the "
             "hardest part of the project from a data-collection standpoint.", 0.08),
        card("06", "CORS and rate limiting",
             "The current configuration allows all origins, which is fine for a demo but not for "
             "production — an explicit domain allow-list plus request throttling is required.",
             0.16),
        card("07", "Automated test suite",
             "pytest coverage per endpoint: valid and invalid keys, malformed bodies, prediction "
             "with no model loaded, and a full training cycle.", 0.24),
        card("08", "Metrics and monitoring",
             "Log latency and confidence distribution per request so drift becomes visible before "
             "users report it.", 0.32),
        card("09", "Unify dependency declarations",
             "requirements.txt and pyproject.toml currently disagree, and the latter lists packages "
             "the project never imports. One source of truth is needed.", 0.40),
    ])

    section("Ambitious", "LONGER TERM")
    grid([
        card("10", "Pretrained Arabic transformer",
             "Benchmark AraBERT or MARBERT against the current baseline. A meaningful accuracy gain "
             "is likely, traded against higher latency and heavier hardware — worth measuring "
             "before committing.", 0.0),
        card("11", "Prediction explanations",
             "Surface the tokens that pushed each decision. Relatively easy with a linear model "
             "because the coefficients are directly readable.", 0.08),
        card("12", "Scheduled retraining",
             "A pipeline that collects newly labelled data and retrains periodically, promoting "
             "the new model only when it beats the incumbent on the held-out split.", 0.16),
    ], cols=3)


# ──────────────────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────────────────

st.markdown(
    '<div style="margin-top:4rem;padding:1.5rem 0 1rem;border-top:1px solid rgba(255,255,255,.1);'
    'text-align:center;color:#828ba3;font-size:.78rem;line-height:2;">'
    '<span class="neon" style="font-family:Space Grotesk,sans-serif;font-weight:700;'
    'font-size:1.05rem;">VibeAR</span><br>'
    'Arabic sentiment analysis · FastAPI + scikit-learn + Streamlit<br>'
    '<span style="font-family:JetBrains Mono,monospace;font-size:.68rem;'
    'display:inline-block;margin-top:.35rem;letter-spacing:.1em;">'
    'CLASSICAL NLP · TF-IDF + LOGISTIC REGRESSION</span></div>',
    unsafe_allow_html=True,
)