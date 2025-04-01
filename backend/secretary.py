# backend/secretary.py
import os
import json
import openai
from backend.expert_manager import select_experts

# Set OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment!")
openai.api_key = OPENAI_API_KEY


class Secretary:
    def __init__(self):
        # Essential fields we need for context
        self.required_fields = ["problem", "persona", "objective", "scenario", "geography", "constraints"]
        # Initialize context as an empty dictionary
        self.context = {}
        # Count of dynamic context questions already asked
        self.context_questions_asked = 0
        # Maximum number of follow-up questions to ask
        self.max_questions = 3

    def evaluate_context(self):
        """
        Uses OpenAI to evaluate the current context.
        Returns a list of missing essential fields. If all required fields are provided, returns an empty list.
        """
        prompt = f"""
You are a business assistant evaluating if all essential information is provided.
The essential fields are: Problem, Persona, Objective, Scenario, Geography, and Constraints.
Here is the current context:
{json.dumps(self.context, indent=2)}

List any missing fields (if multiple, separate them with commas). If all required information is provided, reply with "DONE".
"""
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}]
            )
            answer = response.choices[0].message.content.strip()
            if answer.upper() == "DONE":
                return []
            else:
                # Split by commas and normalize field names
                missing = [field.strip().lower() for field in answer.split(",") if field.strip()]
                # Filter to only those in required_fields
                return [field for field in missing if field in self.required_fields]
        except Exception as e:
            # Fallback: perform a simple check locally.
            missing = []
            for field in self.required_fields:
                if field not in self.context or not self.context[field]:
                    missing.append(field)
            return missing

    def generate_dynamic_followup_question(self, missing_field):
        """
        Uses OpenAI to generate a dynamic follow-up question for a specific missing field.
        Acts as a business doctor asking one targeted question at a time.
        """
        prompt = f"""
You are a business doctor helping a small business owner understand their problem.
The essential information needed includes: Problem, Persona, Objective, Scenario, Geography, and Constraints.
The current context is:
{json.dumps(self.context, indent=2)}

Ask a specific, clear follow-up question to gather more information for the field "{missing_field}".
If no further information is needed for this field, reply with "DONE".
"""
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}]
            )
            question = response.choices[0].message.content.strip()
            return question
        except Exception as e:
            # Fallback generic question
            return f"Could you please provide more details about your {missing_field}?"

    def analyze_input(self, user_input, field_being_answered=None):
        """
        Processes user input and updates context dynamically.
        The first input is treated as the initial business challenge.
        Then, after each input, the current context is evaluated.
        If any essential fields are missing, a targeted follow-up question is generated.
        If all essential fields are present, returns complete.
        """
        if field_being_answered:
            # Save answer for the specific missing field
            self.context[field_being_answered] = user_input.strip()
        else:
            # For the initial input, assume it addresses the 'problem'
            if "problem" not in self.context:
                self.context["problem"] = user_input.strip()

        # Evaluate current context
        missing_fields = self.evaluate_context()
        if not missing_fields:
            return {"status": "complete", "context": self.context}
        else:
            # If we haven't reached the maximum number of follow-up questions, ask for the first missing field
            if self.context_questions_asked < self.max_questions:
                self.context_questions_asked += 1
                # Pick the first missing field
                field_id = missing_fields[0]
                question = self.generate_dynamic_followup_question(field_id)
                if question.strip().upper() == "DONE":
                    return {"status": "complete", "context": self.context}
                else:
                    return {"status": "incomplete", "question": question, "missing_field": field_id, "context": self.context}
            else:
                # Maximum number of follow-up questions reached; assume context is as complete as it will be.
                return {"status": "complete", "context": self.context}
