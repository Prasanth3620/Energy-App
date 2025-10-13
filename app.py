import streamlit as st
import requests
import pandas as pd
import google.generativeai as genai
import re

# ======================================================
# Streamlit Page Setup
# ======================================================
st.set_page_config(page_title="⚡ Energy Vision", layout="wide")

# ======================================================
# CLEAN SMART-HOME DASHBOARD THEME (Light UI)
# ======================================================
st.markdown("""
<style>

/* ---------- PAGE BACKGROUND ---------- */
body {
    font-family: 'Segoe UI', sans-serif;
    background: linear-gradient(to bottom, #F7F9FB, #FFFFFF);
    color: #1A1A1A;
}

/* Remove default padding */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* ---------- HEADER ---------- */
.main-title {
    text-align: center;
    font-weight: 600;
    color: #0078D4;
    font-size: 2.4rem;
    margin-bottom: 0.3rem;
}
.subtitle {
    text-align: center;
    color: #5E6A76;
    font-size: 1.1rem;
    margin-bottom: 2.5rem;
}

/* ---------- SECTION HEADERS ---------- */
.section-header {
    color: #0078D4;
    font-weight: 600;
    font-size: 1.3rem;
    margin-bottom: 1rem;
}

/* ---------- CARD STYLE ---------- */
.info-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid #E5E7EB;
    box-shadow: 0px 3px 8px rgba(0,0,0,0.05);
    transition: all 0.2s ease-in-out;
}
.info-card:hover {
    box-shadow: 0px 5px 12px rgba(0,0,0,0.08);
}

/* ---------- DIVIDER ---------- */
.divider {
    border-left: 1.5px solid #E5E7EB;
    height: 100%;
    margin: auto;
}

/* ---------- BUTTONS ---------- */
div.stButton > button {
    background-color: #0078D4 !important;
    color: white !important;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    box-shadow: 0 2px 6px rgba(0,120,212,0.25);
    transition: all 0.2s ease-in-out;
}
div.stButton > button:hover {
    background-color: #008AED !important;
    transform: scale(1.02);
}

/* ---------- SUCCESS / INFO BOXES ---------- */
.stSuccess, .stInfo, .stWarning {
    border-radius: 10px !important;
    background-color: #F9FAFB !important;
    color: #1A1A1A !important;
}

/* ---------- FORM FIELDS ---------- */
input, textarea {
    border-radius: 8px !important;
    border: 1px solid #D1D5DB !important;
}

/* ---------- DIAGNOSIS CARDS ---------- */
.diagnosis-card {
    background-color: #FFFFFF;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 3px 6px rgba(0,0,0,0.05);
    border: 1px solid #E5E7EB;
}

/* ---------- LIGHT ICONS COLORS ---------- */
.blue-text { color: #0078D4; }
.orange-text { color: #F57C00; }
.gray-text { color: #6B7280; }

</style>
""", unsafe_allow_html=True)

# ======================================================
# HEADER
# ======================================================
st.markdown("<h1 class='main-title'>⚡ Energy Vision</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='subtitle'>Your Personal Energy & Appliance Consultant</h3>", unsafe_allow_html=True)

# ======================================================
# LAYOUT: TWO COLUMNS
# ======================================================
left_col, divider_col, right_col = st.columns([1, 0.05, 1])

# ======================================================
# LEFT: ENERGY INSIGHTS
# ======================================================
with left_col:
    st.markdown("<h3 class='section-header'>🌞 Today's Energy Saving Tip</h3>", unsafe_allow_html=True)

    @st.cache_data
    def load_tips():
        return pd.read_excel("energy_tips_with_alert3.xlsx")

    df = load_tips()

    def fetch_weather_from_pincode(pincode: str):
        geo_url = "https://nominatim.openstreetmap.org/search"
        g = requests.get(
            geo_url,
            params={"postalcode": pincode, "countrycodes": "IN", "format": "json", "limit": 1},
            headers={"User-Agent": "streamlit-weather-app"},
            timeout=20
        )
        g.raise_for_status()
        gdata = g.json()
        if not gdata:
            raise ValueError(f"No location found for PIN code {pincode}")
        loc = gdata[0]
        lat, lon = float(loc["lat"]), float(loc["lon"])
        display_name = loc.get("display_name", "Unknown Location")

        wx_url = "https://api.open-meteo.com/v1/forecast"
        r = requests.get(wx_url, params={
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "temperature_2m,relative_humidity_2m"
        }, timeout=10)
        r.raise_for_status()
        data = r.json()
        temp = data.get("current_weather", {}).get("temperature")
        humidity = None
        if "hourly" in data and "relative_humidity_2m" in data["hourly"]:
            humidity = data["hourly"]["relative_humidity_2m"][0]
        return {"temp_c": temp, "humidity": humidity, "place": display_name}

    def match_prompt(forecast, df):
        temp, hum = forecast["temp_c"], forecast["humidity"]
        if temp is None or hum is None:
            return None
        df_temp = df.copy()
        df_temp["distance"] = ((df_temp["Temperature (°C)"] - temp)**2 + (df_temp["Humidity (%)"] - hum)**2) ** 0.5
        return df_temp.loc[df_temp["distance"].idxmin()]

    with st.container():
        pincode = st.text_input("Enter your PIN Code", placeholder="e.g. 560001")
        if st.button("🔍 Get Today's Insights", use_container_width=True):
            if not pincode:
                st.error("Please enter a valid PIN code.")
            else:
                try:
                    forecast = fetch_weather_from_pincode(pincode)
                    st.markdown(
                        f"""
                        <div class='info-card'>
                        <span class='gray-text'><b>📍 Location:</b> {forecast['place']}</span><br>
                        🌡️ <b>{forecast['temp_c']}°C</b> | 💧 <b>{forecast['humidity']}%</b>
                        </div>
                        """, unsafe_allow_html=True
                    )

                    row = match_prompt(forecast, df)
                    if row is not None:
                        st.markdown("<div class='info-card'><b>💡 Energy Tips</b></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='diagnosis-card blue-text'>🔹 {row['Alert 1']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='diagnosis-card gray-text'>🔹 {row['Alert 2']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='diagnosis-card gray-text'>🔹 {row['Alert 3']}</div>", unsafe_allow_html=True)
                    else:
                        st.warning("No matching condition found.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ======================================================
# DIVIDER
# ======================================================
with divider_col:
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ======================================================
# RIGHT: APPLIANCE DIAGNOSTIC
# ======================================================
with right_col:
    st.markdown("<h3 class='section-header'>🔧 Appliance Diagnostic Assistant</h3>", unsafe_allow_html=True)
    st.markdown("Describe the issue to get quick troubleshooting guidance.", unsafe_allow_html=True)

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    with st.form("diagnostic_form"):
        model_name = st.text_input("Appliance Model Number", placeholder="e.g. LG T70SPSF2Z, Mi L32M6-RA")
        issue = st.text_area("Describe the Issue", placeholder="e.g. No display, making noise...")
        display_error = st.text_input("Error Code (Optional)", placeholder="e.g. E4, F07, etc.")
        submitted = st.form_submit_button("🩺 Diagnose", use_container_width=True)

    if submitted:
        if not model_name or not issue:
            st.warning("Please fill in the required fields.")
        else:
            with st.spinner("Analyzing the issue..."):
                prompt = f"""
You are an intelligent appliance diagnostic assistant.
Model: {model_name}
Issue: {issue}
Error Code: {display_error or 'Not provided'}

Generate 4 sections:
🔹 Quick Checks / Self-Diagnosis
🔹 Customer Care Number
🔹 Probable Causes & Estimated Costs
🔹 Turnaround Time (TAT)
"""
                try:
                    model = genai.GenerativeModel("gemini-2.5-flash-lite")
                    response = model.generate_content(prompt)
                    text = response.text
                    st.markdown("<div class='info-card'><h4>✅ Diagnosis Report</h4></div>", unsafe_allow_html=True)
                    for sec in re.split(r'(?=🔹)', text):
                        sec = sec.strip()
                        if sec:
                            st.markdown(f"<div class='diagnosis-card'>{sec}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
