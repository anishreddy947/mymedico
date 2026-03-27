import sys
import re

file_path = 'app.py'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Import chunk
    c1_old = '''import streamlit as st
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai'''
    c1_new = '''import streamlit as st
import os
import time
import smtplib
import random
import re
from email.message import EmailMessage
from dotenv import load_dotenv
import google.generativeai as genai'''
    content = content.replace(c1_old, c1_new)

    # Session state chunk
    c2_old = '''if 'appointments' not in st.session_state:
    st.session_state.appointments = []

if 'doctors_schedule' not in st.session_state:'''
    c2_new = '''if 'appointments' not in st.session_state:
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

if 'doctors_schedule' not in st.session_state:'''
    content = content.replace(c2_old, c2_new)

    # Helper functions chunk
    c3_old = '''# ===============================
# HELPER FUNCTIONS
# ===============================
def analyze_symptoms_for_specialist(symptoms):'''
    c3_new = '''# ===============================
# HELPER FUNCTIONS
# ===============================
def is_valid_email(email):
    pattern = r"^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"
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
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)

def analyze_symptoms_for_specialist(symptoms):'''
    content = content.replace(c3_old, c3_new)

    # UI render chunk
    c4_old = '''# ===============================
# UI RENDER - MAIN APPLICATION
# ===============================
if not st.session_state.logged_in_email:
    # First interface for login/signup
    st.title("Welcome to MyMedico Assistant ⚕️")
    st.subheader("Please Login or Sign Up to continue")
    
    auth_tab1, auth_tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with auth_tab1:
        with st.form("login_form"):
            login_email = st.text_input("Email")
            login_pwd = st.text_input("Password", type="password")
            submitted_login = st.form_submit_button("Login")
            if submitted_login:
                if login_email in st.session_state.users and st.session_state.users[login_email]["password"] == login_pwd:
                    st.session_state.logged_in_email = login_email
                    st.session_state.user_role = st.session_state.users[login_email]["role"]
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
                    
    with auth_tab2:
        with st.form("signup_form"):
            signup_email = st.text_input("Email")
            signup_pwd = st.text_input("Password", type="password")
            signup_role = st.selectbox("I am a:", ["Patient", "Hospital"])
            submitted_signup = st.form_submit_button("Sign Up")
            if submitted_signup:
                if signup_email in st.session_state.users:
                    st.error("Account already exists with this email.")
                elif signup_email and signup_pwd:
                    st.session_state.users[signup_email] = {"password": signup_pwd, "role": signup_role}
                    st.success("Account created successfully! Please login using the Login tab.")
                else:
                    st.error("Please fill in all fields.")
                    
    st.stop() # Hide the rest of the application until authenticated'''
    c4_new = '''# ===============================
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
                    elif login_email in st.session_state.users and st.session_state.users[login_email]["password"] == login_pwd:
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
                        st.error("Invalid email or password.")
        else:
            with st.form("login_otp_form"):
                st.info(f"An OTP was sent to {st.session_state.auth_state['login_email']}")
                otp_input = st.text_input("Enter 6-digit OTP")
                submit_otp = st.form_submit_button("Verify & Login")
                
                if submit_otp:
                    if otp_input == st.session_state.auth_state["login_otp"]:
                        email = st.session_state.auth_state["login_email"]
                        st.session_state.logged_in_email = email
                        st.session_state.user_role = st.session_state.users[email]["role"]
                        st.session_state.auth_state["login_step"] = 1 # Reset
                        st.success("Logged in successfully!")
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
                    elif signup_email in st.session_state.users:
                        st.error("Account already exists with this email.")
                    elif signup_email and signup_pwd:
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
                        st.session_state.users[email] = {
                            "password": st.session_state.auth_state["signup_pwd"], 
                            "role": st.session_state.auth_state["signup_role"]
                        }
                        st.session_state.auth_state["signup_step"] = 1 # Reset
                        st.success("Account created successfully! Please login using the Login tab.")
                        st.rerun()
                    else:
                        st.error("Invalid OTP.")
                        
            if st.button("Cancel & Go Back", key="cancel_signup"):
                st.session_state.auth_state["signup_step"] = 1
                st.rerun()
                    
    st.stop() # Hide the rest of the application until authenticated'''
    content = content.replace(c4_old, c4_new)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Update successful')
except Exception as e:
    print('Failed:', str(e))
