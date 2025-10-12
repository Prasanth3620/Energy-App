import streamlit as st
import requests
import pandas as pd
import google.generativeai as genai
import re

# ================================================
# Streamlit Page Setup
# ================================================
st.set_page_config(
    page_title="⚡ Energy Vision",
    layout="wide",
)

# -----------------------------
# CSS Styling Section
# -----------------------------
st.markdown("""
    <style>
    /* ---------------- Page Base ---------------- */
    body, .stApp {
        background: radial-gradient(circle at top left, #0f2027, #203a43, #2c5364);
        color: white;
    }

    /* ---------------- Title Styling ---------------- */
    h1 {
        text-align: center;
        font-size: 48px !important;
        background: linear-gradient(90deg, #00e6ff, #ff00ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    h2 {
        text-align: center;
        font-size: 24px !important;
        color: #a0f0ff;
        margin-top: -5px;
        margin-bottom: 40px;
    }

    /* ---------------- Button Styling ---------------- */
    div.stButton > button {
        background: linear-gradient(90deg, #00ffff, #0077ff);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6em 1.2em;
        font-size: 16px;
        transition: 0.3s ease-in-out;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
        background: linear-gradient(90deg, #0077ff, #00ffff);
        box-shadow: 0 0 15px #00ffff;
    }

    /* ---------------- Card (App Containers) ---------------- */
    .app-card {
        background: linear-gradient(145deg, rgba(0, 255, 255, 0.2), rgba(255, 0, 255, 0.2));
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 0 25px rgba(0, 255, 255, 0.3);
        transition: 0.4s ease-in-out;
    }
    .app-card:hover {
        box-shadow: 0 0 45px rgba(0, 255, 255, 0.6);
        transform: translateY(-5px);
    }

    /* ---------------- Streamlit Layout Tweaks ---------------- */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    /* ---------------- Metric Box ---------------- */
    div[data-testid="stMetricValue"] {
        color: #00ffff;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)



# -----------------------------------------
# Custom CSS for Premium Aesthetic Styling
# -----------------------------------------
st.markdown("""
<style>
/* ---------------------------
   GLOBAL BACKGROUND & FONTS
----------------------------*/
html, body, [class*="st-"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background: radial-gradient(circle at top left, #0A0C15, #05070E 70%);
    color: #E8EDF2;
    scroll-behavior: smooth;
}

/* ---------------------------
   HEADER SECTION
----------------------------*/
.main-title {
    font-size: 3.5em;
    font-weight: 800;
    background: linear-gradient(90deg, #00E0FF, #00FFB9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    letter-spacing: 1px;
    text-shadow: 0 0 15px rgba(0,255,255,0.3);
    margin-bottom: 0.2rem;
    animation: fadeDown 1.2s ease;
}
.subtitle {
    text-align: center;
    font-size: 1.4em;
    color: #AEBACF;
    margin-bottom: 4rem;
    font-weight: 400;
    letter-spacing: 0.5px;
    animation: fadeUp 1.2s ease;
}
.header-space {
    height: 80px;
}

/* ---------------------------
   SECTION HEADERS
----------------------------*/
.section-header {
    color: #00FFC6;
    font-size: 1.6em;
    font-weight: 600;
    letter-spacing: 0.3px;
    text-shadow: 0 0 10px rgba(0,255,198,0.4);
    margin-bottom: 1.2rem;
    position: relative;
}
.section-header::after {
    content: "";
    display: block;
    height: 3px;
    width: 50px;
    background: linear-gradient(90deg, #00E0FF, transparent);
    border-radius: 2px;
    margin-top: 6px;
}

/* ---------------------------
   CARDS (GLASSMORPHIC STYLE)
----------------------------*/
.info-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 18px;
    padding: 1.6rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(16px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.5);
    transition: all 0.4s ease;
}
.info-card:hover {
    box-shadow: 0 0 20px rgba(0,255,255,0.25);
    transform: translateY(-3px);
}

/* ---------------------------
   BUTTONS
----------------------------*/
div.stButton > button {
    background: linear-gradient(90deg, #00E0FF, #00C2A8);
    color: white !important;
    border: none;
    border-radius: 14px;
    padding: 0.7rem 1.5rem;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.4px;
    box-shadow: 0 0 15px rgba(0,224,255,0.2);
    transition: all 0.3s ease-in-out;
}
div.stButton > button:hover {
    background: linear-gradient(90deg, #00C2A8, #00E0FF);
    box-shadow: 0 0 25px rgba(0,224,255,0.4);
    transform: scale(1.04);
}

/* ---------------------------
   INPUTS
----------------------------*/
.stTextInput > div > div > input,
.stTextArea textarea {
    background: rgba(255,255,255,0.04) !important;
    color: #EAEAEA !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    transition: 0.3s ease;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: #00E0FF !important;
    box-shadow: 0 0 12px rgba(0,224,255,0.25);
}

/* ---------------------------
   DIVIDER
----------------------------*/
.divider {
    border-left: 2px solid rgba(255,255,255,0.1);
    height: 100%;
    margin: auto;
    animation: glowPulse 3s infinite ease-in-out;
}
@keyframes glowPulse {
    0%, 100% { box-shadow: 0 0 5px rgba(0,255,255,0.2); }
    50% { box-shadow: 0 0 20px rgba(0,255,255,0.5); }
}

/* ---------------------------
   REPORT CARDS
----------------------------*/
.report-card {
    border-radius: 16px;
    padding: 1.4rem;
    margin-bottom: 1.1rem;
    color: white;
    box-shadow: 0 5px 18px rgba(0,0,0,0.4);
    transition: 0.3s ease;
}
.report-card:hover {
    transform: translateY(-2px);
}

/* ---------------------------
   ANIMATIONS
----------------------------*/
@keyframes fadeDown { from {opacity: 0; transform: translateY(-20px);} to {opacity:1; transform: translateY(0);} }
@keyframes fadeUp { from {opacity: 0; transform: translateY(20px);} to {opacity:1; transform: translateY(0);} }
</style>
""", unsafe_allow_html=True)

# ================================================
# HEADER
# ================================================
st.markdown("<h1 class='main-title'>⚡ Energy Vision</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='subtitle'>Your Personal Energy & Appliance Consultant</h3>", unsafe_allow_html=True)
st.markdown("<div class='header-space'></div>", unsafe_allow_html=True)

# Create two sections side by side
left_col, divider_col, right_col = st.columns([1, 0.05, 1])

# ====================================================
# LEFT SIDE → ENERGY INSIGHTS
# ====================================================
with left_col:
    st.markdown("<h3 class='section-header'>🌞 Today's Energy Insight</h3>", unsafe_allow_html=True)

    @st.cache_data
    def load_tips():
        return pd.read_excel("energy_tips_with_alert3.xlsx")

    df = load_tips()

    def fetch_weather_from_pincode(pincode: str):
        geo_url = "https://nominatim.openstreetmap.org/search"
        g = requests.get(
            geo_url,
            params={"postalcode": pincode, "countrycodes": "IN", "format": "json", "limit": 1},
            headers={"User-Agent": "energyvision-app"},
            timeout=15
        )
        g.raise_for_status()
        data = g.json()
        if not data:
            raise ValueError("Invalid PIN code or no data found.")
        loc = data[0]
        lat, lon = float(loc["lat"]), float(loc["lon"])
        display_name = loc.get("display_name", "Unknown")

        wx_url = "https://api.open-meteo.com/v1/forecast"
        r = requests.get(wx_url, params={
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "temperature_2m,relative_humidity_2m"
        }, timeout=10)
        r.raise_for_status()
        wx = r.json()
        temp = wx["current_weather"]["temperature"]
        humidity = wx["hourly"]["relative_humidity_2m"][0]
        return {"temp_c": temp, "humidity": humidity, "place": display_name}

    def match_prompt(forecast, df):
        df_temp = df.copy()
        df_temp["distance"] = ((df_temp["Temperature (°C)"] - forecast["temp_c"])**2 +
                               (df_temp["Humidity (%)"] - forecast["humidity"])**2) ** 0.5
        return df_temp.loc[df_temp["distance"].idxmin()]

    pincode = st.text_input("Enter your PIN Code", placeholder="e.g. 560001")
    if st.button("🔍 Get Today's Insights", use_container_width=True):
        if not pincode:
            st.warning("Please enter a valid PIN code.")
        else:
            try:
                forecast = fetch_weather_from_pincode(pincode)
                st.markdown(f"""
                    <div class='info-card'>
                        <b>📍 Location:</b> {forecast['place']}<br>
                        🌡️ <b>Temperature:</b> {forecast['temp_c']}°C<br>
                        💧 <b>Humidity:</b> {forecast['humidity']}%
                    </div>
                """, unsafe_allow_html=True)

                row = match_prompt(forecast, df)
                st.markdown("<div class='info-card'><b>💡 Energy Tips:</b></div>", unsafe_allow_html=True)
                st.success(f"🔹 {row['Alert 1']}")
                st.info(f"🔹 {row['Alert 2']}")
                st.info(f"🔹 {row['Alert 3']}")
            except Exception as e:
                st.error(f"❌ {e}")

# ====================================================
# DIVIDER
# ====================================================
with divider_col:
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ====================================================
# RIGHT SIDE → APPLIANCE DIAGNOSTIC
# ====================================================
with right_col:
    st.markdown("<h3 class='section-header'>🔧 Appliance Diagnostic Assistant</h3>", unsafe_allow_html=True)
    st.markdown("Get instant AI-powered troubleshooting insights for your appliance issues.")

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    with st.form("diagnostic_form"):
        model_name = st.text_input("Appliance Model Number", placeholder="e.g. LG T70SPSF2Z, Mi L32M6-RA")
        issue = st.text_area("Describe the Issue", placeholder="e.g. No display, beeping noise...")
        display_error = st.text_input("Error Code (Optional)", placeholder="e.g. E4, F07, etc.")
        submitted = st.form_submit_button("🩺 Diagnose", use_container_width=True)

    if submitted:
        if not model_name or not issue:
            st.warning("Please fill in the required fields.")
        else:
            with st.spinner("Analyzing the issue..."):
                prompt = f"""
You are an expert appliance diagnostic assistant.
Model: {model_name}
Issue: {issue}
Error Code: {display_error or 'None'}

Provide:
🔹 Quick Checks
🔹 Customer Care Number
🔹 Probable Causes & Estimated Costs (Markdown table)
🔹 Turnaround Time
"""
                try:
                    model = genai.GenerativeModel("gemini-2.5-flash-lite")
                    res = model.generate_content(prompt)
                    text = res.text

                    st.markdown("<div class='info-card'><h4>✅ Diagnosis Report</h4></div>", unsafe_allow_html=True)
                    sections = re.split(r'(?=🔹)', text)
                    gradients = [
                        "linear-gradient(135deg,#007ACC,#001E3A)",
                        "linear-gradient(135deg,#00B3A4,#003333)",
                        "linear-gradient(135deg,#00E0FF,#004A66)",
                        "linear-gradient(135deg,#008B8B,#003030)"
                    ]
                    for i, sec in enumerate(sections):
                        sec_html = re.sub(r'^\s*[-*]\s+', '• ', sec.strip(), flags=re.MULTILINE)
                        st.markdown(
                            f"<div class='report-card' style='background:{gradients[i % len(gradients)]}'>{sec_html}</div>",
                            unsafe_allow_html=True
                        )
                except Exception as e:
                    st.error(f"❌ {e}")
