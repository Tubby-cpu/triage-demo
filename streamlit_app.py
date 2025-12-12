```python
import streamlit as st
from datetime import datetime
import base64
from fpdf2 import FPDF          # this one is pre-installed on Streamlit Cloud

# ————————————————————————
# Page config & styling
# ————————————————————————
st.set_page_config(page_title="Discovery Triage Pilot", page_icon="hospital", layout="centered")

st.markdown("""
<style>
    .big-font {font-size: 42px !important; font-weight: bold; color: #4B0082;}
    .purple {color: #4B0082;}
    .stButton>button {background-color: #4B0082; color: white; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<p class='big-font'>Discovery Triage Pilot</p>", unsafe_allow_html=True)
st.markdown("<p class='purple'>SATS • HealthID • PDF Report</p>", unsafe_allow_html=True)

# ————————————————————————
# Session state
# ————————————————————————
if "history" not in st.session_state:
    st.session_state.history = []
if "current_patient" not in st.session_state:
    st.session_state.current_patient = None

# ————————————————————————
# Sidebar – Patient lookup
# ————————————————————————
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/9/9f/Discovery_Limited_Logo.svg", width=180)
    st.header("Patient Lookup")
    health_id = st.text_input("HealthID / SA ID", placeholder="e.g. 8203155017089")

    if st.button("Load Patient", type="primary"):
        if health_id and len(health_id) >= 10:
            mock_patients = {
                "8203155017089": {"name": "Thabo Mokoena",      "age": 42, "sex": "Male"},
                "9112240123456": {"name": "Sarah Naidoo",       "age": 31, "sex": "Female"},
                "7509015888088": {"name": "Pieter van der Merwe","age": 49, "sex": "Male"},
            }
            patient = mock_patients.get(health_id, {
                "name": f"Member …{health_id[-4:]}",
                "age": 35,
                "sex": "Not specified"
            })
            patient["health_id"] = health_id
            st.session_state.current_patient = patient
            st.success(f"Patient loaded: {patient['name']}")
            st.rerun()
        else:
            st.error("Enter a valid ID")

    if st.button("New Patient"):
        st.session_state.current_patient = None
        st.rerun()

    st.divider()
    st.subheader("Recent Patients")
    for e in st.session_state.history[-5:]:
        st.caption(f"{e['name']} • {e['priority']} • {e['time']}")

# ————————————————————————
# Main form
# ————————————————————————
if st.session_state.current_patient is None:
    st.info("Load a patient to begin triage.")
    st.stop()

p = st.session_state.current_patient
st.success(f"**Active Patient:** {p['name']} | Age {p.get('age')} | {p.get('sex')} | …{p['health_id'][-4:]}")

col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Age (years)", value=p.get("age", 35), min_value=0, max_value=120)
    # Fixed radio button line – no invisible characters
    current_sex = p.get("sex", "Male")
    if current_sex not in ["Male", "Female", "Other"]:
        current_sex = "Not specified"
    sex = st.radio("Sex", ["Male", "Female", "Other"], 
                   index=["Male","Female","Other"].index(current_sex) if current_sex in ["Male","Female","Other"] else 0,
                   horizontal=True)

with col2:
    mobility = st.selectbox("Mobility", ["Walks unaided", "With help", "Stretcher / Immobile"])
    resp_rate = st.slider("Respiratory Rate", 5, 60, 22)
    heart_rate = st.slider("Heart Rate", 30, 200, 88)
    systolic_bp = st.slider("Systolic BP (mmHg)", 50, 250, 130)
    temp = st.slider("Temperature °C", 30.0, 43.0, 37.0, 0.1)

chief = st.text_area("Chief Complaint", height=100)
symptoms = st.text_input("Other symptoms")

# ————————————————————————
# SATS calculator
# ————————————————————————
def calculate_sats():
    score = 0
    if resp_rate > 30 or resp_rate < 9: score += 3
    elif resp_rate >= 25 or resp_rate <= 10: score += 2
    elif resp_rate >= 22 or resp_rate <= 11: score += 1

    if heart_rate > 140 or heart_rate < 40: score += 3
    elif heart_rate >= 111: score += 2
    elif heart_rate >= 101: score += 1

    if systolic_bp < 90: score += 3
    if temp >= 38.5 or temp < 35: score += 2
    if mobility == "Stretcher / Immobile": score += 3
    elif mobility == "With help": score += 1

    if any(k in chief.lower() for k in ["unconscious","seizure","not breathing","massive bleed"]): score += 3
    if "chest pain" in chief.lower(): score += 2

    if score >= 10: return "RED",     "#ff1744"
    elif score >= 7:  return "ORANGE",  "#ff9100"
    elif score >= 4:  return "YELLOW", "#ffff00"
    else:             return "GREEN",   "#00e676"

if st.button("Calculate SATS Priority", type="primary"):
    priority, colour = calculate_sats()
    st.markdown(f"<h1 style='color:{colour};text-align:center;'>SATS: {priority}</h1>", unsafe_allow_html=True)
    st.session_state.last_priority = priority
    st.balloons()
