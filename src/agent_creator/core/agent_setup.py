from typing import Dict, Any

def get_agent_setup_data(structured_instruction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create initial agent configuration from structured instructions.
    """
    import uuid
    
    agent_id = str(uuid.uuid4())
    
    # Basic configuration setup
    config = {
        "agent_id": agent_id,
        "agent_type": structured_instruction.get("agent_type", "general"),
        "capabilities": structured_instruction.get("capabilities", []),
        "constraints": structured_instruction.get("constraints", []),
        "success_criteria": structured_instruction.get("success_criteria", ""),
        "system_prompt": f"You are a {structured_instruction.get('agent_type', 'assistant')}. "
                         f"Your capabilities include: {', '.join(structured_instruction.get('capabilities', []))}. "
                         f"Constraints: {', '.join(structured_instruction.get('constraints', []))}.",
        "metadata": structured_instruction.get("_metadata", {})
    }
    
    return config
