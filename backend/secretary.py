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
        # Count of dynamic context questions already asked overall
        self.context_questions_asked = 0
        # Maximum number of follow-up questions to ask overall
        self.max_questions = 3
        # Track which fields have been marked complete
        self.fields_complete = {}

    def evaluate_context(self):
        """
        Performs a local check of the essential fields using a minimal character threshold.
        Fields that have already been marked complete are skipped.
        Then uses OpenAI to refine the list of missing fields, returning only those that still require additional detail.
        If all required fields are sufficiently provided, returns an empty list.
        """
        threshold = 15  # Minimal number of characters that signal sufficient detail
        local_missing = []
        for field in self.required_fields:
            if self.fields_complete.get(field, False):
                continue
            # If field is missing or has insufficient detail, flag as missing
            if field not in self.context or len(self.context[field].strip()) < threshold:
                local_missing.append(field)
        if not local_missing:
            return []
        
        prompt = f"""
            You are a business assistant evaluating whether the provided context contains sufficient detail for the following fields:
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
                # Only return fields that are both locally missing and flagged by AI.
                missing = [field for field in local_missing if field in ai_missing]
                return missing if missing else local_missing
        except Exception as e:
            return local_missing

    def generate_dynamic_followup_question(self, missing_field):
        """
        Uses OpenAI to generate a dynamic follow-up question for a specific missing field.
        Includes the current content for that field so the question can be naturally rephrased.
        """
        current_answer = self.context.get(missing_field, "No information provided")
        prompt = f"""
            You are a business doctor helping a small business owner refine their information.
            The essential details needed include: Problem, Persona, Objective, Scenario, Geography, and Constraints.
            For the field "{missing_field}", the current answer is: "{current_answer}".
            Ask a specific, clear follow-up question to gather additional details for "{missing_field}".
            If no further information is needed for this field, reply with "DONE".
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
        If a specific field is being answered, appends the new input to build a richer response.
        Then re-evaluates the context.
        Once a field is deemed sufficiently detailed, it is marked as complete.
        Returns 'complete' if all essential fields are met; otherwise, returns 'incomplete' along with a follow-up question.
        """
        threshold = 15  # Same threshold used in evaluate_context
        
        if field_being_answered:
            # Append new input if the field already exists
            if field_being_answered in self.context and self.context[field_being_answered].strip():
                self.context[field_being_answered] += " " + user_input.strip()
            else:
                self.context[field_being_answered] = user_input.strip()
            # If the field now meets the threshold, mark it as complete
            if len(self.context[field_being_answered].strip()) >= threshold:
                self.fields_complete[field_being_answered] = True
        else:
            # Assume the first input addresses the 'problem'
            if "problem" not in self.context:
                self.context["problem"] = user_input.strip()
                if len(self.context["problem"].strip()) >= threshold:
                    self.fields_complete["problem"] = True

        # Re-evaluate current context
        missing_fields = self.evaluate_context()
        if not missing_fields:
            return {"status": "complete", "context": self.context}
        else:
            if self.context_questions_asked < self.max_questions:
                self.context_questions_asked += 1
                # From the missing fields list, choose the first that hasn't been marked complete
                field_id = missing_fields[0]
                question = self.generate_dynamic_followup_question(field_id)
                if question.strip().upper() == "DONE":
                    return {"status": "complete", "context": self.context}
                else:
                    return {"status": "incomplete", "question": question, "missing_field": field_id, "context": self.context}
            else:
                return {"status": "complete", "context": self.context}