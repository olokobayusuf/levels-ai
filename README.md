# Levels AI
AI models using AI models to build AI pipelines. Powered by MCP.

## Setup Instructions
We use [uv](https://docs.astral.sh/uv/getting-started/installation/) to manage packages.
First, clone this repository. Next, install Python dependencies:
```sh
# Install dependencies
$ uv pip install -r requirements.txt
```

Next, add the MCP server to Cursor:
```json5
{
  // Add the `levels-ai` server to Cursor's `mcp.json`
  "mcpServers": {
    "levels-ai": {
      "command": "/Users/yusuf/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/yusuf/Documents/Projects/olokobayusuf/levels-ai",
        "run",
        "--env-file",
        "/Users/yusuf/Documents/Projects/olokobayusuf/levels-ai/.env",
        "server.py"
      ]
    }
  }
}
```

## Learnings
In no particular order:

1. Claude Desktop sucks compared to Cursor for MCP development. Claude Desktop does not have any 
facilities working with input or output images. You can't get the path to an input image (Cursor supports this); and you also can't get some representation of the image that is useful for a tool call. Accepting `base64` would cause Claude to hallucinate a Base64 string which is always invalid.

2. GPT5 doesn't seem to ever inspect the input schema of the MCP tool. It creates tool calls with no 
apparent understanding of what the model expects as an input. Claude Sonnet 4 on the other hand does an 
excellent job consistently.

3. For some reason, adding local MCP servers to Claude Desktop causes the app's startup time to balloon 
(over a minute). And making any modifications to the MCP server requires closing and reopening Claude Desktop.
**This sucks** for iteration time. In Cursor, it's a simple toggle.

## Developer Notes
A few things relevant to devs who want to remix this project:

### Inspecting the MCP Server
You can use the `@modelcontextprotocol/inspector` tool to start a local UI to play with the MCP server:
```sh
# Start the MCP inspector app
$ npx @modelcontextprotocol/inspector
```