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

# -----------------------------------------
# Custom CSS for styling
# -----------------------------------------
st.markdown(
    """
    <style>
    /* General App Styling */
    body {
        font-family: 'Segoe UI', sans-serif;
    }

    /* Header */
    .main-title {
        color: #00E0FF;
        text-align: center;
        font-size: 3em;
        font-weight: 700;
        text-shadow: 1px 1px 10px rgba(0,255,255,0.3);
        margin-bottom: 0.3rem;
    }

    .subtitle {
        color: #A9B7C6;
        text-align: center;
        font-size: 1.3em;
        margin-bottom: 3rem;
    }

    /* Section Headers */
    .section-header {
        color: #00C896;
        font-size: 1.6em;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    /* Info Cards */
    .info-card {
        background: linear-gradient(135deg, #1B1F2A, #10131A);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }

    /* Divider Line */
    .divider {
        border-left: 2px solid rgba(255,255,255,0.2);
        height: 100%;
        margin: auto;
        animation: fadeIn 1.5s ease-in-out;
    }

    /* Animated subtle glow */
    @keyframes fadeIn {
        from { opacity: 0; transform: scaleY(0.8); }
        to { opacity: 1; transform: scaleY(1); }
    }

    /* Buttons */
    div.stButton > button {
        background-color: #00C2A8 !important;
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #00E0FF !important;
        transform: scale(1.02);
    }

    /* Success & Info Blocks */
    .stSuccess, .stInfo {
        border-radius: 10px !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ================================================
# HEADER
# ================================================
st.markdown("<h1 class='main-title'>⚡ Energy Vision</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='subtitle'>Your Personal Energy & Appliance Consultant</h3>", unsafe_allow_html=True)

# Create two sections side by side
left_col, divider_col, right_col = st.columns([1, 0.05, 1])

# ====================================================
# LEFT SIDE → ENERGY INSIGHTS
# ====================================================
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
            params={
                "postalcode": pincode,
                "countrycodes": "IN",
                "format": "json",
                "limit": 1
            },
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
                    st.markdown(f"<div class='info-card'><b>📍 Location:</b> {forecast['place']}<br>🌡️ <b>Temperature:</b> {forecast['temp_c']}°C<br>💧 <b>Humidity:</b> {forecast['humidity']}%</div>", unsafe_allow_html=True)
                    row = match_prompt(forecast, df)
                    if row is not None:
                        st.markdown("<div class='info-card'><b>💡 Energy Tips:</b></div>", unsafe_allow_html=True)
                        st.success(f"🔹 {row['Alert 1']}")
                        st.info(f"🔹 {row['Alert 2']}")
                        st.info(f"🔹 {row['Alert 3']}")
                    else:
                        st.warning("No matching condition found in the tips sheet.")
                except Exception as e:
                    st.error(f"Error: {e}")

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
    st.markdown("Describe the issue to get quick troubleshooting guidance.")

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    with st.form("diagnostic_form"):
        model_name = st.text_input("Appliance Model Number", placeholder="e.g. LG T70SPSF2Z, Mi L32M6-RA, Samsung WA62M4100HY")
        issue = st.text_area("Describe the Issue", placeholder="e.g. No display, not cooling, making noise...")
        display_error = st.text_input("Error Code (Optional)", placeholder="e.g. E4, F07, etc.")
        submitted = st.form_submit_button("🩺 Diagnose", use_container_width=True)

    if submitted:
        if not model_name or not issue:
            st.warning("Please fill in the required fields.")
        else:
            with st.spinner("Analyzing the issue..."):
                prompt = f"""
You are an intelligent appliance diagnostic assistant.
Model Number: {model_name}
Issue: {issue}
Error Code: {display_error or 'Not provided'}

Generate a diagnostic report with:
🔹 Quick Checks / Self-Diagnosis (2-3 bullet points)
🔹 Customer Care Number
🔹 Probable Causes & Estimated Costs (Markdown table)
🔹 Turnaround Time (TAT)
"""

                try:
                    model = genai.GenerativeModel("gemini-2.5-flash-lite")
                    response = model.generate_content(prompt)
                    text = response.text

                    st.markdown("<div class='info-card'><h4>✅ Diagnosis Report</h4></div>", unsafe_allow_html=True)
                    sections = re.split(r'(?=🔹)', text)
                    colors = ["#007ACC", "#008CBA", "#006C77", "#005577"]

                    for i, sec in enumerate(sections):
                        sec = sec.strip()
                        if sec:
                            sec_html = re.sub(r'^\s*[-*]\s+', '• ', sec, flags=re.MULTILINE)
                            sec_html = sec_html.replace('\n', '<br>')
                            st.markdown(
                                f"""
                                <div style="
                                    background-color:{colors[i % len(colors)]};
                                    color:#FFFFFF;
                                    padding:1.2rem;
                                    border-radius:12px;
                                    margin-bottom:1rem;
                                    box-shadow: 0 0 15px rgba(0,0,0,0.3);
                                ">
                                {sec_html}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                except Exception as e:
                    st.error(f"❌ Error: {e}")
