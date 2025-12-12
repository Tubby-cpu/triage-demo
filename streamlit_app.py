import streamlit as st
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ————————————————————————
# Config & style
# ————————————————————————
st.set_page_config(page_title="Discovery Triage Pilot", page_icon="hospital", layout="centered")

st.markdown("""
<style>
    .big-font {font-size:42px !important; font-weight:bold; color:#4B0082;}
    .purple {color:#4B0082;}
    .stButton>button {background:#4B0082; color:white; border-radius:8px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<p class='big-font'>Discovery Triage Pilot</p>", unsafe_allow_html=True)
st.markdown("<p class='purple'>SATS • HealthID • PDF Report</p>", unsafe_allow_html=True)

# ————————————————————————
# Session state
# ————————————————————————
if "history" not in st.session_state: st.session_state.history = []
if "current_patient" not in st.session_state: st.session_state.current_patient = None

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
            patient = mock_patients.get(health_id, {"name": f"Member …{health_id[-4:]}", "age": 35, "sex": "—"})
            patient["health_id"] = health_id
            st.session_state.current_patient = patient
            st.success("Patient loaded")
            st.rerun()

    if st.button("New Patient"):
        st.session_state.current_patient = None
        st.rerun()

    st.divider()
    st.subheader("Recent Patients")
    for e in st.session_state.history[-5:]:
        st.caption(f"{e['name']} • {e['priority']} • {e['time']}")

# ————————————————————————
# Main screen
# ————————————————————————
if not st.session_state.current_patient:
    st.info("Load a patient to start")
    st.stop()

p = st.session_state.current_patient
st.success(f"**Active:** {p['name']} | {p.get('age')}y | {p.get('sex')} | …{p['health_id'][-4:]}")

c1, c2 = st.columns(2)
with c1:
    age = st.number_input("Age", value=p.get("age",35), min_value=0, max_value=120)
    sex = st.radio("Sex", ["Male","Female","Other"], horizontal=True,
                   index=0 if p.get("sex") not in ["Male","Female","Other"] else ["Male","Female","Other"].index(p["sex"]))
with c2:
    mobility = st.selectbox("Mobility", ["Walks unaided","With help","Stretcher / Immobile"])
    resp_rate   = st.slider("RR",5,60,22)
    heart_rate  = st.slider("HR",30,200,88)
    systolic_bp = st.slider("BP",50,250,130)
    temp        = st.slider("Temp °C",30.0,43.0,37.0,0.1)

chief    = st.text_area("Chief Complaint", height=100)
symptoms = st.text_input("Other symptoms")

# ————————————————————————
# SATS calculator
# ————————————————————————
def get_sats():
    s = 0
    if resp_rate > 30 or resp_rate < 9: s += 3
    elif 25 <= resp_rate <= 30 or 9 <= resp_rate <= 10: s += 2
    elif 22 <= resp_rate <= 24 or 11 <= resp_rate <= 14: s += 1

    if heart_rate > 140 or heart_rate < 40: s += 3
    elif heart_rate >= 111: s += 2
    elif heart_rate >= 101: s += 1

    if systolic_bp < 90: s += 3
    if temp >= 38.5 or temp < 35: s += 2
    if mobility == "Stretcher / Immobile": s += 3
    elif mobility == "With help": s += 1
    if any(k in chief.lower() for k in ["unconscious","seizure","not breathing","massive bleed"]): s += 3
    if "chest pain" in chief.lower(): s += 2

    if s >= 10: return "RED",     "#ff1744"
    if s >= 7:  return "ORANGE",  "#ff9100"
    "
    if s >= 4:  return "YELLOW",  "#ffff00"
    return "GREEN", "#00e676"

if st.button("Calculate SATS Priority", type="primary"):
    priority, col = get_sats()
    st.markdown(f"<h1 style='color:{col};text-align:center;'>SATS: {priority}</h1>", unsafe_allow_html=True)
    st.session_state.last_priority = priority
    st.balloons()

# ————————————————————————
# PDF – safe version (no f-strings inside Paragraph)
# ————————————————————————
def make_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("DISCOVERY HEALTH TRIAGE REPORT", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Patient : " + p["name"], styles["Normal"]))
    story.append(Paragraph("HealthID : ending …" + p["health_id"][-4:], styles["Normal"]))
    story.append(Paragraph("Date/Time : " + datetime.now().strftime("%Y-%m-%d %H:%M"), styles["Normal"]))
    story.append(Paragraph("Priority : " + st.session_state.get("last_priority", "—"), styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Chief complaint : " + (chief or "—"), styles["Normal"]))
    story.append(Paragraph("Symptoms : " + (symptoms or "—"), styles["Normal"]))
    story.append(Paragraph(f"Vitals : RR {resp_rate} | HR {heart_rate} | BP {systolic_bp} | Temp {temp}°C", styles["Normal"]))
    story.append(Paragraph("Mobility : " + mobility, styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()

if st.button("Generate & Download PDF Report"):
    if "last_priority" not in st.session_state:
        st.warning("Calculate SATS first")
    else:
        pdf = make_pdf()
        st.download_button(
            label="Download PDF Report",
            data=pdf,
            file_name=f"Triage_{p['name'].replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        st.session_state.history.append({"name": p["name"], "priority": st.session_state.last_priority, "time": datetime.now().strftime("%H:%M")})
        st.success("Report ready!")

st.divider()
st.caption("2025 Discovery Health Internal Pilot • Built in South Africa")
