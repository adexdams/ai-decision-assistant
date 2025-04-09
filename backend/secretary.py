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
        # Essential fields we need for context in a fixed order
        self.required_fields = ["problem", "persona", "objective", "scenario", "geography", "constraints"]
        # Mapping of fields to friendly, user-understandable prompts
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
        # Count of dynamic context questions asked so far
        self.context_questions_asked = 0
        # Maximum number of follow-up questions allowed overall
        self.max_questions = 3
        # Track how many times each field has been asked (to avoid repetition)
        self.fields_asked = {}
        # Track which fields are considered complete based on provided detail
        self.fields_complete = {}


    def evaluate_context(self):
        """
        Performs a local check of the essential fields using a minimal character threshold.
        Uses a threshold of 15 characters for most fields and 10 for persona.
        Fields marked as complete are skipped.
        Then uses OpenAI to refine which fields still require additional detail.
        Returns a list of missing fields; if all are complete, returns an empty list.
        """
        default_threshold = 15
        local_missing = []
        for field in self.required_fields:
            # For "persona", lower the threshold
            field_threshold = 10 if field == "persona" else default_threshold
            if self.fields_complete.get(field, False):
                continue
            if field not in self.context or len(self.context[field].strip()) < field_threshold:
                local_missing.append(field)
        if not local_missing:
            return []


        # Use OpenAI to evaluate the context and refine the missing fields  
        prompt = f"""
            You are a business assistant evaluating whether the context contains sufficient detail for these fields:
            Problem, Persona, Objective, Scenario, Geography, and Constraints.
            Current context:
            {json.dumps(self.context, indent=2)}
            List any fields that still require additional detail.
            If all fields have sufficient detail, reply with "DONE".
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
        Uses the friendly prompt from self.question_prompts for guidance.
        """
        current_answer = self.context.get(missing_field, "No information provided")
        friendly_prompt = self.question_prompts.get(
            missing_field,
            f"Would you mind elaborating a bit more on your {missing_field}?"
        )
        prompt = f"""
            You are a business doctor helping a small business owner refine their information.
            Essential details needed: Problem, Persona, Objective, Scenario, Geography, and Constraints.
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
            return f"Would you mind elaborating a bit more on your {missing_field}?"


    def analyze_input(self, user_input, field_being_answered=None):
        """
        Processes user input and updates the context.
        If a specific field is being answered, appends new input to build a richer response.
        Once the updated response meets a minimum detail threshold, the field is marked complete.
        The method then evaluates which fields still need additional detail.
        If a field hasn't been asked before, it generates a follow-up question.
        If all fields are complete (or maximum follow-ups are reached), it returns complete.
        """
        threshold = 15  # Default threshold; "persona" uses 10 as applied in evaluate_context.
        if field_being_answered:
            # Merge new input with existing text for the given field.
            if field_being_answered in self.context and self.context[field_being_answered].strip():
                self.context[field_being_answered] += " " + user_input.strip()
            else:
                self.context[field_being_answered] = user_input.strip()
            # Increment the count for how many times this field has been asked.
            self.fields_asked[field_being_answered] = self.fields_asked.get(field_being_answered, 0) + 1
            # Mark the field as complete if its content reaches the threshold.
            field_threshold = 10 if field_being_answered == "persona" else threshold
            if len(self.context[field_being_answered].strip()) >= field_threshold:
                self.fields_complete[field_being_answered] = True
        else:
            # For the initial input, assume it addresses "problem".
            if "problem" not in self.context:
                self.context["problem"] = user_input.strip()
                if len(self.context["problem"].strip()) >= threshold:
                    self.fields_complete["problem"] = True

        # Evaluate the current context.
        missing_fields = self.evaluate_context()
        # Filter out fields that have already been asked.
        filtered_missing = [field for field in missing_fields if self.fields_asked.get(field, 0) == 0]

        if not missing_fields:
            return {"status": "complete", "context": self.context}
        elif not filtered_missing:
            # If all missing fields have been asked before, mark them complete to avoid repetition.
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