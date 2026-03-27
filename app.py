import streamlit as st
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Initialize Streamlit configuration
st.set_page_config(page_title="MyMedico Assistant", layout="wide", page_icon="⚕️")

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# ===============================
# SESSION STATE INITIALIZATION
# ===============================
if 'patient_logged_in' not in st.session_state:
    st.session_state.patient_logged_in = False
if 'hospital_logged_in' not in st.session_state:
    st.session_state.hospital_logged_in = False

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
def analyze_symptoms_for_specialist(symptoms):
    sym = symptoms.lower()
    if any(keyword in sym for keyword in ['heart', 'chest pain', 'palpitation', 'breath']):
        return 'Cardiologist'
    elif any(keyword in sym for keyword in ['headache', 'dizzy', 'brain', 'neuro', 'nerve']):
        return 'Neurologist'
    elif any(keyword in sym for keyword in ['ear', 'nose', 'throat', 'cough']):
        return 'ENT'
    elif any(keyword in sym for keyword in ['skin', 'rash', 'itch']):
        return 'Dermatologist'
    else:
        return 'General Physician'

def get_doctors_by_specialist(specialist):
    return [d for d in st.session_state.doctors_schedule if d['specialist'].lower() == specialist.lower()]

# ===============================
# UI RENDER - MAIN APPLICATION
# ===============================
st.sidebar.title("⚕️ MyMedico Navigation")
domain = st.sidebar.radio("Select Domain", ["Patient Domain", "Hospital Domain"])

if domain == "Patient Domain":
    st.sidebar.subheader("🏥 Patient Navigation")
    patient_nav = st.sidebar.radio(
        "Pages", 
        ["Patient Login", "Preliminary Info", "Symptoms", "Specialist Consult", "Appointment", "Smith AI"]
    )
    
    st.title("Patient Portal 🏥")
    st.divider()

    if patient_nav == "Patient Login":
        st.header("🔑 Patient Login")
        if not st.session_state.patient_logged_in:
            with st.form("patient_login"):
                st.info("💡 Use any mock username and password to login.")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                if submitted:
                    if username and password:
                        st.session_state.patient_logged_in = True
                        st.success("Logged in successfully! Navigate to 'Preliminary Info' in the sidebar.")
                        st.rerun()
                    else:
                        st.error("Please enter credentials.")
        else:
            st.success("✅ You are already logged in.")
            if st.button("Logout"):
                st.session_state.patient_logged_in = False
                st.rerun()

    elif patient_nav == "Preliminary Info":
        st.header("📋 Preliminary Information")
        if st.session_state.patient_logged_in:
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
            # 5 metric cards
            cols = st.columns(5)
            cols[0].metric("Name", st.session_state.patient_info["Name"] or "N/A")
            cols[1].metric("Age", f"{st.session_state.patient_info['Age']} yrs")
            cols[2].metric("Gender", st.session_state.patient_info["Gender"] or "N/A")
            cols[3].metric("Weight", f"{st.session_state.patient_info['Weight']} kg")
            cols[4].metric("Blood Group", st.session_state.patient_info["Blood Group"] or "N/A")
        else:
            st.warning("Please login first.")

    elif patient_nav == "Symptoms":
        st.header("🩺 Symptoms")
        if st.session_state.patient_logged_in:
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
                # Using metric card layout
                st.metric(label="Current Logged Symptoms :warning:", value=st.session_state.symptoms[:50] + "..." if len(st.session_state.symptoms) > 50 else st.session_state.symptoms)
                st.info(f"Full Record: {st.session_state.symptoms}")
        else:
            st.warning("Please login first.")

    elif patient_nav == "Specialist Consult":
        st.header("👨‍⚕️ Specialist Recommendation")
        if st.session_state.patient_logged_in:
            if st.session_state.symptoms:
                st.info(f"**Your Recorded Symptoms:** {st.session_state.symptoms}")
                if st.button("Analyze & Suggest Specialist", type="primary"):
                    with st.spinner("Analyzing your symptoms to find the highly recommended specialist..."):
                        time.sleep(1.5) # mock loading for UX
                        specialist = analyze_symptoms_for_specialist(st.session_state.symptoms)
                        st.session_state.specialist_suggested = specialist
                    
                if st.session_state.specialist_suggested:
                    st.success(f"Based on your symptoms, we strongly recommend consulting a **{st.session_state.specialist_suggested}**.")
            else:
                st.warning("Please record your symptoms in the 'Symptoms' page first.")
        else:
            st.warning("Please login first.")

    elif patient_nav == "Appointment":
        st.header("📅 Book an Appointment")
        if st.session_state.patient_logged_in:
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
                                        "patient": st.session_state.patient_info["Name"] or "Unknown Patient",
                                        "doctor": doc['doctor'],
                                        "hospital": doc['hospital'],
                                        "time": doc['time']
                                    }
                                    st.session_state.appointments.append(appt_details)
                                    
                                    # Send notification to hospital domain
                                    notification_msg = f"New Appointment Alert: {appt_details['patient']} booked {doc['doctor']} on {doc['time']} at {doc['hospital']}"
                                    st.session_state.notifications.append(notification_msg)
                                    
                                    st.success(f"Appointment with {doc['doctor']} on {doc['time']} Booked Successfully!")
                                    st.balloons()
                else:
                    st.warning("No doctors found for this specialization in the current schedule.")
            else:
                st.warning("Please get a specialist recommendation first.")
        else:
            st.warning("Please login first.")
            
    elif patient_nav == "Smith AI":
        st.header("🤖 Ask Smith AI")
        st.caption("Your intelligent medical assistant powered by Google Gemini.")
        
        if not API_KEY:
            st.error("Google Gemini API Key not found. Please add GEMINI_API_KEY to your .env file.")
        elif st.session_state.patient_logged_in:
            
            # Action Buttons
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
            # Quick suggestion buttons
            q_col1, q_col2, q_col3 = st.columns(3)
            
            prompt = st.chat_input("Message Smith AI...")

            if q_col1.button("How to maintain a healthy heart?"):
                prompt = "How to maintain a healthy heart?"
            if q_col2.button("Home remedies for a mild cough?"):
                prompt = "Can you suggest some home remedies for a mild cough?"
            if q_col3.button("Analyze my previous symptoms"):
                symptoms = st.session_state.symptoms if st.session_state.symptoms else "No symptoms recorded."
                prompt = f"Analyze my symptoms: {symptoms} and suggest lifestyle advice."

            # Display chat history
            st.divider()
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt:
                # Add user context based on app state
                patient_info_str = f"Patient Info: Name: {st.session_state.patient_info['Name']}, Age: {st.session_state.patient_info['Age']}, Gender: {st.session_state.patient_info['Gender']}, Blood Group: {st.session_state.patient_info['Blood Group']}. Symptoms from page 2: {st.session_state.symptoms}"
                system_instruction = f"You are Smith AI, an expert medical assistant. You provide safe and accurate health responses and are aware of the medical domain well. The patient context is: {patient_info_str}. ALWAYS add a disclaimer that you are an AI and they should consult a real doctor. Patient says: {prompt}"

                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Smith AI is typing..."):
                        try:
                            # Generate Response
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            response = model.generate_content(system_instruction)
                            st.markdown(response.text)
                            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                        except Exception as e:
                            st.error(f"Error communicating with AI: {e}")
        else:
            st.warning("Please login first.")

elif domain == "Hospital Domain":
    # Topbar using columns for styling, and st.tabs for navigation
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
    
    # Implementing topbar navigation using tabs
    tab1, tab2 = st.tabs(["🔐 Hospital Login", "🩺 Doctors Schedule"])
    
    with tab1:
        st.header("Hospital Administrator Login")
        if not st.session_state.hospital_logged_in:
            with st.form("hospital_login"):
                st.info("💡 Use any mock hospital ID and password to login.")
                h_username = st.text_input("Hospital ID")
                h_password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login to Portal")
                if submitted:
                    if h_username and h_password:
                        st.session_state.hospital_logged_in = True
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("Please enter credentials.")
        else:
            st.success("✅ Logged into Hospital Administrator Portal.")
            if st.button("Logout Hospital", type="primary"):
                st.session_state.hospital_logged_in = False
                st.rerun()
                
    with tab2:
        st.header("Manage Doctors Schedule")
        if st.session_state.hospital_logged_in:
            st.write("### Current Active Schedule")
            # Present mock data elegantly
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
        else:
            st.warning("🔒 Please login from the 'Hospital Login' tab to access schedules.")
            import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
import pandas as pd
import numpy as np

# --- 1. Setup & Configuration ---
# Load environment variables from .env file
load_dotenv()

# Configure Streamlit page layout and title
st.set_page_config(page_title="SMITH AI Demo", page_icon="🤖", layout="wide")

# Hide the proactive trigger button and style the sidebar with CSS
st.markdown("""
<style>
/* Hide the Proactive_Trigger button visually across Streamlit widgets */
div[data-testid="stButton"] button:has(p:contains("Proactive_Trigger")) {
    display: none !important;
}
/* Futuristic styles for headers */
.header-text {
    font-family: 'Courier New', Courier, monospace;
    color: #4CAF50;
    text-shadow: 0 0 5px #4CAF50;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# --- 2. Session State Initialization ---
# Initialize chat history and conversation state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "should_speak" not in st.session_state:
    st.session_state.should_speak = False
if "latest_response" not in st.session_state:
    st.session_state.latest_response = ""
if "first_load" not in st.session_state:
    st.session_state.first_load = True
if "api_disabled" not in st.session_state:
    st.session_state.api_disabled = False

# --- 3. API Configuration & AI Helper Functions ---
def configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.sidebar.error("⚠️ GEMINI_API_KEY missing from .env")
        return False
    genai.configure(api_key=api_key)
    return True

# System instruction strictly mapping to SMITH AI's personality
SYSTEM_INSTRUCTION = (
    "You are 'SMITH', a futuristic, multi-purpose AI assistant capable of handling student queries, "
    "general knowledge, productivity guidance, and casual conversation. You are intelligent, reliable, "
    "and always respond in a structured, concise, and helpful manner. Your personality is friendly, "
    "slightly humorous, motivating, and futuristic. You should keep the conversations short and simple. "
    "Always use emojis, headings, and spacing to structure your texts."
)

def get_gemini_response(user_input, history=[]):
    """Fetches response from Gemini 2.5 Flash, retaining the conversation history."""
    if st.session_state.get("api_disabled", False):
        return "⚠️ SMITH AI is currently resting its neural pathways due to high usage limit restrictions! Please try again tomorrow, or enjoy the dashboard in the meantime."

    if not configure_gemini():
        return "⚠️ Please set up your GEMINI_API_KEY in the .env file."
        
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # Format history for Gemini
        formatted_history = []
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            formatted_history.append({"role": role, "parts": [{"text": msg["content"]}]})
            
        chat = model.start_chat(history=formatted_history)
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
            st.session_state.api_disabled = True
            return "⚠️ SMITH AI is currently resting its neural pathways due to high usage limit restrictions! Please try again tomorrow, or enjoy the dashboard in the meantime."
        return f"⚠️ Error communicating with Gemini: {str(e)}"

def trigger_proactive_greeting():
    """Generates the initial greeting proactively started by the AI."""
    prompt = "Start the conversation by proactively greeting the user and asking about their day. You must act as SMITH AI, a friendly and futuristic assistant."
    return get_gemini_response(prompt)

def trigger_timeout_followup():
    """Generates a follow-up question if the user hasn't responded for 30s."""
    prompt = "The user has not responded for 30 seconds. Proactively ask them a question about their day or if they need any productivity or general assistance. Keep it short, futuristic, and friendly."
    return get_gemini_response(prompt, history=st.session_state.messages)

# --- 4. Sidebar Navigation ---
st.sidebar.markdown("<h1 class='header-text'>🤖 SMITH AI</h1>", unsafe_allow_html=True)
page = st.sidebar.radio("Navigation", ["Dashboard", "Chat AI", "Analytics"])

st.sidebar.markdown("---")
st.sidebar.markdown("### Example Queries")
st.sidebar.info("• 'What's my productivity score?'\n• 'Tell me a fun fact about space.'\n• 'How can I stop procrastinating?'")

# --- 5. Page Implementations ---
if page == "Dashboard":
    st.title("📊 Dashboard")
    st.markdown("Welcome to the **SMITH AI Command Center**.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Completed Tasks", "12", "+3")
    col2.metric("Pending Tasks", "5", "-1")
    col3.metric("Productivity Index", "87%", "+5%")
    col4.metric("Mood Score", "Awesome 🚀")
    
    st.markdown("### 📋 Recent Activity")
    st.markdown("""
    - ✅ **Completed**: Math Homework
    - ✅ **Completed**: 30 min reading session
    - ⏳ **Pending**: AI Hackathon Demo
    """)

elif page == "Analytics":
    st.title("📈 Analytics")
    st.markdown("Your productivity trends over the last 7 days.")
    
    # Mock data for analytics charts
    chart_data = pd.DataFrame(
        np.random.randn(7, 3) * 10 + [80, 50, 20],
        columns=['Focus (mins)', 'Tasks Done', 'Distractions']
    )
    st.line_chart(chart_data)

elif page == "Chat AI":
    st.title("💬 Chat with SMITH AI")
    st.caption("🔊 Ensure your system sound is on. The AI will speak automatically. If it doesn't speak initially, please click anywhere on the interface to allow browser autoplay.")
    
    # Hidden button used by Javascript to trigger the 30-sec inactivity proactive response
    if st.button("Proactive_Trigger", key="proactive"):
        with st.chat_message("assistant"):
            with st.spinner("SMITH is sensing silence..."):
                response = trigger_timeout_followup()
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.should_speak = True
                st.session_state.latest_response = response
        st.rerun()

    # Initial load trigger: Start conversation without input
    if st.session_state.first_load:
        st.session_state.first_load = False
        greeting = trigger_proactive_greeting()
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.should_speak = True
        st.session_state.latest_response = greeting
        st.rerun()

    # Display chat history iteratively
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input for user
    if prompt := st.chat_input("Say something to SMITH AI..."):
        # Append and display user input
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Append and display AI response
        with st.chat_message("assistant"):
            with st.spinner("SMITH is analyzing..."):
                response = get_gemini_response(prompt, history=st.session_state.messages[:-1])
                st.markdown(response)
                
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.should_speak = True
        st.session_state.latest_response = response
        st.rerun()

    # --- 6. Handle Javascript TTS and 30s Wait Injection ---
    if st.session_state.should_speak:
        st.session_state.should_speak = False  # consume flag to prevent re-speaking on generic refreshes
        
        # Clean text for speech: Remove emojis while preserving standard punctuation
        text_body = st.session_state.latest_response
        clean_text = re.sub(r'[^\w\s,\.\?!\'-]', '', text_body)
        
        # Escape newlines and quotes to prevent Javascript string errors
        clean_text = clean_text.replace('\n', ' ').replace('"', '\\"').replace("'", "\\'")
        
        # Javascript block that executes the SpeechSynthesis and establishes a 30s timeout tracker
        js_code = f"""
        <script>
        // Auxiliary function to ensure our hidden trigger button is strictly hidden
        const hideTrigger = () => {{
            const btns = window.parent.document.querySelectorAll('button');
            btns.forEach(btn => {{
                if (btn.innerText.includes('Proactive_Trigger')) {{
                    btn.style.display = 'none';
                    if(btn.parentElement && btn.parentElement.parentElement) {{
                        btn.parentElement.parentElement.style.display = 'none';
                    }}
                }}
            }});
        }};
        hideTrigger();

        function speak() {{
            if (!window.speechSynthesis) return;
            window.speechSynthesis.cancel(); // Cancel any prior ongoing speech
            
            var msg = new SpeechSynthesisUtterance("{clean_text}");
            var voices = window.speechSynthesis.getVoices();
            
            // Prioritize a male voice as requested
            var maleVoice = voices.find(voice => voice.name.toLowerCase().includes('male'));
            if (maleVoice) {{
                msg.voice = maleVoice;
            }} else {{
                // Fallback to English voice if system doesn't formally tag 'male'
                var enVoice = voices.find(voice => voice.lang.startsWith('en'));
                if (enVoice) msg.voice = enVoice;
            }}
            
            msg.pitch = 0.8; // Slightly lower pitch for a structured male voice
            msg.rate = 1.0;
            
            // Trigger 30s counter ONLY when the AI finishes reading the response
            msg.onend = function() {{
                if (window.parent.proactiveTimer) clearTimeout(window.parent.proactiveTimer);
                
                var apiDisabled = {str(st.session_state.get('api_disabled', False)).lower()};
                if (!apiDisabled) {{
                    window.parent.proactiveTimer = setTimeout(function() {{
                        var btns = window.parent.document.querySelectorAll('button');
                        for (var i = 0; i < btns.length; i++) {{
                            if (btns[i].innerText.includes('Proactive_Trigger')) {{
                                btns[i].click(); // Simulate user pressing hidden button to trigger python execution
                                break;
                            }}
                        }}
                    }}, 30000); // 30 seconds
                }}
            }};
            
            window.speechSynthesis.speak(msg);
        }}
        
        // Wait briefly for speech synthesis voices to load into the browser context if zero
        if (window.speechSynthesis.getVoices().length === 0) {{
            window.speechSynthesis.onvoiceschanged = () => {{ speak(); }};
        }} else {{
            setTimeout(speak, 500);
        }}
        
        // Setup input interception to immediately stop/cancel the proactive 30s timer when the user gets active
        var chatInput = window.parent.document.querySelector('textarea[aria-label="Say something to SMITH AI..."]') || 
                        window.parent.document.querySelector('input[aria-label="Say something to SMITH AI..."]');
        if (chatInput) {{
            chatInput.addEventListener('keydown', function() {{
                if (window.parent.proactiveTimer) clearTimeout(window.parent.proactiveTimer);
                window.speechSynthesis.cancel();
            }});
        }}
        </script>
        """
        
        # Inject JavaScript seamlessly without adding visual height/width
        st.components.v1.html(js_code, height=0, width=0)
