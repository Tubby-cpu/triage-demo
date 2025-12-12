import streamlit as st
from datetime import datetime

# ————————————————————————
# Page setup
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
st.markdown("<p class='purple'>SATS • HealthID • Instant PDF (no extra packages)</p>", unsafe_allow_html=True)

# ————————————————————————
# Session state
# ————————————————————————
if "history" not in st.session_state: st.session_state.history = []
if "patient" not in st.session_state: st.session_state.patient = None

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
                "7509015888088":    {"name": "Pieter van der Merwe","age": 49, "sex": "Male"},
            }
            p = mock.get(health_id, {"name": f"Member …{health_id[-4:]}", "age": 35, "sex": "—"})
            p["health_id"] = health_id
            st.session_state.patient = p
            st.success("Patient loaded")
            st.rerun()

    if st.button("New Patient"):
        st.session_state.patient = None
        st.rerun()

    st.divider()
    st.subheader("Recent Patients")
    for e in st.session_state.history[-5:]:
        st.caption(f"{e['name']} • {e['priority']} • {e['time']}")

# ————————————————————————
# Main form
# ————————————————————————
if not st.session_state.patient:
    st.info("Load a patient to start triage.")
    st.stop()

p = st.session_state.patient
st.success(f"**Active:** {p['name']} | {p.get('age')}y | {p.get('sex')} | …{p['health_id'][-4:]}")

c1, c2 = st.columns(2)
with c1:
    age = st.number_input("Age", value=p.get("age",35), min_value=0, max_value=120)
    sex = st.radio("Sex", ["Male","Female","Other"], horizontal=True,
                   index=0 if p.get("sex") not in ["Male","Female","Other"] else 0)
with c2:
    mobility = st.selectbox("Mobility", ["Walks unaided","With help","Stretcher / Immobile"])
    rr = st.slider("Respiratory Rate",5,60,22)
    hr = st.slider("Heart Rate",30,200,88)
    bp = st.slider("Systolic BP",50,250,130)
    temp = st.slider("Temperature °C",30.0,43.0,37.0,0.1)

chief = st.text_area("Chief Complaint", height=100)
symptoms = st.text_input("Other symptoms")

# ————————————————————————
# SATS
# ————————————————————————
def sats():
    s = 0
    if rr > 30 or rr < 9: s += 3
    elif rr >= 25 or rr <= 10: s += 2
    elif rr >= 22 or rr <= 11: s += 1
    if hr > 140 or hr < 40: s += 3
    elif hr >= 111: s += 2
    elif hr >= 101: s += 1
    if bp < 90: s += 3
    if temp >= 38.5 or temp < 35: s += 2
    if mobility == "Stretcher / Immobile": s += 3
    elif mobility == "With help": s += 1
    if any(k in chief.lower() for k in ["unconscious","seizure","not breathing","massive bleed"]): s += 3
    if "chest pain" in chief.lower(): s += 2

    if s >= 10: return "RED",     "#ff1744"
    if s >= 7:  return "ORANGE",  "#ff9100"
    if s >= 4:  return "YELLOW",  "#ffff00"
    return "GREEN", "#00e676"

if st.button("Calculate SATS Priority", type="primary"):
    priority, col = sats()
    st.markdown(f"<h1 style='color:{col};text-align:center;'>SATS: {priority}</h1>", unsafe_allow_html=True)
    st.session_state.last_priority = priority
    st.balloons()

# ————————————————————————
# PDF using only built-in Python (base64 HTML → PDF-like download)
# ————————————————————————
if st.button("Generate & Download PDF Report"):
    if "last_priority" not in st.session_state:
        st.warning("Calculate SATS first")
    else:
        html = f"""
        <html>
        <head><title>Discovery Triage Report</title></head>
        <body style="font-family:Arial; margin:40px;">
        <h1 style="color:#4B0082; text-align:center;">DISCOVERY HEALTH TRIAGE REPORT</h1>
        <hr>
        <p><b>Patient</b>: {p['name']}</p>
        <p><b>HealthID</b>: ending …{p['health_id'][-4:]}</p>
        <p><b>Date & Time</b>: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <p><b>SATS Priority</b>: {st.session_state.last_priority}</p>
        <hr>
        <p><b>Chief complaint</b>: {chief or "—"}</p>
        <p><b>Symptoms</b>: {symptoms or "—"}</p>
        <p><b>Vitals</b>: RR {rr} | HR {hr} | BP {bp} | Temp {temp}°C</p>
        <p><b>Mobility</b>: {mobility}</p>
        <br><br>
        <p style="text-align:center; color:#666; font-size:12px;">Discovery Health Triage Pilot – Internal use only</p>
        </body>
        </html>
        """
        import base64
        b64 = base64.b64encode(html.encode()).decode()
        href = f'<a href="data:text/html;base64,{b64}" download="Triage_Report_{p["name"].replace(" ","_")}.html">Download Report (open in browser → Print → Save as PDF)</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.session_state.history.append({"name": p["name"], "priority": st.session_state.last_priority, "time": datetime.now().strftime("%H:%M")})
        st.success("Report ready – click link above")

st.divider()
st.caption("2025 Discovery Health Internal Pilot • Built in South Africa • No external packages")
