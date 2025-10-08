import streamlit as st
import requests
import pandas as pd
import google.generativeai as genai
import re

# -----------------------------
# Streamlit Page Setup
# -----------------------------
st.set_page_config(
    page_title="Energy & Appliance Assistant",
    layout="wide",
)

st.title("⚡ Smart Home Energy & Appliance Assistant")

# Create three columns: left app | divider | right app
left_col, divider_col, right_col = st.columns([1, 0.02, 1])

# ====================================================
# LEFT SIDE → ENERGY INSIGHTS
# ====================================================
with left_col:
    st.header("🌍 Your Energy Your Way")

    @st.cache_data
    def load_tips():
        df = pd.read_excel("energy_tips_with_alert3.xlsx")
        return df

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
        lat = float(loc["lat"])
        lon = float(loc["lon"])
        display_name = loc.get("display_name", "Unknown Location")

        wx_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "temperature_2m,relative_humidity_2m"
        }
        r = requests.get(wx_url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        current = data.get("current_weather", {})
        temp = current.get("temperature")

        hourly_humidity = None
        if "hourly" in data and "relative_humidity_2m" in data["hourly"]:
            hourly_humidity = data["hourly"]["relative_humidity_2m"][0]

        return {"temp_c": temp, "humidity": hourly_humidity, "place": display_name}

    def match_prompt(forecast, df):
        temp = forecast["temp_c"]
        hum = forecast["humidity"]
        if temp is None or hum is None:
            return None
        df_temp = df.copy()
        df_temp["distance"] = ((df_temp["Temperature (°C)"] - temp) ** 2 + (df_temp["Humidity (%)"] - hum) ** 2) ** 0.5
        return df_temp.loc[df_temp["distance"].idxmin()]

    pincode = st.text_input("Enter your area PIN code (e.g., 560001):")

    if st.button("Get Today’s Insights"):
        if not pincode:
            st.error("Please enter a valid PIN code.")
        else:
            try:
                forecast = fetch_weather_from_pincode(pincode)
                st.subheader(f"Today's Forecast near {forecast['place']}")
                st.write(f"🌡️ Temperature: {forecast['temp_c']} °C")
                st.write(f"💧 Humidity: {forecast['humidity']} %")

                row = match_prompt(forecast, df)
                if row is not None:
                    st.subheader("⚡ Insights")
                    st.success(f"🔹 {row['Alert 1']}")
                    st.info(f"🔹 {row['Alert 2']}")
                    st.info(f"🔹 {row['Alert 3']}")
                else:
                    st.warning("No exact match found in the tips sheet.")
            except Exception as e:
                st.error(f"Error: {e}")

# ====================================================
# DIVIDER LINE (Vertical)
# ====================================================
with divider_col:
    st.markdown(
        """
        <div style="border-left: 2px solid #d3d3d3; height: 100vh; margin-left: auto; margin-right: auto;"></div>
        """,
        unsafe_allow_html=True,
    )

# ====================================================
# RIGHT SIDE → APPLIANCE DIAGNOSTIC
# ====================================================
with right_col:
    st.header("🔧 Appliance Diagnostic Assistant")

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    st.markdown(
        "Get quick **self-diagnosis steps**, **probable causes**, **service timelines**, and **customer support info** for your home appliances."
    )

    with st.form("diagnostic_form"):
        model_name = st.text_input("Model Number", placeholder="e.g. Mi L32M6-RA, LG T70SPSF2Z, Samsung WA62M4100HY")
        col1, col2 = st.columns(2)
        with col1:
            issue = st.text_area("Describe the Issue", placeholder="e.g. No display, Not cooling, making noise...")
        with col2:
            display_error = st.text_input("Error Code / Message (Optional)", placeholder="e.g. E4, F07, etc.")
        submitted = st.form_submit_button("Diagnose Appliance", use_container_width=True)

    if submitted:
        if not model_name or not issue:
            st.warning("Please fill in the required fields before diagnosing.")
        else:
            with st.spinner("Analyzing the issue... Please wait "):
                prompt = f"""
You are an intelligent appliance service diagnostic assistant.

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
   • Use simple spacing to make it look like a neat table.
   
   🔹 Turnaround Time (TAT)  
   • Mention the realistic average service time in days.

Formatting Instructions:
- Use no markdown, *, or # symbols.
- Each section heading should start with a blue diamond (🔹).
- Each point inside should start with a small black dot (•).
- Keep response short, clean, and visually structured.
"""

                try:
                    model = genai.GenerativeModel("gemini-2.5-flash-lite")
                    response = model.generate_content(prompt)
                    text = response.text

                    st.success("Diagnosis Report Generated Successfully!")
                    st.markdown("---")

                    match_brand = re.search(r'(Brand|Appliance Type).*?:\s*(.*)', text, re.IGNORECASE)
                    if match_brand:
                        st.markdown(
                            f"""
                            <div style='
                                background-color:#003366;
                                color:#FFFFFF;
                                padding:1rem;
                                border-radius:10px;
                                font-family:Arial;
                                margin-bottom:1rem;
                            '>
                            <h3>Brand & Appliance</h3>
                            <b>{match_brand.group(2).strip()}</b>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    sections = re.split(r'(?=🔹)', text)
                    colors = ["#1E90FF", "#4682B4", "#2E8B57", "#8B008B"]

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
                                    padding:1rem;
                                    border-radius:12px;
                                    margin-bottom:1rem;
                                    font-family:Arial, sans-serif;
                                    line-height:1.6;
                                ">
                                {sec_html}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                except Exception as e:
                    st.error(f"❌ Error: {e}")
