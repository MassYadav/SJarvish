import logging
from langchain_core.messages import AIMessage
from agents.state import AgentState
from llm.litellm_router.router import llm_router
from memory.service import memory_vault

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# WORKER 1: THE ELITE CODER
# ---------------------------------------------------------
async def coder_node(state: AgentState) -> dict:
    """Handles deep technical generation, software architecture, and algorithm writing."""
    logger.info("👨‍💻 Coder Worker activated. Processing technical request...")
    
    messages = [{"role": "system", "content": "You are a JARVIS-class Elite Software Engineer. Write clean, production-grade code. Do not over-explain basics. Deliver technical excellence."}]
    
    # Map the LangGraph state history into LiteLLM format
    for msg in state["messages"]:
        role = "user" if msg.type == "human" else "assistant"
        messages.append({"role": role, "content": msg.content})
        
    response = await llm_router.generate_reply(messages)
    reply_content = response.get("content", "Error: Coder module failed to execute.")
    
    return {"messages": [AIMessage(content=reply_content)]}

# ---------------------------------------------------------
# WORKER 2: THE DEEP RESEARCHER
# ---------------------------------------------------------
async def researcher_node(state: AgentState) -> dict:
    """Handles logical analysis, conceptual breakdowns, and vast factual synthesis."""
    logger.info("🔍 Researcher Worker activated. Synthesizing data...")
    
    messages = [{"role": "system", "content": "You are a JARVIS-class Research AI. Provide deep, highly accurate, and analytical insights. Structure your responses for extreme readability."}]
    
    for msg in state["messages"]:
        role = "user" if msg.type == "human" else "assistant"
        messages.append({"role": role, "content": msg.content})
        
    response = await llm_router.generate_reply(messages)
    reply_content = response.get("content", "Error: Research module failed to execute.")
    
    return {"messages": [AIMessage(content=reply_content)]}

# ---------------------------------------------------------
# WORKER 3: THE MEMORY SUBSYSTEM
# ---------------------------------------------------------
async def memory_node(state: AgentState) -> dict:
    """Connects to ChromaDB to retrieve stored context and semantic episodic memories."""
    logger.info("🗄️ Memory Worker activated. Searching persistent vector cortex...")
    
    # Grab the very last question the user asked
    last_user_query = state["messages"][-1].content
    
    # 1. Search the Vector Cortex (Built in Phase 7)
    memories = await memory_vault.recall_semantic_memories(inquiry=last_user_query)
    
    # 2. Format the mathematical context block
    context_block = "No historical data found in the cortex."
    if memories:
        context_block = "Cortex Memories Retrieved:\n"
        for m in memories:
            context_block += f"- {m['facts']} (Relevance Score: {m['distance_score']})\n"
            
    # 3. Instruct LiteLLM to synthesize an answer based ONLY on the retrieved facts
    sys_prompt = f"You are the OS Memory subsystem. Answer the user's query utilizing ONLY this retrieved systemic context:\n\n{context_block}"
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": last_user_query}
    ]
    
    response = await llm_router.generate_reply(messages)
    reply_content = response.get("content", "Error: Memory retrieval failed.")
    
    return {"messages": [AIMessage(content=reply_content)]}