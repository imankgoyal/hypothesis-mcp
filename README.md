# hypothesis-mcp

MCP server for the [Hypothesis](https://hypothes.is) annotation service. Gives Claude access to your annotations and the ability to read PDFs — including finding which PDF in your library discusses a given topic.

> **Note:** All code written by [Claude](https://claude.ai) (Anthropic) under the supervision of [Ankit Goyal](https://github.com/imankgoyal).

## Quick Install (Claude Code)

```bash
# 1. Get your API key: https://hypothes.is/account/developer
# 2. Run this in Claude Code:
claude mcp add hypothesis -e HYPOTHESIS_API_KEY=your-key-here -- uvx --from git+https://github.com/imankgoyal/hypothesis-mcp hypothesis-mcp
```

That's it — no cloning, no venv, no config files. Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

## Tools

| Tool | Description |
|---|---|
| `search_annotations` | Search annotations by URL, user, group, tag, text |
| `get_annotation` | Fetch a single annotation by ID |
| `create_annotation` | Create an annotation with optional quote/selectors |
| `update_annotation` | Update annotation text or tags |
| `delete_annotation` | Delete an annotation |
| `flag_annotation` | Flag an annotation for moderation |
| `hide_annotation` / `unhide_annotation` | Hide or unhide an annotation |
| `list_groups` / `get_group` | List or fetch groups |
| `get_user_profile` | Fetch the authenticated user's profile |
| `read_pdf` | Extract text from a PDF URL (direct or Chrome extension viewer format) |
| `discover_pdfs` | Scan all your annotated PDFs and find which ones discuss a topic |

## Installation

### Option A — `uvx` from GitHub (recommended, no cloning required)

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) to be installed.

```bash
claude mcp add hypothesis -e HYPOTHESIS_API_KEY=your-key-here -- uvx --from git+https://github.com/imankgoyal/hypothesis-mcp hypothesis-mcp
```

### Option B — local install

```bash
git clone https://github.com/imankgoyal/hypothesis-mcp
cd hypothesis-mcp
python3 -m venv .venv
.venv/bin/pip install -e .
claude mcp add hypothesis \
  -e HYPOTHESIS_API_KEY=your-key-here \
  -- /path/to/hypothesis-mcp/.venv/bin/hypothesis-mcp
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hypothesis": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/imankgoyal/hypothesis-mcp", "hypothesis-mcp"],
      "env": {
        "HYPOTHESIS_API_KEY": "your-key-here"
      }
    }
  }
}
```

## PDF URL formats

`read_pdf` accepts both formats:

```
https://arxiv.org/pdf/2507.05331
chrome-extension://bjfhmglciegochdpefhhlphglcehbmek/pdfjs/web/viewer.html?file=https%3A%2F%2Farxiv.org%2Fpdf%2F2507.05331
```

Paste either directly — the chrome-extension URL is automatically unwrapped.

## Self-hosted Hypothesis

Point the server at your own instance by setting `HYPOTHESIS_BASE_URL`:

```bash
claude mcp add hypothesis \
  -e HYPOTHESIS_API_KEY=your-key-here \
  -e HYPOTHESIS_BASE_URL=https://your-hypothesis-instance.com/api \
  -- uvx hypothesis-mcp
```

## License

Apache 2.0 — see [LICENSE](LICENSE). Any modifications must credit Ankit Goyal as the original author and state what was changed (per Apache 2.0 Section 4(b)).
