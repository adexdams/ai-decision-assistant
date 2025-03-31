# frontend/waitlist.py
import streamlit as st
import re
import logging
from backend.database import save_waitlist

# Setup logging to file
logging.basicConfig(
    filename="waitlist.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def validate_email(email):
    # Simple regex for email validation
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return re.match(email_regex, email) is not None


def main():
    # Return to Call Meeting button at the top
    if st.button("Return to Call Meeting"):
        logging.info("User clicked Return to Call Meeting.")
        st.write("Refresh page to return to meeting page.")
        st.markdown("<script>window.location.href = 'ui.py';</script>", unsafe_allow_html=True)

    st.title("📋 Join the Waitlist")
    st.caption("🔔 Get priority access and updates for our Decision-Making Assistant.")

    st.write("""
    **Product Vision**

    Imagine having a board of experts in your pocket that you can summon at any time.
    Over time, this system will learn your unique style and decision preferences,
    becoming smarter at guiding you towards your desired future business success.
    """)

    # Email input field
    email = st.text_input("Enter your email to join the waitlist:")

    # Button to join waitlist
    if st.button("Join Waitlist"):
        if email and validate_email(email):
            save_waitlist(email, priority_access=False)
            logging.info(f"Waitlist entry added: {email}")
            st.success("Thank you! You've been added to the waitlist.")
        else:
            logging.error(f"Invalid email attempted: {email}")
            st.error("Please enter a valid email address.")

    st.write("---")
    st.write("For $5, join priority access")

    # Button to redirect to Stripe payment page for priority access
    if st.button("Pay Here"):
        logging.info("User clicked 'Pay Here' for priority access.")
        st.markdown("<script>window.location.href = 'https://your-stripe-payment-page.com';</script>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()