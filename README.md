# Summons – AI-Driven Decision-Making Assistant

Summons is an AI-powered decision-making partner designed for small business owners and aspiring founders. It helps users tackle complex business challenges by simulating a meeting with a board of expert advisors. The system interactively gathers essential context, selects relevant experts, and generates a simulated expert discussion along with strategic recommendations—all powered by OpenAI's GPT models.

## Features

- **Dynamic Context Gathering:**  
  The system, through its Secretary module, interactively collects essential information such as:
  - **Problem:** What is the challenge or contention?
  - **Persona:** What is your role in the situation?
  - **Objective:** What do you want to achieve?
  - **Scenario:** How and where did the situation occur?
  - **Constraints:** What resources are available (financial, human, time, technology)?
  - Optionally, additional specialty-related background is gathered if needed.

- **Expert Discussion & Recommendations:**  
  Once the context is complete, the system selects relevant experts and generates:
  - A sequential expert discussion (with each expert offering their specialized perspective).
  - A consolidated meeting conclusion that provides 2–3 clear strategic options with risk-reward analyses, leadership style insights, and real-world analogies.
  - An extra follow-up functionality for one additional clarification question, yielding a targeted expert response.

- **Waitlist & Monetization:**  
  Users who have exhausted their meeting sessions can join a waitlist (with email collection) and optionally opt for priority access via Stripe integration (to be implemented).

- **Logging & Analytics:**  
  Basic logging is incorporated to track user actions and waitlist sign-ups, helping you analyze usage and performance.

## Installation

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd ai_decision_assistant
