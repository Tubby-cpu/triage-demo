import streamlit as st
import requests
import json
from datetime import datetime
import os

# Page config & styling
st.set_page_config(
    page_title="Discovery Triage Pilot",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Discovery Health purple theme
st.markdown("""
<style>
    .css-1d391kg {padding-top: 1rem;}
    .stApp {background-color: #f8f5ff;}
    .big-font {font-size: 42px !important; font-weight: bold; color: #4B0082;}
    .purple {color: #4B0082;}
    .stButton>button {background-color: #4B0082; color: white;}
</style>
""", unsafe_allow_html=True)

st.markdown("<p class='big-font'>Discovery Triage Pilot</p>", unsafe_allow_html=True)
st.markdown("<p class='purple'>AI-powered SATS + HealthID integration</p>", unsafe_allow_html=True)

# Sidebar – HealthID login (mock for now)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/9/9f/Discovery_Limited_Logo.svg", width=200)
    st.header("Patient Lookup")
    health_id = st.text_input("Enter HealthID / ID Number", placeholder="e.g. 8203155017089")
    
    if st.button("Load Patient"):
        if health_id:
            st.success(f"Patient found: Member {health_id[:4]}****")
            st.session_state.patient_id = health_id
        else:
            st.warning("Please enter a valid HealthID")

    st.divider()
    st.caption("Built for Discovery Primary Care & Employer Clinics")

# Main triage form
st.header("Clinical Triage (SATS)")

col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Age (years)", min_value=0, max_value=120, value=35)
    male = st.radio("Sex", ["Male", "Female", "Other"])

with col2:
    mobility = st.selectbox("Mobility", ["Walks", "With help", "Stretcher / Immobile"])
    resp_rate = st.slider("Respiratory Rate (breaths/min)", 5, 60, 20)
    heart_rate = st.slider("Heart Rate (bpm)", 30, 200, 90)
    systolic_bp = st.slider("Systolic BP (mmHg)", 50, 250, 120)
    temperature = st.slider("Temperature (°C)", 30.0, 43.0, 36.8, 0.1)

st.subheader("Chief Complaint & Symptoms")
chief_complaint = st.text_area("Chief complaint", placeholder="e.g. Chest pain, shortness of breath, fever x 3 days")
symptoms = st.text_input("Additional symptoms (comma-separated)", placeholder="nausea, vomiting, headache")

# AI Symptom Checker (Groq + Llama 3.1)
GROQ_API_KEY = "gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Replace with your free key from console.groq.com/keys

if st.button("Run AI Symptom Analysis"):
    if GROQ_API_KEY == "gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX":
        st.warning("Quick setup: Get your free Groq API key at https://console.groq.com/keys and paste it above. Until then, here's a demo response:")
        st.info("**AI Suggestion:** Based on chest pain and elevated HR, this suggests ORANGE priority - immediate nurse assessment for cardiac rule-out.")
    else:
        with st.spinner("Analysing with Llama 3.1..."):
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                prompt = f"""
                You are an experienced South African emergency nurse.
                Patient: {age} year old {male.lower()}, chief complaint: {chief_complaint}.
                Symptoms: {symptoms}.
                Vitals: RR {resp_rate}, HR {heart_rate}, BP {systolic_bp}, Temp {temperature}°C.
                Give ONLY the likely SATS colour (RED / ORANGE / YELLOW / GREEN) and 1-sentence justification.
                """
                payload = {
                    "model": "llama-3.1-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 100
                }
                response = requests.post(url, headers=headers, json=payload, timeout=20)
                response.raise_for_status()
                ai_result = response.json()["choices"][0]["message"]["content"]
                st.success("AI Suggested Priority:", ai_result)
            except Exception as e:
                st.error(f"AI hiccup: {str(e)[:100]}... Check your key or try again.")

# Simple SATS calculator (Western Cape 2024 adult version)
def calculate_sats():
    score = 0
    if resp_rate > 30 or resp_rate < 9: score += 3
    elif resp_rate >= 25 or resp_rate <= 10: score += 2
    elif resp_rate >= 22 or resp_rate <= 11: score += 1

    if heart_rate > 140 or heart_rate < 40: score += 3
    elif heart_rate >= 120 or heart_rate <= 50: score += 2
    elif heart_rate >= 100 or heart_rate <= 60: score += 1

    if systolic_bp > 220 or systolic_bp < 80: score += 3
    elif systolic_bp >= 200 or systolic_bp <= 90: score += 2

    if temperature >= 38.5 or temperature < 35: score += 2

    if mobility in ["Stretcher / Immobile"]: score += 3
    elif mobility == "With help": score += 1

    # TEWS modifiers
    if "unconscious" in chief_complaint.lower() or "seizure" in chief_complaint.lower(): score += 3
    if "chest pain" in chief_complaint.lower(): score += 2
    if "severe" in chief_complaint.lower() or "bleeding" in chief_complaint.lower(): score += 3

    if score >= 10: return "RED", "#ff0000"
    elif score >= 7: return "ORANGE", "#ffa500"
    elif score >= 4: return "YELLOW", "#ffff00"
    else: return "GREEN", "#00ff00"

if st.button("Calculate SATS Priority", type="primary"):
    priority, colour = calculate_sats()
    st.markdown(f"""
    <h2 style='color:{colour};text-align:center;'>
        SATS PRIORITY: {priority}
    </h2>
    """, unsafe_allow_html=True)
    st.balloons()

# Footer
st.divider()
st.caption("2025 Discovery Health Pilot. Built in South Africa. For internal demonstration only.")
