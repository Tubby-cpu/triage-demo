import streamlit as st
from datetime import datetime
import requests
import base64

# Page config
st.set_page_config(page_title="Discovery Triage Pilot", page_icon="🏥", layout="centered")

st.markdown("""
<style>
    .big-font {font-size:42px !important; font-weight:bold; color:#4B0082;}
    .purple {color:#4B0082;}
    .stButton>button {background:#4B0082; color:white; border-radius:8px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<p class='big-font'>Discovery Triage Pilot</p>", unsafe_allow_html=True)
st.markdown("<p class='purple'>SATS (Manual-Based) • AI Assist • HealthID • Report</p>", unsafe_allow_html=True)

# Session state
if "history" not in st.session_state: st.session_state.history = []
if "patient" not in st.session_state: st.session_state.patient = None

# Sidebar - Patient lookup
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/9/9f/Discovery_Limited_Logo.svg", width=180)
    st.header("Patient Lookup")
    health_id = st.text_input("HealthID / SA ID", placeholder="e.g. 8203155017089")

    if st.button("Load Patient", type="primary"):
        if health_id and len(health_id) >= 10:
            mock = {
                "8203155017089": {"name": "Thabo Mokoena", "age": 42, "sex": "Male"},
                "9112240123456": {"name": "Sarah Naidoo", "age": 31, "sex": "Female"},
                "7509015888088": {"name": "Pieter van der Merwe", "age": 49, "sex": "Male"},
            }
            p = mock.get(health_id, {"name": f"Member …{health_id[-4:]}", "age": 35, "sex": "—"})
            p["health_id"] = health_id
            st.session_state.patient = p
            st.success("Patient loaded")
            st.rerun()
        else:
            st.error("Enter a valid ID")

    if st.button("New Patient"):
        st.session_state.patient = None
        st.rerun()

    st.divider()
    st.subheader("Recent Patients")
    for e in st.session_state.history[-5:]:
        st.caption(f"{e['name']} • {e['priority']} • {e['time']}")

    st.divider()
    groq_key = st.text_input("Groq API Key for AI", type="password")

# Main form
if not st.session_state.patient:
    st.info("Load a patient to begin triage.")
    st.stop()

p = st.session_state.patient
st.success(f"**Active:** {p['name']} | {p.get('age')}y | {p.get('sex')} | …{p['health_id'][-4:]}")

c1, c2 = st.columns(2)
with c1:
    age = st.number_input("Age", value=p.get("age",35), min_value=0, max_value=120)
    sex = st.radio("Sex", ["Male","Female","Other"], horizontal=True, index=0)
with c2:
    mobility = st.selectbox("Mobility", ["Walking","With help","Stretcher / Immobile"])

rr = st.slider("Respiratory Rate (breaths/min)",5,60,12)
hr = st.slider("Heart Rate (bpm)",30,200,80)
bp = st.slider("Systolic BP (mmHg)",50,250,120)
temp = st.slider("Temperature (°C)",30.0,43.0,37.0,0.1)
avpu = st.selectbox("AVPU", ["Alert","Confused","Reacts to Voice","Reacts to Pain","Unresponsive"])
trauma = st.radio("Trauma (injury past 48h)", ["No","Yes"], horizontal=True)

chief = st.text_area("Chief Complaint", height=100)
symptoms = st.text_input("Other symptoms")

# Manual-based TEWS calculation (from SATS manual)
def calculate_tews():
    score = 0
    # Mobility
    if mobility == "Stretcher / Immobile": score += 3
    elif mobility == "With help": score += 1
    # RR
    if rr < 9: score += 3
    elif 9 <= rr <= 11: score += 2
    elif 12 <= rr <= 16: score += 0
    elif 17 <= rr <= 22: score += 1
    elif 23 <= rr <= 30: score += 2
    elif rr > 30: score += 3
    # HR
    if hr < 41: score += 3
    elif 41 <= hr <= 50: score += 2
    elif 51 <= hr <= 90: score += 0
    elif 91 <= hr <= 110: score += 1
    elif 111 <= hr <= 130: score += 2
    elif hr > 130: score += 3
    # SBP
    if bp < 71: score += 3
    elif 71 <= bp <= 80: score += 2
    elif 81 <= bp <= 100: score += 1
    elif 101 <= bp <= 199: score += 0
    elif bp > 199: score += 2
    # Temp
    if temp < 35: score += 2
    elif temp > 38.4: score += 2
    # AVPU
    if avpu == "Confused": score += 1
    elif avpu == "Reacts to Voice": score += 2
    elif avpu == "Reacts to Pain" or avpu == "Unresponsive": score += 3
    # Trauma
    if trauma == "Yes": score += 1
    return score

# Priority from TEWS (manual: 0-2 Green, 3-4 Yellow, 5-6 Orange, 7+ Red)
def get_priority(score):
    if score >= 7: return "RED", "#ff0000"
    elif score >= 5: return "ORANGE", "#ffa500"
    elif score >= 3: return "YELLOW", "#ffff00"
    return "GREEN", "#00ff00"

if st.button("Calculate SATS Priority (Manual TEWS)", type="primary"):
    score = calculate_tews()
    priority, colour = get_priority(score)
    st.markdown(f"<h1 style='color:{colour};text-align:center;'>SATS: {priority} (TEWS: {score})</h1>", unsafe_allow_html=True)
    st.session_state.last_priority = priority
    st.session_state.last_score = score
    st.balloons()

# AI Assist (Groq/Llama with manual rules)
if st.button("AI Analyze (Manual-Based)"):
    if not groq_key:
        st.warning("Enter Groq API Key in sidebar (free at console.groq.com)")
    else:
        with st.spinner("AI analyzing per SATS manual..."):
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                prompt = f"""You are a South African triage nurse using the 2012 SATS manual for adults.

Patient: {age}y {sex}, Mobility: {mobility}, RR: {rr}, HR: {hr}, SBP: {bp}, Temp: {temp}, AVPU: {avpu}, Trauma: {trauma}

Chief complaint: {chief}

Symptoms: {symptoms}

Step 1: Calculate TEWS using this table:
Mobility: Walking=0, Help=1, Stretcher=3
RR: <9=3, 9-11=2, 12-16=0, 17-22=1, 23-30=2, >30=3
HR: <41=3, 41-50=2, 51-90=0, 91-110=1, 111-130=2, >130=3
SBP: <71=3, 71-80=2, 81-100=1, 101-199=0, >199=2
Temp: <35=2, 35-38.4=0, >38.4=2
AVPU: Alert=0, Confused=1, Voice=2, Pain/Unresponsive=3
Trauma: No=0, Yes=1

TEWS score determines minimum priority: 0-2 Green, 3-4 Yellow, 5-6 Orange, 7+ Red

Step 2: Check discriminators from chief/symptoms and upgrade:
Emergency (RED override): Obstructed airway, seizures current, burn facial inhalation, hypoglycaemia <3mmol/L, cardiac arrest

Very urgent (ORANGE min): High energy transfer, focal neurology acute, burn circumferential, shortness of breath acute, aggression, burn chemical, level of consciousness reduced/confused, threatened limb, poisoning/overdose, coughing blood, eye injury, diabetic glucose >11 + ketonuria, chest pain, dislocation larger joint, vomiting fresh blood, stabbed neck, fracture compound, pregnancy + abdominal trauma, haemorrhage uncontrolled, burn >20%, pregnancy + abdominal pain, seizure post ictal, burn electrical, severe pain

Urgent (YELLOW min): Haemorrhage controlled, abdominal pain

Output ONLY: TEWS score: X
Detected discriminators: list or none
Final suggested priority: COLOR - 1-sentence reason"""
                payload = {
                    "model": "llama-3.1-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 200
                }
                response = requests.post(url, headers=headers, json=payload)
                ai_output = response.json()["choices"][0]["message"]["content"]
                st.success(ai_output)
            except:
                st.error("AI error - check key or try again")

# Report (HTML → Print to PDF)
if st.button("Generate & Download Report"):
    if "last_priority" not in st.session_state:
        st.warning("Calculate SATS first")
    else:
        html = f"""
<html>
<body style="font-family:Arial; padding:20px;">
<h1 style="color:#4B0082; text-align:center;">DISCOVERY HEALTH TRIAGE REPORT</h1>
<hr>
<p><b>Patient:</b> {p['name']}</p>
<p><b>HealthID:</b> ending …{p['health_id'][-4:]}</p>
<p><b>Date/Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
<p><b>SATS Priority:</b> {st.session_state.last_priority} (TEWS: {st.session_state.last_score})</p>
<hr>
<p><b>Chief Complaint:</b> {chief or '—'}</p>
<p><b>Symptoms:</b> {symptoms or '—'}</p>
<p><b>Vitals:</b> RR {rr} | HR {hr} | SBP {bp} | Temp {temp}°C</p>
<p><b>Mobility:</b> {mobility}</p>
<p><b>AVPU:</b> {avpu}</p>
<p><b>Trauma:</b> {trauma}</p>
<hr style="border:0;">
<p style="text-align:center; color:#666; font-size:12px;">Discovery Triage Pilot - Internal use only</p>
</body>
</html>
"""
        b64 = base64.b64encode(html.encode()).decode()
        href = f'<a href="data:text/html;base64,{b64}" download="Triage_Report_{p["name"].replace(" ","_")}.html">Download Report (Open & Print to PDF)</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.session_state.history.append({"name": p["name"], "priority": st.session_state.last_priority, "time": datetime.now().strftime("%H:%M")})
        st.success("Report ready!")

st.divider()
st.caption("2025 Discovery Health Internal Pilot • SATS Manual Integrated • Built in South Africa")
