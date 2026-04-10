Install the Hypothesis MCP server for Claude Code.

Steps:
1. Ask the user for their Hypothesis API key (they can get one at https://hypothes.is/account/developer). Do not proceed without it.
2. Check if `uvx` is available by running `which uvx`. If not found, tell the user to install uv first: `curl -LsSf https://astral.sh/uv/install.sh | sh`, then re-check.
3. Run: `claude mcp add hypothesis -e HYPOTHESIS_API_KEY=<key> -- uvx hypothesis-mcp`
4. Verify the install by running: `claude mcp list` and confirming `hypothesis` appears.
5. Tell the user to restart Claude Code for the MCP server to load, then they can ask Claude things like "show me my recent Hypothesis annotations" or "find papers I've annotated about diffusion models".
