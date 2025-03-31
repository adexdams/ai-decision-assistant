# backend/expert_manager.py
import os
from openai import OpenAI
import logging

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

logging.basicConfig(filename="logs/expert_selection.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Retrieve the OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment!")

EXPERT_CATEGORIES = [
    "Business Strategy Expert",
    "Financial Expert",
    "Legal Consultant",
    "Technical Expert",
    "Marketing Specialist",
    "Project Manager",
    "Operations Consultant",
    "Leadership Coach",
    "Industry-Specific Advisor"
]

def select_experts(user_context):
    """
    Uses OpenAI to determine the most relevant experts for the user's situation.
    Ensures at least 3 experts are selected.
    """
    prompt = f"""
Based on the following business context:
{user_context}

Please select between 3 to 5 experts from the following categories that would be most helpful:
{", ".join(EXPERT_CATEGORIES)}

Return only a list of expert roles, one per line.
"""
    try:
        response = client.chat.completions.create(model="gpt-4",
        messages=[{"role": "system", "content": prompt}])
        experts_text = response.choices[0].message.content
        experts = [line.strip() for line in experts_text.splitlines() if line.strip() in EXPERT_CATEGORIES]

        # Fallback: Ensure at least 3 experts are selected
        while len(experts) < 3:
            for expert in EXPERT_CATEGORIES:
                if expert not in experts:
                    experts.append(expert)
                    if len(experts) >= 3:
                        break

        # Log expert selection
        logging.info(f"User Context: {user_context}")
        logging.info(f"Selected Experts: {experts}")

        return experts
    except Exception as e:
        logging.error(f"Error selecting experts: {e}")
        # Fallback: Return a default set of experts if OpenAI call fails
        return ["Business Strategy Expert", "Financial Expert", "Technical Expert"]