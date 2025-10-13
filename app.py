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
# Modern Light Theme CSS
# -----------------------------------------
st.markdown(
    """
    <style>
    /* ----------- General Page ----------- */
    body {
        font-family: 'Segoe UI', sans-serif;
        background-color: #F5F7FA;
        color: #1A1A1A;
    }

    /* Remove Streamlit default padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* ----------- Header ----------- */
    .main-title {
        color: #0078D7;
        text-align: center;
        font-size: 2.6em;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #6B7280;
        text-align: center;
        font-size: 1.2em;
        margin-bottom: 2rem;
    }

    /* ----------- Section Headers ----------- */
    .section-header {
        color: #0078D7;
        font-size: 1.4em;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    /* ----------- Card Design ----------- */
    .info-card {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        border: 1px solid #E5E7EB;
    }

    /* Card hover */
    .info-card:hover {
        box-shadow: 0 4px 16px rgba(0,120,215,0.15);
        transition: all 0.2s ease-in-out;
    }

    /* ----------- Divider ----------- */
    .divider {
        border-left: 2px solid #E5E7EB;
        height: 100%;
        margin: auto;
    }

    /* ----------- Buttons ----------- */
    div.stButton > button {
        background: linear-gradient(90deg, #0078D7, #0094FF);
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        box-shadow: 0 3px 8px rgba(0,120,215,0.25);
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #0094FF, #00B7FF);
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0,120,215,0.3);
    }

    /* ----------- Diagnosis Cards ----------- */
    .diagnosis-card {
        border-radius: 14px;
        padding: 1.2rem;
        background: linear-gradient(180deg, #F8FAFC, #FFFFFF);
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }

    /* Scrollable area fix */
    [data-testid="stVerticalBlock"] {
        gap: 1rem !important;
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
                        <b>📍 Location:</b> {forecast['place']}<br>
                        🌡️ <b>Temperature:</b> {forecast['temp_c']}°C<br>
                        💧 <b>Humidity:</b> {forecast['humidity']}%
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
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
        model_name = st.text_input("Appliance Model Number", placeholder="e.g. LG T70SPSF2Z, Mi L32M6-RA ")
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
Model Number: {model_name}
Issue: {issue}
Error Code: {display_error or 'Not provided'}

Tasks:
1. Identify the **appliance brand** (e.g., LG, Samsung, Mi, Whirlpool, etc.) and **type** (e.g., TV, Washing Machine, Refrigerator, AC) from the model number.
2. Then generate a short, clean, and aesthetic diagnostic report with **four clearly separated sections** as follows:
 
   🔹 Quick Checks / Self-Diagnosis  
   • Give 2–3 simple user-level checks to perform before calling a technician.
 
   🔹 Customer Care Number  
   • Give the official customer care helpline number for the brand.
 
   🔹 Probable Causes & Estimated Costs  
   • Mention 2–3 possible technical causes (just name them, no explanations).  
   • Add approximate cost range in INR for each cause.  
   • Present this section **strictly as a clean 2-column table** —  
     Column 1: “Probable Cause”  
     Column 2: “Estimated Cost (INR Range)”.  
   • Do not include markdown symbols like |, *, or #.  
   • Use simple spacing to make it look like a neat table.
 
   🔹 Turnaround Time (TAT)  
   • Mention the realistic average service time in days.
 
Formatting Instructions:
- Each section heading should start with a blue diamond (🔹).
- Each point should start with a small black dot (•) except inside the table.
- Keep response short, well-structured, and visually clean.
- Avoid unnecessary text or explanations.
"""
                try:
                    model = genai.GenerativeModel("gemini-2.5-flash-lite")
                    response = model.generate_content(prompt)
                    text = response.text

                    st.markdown("<div class='info-card'><h4>✅ Diagnosis Report</h4></div>", unsafe_allow_html=True)
                    sections = re.split(r'(?=🔹)', text)

                    for sec in sections:
                        sec = sec.strip()
                        if sec:
                            st.markdown(f"<div class='diagnosis-card'>{sec}</div>", unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error: {e}")
