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
st.markdown("""
<style>
/* --- Premium Dark UI (Tesla-inspired, enhanced) --- */
body, .stApp {
    background: linear-gradient(135deg, #0B0E13 0%, #101419 40%, #0F171C 100%);
    color: #E8EEF5;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* Header */
.main-title {
    color: #00D0FF;
    text-align: center;
    font-size: 3em;
    font-weight: 700;
    text-shadow: 0 2px 18px rgba(0, 208, 255, 0.4);
    margin-bottom: 0.2rem;
    letter-spacing: 0.5px;
}

.subtitle {
    color: #AAB5C2;
    text-align: center;
    font-size: 1.1em;
    margin-bottom: 2.2rem;
}

/* Section headers */
.section-header {
    color: #00B7FF;
    font-size: 1.5em;
    font-weight: 600;
    text-shadow: 0 0 10px rgba(0, 183, 255, 0.35);
    margin-top: 1rem;
}

/* Info cards */
.info-card {
    background: radial-gradient(circle at top left, #181E25 0%, #0F1418 90%);
    border-radius: 18px;
    padding: 1.4rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.65), inset 0 0 20px rgba(0, 208, 255, 0.04);
    transition: all 0.25s ease-in-out;
}
.info-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 208, 255, 0.1), inset 0 0 25px rgba(0, 208, 255, 0.06);
}

/* Buttons */
div.stButton > button {
    background: linear-gradient(135deg, #00B7FF, #007BFF);
    color: white !important;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    font-size: 1rem;
    padding: 0.7rem 1.3rem;
    box-shadow: 0 4px 15px rgba(0, 183, 255, 0.35);
    transition: all 0.25s ease-in-out;
}
div.stButton > button:hover {
    background: linear-gradient(135deg, #00D0FF, #00A9FF);
    transform: scale(1.05);
    box-shadow: 0 6px 20px rgba(0, 183, 255, 0.5);
}

/* Inputs */
.stTextInput > div > div > input, textarea {
    background: #151A20 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #E8EEF5 !important;
    box-shadow: inset 0 0 10px rgba(0,0,0,0.3);
    transition: all 0.2s ease;
}
.stTextInput > div > div > input:focus {
    border-color: #00B7FF !important;
    box-shadow: 0 0 10px rgba(0,183,255,0.3);
}

/* Status and containers */
.stSuccess, .stInfo, .stWarning {
    border-radius: 12px !important;
    padding: 0.9rem !important;
    background-color: #151A20 !important;
    border: 1px solid rgba(0,183,255,0.25) !important;
    color: #BFD8E8 !important;
}

/* Divider line */
.divider {
    border-left: 2px solid rgba(255,255,255,0.07);
    height: 100%;
    margin: auto;
}

/* Subtle glow animation for active sections */
@keyframes glowPulse {
    0% { box-shadow: 0 0 10px rgba(0,208,255,0.15); }
    50% { box-shadow: 0 0 20px rgba(0,208,255,0.35); }
    100% { box-shadow: 0 0 10px rgba(0,208,255,0.15); }
}
.glow-active {
    animation: glowPulse 2.5s infinite ease-in-out;
}

/* Footer or subtle fade */
.header-space {
    height: 60px;
    background: linear-gradient(to bottom, rgba(0,183,255,0.06), rgba(0,0,0,0));
}
</style>
""", unsafe_allow_html=True)
 
# ================================================
# HEADER
# ================================================
st.markdown("<h1 class='main-title'>⚡ Energy Vision</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='subtitle'>Your Personal Energy & Appliance Consultant</h3>", unsafe_allow_html=True)
 
# Add extra vertical space below header
st.markdown("<div class='header-space'></div>", unsafe_allow_html=True)
 
 
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
