from typing import Dict, Any
from utils.logger import log_event
from .mdp_converter import convert_query_via_mdp
from .agent_setup import get_agent_setup_data
from .llm_selector import select_llm
from .retry import genesis_retry
from qa.qa_vet import quality_assurance_test
from .agent_generator import create_agent_a2a

class ValidationError(Exception):
    """Custom exception for input validation failures"""
    pass

def genesis(instruction: str) -> Dict[str, Any]:
    """Genesis Agent: Entry point for dynamic agent creation."""
    log_event("GENESIS_START", instruction_length=len(instruction) if instruction else 0)
    
    # Input validation
    if not instruction:
        raise ValidationError("Instruction cannot be null or empty")
    
    if len(instruction.strip()) < 10:
        raise ValidationError("Instruction too short - provide detailed requirements (min 10 chars)")
    
    if len(instruction) > 5000:
        raise ValidationError("Instruction too long - please be more concise (max 5000 chars)")
    
    log_event("VALIDATION_PASSED", instruction_preview=instruction[:100])
    
    try:
        # Process 2: Convert to structured instruction via MDP
        structured_instruction = convert_query_via_mdp(instruction)
        
        # Process 3: Create agent configuration
        agent_config = get_agent_setup_data(structured_instruction)
        
        # Process 4: Select LLM
        llm_instance = select_llm(structured_instruction, agent_config)
       
        # Add selected model to agent config for agent generation
        agent_config["selected_model"] = llm_instance.model_name
        agent_config["model_temperature"] = llm_instance.temperature
        agent_config["model_context_window"] = llm_instance.context_window
        
        # Process 5: Quality assurance via SPICE testing
        qa_result = quality_assurance_test(agent_config, llm_instance, structured_instruction)
        print("qa_result", qa_result)
        if not qa_result["passed"]:
            log_event("QA_FAILED", 
                     agent_id=agent_config["agent_id"],
                     reason=qa_result["reason"],
                     test_scores=qa_result["scores"])
            
            # Attempt retry with enhanced configuration (up to 3 attempts)
            return genesis_retry(
                qa_result["feedback"],
                agent_config,
                llm_instance,
                structured_instruction
            )
        
        # Process 6: Create Agent class and Register with A2A network
        a2a_registration = create_agent_a2a(agent_config)
        
        log_event("GENESIS_SUCCESS",
                 agent_id=agent_config["agent_id"],
                 agent_type=agent_config["agent_type"],
                 qa_scores=qa_result["scores"])
        
        return {
            "success": True,
            "agent_id": agent_config["agent_id"],
            "agent_type": agent_config["agent_type"],
            "capabilities": agent_config["capabilities"],
            "a2a_endpoint": a2a_registration["endpoint"],
            "qa_scores": qa_result["scores"]
        }
        
    except Exception as e:
        log_event("GENESIS_ERROR", error=str(e), error_type=type(e).__name__)
        raise