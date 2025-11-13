import streamlit as st
import requests
import pandas as pd
import google.generativeai as genai
import re
import json
import os
import psycopg2

# ------------------------
# Database connection
# ------------------------
def get_connection():
    return psycopg2.connect(os.environ["Internal_Database_URL"])

conn = get_connection()
cursor = conn.cursor()

# Ensure the service_requests table exists (run only once)
cursor.execute("""
CREATE TABLE IF NOT EXISTS service_requests (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  model_name TEXT,
  error_code TEXT,
  issue TEXT
)
""")
conn.commit()

# ------------------------
# Streamlit Page Setup
# ------------------------
st.set_page_config(
    page_title="⚡ Energy Vision",
    layout="wide",
)

# ------------------------
# Click Tracker
# ------------------------
def update_click_count(key):
    filename = "click_counts.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
    else:
        data = {"insight_clicks": 0, "diagnostic_clicks": 0}
    data[key] += 1
    with open(filename, "w") as f:
        json.dump(data, f)

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
    .stApp { background: linear-gradient(to bottom, #D6E1F0, #C5D4E7); }
</style>
""", unsafe_allow_html=True)

# ------------------------
# Header
# ------------------------
st.markdown("<h1 class='main-title'>⚡ Energy Vision</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='subtitle'>Your Personal Energy & Appliance Consultant</h3>", unsafe_allow_html=True)
st.markdown("<div class='header-space'></div>", unsafe_allow_html=True)

# ------------------------
# Main Columns
# ------------------------
left_col, divider_col, right_col = st.columns([1, 0.05, 1])

# ------------------------
# LEFT SIDE → ENERGY INSIGHTS
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
            raise ValueError(f"No location found for PIN code {pincode}")
        loc = gdata[0]
        lat, lon = float(loc["lat"]), float(loc["lon"])
        display_name = loc.get("display_name", "Unknown Location")
        wx_url = "https://api.open-meteo.com/v1/forecast"
        r = requests.get(wx_url, params={"latitude": lat, "longitude": lon, "current_weather": True, "hourly": "temperature_2m,relative_humidity_2m"}, timeout=10)
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

    ENERGY_CSV = "energy_requests.csv"  # CSV file for storing energy requests

    with st.container():
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            pincode = st.text_input("Enter your PIN Code", placeholder="e.g. 560001")
            if st.button("🔍 Get Today's Insights", use_container_width=True):
                update_click_count("insight_clicks")
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

                        # ------------------------
                        # Save request to CSV including location & alerts
                        # ------------------------
                        energy_data = {
                            "timestamp": pd.Timestamp.now(),
                            "pincode": pincode,
                            "location": forecast['place'],
                            "temperature": forecast['temp_c'],
                            "humidity": forecast['humidity'],
                            "Alert 1": row["Alert 1"] if row is not None else "",
                            "Alert 2": row["Alert 2"] if row is not None else "",
                            "Alert 3": row["Alert 3"] if row is not None else ""
                        }
                        if os.path.exists(ENERGY_CSV):
                            df_energy = pd.read_csv(ENERGY_CSV)
                            df_energy = pd.concat([df_energy, pd.DataFrame([energy_data])], ignore_index=True)
                        else:
                            df_energy = pd.DataFrame([energy_data])
                        df_energy.to_csv(ENERGY_CSV, index=False)

                        # Save to DB (optional, if you still want)
                        try:
                            cursor.execute(
                                "INSERT INTO energy_requests (pincode, temperature, humidity, location, alert1, alert2, alert3) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                (pincode, forecast['temp_c'], forecast['humidity'], forecast['place'],
                                 row["Alert 1"] if row is not None else None,
                                 row["Alert 2"] if row is not None else None,
                                 row["Alert 3"] if row is not None else None)
                            )
                            conn.commit()
                        except Exception as e:
                            st.error(f"❌ Database Error: {e}")
                    except Exception as e:
                        st.error(f"Error: {e}")

# ------------------------
# Divider
# ------------------------
with divider_col:
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ------------------------
# RIGHT SIDE → APPLIANCE DIAGNOSTIC
# ------------------------
with right_col:
    st.markdown("<h3 class='section-header'>🔧 Appliance Diagnostic Assistant</h3>", unsafe_allow_html=True)
    st.markdown("Describe the issue to get quick troubleshooting guidance.")

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    with st.form("diagnostic_form"):
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            model_name = st.text_input("Appliance Model Number", placeholder="e.g. LG T70SPSF2Z, Mi L32M6-RA")
        with col2:
            display_error = st.text_input("Error Code (Optional)", placeholder="e.g. E4, F07, etc.")

        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            issue = st.text_area("Describe the Issue", placeholder="e.g. No display, making noise...")

        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            submitted = st.form_submit_button("🩺 Diagnose", use_container_width=True)

    if submitted:
        update_click_count("diagnostic_clicks")
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
                            sec_html = sec.replace('\n', '<br>')
                            st.markdown(f"""
<div style="
    background-color:{colors[i % len(colors)]};
    color:#FFFFFF;
    padding:1.2rem;
    border-radius:12px;
    margin-bottom:1rem;
    box-shadow: 0 0 15px rgba(0,0,0,0.3);
">
{sec_html}
</div>""", unsafe_allow_html=True)
                    # Save to DB
                    try:
                        cursor.execute(
                            "INSERT INTO service_requests (model_name, error_code, issue) VALUES (%s, %s, %s)",
                            (model_name, display_error, issue)
                        )
                        conn.commit()
                    except Exception as e:
                        st.error(f"❌ Database Error: {e}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# # ------------------------
# # Sidebar Click Tracker + Admin Access
# # ------------------------
# st.sidebar.title("📊 Click Tracker")
# if os.path.exists("click_counts.json"):
#     with open("click_counts.json", "r") as f:
#         data = json.load(f)
#     st.sidebar.write(f"🔹 Insights Clicks: {data['insight_clicks']}")
#     st.sidebar.write(f"🔹 Diagnostic Clicks: {data['diagnostic_clicks']}")
# else:
#     st.sidebar.info("No clicks recorded yet.")

# ------------------------
# Sidebar Admin Password & Data Access
# ------------------------
st.sidebar.title("🔒 Admin Access")
admin_password = st.sidebar.text_input("Enter Admin Password", type="password")
if admin_password == os.environ["DATA_PASSWORD"]:
    st.sidebar.success("Access granted ✅")

    st.sidebar.markdown("### 📂 Previous Energy Requests")
    if os.path.exists(ENERGY_CSV):
        df_energy = pd.read_csv(ENERGY_CSV)
        st.sidebar.dataframe(df_energy)
        st.sidebar.download_button(
            label="⬇️ Download Energy Requests CSV",
            data=df_energy.to_csv(index=False).encode("utf-8"),
            file_name="energy_requests.csv",
            mime="text/csv"
        )
    else:
        st.sidebar.info("No energy requests recorded yet.")

   
    try:
        df_ene = pd.read_sql("SELECT * FROM energy_requests ORDER BY timestamp DESC", conn)
        if not df_ene.empty:
            st.sidebar.dataframe(df_ene)
            st.sidebar.download_button(
                label="⬇️ Download Energy Entries CSV",
                data=df_ene.to_csv(index=False).encode("utf-8"),
                file_name="energy_requests.csv",
                mime="text/csv"
            )
        else:
            st.sidebar.info("No Pincode entries recorded yet.")
    except Exception as e:
        st.sidebar.error(f"❌ Could not fetch Pincode entries: {e}")
        
    st.sidebar.markdown("### 📂 Previous Diagnostic Entries")    
    try:
        df_diag = pd.read_sql("SELECT * FROM service_requests ORDER BY timestamp DESC", conn)
        if not df_diag.empty:
            st.sidebar.dataframe(df_diag)
            st.sidebar.download_button(
                label="⬇️ Download Diagnostic Entries CSV",
                data=df_diag.to_csv(index=False).encode("utf-8"),
                file_name="service_requests.csv",
                mime="text/csv"
            )
        else:
            st.sidebar.info("No diagnostic entries recorded yet.")
    except Exception as e:
        st.sidebar.error(f"❌ Could not fetch diagnostic entries: {e}")
elif admin_password:
    st.sidebar.error("❌ Incorrect password")

# ------------------------
# Disclaimer
# ------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color: #555555; font-size: 0.9rem;'>⚠️ Disclaimer: The factuality of the responses may not be precise as they are LLM-generated responses. Please share your feedback with us.</p>",
    unsafe_allow_html=True
)
