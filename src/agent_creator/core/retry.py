from typing import Dict, Any
from utils.logger import log_event
from .agent_setup import get_agent_setup_data
from .llm_selector import select_llm
from qa.qa_vet import quality_assurance_test
from .agent_generator import create_agent_a2a

def genesis_retry(
    feedback: str,
    agent_config: Dict[str, Any],
    llm_instance: Any,
    structured_instruction: Dict[str, Any],
    retry_count: int = 0,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Retry agent creation with adjustments based on QA feedback.
    
    Implements intelligent retry strategy:
    - Retry 1: Adjust system prompt based on failed questions
    - Retry 2: Modify capabilities and constraints
    - Retry 3: Simplify or enhance based on variance
    - After 3 attempts: Request human intervention
    
    Args:
        feedback: QA feedback from failed test
        agent_config: Current agent configuration
        llm_instance: Selected LLM model
        structured_instruction: Original structured instruction
        retry_count: Current retry attempt (0-indexed)
        max_retries: Maximum retry attempts before giving up
    """
    log_event("GENESIS_RETRY_START", 
             retry_count=retry_count + 1,
             max_retries=max_retries,
             feedback=feedback[:200])
    
    # Check if we've exhausted retries
    if retry_count >= max_retries:
        log_event("GENESIS_RETRY_EXHAUSTED", 
                 attempts=retry_count,
                 final_feedback=feedback)
        return {
            "success": False,
            "message": f"QA failed after {max_retries} retry attempts - human intervention required",
            "feedback": feedback,
            "suggestion": "Review agent configuration and requirements. Consider simplifying the task or providing more specific instructions.",
            "retry_count": retry_count
        }
    
    # Analyze feedback to determine adjustment strategy
    adjustment_strategy = _determine_adjustment_strategy(feedback, retry_count)
    
    log_event("RETRY_STRATEGY", 
             attempt=retry_count + 1,
             strategy=adjustment_strategy)
    
    # Apply adjustments to agent config
    adjusted_config = _apply_adjustments(
        agent_config, 
        structured_instruction, 
        adjustment_strategy, 
        feedback
    )
    
    # Re-run QA with adjusted configuration
    log_event("RETRY_QA_START", attempt=retry_count + 1)
    qa_result = quality_assurance_test(adjusted_config, llm_instance, structured_instruction)
    
    if qa_result["passed"]:
        log_event("RETRY_SUCCESS", 
                 attempt=retry_count + 1,
                 final_scores=qa_result["scores"])
        
        # Generate agent with successful config
        a2a_registration = create_agent_a2a(adjusted_config)
        
        return {
            "success": True,
            "agent_id": adjusted_config["agent_id"],
            "agent_type": adjusted_config["agent_type"],
            "capabilities": adjusted_config["capabilities"],
            "a2a_endpoint": a2a_registration["endpoint"],
            "qa_scores": qa_result["scores"],
            "retry_count": retry_count + 1
        }
    else:
        # Recursive retry with incremented count
        log_event("RETRY_FAILED", 
                 attempt=retry_count + 1,
                 reason=qa_result["reason"])
        
        return genesis_retry(
            qa_result["feedback"],
            adjusted_config,
            llm_instance,
            structured_instruction,
            retry_count + 1,
            max_retries
        )


def _determine_adjustment_strategy(feedback: str, retry_count: int) -> str:
    """
    Determine what adjustment strategy to use based on feedback and retry count.
    """
    feedback_lower = feedback.lower()
    
    # Retry 1: Focus on prompt enhancement
    if retry_count == 0:
        if "variance" in feedback_lower or "difficulty" in feedback_lower:
            return "adjust_prompt_for_difficulty"
        elif "failed" in feedback_lower and "easy" in feedback_lower:
            return "strengthen_fundamentals"
        else:
            return "enhance_prompt_specificity"
    
    # Retry 2: Modify capabilities
    elif retry_count == 1:
        if "variance" in feedback_lower:
            return "adjust_capabilities"
        else:
            return "refine_constraints"
    
    # Retry 3: Last attempt - simplify or enhance drastically
    else:
        if "too easy" in feedback_lower or "100%" in feedback_lower:
            return "increase_complexity"
        else:
            return "simplify_requirements"


def _apply_adjustments(
    agent_config: Dict[str, Any],
    structured_instruction: Dict[str, Any],
    strategy: str,
    feedback: str
) -> Dict[str, Any]:
    """
    Apply adjustments to agent configuration based on strategy.
    """
    import copy
    adjusted_config = copy.deepcopy(agent_config)
    
    if strategy == "adjust_prompt_for_difficulty":
        # Enhance system prompt to handle edge cases better
        adjusted_config["system_prompt"] += (
            "\n\nIMPORTANT: Pay special attention to edge cases and complex scenarios. "
            "Provide detailed reasoning for challenging questions."
        )
        log_event("ADJUSTMENT_APPLIED", strategy=strategy, change="Enhanced system prompt")
    
    elif strategy == "strengthen_fundamentals":
        # Add emphasis on fundamental concepts
        adjusted_config["system_prompt"] += (
            "\n\nFocus on demonstrating strong understanding of fundamental concepts. "
            "Ensure accuracy in basic operations before tackling complex problems."
        )
        log_event("ADJUSTMENT_APPLIED", strategy=strategy, change="Added fundamentals focus")
    
    elif strategy == "enhance_prompt_specificity":
        # Make prompt more specific to capabilities
        caps_str = ", ".join(adjusted_config["capabilities"])
        adjusted_config["system_prompt"] += (
            f"\n\nYour core expertise areas are: {caps_str}. "
            "Demonstrate deep knowledge in these specific areas."
        )
        log_event("ADJUSTMENT_APPLIED", strategy=strategy, change="Added capability specifics")
    
    elif strategy == "adjust_capabilities":
        # Add or refine capabilities based on feedback
        if "capabilities" in adjusted_config:
            # Add a meta-capability for self-improvement
            if "continuous_learning" not in adjusted_config["capabilities"]:
                adjusted_config["capabilities"].append("continuous_learning")
                adjusted_config["system_prompt"] += (
                    "\n\nYou have the ability to learn from feedback and improve your responses."
                )
        log_event("ADJUSTMENT_APPLIED", strategy=strategy, change="Added learning capability")
    
    elif strategy == "refine_constraints":
        # Add constraints for better performance
        if "constraints" not in adjusted_config:
            adjusted_config["constraints"] = []
        adjusted_config["constraints"].append("prioritize_accuracy_over_speed")
        adjusted_config["system_prompt"] += (
            "\n\nPrioritize accuracy and thoroughness in your responses."
        )
        log_event("ADJUSTMENT_APPLIED", strategy=strategy, change="Added accuracy constraint")
    
    elif strategy == "increase_complexity":
        # Agent is too good - questions might be too easy
        # Add advanced reasoning requirement
        adjusted_config["system_prompt"] += (
            "\n\nDemonstrate advanced reasoning and consider multiple perspectives. "
            "Go beyond surface-level answers."
        )
        log_event("ADJUSTMENT_APPLIED", strategy=strategy, change="Increased complexity requirement")
    
    elif strategy == "simplify_requirements":
        # Simplify the agent's focus
        adjusted_config["system_prompt"] = (
            f"You are a {adjusted_config['agent_type']}. "
            f"Your primary capabilities are: {', '.join(adjusted_config['capabilities'][:3])}. "
            "Provide clear, accurate, and concise responses."
        )
        log_event("ADJUSTMENT_APPLIED", strategy=strategy, change="Simplified prompt")
    
    return adjusted_config