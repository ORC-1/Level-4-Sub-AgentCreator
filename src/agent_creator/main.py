import sys
from core.genesis import genesis

def create_agent(instruction: str):
    """
    Genesis Agent: Entry point for dynamic agent creation.
    
    This function serves as an AI tool that accepts natural language
    instructions and orchestrates the creation of specialized agents.
    
    Args:
        instruction: Natural language description of the required agent capability
        
    Returns:
        Dict containing agent_id, status, and metadata
        
    Raises:
        ValidationError: If input validation fails
    """

    try:
        result = genesis(instruction)
        print(result)
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    """CLI entry point."""
    if len(sys.argv) > 1:
        create_agent(sys.argv[1])
    else:
        print("Usage: python -m agent_creator.main <instruction>")

if __name__ == "__main__":
    main()
