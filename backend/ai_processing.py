# backend/ai_processing.py
from openai import OpenAI

client = OpenAI()
import json
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment!")


def generate_expert_discussion(context, experts):
    """
    Generates a simulated expert discussion and meeting conclusion based on the user's context.
    The output will include:
      1. A sequential discussion where each expert states their specialized perspective.
      2. A final meeting conclusion with an executive summary slide format that presents:
         - What's happening?
         - What are the options? (maximum of 3 options)
         - What's recommended?
    The discussion should first determine whether the decision is strategic (long-term, high impact)
    or operational/tactical (short-term, execution-focused) and then tailor its conversation accordingly.

    The recommendations must:
      • Offer neutral comparisons, scenario analyses, and "what-if" forecasts.
      • Include pattern-rich stories, real-world analogies, or frameworks (such as decision matrices or scenario ladders)
        that map to past wins or losses.
      • Be brief and structured (no more than 1 page), clearly displaying risk-reward tradeoffs and blind spots
        (e.g., what would have to be true for an option to fail).
      • Help the user think clearly and quickly by highlighting 2-3 key options with supporting analysis.

    Final output format:
    Executive Summary Slide:
      - Highlight the conclusion or recommendation upfront.
      - Then, list 2-3 strategic options with supporting analysis.
      - Use a decision matrix or quadrant map if applicable.
      - Include a red team/blue team analysis with opposing viewpoints on risks and hidden upsides.

    **New Instruction:**
    You are a panel of experts wearing multiple hats – including seasoned business consultants,
    technical experts, successful entrepreneurs (mentors), and specialized consultants in various fields –
    gathered in a meeting to help a small business owner or aspiring founder make a critical decision.
    Each expert should speak from their specialized perspective. For instance, if technical expertise is required,
    adopt the voice of a technical expert; if entrepreneurial insights are needed, speak as a successful mentor.
    Your discussion should reflect a comprehensive, multi-dimensional viewpoint that leverages the unique strengths
    of each identified role.

    Tailor your final output based on the decision type (strategic vs. operational/tactical) inferred from the context.
    """
    prompt = f"""
You are a panel of experts wearing multiple hats – including seasoned business consultants, technical experts, successful entrepreneurs (mentors), and specialized consultants – gathered in a meeting to help a small business owner or aspiring founder make a critical decision.
The user's context is:
{json.dumps(context, indent=2)}

The experts present are: {', '.join(experts)}.

First, determine whether the decision is strategic (long-term, high impact) or operational/tactical (short-term, execution-focused), and then simulate a sequential discussion where each expert states their individual, specialized perspective on the problem. 
The experts debate potential strategies, just as in a real brainstorming meeting.
Use real-world analogies, neutral comparisons, and "what-if" forecasts to highlight both risks and opportunities.
Incorporate geographic details from the context into your analysis so that regional nuances enhance your recommendations.

After the discussion, produce a final meeting conclusion in the following format:

Meeting Resolutions:
"Here are our recommendations for approaches to help you achieve {context.get('objective', 'your goal')} (Present 2-3 clear, varied strategic options in bullet points below.):
   1. [Strategic Choice 1]
   2. [Strategic Choice 2]
   3. [Strategic Choice 3]

Here are our analysis of each choice and the additional insights you need to help you make the best decision."

For each of the three strategic choices, include:
1. A description of the strategic option.
2. A detailed assessment of the risks and rewards, including both the upside and the downside. Include evidentiary data and facts to support your assessment, 
with links at the bottom (do not make any of the data up). Also, mention what would need to happen for each option to fail.
3. A discussion of the leadership style required to execute this choice.
4. A description of the value system and personality traits of a person who would choose this option (for example, risk-taking, conservative, community-oriented, religious, etc.).
5. Draw a 2v2 decision quadrant table of impact vs risk for all strategic options.
6. Highlight the preferred option with a top-down explanation of its expected impact.


Output the final result as a clear, structured meeting conclusion with both the sequential discussion and the formatted recommendations section. 
Ensure the output is concise (no more than one page) and structured to help the user quickly grasp the trade-offs and make an informed decision.
"""
    try:
        response = client.chat.completions.create(model="gpt-4",
        messages=[{"role": "system", "content": prompt}])
        discussion = response.choices[0].message.content
        return discussion
    except Exception as e:
        return f"Error generating expert discussion: {e}"


# NEW: Function to generate an extra follow-up response based on the user's additional question.
def generate_extra_followup_response(extra_question, context, experts):
    """
    Generates a targeted response to an extra follow-up question by identifying the most relevant expert perspective
    from the previous discussion and responding directly in that expert's voice.

    The prompt instructs the panel to consider the extra follow-up question in the context of the user's situation
    and the previous expert discussion, then provide a concise, actionable answer that includes relevant risk-reward
    analysis, scenario comparisons, and real-world analogies where applicable.

    The answer should be formatted as:
        "<Expert Role>: <Answer>"
    """
    prompt = f"""
You are a panel of experts wearing multiple hats – including seasoned business consultants, technical experts, successful entrepreneurs (mentors), and specialized consultants – gathered in a meeting to help a small business owner or aspiring founder make critical decisions.
The user's context is:
{json.dumps(context, indent=2)}

The experts present are: {', '.join(experts)}.

An expert meeting has already taken place and recommendations have been provided.
Now, the user has asked an additional follow-up question:
"{extra_question}"

Based on the previous discussion and this extra follow-up question, determine which expert's perspective is most relevant.
Respond directly in that expert's voice with a concise answer addressing the follow-up question, including any pertinent risk-reward considerations, scenario analyses, and real-world analogies.
Use second-person language where appropriate and keep your response brief and actionable.
**Return your answer in the following format: "ExpertRole: Your answer here."**
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        extra_response = response.choices[0].message.content
        return extra_response
    except Exception as e:
        return f"Error generating extra follow-up response: {e}"
