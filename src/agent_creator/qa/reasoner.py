from typing import Dict, Any
from ..llm.factory import create_llm_client
from ..utils.logger import log_event


def agent_response_to_challenge(
    agent_config: Dict[str, Any],
    question: Dict[str, Any]
) -> str:
    """
    Agent attempts to answer challenge question (Reasoner role in SPICE).
    """
    log_event("AGENT_RESPONSE_START",
             agent_id=agent_config["agent_id"],
             question=question["question"][:100])
    
    # Create LLM client with agent's configuration
    llm = create_llm_client()
    
    # Use agent's system prompt
    system_instruction = agent_config["system_prompt"]
    
    # Format question
    prompt = f"""Answer this test question that evaluates your capabilities:

Question: {question['question']}

Provide a clear, concise answer. If you're unsure, explain your reasoning."""
    
    try:
        # We use generate_json but here we just want text. 
        # Since our interface is generate_json, we wrap the prompt to ask for a JSON response with a "text" field
        # or we update the interface. For now, let's ask for JSON.
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