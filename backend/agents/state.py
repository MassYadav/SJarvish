from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    The core state machine memory matrix for the AI OS.
    Acts as a shared, append-only context clipboard between all worker agents.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    next_node: str
    context_summary: str