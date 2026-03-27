import streamlit as st
import os
import time
import smtplib
import random
import re
import requests
from email.message import EmailMessage
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Initialize Streamlit configuration
st.set_page_config(page_title="MyMedico Assistant", layout="wide", page_icon="⚕️")

# Configure APIs
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# ===============================
# SESSION STATE INITIALIZATION
# ===============================
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'logged_in_email' not in st.session_state:
    st.session_state.logged_in_email = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

if 'patient_info' not in st.session_state:
    st.session_state.patient_info = {
        "Name": "", "Age": 0, "Gender": "Male", "Weight": 0.0, "Blood Group": "O+"
    }
if 'symptoms' not in st.session_state:
    st.session_state.symptoms = ""
if 'specialist_suggested' not in st.session_state:
    st.session_state.specialist_suggested = ""

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'notifications' not in st.session_state:
    st.session_state.notifications = []
if 'appointments' not in st.session_state:
    st.session_state.appointments = []

if 'auth_state' not in st.session_state:
    st.session_state.auth_state = {
        "login_step": 1,
        "login_email": "",
        "login_otp": "",
        "signup_step": 1,
        "signup_email": "",
        "signup_pwd": "",
        "signup_role": "",
        "signup_otp": ""
    }

if 'doctors_schedule' not in st.session_state:
    st.session_state.doctors_schedule = [
        {"hospital": "City Care Hospital", "doctor": "Dr. Sarah Smith", "specialist": "Cardiologist", "time": "09:00 AM - 01:00 PM"},
        {"hospital": "City Care Hospital", "doctor": "Dr. John Doe", "specialist": "Neurologist", "time": "10:00 AM - 03:00 PM"},
        {"hospital": "Metro Health", "doctor": "Dr. Alice Brown", "specialist": "ENT", "time": "11:00 AM - 04:00 PM"},
        {"hospital": "Metro Health", "doctor": "Dr. Bob White", "specialist": "General Physician", "time": "08:00 AM - 12:00 PM"}
    ]

# ===============================
# HELPER FUNCTIONS
# ===============================
def firebase_login(email, password):
    if not FIREBASE_API_KEY:
        return False, "FIREBASE_API_KEY not found in .env"
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return True, response.json()
    else:
        return False, response.json().get("error", {}).get("message", "Login failed")

def firebase_signup(email, password):
    if not FIREBASE_API_KEY:
        return False, "FIREBASE_API_KEY not found in .env"
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return True, response.json()
    else:
        return False, response.json().get("error", {}).get("message", "Signup failed")

def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None

def send_otp_email(receiver_email, otp, purpose="Login"):
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    
    if not sender_email or not sender_password:
        return False, "SMTP_EMAIL or SMTP_PASSWORD not found in .env"
        
    msg = EmailMessage()
    msg.set_content(f"Your {purpose} OTP code for MyMedico Assistant is: {otp}")
    msg['Subject'] = f"{purpose} OTP Verification - MyMedico"
    msg['From'] = f"MyMedico <{sender_email}>"
    msg['To'] = receiver_email
    
    try:
        # Using Gmail SMTP by default, can be customized
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"DEBUG: Successfully sent OTP {otp} to {receiver_email}")
        return True, "Email sent successfully"
    except Exception as e:
        print(f"DEBUG Error sending email: {e}")
        return False, str(e)

def analyze_symptoms_for_specialist(symptoms):
    if not API_KEY:
        return 'General Physician'
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Based on the following symptoms, suggest the single most appropriate medical specialist from this list: [Cardiologist, Neurologist, ENT, Dermatologist, General Physician, Orthopedic]. Output ONLY the specialist name. Symptoms: {symptoms}"
        response = model.generate_content(prompt)
        text = response.text.replace('\n', '').strip()
        # Clean up response if it contains extra text
        for spec in ["Cardiologist", "Neurologist", "ENT", "Dermatologist", "General Physician", "Orthopedic"]:
            if spec.lower() in text.lower():
                return spec
        return text
    except Exception as e:
        return 'General Physician'

def get_doctors_by_specialist(specialist):
    return [d for d in st.session_state.doctors_schedule if d['specialist'].lower() == specialist.lower()]

# ===============================
# UI RENDER - MAIN APPLICATION
# ===============================
if not st.session_state.logged_in_email:
    # First interface for login/signup
    st.title("Welcome to MyMedico Assistant ⚕️")
    st.subheader("Please Login or Sign Up to continue")
    
    auth_tab1, auth_tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with auth_tab1:
        if st.session_state.auth_state["login_step"] == 1:
            with st.form("login_form"):
                login_email = st.text_input("Email")
                login_pwd = st.text_input("Password", type="password")
                submitted_login = st.form_submit_button("Send Login Code")
                if submitted_login:
                    if not is_valid_email(login_email):
                        st.error("Please enter a valid email address.")
                    else:
                        fb_success, fb_msg = firebase_login(login_email, login_pwd)
                        if fb_success:
                            otp = str(random.randint(100000, 999999))
                            success, msg = send_otp_email(login_email, otp, "Login")
                            
                            st.session_state.auth_state["login_email"] = login_email
                            st.session_state.auth_state["login_otp"] = otp
                            st.session_state.auth_state["login_step"] = 2
                            
                            if success:
                                st.success(f"OTP sent to {login_email}")
                            else:
                                st.warning(f"Could not send email ({msg}). FOR TESTING ONLY, OTP is: {otp}")
                            st.rerun()
                        else:
                            st.error(f"Firebase Auth Error: {fb_msg}")
        else:
            with st.form("login_otp_form"):
                st.info(f"An OTP was sent to {st.session_state.auth_state['login_email']}")
                otp_input = st.text_input("Enter 6-digit OTP")
                submit_otp = st.form_submit_button("Verify & Login")
                
                if submit_otp:
                    if otp_input == st.session_state.auth_state["login_otp"]:
                        email = st.session_state.auth_state["login_email"]
                        st.session_state.logged_in_email = email
                        
                        # Fallback to Patient if role is not found
                        role = "Patient"
                        if email in st.session_state.users:
                            role = st.session_state.users[email].get("role", "Patient")
                        
                        st.session_state.user_role = role
                        st.session_state.auth_state["login_step"] = 1 # Reset
                        st.success("Logged in successfully via Firebase!")
                        st.rerun()
                    else:
                        st.error("Invalid OTP.")
            
            if st.button("Cancel & Go Back", key="cancel_login"):
                st.session_state.auth_state["login_step"] = 1
                st.rerun()
                    
    with auth_tab2:
        if st.session_state.auth_state["signup_step"] == 1:
            with st.form("signup_form"):
                signup_email = st.text_input("Email")
                signup_pwd = st.text_input("Password", type="password")
                signup_role = st.selectbox("I am a:", ["Patient", "Hospital"])
                submitted_signup = st.form_submit_button("Send Signup Code")
                if submitted_signup:
                    if not is_valid_email(signup_email):
                        st.error("Please enter a valid email address.")
                    elif signup_email and signup_pwd:
                        # We will actually create the Firebase user AFTER OTP validation
                        otp = str(random.randint(100000, 999999))
                        success, msg = send_otp_email(signup_email, otp, "Signup")
                        
                        st.session_state.auth_state["signup_email"] = signup_email
                        st.session_state.auth_state["signup_pwd"] = signup_pwd
                        st.session_state.auth_state["signup_role"] = signup_role
                        st.session_state.auth_state["signup_otp"] = otp
                        st.session_state.auth_state["signup_step"] = 2
                        
                        if success:
                            st.success(f"OTP sent to {signup_email}")
                        else:
                            st.warning(f"Could not send email ({msg}). FOR TESTING ONLY, OTP is: {otp}")
                        st.rerun()
                    else:
                        st.error("Please fill in all fields.")
        else:
            with st.form("signup_otp_form"):
                st.info(f"An OTP was sent to {st.session_state.auth_state['signup_email']}")
                otp_input = st.text_input("Enter 6-digit OTP")
                submit_otp = st.form_submit_button("Verify & Sign Up")
                
                if submit_otp:
                    if otp_input == st.session_state.auth_state["signup_otp"]:
                        email = st.session_state.auth_state["signup_email"]
                        pwd = st.session_state.auth_state["signup_pwd"]
                        
                        st.info("Registering with Firebase...")
                        fb_success, fb_msg = firebase_signup(email, pwd)
                        if fb_success:
                            st.session_state.users[email] = {
                                "role": st.session_state.auth_state["signup_role"]
                            }
                            st.session_state.auth_state["signup_step"] = 1 # Reset
                            st.success("Account created successfully in Firebase! Please login using the Login tab.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Firebase Signup Error: {fb_msg}")
                    else:
                        st.error("Invalid OTP.")
                        
            if st.button("Cancel & Go Back", key="cancel_signup"):
                st.session_state.auth_state["signup_step"] = 1
                st.rerun()
                    
    st.stop() # Hide the rest of the application until authenticated

# Sidebar Navigation once logged in
st.sidebar.title("⚕️ MyMedico Navigation")
st.sidebar.markdown(f"**Logged in as:** {st.session_state.logged_in_email}")
st.sidebar.markdown(f"**Role:** {st.session_state.user_role}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in_email = None
    st.session_state.user_role = None
    st.rerun()

st.sidebar.divider()

if st.session_state.user_role == "Patient":
    domain = st.sidebar.radio("Select Domain", ["Patient Domain", "Hospital Domain"], index=0)
else:
    domain = st.sidebar.radio("Select Domain", ["Patient Domain", "Hospital Domain"], index=1)

if domain == "Patient Domain":
    if st.session_state.user_role != "Patient":
        st.error("❌ You do not have access to the Patient Domain.")
        st.stop()
        
    st.sidebar.subheader("🏥 Patient Navigation")
    patient_nav = st.sidebar.radio(
        "Pages", 
        ["Preliminary Info", "Symptoms", "Specialist Consult", "Appointments", "Smith AI"]
    )
    
    st.title("Patient Portal 🏥")
    st.divider()

    if patient_nav == "Preliminary Info":
        st.header("📋 Preliminary Information")
        with st.form("info_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Name", st.session_state.patient_info["Name"])
            age = col2.number_input("Age", min_value=0, max_value=120, value=st.session_state.patient_info.get("Age", 0))
            gender = col1.selectbox("Gender", ["Male", "Female", "Other"])
            weight = col2.number_input("Weight (kg)", min_value=0.0, max_value=300.0, value=float(st.session_state.patient_info.get("Weight", 0.0)))
            blood_group = col1.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
            
            submitted = st.form_submit_button("Save Info")
            if submitted:
                st.session_state.patient_info = {
                    "Name": name, "Age": age, "Gender": gender, "Weight": weight, "Blood Group": blood_group
                }
                st.success("Information saved!")
                
        st.divider()
        st.subheader("Your Profile Summary")
        cols = st.columns(5)
        cols[0].metric("Name", st.session_state.patient_info["Name"] or "N/A")
        cols[1].metric("Age", f"{st.session_state.patient_info['Age']} yrs")
        cols[2].metric("Gender", st.session_state.patient_info["Gender"] or "N/A")
        cols[3].metric("Weight", f"{st.session_state.patient_info['Weight']} kg")
        cols[4].metric("Blood Group", st.session_state.patient_info["Blood Group"] or "N/A")

    elif patient_nav == "Symptoms":
        st.header("🩺 Symptoms")
        st.write("Please describe your symptoms in detail below.")
        symptoms_input = st.text_area("Your Symptoms", st.session_state.symptoms, height=150)
        if st.button("Submit Symptoms"):
            if symptoms_input:
                st.session_state.symptoms = symptoms_input
                st.success("Symptoms recorded successfully!")
            else:
                st.error("Please enter your symptoms.")
                
        if st.session_state.symptoms:
            st.divider()
            st.subheader("Recorded Symptoms Summary")
            st.metric(label="Current Logged Symptoms :warning:", value=st.session_state.symptoms[:50] + "..." if len(st.session_state.symptoms) > 50 else st.session_state.symptoms)
            st.info(f"Full Record: {st.session_state.symptoms}")

    elif patient_nav == "Specialist Consult":
        st.header("👨‍⚕️ Specialist Recommendation")
        if st.session_state.symptoms:
            st.info(f"**Your Recorded Symptoms:** {st.session_state.symptoms}")
            if st.button("Analyze & Suggest Specialist (AI Powered)", type="primary"):
                with st.spinner("Smith AI is analyzing your symptoms..."):
                    specialist = analyze_symptoms_for_specialist(st.session_state.symptoms)
                    st.session_state.specialist_suggested = specialist
                
            if st.session_state.specialist_suggested:
                st.success(f"Based on AI analysis of your symptoms, we strongly recommend consulting a **{st.session_state.specialist_suggested}**.")
        else:
            st.warning("Please record your symptoms in the 'Symptoms' page first.")

    elif patient_nav == "Appointments":
        st.header("📅 Book an Appointment")
        if st.session_state.specialist_suggested:
            st.markdown(f"#### Viewing Schedules for Specialist: **{st.session_state.specialist_suggested}**")
            doctors = get_doctors_by_specialist(st.session_state.specialist_suggested)
            
            if doctors:
                st.write("### Recommended Doctors")
                for i, doc in enumerate(doctors):
                    with st.container():
                        col1, col2 = st.columns([7, 3])
                        with col1:
                            st.info(f"**{doc['doctor']}** - {doc['hospital']} | Time: {doc['time']}")
                        with col2:
                            if st.button(f"Book Appointment", key=f"book_{i}", use_container_width=True):
                                appt_details = {
                                    "id": str(time.time()),
                                    "patient": st.session_state.patient_info["Name"] or st.session_state.logged_in_email,
                                    "patient_email": st.session_state.logged_in_email,
                                    "doctor": doc['doctor'],
                                    "hospital": doc['hospital'],
                                    "time": doc['time'],
                                    "status": "Pending"
                                }
                                st.session_state.appointments.append(appt_details)
                                
                                notification_msg = f"New Appointment Alert: {appt_details['patient']} booked {doc['doctor']}."
                                st.session_state.notifications.append(notification_msg)
                                
                                st.success(f"Appointment request sent for {doc['doctor']} on {doc['time']}. Please wait for confirmation.")
                                st.balloons()
            else:
                st.warning("No doctors found for this specialization in the current schedule.")
        else:
            st.warning("Please get a specialist recommendation first.")
            
        st.divider()
        st.write("### Your Medical Appointments")
        my_appointments = [a for a in st.session_state.appointments if a.get("patient_email") == st.session_state.logged_in_email]
        if my_appointments:
            for appt in my_appointments:
                if appt["status"] == "Accepted":
                    st.success(f"**{appt['doctor']}** at {appt['hospital']} | Time: {appt['time']} | Status: ✅ **{appt['status']}**")
                elif appt["status"] == "Rejected":
                    st.error(f"**{appt['doctor']}** at {appt['hospital']} | Time: {appt['time']} | Status: ❌ **{appt['status']}**")
                else:
                    st.warning(f"**{appt['doctor']}** at {appt['hospital']} | Time: {appt['time']} | Status: ⏳ **{appt['status']}**")
        else:
            st.info("You have no appointments booked yet.")
            
    elif patient_nav == "Smith AI":
        st.header("🤖 Ask Smith AI")
        st.caption("Your intelligent medical assistant powered by Google Gemini.")
        
        if not API_KEY:
            st.error("Google Gemini API Key not found. Please add GEMINI_API_KEY to your .env file.")
        else:
            col1, col2, col3 = st.columns([1, 1, 6])
            with col1:
                if st.button("🧹 Clear Chat"):
                    st.session_state.chat_history = []
                    st.rerun()
            with col2:
                if st.button("💾 Save Chat"):
                    chat_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.chat_history])
                    st.download_button(label="Download", data=chat_text, file_name="smith_ai_chat.txt", mime="text/plain")

            st.write("### Quick Prompts")
            q_col1, q_col2, q_col3 = st.columns(3)
            
            prompt = st.chat_input("Message Smith AI...")

            if q_col1.button("How to maintain a healthy heart?"):
                prompt = "How to maintain a healthy heart?"
            if q_col2.button("Home remedies for a mild cough?"):
                prompt = "Can you suggest some home remedies for a mild cough?"
            if q_col3.button("Analyze my previous symptoms"):
                symptoms = st.session_state.symptoms if st.session_state.symptoms else "No symptoms recorded."
                prompt = f"Analyze my symptoms: {symptoms} and suggest lifestyle advice."

            st.divider()
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt:
                patient_info_str = f"Patient Info: Name: {st.session_state.patient_info['Name']}, Age: {st.session_state.patient_info['Age']}, Gender: {st.session_state.patient_info['Gender']}, Blood Group: {st.session_state.patient_info['Blood Group']}. Symptoms from page 2: {st.session_state.symptoms}"
                system_instruction = f"You are Smith AI, an expert medical assistant. You provide safe and accurate health responses and are aware of the medical domain well. The patient context is: {patient_info_str}. ALWAYS add a disclaimer that you are an AI and they should consult a real doctor. Patient says: {prompt}"

                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Smith AI is typing..."):
                        try:
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            response = model.generate_content(system_instruction)
                            st.markdown(response.text)
                            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                        except Exception as e:
                            st.error(f"Error communicating with AI: {e}")

elif domain == "Hospital Domain":
    if st.session_state.user_role != "Hospital":
        st.error("❌ You do not have access to the Hospital Domain.")
        st.stop()
        
    col_nav, col_notif = st.columns([8, 2])
    
    with col_notif:
        st.markdown(f"**🔔 Notifications ({len(st.session_state.notifications)})**")
        with st.expander("View Inbox"):
            if st.session_state.notifications:
                for n in reversed(st.session_state.notifications):
                    st.warning(n)
                if st.button("Clear Notifications"):
                    st.session_state.notifications = []
                    st.rerun()
            else:
                st.write("No new notifications.")

    st.title("Hospital Portal 🏢")
    
    tab1, tab2 = st.tabs(["📝 View & Manage Appointments", "🩺 Doctors Schedule"])
    
    with tab1:
        st.header("Manage Appointment Applications")
        pending_appts = [a for a in st.session_state.appointments if a["status"] == "Pending"]
        
        if pending_appts:
            for appt in pending_appts:
                with st.container():
                    st.markdown(f"**Patient:** {appt['patient']} &emsp;|&emsp; **Doctor:** {appt['doctor']} &emsp;|&emsp; **Time:** {appt['time']}")
                    col_acc, col_rej, _ = st.columns([1, 1, 6])
                    with col_acc:
                        if st.button("Accept", key=f"acc_{appt['id']}", type="primary"):
                            appt["status"] = "Accepted"
                            st.session_state.notifications.append(f"Accepted appointment for {appt['patient']} with {appt['doctor']}.")
                            st.rerun()
                    with col_rej:
                        if st.button("Reject", key=f"rej_{appt['id']}"):
                            appt["status"] = "Rejected"
                            st.session_state.notifications.append(f"Rejected appointment for {appt['patient']} with {appt['doctor']}.")
                            st.rerun()
                    st.divider()
        else:
            st.info("✅ No pending appointment requests.")
            
        st.subheader("Recent Applications (Accepted/Rejected)")
        history_appts = [a for a in st.session_state.appointments if a["status"] != "Pending"]
        if history_appts:
            for appt in reversed(history_appts):
                status_icon = "✅ Accepted" if appt["status"] == "Accepted" else "❌ Rejected"
                st.write(f"- {appt['patient']} with {appt['doctor']} on {appt['time']} -> **{status_icon}**")

    with tab2:
        st.header("Manage Doctors Schedule")
        st.write("### Current Active Schedule")
        st.dataframe(st.session_state.doctors_schedule, use_container_width=True)
        
        st.divider()
        st.subheader("Add / Update Doctor Availability")
        with st.form("add_doctor"):
            col_a, col_b = st.columns(2)
            doc_hosp = col_a.text_input("Hospital Name", "City Care Hospital")
            doc_name = col_b.text_input("Doctor's Name", "Dr. ")
            doc_spec = col_a.selectbox("Specialization", ["Cardiologist", "Neurologist", "ENT", "Dermatologist", "General Physician", "Orthopedic"])
            doc_time = col_b.text_input("Available Time (e.g. 10:00 AM - 02:00 PM)")
            
            if st.form_submit_button("Add to Schedule", type="primary"):
                if doc_name and doc_hosp and doc_time:
                    st.session_state.doctors_schedule.append({
                        "hospital": doc_hosp,
                        "doctor": doc_name,
                        "specialist": doc_spec,
                        "time": doc_time
                    })
                    st.success(f"Successfully added Dr. {doc_name} to the schedule.")
                    st.rerun()
                else:
                    st.error("Please fill all required fields.")
