"""LangGraph agent for literature search and review."""

from __future__ import annotations

from typing import Annotated

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from scholaragent.client import SemanticScholarClient
from scholaragent.tools import create_tools

SYSTEM_PROMPT = (
    "You are an AI assistant that helps with literature search and review. "
    "You can search for papers and authors, retrieve detailed information "
    "about papers and authors, and get recommendations. "
    "Use the provided tools to assist in your tasks."
)


class State(TypedDict):
    messages: Annotated[list, add_messages]


def build_agent(
    client: SemanticScholarClient,
    *,
    model: str = "gpt-4o",
    temperature: float = 0,
):
    """Build and return a compiled LangGraph agent."""
    tools = create_tools(client)
    llm = ChatOpenAI(model=model, temperature=temperature).bind_tools(tools)

    def chatbot(state: State):
        return {"messages": [llm.invoke(state["messages"])]}

    def route_tools(state: State):
        if isinstance(state, list):
            ai_message = state[-1]
        elif messages := state.get("messages", []):
            ai_message = messages[-1]
        else:
            raise ValueError(f"No messages found in state: {state}")
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"
        return END

    graph = StateGraph(State)
    graph.add_node("chatbot", chatbot)
    graph.add_node("tools", ToolNode(tools=tools))
    graph.add_edge(START, "chatbot")
    graph.add_conditional_edges("chatbot", route_tools)
    graph.add_edge("tools", "chatbot")

    return graph.compile(checkpointer=MemorySaver())


def run_agent(graph, prompt: str, *, thread_id: str = "1"):
    """Stream the agent on a user prompt and print messages."""
    for event in graph.stream(
        input={"messages": [("user", prompt)]},
        config={"configurable": {"thread_id": thread_id}},
        stream_mode="values",
    ):
        if "messages" in event:
            event["messages"][-1].pretty_print()
