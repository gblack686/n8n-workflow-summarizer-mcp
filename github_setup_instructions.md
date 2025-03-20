# GitHub Repository Setup Instructions

Follow these steps to create a GitHub repository and push your local code:

## Step 1: Create a New Repository on GitHub

1. Go to [GitHub](https://github.com/) and sign in to your account
2. Click the "+" icon in the top right corner and select "New repository"
3. Enter repository name: `n8n-workflow-summarizer-mcp`
4. Add a description: "An MCP tool that analyzes and summarizes n8n workflows for Claude"
5. Choose "Public" visibility (or Private if you prefer)
6. **Important**: Do NOT initialize the repository with a README, .gitignore, or license since we already have these files locally
7. Click "Create repository"

## Step 2: Connect Your Local Repository to GitHub

After creating the repository, GitHub will show you a page with instructions. Use the "push an existing repository" option.

Open a terminal in your local repository folder (`github-repo`) and run:

```bash
# Add the GitHub repository as a remote named "origin"
git remote add origin https://github.com/YOUR_USERNAME/n8n-workflow-summarizer-mcp.git

# Push your code to GitHub
git push -u origin master
```

Replace `YOUR_USERNAME` with your actual GitHub username.

## Step 3: Verify the Repository

1. Go to `https://github.com/YOUR_USERNAME/n8n-workflow-summarizer-mcp`
2. You should see all your files uploaded to GitHub

## Step 4: Install the MCP Tool (For Users)

Once the repository is set up, users can install the tool with:

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/n8n-workflow-summarizer-mcp.git
cd n8n-workflow-summarizer-mcp

# Install the MCP tool
fastmcp install workflow_summarizer_mcp.py --name "N8N Workflow Summarizer" -e OPENAI_API_KEY=your_api_key_here
``` 