import pandas as pd
import streamlit as st
from supabase import create_client
 
# -----------------------------
# Streamlit setup
# -----------------------------
st.set_page_config(
    page_title="DHT11 Dashboard",
    page_icon="🌡️",
    layout="centered",
    initial_sidebar_state="collapsed",
)
 
# -----------------------------
# Supabase connection
# -----------------------------
@st.cache_resource
def get_client():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]  # anon/public key
    return create_client(url, key)
 
supabase = get_client()
 
# -----------------------------
# Fetch data
# -----------------------------
@st.cache_data(ttl=10)  # refresh every 10 seconds
def fetch_data(limit=1000):
    res = (
        supabase.table("maintable")      # <-- change "maintable" if your table name differs
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    df = pd.DataFrame(res.data or [])
    if df.empty:
        return df
 
    # Parse timestamps
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df = df.sort_values("created_at")
    df["DateTime"] = df["created_at"].dt.tz_convert(None)  # strip timezone
    return df
 
# -----------------------------
# UI
# -----------------------------
st.title("🌡️ DHT11 Live Dashboard")
 
df = fetch_data(limit=1000)
if df.empty:
    st.info("No data found yet. Once your Arduino writes rows to Supabase, they’ll show up here.")
else:
    latest = df.iloc[-1]
 
    # Metrics
    c1, c2, c3 = st.columns(3)
    if "temperature" in df.columns:
        c1.metric("Latest Temperature (°C)", f"{latest['temperature']:.1f}")
    if "humidity" in df.columns:
        c2.metric("Latest Humidity (%)", f"{latest['humidity']:.1f}")
    c3.metric("Last Update", latest["DateTime"].strftime("%Y-%m-%d %H:%M:%S"))
 
    # Charts
    if "temperature" in df.columns:
        st.subheader("Temperature")
        st.line_chart(df.set_index("DateTime")[["temperature"]], use_container_width=True)
 
    if "humidity" in df.columns:
        st.subheader("Humidity")
        st.line_chart(df.set_index("DateTime")[["humidity"]], use_container_width=True)
 
    # Raw data
    with st.expander("Raw Data"):
        st.dataframe(df[::-1], use_container_width=True)
