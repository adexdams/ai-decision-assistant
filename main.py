# main.py
from backend.secretary import Secretary
from backend.expert_manager import select_experts
from backend.ai_processing import generate_expert_discussion

if __name__ == "__main__":
    secretary = Secretary()
    # Initial input
    user_prompt = input("Describe your business challenge: ")
    response = secretary.analyze_input(user_prompt)

    # Continue asking follow-up questions until context is complete
    while response["status"] == "incomplete":
        print("Follow-up: ", response["question"])
        answer = input("Your answer: ")
        response = secretary.analyze_input(answer, field_being_answered=response["missing_field"])

    print("All context gathered:", response["context"])
    print("Let me get you the relevant experts...")
    experts = select_experts(response["context"])
    print("Entering meeting with: ", ", ".join(experts))

    print("\nSimulating expert discussion and generating strategic recommendations...\n")
    discussion = generate_expert_discussion(response["context"], experts)
    print(discussion)