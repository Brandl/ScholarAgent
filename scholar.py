import getpass
import os
import logging

from dotenv import load_dotenv
from mako.template import Template
from typing import Annotated
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, ToolMessage

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.DEBUG)

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env("OPENAI_API_KEY")
_set_env("S2_API_KEY")

from SemanticScholarAPI import tool_list

# Initialize the ChatOpenAI model
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tool_list)

# Define our action graph
class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

def route_tools(state: State):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=tool_list))

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", route_tools)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge("chatbot", END)

# Instantiate the graph with memory
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# Start our agent and give it the initial prompt
template = Template("""
You are an AI assistant that helps with literature search and review.
You can search for papers and authors, retrieve detailed information about papers and authors, and get recommendations.
Use the provided tools to assist in your tasks.

Make a plan on how to research the topic 'machine learning in cyber security' and execute the plan.
Focus on recent papers published between 2023 and 2024. If you find a paper that is relevant also look at the references and citations.
Look at the papers that are mentioned in the references and citations, maybe they are also relevant.
After you have gathered enough information, provide a summary of the research and the most relevant papers.
""").render()


# Process the events and print outputs, ask for approval before running tools   

for event in  graph.stream(
    input={
        "messages": [
            ("user", template),
        ]
    },
    config={
        "configurable": {"thread_id": "1"}
    },
    stream_mode="values"
):
    if "messages" in event: 
        #if isinstance(event["messages"][-1], AIMessage):
        event["messages"][-1].pretty_print()
