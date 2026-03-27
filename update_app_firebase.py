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
import smtplib
import random
import re
from email.message import EmailMessage'''
    c1_new = '''import streamlit as st
import os
import time
import smtplib
import random
import re
import requests
from email.message import EmailMessage'''
    content = content.replace(c1_old, c1_new)

    # API keys chunk
    c2_old = '''# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")'''
    c2_new = '''# Configure APIs
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

API_KEY = os.getenv("GEMINI_API_KEY")'''
    content = content.replace(c2_old, c2_new)

    # Helper functions chunk
    c3_old = '''# ===============================
# HELPER FUNCTIONS
# ===============================
def is_valid_email(email):'''
    c3_new = '''# ===============================
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

def is_valid_email(email):'''
    content = content.replace(c3_old, c3_new)

    # UI render logic chunk for Login
    c4_old = '''                    elif login_email in st.session_state.users and st.session_state.users[login_email]["password"] == login_pwd:
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
                        st.error("Invalid email or password.")'''
    c4_new = '''                    else:
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
                            st.error(f"Firebase Auth Error: {fb_msg}")'''
    content = content.replace(c4_old, c4_new)

    # UI render logic chunk for Signup
    c5_old = '''                    elif signup_email in st.session_state.users:
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
                        st.error("Please fill in all fields.")'''
    c5_new = '''                    elif signup_email and signup_pwd:
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
                        st.error("Please fill in all fields.")'''
    content = content.replace(c5_old, c5_new)

    # Signup OTP verification step
    c6_old = '''                if submit_otp:
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
                        st.error("Invalid OTP.")'''
    c6_new = '''                if submit_otp:
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
                        st.error("Invalid OTP.")'''
    content = content.replace(c6_old, c6_new)

    # Login OTP verification fixing role extraction
    c7_old = '''                if submit_otp:
                    if otp_input == st.session_state.auth_state["login_otp"]:
                        email = st.session_state.auth_state["login_email"]
                        st.session_state.logged_in_email = email
                        st.session_state.user_role = st.session_state.users[email]["role"]
                        st.session_state.auth_state["login_step"] = 1 # Reset
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid OTP.")'''
    c7_new = '''                if submit_otp:
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
                        st.error("Invalid OTP.")'''
    content = content.replace(c7_old, c7_new)


    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Update successful')
except Exception as e:
    print('Failed:', str(e))
