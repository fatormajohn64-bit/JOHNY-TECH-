# =============================================================================
#  JOHNNY TEC — Neural Command Interface (Streamlit / Web Edition)
#  A browser-hosted, Jarvis-inspired voice assistant with a cyber-matrix HUD.
#
#  Stack:
#      Framework       : Streamlit
#      Speech-to-Text  : Browser Web Speech API (via streamlit-mic-recorder)
#      Text-to-Speech  : Browser speechSynthesis API (zero server dependency)
#      Visualizer      : HTML5 Canvas animation embedded via components.html
#
#  Deploy: push to GitHub, connect the repo on share.streamlit.io, done.
#  Author: Johnny Tec Systems (Invincible 911 build)
#  Version: 1.0.0 (web)
# =============================================================================

import re
import random
import urllib.parse
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

try:
    from streamlit_mic_recorder import speech_to_text
except ImportError:
    speech_to_text = None


# =============================================================================
#  SECTION 1 — THEME CONSTANTS
# =============================================================================

class Theme:
    BG_OBSIDIAN    = "#0B0C10"
    BG_PANEL       = "#101318"
    BG_PANEL_EDGE  = "#141820"
    CYAN           = "#66FCF1"
    CYAN_DIM       = "#2E4A48"
    PURPLE         = "#833AB4"
    PURPLE_BRIGHT  = "#B24BF3"
    GREEN_OK       = "#39FF88"
    RED_ALERT      = "#FF4C4C"
    AMBER_WARN     = "#FFC857"
    TEXT_PRIMARY   = "#E8FFFE"
    TEXT_SECONDARY = "#7FA8A5"
    BORDER         = "#1F2A2E"
    FONT_MONO      = "'Share Tech Mono', 'Consolas', monospace"
    FONT_DISPLAY   = "'Orbitron', sans-serif"


STATE_COLORS = {
    "IDLE":       Theme.CYAN,
    "LISTENING":  Theme.CYAN,
    "PROCESSING": Theme.PURPLE_BRIGHT,
    "SPEAKING":   Theme.GREEN_OK,
    "ERROR":      Theme.RED_ALERT,
}


# =============================================================================
#  SECTION 2 — PAGE CONFIG + GLOBAL CSS
# =============================================================================

def configure_page():
    st.set_page_config(
        page_title="JOHNNY TEC :: Neural Command Interface",
        page_icon="◆",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def inject_global_css():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Share+Tech+Mono&display=swap');

        html, body, [class*="css"] {{
            background-color: {Theme.BG_OBSIDIAN} !important;
            color: {Theme.TEXT_PRIMARY};
            font-family: {Theme.FONT_MONO};
        }}
        #MainMenu, footer, header {{ visibility: hidden; }}
        .block-container {{ padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1300px; }}

        .jt-title {{
            font-family: {Theme.FONT_DISPLAY};
            font-size: 26px;
            font-weight: 900;
            letter-spacing: 3px;
            color: {Theme.CYAN};
            text-shadow: 0 0 12px {Theme.CYAN}88;
        }}
        .jt-clock {{
            font-family: {Theme.FONT_MONO};
            font-size: 13px;
            color: {Theme.TEXT_SECONDARY};
            text-align: right;
        }}
        .jt-divider {{
            border: none;
            border-top: 1px solid {Theme.BORDER};
            margin: 10px 0 18px 0;
        }}
        .jt-panel {{
            background-color: {Theme.BG_PANEL};
            border: 1px solid {Theme.BORDER};
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 14px;
        }}
        .jt-panel-title {{
            color: {Theme.PURPLE_BRIGHT};
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 1.5px;
            border-bottom: 1px solid {Theme.BORDER};
            padding-bottom: 6px;
            margin-bottom: 8px;
        }}
        .jt-row {{
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            padding: 3px 0;
        }}
        .jt-row-label {{ color: {Theme.TEXT_SECONDARY}; letter-spacing: 0.5px; }}
        .jt-row-value {{ color: {Theme.CYAN}; font-weight: bold; }}

        .jt-console {{
            background-color: {Theme.BG_PANEL};
            border: 1px solid {Theme.BORDER};
            border-radius: 8px;
            padding: 12px 14px;
            height: 220px;
            overflow-y: auto;
            font-size: 12px;
            line-height: 1.6;
        }}
        .jt-console-ts {{ color: {Theme.TEXT_SECONDARY}; }}
        .jt-console-tag {{ font-weight: bold; }}

        .jt-state-caption {{
            text-align: center;
            color: {Theme.TEXT_SECONDARY};
            font-size: 12px;
            letter-spacing: 1.5px;
            margin-top: 6px;
        }}

        div.stButton > button {{
            background-color: {Theme.BG_PANEL_EDGE};
            color: {Theme.CYAN};
            border: 1px solid {Theme.CYAN_DIM};
            border-radius: 6px;
            font-family: {Theme.FONT_MONO};
            letter-spacing: 1px;
            font-weight: bold;
            font-size: 12px;
            padding: 0.5rem 1rem;
        }}
        div.stButton > button:hover {{
            border: 1px solid {Theme.CYAN};
            color: {Theme.TEXT_PRIMARY};
            background-color: {Theme.CYAN_DIM};
        }}
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
#  SECTION 3 — SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    defaults = {
        "assistant_state": "IDLE",
        "logs": [],
        "metrics": {
            "status": "ONLINE",
            "engine": "NEURAL-CORE v1 (web)",
            "integrity": "100%",
            "latency": "0.02ms",
            "audio_state": "STANDBY",
            "last_cmd": "NONE",
            "last_action": "IDLE",
            "recognizer": "WEB-SPEECH-API",
        },
        "pending_speech": None,
        "boot_done": False,
        "last_heard": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def log_event(message, tag="SYS", color=Theme.CYAN):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append((timestamp, tag, color, message))
    st.session_state.logs = st.session_state.logs[-60:]


def update_metric(key, value):
    st.session_state.metrics[key] = value


def set_state(new_state):
    st.session_state.assistant_state = new_state


# =============================================================================
#  SECTION 4 — HUD VISUALIZER (HTML5 canvas component)
# =============================================================================

def render_visualizer(state: str, height: int = 340):
    color = STATE_COLORS.get(state, Theme.CYAN)
    html = f"""
    <div style="display:flex; justify-content:center; align-items:center; background:transparent;">
        <canvas id="hud" width="340" height="340"></canvas>
    </div>
    <script>
        const canvas = document.getElementById('hud');
        const ctx = canvas.getContext('2d');
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const baseRadius = 150;
        const color = "{color}";
        const stateLabel = "{state}";
        let angle = 0;
        let angleRev = 0;
        let pulsePhase = 0;
        let bars = Array.from({{length: 48}}, () => Math.random() * 0.7 + 0.2);

        function hexToRgba(hex, alpha) {{
            const r = parseInt(hex.slice(1,3),16);
            const g = parseInt(hex.slice(3,5),16);
            const b = parseInt(hex.slice(5,7),16);
            return `rgba(${{r}},${{g}},${{b}},${{alpha}})`;
        }}

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // outer glow
            const glow = ctx.createRadialGradient(cx, cy, baseRadius*0.6, cx, cy, baseRadius*1.35);
            glow.addColorStop(0, hexToRgba(color, 0.18));
            glow.addColorStop(1, hexToRgba(color, 0));
            ctx.fillStyle = glow;
            ctx.beginPath();
            ctx.arc(cx, cy, baseRadius*1.35, 0, Math.PI*2);
            ctx.fill();

            // outer rotating segmented ring
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(angle * Math.PI/180);
            const segCount = 36;
            for (let i = 0; i < segCount; i++) {{
                const segAngle = (Math.PI*2) / segCount;
                const active = (i % 3 !== 0);
                ctx.strokeStyle = hexToRgba(color, active ? 0.9 : 0.25);
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.arc(0, 0, baseRadius, i*segAngle, i*segAngle + segAngle*0.65);
                ctx.stroke();
            }}
            ctx.restore();

            // mid counter-rotating dashed ring
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(angleRev * Math.PI/180);
            ctx.setLineDash([4, 7]);
            ctx.strokeStyle = "{Theme.PURPLE}";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(0, 0, baseRadius*0.80, 0, Math.PI*2);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.restore();

            // inner spectrum bars
            ctx.save();
            ctx.translate(cx, cy);
            const barRIn = baseRadius * 0.46;
            const barSpan = baseRadius * 0.18;
            const n = bars.length;
            for (let i = 0; i < n; i++) {{
                const theta = (Math.PI*2 / n) * i;
                const len = barSpan * bars[i];
                ctx.save();
                ctx.rotate(theta);
                ctx.strokeStyle = hexToRgba(color, 0.85);
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(0, -barRIn);
                ctx.lineTo(0, -(barRIn + len));
                ctx.stroke();
                ctx.restore();
            }}
            ctx.restore();

            // pulsing core
            const pulse = (Math.sin(pulsePhase) + 1) / 2;
            const coreR = baseRadius * (0.30 + 0.03 * pulse);
            const coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR);
            coreGrad.addColorStop(0, hexToRgba(color, 0.85));
            coreGrad.addColorStop(1, hexToRgba(color, 0.05));
            ctx.fillStyle = coreGrad;
            ctx.beginPath();
            ctx.arc(cx, cy, coreR, 0, Math.PI*2);
            ctx.fill();
            ctx.strokeStyle = color;
            ctx.lineWidth = 1;
            ctx.stroke();

            // brand text
            ctx.fillStyle = "{Theme.TEXT_PRIMARY}";
            ctx.font = "bold 17px Orbitron, sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("JOHNNY TEC", cx, cy - 2);

            ctx.fillStyle = color;
            ctx.font = "10px 'Share Tech Mono', monospace";
            ctx.fillText("[ " + stateLabel + " ]", cx, cy + 18);

            angle = (angle + 1.6) % 360;
            angleRev = (angleRev - 1.1 + 360) % 360;
            pulsePhase += 0.10;
            for (let i = 0; i < bars.length; i++) {{
                if (Math.random() < 0.08) {{
                    bars[i] = Math.random() * 0.75 + 0.25;
                }} else {{
                    bars[i] += (0.4 - bars[i]) * 0.06;
                }}
            }}
            requestAnimationFrame(draw);
        }}
        draw();
    </script>
    """
    components.html(html, height=height)


# =============================================================================
#  SECTION 5 — TEXT TO SPEECH (browser speechSynthesis)
# =============================================================================

def speak_in_browser(text: str):
    safe_text = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    html = f"""
    <script>
        try {{
            const synth = window.parent.speechSynthesis || window.speechSynthesis;
            const utter = new SpeechSynthesisUtterance("{safe_text}");
            utter.rate = 1.02;
            utter.pitch = 0.95;
            utter.volume = 1.0;
            const voices = synth.getVoices();
            const preferred = voices.find(v => /male|david|daniel|en-/i.test(v.name + v.lang));
            if (preferred) {{ utter.voice = preferred; }}
            synth.cancel();
            synth.speak(utter);
        }} catch (e) {{ console.log("TTS error", e); }}
    </script>
    """
    components.html(html, height=0)


# =============================================================================
#  SECTION 6 — COMMAND ENGINE
# =============================================================================

WITTY_FAILS = [
    "I'm afraid I didn't catch that directive, sir.",
    "That command fell outside my current parameters. Try again?",
    "Signal received, but the instruction set was incomplete.",
    "I'm going to need a bit more clarity on that one, sir.",
]


def cmd_system_check(text, match):
    latency = round(random.uniform(0.01, 0.09), 3)
    integrity = random.randint(96, 100)
    update_metric("latency", f"{latency}ms")
    update_metric("integrity", f"{integrity}%")
    update_metric("status", "ONLINE")
    log_event("Running full neural diagnostic sweep...", "CMD", Theme.PURPLE_BRIGHT)
    response = (
        f"System check complete, sir. All subsystems nominal. "
        f"Neural integrity at {integrity} percent, latency holding at {latency} milliseconds."
    )
    return response, "system_check", None


def cmd_search_web(text, match):
    query = match.group(2).strip() if match and match.lastindex and match.lastindex >= 2 else text
    if not query:
        return "I need something to search for, sir.", "search_web", None
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    log_event(f"Launching web search for '{query}'", "NET", Theme.CYAN)
    return f"Searching the web for {query}, sir.", "search_web", url


def cmd_open_browser(text, match):
    log_event("Opening default search engine.", "NET", Theme.CYAN)
    return "Browser interface online, sir.", "open_browser", "https://www.google.com"


def cmd_show_map(text, match):
    groups = match.groups() if match else ()
    location = groups[-1].strip() if groups and groups[-1] else "current location"
    url = "https://www.google.com/maps/search/" + urllib.parse.quote_plus(location)
    log_event(f"Pulling cartographic data for '{location}'", "NAV", Theme.PURPLE_BRIGHT)
    return f"Displaying map coordinates for {location}, sir.", "show_map", url


def cmd_time_date(text, match):
    now = datetime.now()
    time_str = now.strftime("%I:%M %p").lstrip("0")
    date_str = now.strftime("%A, %B %d, %Y")
    log_event(f"Temporal sync: {time_str} — {date_str}", "SYS", Theme.CYAN)
    return f"Temporal scan complete. It is currently {time_str}, on {date_str}, sir.", "time_date", None


def cmd_clear_logs(text, match):
    st.session_state.logs = []
    log_event("Log matrix cleared and reinitialized.", "SYS", Theme.AMBER_WARN)
    update_metric("status", "MATRIX RESET")
    return "Dashboard logs cleared and matrix reinitialized, sir.", "clear_logs", None


def cmd_introduce(text, match):
    return (
        "I am JOHNNY TEC, an autonomous neural interface running in your browser, "
        "designed for voice-driven command and system oversight, sir.",
        "introduce", None
    )


def cmd_joke(text, match):
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs, sir.",
        "I would tell you a UDP joke, but you might not get it.",
        "There are only 10 types of people, sir: those who understand binary and those who don't.",
    ]
    return random.choice(jokes), "joke", None


def cmd_greeting(text, match):
    hour = datetime.now().hour
    greet = "Good morning, sir." if hour < 12 else "Good afternoon, sir." if hour < 18 else "Good evening, sir."
    return f"{greet} All systems are online and awaiting your command.", "greeting", None


def cmd_shutdown(text, match):
    log_event("Shutdown directive received. Standing by.", "SYS", Theme.AMBER_WARN)
    return "Powering down active listeners, sir. Standing by.", "shutdown", None


COMMAND_TABLE = [
    (r"\b(system check|run diagnostics|status report)\b", cmd_system_check),
    (r"\b(search for|google|look up) (.+)", cmd_search_web),
    (r"\bopen browser\b", cmd_open_browser),
    (r"\b(show|find|pull up)?\s*map (of|for)? ?(.+)", cmd_show_map),
    (r"\b(time and date|what time|what's the date|current time)\b", cmd_time_date),
    (r"\b(clear logs|initiate matrix|reset dashboard|clear the console)\b", cmd_clear_logs),
    (r"\b(who are you|introduce yourself|what is your name)\b", cmd_introduce),
    (r"\b(tell me a joke|say something funny)\b", cmd_joke),
    (r"\b(good morning|good evening|hello|hey johnny|hi johnny)\b", cmd_greeting),
    (r"\b(shutdown|power down|exit|goodbye|stand down)\b", cmd_shutdown),
]


def process_command(raw_text: str):
    text = raw_text.strip().lower()
    for pattern, handler in COMMAND_TABLE:
        m = re.search(pattern, text)
        if m:
            return handler(text, m)
    return random.choice(WITTY_FAILS), "unknown", None


# =============================================================================
#  SECTION 7 — PANEL RENDERING HELPERS
# =============================================================================

def render_panel(title, rows):
    rows_html = "".join(
        f'<div class="jt-row"><span class="jt-row-label">{label}</span>'
        f'<span class="jt-row-value">{value}</span></div>'
        for label, value in rows
    )
    st.markdown(f"""
        <div class="jt-panel">
            <div class="jt-panel-title">◈ {title}</div>
            {rows_html}
        </div>
    """, unsafe_allow_html=True)


def render_console():
    if not st.session_state.logs:
        rows = '<div class="jt-console-ts">Awaiting first directive...</div>'
    else:
        rows = ""
        for ts, tag, color, message in reversed(st.session_state.logs):
            rows += (
                f'<div><span class="jt-console-ts">[{ts}]</span> '
                f'<span class="jt-console-tag" style="color:{color};">[{tag}]</span> '
                f'{message}</div>'
            )
    st.markdown(f'<div class="jt-console">{rows}</div>', unsafe_allow_html=True)


def open_url_in_new_tab(url: str):
    safe_url = url.replace('"', '%22')
    components.html(f'<script>window.open("{safe_url}", "_blank");</script>', height=0)


# =============================================================================
#  SECTION 8 — MAIN DISPATCH
# =============================================================================

def dispatch_text(heard_text: str):
    log_event(f'Heard: "{heard_text}"', "MIC", Theme.CYAN)
    update_metric("last_cmd", heard_text[:32])
    set_state("PROCESSING")

    response, action, url = process_command(heard_text)

    update_metric("last_action", action.upper())
    log_event(response, "AI", Theme.PURPLE_BRIGHT)
    set_state("SPEAKING")

    if url:
        open_url_in_new_tab(url)
    speak_in_browser(response)


# =============================================================================
#  SECTION 9 — MAIN APP LAYOUT
# =============================================================================

def main():
    configure_page()
    inject_global_css()
    init_session_state()

    if not st.session_state.boot_done:
        log_event("JOHNNY TEC neural core initializing...", "BOOT", Theme.PURPLE_BRIGHT)
        log_event("Loading command matrix and audio subsystem...", "BOOT", Theme.CYAN)
        log_event("Voice pipeline armed. Click START LISTENING to begin.", "BOOT", Theme.GREEN_OK)
        st.session_state.boot_done = True

    # --- Top bar -------------------------------------------------------------
    top_l, top_r = st.columns([3, 1])
    with top_l:
        st.markdown('<div class="jt-title">◆ JOHNNY TEC — NEURAL COMMAND MATRIX ◆</div>', unsafe_allow_html=True)
    with top_r:
        st.markdown(
            f'<div class="jt-clock">{datetime.now().strftime("%A, %d %B %Y — %H:%M:%S")}</div>',
            unsafe_allow_html=True
        )
    st.markdown('<hr class="jt-divider">', unsafe_allow_html=True)

    # --- Body: left panels | visualizer | right panels ------------------------
    left, center, right = st.columns([3, 5, 3])

    with left:
        render_panel("SYSTEM STATUS", [
            ("STATUS", st.session_state.metrics["status"]),
            ("ENGINE", st.session_state.metrics["engine"]),
            ("INTEGRITY", st.session_state.metrics["integrity"]),
        ])
        render_panel("AUDIO INPUT", [
            ("INPUT", st.session_state.metrics["audio_state"]),
            ("RECOGNIZER", st.session_state.metrics["recognizer"]),
        ])

    with center:
        render_visualizer(st.session_state.assistant_state)
        st.markdown(
            f'<div class="jt-state-caption">[ {st.session_state.assistant_state} ]'
            f' — {"LISTENING FOR DIRECTIVE..." if st.session_state.assistant_state == "LISTENING" else "AWAITING VOICE DIRECTIVE..."}</div>',
            unsafe_allow_html=True
        )
        st.write("")

        mic_col1, mic_col2, mic_col3 = st.columns([1, 2, 1])
        with mic_col2:
            if speech_to_text is None:
                st.error(
                    "streamlit-mic-recorder isn't installed. Run: "
                    "pip install streamlit-mic-recorder"
                )
            else:
                heard = speech_to_text(
                    language="en",
                    start_prompt="🎙 START LISTENING",
                    stop_prompt="⏸ STOP",
                    just_once=False,
                    use_container_width=True,
                    key="jt_mic",
                )
                if heard and heard != st.session_state.last_heard:
                    st.session_state.last_heard = heard
                    update_metric("audio_state", "PROCESSING")
                    dispatch_text(heard)
                    set_state("IDLE")
                    update_metric("audio_state", "LISTENING")
                    st.rerun()

        btn_a, btn_b, btn_c = st.columns(3)
        with btn_a:
            if st.button("⚙ SYSTEM CHECK", use_container_width=True):
                dispatch_text("system check")
                st.rerun()
        with btn_b:
            if st.button("🕐 TIME & DATE", use_container_width=True):
                dispatch_text("time and date")
                st.rerun()
        with btn_c:
            if st.button("⟲ CLEAR LOGS", use_container_width=True):
                dispatch_text("clear logs")
                st.rerun()

    with right:
        render_panel("LINK METRICS", [
            ("LATENCY", st.session_state.metrics["latency"]),
            ("BANDWIDTH", "STABLE"),
        ])
        render_panel("LAST COMMAND", [
            ("DIRECTIVE", st.session_state.metrics["last_cmd"]),
            ("ACTION", st.session_state.metrics["last_action"]),
        ])

    # --- Bottom: log console ---------------------------------------------------
    st.markdown('<div class="jt-panel-title" style="margin-top:8px;">◈ SYSTEM LOG FEED</div>', unsafe_allow_html=True)
    render_console()

    st.caption(
        "Voice input requires microphone permission in your browser. Click START LISTENING once — "
        "after that, JOHNNY TEC keeps listening continuously without further clicks."
    )


if __name__ == "__main__":
    main()
