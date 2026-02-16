# Agents

This directory contains reference agent definitions for the researching-codebases skill. These files are not usable directly from this location - they must be installed to your agentic CLI tool to be utilized.

## Format

The definitions are written in [OpenCode](https://opencode.ai) format. If using another tool, refer to your tool's documentation on configuring agents and adapt accordingly. Each agent file contains:

- **YAML frontmatter**: Tool-specific configuration (model, tools, permissions)
- **Markdown body**: System prompt defining the agent's behavior

The system prompt content should be portable across tools. The frontmatter will need adaptation to your tool's configuration format.

## Migration Prompt

If your tool supports custom agents, you can use this prompt to help migrate:

> Read the agent definitions in this directory and convert them to [YOUR TOOL] format. Preserve the system prompts exactly - only adapt the configuration (model selection, tool access, permissions) to match [YOUR TOOL]'s agent configuration format.
