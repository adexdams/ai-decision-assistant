# test_ai_processing.py
from backend.ai_processing import generate_expert_discussion

sample_context = {
    "problem": "Sales have been declining despite increased marketing efforts.",
    "persona": "Owner of a small retail business",
    "objective": "Increase sales and customer engagement",
    "scenario": "The business is located in a competitive urban area",
    "constraints": "Limited budget and staffing",
    "vision": "Long-term sustainable growth with a loyal customer base"
}
sample_experts = ["Business Strategy Expert", "Financial Expert", "Marketing Specialist"]

discussion = generate_expert_discussion(sample_context, sample_experts)
print(discussion)