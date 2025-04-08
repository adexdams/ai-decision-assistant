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
        First performs a local check of the essential fields (problem, persona, objective, scenario, geography, constraints).
        A simple threshold is used to determine if a provided answer is sufficiently detailed.
        Then uses OpenAI to refine the list of missing fields, returning only those that still require additional detail.
        If all required fields are sufficiently provided, returns an empty list.
        """
        # Define a threshold for minimal acceptable detail
        threshold = 15  # adjust as necessary
        local_missing = [field for field in self.required_fields 
                         if field not in self.context or len(self.context[field].strip()) < threshold]
        if not local_missing:
            return []
        
        # Use OpenAI to further evaluate the current context
        prompt = f"""
    You are a business assistant evaluating if the provided context contains sufficient detail for the following essential fields:
    Problem, Persona, Objective, Scenario, Geography, and Constraints.
    Here is the current context:
    {json.dumps(self.context, indent=2)}
    Based on this context, list any fields that still require additional detail.
    If all required fields are sufficiently provided, reply with "DONE".
    """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}]
            )
            answer = response.choices[0].message.content.strip()
            if answer.upper() == "DONE":
                return []
            else:
                ai_missing = [field.strip().lower() for field in answer.split(",") if field.strip()]
                # Return only those fields that are both locally missing and flagged by AI;
                # If none are flagged, fall back to the local missing fields.
                missing = [field for field in local_missing if field in ai_missing]
                return missing if missing else local_missing
        except Exception as e:
            # Fallback to the local check if there's an error with the API.
            return local_missing

    def generate_dynamic_followup_question(self, missing_field):
        """
        Uses OpenAI to generate a dynamic follow-up question for the specific missing field.
        Incorporates the current content for that field to avoid repetitive questions.
        """
        current_answer = self.context.get(missing_field, "No information provided")
        prompt = f"""
You are a business doctor helping a small business owner understand their problem.
The essential information needed includes: Problem, Persona, Objective, Scenario, Geography, and Constraints.
The current information for "{missing_field}" is: "{current_answer}".
Ask a specific, clear follow-up question to gather additional detail for the field "{missing_field}".
If the answer provided so far is sufficient, reply with "DONE".
"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}]
            )
            question = response.choices[0].message.content.strip()
            return question
        except Exception as e:
            return f"Could you please provide more details about your {missing_field}?"

    def analyze_input(self, user_input, field_being_answered=None):
        """
        Processes user input and updates context dynamically.
        If a specific field is being answered and that field already has data, appends the new input.
        Otherwise, treats the initial input as addressing the 'problem'.
        Then evaluates the context. If any essential fields are missing, it generates a targeted follow-up
        question for the first missing field. If all fields are sufficiently complete, returns complete.
        """
        if field_being_answered:
            # If the field already has some content, append the new input.
            if field_being_answered in self.context and self.context[field_being_answered].strip():
                self.context[field_being_answered] += " " + user_input.strip()
            else:
                self.context[field_being_answered] = user_input.strip()
        else:
            # For the initial input, assume it addresses the 'problem'
            if "problem" not in self.context:
                self.context["problem"] = user_input.strip()
    
        # Evaluate the current context using our updated evaluation logic.
        missing_fields = self.evaluate_context()
        if not missing_fields:
            return {"status": "complete", "context": self.context}
        else:
            # Only ask a follow-up if we haven't reached the maximum number allowed.
            if self.context_questions_asked < self.max_questions:
                self.context_questions_asked += 1
                field_id = missing_fields[0]
                question = self.generate_dynamic_followup_question(field_id)
                if question.strip().upper() == "DONE":
                    return {"status": "complete", "context": self.context}
                else:
                    return {"status": "incomplete", "question": question, "missing_field": field_id, "context": self.context}
            else:
                return {"status": "complete", "context": self.context}
