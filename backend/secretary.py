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
        # Count of dynamic context questions overall
        self.context_questions_asked = 0
        # Maximum number of follow-up questions to ask overall
        self.max_questions = 3
        # Track how many times each field has been asked
        self.fields_asked = {}

    def evaluate_context(self):
        """
        Performs a local check of the essential fields using a minimum character threshold.
        Then uses OpenAI to refine the list of missing fields, returning only those that
        still require more detail. If all required fields are provided, returns an empty list.
        """
        threshold = 15  # Adjust this threshold as needed
        local_missing = [field for field in self.required_fields 
                         if field not in self.context or len(self.context[field].strip()) < threshold]
        if not local_missing:
            return []

        prompt = f"""
            You are a business assistant evaluating whether the context contains sufficient detail for these fields:
            Problem, Persona, Objective, Scenario, Geography, and Constraints.
            Current context:
            {json.dumps(self.context, indent=2)}
            List the fields that still require additional detail. If all fields have sufficient detail, reply with "DONE".
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
                # Only flag fields that are locally missing AND flagged by AI:
                missing = [field for field in local_missing if field in ai_missing]
                return missing if missing else local_missing
        except Exception as e:
            return local_missing

    def generate_dynamic_followup_question(self, missing_field):
        """
        Uses OpenAI to generate a dynamic follow-up question for the specified missing field.
        Includes current content for that field so that the question can be naturally rephrased.
        """
        current_answer = self.context.get(missing_field, "No information provided")
        prompt = f"""
            You are a business doctor helping a small business owner refine their information.
            The essential details needed include: Problem, Persona, Objective, Scenario, Geography, and Constraints.
            For the field "{missing_field}", the current answer is: "{current_answer}".
            Please ask a specific, clear follow-up question to gather additional detail for "{missing_field}".
            If no further information is needed, reply with "DONE".
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
        If a field is already answered and the user is providing more input, append that input.
        Then re-evaluate the context:
          - If all required fields are complete, return complete.
          - Otherwise, if a field is still missing and hasn't been asked before, ask for follow-up.
          - It will only ask follow-up up to the maximum allowed questions.
        """
        # Update the context
        if field_being_answered:
            if field_being_answered in self.context and self.context[field_being_answered].strip():
                self.context[field_being_answered] += " " + user_input.strip()
            else:
                self.context[field_being_answered] = user_input.strip()
            # Track follow-up count for this field
            self.fields_asked[field_being_answered] = self.fields_asked.get(field_being_answered, 0) + 1
        else:
            if "problem" not in self.context:
                self.context["problem"] = user_input.strip()

        # Evaluate the context
        missing_fields = self.evaluate_context()
        # Remove fields that have already been asked (and get enough detail)
        filtered_missing = [field for field in missing_fields if self.fields_asked.get(field, 0) == 0]

        if not filtered_missing:
            return {"status": "complete", "context": self.context}
        else:
            if self.context_questions_asked < self.max_questions:
                self.context_questions_asked += 1
                field_id = filtered_missing[0]
                question = self.generate_dynamic_followup_question(field_id)
                if question.strip().upper() == "DONE":
                    return {"status": "complete", "context": self.context}
                else:
                    return {"status": "incomplete", "question": question, "missing_field": field_id, "context": self.context}
            else:
                return {"status": "complete", "context": self.context}
