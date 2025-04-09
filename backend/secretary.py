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
        # User-friendly mapping for questions
        self.question_prompts = {
            "problem": "Could you please describe the business challenge you're facing?",
            "persona": "Could you please describe your role or position in this situation?",
            "objective": "What is the main goal or vision you want to achieve with this project?",
            "scenario": "Can you explain the situation or context in which this project is taking place?",
            "geography": "Where will this project be executed (location, market, etc.)?",
            "constraints": "What limitations or constraints (time, budget, resources) are you facing?"
        }
        # Initialize context as an empty dictionary
        self.context = {}
        # Count of dynamic context questions already asked overall
        self.context_questions_asked = 0
        # Maximum number of follow-up questions to ask overall
        self.max_questions = 3
        # Track which fields have been asked (to avoid repetition)
        self.fields_asked = {}
        # Track which fields are complete
        self.fields_complete = {}

    def evaluate_context(self):
        """
        Checks the context locally to see if each field meets a minimum detail threshold.
        Fields already marked as complete are skipped.
        Then uses OpenAI to refine the missing fields.
        """
        threshold = 15  # Minimal characters considered sufficient for a field
        local_missing = []
        for field in self.required_fields:
            if self.fields_complete.get(field, False):
                continue
            if field not in self.context or len(self.context[field].strip()) < threshold:
                local_missing.append(field)
        if not local_missing:
            return []
        
        prompt = f"""
            You are a business assistant evaluating whether the context contains sufficient detail for these fields:
            Problem, Persona, Objective, Scenario, Geography, and Constraints.
            Current context:
            {json.dumps(self.context, indent=2)}
            List any fields that still require additional detail. If all fields are sufficiently provided, reply with "DONE".
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
                missing = [field for field in local_missing if field in ai_missing]
                return missing if missing else local_missing
        except Exception as e:
            return local_missing

    def generate_dynamic_followup_question(self, missing_field):
        """
        Uses OpenAI to generate a dynamic follow-up question for a specific missing field.
        Incorporates the user-friendly prompt for that field.
        """
        current_answer = self.context.get(missing_field, "No information provided")
        # Use the friendly prompt if available; fallback to a generic question.
        friendly_prompt = self.question_prompts.get(
            missing_field,
            f"Could you please provide more details about your {missing_field}?"
        )
        prompt = f"""
            You are a business doctor helping a small business owner refine their information.
            The essential information needed includes: Problem, Persona, Objective, Scenario, Geography, and Constraints.
            For the field "{missing_field}", the current answer is: "{current_answer}".
            Using the following guidance: "{friendly_prompt}"
            Ask a specific, clear follow-up question to gather additional detail for "{missing_field}".
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
        Processes user input, updates context, and follows a sequential process.
        For a field that’s already answered, appends new details.
        Then evaluates if additional detail is needed; if so, generates a follow-up question using the friendly prompt.
        """
        threshold = 15  # Same threshold as evaluate_context
        
        if field_being_answered:
            if field_being_answered in self.context and self.context[field_being_answered].strip():
                self.context[field_being_answered] += " " + user_input.strip()
            else:
                self.context[field_being_answered] = user_input.strip()
            # Increase tracking for that field.
            self.fields_asked[field_being_answered] = self.fields_asked.get(field_being_answered, 0) + 1
            if len(self.context[field_being_answered].strip()) >= threshold:
                self.fields_complete[field_being_answered] = True
        else:
            if "problem" not in self.context:
                self.context["problem"] = user_input.strip()
                if len(self.context["problem"].strip()) >= threshold:
                    self.fields_complete["problem"] = True

        missing_fields = self.evaluate_context()
        filtered_missing = [field for field in missing_fields if self.fields_asked.get(field, 0) == 0]

        if not missing_fields:
            return {"status": "complete", "context": self.context}
        elif not filtered_missing:
            for field in missing_fields:
                self.fields_complete[field] = True
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
