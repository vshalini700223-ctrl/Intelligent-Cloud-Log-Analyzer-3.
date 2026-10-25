import streamlit as st

# ✅ Page config must come FIRST
st.set_page_config(page_title="Log Analyzer", layout="wide")

import pandas as pd
from utils.parser import parse_log_file
from utils.anomaly import detect_anomalies
from utils.storage import init_db, save_logs
from utils.slack_alert import send_slack_alert  # 🔔 Slack integration
from streamlit_autorefresh import st_autorefresh

# 🔁 Auto-refresh every 10 seconds
st_autorefresh(interval=10_000, limit=None, key="refresh")

# 🔧 Initialize DB
init_db()

# 🏷️ App Title
st.title("📊 Log Analyzer Dashboard")

# --- Upload log file ---
uploaded_file = st.file_uploader("Upload a log file (.log or .json)", type=["log", "json"])

if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    extension = uploaded_file.name.split('.')[-1]
    temp_path = f"logs/temp_uploaded.{extension}"
    with open(temp_path, "w") as f:
        f.write(content)
    df = parse_log_file(temp_path)
    st.success("✅ File uploaded and parsed successfully!")
else:
    df = parse_log_file("logs/sample1.log")  # fallback file
    st.success("✅ Sample file parsed successfully!")

# --- Filter logs ---
st.subheader("🔍 Filter Logs")
services = ['All'] + sorted(df['service'].unique())
levels = ['All'] + sorted(df['level'].unique())

col1, col2 = st.columns(2)
selected_service = col1.selectbox("Service", services)
selected_level = col2.selectbox("Log Level", levels)

if selected_service != 'All':
    df = df[df['service'] == selected_service]
if selected_level != 'All':
    df = df[df['level'] == selected_level]

# --- Show parsed logs ---
st.subheader("🧾 Parsed Logs")
st.dataframe(df)

# --- Save to DB ---
if st.button("💾 Save logs to DB"):
    save_logs(df)
    st.success("Logs saved to SQLite!")

# --- Anomaly detection ---
st.subheader("🚨 Anomalous Services")
anomalies = detect_anomalies(df)

if anomalies.empty:
    st.success("No anomalies detected 🎉")
else:
    st.error("Anomalies found!")
    st.dataframe(anomalies)

    st.warning("📢 Alert: Spike in anomalies detected!")

    # 🔔 Send Slack alert
    services = anomalies['service'].tolist()
    webhook_url = st.secrets.get("slack", {}).get("webhook", "")
    success = send_slack_alert(services, webhook_url)

   if webhook_url:
    success = send_slack_alert(services, webhook_url)
else:
    success = False
# --- Error chart ---
st.subheader("📈 Error Count by Service")
error_counts = df[df['level'] == 'ERROR'].groupby('service').size()
if not error_counts.empty:
    st.bar_chart(error_counts)
else:
    st.info("No error logs to display.")
