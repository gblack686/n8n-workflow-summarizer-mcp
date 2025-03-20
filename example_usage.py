#!/usr/bin/env python3
"""
Example usage of the N8N Workflow Summarizer as a Python module
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("example_usage")

# Try to import from the package
try:
    from workflow_summarizer_mcp import summarize_workflow
except ImportError:
    logger.error("Could not import from workflow_summarizer_mcp. Make sure it's in your PYTHONPATH.")
    sys.exit(1)

async def main():
    """
    Example of using the workflow summarizer
    """
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is not set!")
        print("Please set your OpenAI API key as an environment variable:")
        print("export OPENAI_API_KEY='your-key-here'  # Linux/macOS")
        print("set OPENAI_API_KEY=your-key-here  # Windows CMD")
        print("$env:OPENAI_API_KEY='your-key-here'  # Windows PowerShell")
        sys.exit(1)

    # Path to an example workflow file
    workflow_path = Path("example_workflow.json")
    
    if not workflow_path.exists():
        logger.error(f"Workflow file not found: {workflow_path}")
        print(f"Please place an n8n workflow JSON file at {workflow_path}")
        sys.exit(1)
    
    print(f"Summarizing workflow: {workflow_path}")
    
    # Call the summarize_workflow function
    try:
        summary = await summarize_workflow(
            workflow_path=str(workflow_path),
            model="gpt-4o"  # You can change this to "o1" or other models
        )
        
        print("\nSummary generated successfully!")
        print(f"Output saved to: {workflow_path.stem}_summary.md")
        
        # Print first few lines of the summary
        print("\nSummary preview:")
        print("-" * 40)
        print("\n".join(summary.split("\n")[:10]))
        print("...")
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 