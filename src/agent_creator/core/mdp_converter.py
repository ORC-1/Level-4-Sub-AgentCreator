from typing import Dict, Any
from llm.factory import create_llm_client
from utils.logger import log_event


def convert_query_via_mdp(instruction: str) -> Dict[str, Any]:
    """
    Apply Markov Decision Process formulation to transform natural language
    into structured agent configuration using REAL Gemini API.
    
    MDP Mapping:
    - State: Current system state + user instruction
    - Action: Generated structured configuration
    - Reward: Alignment score with user intent
  
    """
    log_event("MDP_CONVERSION_START", instruction_length=len(instruction))
    
    # Create LLM client (provider agnostic, defaults to config)
    log_event("Creating LLM client")
    llm = create_llm_client()
    log_event("LLM client created")
    # Define JSON schema for structured output
    schema = {
        "type": "object",
        "required": ["agent_type", "capabilities", "success_criteria"],
        "properties": {
            "agent_type": {"type": "string"},
            "capabilities": {"type": "array", "items": {"type": "string"}},
            "constraints": {"type": "array", "items": {"type": "string"}},
            "success_criteria": {"type": "string"},
            "estimated_complexity": {"type": "string", "enum": ["low", "medium", "high"]}
        }
    }
    
    # System instruction for MDP-based analysis
    system_instruction = """You are an MDP-based agent configuration system.
Your role is to analyze user instructions and extract structured configuration
by treating the prompt as the current state and configuration as the action."""
    
    # Create prompt for structured extraction
    prompt = f"""Analyze this instruction and extract structured configuration:

Instruction: {instruction}

Extract the following in JSON format:
1. agent_type: Primary role (e.g., "data_analyst", "code_generator", "researcher", "general_assistant")
2. capabilities: List of specific skills required (be specific and actionable)
3. constraints: Any limitations or requirements (e.g., "must_use_python", "realtime_processing")
4. success_criteria: Clear success metric (e.g., "Generate accurate statistical summary")
5. estimated_complexity: "low", "medium", or "high"

Return ONLY valid JSON matching this structure."""
    
    try:
        response = llm.generate_json(
            prompt=prompt,
            system_instruction=system_instruction,
            schema=schema
        )
        
        structured_config = response["parsed_json"]
        
        # Add metadata
        structured_config["_metadata"] = {
            "tokens_used": response["total_tokens"],
            "api_cost": response["cost_usd"],
            "model": response["model"]
        }
        
        log_event("MDP_CONVERSION_SUCCESS",
                 agent_type=structured_config["agent_type"],
                 tokens=response["total_tokens"],
                 cost=response["cost_usd"])
        
        return structured_config
        
    except Exception as e:
        log_event("MDP_CONVERSION_ERROR", error=str(e))
        raise ValueError(f"Failed to convert instruction to structured config: {e}")