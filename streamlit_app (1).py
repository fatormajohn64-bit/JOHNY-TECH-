import os
import time
from datetime import datetime
import streamlit as st
from groq import Groq
from streamlit_mic_recorder import speech_to_text

# ====================================================================
# 1. PAGE CONFIGURATION & SCI-FI CYBER MATRIX THEME (QSS/CSS)
# ====================================================================
st.set_page_config(
    page_title="JOHNNY TEC — COGNITIVE AUDIO MATRIX",
    page_icon="🌌",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Deep obsidian, electric cyan, and neon purple matrix styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap');
    
    /* Global App Background */
    .stApp {
        background-color: #0B0C10;
        color: #C5C6C7;
        font-family: 'Share Tech Mono', monospace;
    }
    
    /* Central Glowing HUD Ring Animation */
    .hud-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 30px 0;
        position: relative;
    }
    
    .hud-circle {
        width: 260px;
        height: 260px;
        border-radius: 50%;
        border: 4px dashed #66FCF1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        position: relative;
        box-shadow: 0 0 35px rgba(102, 252, 241, 0.3), inset 0 0 35px rgba(102, 252, 241, 0.2);
        animation: rotateRing 25s linear infinite;
    }
    
    .hud-inner-core {
        position: absolute;
        width: 190px;
        height: 190px;
        border-radius: 50%;
        border: 2px double #833AB4;
        box-shadow: 0 0 20px rgba(131, 58, 180, 0.4);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle, rgba(102,252,241,0.15) 0%, rgba(11,12,16,0.8) 70%);
    }

    .hud-text-brand {
        font-family: 'Orbitron', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: #FFFFFF;
        text-shadow: 0 0 10px #66FCF1;
        letter-spacing: 2px;
        margin: 0;
    }
    
    .hud-status-sub {
        font-size: 12px;
        color: #66FCF1;
        letter-spacing: 3px;
        margin-top: 5px;
        text-transform: uppercase;
    }
    
    @keyframes rotateRing {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Sci-Fi Directive Label */
    .directive-label {
        text-align: center;
        color: #45A29E;
        font-size: 14px;
        letter-spacing: 2px;
        margin-bottom: 25px;
    }
    
    /* Metrics Board Layout */
    .metric-box {
        background-color: rgba(31, 40, 51, 0.4);
        border: 1px solid #1F2833;
        border-left: 4px solid #833AB4;
        padding: 15px;
        border-radius: 4px;
        margin-top: 20px;
    }
    
    .metric-title {
        color: #833AB4;
        font-size: 12px;
        font-weight: bold;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }
    
    .metric-row {
        display: flex;
        justify-content: space-between;
        font-size: 14px;
        margin: 5px 0;
    }
    
    .metric-value-cyan {
        color: #66FCF1;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ====================================================================
# 2. INITIALIZE COGNITIVE DATA MATRIX & STATE
# ====================================================================
if "johnny_status" not in st.session_state:
    st.session_state.johnny_status = "IDLE"
if "terminal_logs" not in st.session_state:
    st.session_state.terminal_logs = ["[SYSTEM] Protocol 911 initialized. Neural Engine Active."]

# Securely bind the Groq client
@st.cache_resource
def init_groq_client():
    try:
        # Pulls directly from your secure Streamlit Secrets Vault
        api_key = st.secrets["GROQ_API_KEY"]
        return Groq(api_key=api_key)
    except Exception as e:
        st.error("Matrix Disconnected: Secure GROQ_API_KEY missing from Streamlit secrets.")
        return None

client = init_groq_client()

# ====================================================================
# 3. JOHNNY TEC INTERACTION LOGIC
# ====================================================================
def run_system_check():
    st.session_state.terminal_logs.append("[DIAGNOSTIC] Scan initiated: Core temperatures stable at 41°C.")
    st.session_state.terminal_logs.append("[DIAGNOSTIC] Synaptic link paths clear. Security parameters locked.")

def process_voice_directive(prompt_text):
    if not client:
        return "System error: Cognition core missing API credentials."
    
    st.session_state.johnny_status = "PROCESSING"
    st.session_state.terminal_logs.append(f"[USER VOICE]: {prompt_text}")
    
    # Custom Jarvis persona alignment rules
    system_prompt = (
        "You are JOHNNY TEC, an advanced, elite, highly sophisticated AI assistant "
        "resembling J.A.R.V.I.S. from Iron Man. Your responses must be elegant, sharp, "
        "witty, and highly professional. Always address the user as 'Invincible 911' or 'Sir'. "
        "Keep answers crisp, precise, and tailored to cyber systems and developer environments."
    )
    
    try:
        # Triggering the fast Llama model via Groq API
        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text}
            ],
            max_tokens=250,
            temperature=0.7
        )
        response_text = chat_completion.choices[0].message.content
        st.session_state.terminal_logs.append(f"[JOHNNY TEC]: {response_text}")
        st.session_state.johnny_status = "SPEAKING"
        return response_text
    except Exception as e:
        error_msg = f"Neural bridge breakdown: {str(e)}"
        st.session_state.terminal_logs.append(f"[ERROR]: {error_msg}")
        return "I encountered a minor processing anomaly within my core mainframe, Sir."

# ====================================================================
# 4. RENDER UI LAYOUT (MATCHING THE HUD PRESET)
# ====================================================================

# Centered Animated Visualizer
status_label = "IDLE" if st.session_state.johnny_status == "IDLE" else st.session_state.johnny_status

st.markdown(f"""
<div class="hud-container">
    <div class="hud-circle">
        <div class="hud-inner-core">
            <h1 class="hud-text-brand">JOHNNY TEC</h1>
            <div class="hud-status-sub">[ {status_label} ]</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"<div class='directive-label'>[ {status_label} ] — AWAITING COGNITIVE INPUT...</div>", unsafe_allow_html=True)

# Audio Matrix Input Widget (No Typing Allowed)
st.markdown("<p style='text-align: center; color: #66FCF1; font-size:12px;'>👇 ENGAGE AUDIO TRANSLINK MODULE 👇</p>", unsafe_allow_html=True)

# Using speech_to_text from the plugin
voice_input = speech_to_text(
    language='en',
    start_prompt="🔴 INITIALIZE UPLINK WAVE",
    stop_prompt="⚡ TERMINATE RECORDING",
    just_once=True,
    use_container_width=True,
    key="johnny_matrix_mic"
)

# Trigger AI generation if voice input data is caught
if voice_input:
    ai_reply = process_voice_directive(voice_input)
    st.write(f"**Johnny Tec Direct Response:** {ai_reply}")
    # Automatically revert status back to IDLE after rendering response
    st.session_state.johnny_status = "IDLE"

st.markdown("---")

# Cyber HUD Matrix Interface Navigation
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⚙️ SYSTEM CHECK", use_container_width=True):
        run_system_check()
with col2:
    if st.button("🕒 TIME & DATE", use_container_width=True):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        st.session_state.terminal_logs.append(f"[SYSTEM] Current timeline index verified: {current_time}")
with col3:
    if st.button("🔄 CLEAR LOGS", use_container_width=True):
        st.session_state.terminal_logs = ["[SYSTEM] Log terminal data cleared. Matrix refreshed."]

# Diagnostic Feed Output Display
st.text_area("MATRIX DIALOG INTERFACE LOGS", value="\n".join(st.session_state.terminal_logs), height=150, disabled=True)

# Static Link Metrics Sidebar/Panel Container
st.markdown("""
<div class="metric-box">
    <div class="metric-title">❖ LINK METRICS</div>
    <div class="metric-row"><span>LATENCY</span><span class="metric-value-cyan">0.02ms</span></div>
    <div class="metric-row"><span>BANDWIDTH</span><span class="metric-value-cyan">STABLE</span></div>
    <div class="metric-row"><span>COGNITIVE ENGINE</span><span class="metric-value-cyan">LLAMA-3.3-GROQ</span></div>
</div>
""", unsafe_allow_html=True)
