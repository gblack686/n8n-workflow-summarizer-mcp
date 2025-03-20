# N8N Workflow Summarizer MCP Tool

An MCP tool that analyzes and summarizes n8n workflows for Claude.

## Overview

This tool simplifies n8n workflow JSON files into clear, concise summaries. It extracts key information about nodes, connections, and functionality to help Claude understand complex workflows.

## Features

- Analyzes n8n workflow JSON files
- Extracts node counts and types 
- Identifies connections between nodes
- Produces markdown summaries
- Compatible with Model Context Protocol (MCP)

## Installation

Follow these steps to install the N8N Workflow Summarizer MCP tool:

```bash
# Clone the repository
git clone https://github.com/gblack686/n8n-workflow-summarizer-mcp.git
cd n8n-workflow-summarizer-mcp

# Set up your OpenAI API key
export OPENAI_API_KEY=your_api_key_here

# Install dependencies
pip install -r requirements.txt

# Install as MCP tool
fastmcp install workflow_summarizer_mcp.py --name "N8N Workflow Summarizer"
```

## Usage

Check the `example_usage.py` file for a complete example of how to use this tool.

```python
import asyncio
from workflow_summarizer_mcp import summarize_workflow

async def main():
    # Specify your workflow JSON file
    workflow_file = "example_workflow.json"
    
    # Summarize the workflow using a specific model
    summary = await summarize_workflow(workflow_file, model="gpt-4o")
    
    print(summary)

if __name__ == "__main__":
    asyncio.run(main())
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 