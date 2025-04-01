# frontend/ui.py
import sys
sys.path.append(".")
import streamlit as st
from backend.secretary import Secretary
from backend.expert_manager import select_experts
from backend.ai_processing import generate_expert_discussion, generate_extra_followup_response
import logging
import streamlit.components.v1 as components

# Navigation logic - check session state to determine which page to display.
if "page" not in st.session_state:
    st.session_state["page"] = "chat"


logging.basicConfig(
    filename="ui.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# Custom CSS styling for simplified message boxes and sidebar navigation
st.markdown("""
    <style>
    /* Sidebar styling: light gray background */
    [data-testid="stSidebar"] {
        background-color: #F5F5F5 !important;
        color: #333 !important;
    }

    /* Message box styling */
    .message-box {
        border: 1px solid #e6e6e6;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
        max-width: 80%;
        word-wrap: break-word;
        white-space: normal;
    }

    /* Background colors based on alignment */
    .message-box.message-right {
        background-color: #e6e6e6;
    }

    .message-box.message-left {
        background-color: #ffffff;
    }

    /* Role label styling */
    .role-label {
        font-weight: bold;
        margin-bottom: 5px;
    }

    /* Alignment for user messages */
    .message-right {
        text-align: right;
        margin-left: auto;
    }

    /* Alignment for system messages */
    .message-left {
        text-align: left;
        margin-right: auto;
    }

    /* Styling for the top-right buttons in the sidebar */
    .top-buttons {
        text-align: right;
        margin-bottom: 10px;
    }
    .top-buttons button {
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .start-button {
        background-color: #dddddd;
        color: #000;
    }
    .waitlist-button {
        background-color: red;
        color: white;
        margin-left: 10px;
    }
    .start-button:hover {
        border: 1px solid #dddddd;
        background-color: #ffffff;
    }
    .waitlist-button:hover {
        border: 1px solid red;
        color: red;
        background-color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)


# Top-right button section using st.columns for side-by-side buttons
cols = st.columns(2)
with cols[0]:
    if st.button("Start New Meeting", key="start_new_meeting"):
        st.session_state.clear()
        try:
            st.experimental_rerun()
        except AttributeError:
            st.markdown("<script>window.location.reload();</script>", unsafe_allow_html=True)
with cols[1]:
    st.markdown("""
    <div class="waitlist-button", style="text-align:right;">
      <a href="https://sites.google.com/view/summonexperts/home" target="_blank">
            Join Waitlist
        </a>
    </div>
    """, unsafe_allow_html=True)


# Sidebar: "Join Waitlist" button at the very top, above the overview content.
with st.sidebar:
    st.title("Overview")
    st.write("""
        **Welcome! This is an AI-driven Decision-Making Assistant**

        It is designed to help small business owners and aspiring founders tackle 
        business challenges by gathering a meeting of experts to provide personalized strategic recommendations.

        **How to Use:**
        1. Describe your business challenge in the input box.
        2. Answer follow-up questions as prompted.
        3. Review the expert conversation and meeting resolution.

        **Product Vision**

        Over time, the system will learn your unique style and decision preferences,
        becoming smarter at guiding you towards your desired future business goals.
    """)

# Main page title and caption with emojis
st.title("💬 Call a Meeting")
st.caption("🚀 Use this application to summon a board of experts to help you make the right decision.")

# NEW: Initialize session state objects if not already set
if "secretary" not in st.session_state:
    st.session_state.secretary = Secretary()
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "Secretary", "content": "How can the team help you today?"}]
if "meeting_complete" not in st.session_state:
    st.session_state.meeting_complete = False
if "extra_followup_asked" not in st.session_state:
    st.session_state.extra_followup_asked = False


def display_message(role: str, content: str, user: bool = False):
    """
    Renders a message box with a role label (in bold) and content.
    User messages are right-aligned, while system messages (Secretary/Experts) are left-aligned.
    The role string is cleaned to remove any bold markers.
    """
    role = role.replace("**", "")
    alignment = "message-right" if user else "message-left"
    message_html = f"""
    <div class="message-box {alignment}">
        <div class="role-label">{role}</div>
        <div class="message-content">{content}</div>
    </div>
    """
    st.markdown(message_html, unsafe_allow_html=True)


def display_plain_text(content: str):
    """Displays plain text without any message box styling, removing markdown bold markers."""
    st.write(content.replace("**", ""))


def display_expert_conversation(conversation: str):
    """
    Splits the expert conversation into individual messages and displays each as a separate message box.
    Assumes each expert message is on its own line and in the format "Role: Message".
    """
    lines = conversation.splitlines()
    for line in lines:
        if line.strip():
            if ":" in line:
                role, msg = line.split(":", 1)
                display_message(role.strip(), msg.strip(), user=False)
            else:
                display_message("Expert", line.strip(), user=False)


def main():
    # Display previous messages
    for msg in st.session_state.messages:
        if msg["role"] == "You":
            display_message("You", msg["content"], user=True)
        else:
            display_message(msg["role"], msg["content"], user=False)

    # If meeting is not complete, process initial challenge input
    if not st.session_state.meeting_complete:
        prompt = st.chat_input("Please describe your business challenge.")
        if prompt:
            st.session_state.messages.append({"role": "You", "content": prompt})
            display_message("You", prompt, user=True)

            response = st.session_state.secretary.analyze_input(prompt)
            if response["status"] == "incomplete":
                followup_text = f"Follow-up: {response['question']}"
                st.session_state.messages.append({"role": "Secretary", "content": followup_text})
                display_message("Secretary", followup_text, user=False)
            else:
                st.session_state.meeting_complete = True
                secretary_message = "I understand your business better now, let me get you the experts who can help."
                st.session_state.messages.append({"role": "Secretary", "content": secretary_message})
                display_message("Secretary", secretary_message, user=False)

                experts = select_experts(response["context"])
                meeting_intro = f"Entering meeting with: {', '.join(experts)}"
                st.success(meeting_intro)

                # Generate the full expert discussion and meeting conclusion
                discussion = generate_expert_discussion(response["context"], experts)
                display_message("Meeting Resolutions", discussion, user=False)

                extra_secretary = "If you need further clarification, feel free to ask questions to help you make the best decision."
                st.session_state.messages.append({"role": "Secretary", "content": extra_secretary})
                display_message("Secretary", extra_secretary, user=False)
    else:
        # Meeting is complete: process extra follow-up question if available
        extra_prompt = st.chat_input("Additional Question (Max 1):")
        if extra_prompt:
            if not st.session_state.extra_followup_asked:
                st.session_state.messages.append({"role": "You", "content": extra_prompt})
                display_message("You", extra_prompt, user=True)

                context = st.session_state.secretary.context
                if "experts" not in st.session_state:
                    experts = select_experts(context)
                    st.session_state.experts = experts
                else:
                    experts = st.session_state.experts

                extra_reply = generate_extra_followup_response(extra_prompt, context, experts)
                if ":" in extra_reply:
                    role_from_reply, reply_message = extra_reply.split(":", 1)
                    display_message(role_from_reply.strip(), reply_message.strip(), user=False)
                    st.session_state.messages.append(
                        {"role": role_from_reply.strip(), "content": reply_message.strip()})
                else:
                    display_message("Expert", extra_reply, user=False)
                    st.session_state.messages.append({"role": "Expert", "content": extra_reply})

                st.session_state.extra_followup_asked = True
            else:
                st.error("That is the maximum number of follow-up questions allowed for now.")


if __name__ == "__main__":
    main()
