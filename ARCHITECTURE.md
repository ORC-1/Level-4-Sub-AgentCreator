# Agent Creator System - Architecture Overview

## Core Architecture: The Genesis Program

At the heart of the system is the **Genesis Program** (`genesis.py`), a classical orchestration layer that controls the flow of agent creation. Genesis acts as the conductor, performing input validation and routing requests through **five distinct stages**, each powered by specialized LLM-driven processes.

### Input Validation Layer

Before entering the pipeline, Genesis performs simple validation:
- **Null/Empty Check**: Ensures instruction is provided
- **Minimum Length**: Requires at least 10 characters for meaningful context
- **Maximum Length**: Caps at 5,000 characters to prevent token overflow
- **Logging**: All validation events are tracked for observability

---

## Five-Stage Pipeline Architecture

### **Stage 1: MDP-Based Natural Language Enrichment**

**Powered by**: Currently by Google Gemini (via ADK), can be configured with any other LLM vendor 
**Module**: `mdp_converter.py`  
**Paradigm**: Markov Decision Process (MDP)

This stage treats the agent creation task as a **Markov Decision Process**:
- **State**: Current system state + user's natural language instruction
- **Action**: Generated structured configuration
- **Reward**: Alignment score with user intent

**Process Flow**:
1. System provides natural language instruction (e.g., "Create a data analyst agent that can process CSV files")
2. LLM analyzes the instruction using MDP formulation
3. Extracts structured JSON output with:
   - `agent_type`: Primary role (e.g., "data_analyst", "code_generator", "researcher")
   - `capabilities`: List of specific, actionable skills
   - `constraints`: Limitations or requirements (e.g., "must_use_python", "realtime_processing")
   - `success_criteria`: Clear success metrics
   - `estimated_complexity`: "low", "medium", or "high"

**Google Tech Integration**:
- Uses `google-genai` SDK client (`genai.Client`)
- Leverages Gemini's structured output capabilities
- Tracks token usage and API costs for transparency

**Output Example**:
```json
{
  "agent_type": "data_analyst",
  "capabilities": ["csv_processing", "statistical_analysis", "visualization"],
  "constraints": ["must_use_python", "pandas_required"],
  "success_criteria": "Generate accurate statistical summaries with visualizations",
  "estimated_complexity": "medium",
  "_metadata": {
    "tokens_used": 1250,
    "api_cost": 0.00125,
    "model": "gemini-2.0-flash"
  }
}
```

---

### **Stage 2: Agent Configuration Blueprint**

**Module**: `agent_setup.py`  
**Function**: `get_agent_setup_data()`  
**Purpose**: Transform structured instruction into agent configuration

This stage takes the MDP-enriched output and creates a comprehensive agent blueprint:
- Generates unique `agent_id` (UUID)
- Constructs initial `system_prompt` based on capabilities and constraints
- Packages metadata for downstream stages

**Key Configuration Elements**:
- Agent identity and type
- Capability matrix
- Operational constraints
- Success criteria
- Metadata from Stage 1 (tokens, cost, model used)

---

### **Stage 3: Intelligent LLM Selection**

**Powered by**: Google Gemini (Model-of-Models approach) and can be configured with any other LLM
**Module**: `llm_selector.py`  
**Innovation**: Meta-learning for optimal model selection

This stage implements a **"model-of-models"** paradigm where an LLM(Gemini) recommends the optimal LLM configuration for the agent being created.

**Selection Criteria**:
- **Task Complexity**: Matches model capability to estimated complexity
- **Context Window**: Ensures sufficient context for agent's tasks
- **Cost Optimization**: Balances performance with budget constraints
- **Capability Alignment**: Matches model strengths (coding, reasoning, analysis) to agent needs

**LLM Integration**:
- LLM (Gemini) analyzes agent requirements
- Returns structured recommendation with:
  - `model_name`: Selected model (e.g., "gemini-1.5-flash", "gpt-4.1-mini")
  - `context_window`: Token capacity (e.g., 1,000,000 for Gemini 1.5)
  - `temperature`: Creativity vs. determinism setting (0.0-1.0)
  - `reasoning`: Explanation for model choice
  - `estimated_cost_per_1k_tokens`: Cost projection

**Output Example**:
```json
{
  "model_name": "gemini-1.5-flash",
  "context_window": 1000000,
  "temperature": 0.7,
  "reasoning": "Balanced performance for data analysis tasks with moderate complexity",
  "estimated_cost_per_1k": 0.00105
}
```

**Note**: This stage returns a `ModelSelection` dataclass with JSON recommendation.

---

### **Stage 4: SPICE Quality Assurance**

**Powered by**: Google Gemini (Adversarial Self-Play)  
**Module**: `qa_vet.py`  
**Framework**: SPICE (Self-Play In Corpus Environments) 

This is the **most sophisticated stage**, implementing a testing simulation inspired by academic research in AI evaluation.

#### SPICE Methodology

**Two-Role System**:

1. **Challenger Role** (Question Generator):
   - Gemini generates grounded test questions
   - Questions sourced from real-world datasets (Google interviews, LeetCode, StackOverflow)
   - Varied difficulty levels (easy: 0.2-0.4, medium: 0.5-0.6, hard: 0.7-0.9)
   - Targets **50% pass rate** for optimal learning frontier

2. **Reasoner Role** (Agent Under Test):
   - Newly created agent attempts to answer questions
   - Uses its configured LLM model and system prompt
   - Responses evaluated for correctness, similarity, and completeness

#### Quality Metrics

**Variance-Based Evaluation** (Bernoulli Variance):
- Formula: `variance = p(1-p)` where `p` is success rate
- **Optimal variance ≈ 0.25** (corresponds to 50% pass rate)
- Indicates questions are at the **frontier of capability**
- Too low variance (0.0 or near 1.0) means questions are too easy/hard

**Acceptance Criteria**:
- Average score ≥ 0.6 (demonstrates competence)
- Variance in range [0.15, 0.35] (optimal difficulty distribution)


#### Retry Mechanism

**Failure Handling**:
- Up to **3 automatic retry attempts** with enhanced configuration
- Failures can result from:
  - Wrong answers (competence gap)
  - Low variance (questions too similar or poorly calibrated)
  - High variance (inconsistent performance)
- After 3 failures: **Human-in-the-loop** intervention requested

**Module**: `retry.py` (referenced in `genesis.py`)

---

### **Stage 5: Agent Code Generation & A2A Registration**

**Module**: `agent_generator.py`  
**Function**: `create_agent_a2a()`  
**Output**: Production-ready Python agent file + A2A registration

This is the **final stage** where the actual agent implementation is generated. Upon successful QA validation from Stage 4, this stage generates a **complete, executable Python file** that implements the agent with full A2A compliance.

**Generated Components**:

1. **Agent Class**:
   - Initializes Google Gemini client using ADK (or configured LLM provider)
   - Implements `process()` method for message handling
   - Supports context-aware multi-agent communication
   - Exposes `get_capabilities()` for A2A discovery

2. **A2A Protocol Interface**:
   - `send_message()`: Agent-to-agent communication
   - `receive_message()`: Handle incoming messages with sender context
   - `broadcast()`: Network-wide message distribution

3. **Factory Function**:
   - `create_agent()`: Easy instantiation with API key management

4. **Standalone Execution**:
   - `if __name__ == "__main__"`: Built-in testing and demonstration

**File Structure**:
```
agents/generated/
└── data_analyst/
    └── data_analyst_a1b2c3d4.py
```



## Google Technology Stack

### **Google Gemini Models**

The system is **model-agnostic by design** but optimized for Google's Gemini family:

- **gemini-2.0-flash**: Default for fast, cost-effective operations
- **gemini-1.5-flash**: Balanced performance and cost
- **gemini-1.5-pro**: High-capability tasks requiring deep reasoning
- **Context Windows**: Up to 1,000,000 tokens for long-context tasks

### **Google AI Developer Kit (ADK)**

**Integration Points**:

1. **SDK**: `google-genai` Python package
2. **Client**: `genai.Client(api_key=...)` for all LLM interactions
3. **API**: `client.models.generate_content()` for text generation
4. **Structured Output**: JSON parsing with schema validation
5. **Token Tracking**: Usage metadata for cost optimization

**Configuration** (`config.py`):
```python
LLM_PROVIDER = "google"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
```

**Factory Pattern** (`llm/factory.py`):
```python
class GoogleLLMClient(LLMClient):
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.client = genai.Client(api_key=api_key)
```

---

## Key Architectural Patterns

### 1. **Separation of Concerns**
- Genesis orchestrates, doesn't implement
- Each stage is modular and independently testable
- Clear interfaces between stages

### 2. **Provider Abstraction**
- `LLMClient` abstract base class
- Easy to extend to other providers (OpenAI, Anthropic, etc.)
- Google implementation as reference

### 3. **Observability First**
- Comprehensive logging at every stage (`utils/logger.py`)
- Token usage and cost tracking
- QA scores and performance metrics

### 4. **Fail-Safe Design**
- Input validation prevents garbage in
- Fallback models for selection failures
- Retry mechanisms with human escalation
- Graceful error handling throughout

### 5. **A2A Compliance**
- Generated agents follow standard protocol
- Discoverable capabilities
- Context-aware messaging
- Network-ready architecture
---

## Configuration Settings

**From Agent Config** (populated through stages):
- `agent_id`: Unique identifier
- `agent_type`: Role classification
- `capabilities`: Skill matrix
- `constraints`: Operational limits
- `system_prompt`: LLM instruction template
- `selected_model`: Gemini model name
- `model_temperature`: Creativity setting (0.0-1.0)
- `model_context_window`: Token capacity
- `metadata`: Token usage, costs, model info

---

## Error Handling & Resilience

### Validation Errors
- **ValidationError**: Custom exception for input failures
- Early rejection prevents wasted API calls

### QA Failures
- Structured feedback with actionable insights
- Automatic retry with configuration enhancement
- Human escalation after 3 attempts

---

## Future Enhancements

### Planned Improvements
1. **Local Model**: Directly download model from Hugging face, finetune, test and use it locally


### Research Directions
- **SPICE Optimization**: Dynamic difficulty adjustment
- **Meta-learning**: Learn from agent creation patterns
- **Transfer Learning**: Reuse successful agent configurations
- **Adversarial Robustness**: Red-team testing integration

---

## Conclusion

The Agent Creator System represents a **proof of concept** for autonomous agent generation, deeply integrated with **Google's Gemini ecosystem** through the **AI Developer Kit (ADK)**. By combining classical software engineering (Genesis orchestration) with cutting-edge AI capabilities (Gemini-powered stages), the system delivers:

✅ **Intelligent**: MDP-based understanding of user intent  
✅ **Adaptive**: Model-of-models selection for optimal configuration  
✅ **Robust**: SPICE-based quality assurance with academic rigor  
✅ **Production-Ready**: A2A-compliant agents with full observability  
✅ **Cost-Effective**: Token tracking and optimization throughout  

This architecture serves as a **blueprint for next-generation AI systems** that can autonomously create, validate, and deploy specialized agents at scale.
