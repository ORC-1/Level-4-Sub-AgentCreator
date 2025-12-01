from typing import Dict, Any, List
from dataclasses import dataclass
from utils.logger import log_event
from llm.factory import create_llm_client
from core.llm_selector import ModelSelection

@dataclass
class QAResult:
    """Quality assurance test result"""
    passed: bool
    scores: Dict[str, float]
    reason: str
    feedback: str

def quality_assurance_test(
    agent_config: Dict[str, Any],
    llm_instance: ModelSelection,
    structured_instruction: Dict[str, Any]
) -> Dict[str, Any]:
    """
    SPICE-inspired quality assurance using adversarial self-play.
    
    Challenger Role: Generate test questions at the frontier of capability
    Reasoner Role: The newly created agent attempts to answer
    
    Reference: SPICE paper (arXiv:2510.24684v1)
    """
    log_event("QA_TEST_START", agent_id=agent_config["agent_id"])
    
    # Generate challenge questions (Challenger role)
    challenge_questions = generate_challenge_questions(
        agent_config["agent_type"],
        agent_config["capabilities"],
        num_questions=5
    )
    
    # Agent attempts to answer (Reasoner role)
    responses = []
    for question in challenge_questions:
        log_event("QA_QUESTION", question=question)
        response = simulate_agent_response(agent_config, question, llm_instance)
        responses.append(response)
    
    # Score responses
    scores = evaluate_responses(responses, challenge_questions)
    
    # Calculate variance (SPICE-inspired metric)
    correctness_variance = calculate_variance([s["correct"] for s in scores])
    
    # Quality thresholds
    avg_score = sum(s["score"] for s in scores) / len(scores)
    min_acceptable_score = 0.6
    optimal_variance_range = (0.15, 0.35)  # Near 0.25 for 50% pass rate
    
    passed = (
        avg_score >= min_acceptable_score and
        optimal_variance_range[0] <= correctness_variance <= optimal_variance_range[1]
    )
    
    qa_result = {
        "passed": passed,
        "scores": {
            "average": avg_score,
            "variance": correctness_variance,
            "individual": scores
        },
        "reason": generate_qa_reason(passed, avg_score, correctness_variance),
        "feedback": generate_qa_feedback(scores, agent_config)
    }
    
    log_event("QA_TEST_COMPLETE",
             agent_id=agent_config["agent_id"],
             passed=passed,
             avg_score=avg_score,
             variance=correctness_variance)
    
    return qa_result

def generate_challenge_questions(
    agent_type: str,
    capabilities: List[str],
    num_questions: int = 5
) -> List[Dict[str, Any]]:
    """
    Generate challenge questions based on agent capabilities using LLM.
    Implements SPICE (Self-Play In Corpus Environments) methodology:
    - Questions should have varied difficulty to achieve ~0.25 variance
    - Variance of 0.25 corresponds to 50% pass rate (optimal for learning)
    - Questions grounded in real-world sources (tech interviews, StackOverflow, etc.)
    """
    log_event("QA_GENERATION_START", agent_type=agent_type, num_questions=num_questions)
    
    llm = create_llm_client()
    
    # SPICE-inspired prompt: request questions at the frontier of capability
    prompt = f"""Generate {num_questions} technical interview questions for an AI agent.

Role: {agent_type}
Capabilities: {', '.join(capabilities)}

REQUIREMENTS:
1. Mix difficulty levels (easy 0.2-0.4, medium 0.5-0.6, hard 0.7-0.9)
2. Base on real interview questions (Google, Amazon, StackOverflow, LeetCode)
3. Target 50% pass rate overall
4. Keep answers concise (1-2 sentences max)

CRITICAL: Return ONLY valid JSON array. No markdown, no code blocks, no extra text.

Example format:
[
  {{"q": "Question text here", "answer": "Brief answer", "difficulty": 0.3, "source": "Google"}},
  {{"q": "Another question", "answer": "Brief answer", "difficulty": 0.6, "source": "LeetCode"}}
]

Generate {num_questions} questions now:"""

    try:
        response = llm.generate_json(
            prompt=prompt,
            system_instruction="Return only a valid JSON array. No markdown formatting. No code blocks.",
            schema={"type": "array", "items": {"type": "object"}}
        )
        
        questions = response["parsed_json"]
        
        # Validate structure
        if not isinstance(questions, list):
            # Try to extract from string if needed
            if isinstance(questions, str):
                import json
                questions = json.loads(questions)
            else:
                questions = [questions]
            
        valid_questions = []
        for q in questions:
            if isinstance(q, dict) and "q" in q and "answer" in q:
                # Clean up any potential formatting issues
                valid_questions.append({
                    "q": str(q["q"]).strip(),
                    "answer": str(q["answer"]).strip(),
                    "difficulty": float(q.get("difficulty", 0.5)),
                    "source": str(q.get("source", "Generated")).strip()
                })
        
        # Verify we have enough questions
        if len(valid_questions) < num_questions:
            log_event("QA_GENERATION_WARNING", 
                     expected=num_questions, 
                     received=len(valid_questions),
                     message="Falling back to ensure minimum questions")
            
            # Add fallback questions to reach target
            while len(valid_questions) < num_questions:
                difficulty = 0.3 if len(valid_questions) == 0 else (0.6 if len(valid_questions) == 1 else 0.8)
                valid_questions.append({
                    "q": f"Explain a {['basic', 'intermediate', 'advanced'][len(valid_questions) % 3]} concept related to {agent_type}",
                    "answer": "Detailed technical explanation",
                    "difficulty": difficulty,
                    "source": "Fallback"
                })
        
        result_questions = valid_questions[:num_questions]
        
        # Log difficulty distribution for debugging
        difficulties = [q["difficulty"] for q in result_questions]
        log_event("QA_GENERATION_SUCCESS", 
                 num_questions=len(result_questions),
                 avg_difficulty=sum(difficulties)/len(difficulties) if difficulties else 0,
                 difficulty_range=(min(difficulties), max(difficulties)) if difficulties else (0, 0))
        
        return result_questions
        
    except Exception as e:
        log_event("QA_GENERATION_ERROR", error=str(e))
        # Fallback: generate questions with varied difficulty
        return [
            {
                "q": f"Basic task: Explain the fundamentals of {agent_type}",
                "answer": "Clear explanation of core concepts",
                "difficulty": 0.3,
                "source": "Fallback"
            },
            {
                "q": f"Intermediate: Apply {capabilities[0] if capabilities else 'your skills'} to solve a problem",
                "answer": "Practical application with reasoning",
                "difficulty": 0.6,
                "source": "Fallback"
            },
            {
                "q": f"Advanced: Optimize and debug complex {agent_type} scenarios",
                "answer": "Deep technical solution with edge cases",
                "difficulty": 0.8,
                "source": "Fallback"
            }
        ][:num_questions]

def simulate_agent_response(agent_config: Dict[str, Any], question: Dict[str, Any], llm_instance: ModelSelection) -> str:
    """
    Agent responds to challenge question using the selected LLM model.
    """
    log_event("AGENT_RESPONSE_START", 
             agent_id=agent_config["agent_id"],
             question=question["q"][:100])
    
    # Create LLM client using the selected model
    llm = create_llm_client()
    
    # Use agent's system prompt
    system_instruction = agent_config["system_prompt"]
    
    # Format the question
    prompt = f"""Answer this test question that evaluates your capabilities:

Question: {question['q']}

Provide a clear, concise answer. If you're unsure, explain your reasoning."""
    
    try:
        # Ask for JSON response with a "text" field
        prompt += "\n\nReturn your answer in JSON format: {\"text\": \"your answer\"}"
        response = llm.generate_json(prompt, system_instruction, schema={})
        
        log_event("AGENT_RESPONSE_SUCCESS",
                 agent_id=agent_config["agent_id"],
                 response_length=len(response["parsed_json"]["text"]))
        
        return response["parsed_json"]["text"]
        
    except Exception as e:
        log_event("AGENT_RESPONSE_ERROR",
                 agent_id=agent_config["agent_id"],
                 error=str(e))
        return f"Error generating response: {e}"

def evaluate_responses(
    responses: List[str],
    questions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Evaluate agent responses against expected answers using LLM-based semantic similarity.
    """
    scores = []
    llm = create_llm_client()
    
    for response, question in zip(responses, questions):
        # Use LLM to evaluate semantic similarity and accuracy
        eval_prompt = f"""You are an expert evaluator. Compare the agent's response to the expected answer.

Question: {question['q']}
Expected Answer: {question['answer']}
Agent's Response: {response}

Evaluate the agent's response on:
1. Correctness: Does it answer the question correctly?
2. Similarity: Is it semantically similar to the expected answer?
3. Completeness: Does it cover the key points?

Return JSON with:
- "correct": boolean (true if the response is acceptable)
- "score": float 0.0-1.0 (quality score)
- "reasoning": string (brief explanation)
"""
        
        try:
            eval_response = llm.generate_json(
                prompt=eval_prompt,
                system_instruction="You are a strict but fair evaluator.",
                schema={}
            )
            
            result = eval_response["parsed_json"]
            correct = result.get("correct", False)
            score = result.get("score", 0.0)
            
        except Exception as e:
            log_event("EVALUATION_ERROR", error=str(e))
            # Fallback to simple substring matching
            correct = question["answer"].lower() in response.lower()
            score = 1.0 if correct else 0.0
        
        scores.append({
            "question": question["q"],
            "correct": correct,
            "score": score,
            "difficulty": question["difficulty"]
        })
    
    return scores

def calculate_variance(binary_outcomes: List[bool]) -> float:
    """
    Calculate variance of binary outcomes (Bernoulli variance).
    
    SPICE Framework:
    - Variance = p(1-p) where p is the success rate
    - Optimal variance ~0.25 (when p=0.5, i.e., 50% pass rate)
    - This indicates questions are at the frontier of capability
    - Too low variance (0.0 or near 1.0) means questions are too easy or too hard
    """
    if not binary_outcomes:
        return 0.0
    
    p = sum(binary_outcomes) / len(binary_outcomes)
    variance = p * (1 - p)
    
    log_event("VARIANCE_CALCULATED", 
             pass_rate=p, 
             variance=variance,
             optimal_range="0.15-0.35")
    
    return variance

def generate_qa_reason(passed: bool, avg_score: float, variance: float) -> str:
    """
    Generate human-readable reason for QA result based on SPICE criteria.
    
    SPICE Quality Metrics:
    1. Average score >= 0.6 (agent demonstrates competence)
    2. Variance in range [0.15, 0.35] (questions at capability frontier)
    """
    if not passed:
        if avg_score < 0.6:
            return (f"Agent scored below competence threshold "
                   f"(avg={avg_score:.2f} < 0.6). "
                   f"Agent needs more training or simpler tasks.")
        else:
            # Variance issue
            if variance < 0.15:
                if variance == 0.0:
                    return (f"Task difficulty not optimal (variance={variance:.3f}, expected ~0.25). "
                           f"All questions answered identically - need more varied difficulty levels.")
                else:
                    return (f"Task difficulty not optimal (variance={variance:.3f}, expected ~0.25). "
                           f"Questions too easy or too hard - need better difficulty distribution.")
            else:  # variance > 0.35
                return (f"Task difficulty not optimal (variance={variance:.3f}, expected ~0.25). "
                       f"Performance too inconsistent - questions may be poorly calibrated.")
    
    return (f"Agent passed all quality checks "
           f"(avg={avg_score:.2f}, variance={variance:.3f} ≈ 0.25)")

def generate_qa_feedback(scores: List[Dict], agent_config: Dict) -> str:
    """
    Generate actionable feedback for improvement based on SPICE analysis.
    
    Analyzes:
    - Which questions failed
    - Difficulty levels of failed questions
    - Patterns in failures
    """
    failed_questions = [s for s in scores if not s["correct"]]
    
    if not failed_questions:
        # Check if variance is good
        all_correct = all(s["correct"] for s in scores)
        if all_correct:
            return ("All questions answered correctly, but this may indicate "
                   "questions are too easy. Consider increasing difficulty.")
        return "Performance is optimal - continue with current difficulty level"
    
    # Analyze failure patterns
    failed_easy = [q for q in failed_questions if q["difficulty"] < 0.5]
    failed_hard = [q for q in failed_questions if q["difficulty"] >= 0.7]
    
    feedback_parts = []
    
    if failed_easy:
        feedback_parts.append(
            f"Failed {len(failed_easy)} easy question(s) - fundamental gaps detected"
        )
    
    if failed_hard:
        feedback_parts.append(
            f"Failed {len(failed_hard)} hard question(s) - expected at capability frontier"
        )
    
    # List specific questions to focus on
    feedback_parts.append("Focus on improving:")
    for q in failed_questions[:3]:  # Top 3 failures
        feedback_parts.append(f"  - '{q['question']}' (difficulty: {q['difficulty']:.1f})")
    
    return "\n".join(feedback_parts)