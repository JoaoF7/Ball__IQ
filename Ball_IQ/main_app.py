import streamlit as st
import json
from streamlit_lottie import st_lottie
import requests
import re
import time
from PIL import Image
from streamlit_app_not_main_file.users_db import UserDatabase
from chatbot.bot import MainChatbot  # Import the chatbot class
import subprocess


# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "register_in" not in st.session_state:
    st.session_state.register_in = False

if "navigate_to" not in st.session_state:
    st.session_state.navigate_to = "home"
    

# Configure the app
st.set_page_config(
    page_title="Welcome to BallIQ - Fantasy Football AI",
    page_icon="⚽",
    layout="wide", # wide , centered
    initial_sidebar_state="auto",
)


# Load the database
db = UserDatabase()

# Load local CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("Ball_IQ/streamlit_app_not_main_file/style/style11.css") 


def load_lottie_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:  # Specify UTF-8 encoding
        return json.load(f)

lottie_animation = load_lottie_file("Ball_IQ/streamlit_app_not_main_file/lottie/animation.json")

image_logo = Image.open("Ball_IQ/streamlit_app_not_main_file/images/logo_balliq_2.png") 

# Function to validate email
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


# Define the Home Page
def home_page():
    # Define columns with proportions for a small blank column in the middle
    col_left, col_gap, col_right = st.columns([1.3, 0.3, 1.4])  # Left column is larger, blank column for spacing

    # Left Column: Title, Subheader, and Logo
    with col_left:
        st.title("BallIQ - Fantasy Football AI")
        st.subheader("Welcome to the future of Fantasy Football")
        st.write("---")  # Separator
        st.image(image_logo, width = 500) # use_container_width = True

    # Empty Column for spacing
    with col_gap:
        st.markdown("")

    # Right Column: Buttons and Contact Us Section
    with col_right:
        # Center buttons in the middle of the column
        st.write("<div style='text-align: center; line-height: 1.8;'>", unsafe_allow_html=True)

        if st.button("Login"):
            st.session_state.navigate_to = "login"
            st.rerun()

        st.write("<div style='margin: 20px;'></div>", unsafe_allow_html=True)  # Add spacing
        if st.button("Register"):
            st.session_state.navigate_to = "register"
            st.rerun()

        st.write("<div style='margin: 20px;'></div>", unsafe_allow_html=True)  # Add spacing
        if st.button("About Us"):
            st.session_state.navigate_to = "about_us"
            st.rerun()

        st.write("</div>", unsafe_allow_html=True)  # End centering div

        # Add Contact Us Section
        st.write("---")  # Separator
        st.header("Contact Us")
        contact_form = """ 
        <form action="https://formsubmit.co/fantasyball.iq@gmail.com" method="POST">
            <input type="hidden" name="_captcha" value="false"> 
            <input type="text" name="name" placeholder="Your name" required style="width: 100%; margin-bottom: 10px;">
            <input type="email" name="email" placeholder="Your email" required style="width: 100%; margin-bottom: 10px;">
            <textarea name="message" placeholder="Your message here" required style="width: 100%; margin-bottom: 10px;"></textarea>
            <button type="submit" style="width: 100%;">Send</button>
        </form>
        """ 

        # Render the contact form
        st.markdown(contact_form, unsafe_allow_html=True)


def login_page():
    placeholder = st.empty()  # Create a placeholder for the page

    with placeholder.container():
        st.title("Login")
        
        # Display any error message if there's one stored in session state
        if "login_error" in st.session_state and st.session_state.login_error:
            st.error(st.session_state.login_error)

        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")

            if login_button:
                if not email or not password:
                    st.session_state.login_error = "Please fill all fields"
                elif not db.check_if_email_exists(email):
                    st.session_state.login_error = "Email not registered"
                elif not db.verify_user(email, password):
                    st.session_state.login_error = "Incorrect password"
                else:
                    st.session_state.login_error = None  # Clear any previous error
                    st.success("Login successful!")
                    
                    # Save user details in session state
                    st.session_state.username = db.get_user_details(email)[0]
                    st.session_state.user_id = db.get_user_id(email)
                    st.session_state.logged_in = True
                
                    # Use a loading spinner instead of immediately navigating
                    with st.spinner("Redirecting to the chatbot..."):
                        time.sleep(2)  # Loading spinner for transition 

                    # Clear placeholder before navigating
                    placeholder.empty()
                    
                    # Navigate to chat page
                    st.session_state.navigate_to = "chat"
                st.rerun()  # Ensure that the page updates after the wait


    if st.button("Back to Home"):
        st.session_state.navigate_to = "home"
        st.rerun()


# Define Register Page
def register_page():
    st.title("Register")
    
    # Display any error message if there's one stored in session state
    if "register_error" in st.session_state and st.session_state.register_error:
        st.error(st.session_state.register_error)

    with st.form("register_form"):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input("Username")
            email = st.text_input("Email")

        with col2:
            password = st.text_input("Password", type="password")
            team_name = st.text_input("Team Name")

        submit = st.form_submit_button("Register")
        if submit:
            if not all([username, email, password, team_name]):
                st.session_state.register_error = "Please fill all fields"
            elif not is_valid_email(email):
                st.session_state.register_error = "Invalid email format"
            elif len(password) < 8:
                st.session_state.register_error = "Password must be at least 8 characters"
            elif db.check_if_email_exists(email):
                st.session_state.register_error = "Email already registered"
            else:
                st.session_state.register_error = None  # Clear any previous error
                db.add_user(username, email, password, team_name)
                st.success("Registration successful!")
                st.session_state.register_in = True


                # Delay for 2 seconds before redirecting
                time.sleep(1)  
                
                # Navigate to login page after successful registration
                st.session_state.navigate_to = "login"
                time.sleep(1) # Delay for 1 seconds before redirecting
            st.rerun()  # Ensure that the page updates after the wait


    if st.button("Back to Home"):
        st.session_state.navigate_to = "home"
        st.rerun()

# About Us Page 
def about_us_page():
    st.title("About Us")

    # Layout with an additional blank column for spacing
    col_left, col_gap, col_right = st.columns([1.5, 0.2, 2])  # Adjust proportions for blank space

    # Left Column: Mission, Vision, Values, and Back to Home Button
    with col_left:
        st.markdown(
            """
            <style>
            .section-header {
                font-size: 24px;
                font-weight: bold;
                margin-top: 20px;
                color: #4ca1af; /* Updated to the requested color */
            }
            .values-list {
                margin-left: 20px;
                font-size: 18px;
                color: black; /* Set remaining text to black */
            }
            .back-button {
                margin-top: 30px; /* Spacing above the button */
                background-color: #3498DB;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
                border: none;
                cursor: pointer;
                text-align: center;
            }
            .back-button:hover {
                background-color: #21618C; /* Darker blue on hover */
            }
            .separator {
                border-top: 1px solid black; /* Updated to black */
                margin: 40px 0; /* Spacing around the line */
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Mission Section
        st.markdown("<div class='section-header'>Mission</div>", unsafe_allow_html=True)
        st.write(
            "At BallIQ, our mission is to revolutionize the world of fantasy football by empowering enthusiasts "
            "with cutting-edge AI tools to make smarter decisions and enjoy the game like never before.",
            unsafe_allow_html=True,
        )

        # Vision Section
        st.markdown("<div class='section-header'>Vision</div>", unsafe_allow_html=True)
        st.write(
            "Our vision is to become the leading AI-driven platform in the fantasy football space, "
            "bridging the gap between sports and technology to create a dynamic and engaging community.",
            unsafe_allow_html=True,
        )

        # Values Section
        st.markdown("<div class='section-header'>Values</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <ul class="values-list">
                <li><strong>Innovation:</strong> We embrace technology to deliver top-notch solutions.</li>
                <li><strong>Integrity:</strong> Transparency and trust are at the core of everything we do.</li>
                <li><strong>Community:</strong> Building a strong and supportive fantasy football community is our priority.</li>
                <li><strong>Excellence:</strong> Striving for the best in every aspect of our platform.</li>
            </ul>
            """,
            unsafe_allow_html=True,
        )

        # Add a horizontal line to separate Values and the Back to Home button
        st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

        # Back to Home Button
        if st.button("Back to Home", key="back_button"):
            st.session_state.navigate_to = "home"
            st.rerun()

    # Empty Column for spacing
    with col_gap:
        st.markdown("")

    # Right Column: Introductory Text and Animation
    with col_right:
        st.markdown(
            """
            <style>
            .intro-header {
                font-size: 18px;
                font-weight: bold;
                color: #4ca1af; /* Updated to the requested color */
            }
            .intro-names {
                font-size: 18px;
                font-weight: normal; /* Removed bold (negrito) from names */
                color: black; /* Set names to black */
            }
            .intro-footer {
                font-size: 16px;
                font-weight: normal;
                color: black; /* Set footer to black */
            }
            </style>
            <div class="intro-header">
                Welcome to BallIQ! Our platform is brought to you by a team of passionate developers:
            </div>
            <ul class="intro-names">
                <li>João Ferreira</li>
                <li>Miguel Mendes</li>
                <li>Rodrigo Maia</li>
                <li>Artem Khomytskyi</li>
                <li>Tymofii Kuzmenko</li>
            </ul>
            <div class="intro-footer">
                Together, we strive to revolutionize the fantasy football experience with cutting-edge technology and a vision for the future.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")  

        # Display Animation
        st_lottie(lottie_animation, height=300, key="animation")



# Define Chat Page
def chat_page():
    user_input = st.chat_input("Say something")

    def simulate_streaming(message):
        buffer = ""
        for char in message:
            buffer += char
            if char == " " or char == "\n":
                yield buffer
                buffer = ""
                if char == "\n":  # To simulate line breaks
                    time.sleep(0.1)  # Longer pause for newlines (optional)
                else:
                    time.sleep(0.05)
        if buffer:  # Yield any remaining characters
            yield buffer

    st.title("BallIQ Chatbot")
    
    bot = MainChatbot(st.session_state.user_id, 1)
    bot.user_login(st.session_state.user_id, 1)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        name = st.session_state.username # Replace with user's name
        # First time user
        if st.session_state.register_in:
            initial_message = (
                " Welcome {name}, ask me anything you want!"
            )
            response = initial_message.format(name=name)
            # Add chatbot response message to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            initial_message = "Hello {name}, I'm glad your back!"
            response = initial_message.format(name=name)
            # Add chatbot response message to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(user_input)

    # Check if user input is a string
    if isinstance(user_input, str):
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response = bot.process_user_input({"customer_input": user_input})
            st.write_stream(simulate_streaming(response))
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

    if st.button("Back to home"):
        st.session_state.navigate_to = "home"
        st.rerun()


# Navigation Logic
if st.session_state.navigate_to == "home":
    home_page()
elif st.session_state.navigate_to == "about_us":
    about_us_page()
elif st.session_state.navigate_to == "login":
    login_page()
elif st.session_state.navigate_to == "register":
    register_page()
elif st.session_state.logged_in:
    chat_page()
