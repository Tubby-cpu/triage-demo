import streamlit as st
from datetime import datetime
import base64
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

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
st.markdown("<p class='purple'>SATS • HealthID • Instant PDF Report</p>", unsafe_allow_html=True)

# ————————————————————————
# Session state
# ————————————————————————
if "history" not in st.session_state: st.session_state.history = []
if "current_patient" not in st.session_state: st.session_state.current_patient = None

# ————————————————————————
# Sidebar
# ————————————————————————
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/9/9f/Discovery_Limited_Logo.svg", width=180)
    st.header("Patient Lookup")
    health_id = st.text_input("HealthID / SA ID", placeholder="e.g. 8203155017089")

    if st.button("Load Patient", type="primary"):
        if health_id and len(health_id) >= 10:
            mock = {
                "8203155017089": {"name": "Thabo Mokoena",      "age": 42, "sex": "Male"},
                "9112240123456": {"name": "Sarah Naidoo",       "age": 31, "sex": "Female"},
                "7509015888088": {"name": "Pieter van der Merwe","age": 49, "sex": "Male"},
            }
            patient = mock.get(health_id, {"name": f"Member …{health_id[-4:]}", "age": 35, "sex": "Not specified"})
            patient["health_id"] = health_id
            st.session_state.current_patient = patient
            st.success(f"Loaded: {patient['name']}")
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
    st.info("Load a patient to start triage.")
    st.stop()

p = st.session_state.current_patient
st.success(f"**Active:** {p['name']} | {p.get('age')}y | {p.get('sex')} | …{p['health_id'][-4:]}")

col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Age", value=p.get("age",35), min_value=0, max_value=120)
    sex = st.radio("Sex", ["Male","Female","Other"], horizontal=True,
                   index=["Male","Female","Other"].index(p.get("sex","Male")) if p.get("sex") in ["Male","Female","Other"] else 0)

with col2:
    mobility = st.selectbox("Mobility", ["Walks unaided", "With help", "Stretcher / Immobile"])
    resp_rate = st.slider("RR",5,60,22)
    heart_rate = st.slider("HR",30,200,88)
    systolic_bp = st.slider("BP",50,250,130)
    temp = st.slider("Temp °C",30.0,43.0,37.0,0.1)

chief = st.text_area("Chief Complaint", height=100)
symptoms = st.text_input("Other symptoms")

# ————————————————————————
# SATS calculator
# ————————————————————————
def sats():
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
    elif score >= 7:  return "ORANGE", "#ff9100"
    elif score >= 4:  return "YELLOW", "#ffff00"
    else:             return "GREEN",  "#00e676"

if st.button("Calculate SATS Priority", type="primary"):
    priority, colour = sats()
    st.markdown(f"<h1 style='color:{colour};text-align:center;'>SATS: {priority}</h1>", unsafe_allow_html=True)
    st.session_state.last_priority = priority
    st.balloons()

# ————————————————————————
# PDF with ReportLab (always works on Streamlit Cloud)
# ————————————————————————
def generate_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("DISCOVERY HEALTH TRIAGE REPORT", styles['Title']))
    story.append(Spacer(1, 12))

    # Details
    story.append(Paragraph(f"<b>Patient:</b> {p['name']}", styles['Normal']))
    story.append(Paragraph(f"<b>HealthID:</b> ending …{p['health_id'][-4:]}", styles['Normal']))
    story.append(Paragraph(f"<b>Date & Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Paragraph(f"<b>Priority:</b> {st.session_state.get('last_priority', '—')}", styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Chief complaint:</b> {chief or '—}", styles['Normal']))
    story.append(Paragraph(f"<b>Symptoms:</b> {symptoms or '—'}", styles['Normal']))
    story.append(Paragraph(f"<b>Vitals:</b> RR {resp_rate} | HR {heart_rate} | BP {systolic_bp} | Temp {temp}°C", styles['Normal']))
    story.append(Paragraph(f"<b>Mobility:</b> {mobility}", styles['Normal']))

    doc.build(story)
    return buffer.getvalue()

if st.button("Generate & Download PDF Report"):
    if "last_priority" not in st.session_state:
        st.warning("Calculate SATS first")
    else:
        pdf = generate_pdf()
        st.download_button(
            label="Download PDF Report",
            data=pdf,
            file_name=f"Triage_{p['name'].replace(' ','_')}.pdf",
            mime="application/pdf"
        )
        st.session_state.history.append({
            "name": p["name"],
            "priority": st.session_state.last_priority,
            "time": datetime.now().strftime("%H:%M")
        })
        st.success("Report ready!")

st.divider()
st.caption("2025 Discovery Health Internal Pilot • Built in South Africa")
