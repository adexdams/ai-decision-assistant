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
        # Define the sequential order of required fields
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
        # Storage for context gathered from the user
        self.context = {}
        # Index to track which field is currently being asked for
        self.current_field_index = 0  
        # Total number of fields
        self.max_fields = len(self.required_fields)

    def next_followup(self):
        """
        Returns the next question in the sequence.
        If all fields have been answered, returns None.
        """
        if self.current_field_index < self.max_fields:
            field = self.required_fields[self.current_field_index]
            return {"field": field, "question": self.question_prompts[field]}
        else:
            return None

    def analyze_input(self, user_input):
        """
        Processes the user input sequentially.
        The first input addresses the current required field.
        It then advances to the next field in the predetermined order.
        Returns a response with a follow-up question if more fields remain,
        or indicates completion if all fields have been answered.
        """
        # Assign the user's input to the current field
        if self.current_field_index < self.max_fields:
            field = self.required_fields[self.current_field_index]
            self.context[field] = user_input.strip()
            self.current_field_index += 1

        next_q = self.next_followup()
        if next_q:
            return {"status": "incomplete", "question": next_q["question"], "missing_field": next_q["field"], "context": self.context}
        else:
            return {"status": "complete", "context": self.context}
