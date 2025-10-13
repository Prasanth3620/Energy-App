import streamlit as st
import requests
import pandas as pd
import google.generativeai as genai
import re

# ================================================
# Streamlit Page Setup
# ================================================
st.set_page_config(
    page_title="Device Details",
    layout="centered"
)

# ================================================
# Custom CSS for Google-Nest-Like Look
# ================================================
st.markdown("""
    <style>
    /* -----------------------------
       GENERAL APP BACKGROUND
    ------------------------------ */
    html, body, [class*="stAppViewContainer"], [class*="main"] {
        background: linear-gradient(to bottom, #ffffff 0%, #dbe9f9 100%) !important;
        color: #333333;
        font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    }

    /* -----------------------------
       TITLE HEADER
    ------------------------------ */
    .app-header {
        text-align: center;
        font-size: 1.4rem;
        font-weight: 600;
        color: #1e3a8a;
        padding-top: 0.8rem;
    }

    /* -----------------------------
       SUB HEADER
    ------------------------------ */
    .sub-header {
        text-align: center;
        font-size: 1.1rem;
        color: #444;
        margin-bottom: 0.5rem;
    }

    /* -----------------------------
       CARD CONTAINERS
    ------------------------------ */
    .card {
        background: #ffffff;
        border-radius: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        padding: 1.5rem;
        text-align: center;
        margin: 1rem auto;
        width: 90%;
        max-width: 420px;
    }

    /* -----------------------------
       TEMPERATURE VALUES
    ------------------------------ */
    .temp {
        font-size: 3rem;
        font-weight: 500;
        color: #1e3a8a;
    }
    .unit {
        font-size: 1.2rem;
        vertical-align: super;
        color: #3b82f6;
    }

    /* -----------------------------
       LABELS AND TEXT
    ------------------------------ */
    .label {
        color: #666;
        font-size: 0.9rem;
        margin-top: -5px;
    }

    /* -----------------------------
       BUTTON STYLING
    ------------------------------ */
    div.stButton > button {
        background: #e6f0ff;
        color: #1e3a8a;
        border: none;
        border-radius: 15px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        font-size: 1rem;
        box-shadow: 0 3px 8px rgba(0,0,0,0.1);
        transition: all 0.2s ease-in-out;
    }

    div.stButton > button:hover {
        background: #3b82f6;
        color: white;
        transform: translateY(-2px);
    }

    /* -----------------------------
       ICON-LIKE BUTTON GROUPS
    ------------------------------ */
    .bottom-icons {
        display: flex;
        justify-content: space-around;
        margin-top: 1.5rem;
        color: #1e3a8a;
    }

    .icon-item {
        background: #f1f5ff;
        border-radius: 50%;
        width: 70px;
        height: 70px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 3px 8px rgba(0,0,0,0.1);
        font-size: 0.85rem;
        flex-direction: column;
    }

    .icon-item span {
        font-size: 0.7rem;
        color: #444;
        margin-top: 0.3rem;
    }

    </style>
""", unsafe_allow_html=True)

# ================================================
# UI Layout
# ================================================
st.markdown("<div class='app-header'>Device Details</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>1st Floor Thermostat</div>", unsafe_allow_html=True)

# Temperature display card
st.markdown("""
    <div class='card'>
        <div class='label'>Indoor</div>
        <div class='temp'>74<span class='unit'>°F</span></div>
        <hr style='border: 0.5px solid #e3e3e3; margin: 1rem 0;'>
        <div class='label'>Schedule</div>
        <div style='display: flex; justify-content: space-around; margin-top: 1rem;'>
            <div>
                <div class='label'>Heat to</div>
                <div class='temp' style='color:#f97316;'>65<span class='unit'>°F</span></div>
            </div>
            <div>
                <div class='label'>Cool to</div>
                <div class='temp' style='color:#2563eb;'>67<span class='unit'>°F</span></div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Buttons
col1, col2, col3 = st.columns(3)
with col2:
    st.button("Following Schedule")

# Icon-like info buttons
st.markdown("""
    <div class='bottom-icons'>
        <div class='icon-item'>
            <span>Mode</span>
            <strong>Auto</strong>
        </div>
        <div class='icon-item'>
            <span>Floor</span>
            <strong>67°F</strong>
        </div>
        <div class='icon-item'>
            <span>Humidity</span>
            <strong>54%</strong>
        </div>
        <div class='icon-item'>
            <span>Fan</span>
            <strong>Schedule</strong>
        </div>
    </div>
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
