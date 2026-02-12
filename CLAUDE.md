# Claude Custom Instructions Template

## Instructions for Claude

Before proceeding with any task, please check for relevant custom instructions in:

```
~/Documents/Admin/apps/claude/custom-instructions/
```

## How to Use Custom Instructions

1. **Check for relevant instructions**: Look for markdown files in the custom-instructions directory that relate to the current task
2. **Read and follow**: If a relevant instruction file exists, read it carefully and follow the guidelines provided
3. **Apply context-aware**: Use the custom instructions when they're relevant to the task at hand
4. **Ask if unclear**: If custom instructions conflict with the request or are unclear, ask for clarification

## Available Custom Instructions

Check the custom-instructions directory for files like:
- `shell-command-aliases.md` - **CRITICAL:** Always use -f flag with rm, cp, mv commands
- `stealth-fetch.md` - Web fetching tool for Cloudflare-protected sites
- `python-uv-usage.md` - Always use UV for Python package management and script execution
- `mermaid_code_formatting_guide.md` - Mermaid diagram formatting guidelines
- Add more custom instruction files as needed

## Example Usage

When you need to fetch a web page and encounter bot protection:
1. Check `stealth-fetch.md` for the stealth-fetch tool instructions
2. Follow the usage patterns documented in that file
3. Use the tool as specified in the custom instructions

## Adding New Custom Instructions

To add new custom instructions:
1. Create a new `.md` file in `~/Documents/Admin/apps/claude/custom-instructions/`
2. Document the tool, workflow, or guideline clearly
3. Include usage examples and common scenarios
4. Update this template if needed to reference the new instruction file
