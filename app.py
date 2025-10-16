import streamlit as st
import psycopg2
import pandas as pd
import os
from datetime import datetime

# ==========================================================
# Streamlit Page Setup
# ==========================================================
st.set_page_config(page_title="⚡ Energy Vision", layout="wide")

# ==========================================================
# Database Connection
# ==========================================================
def get_connection():
    return psycopg2.connect(
        host="dpg-d3n13u9r0fns739jnt4g-a.oregon-postgres.render.com",
        database="energyvision_db",
        user="energyvision_db_user",
        password="reuERnvdz2UF6oNwofZX1rLpFkZgTACQ",
        port="5432"
    )

conn = get_connection()
cursor = conn.cursor()

# ==========================================================
# Table Setup
# ==========================================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS energy_requests (
    id SERIAL PRIMARY KEY,
    pincode VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS service_requests (
    id SERIAL PRIMARY KEY,
    appliance_model VARCHAR(100),
    error_code VARCHAR(100),
    issue VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()

# ==========================================================
# CSS Styling
# ==========================================================
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #DFF1FF 0%, #A2C2E8 100%);
}
h1, h2, h3 {
    color: #003366;
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# Title
# ==========================================================
st.markdown("<h1 style='text-align:center;'>⚡ Energy Vision Portal</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#003366;'>Empowering Smart Diagnostics and Energy Insights</p>", unsafe_allow_html=True)
st.markdown("---")

# ==========================================================
# Layout with Two Columns
# ==========================================================
col1, col2 = st.columns(2)

# ---------------- Left Side: Energy Request ----------------
with col1:
    st.subheader("🏠 Energy Requests")
    pincode = st.text_input("Enter your area pincode:")
    if st.button("Submit Pincode"):
        if pincode.strip():
            cursor.execute("INSERT INTO energy_requests (pincode) VALUES (%s)", (pincode,))
            conn.commit()
            st.success("✅ Pincode submitted successfully!")
        else:
            st.warning("⚠️ Please enter a valid pincode.")

# ---------------- Right Side: Service Diagnostics ----------------
with col2:
    st.subheader("🔧 Appliance Diagnostic Form")
    appliance_model = st.text_input("Appliance Model:")
    error_code = st.text_input("Error Code:")
    issue = st.text_area("Describe the issue:")
    if st.button("Submit Diagnostic"):
        if appliance_model.strip() and error_code.strip() and issue.strip():
            cursor.execute("""
                INSERT INTO service_requests (appliance_model, error_code, issue)
                VALUES (%s, %s, %s)
            """, (appliance_model, error_code, issue))
            conn.commit()
            st.success("✅ Diagnostic submitted successfully!")
        else:
            st.warning("⚠️ Please fill all fields before submitting.")

# ==========================================================
# Disclaimer
# ==========================================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:black; font-size:14px;'>⚠️ Disclaimer: "
    "The factuality of the responses may not be precise as they are LLM-generated responses.</p>",
    unsafe_allow_html=True,
)

# ==========================================================
# 🔒 ADMIN PANEL (Password Protected)
# ==========================================================
st.markdown("---")
st.markdown("<h4 style='text-align:center; color:#005FE6;'>🔐 Admin Access (Private)</h4>", unsafe_allow_html=True)

admin_pass = st.text_input("Enter admin password to view database", type="password")

if admin_pass == os.environ.get("DATA_PASSWORD"):
    st.success("✅ Access granted. Welcome, Admin!")

    tab1, tab2 = st.tabs(["🌞 Energy Requests", "🔧 Diagnostic Entries"])

    # Energy Requests
    with tab1:
        try:
            df_energy = pd.read_sql("SELECT * FROM energy_requests ORDER BY timestamp DESC", conn)
            if not df_energy.empty:
                st.dataframe(df_energy, use_container_width=True)
                st.download_button(
                    label="⬇️ Download Energy Data (CSV)",
                    data=df_energy.to_csv(index=False).encode("utf-8"),
                    file_name="energy_requests.csv",
                    mime="text/csv"
                )
            else:
                st.info("No energy requests recorded yet.")
        except Exception as e:
            st.error(f"❌ Could not fetch energy requests: {e}")

    # Diagnostic Requests
    with tab2:
        try:
            df_diag = pd.read_sql("SELECT * FROM service_requests ORDER BY timestamp DESC", conn)
            if not df_diag.empty:
                st.dataframe(df_diag, use_container_width=True)
                st.download_button(
                    label="⬇️ Download Diagnostic Data (CSV)",
                    data=df_diag.to_csv(index=False).encode("utf-8"),
                    file_name="service_requests.csv",
                    mime="text/csv"
                )
            else:
                st.info("No diagnostic entries recorded yet.")
        except Exception as e:
            st.error(f"❌ Could not fetch diagnostic entries: {e}")

elif admin_pass:
    st.error("❌ Incorrect password.")
