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
    # TODO: Add support for other models and update prompt
    """
    Use Gemini to select the optimal model configuration.
    This implements "model-of-models" where Gemini helps choose the best setup.
    """
    log_event("LLM_SELECTION_START", 
             complexity=structured_instruction.get("estimated_complexity"))
    
    # Create LLM client for selection
    llm = create_llm_client()
    
    prompt = f"""You are an AI model selection expert. Analyze this agent configuration
and recommend the optimal Google Gemini model.

Agent Type: {structured_instruction['agent_type']}
Complexity: {structured_instruction.get('estimated_complexity', 'medium')}
Capabilities Required: {', '.join(structured_instruction['capabilities'])}
Constraints: {', '.join(structured_instruction.get('constraints', []))}

Consider:
- Task complexity vs cost
- Context window requirements
- Specific capability needs (coding, reasoning, analysis)
- Budget constraints

IMPORTANT: You must choose from these Google Gemini models ONLY:
- gemini-2.0-flash-exp (fastest, cheapest, good for simple tasks)
- gemini-1.5-flash (balanced, 1M context window)
- gemini-1.5-pro (most capable, best for complex reasoning)
- gemini-pro (legacy, general purpose)

Recommend ONE Gemini model with reasoning in JSON:
{{
    "model_name": "gemini-1.5-flash",
    "context_window": 1000000,
    "temperature": 0.7,
    "reasoning": "why this specific Gemini model",
    "estimated_cost_per_1k_tokens": 0.00015
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