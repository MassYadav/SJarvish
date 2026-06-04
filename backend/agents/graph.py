import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import the shared state schema
from agents.state import AgentState

# Import the cognitive routing supervisor
from agents.supervisor import supervisor_node

# Import the specialist worker nodes
from agents.nodes.workers import coder_node, researcher_node, memory_node

logger = logging.getLogger(__name__)

def build_ai_os_graph():
    """
    Compiles the core cognitive state machine for the AI Operating System.
    Connects the Supervisor router to the Specialist worker nodes.
    """
    logger.info("⚙️ Compiling LangGraph Multi-Agent State Machine...")

    # 1. Initialize the Graph with our unified AgentState schema
    builder = StateGraph(AgentState)

    # 2. Register all execution nodes to the graph
    builder.add_node("Supervisor", supervisor_node)
    builder.add_node("Coder", coder_node)
    builder.add_node("Researcher", researcher_node)
    builder.add_node("MemoryWorker", memory_node)

    # 3. Define the entry point (Every task starts at the Supervisor)
    builder.set_entry_point("Supervisor")

    # 4. Define the dynamic routing logic (Conditional Edges)
    def route_from_supervisor(state: AgentState):
        routing_destination = state.get("next_node", "FINISH")
        if routing_destination == "FINISH":
            return END
        return routing_destination

    # Attach the conditional routing map to the Supervisor
    builder.add_conditional_edges(
        "Supervisor",
        route_from_supervisor,
        {
            "Coder": "Coder",
            "Researcher": "Researcher",
            "MemoryWorker": "MemoryWorker",
            END: END
        }
    )

    # 5. Define the return paths (Workers always loop back or end)
    builder.add_edge("Coder", END)
    builder.add_edge("Researcher", END)
    builder.add_edge("MemoryWorker", END)

    # 6. Compile the graph with a built-in memory checkpointer
    # MemorySaver is the most robust way to manage state locally without async DB conflicts.
    memory_saver = MemorySaver()
    ai_os_app = builder.compile(checkpointer=memory_saver)

    logger.info("✅ Graph Compilation Complete. Brain is online.")
    return ai_os_app