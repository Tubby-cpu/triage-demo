import streamlit as st
from datetime import datetime
import base64

# Page config
st.set_page_config(page_title="QuickTriage SA - Self Triage", page_icon="🏥", layout="wide")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {background: linear-gradient(to bottom, #003366, #66ccff); color: #003366;}
    .big-font {font-size:42px !important; font-weight:bold; color:#003366;}
    .blue {color:#003366;}
    .stButton>button {background:#003366; color:white; border-radius:8px; border: none;}
    .stAlert {border:2px solid #003366; background: rgba(255,255,255,0.8); color:#003366;}
    .stTextInput > div > div > input, .stSlider > div {background:white; color:#003366;}
    .stRadio > label, .stSelectbox > label {color:#003366;}
    
    /* Enhanced card layouts */
    .card {background: white; border-radius:12px; box-shadow:0 4px 8px rgba(0,0,0,0.1); padding:20px; margin-bottom:20px;}
    
    /* Headings dark for readability */
    .stHeader, .stSubheader {color:#003366 !important;}
    
    /* Mobile-responsive adjustments */
    @media (max-width: 600px) {
        .big-font {font-size:30px !important;}
        .stButton>button {width:100%; margin-bottom:10px;}
        .stColumn {flex-direction:column;}
        .stSlider {width:100% !important;}
        .stTextArea > div > textarea {height:100px !important;}
        .stHeader, .stSubheader {text-align:center;}
        [data-testid="stHorizontalBlock"] {flex-direction:column;}
        .card {padding:15px; margin:10px;}
    }
    
    /* Sleek card style for sections */
    .stExpander {background: white; color: #003366; border-radius:12px; box-shadow:0 4px 8px rgba(0,0,0,0.1); padding:15px;}
    .stExpander > label {color:#003366; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

st.markdown("<p class='big-font'>QuickTriage SA</p>", unsafe_allow_html=True)
st.markdown("<p style='color:#003366; font-size:20px;'>Self-Triage for Faster Clinic Care (SATS-Based)</p>", unsafe_allow_html=True)

st.info("Answer questions honestly. This is not medical advice—see a doctor if unsure. For emergencies, call 10177. This app is NHI-compliant, adhering to POPIA for data privacy and supporting universal healthcare access.")

# Session state for question flow
if "step" not in st.session_state: st.session_state.step = 0
if "responses" not in st.session_state: st.session_state.responses = {}
if "is_pediatric" not in st.session_state: st.session_state.is_pediatric = False
if "pediatric_category" not in st.session_state: st.session_state.pediatric_category = None

# Step 0: Basic info
if st.session_state.step == 0:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("Welcome – Let's Start")
        name = st.text_input("Your Name")
        age = st.number_input("Age", min_value=0, max_value=120, value=35)
        sex = st.radio("Sex", ["Male","Female","Other"], horizontal=True)
        health_id = st.text_input("HealthID / SA ID (optional)", placeholder="e.g. 8203155017089")
        height_cm = st.number_input("Height (cm, optional for children)", min_value=0, value=0)  # For pediatric check
        if st.button("Next"):
            is_pediatric = age < 12 or (height_cm > 0 and height_cm < 150)
            pediatric_category = "younger" if height_cm <= 95 else "older" if is_pediatric else None
            st.session_state.is_pediatric = is_pediatric
            st.session_state.pediatric_category = pediatric_category
            st.session_state.responses.update({"name": name, "age": age, "sex": sex, "health_id": health_id, "height_cm": height_cm})
            st.session_state.step = 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Step 1: Chief complaint & symptom discriminators (yes/no flow from manual)
if st.session_state.step == 1:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("Symptoms Check (Yes/No)")
        chief = st.text_area("What is your main problem today? (Chief Complaint)")
        symptoms = st.text_input("Other symptoms?")

        # Emergency discriminators (RED override)
        with st.expander("Emergency Signs 🔴"):
            obstructed_airway = st.radio("Difficulty breathing due to blocked airway?", ["No","Yes"])
            seizure = st.radio("Having a seizure now?", ["No","Yes"])
            facial_burn = st.radio("Facial burn with inhalation injury?", ["No","Yes"])
            low_sugar = st.radio("Low blood sugar (<3mmol/L) if diabetic?", ["No","Yes"])
            cardiac_arrest = st.radio("Cardiac arrest?", ["No","Yes"])
            severe_dehydration = st.radio("Severe dehydration (sunken eyes, lethargic, no urine)?", ["No","Yes"]) if st.session_state.is_pediatric else "No"

        # Very urgent (ORANGE min)
        with st.expander("Very Urgent Signs 🟠"):
            high_energy = st.radio("High-energy injury (e.g., car crash)?", ["No","Yes"])
            focal_neurology = st.radio("Sudden weakness/numbness on one side?", ["No","Yes"])
            burn_circum = st.radio("Circumferential burn?", ["No","Yes"])
            sob_acute = st.radio("Sudden severe shortness of breath?", ["No","Yes"])
            aggression = st.radio("Aggressive behavior?", ["No","Yes"])
            burn_chemical = st.radio("Chemical burn?", ["No","Yes"])
            loc_reduced = st.radio("Reduced consciousness or confusion?", ["No","Yes"])
            threatened_limb = st.radio("Threatened limb (e.g., cold/pulseless)?", ["No","Yes"])
            poisoning = st.radio("Poisoning or overdose?", ["No","Yes"])
            coughing_blood = st.radio("Coughing up blood?", ["No","Yes"])
            eye_injury = st.radio("Eye injury?", ["No","Yes"])
            diabetic_high = st.radio("Diabetic with glucose >11mmol/L + ketones?", ["No","Yes"])
            chest_pain = st.radio("Severe chest pain?", ["No","Yes"])
            dislocation = st.radio("Dislocated large joint?", ["No","Yes"])
            vomiting_blood = st.radio("Vomiting fresh blood?", ["No","Yes"])
            stabbed_neck = st.radio("Stabbed in neck?", ["No","Yes"])
            fracture_compound = st.radio("Open fracture?", ["No","Yes"])
            preg_abd_trauma = st.radio("Pregnant with abdominal trauma?", ["No","Yes"])
            haemorrhage_unc = st.radio("Uncontrolled bleeding?", ["No","Yes"])
            burn_large = st.radio("Burn >20% body?", ["No","Yes"])
            preg_abd_pain = st.radio("Pregnant with abdominal pain?", ["No","Yes"])
            seizure_post = st.radio("Post-seizure state?", ["No","Yes"])
            burn_electrical = st.radio("Electrical burn?", ["No","Yes"])
            severe_pain = st.radio("Severe pain?", ["No","Yes"])
            moderate_dehydration = st.radio("Moderate dehydration (restless, thirsty)?", ["No","Yes"]) if st.session_state.is_pediatric else "No"

        # Urgent (YELLOW min)
        with st.expander("Urgent Signs 🟡"):
            haemorrhage_con = st.radio("Controlled bleeding?", ["No","Yes"])
            abd_pain = st.radio("Abdominal pain?", ["No","Yes"])

        if st.button("Next to Vitals"):
            st.session_state.responses.update({
                "chief": chief, "symptoms": symptoms,
                "emergency": any([obstructed_airway=="Yes", seizure=="Yes", facial_burn=="Yes", low_sugar=="Yes", cardiac_arrest=="Yes", severe_dehydration=="Yes"]),
                "very_urgent": any([high_energy=="Yes", focal_neurology=="Yes", burn_circum=="Yes", sob_acute=="Yes", aggression=="Yes", burn_chemical=="Yes", loc_reduced=="Yes", threatened_limb=="Yes", poisoning=="Yes", coughing_blood=="Yes", eye_injury=="Yes", diabetic_high=="Yes", chest_pain=="Yes", dislocation=="Yes", vomiting_blood=="Yes", stabbed_neck=="Yes", fracture_compound=="Yes", preg_abd_trauma=="Yes", haemorrhage_unc=="Yes", burn_large=="Yes", preg_abd_pain=="Yes", seizure_post=="Yes", burn_electrical=="Yes", severe_pain=="Yes", moderate_dehydration=="Yes"]),
                "urgent": any([haemorrhage_con=="Yes", abd_pain=="Yes"])
            })
            st.session_state.step = 2
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Step 2: Vitals
if st.session_state.step == 2:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.header("Vitals (Measure if possible)")
        rr = st.number_input("Respiratory Rate (breaths/min - count for 1 min)", min_value=0, value=12)
        hr = st.number_input("Heart Rate (bpm - feel pulse for 1 min)", min_value=0, value=80)
        bp = st.number_input("Systolic BP (mmHg - if you have a monitor)", min_value=0, value=120)
        temp = st.number_input("Temperature (°C - if you have a thermometer)", min_value=30.0, max_value=43.0, value=37.0)
        avpu = st.selectbox("AVPU (how alert are you?)", ["Alert","Confused","Reacts to Voice","Reacts to Pain","Unresponsive"])
        trauma = st.radio("Trauma (injury in past 48h)?", ["No","Yes"], horizontal=True)

        if st.button("Calculate Priority"):
            st.session_state.responses.update({"rr": rr, "hr": hr, "bp": bp, "temp": temp, "avpu": avpu, "trauma": trauma})
            st.session_state.step = 3
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Step 3: Compute & Show Priority
if st.session_state.step == 3:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        r = st.session_state.responses

        # TEWS calculation - Pediatric logic
        score = 0
        mobility = st.selectbox("Mobility (how did you arrive?)", ["Walking","With help","Stretcher / Immobile"])
        if mobility == "Stretcher / Immobile": score += 3
        elif mobility == "With help": score += 1

        if st.session_state.is_pediatric:
            if st.session_state.pediatric_category == "younger":  # 50-95cm
                # RR younger
                if r["rr"] < 10 or r["rr"] > 60: score += 3
                elif 10 <= r["rr"] <= 14 or 51 <= r["rr"] <= 59: score += 2
                elif 15 <= r["rr"] <= 20 or 41 <= r["rr"] <= 50: score += 1
                elif 21 <= r["rr"] <= 40: score += 0
                # HR younger
                if r["hr"] < 60 or r["hr"] > 180: score += 3
                elif 60 <= r["hr"] <= 79 or 161 <= r["hr"] <= 179: score += 2
                elif 80 <= r["hr"] <= 99 or 141 <= r["hr"] <= 160: score += 1
                elif 100 <= r["hr"] <= 140: score += 0
                # SBP younger
                if r["bp"] < 50: score += 3
                elif 50 <= r["bp"] <= 59: score += 2
                elif 60 <= r["bp"] <= 69: score += 1
                elif 70 <= r["bp"] <= 94: score += 0
                elif r["bp"] > 94: score += 2
            else:  # older 96-150cm
                # RR older
                if r["rr"] < 9 or r["rr"] > 30: score += 3
                elif 9 <= r["rr"] <= 11 or 23 <= r["rr"] <= 30: score += 2
                elif 12 <= r["rr"] <= 16: score += 0
                elif 17 <= r["rr"] <= 22: score += 1
                # HR older
                if r["hr"] < 41 or r["hr"] > 130: score += 3
                elif 41 <= r["hr"] <= 50 or 111 <= r["hr"] <= 130: score += 2
                elif 51 <= r["hr"] <= 90: score += 0
                elif 91 <= r["hr"] <= 110: score += 1
                # SBP older
                if r["bp"] < 71: score += 3
                elif 71 <= r["bp"] <= 80: score += 2
                elif 81 <= r["bp"] <= 100: score += 1
                elif 101 <= r["bp"] <= 199: score += 0
                elif r["bp"] > 199: score += 2
        else:  # Adult TEWS (original)
            if r["rr"] < 9: score += 3
            elif 9 <= r["rr"] <= 11: score += 2
            elif 12 <= r["rr"] <= 16: score += 0
            elif 17 <= r["rr"] <= 22: score += 1
            elif 23 <= r["rr"] <= 30: score += 2
            elif r["rr"] > 30: score += 3
            if r["hr"] < 41: score += 3
            elif 41 <= r["hr"] <= 50: score += 2
            elif 51 <= r["hr"] <= 90: score += 0
            elif 91 <= r["hr"] <= 110: score += 1
            elif 111 <= r["hr"] <= 130: score += 2
            elif r["hr"] > 130: score += 3
            if r["bp"] < 71: score += 3
            elif 71 <= r["bp"] <= 80: score += 2
            elif 81 <= r["bp"] <= 100: score += 1
            elif 101 <= r["bp"] <= 199: score += 0
            elif r["bp"] > 199: score += 2

        # Common: Temp, AVPU, Trauma
        if r["temp"] < 35: score += 2
        elif r["temp"] > 38.4: score += 2
        if r["avpu"] == "Confused": score += 1
        elif r["avpu"] == "Reacts to Voice": score += 2
        elif r["avpu"] in ["Reacts to Pain","Unresponsive"]: score += 3
        if r["trauma"] == "Yes": score += 1

        # Base priority from TEWS
        if score >= 7: priority = "RED"
        elif score >= 5: priority = "ORANGE"
        elif score >= 3: priority = "YELLOW"
        else: priority = "GREEN"

        # Upgrade per discriminators
        if r["emergency"]:
            priority = "RED"
        elif r["very_urgent"] and priority not in ["RED"]:
            priority = "ORANGE"
        elif r["urgent"] and priority == "GREEN":
            priority = "YELLOW"

        st.header("Your Triage Priority")
        colour = {"RED":"#ff0000", "ORANGE":"#ffa500", "YELLOW":"#ffff00", "GREEN":"#00ff00"}[priority]
        st.markdown(f"<h1 style='color:{colour};text-align:center;'>{priority}</h1>", unsafe_allow_html=True)

        if priority == "GREEN":
            st.success("Non-urgent – Nurse alerted. You can leave if feeling ok. See a GP or clinic later.")
            # Mock nurse alert
            st.info("ALERT SENT TO NURSE: Patient {r['name']} green-coded, safe to leave.")
        else:
            st.warning(f"{priority} - Please stay and see the doctor soon.")

        # Report
        html = f"""
<html>
<body style="font-family:Arial; padding:20px;">
<h1 style="color:#4B0082; text-align:center;">QUICKTRIAGE REPORT</h1>
<hr>
<p><b>Patient:</b> {r['name']}</p>
<p><b>HealthID:</b> {r['health_id'] or '—'}</p>
<p><b>Priority:</b> {priority} (TEWS: {score})</p>
<p><b>Chief:</b> {r['chief'] or '—'}</p>
<p><b>Symptoms:</b> {r['symptoms'] or '—'}</p>
<p><b>Vitals:</b> RR {r['rr']} | HR {r['hr']} | BP {r['bp']} | Temp {r['temp']}°C</p>
<p><b>Mobility:</b> {mobility}</p>
<p><b>AVPU:</b> {r['avpu']}</p>
<p><b>Trauma:</b> {r['trauma']}</p>
</body>
</html>
"""
        b64 = base64.b64encode(html.encode()).decode()
        st.markdown(f'<a href="data:text/html;base64,{b64}" download="Triage_Report.html">Download Report</a>', unsafe_allow_html=True)

        if st.button("Finish"):
            st.session_state.history.append({"name": r['name'], "priority": priority, "time": datetime.now().strftime("%H:%M")})
            st.session_state.patient = None
            st.session_state.step = 0
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("QuickTriage SA – Reducing Clinic Waits • SATS Manual Compliant • 2025 Demo")
