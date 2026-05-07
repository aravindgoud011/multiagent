import operator
import os
import datetime
from typing import Annotated, Sequence, TypedDict, List, Union

from google import genai
import os
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Import our tools
from agents.admin_tools import (
    query_inventory, update_stock, 
    get_sales_report, get_customer_requests, get_payments
)

# Define LangChain Tools (for use in graph)
@tool
def tool_query_inventory(query: str):
    """Search for products and stock info."""
    return query_inventory(query)

@tool
def tool_update_stock(product_name: str, stock_change: int):
    """Update stock for an existing product."""
    return update_stock(product_name, stock_change)

@tool
def tool_get_sales_report(days: int = 7):
    """Get sales revenue and report."""
    return get_sales_report(days)

@tool
def tool_get_product_sales(product_name: str):
    """Get sales data for a specific product by joining bill_item and product tables."""
    from agents.admin_tools import get_product_sales
    return get_product_sales(product_name)

@tool
def tool_get_customer_requests():
    """Check what customers are asking for."""
    return get_customer_requests()

@tool
def tool_get_top_selling_products(limit: int = 5):
    """Get the top selling products by total quantity sold."""
    from agents.admin_tools import get_top_selling_products
    return get_top_selling_products(limit)

@tool
def tool_get_payments(limit: int = 10):
    """View recent payments."""
    return get_payments(limit)

# Define State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# Define Azure OpenAI LLM
def get_admin_llm():
    return AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=0
    )

# Use this for supervisor and specialists
llm = get_admin_llm()

def get_content(msg: BaseMessage) -> str:
    """Helper to safely extract string content from message."""
    if isinstance(msg.content, str):
        return msg.content
    if isinstance(msg.content, list):
        return "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in msg.content])
    return str(msg.content)

# Define Agent Nodes
def supervisor_node(state):
    print(f"Supervisor active. Last message: {get_content(state['messages'][-1])[:50]}...")
    history = ""
    for msg in state['messages'][-5:]: # Look at last 5 messages for context
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        if isinstance(msg, ToolMessage): role = "Tool"
        history += f"{role}: {get_content(msg)[:300]}\n"

    prompt = f"""You are a supervisor for a retail admin system. 
    Analyze the conversation history and decide the next step.
    
    SPECIALISTS:
    - InventorySpecialist: Products, stock, inventory details.
    - SalesSpecialist: Revenue, sales reports, payments, top-selling items.
    - SupportSpecialist: Customer requests, notifications.
    
    HISTORY:
    {history}
    
    RULES:
    1. If the specialist has already provided the data in the history, summarize it and say 'FINISH: [Your Answer]'.
    2. ALWAYS include specific data points (e.g., "₹500", "10 units") in your final answer.
    3. Use the Rupee symbol (₹) for money.
    4. If you need more data, name the specialist.
    5. Respond with ONLY 'FINISH: [Answer]' or the name of the specialist.
    """
    
    response = llm.invoke(prompt)
    content = response.content.strip()
    print(f"Supervisor decided: {content}")
    
    if "Inventory" in content:
        return {"next": "InventorySpecialist"}
    elif "Sales" in content:
        return {"next": "SalesSpecialist"}
    elif "Support" in content:
        return {"next": "SupportSpecialist"}
    else:
        if "FINISH:" in content:
            # Extract answer if provided
            answer = content.split("FINISH:")[1].strip()
            return {"messages": [AIMessage(content=answer)], "next": "FINISH"}
        return {"next": "FINISH"}

def convert_to_genai_msgs(messages):
    """Convert LangChain messages to Google GenAI format."""
    genai_msgs = []
    for m in messages:
        if isinstance(m, HumanMessage):
            genai_msgs.append({'role': 'user', 'content': get_content(m)})
        elif isinstance(m, AIMessage):
            genai_msgs.append({'role': 'model', 'content': get_content(m)})
        # Tool messages are more complex, but for simple chat it might be enough
    return genai_msgs

def inventory_specialist(state):
    print("InventorySpecialist active...")
    try:
        # Removed tool_add_product as requested
        agent_llm = llm.bind_tools([tool_query_inventory, tool_update_stock])
        response = agent_llm.invoke(state['messages'])
        return {"messages": [response], "next": "supervisor"}
    except Exception as e:
        return {"messages": [AIMessage(content=f"Error in InventorySpecialist: {e}")], "next": "supervisor"}

def sales_specialist(state):
    print("SalesSpecialist active...")
    try:
        # Added tool_get_top_selling_products for smarter analysis
        agent_llm = llm.bind_tools([
            tool_get_sales_report, 
            tool_get_payments, 
            tool_get_product_sales,
            tool_get_top_selling_products
        ])
        response = agent_llm.invoke(state['messages'])
        return {"messages": [response], "next": "supervisor"}
    except Exception as e:
        return {"messages": [AIMessage(content=f"Error in SalesSpecialist: {e}")], "next": "supervisor"}

def support_specialist(state):
    print("SupportSpecialist active...")
    try:
        agent_llm = llm.bind_tools([tool_get_customer_requests])
        response = agent_llm.invoke(state['messages'])
        return {"messages": [response], "next": "supervisor"}
    except Exception as e:
        return {"messages": [AIMessage(content=f"Error in SupportSpecialist: {e}")], "next": "supervisor"}

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("InventorySpecialist", inventory_specialist)
builder.add_node("SalesSpecialist", sales_specialist)
builder.add_node("SupportSpecialist", support_specialist)

# Tools execution node
tools = [
    tool_query_inventory, tool_update_stock,
    tool_get_sales_report, tool_get_payments, tool_get_customer_requests,
    tool_get_product_sales, tool_get_top_selling_products
]
tool_node = ToolNode(tools)
builder.add_node("tools", tool_node)

# Define Edges
builder.set_entry_point("supervisor")

# Routing from specialists to tools if needed, or back to supervisor
def route_specialist(state):
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "tools"
    return "supervisor"

builder.add_conditional_edges("InventorySpecialist", route_specialist, {"tools": "tools", "supervisor": "supervisor"})
builder.add_conditional_edges("SalesSpecialist", route_specialist, {"tools": "tools", "supervisor": "supervisor"})
builder.add_conditional_edges("SupportSpecialist", route_specialist, {"tools": "tools", "supervisor": "supervisor"})

builder.add_edge("tools", "supervisor")

builder.add_conditional_edges(
    "supervisor",
    lambda x: x["next"],
    {
        "InventorySpecialist": "InventorySpecialist",
        "SalesSpecialist": "SalesSpecialist",
        "SupportSpecialist": "SupportSpecialist",
        "FINISH": END
    }
)

admin_graph = builder.compile()

def process_admin_query(query: str):
    # Short-circuit for simple greetings to save API quota
    greetings = ["hi", "hello", "hey", "hii", "hello there"]
    if query.lower().strip() in greetings:
        return "Hello Administrator! How can I help you manage the shop today?"
        
    inputs = {"messages": [HumanMessage(content=query)]}
    try:
        # Added recursion limit to prevent infinite loops
        result = admin_graph.invoke(inputs, config={"recursion_limit": 25})
        return get_content(result['messages'][-1])
    except Exception as e:
        print(f"Graph Execution Error: {e}")
        return f"I encountered an error while processing your request. This is likely due to API quota limits. Error details: {str(e)[:100]}..."
