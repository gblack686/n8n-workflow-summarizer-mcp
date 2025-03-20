from fastmcp import FastMCP, Context
import json
import os
from pathlib import Path
import logging
import datetime
from openai import OpenAI

# Initialize FastMCP
mcp = FastMCP(
    "N8N Workflow Summarizer",
    description="Analyzes and summarizes n8n workflows",
    dependencies=["openai>=1.0.0"]
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("workflow_summarizer_mcp")

@mcp.tool()
async def summarize_workflow(workflow_path: str, model: str = "gpt-4o", ctx: Context = None) -> str:
    """
    Summarize an n8n workflow JSON file
    
    Parameters:
    - workflow_path: Path to the n8n workflow JSON file
    - model: OpenAI model to use (default: gpt-4o)
    
    Returns:
    - A markdown summary of the workflow
    """
    if ctx:
        ctx.info(f"Starting to summarize workflow from: {workflow_path}")
    
    # Load workflow JSON
    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow_json = json.load(f)
    except UnicodeDecodeError:
        if ctx:
            ctx.warning("UTF-8 encoding failed, trying latin-1")
        with open(workflow_path, "r", encoding="latin-1") as f:
            workflow_json = json.load(f)
    
    if ctx:
        ctx.info(f"Successfully loaded workflow JSON from {workflow_path}")
    
    # Extract workflow information
    workflow_title = workflow_json.get("name", "Untitled Workflow")
    if ctx:
        ctx.info(f"Workflow title: {workflow_title}")
    
    # Count nodes and identify types
    nodes = workflow_json.get("nodes", [])
    node_count = len(nodes)
    if ctx:
        ctx.info(f"Number of nodes: {node_count}")
    
    # Identify node types
    node_types = {}
    for node in nodes:
        node_type = node.get("type", "unknown")
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    if ctx:
        ctx.info(f"Node types identified: {node_types}")
    
    # Identify AI/agent nodes and database nodes
    ai_nodes = sum(count for type_, count in node_types.items() 
                 if "openai" in type_.lower() or "ai" in type_.lower() 
                 or "gpt" in type_.lower() or "llm" in type_.lower() 
                 or "agent" in type_.lower() or "anthropic" in type_.lower()
                 or "langchain" in type_.lower())
    
    db_nodes = sum(count for type_, count in node_types.items() 
                 if "postgres" in type_.lower() or "mysql" in type_.lower() 
                 or "database" in type_.lower() or "sql" in type_.lower() 
                 or "mongo" in type_.lower() or "supabase" in type_.lower())
    
    if ctx:
        ctx.info(f"Agent nodes: {ai_nodes}, Database nodes: {db_nodes}")
    
    # Extract prompts used in agent nodes
    user_prompts = []
    system_prompts = []
    
    for node in nodes:
        if "agent" in node.get("type", "").lower() or "openai" in node.get("type", "").lower():
            parameters = node.get("parameters", {})
            system_prompt = parameters.get("systemPrompt", "")
            user_prompt = parameters.get("text", "")
            
            if system_prompt and len(system_prompt) > 10:
                system_prompts.append(system_prompt)
            if user_prompt and len(user_prompt) > 10:
                user_prompts.append(user_prompt)
    
    if ctx:
        ctx.info(f"Extracted {len(user_prompts)} user prompts and {len(system_prompts)} system prompts")
    
    # Get timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Initialize OpenAI client
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        error_message = "OPENAI_API_KEY environment variable not set"
        if ctx:
            ctx.error(error_message)
        return error_message
    
    client = OpenAI(api_key=openai_api_key)
    if ctx:
        ctx.info("Initializing OpenAI client")
    
    # Handle large workflows by simplifying
    workflow_str = json.dumps(workflow_json)
    workflow_size = len(workflow_str)
    if ctx:
        ctx.info(f"Workflow JSON size: {workflow_size} characters")
    
    # Estimate token count (rough approximation)
    estimated_tokens = workflow_size // 4
    if ctx:
        ctx.info(f"Estimated token count: {estimated_tokens}")
    
    # Simplify workflow if needed
    simplified_workflow = workflow_json.copy()
    if estimated_tokens > 12000:
        if ctx:
            ctx.info("Simplifying workflow for token reduction")
            await ctx.report_progress(0.1, f"Simplifying large workflow ({estimated_tokens} tokens)")
        
        # Keep only essential node information
        simplified_nodes = []
        for node in nodes:
            simplified_node = {
                "name": node.get("name", ""),
                "type": node.get("type", ""),
                "parameters": {},
                "position": node.get("position", [])
            }
            
            # Keep only essential parameters
            parameters = node.get("parameters", {})
            important_params = ["text", "systemPrompt", "operation", "table", "query"]
            for param in important_params:
                if param in parameters:
                    simplified_node["parameters"][param] = parameters[param]
            
            simplified_nodes.append(simplified_node)
        
        simplified_workflow["nodes"] = simplified_nodes
        
        # Remove unnecessary workflow properties
        keys_to_remove = ["pinData", "connections", "settings", "staticData"]
        for key in keys_to_remove:
            if key in simplified_workflow:
                del simplified_workflow[key]
        
        simplified_str = json.dumps(simplified_workflow)
        simplified_tokens = len(simplified_str) // 4
        if ctx:
            ctx.info(f"Simplified workflow size: {simplified_tokens} tokens")
            await ctx.report_progress(0.2, "Workflow simplified successfully")
        
        # Use simplified workflow
        workflow_json = simplified_workflow
    
    # Prepare prompt for OpenAI API
    prompt = f"""
    You are a workflow analysis expert. Analyze this n8n workflow JSON and provide a detailed summary.
    
    Here's the workflow information:
    Title: {workflow_title}
    Number of Nodes: {node_count}
    Node Types: {json.dumps(node_types, indent=2)}
    AI/Agent Nodes: {ai_nodes}
    Database Nodes: {db_nodes}
    
    User Prompts Found: {json.dumps(user_prompts, indent=2)}
    System Prompts Found: {json.dumps(system_prompts, indent=2)}
    
    Full Workflow JSON: {json.dumps(workflow_json, indent=2)}
    
    Please provide a summary with the following sections:
    1) STRUCTURED SUMMARY: Basic workflow metadata in bullet points
    2) CURRENT TIMESTAMP: When this analysis was performed ({timestamp})
    3) DETAILED STEP-BY-STEP EXPLANATION (MARKDOWN): How the workflow functions
    4) AGENT SYSTEM PROMPTS AND USER PROMPTS: Any prompts used in agent/AI nodes
    5) A PYTHON FUNCTION THAT REPLICATES THE WORKFLOW: Conceptual Python code that would perform similar operations
    
    Format the response in Markdown.
    """
    
    if ctx:
        ctx.info("Constructing prompt for OpenAI API")
        ctx.info(f"Prompt token estimate: {len(prompt) // 4}")
        await ctx.report_progress(0.3, "Preparing to call OpenAI API")
    
    # Call OpenAI API with model-specific parameters
    if ctx:
        ctx.info(f"Calling OpenAI API using model: {model}")
        await ctx.report_progress(0.4, f"Calling OpenAI with model: {model}")
    
    try:
        if model == "o1":
            # o1 model requires max_completion_tokens instead of max_tokens
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=4000,
            )
        else:
            # Standard parameters for other models
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.7
            )
        
        if ctx:
            ctx.info("Successfully received response from OpenAI API")
            await ctx.report_progress(0.8, "Received summary from OpenAI")
        
        summary = response.choices[0].message.content
        
        # Save to file and return the summary
        output_path = Path(workflow_path).stem + "_summary.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
        
        if ctx:
            ctx.info(f"Workflow summary saved successfully to {output_path}")
            await ctx.report_progress(1.0, f"Summary saved to {output_path}")
        
        return summary
        
    except Exception as e:
        error_message = f"Error calling OpenAI API: {str(e)}"
        if ctx:
            ctx.error(error_message)
            await ctx.report_progress(1.0, f"Error: {str(e)}", "error")
        
        # Try with fallback model if primary fails and it's not already the fallback
        if model != "gpt-3.5-turbo-16k":
            if ctx:
                ctx.info("Attempting with fallback model gpt-3.5-turbo-16k")
                await ctx.report_progress(0.5, "Trying fallback model")
            
            # Further simplify the workflow for the fallback model
            super_simplified = {
                "name": workflow_title,
                "node_count": node_count,
                "node_types": node_types,
                "nodes": simplified_workflow.get("nodes", [])[:min(20, len(simplified_workflow.get("nodes", [])))]
            }
            
            # Shorten the prompt for the fallback model
            fallback_prompt = f"""
            Analyze this simplified n8n workflow and provide a summary:
            
            Title: {workflow_title}
            Number of Nodes: {node_count}
            Node Types: {json.dumps(node_types, indent=2)}
            
            Simplified JSON: {json.dumps(super_simplified, indent=2)}
            
            Format as markdown with these sections:
            1. Basic summary and stats
            2. Current timestamp ({timestamp})
            3. Step-by-step explanation
            4. Found prompts
            5. Example Python function
            """
            
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo-16k",
                    messages=[{"role": "user", "content": fallback_prompt}],
                    max_tokens=4000,
                    temperature=0.7
                )
                
                if ctx:
                    ctx.info("Successfully received response from fallback model")
                    await ctx.report_progress(0.9, "Received summary from fallback model")
                
                summary = response.choices[0].message.content
                
                # Save to file and return the summary
                output_path = Path(workflow_path).stem + "_summary.md"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(summary)
                
                if ctx:
                    ctx.info(f"Workflow summary saved successfully to {output_path}")
                    await ctx.report_progress(1.0, f"Summary saved to {output_path} (fallback model)")
                
                return summary
            
            except Exception as fallback_error:
                if ctx:
                    ctx.error(f"Error with fallback model: {str(fallback_error)}")
                    await ctx.report_progress(1.0, f"All attempts failed: {str(fallback_error)}", "error")
                return f"Error with fallback model: {str(fallback_error)}"
        
        return error_message

from fastmcp.prompts.base import UserMessage, AssistantMessage

@mcp.prompt()
def summarize_workflow_prompt() -> list:
    """Prompt to guide users on using the workflow summarizer"""
    return [
        AssistantMessage("I can help you analyze and summarize n8n workflows. To get started, I need:"),
        AssistantMessage("1. The path to your n8n workflow JSON file\n2. (Optional) Which OpenAI model to use (default: gpt-4o)"),
        UserMessage("I'd like to summarize my workflow at path/to/workflow.json"),
        AssistantMessage("I'll analyze that workflow for you. Would you like to use the default model (gpt-4o) or specify a different one?")
    ]

@mcp.resource("docs://workflows")
def workflow_docs() -> str:
    """Documentation about N8N workflows and how they're structured"""
    return """
    # N8N Workflow Structure Documentation
    
    N8N workflows are defined in JSON format and consist of nodes connected together to form an automation flow.
    
    ## Key Components
    
    ### Nodes
    The basic building blocks of a workflow. Each node represents an action or operation.
    
    ### Connections
    Define the flow between nodes, determining the execution path.
    
    ### Parameters
    Configure how each node operates, providing inputs and settings.
    
    ## Common Node Types
    
    - HTTP Request: Make API calls to external services
    - Code: Execute custom JavaScript/TypeScript code
    - Function: Run a function on the input data
    - IF: Conditional branching based on conditions
    - Split: Divide workflow execution into parallel branches
    - Merge: Combine data from multiple branches
    - Filter: Filter items based on conditions
    - Set: Set values in the workflow data
    
    ## AI/Agent Nodes
    
    N8N supports various AI nodes for LLM integration:
    - OpenAI: Connect to OpenAI's models
    - Anthropic: Connect to Claude models
    - LangChain: Build complex AI applications
    
    ## Database Nodes
    
    Connect to various databases:
    - PostgreSQL
    - MySQL
    - MongoDB
    - Supabase
    """

if __name__ == "__main__":
    mcp.run() 