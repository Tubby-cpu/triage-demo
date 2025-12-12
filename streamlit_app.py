import streamlit as st
import requests
from datetime import datetime
import base64
from fpdf import FPDF

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
st.markdown("<p class='purple'>AI-powered SATS • HealthID • PDF Report</p>", unsafe_allow_html=True)

# ————————————————————————
# Session state
# ————————————————————————
if "history" not in st.session_state:
    st.session_state.history = []
if "current_patient" not in st.session_state:
    st.session_state.current_patient = None

# ————————————————————————
# Sidebar – Patient lookup
# ———————————————————————
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/9/9f/Discovery_Limited_Logo.svg", width=180)
    st.header("Patient Lookup")
    health_id = st.text_input("HealthID / SA ID Number", placeholder="e.g. 8203155017089")

    if st.button("Load Patient", type="primary"):
        if health_id and len(health_id) >= 10:                      # ← fixed line
            # Mock data (replace with real HealthID API later)
            mock_patients = {
                "8203155017089": {"name": "Thabo Mokoena",     "age": 42, "sex": "Male"},
                "9112240123456": {"name": "Sarah Naidoo",      "age": 31, "sex": "Female"},
                "7509015888088": {"name": "Pieter van der Merwe", "age": 49, "sex": "Male"},
            }
            patient = mock_patients.get(health_id, {
                "name": f"Member …{health_id[-4:]}",
                "age": 35,
                "sex": "Not specified"
            })
            st.session_state.current_patient = patient
            st.session_state.current_patient["health_id"] = health_id
            st.success(f"Patient loaded: {patient['name']}")
            st.rerun()
        else:
            st.error("Please enter a valid ID number")

    if st.button("New Patient", type="secondary"):
        st.session_state.current_patient = None
        st.rerun()

    st.divider()
    st.subheader("Recent Patients")
    for entry in st.session_state.history[-5:]:
        st.caption(f"{entry['name']} • {entry['priority']} • {entry['time']}")

# ————————————————————————
# Main form
# ————————————————————————
if st.session_state.current_patient is None:
    st.info("Load a patient with their HealthID to start triage.")
    st.stop()

p = st.session_state.current_patient

st.success(f"**Active Patient:** {p['name']} | Age: {p.get('age', '?')} | {p.get('sex', '?')} | …{p['health_id'][-4:]}")

col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Age (years)", value=p.get("age", 35), min_value=0, max_value=120)
    sex = st.radio("Sex", ["Male", "Female", "Other"], index=["Male","Female","Other"].index(p.get("sex","Male")) if p.get("sex") in ["Male","Female","Other"] else 0, horizontal=True)

with col2:
    mobility = st.selectbox("Mobility", ["Walks unaided", "With help", "Stretcher / Immobile"])
    resp_rate = st.slider("Respiratory Rate", 5, 60, 22)
    heart_rate = st.slider("Heart Rate", 30, 200, 88)
    systolic_bp = st.slider("Systolic BP (mmHg)", 50, 250, 130)
    temp = st.slider("Temperature (°C)", 30.0, 43.0, 37.0, 0.1)

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

    critical_keywords = ["unconscious", "seizure", "not breathing", "massive bleed"]
    if any(k in chief.lower() for k in critical_keywords): score += 3
    if "chest pain" in chief.lower(): score += 2

    if score >= 10: return "RED", "#ff1744"
    elif score >= 7: return "ORANGE", "#ff9100"
    elif score >= 4: return "YELLOW", "#ff0"
    else: return "GREEN", "#00ff00"

if st.button("Calculate SATS Priority", type="primary"):
    priority, colour = calculate_sats()
    st.markdown(f"<h1 style='color:{colour};text-align:center;'>SATS: {priority}</h1>", unsafe_allow_html=True)
    st.session_state.last_priority = priority
    st.balloons()

# ————————————————————————
# PDF report
# ————————————————————————
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.set_fill_color(75, 0, 130)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "DISCOVERY HEALTH TRIAGE REPORT", ln=1, align="C", fill=True)
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"Patient      : {p['name']}", ln=1)
    pdf.cell(0, 8, f"HealthID    : ending …{p['health_id'][-4:]}", ln=1)
    pdf.cell(0, 8, f"Date & Time : {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
    pdf.cell(0, 8, f"Priority    : {st.session_state.get('last_priority', 'Not calculated')}", ln=1)
    pdf.ln(8)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7, f"Chief complaint : {chief or '—'}")
    pdf.multi_cell(0, 7, f"Other symptoms  : {symptoms or '—'}")
    pdf.multi_cell(0, 7, f"Vitals         : RR {resp_rate} | HR {heart_rate} | BP {systolic_bp} | Temp {temp}°C")
    pdf.multi_cell(0, 7, f"Mobility       : {mobility}")
    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 8, "Generated by Discovery Triage Pilot • Internal use only", align="C")
    return pdf.output(dest="S").encode("latin-1")

if st.button("Generate & Download PDF Report"):
    if "last_priority" not in st.session_state:
        st.warning("Calculate SATS priority first")
    else:
        pdf_bytes = create_pdf()
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="Triage_{p["name"].replace(" ", "_")}.pdf">Download PDF Report</a>'
        st.markdown(href, unsafe_allow_html=True)

        # Save to history
        st.session_state.history.append({
            "name": p["name"],
            "priority": st.session_state.last_priority,
            "time": datetime.now().strftime("%H:%M")
        })

st.divider()
st.caption("2025 Discovery Health Internal Pilot • Built in South Africa")
