import streamlit as st

from google import genai
from google.genai import types
from twilio.rest import Client

from prompts import (
    HEALTH_ASSISTANT_PROMPT,
    IMAGE_ANALYSIS_PROMPT,
    EMERGENCY_ALERT_PROMPT
)

def send_whatsapp_message(to_number, message_body):
    try:
        account_sid = st.secrets["twilio"]["account_sid"]
        api_key = st.secrets["twilio"]["api_key"]
        api_secret = st.secrets["twilio"]["api_secret"]
        whatsapp_from = st.secrets["twilio"]["whatsapp_from"]

        client = Client(
            api_key,
            api_secret,
            account_sid
        )

        message = client.messages.create(
            from_=whatsapp_from,
            to=f"whatsapp:{to_number}",
            body=message_body
        )

        return True, message.sid

    except Exception as e:
        return False, str(e)
    
# PAGE CONFIG

st.set_page_config(
    page_title="AroTrack",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# GEMINI

client = genai.Client(
    api_key=st.secrets["gemini"]["api_key"]
)

MODEL_NAME = "gemini-3.5-flash-lite"

# SESSION STATE

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "current_chat_title" not in st.session_state:
    st.session_state.current_chat_title = None

if "show_health_settings" not in st.session_state:
    st.session_state.show_health_settings = False

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "age": 20,
        "sex": "Male",
        "height": 165,
        "weight": 50,
        "activity": "Moderate",
        "smoker": "No",
        "children": 0,
        "water": 2.5,
        "sleep": 8.0,
        "steps": 8000,
        "weight_goal": 55,
        "calories": 2400
    }

# HELPER FUNCTIONS

def save_current_conversation():
    """Save the current conversation in session state."""

    messages = st.session_state.messages

    if not messages:
        return

    title = st.session_state.current_chat_title

    if not title:
        for message in messages:
            if message["role"] == "user":
                title = message["content"][:45]
                break

    if not title:
        title = "New conversation"

    st.session_state.current_chat_title = title

    st.session_state.conversations[title] = [
        {
            "role": message["role"],
            "content": message["content"]
        }
        for message in messages
    ]


def start_new_chat():
    """Start a clean conversation."""

    save_current_conversation()

    st.session_state.messages = []
    st.session_state.current_chat_title = None
    st.session_state.show_health_settings = False
    st.session_state.pending_question = None


def calculate_bmi(height_cm, weight_kg):
    """Calculate BMI."""

    if height_cm <= 0:
        return 0

    height_m = height_cm / 100

    return weight_kg / (height_m ** 2)

# CSS
st.markdown(
    """
    <style>

    /*
       MAIN CONTAINER
                        */

    .block-container {
        max-width: 1180px;
        padding-top: 1.2rem;
        padding-bottom: 5rem;
    }


    /*
       HIDE DEFAULT STREAMLIT UI
                                */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }


    /*
       SIDEBAR
                */

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,0.18);
    }

    .sidebar-brand {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 2px;
    }

    .sidebar-subtitle {
        color: #808782;
        font-size: 12px;
        margin-bottom: 25px;
    }

    .sidebar-heading {
        color: #858c89;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 25px;
        margin-bottom: 8px;
    }


    /*
       TOP HEADER
                    */

    .top-title {
        font-size: 21px;
        font-weight: 700;
        margin-bottom: 2px;
    }

    .top-subtitle {
        color: #7d8581;
        font-size: 12px;
    }


    /*
       WELCOME SCREEN
                        */

    .welcome-space {
        height: 45px;
    }

    .welcome-title {
        font-size: 32px;
        font-weight: 750;
        text-align: center;
        margin-top: 12px;
        margin-bottom: 8px;
    }

    .welcome-text {
        color: #7b837f;
        text-align: center;
        max-width: 580px;
        margin: auto;
        line-height: 1.6;
        font-size: 14px;
    }


    /* 
       STARTER QUESTION BUTTONS
                                */

    div[data-testid="stButton"] button {
        border-radius: 14px;
        min-height: 88px;
        padding: 12px 16px;
        text-align: left;
        font-size: 14px;
        line-height: 1.45;
    }

    div[data-testid="stButton"] button:hover {
        border-color: rgba(49, 130, 206, 0.45);
        transform: translateY(-1px);
        transition: 0.15s ease;
    }


    /*
       HEALTH NOTICE
                    */

    .medical-note {
        color: #929895;
        font-size: 10px;
        text-align: center;
        margin-top: 18px;
        margin-bottom: 5px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# SIDEBAR

with st.sidebar:
    # BRAND

    st.markdown(
        '<div class="sidebar-brand">🩺 AroTrack</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sidebar-subtitle">Arogya Sahayak</div>',
        unsafe_allow_html=True
    )

    # NEW CHAT

    if st.button(
        "＋ New Chat",
        use_container_width=True,
        key="sidebar_new_chat"
    ):
        start_new_chat()
        st.rerun()

    # CONVERSATIONS

    st.markdown(
        '<div class="sidebar-heading">Conversations</div>',
        unsafe_allow_html=True
    )

    search_chats = st.text_input(
        "Search conversations",
        placeholder="Search chats...",
        label_visibility="collapsed",
        key="conversation_search"
    )

    conversations = st.session_state.conversations

    if not conversations:

        st.caption(
            "No previous conversations yet."
        )

    else:

        displayed_chats = list(conversations.keys())

        for index, chat_title in enumerate(displayed_chats):

            if (
                not search_chats
                or search_chats.lower() in chat_title.lower()
            ):

                if st.button(
                    chat_title,
                    use_container_width=True,
                    key=f"conversation_{index}"
                ):

                    st.session_state.messages = [
                        {
                            "role": message["role"],
                            "content": message["content"]
                        }
                        for message in conversations[chat_title]
                    ]

                    st.session_state.current_chat_title = chat_title
                    st.session_state.show_health_settings = False
                    st.session_state.pending_question = None

                    st.rerun()

    # MY HEALTH

    st.markdown(
        '<div class="sidebar-heading">👤 My Health</div>',
        unsafe_allow_html=True
    )

    profile = st.session_state.user_profile

    # BMI

    bmi = calculate_bmi(
        profile["height"],
        profile["weight"]
    )

    # PROFILE

    with st.expander(
        "👤 Profile",
        expanded=True
    ):

        st.write(
            f"**Age:** {profile['age']} years"
        )

        st.write(
            f"**Sex:** {profile['sex']}"
        )

        st.write(
            f"**Height:** {profile['height']} cm"
        )

        st.write(
            f"**Weight:** {profile['weight']} kg"
        )
st.subheader("📱 WhatsApp Alert")

phone_number = st.text_input(
    "WhatsApp number",
    placeholder="+17372212163"
)

if st.button("Send WhatsApp Test"):
    if not phone_number:
        st.warning("Please enter a WhatsApp number.")
    else:
        success, result = send_whatsapp_message(
            phone_number,
            "🩺 Hello from AroTrack!\n\n"
            "This is a test WhatsApp notification."
        )

        if success:
            st.success("✅ WhatsApp message sent successfully!")
        else:
            st.error("❌ Failed to send WhatsApp message.")
            st.code(result)

    # BODY

    with st.expander("⚖️ Body"):

        st.metric(
            "BMI",
            f"{bmi:.1f}"
        )

        st.caption(
            "BMI is a screening measure and does not diagnose health conditions."
        )

        st.write(
            f"Height: **{profile['height']} cm**"
        )

        st.write(
            f"Weight: **{profile['weight']} kg**"
        )

    # LIFESTYLE

    with st.expander("🌿 Lifestyle"):

        st.write(
            f"🏃 **Activity:** {profile['activity']}"
        )

        st.write(
            f"🚭 **Smoking:** {profile['smoker']}"
        )

        st.write(
            f"💧 **Water goal:** {profile['water']} L/day"
        )

        st.write(
            f"😴 **Sleep goal:** {profile['sleep']} hours"
        )

        st.write(
            f"🚶 **Daily steps:** {profile['steps']:,}"
        )

    # GOALS

    with st.expander("🎯 Goals"):

        st.write(
            f"⚖️ **Weight goal:** {profile['weight_goal']} kg"
        )

        st.write(
            f"🔥 **Daily calories:** {profile['calories']:,} kcal"
        )

        st.write(
            f"🚶 **Step goal:** {profile['steps']:,}"
        )

    # FAMILY

    with st.expander("👨‍👩‍👧 Family"):

        st.write(
            f"Dependents / children: **{profile['children']}**"
        )

    # HEALTH INFORMATION

    if st.button(
        "⚙️ Health Information",
        use_container_width=True,
        key="sidebar_health_information"
    ):

        st.session_state.show_health_settings = (
            not st.session_state.show_health_settings
        )

    # HEALTH INFORMATION EDITOR

    if st.session_state.show_health_settings:

        st.markdown("---")

        st.markdown(
            "### ⚙️ Health Information"
        )

        st.caption(
            "Update the information AroTrack can use when it is relevant to your questions."
        )
        # BASIC PROFILE

        st.markdown(
            "#### 👤 Basic Profile"
        )

        new_age = st.number_input(
            "Age",
            min_value=1,
            max_value=120,
            value=int(profile["age"]),
            step=1,
            key="health_age"
        )

        sex_options = [
            "Male",
            "Female",
            "Other",
            "Prefer not to say"
        ]

        new_sex = st.selectbox(
            "Sex",
            sex_options,
            index=(
                sex_options.index(profile["sex"])
                if profile["sex"] in sex_options
                else 0
            ),
            key="health_sex"
        )

        # BODY

        st.markdown(
            "#### ⚖️ Body"
        )

        new_height = st.number_input(
            "Height (cm)",
            min_value=50,
            max_value=250,
            value=int(profile["height"]),
            step=1,
            key="health_height"
        )

        new_weight = st.number_input(
            "Weight (kg)",
            min_value=10.0,
            max_value=300.0,
            value=float(profile["weight"]),
            step=0.5,
            key="health_weight"
        )

        # LIFESTYLE

        st.markdown(
            "#### 🌿 Lifestyle"
        )

        activity_options = [
            "Sedentary",
            "Light",
            "Moderate",
            "Active",
            "Very Active"
        ]

        new_activity = st.selectbox(
            "Activity level",
            activity_options,
            index=(
                activity_options.index(profile["activity"])
                if profile["activity"] in activity_options
                else 2
            ),
            key="health_activity"
        )

        smoker_options = [
            "No",
            "Yes",
            "Prefer not to say"
        ]

        new_smoker = st.selectbox(
            "Smoking",
            smoker_options,
            index=(
                smoker_options.index(profile["smoker"])
                if profile["smoker"] in smoker_options
                else 0
            ),
            key="health_smoker"
        )

        new_water = st.number_input(
            "Water goal (L/day)",
            min_value=0.5,
            max_value=10.0,
            value=float(profile["water"]),
            step=0.1,
            key="health_water"
        )

        new_sleep = st.number_input(
            "Sleep goal (hours)",
            min_value=1.0,
            max_value=16.0,
            value=float(profile["sleep"]),
            step=0.5,
            key="health_sleep"
        )

        new_steps = st.number_input(
            "Daily step goal",
            min_value=500,
            max_value=50000,
            value=int(profile["steps"]),
            step=500,
            key="health_steps"
        )


        # GOALS

        st.markdown(
            "#### 🎯 Goals"
        )

        new_weight_goal = st.number_input(
            "Weight goal (kg)",
            min_value=10.0,
            max_value=300.0,
            value=float(profile["weight_goal"]),
            step=0.5,
            key="health_weight_goal"
        )

        new_calories = st.number_input(
            "Daily calorie target",
            min_value=500,
            max_value=10000,
            value=int(profile["calories"]),
            step=50,
            key="health_calories"
        )

        # FAMILY

        st.markdown(
            "#### 👨‍👩‍👧 Family"
        )

        new_children = st.number_input(
            "Children / dependents",
            min_value=0,
            max_value=20,
            value=int(profile["children"]),
            step=1,
            key="health_children"
        )

        # SAVE

        if st.button(
            "💾 Save Health Information",
            use_container_width=True,
            key="save_health_information"
        ):

            st.session_state.user_profile = {
                "age": new_age,
                "sex": new_sex,
                "height": new_height,
                "weight": new_weight,
                "activity": new_activity,
                "smoker": new_smoker,
                "children": new_children,
                "water": new_water,
                "sleep": new_sleep,
                "steps": new_steps,
                "weight_goal": new_weight_goal,
                "calories": new_calories
            }

            st.session_state.show_health_settings = False

            st.success(
                "Health information updated."
            )

            st.rerun()

# MAIN HEADER

header_left, header_right = st.columns(
    [5, 1]
)

with header_left:

    st.markdown(
        '<div class="top-title">🩺 AroTrack</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="top-subtitle">'
        'Arogya Sahayak • AI Health Assistant'
        '</div>',
        unsafe_allow_html=True
    )

with header_right:

    st.caption(
        "● AI Assistant"
    )

st.divider()

# WELCOME SCREEN

if not st.session_state.messages:

    st.markdown(
        '<div class="welcome-space"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        "<h1 style='text-align:center;'>🩺</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="welcome-title">'
        'How can I help you?'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="welcome-text">'
        'Your AI health assistant for general health '
        'information and everyday wellness questions.'
        '</div>',
        unsafe_allow_html=True
    )

    st.write("")

    # STARTER QUESTIONS — ROW 1

    col1, col2, col3 = st.columns(
        3,
        gap="medium"
    )

    with col1:

        if st.button(
            "🥗 Nutrition\n\nWhat should I eat for a healthy diet?",
            use_container_width=True,
            key="starter_nutrition"
        ):

            st.session_state.pending_question = (
                "What should I eat for a healthy diet?"
            )

            st.rerun()

    with col2:

        if st.button(
            "😴 Sleep\n\nHow can I improve my sleep?",
            use_container_width=True,
            key="starter_sleep"
        ):

            st.session_state.pending_question = (
                "How can I improve my sleep?"
            )

            st.rerun()

    with col3:

        if st.button(
            "🏃 Fitness\n\nHow much exercise should I get?",
            use_container_width=True,
            key="starter_fitness"
        ):

            st.session_state.pending_question = (
                "How much exercise should I get?"
            )

            st.rerun()

    # GAP

    st.write("")

    # STARTER QUESTIONS — ROW 2

    col4, col5, empty = st.columns(
        [1, 1, 1],
        gap="medium"
    )

    with col4:

        if st.button(
            "💧 Hydration\n\nHow much water should I drink?",
            use_container_width=True,
            key="starter_hydration"
        ):

            st.session_state.pending_question = (
                "How much water should I drink?"
            )

            st.rerun()

    with col5:

        if st.button(
            "⚖️ Healthy Weight\n\nHow can I maintain a healthy weight?",
            use_container_width=True,
            key="starter_weight"
        ):

            st.session_state.pending_question = (
                "How can I maintain a healthy weight?"
            )

            st.rerun()

# DISPLAY CONVERSATION

for message in st.session_state.messages:

    if message["role"] == "user":

        with st.chat_message(
            "user",
            avatar="👤"
        ):

            st.write(
                message["content"]
            )

    elif message["role"] == "assistant":

        with st.chat_message(
            "assistant",
            avatar="🩺"
        ):

            st.write(
                message["content"]
            )

# CHAT INPUT

chat_input = st.chat_input(
    "Ask AroTrack anything...",
    key="main_chat_input",
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp"]
)

question = None
uploaded_image = None

# READ CHAT INPUT

if chat_input:

    question = chat_input.text.strip()

    if chat_input.files:
        uploaded_image = chat_input.files[0]

# DETERMINE QUESTION

if st.session_state.pending_question:

    question = st.session_state.pending_question

    st.session_state.pending_question = None

# PROCESS QUESTION / IMAGE

if question or uploaded_image:

    # DEFAULT IMAGE QUESTION

    if not question:

        question = (
            "Describe the visible features in this image."
        )

    # USER MESSAGE

    user_content = question

    if uploaded_image:

        user_content = (
            f"[Image: {uploaded_image.name}]\n"
            f"{question}"
        )

    # SAVE USER MESSAGE

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_content
        }
    )

    # CREATE CHAT TITLE

    if not st.session_state.current_chat_title:

        st.session_state.current_chat_title = question[:45]

    # DISPLAY USER MESSAGE

    with st.chat_message(
        "user",
        avatar="👤"
    ):

        if uploaded_image:

            st.image(
                uploaded_image,
                caption=uploaded_image.name,
                width=350
            )

        st.write(question)


    # AROTRACK RESPONSE

    with st.chat_message(
        "assistant",
        avatar="🩺"
    ):

        with st.spinner(
            "AroTrack is analyzing..."
            if uploaded_image
            else "AroTrack is thinking..."
        ):

            try:
                # IMAGE ANALYSIS

                if uploaded_image:

                    image_bytes = uploaded_image.getvalue()

                    image_part = types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=uploaded_image.type
                    )

                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=[
                            IMAGE_ANALYSIS_PROMPT,
                            question,
                            image_part
                        ]
                    )


                # NORMAL TEXT CHAT + GOOGLE SEARCH

                else:

                    # ---------------------------------------------
                    # CREATE CONVERSATION
                    # ---------------------------------------------

                    conversation = [
                        HEALTH_ASSISTANT_PROMPT,
                        EMERGENCY_ALERT_PROMPT
                    ]


                    # ---------------------------------------------
                    # USER HEALTH CONTEXT
                    # ---------------------------------------------

                    profile = st.session_state.user_profile

                    conversation.append(
                        f"""
User health context:

Age: {profile['age']} years
Sex: {profile['sex']}
Height: {profile['height']} cm
Weight: {profile['weight']} kg
Activity level: {profile['activity']}
Smoking: {profile['smoker']}
Water goal: {profile['water']} L/day
Sleep goal: {profile['sleep']} hours
Daily step goal: {profile['steps']}
Weight goal: {profile['weight_goal']} kg
Daily calorie target: {profile['calories']} kcal
Dependents / children: {profile['children']}

Use this information only when it is relevant to the user's question.

Do not make medical diagnoses based only on this information.
"""
                    )
                    # PREVIOUS MESSAGES

                    for message in st.session_state.messages:

                        conversation.append(
                            f"{message['role']}: {message['content']}"
                        )

                    # GOOGLE SEARCH TOOL

                    search_tool = types.Tool(
                        google_search=types.GoogleSearch()
                    )

                    # GEMINI CONFIG

                    search_config = types.GenerateContentConfig(
                        tools=[search_tool]
                    )

                    # GEMINI RESPONSE

                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=conversation,
                        config=search_config
                    )

                # GET RESPONSE

                answer = response.text


                # DISPLAY RESPONSE

                st.write(answer)

                # SAVE ASSISTANT RESPONSE

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )

                # SAVE CONVERSATION

                save_current_conversation()

            # ERROR HANDLING

            except Exception as e:

                error_message = str(e)

    # QUOTA / RATE LIMIT ERROR

    if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:

        st.error(
            "🕐 Gemini API returned a quota/rate-limit error."
        )

        st.code(error_message)

    # API / OTHER ERROR

    else:

        st.error(
            "AroTrack encountered an unexpected error."
        )

        st.caption(
            f"Technical details: {error_message}"
        )

# MEDICAL NOTICE

st.markdown(
    """
    <div class="medical-note">
        🩺 AroTrack provides general health information
        and is not a replacement for professional medical advice.
    </div>
    """,
    unsafe_allow_html=True
)