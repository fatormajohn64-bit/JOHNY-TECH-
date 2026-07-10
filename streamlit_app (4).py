# =============================================================================
#  JOHNNY TEC — Neural Command Interface (Streamlit / Web Edition v2)
#  Main screen: visualizer + mic only. All text/metrics live in the sidebar.
#
#  Stack:
#      Framework       : Streamlit
#      Speech-to-Text  : Browser Web Speech API (via streamlit-mic-recorder)
#      Text-to-Speech  : Browser speechSynthesis API
#      Visualizer      : HTML5 Canvas animation embedded via components.html
#
#  Author: Johnny Tec Systems (Invincible 911 build)
#  Version: 2.0.0 (web, sidebar edition)
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
#  SECTION 1 — THEME + IDENTITY CONSTANTS
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

USER_TITLE = "Sir Abdullah"

WELCOME_MESSAGES = [
    f"Welcome back, {USER_TITLE}. All systems are primed and ready.",
    f"Good to see you, {USER_TITLE}. JOHNNY TEC is fully online.",
    f"Systems synchronized. Standing by for your command, {USER_TITLE}.",
    f"Ah, {USER_TITLE} has arrived. Initiating full operational mode.",
    f"Welcome aboard, {USER_TITLE}. The neural core is at your service.",
    f"Good day, {USER_TITLE}. JOHNNY TEC reporting for duty.",
    f"Systems online. It's good to have you back, {USER_TITLE}.",
    f"{USER_TITLE}, all subsystems check green. I'm listening whenever you're ready.",
]


# =============================================================================
#  SECTION 2 — PAGE CONFIG + GLOBAL CSS
# =============================================================================

def configure_page():
    st.set_page_config(
        page_title="JOHNNY TEC",
        page_icon="◆",
        layout="wide",
        initial_sidebar_state="expanded",
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
        .block-container {{
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
            max-width: 900px;
        }}
        section[data-testid="stSidebar"] {{
            background-color: {Theme.BG_PANEL};
            border-right: 1px solid {Theme.BORDER};
        }}

        .jt-panel {{
            background-color: {Theme.BG_PANEL_EDGE};
            border: 1px solid {Theme.BORDER};
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 12px;
        }}
        .jt-panel-title {{
            color: {Theme.PURPLE_BRIGHT};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1.5px;
            border-bottom: 1px solid {Theme.BORDER};
            padding-bottom: 6px;
            margin-bottom: 8px;
        }}
        .jt-row {{
            display: flex;
            justify-content: space-between;
            font-size: 11.5px;
            padding: 3px 0;
        }}
        .jt-row-label {{ color: {Theme.TEXT_SECONDARY}; letter-spacing: 0.5px; }}
        .jt-row-value {{ color: {Theme.CYAN}; font-weight: bold; }}

        .jt-console {{
            background-color: {Theme.BG_PANEL_EDGE};
            border: 1px solid {Theme.BORDER};
            border-radius: 8px;
            padding: 10px 12px;
            height: 200px;
            overflow-y: auto;
            font-size: 10.5px;
            line-height: 1.6;
        }}
        .jt-console-ts {{ color: {Theme.TEXT_SECONDARY}; }}
        .jt-console-tag {{ font-weight: bold; }}

        .jt-sidebar-title {{
            font-family: {Theme.FONT_DISPLAY};
            font-size: 16px;
            font-weight: 900;
            letter-spacing: 2px;
            color: {Theme.CYAN};
            text-shadow: 0 0 10px {Theme.CYAN}88;
            margin-bottom: 4px;
        }}

        /* Mic button: icon-only, no visible label text */
        div[data-testid="stHorizontalBlock"] button {{
            border-radius: 50% !important;
            width: 84px !important;
            height: 84px !important;
            font-size: 30px !important;
            background-color: {Theme.BG_PANEL_EDGE} !important;
            border: 2px solid {Theme.CYAN_DIM} !important;
            color: {Theme.CYAN} !important;
        }}
        div[data-testid="stHorizontalBlock"] button:hover {{
            border: 2px solid {Theme.CYAN} !important;
            box-shadow: 0 0 18px {Theme.CYAN}55;
        }}

        div.stButton > button {{
            background-color: {Theme.BG_PANEL_EDGE};
            color: {Theme.CYAN};
            border: 1px solid {Theme.CYAN_DIM};
            border-radius: 6px;
            font-family: {Theme.FONT_MONO};
            letter-spacing: 1px;
            font-weight: bold;
            font-size: 11px;
        }}
        div.stButton > button:hover {{
            border: 1px solid {Theme.CYAN};
            color: {Theme.TEXT_PRIMARY};
            background-color: {Theme.CYAN_DIM};
        }}
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
#  SECTION 3 — SESSION STATE
# =============================================================================

def init_session_state():
    defaults = {
        "assistant_state": "IDLE",
        "logs": [],
        "metrics": {
            "status": "ONLINE",
            "engine": "NEURAL-CORE v2 (web)",
            "integrity": "100%",
            "latency": "0.02ms",
            "audio_state": "STANDBY",
            "last_cmd": "NONE",
            "last_action": "IDLE",
            "recognizer": "WEB-SPEECH-API",
        },
        "greeted": False,
        "engaged": False,
        "last_heard": "",
        "pending_greeting": False,
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
#  SECTION 4 — HUD VISUALIZER (HTML5 canvas, no text overlay besides state)
# =============================================================================

def render_visualizer(state: str, height: int = 380):
    color = STATE_COLORS.get(state, Theme.CYAN)
    html = f"""
    <div style="display:flex; justify-content:center; align-items:center; background:transparent;">
        <canvas id="hud" width="360" height="360"></canvas>
    </div>
    <script>
        const canvas = document.getElementById('hud');
        const ctx = canvas.getContext('2d');
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const baseRadius = 158;
        const color = "{color}";
        const stateLabel = "{state}";
        let angle = 0;
        let angleRev = 0;
        let pulsePhase = 0;
        let bars = Array.from({{length: 52}}, () => Math.random() * 0.7 + 0.2);

        function hexToRgba(hex, alpha) {{
            const r = parseInt(hex.slice(1,3),16);
            const g = parseInt(hex.slice(3,5),16);
            const b = parseInt(hex.slice(5,7),16);
            return `rgba(${{r}},${{g}},${{b}},${{alpha}})`;
        }}

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const glow = ctx.createRadialGradient(cx, cy, baseRadius*0.6, cx, cy, baseRadius*1.35);
            glow.addColorStop(0, hexToRgba(color, 0.18));
            glow.addColorStop(1, hexToRgba(color, 0));
            ctx.fillStyle = glow;
            ctx.beginPath();
            ctx.arc(cx, cy, baseRadius*1.35, 0, Math.PI*2);
            ctx.fill();

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

            ctx.fillStyle = "{Theme.TEXT_PRIMARY}";
            ctx.font = "bold 18px Orbitron, sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("JOHNNY TEC", cx, cy - 2);

            ctx.fillStyle = color;
            ctx.font = "10px 'Share Tech Mono', monospace";
            ctx.fillText("[ " + stateLabel + " ]", cx, cy + 19);

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
    f"I'm afraid I didn't catch that directive, {USER_TITLE}.",
    "That command fell outside my current parameters. Try again?",
    "Signal received, but the instruction set was incomplete.",
    f"I'm going to need a bit more clarity on that one, {USER_TITLE}.",
]


def cmd_system_check(text, match):
    latency = round(random.uniform(0.01, 0.09), 3)
    integrity = random.randint(96, 100)
    update_metric("latency", f"{latency}ms")
    update_metric("integrity", f"{integrity}%")
    update_metric("status", "ONLINE")
    log_event("Running full neural diagnostic sweep...", "CMD", Theme.PURPLE_BRIGHT)
    response = (
        f"System check complete, {USER_TITLE}. All subsystems nominal. "
        f"Neural integrity at {integrity} percent, latency holding at {latency} milliseconds."
    )
    return response, "system_check", None


def cmd_search_web(text, match):
    query = match.group(2).strip() if match and match.lastindex and match.lastindex >= 2 else text
    if not query:
        return f"I need something to search for, {USER_TITLE}.", "search_web", None
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    log_event(f"Launching web search for '{query}'", "NET", Theme.CYAN)
    return f"Searching the web for {query}, {USER_TITLE}.", "search_web", url


def cmd_open_browser(text, match):
    log_event("Opening default search engine.", "NET", Theme.CYAN)
    return f"Browser interface online, {USER_TITLE}.", "open_browser", "https://www.google.com"


def cmd_show_map(text, match):
    groups = match.groups() if match else ()
    location = groups[-1].strip() if groups and groups[-1] else "current location"
    url = "https://www.google.com/maps/search/" + urllib.parse.quote_plus(location)
    log_event(f"Pulling cartographic data for '{location}'", "NAV", Theme.PURPLE_BRIGHT)
    return f"Displaying map coordinates for {location}, {USER_TITLE}.", "show_map", url


def cmd_time_date(text, match):
    now = datetime.now()
    time_str = now.strftime("%I:%M %p").lstrip("0")
    date_str = now.strftime("%A, %B %d, %Y")
    log_event(f"Temporal sync: {time_str} — {date_str}", "SYS", Theme.CYAN)
    return f"Temporal scan complete. It is currently {time_str}, on {date_str}, {USER_TITLE}.", "time_date", None


def cmd_clear_logs(text, match):
    st.session_state.logs = []
    log_event("Log matrix cleared and reinitialized.", "SYS", Theme.AMBER_WARN)
    update_metric("status", "MATRIX RESET")
    return f"Dashboard logs cleared and matrix reinitialized, {USER_TITLE}.", "clear_logs", None


def cmd_introduce(text, match):
    return (
        f"I am JOHNNY TEC, an autonomous neural interface running in your browser, "
        f"built to serve you, {USER_TITLE}.",
        "introduce", None
    )


def cmd_joke(text, match):
    jokes = [
        f"Why do programmers prefer dark mode? Because light attracts bugs, {USER_TITLE}.",
        "I would tell you a UDP joke, but you might not get it.",
        f"There are only 10 types of people, {USER_TITLE}: those who understand binary and those who don't.",
    ]
    return random.choice(jokes), "joke", None


def cmd_greeting(text, match):
    return random.choice(WELCOME_MESSAGES), "greeting", None


def cmd_shutdown(text, match):
    log_event("Shutdown directive received. Standing by.", "SYS", Theme.AMBER_WARN)
    return f"Powering down active listeners, {USER_TITLE}. Standing by.", "shutdown", None


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
#  SECTION 7 — SIDEBAR (all text/metrics/logs live here)
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


def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="jt-sidebar-title">◆ JOHNNY TEC MATRIX ◆</div>', unsafe_allow_html=True)
        st.caption(datetime.now().strftime("%A, %d %B %Y — %H:%M:%S"))
        st.markdown("---")

        render_panel("SYSTEM STATUS", [
            ("STATUS", st.session_state.metrics["status"]),
            ("ENGINE", st.session_state.metrics["engine"]),
            ("INTEGRITY", st.session_state.metrics["integrity"]),
        ])
        render_panel("AUDIO INPUT", [
            ("INPUT", st.session_state.metrics["audio_state"]),
            ("RECOGNIZER", st.session_state.metrics["recognizer"]),
        ])
        render_panel("LINK METRICS", [
            ("LATENCY", st.session_state.metrics["latency"]),
            ("BANDWIDTH", "STABLE"),
        ])
        render_panel("LAST COMMAND", [
            ("DIRECTIVE", st.session_state.metrics["last_cmd"]),
            ("ACTION", st.session_state.metrics["last_action"]),
        ])

        st.markdown('<div class="jt-panel-title">◈ QUICK COMMANDS</div>', unsafe_allow_html=True)
        qc1, qc2, qc3 = st.columns(3)
        with qc1:
            if st.button("⚙ CHECK", use_container_width=True, key="qc_check"):
                dispatch_text("system check")
                st.rerun()
        with qc2:
            if st.button("🕐 TIME", use_container_width=True, key="qc_time"):
                dispatch_text("time and date")
                st.rerun()
        with qc3:
            if st.button("⟲ CLEAR", use_container_width=True, key="qc_clear"):
                dispatch_text("clear logs")
                st.rerun()

        st.markdown('<div class="jt-panel-title" style="margin-top:10px;">◈ SYSTEM LOG FEED</div>', unsafe_allow_html=True)
        render_console()

        st.markdown("---")
        st.caption(
            "Tap the mic once to wake JOHNNY TEC. Chrome or Edge recommended "
            "for continuous browser speech recognition."
        )


# =============================================================================
#  SECTION 8 — DISPATCH + URL HANDLING
# =============================================================================

def open_url_in_new_tab(url: str):
    safe_url = url.replace('"', '%22')
    components.html(f'<script>window.open("{safe_url}", "_blank");</script>', height=0)


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

    # Return to a listening-ready state so the mic keeps going without
    # requiring the user to press the button again.
    set_state("LISTENING")
    update_metric("audio_state", "LISTENING")


# =============================================================================
#  SECTION 9 — MAIN SCREEN (visual-only: HUD + mic, nothing else)
# =============================================================================

def render_main_screen():
    render_visualizer(st.session_state.assistant_state)

    spacer_l, mic_col, spacer_r = st.columns([2, 1, 2])
    with mic_col:
        if speech_to_text is None:
            st.error("Run: pip install streamlit-mic-recorder")
            return

        heard = speech_to_text(
            language="en",
            start_prompt="🎙️",
            stop_prompt="⏹️",
            just_once=False,
            use_container_width=True,
            key="jt_mic",
        )

        if not st.session_state.engaged and heard is None:
            # First render before any interaction — nothing to do yet.
            pass

        if heard and heard != st.session_state.last_heard:
            st.session_state.last_heard = heard
            st.session_state.engaged = True

            if not st.session_state.greeted:
                st.session_state.greeted = True
                update_metric("audio_state", "LISTENING")
                welcome = random.choice(WELCOME_MESSAGES)
                log_event(welcome, "AI", Theme.PURPLE_BRIGHT)
                set_state("SPEAKING")
                speak_in_browser(welcome)
                set_state("LISTENING")
            else:
                update_metric("audio_state", "PROCESSING")
                dispatch_text(heard)


# =============================================================================
#  SECTION 10 — APP ENTRY POINT
# =============================================================================

def main():
    configure_page()
    inject_global_css()
    init_session_state()

    render_sidebar()
    render_main_screen()


if __name__ == "__main__":
    main()
