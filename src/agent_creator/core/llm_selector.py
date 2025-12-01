from typing import Dict, Any
from dataclasses import dataclass
from llm.factory import create_llm_client
from utils.logger import log_event


@dataclass
class ModelSelection:
    """Selected model configuration"""
    model_name: str
    context_window: int
    temperature: float
    reasoning: str
    estimated_cost_per_1k: float


def select_llm(
    structured_instruction: Dict[str, Any],
    agent_config: Dict[str, Any]
) -> ModelSelection:
    """
    Use Gemini to select the optimal model configuration.
    This implements "model-of-models" where Gemini helps choose the best setup.
    """
    log_event("LLM_SELECTION_START", 
             complexity=structured_instruction.get("estimated_complexity"))
    
    # Create LLM client for selection
    llm = create_llm_client()
    
    prompt = f"""You are an AI model selection expert. Analyze this agent configuration
and recommend the optimal LLM model.

Agent Type: {structured_instruction['agent_type']}
Complexity: {structured_instruction.get('estimated_complexity', 'medium')}
Capabilities Required: {', '.join(structured_instruction['capabilities'])}
Constraints: {', '.join(structured_instruction.get('constraints', []))}

Consider:
- Task complexity vs cost
- Context window requirements
- Specific capability needs (coding, reasoning, analysis)
- Budget constraints

Recommend ONE model with reasoning in JSON:
{{
    "model_name": "chosen_model",
    "context_window": number,
    "temperature": 0.0-1.0,
    "reasoning": "why this model",
    "estimated_cost_per_1k_tokens": number
}}"""
    
    try:
        # We need to construct the prompt to ask for JSON since our client expects it
        # The client's generate_json handles the call
        response = llm.generate_json(prompt, system_instruction="You are an expert AI architect.", schema={})
        selection_data = response["parsed_json"]
        
        model_selection = ModelSelection(
            model_name=selection_data["model_name"],
            context_window=selection_data["context_window"],
            temperature=selection_data["temperature"],
            reasoning=selection_data["reasoning"],
            estimated_cost_per_1k=selection_data["estimated_cost_per_1k_tokens"]
        )
        
        log_event("LLM_SELECTION_SUCCESS",
                 selected_model=model_selection.model_name,
                 reasoning=model_selection.reasoning)
        
        return model_selection
        
    except Exception as e:
        log_event("LLM_SELECTION_ERROR", error=str(e))