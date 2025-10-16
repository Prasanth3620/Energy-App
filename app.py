import streamlit as st
import requests
import pandas as pd
import google.generativeai as genai
import re
import json
import os

# ------------------------
# Streamlit Page Setup
# ------------------------
st.set_page_config(
    page_title="⚡ Energy Vision",
    layout="wide",
)

# ------------------------
# File Paths
# ------------------------
ENERGY_CSV = "energy_requests.csv"
SERVICE_CSV = "service_requests.csv"
CLICK_FILE = "click_counts.json"

# ------------------------
# Click Tracker
# ------------------------
def update_click_count(key):
    if os.path.exists(CLICK_FILE):
        with open(CLICK_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"insight_clicks": 0, "diagnostic_clicks": 0}
    data[key] += 1
    with open(CLICK_FILE, "w") as f:
        json.dump(data, f)

# ------------------------
# Save to CSV Helper
# ------------------------
def save_to_csv(filename, row):
    df_new = pd.DataFrame([row])
    if os.path.exists(filename):
        df_new.to_csv(filename, mode="a", index=False, header=False)
    else:
        df_new.to_csv(filename, index=False)

# ------------------------
# Custom CSS Styling
# ------------------------
st.markdown("""
<style>
    body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(to bottom, #D6E1F0, #C5D4E7); color: #0D1B2A; }
    .main-title { color: #005FE6; text-align: center; font-size: 2.5em; font-weight: 700; text-shadow: 0 1px 10px rgba(0, 95, 230, 0.25); margin-bottom: 0.3rem; }
    .subtitle { color: #3F4E61; text-align: center; font-size: 1.3em; margin-bottom: 2.5rem; }
    .section-header { color: #005FE6; font-size: 1.6em; font-weight: 600; margin-bottom: 1rem; }
    .info-card { background: linear-gradient(135deg, #E3E9F4, #D8E1F2); border-radius: 18px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15); border: 1px solid rgba(0, 95, 230, 0.15); }
    .divider { border-left: 2px solid rgba(0, 0, 0, 0.1); height: 100%; margin: auto; }
    div.stButton > button { background: linear-gradient(135deg, #005FE6, #007FFF) !important; color: white !important; border: none; border-radius: 12px; padding: 0.6rem 1.2rem; font-weight: 600; font-size: 1rem; box-shadow: 0 3px 10px rgba(0, 95, 230, 0.4); transition: all 0.2s ease-in-out; }
    div.stButton > button:hover { background: linear-gradient(135deg, #007FFF, #33A0FF) !important; transform: scale(1.03); box-shadow: 0 5px 14px rgba(0, 95, 230, 0.45); }
    .header-space { height: 80px; background: linear-gradient(to bottom, rgba(0,95,230,0.1), rgba(255,255,255,0)); }
</style>
""", unsafe_allow_html=True)

# ------------------------
# Header
# ------------------------
st.markdown("<h1 class='main-title'>⚡ Energy Vision</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='subtitle'>Your Personal Energy & Appliance Consultant</h3>", unsafe_allow_html=True)
st.markdown("<div class='header-space'></div>", unsafe_allow_html=True)

# ------------------------
# Layout
# ------------------------
left_col, divider_col, right_col = st.columns([1, 0.05, 1])

# ------------------------
# LEFT SIDE → Energy Insights
# ------------------------
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
            raise ValueError("Invalid PIN code.")
        loc = gdata[0]
        lat, lon = float(loc["lat"]), float(loc["lon"])
        display_name = loc.get("display_name", "Unknown Location")
        wx_url = "https://api.open-meteo.com/v1/forecast"
        r = requests.get(wx_url, params={"latitude": lat, "longitude": lon, "current_weather": True}, timeout=10)
        r.raise_for_status()
        data = r.json()
        temp = data.get("current_weather", {}).get("temperature")
        return {"temp_c": temp, "place": display_name}

    def match_prompt(forecast, df):
        temp = forecast["temp_c"]
        df["distance"] = abs(df["Temperature (°C)"] - temp)
        return df.loc[df["distance"].idxmin()]

    pincode = st.text_input("Enter your PIN Code", placeholder="e.g. 560001")
    if st.button("🔍 Get Today's Insights", use_container_width=True):
        update_click_count("insight_clicks")
        if not pincode:
            st.error("Please enter a valid PIN code.")
        else:
            try:
                forecast = fetch_weather_from_pincode(pincode)
                st.markdown(f"<div class='info-card'><b>📍 Location:</b> {forecast['place']}<br>🌡️ Temperature: {forecast['temp_c']}°C</div>", unsafe_allow_html=True)
                row = match_prompt(forecast, df)
                st.success(f"💡 {row['Alert 1']}")
                st.info(f"🔹 {row['Alert 2']}")
                st.info(f"🔹 {row['Alert 3']}")
                save_to_csv(ENERGY_CSV, {"pincode": pincode, "temperature": forecast["temp_c"], "location": forecast["place"]})
            except Exception as e:
                st.error(f"Error: {e}")

    # Password-protected view
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h4>📂 Previous Energy Requests</h4>", unsafe_allow_html=True)
    password_input = st.text_input("Enter password to view/download energy requests", type="password", key="energy_pass")

    if password_input == os.environ.get("DATA_PASSWORD", "admin123"):
        if os.path.exists(ENERGY_CSV):
            df_energy = pd.read_csv(ENERGY_CSV)
            st.dataframe(df_energy, use_container_width=True)
            st.download_button(
                label="⬇️ Download All Energy Entries as CSV",
                data=df_energy.to_csv(index=False).encode("utf-8"),
                file_name="energy_requests.csv",
                mime="text/csv"
            )
        else:
            st.info("No energy requests recorded yet.")
    elif password_input:
        st.error("❌ Incorrect password")

# ------------------------
# Divider
# ------------------------
with divider_col:
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ------------------------
# RIGHT SIDE → Appliance Diagnostic
# ------------------------
with right_col:
    st.markdown("<h3 class='section-header'>🔧 Appliance Diagnostic Assistant</h3>", unsafe_allow_html=True)
    st.markdown("Describe the issue to get quick troubleshooting guidance.")

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    model_name = st.text_input("Appliance Model Number", placeholder="e.g. LG T70SPSF2Z")
    display_error = st.text_input("Error Code (Optional)", placeholder="e.g. E4, F07")
    issue = st.text_area("Describe the Issue", placeholder="e.g. No display, making noise...")

    if st.button("🩺 Diagnose", use_container_width=True):
        update_click_count("diagnostic_clicks")
        if not model_name or not issue:
            st.warning("Please fill in the required fields.")
        else:
            with st.spinner("Analyzing the issue..."):
                prompt = f"Model: {model_name}\nIssue: {issue}\nError: {display_error or 'None'}"
                try:
                    model = genai.GenerativeModel("gemini-2.5-flash-lite")
                    response = model.generate_content(prompt)
                    st.markdown("<div class='info-card'><h4>✅ Diagnosis Report</h4></div>", unsafe_allow_html=True)
                    st.write(response.text)
                    save_to_csv(SERVICE_CSV, {"model_name": model_name, "error_code": display_error, "issue": issue})
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    # Password-protected section
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h4>📂 Previous Diagnostic Entries</h4>", unsafe_allow_html=True)
    password_input2 = st.text_input("Enter password to view/download diagnostic entries", type="password", key="diag_pass")

    if password_input2 == os.environ.get("DATA_PASSWORD", "admin123"):
        if os.path.exists(SERVICE_CSV):
            df_service = pd.read_csv(SERVICE_CSV)
            st.dataframe(df_service, use_container_width=True)
            st.download_button(
                label="⬇️ Download All Diagnostic Entries as CSV",
                data=df_service.to_csv(index=False).encode("utf-8"),
                file_name="service_requests.csv",
                mime="text/csv"
            )
        else:
            st.info("No diagnostic entries recorded yet.")
    elif password_input2:
        st.error("❌ Incorrect password")

# ------------------------
# Sidebar Tracker
# ------------------------
st.sidebar.title("📊 Click Tracker")
if os.path.exists(CLICK_FILE):
    with open(CLICK_FILE, "r") as f:
        data = json.load(f)
    st.sidebar.write(f"🔹 Insights Clicks: {data['insight_clicks']}")
    st.sidebar.write(f"🔹 Diagnostic Clicks: {data['diagnostic_clicks']}")
else:
    st.sidebar.info("No clicks recorded yet.")

# ------------------------
# Disclaimer
# ------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color: #555555; font-size: 0.9rem;'>⚠️ Disclaimer: The factuality of the responses may not be precise as they are LLM-generated responses.</p>",
    unsafe_allow_html=True
)
