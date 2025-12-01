from typing import List, Dict, Any
from llm.factory import create_llm_client
from utils.logger import log_event


def generate_challenge_questions(
    agent_type: str,
    capabilities: List[str],
    num_questions: int = 5
) -> List[Dict[str, Any]]:
    """
    Generate challenge questions using Gemini (Challenger role in SPICE).
    
    Reference: SPICE paper (arXiv:2510.24684v1)
    """
    log_event("CHALLENGE_GENERATION_START",
             agent_type=agent_type,
             num_questions=num_questions)
    
    llm = create_llm_client()  # Higher temp for diversity handled in prompt or client config if supported
    
    prompt = f"""You are the Challenger in a SPICE self-play QA system.
Generate {num_questions} challenging test questions for this agent:

Agent Type: {agent_type}
Capabilities: {', '.join(capabilities)}

Requirements:
1. Questions should test the FRONTIER of capability (not too easy, not impossible)
2. Target 50% success rate (optimal difficulty for learning)
3. Include varying difficulty levels
4. Provide clear expected answers
5. Include difficulty rating (0.0 = trivial, 1.0 = impossible)

Return JSON array:
[
    {{
        "question": "test question",
        "expected_answer": "correct answer or key criteria",
        "difficulty": 0.0-1.0,
        "tests_capability": "which capability this tests"
    }},
    ...
]"""
    
    try:
        response = llm.generate_json(prompt, system_instruction="You are a challenging QA tester.", schema={})
        questions = response["parsed_json"]
        
        # Ensure we have a list
        if not isinstance(questions, list):
            questions = [questions]
        
        log_event("CHALLENGE_GENERATION_SUCCESS",
                 num_generated=len(questions),
                 tokens=response["total_tokens"])
        
        return questions[:num_questions]
        
    except Exception as e:
        log_event("CHALLENGE_GENERATION_ERROR", error=str(e))
        # Return fallback questions
        return [
            {
                "question": f"What is your primary function as a {agent_type}?",
                "expected_answer": f"Provide {agent_type} services",
                "difficulty": 0.2,
                "tests_capability": "self_awareness"
            }
        ]