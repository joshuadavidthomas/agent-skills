---
name: tool-name
description: One-line description of what the tool does. Use when [trigger phrases].
---

# Tool Name

One-sentence description of what this tool does and why you'd use it.

## Requirements

What needs to exist before using this tool:
- Required accounts or API keys
- System dependencies
- Other tools that must be installed first

## Installation

### macOS (Homebrew)
```bash
brew install tool-name
```

### Linux
```bash
sudo apt install tool-name
# or
cargo install tool-name
```

### Verify
```bash
tool-name --version
```

## Quick Start

Get something useful done fast:
```bash
tool-name do-the-thing
```

## Usage

### View / List
```bash
tool-name list                    # List all items
tool-name show <id>               # Show details
```

### Create / Add
```bash
tool-name add "name" https://url
tool-name create --name "foo"
```

### Edit / Update
```bash
tool-name edit <id>
tool-name update <id> --field value
```

### Delete / Remove
```bash
tool-name remove <id>
```

### Search
```bash
tool-name search "query"
```

## Output Formats

```bash
tool-name list --output json
tool-name list --format "{{.Name}}"
```

## Tips & Gotchas

- Thing that's not obvious
- Platform-specific notes

## Troubleshooting

### Debug mode
```bash
tool-name --verbose command
```

### Common errors

**Error: "connection refused"**
- Check if the service is running

**Error: "authentication failed"**
- Verify API key

### Reset state
```bash
rm -rf ~/.local/share/tool-name/cache
```

## Configuration

### Config file
```
~/.config/tool-name/config.toml
```

### Minimal config
```toml
[section]
key = "value"
```

### Environment variables
```bash
export TOOL_API_KEY="your-key"
```

## Uninstall

```bash
brew uninstall tool-name
rm -rf ~/.config/tool-name
rm -rf ~/.local/share/tool-name
```

## References

- [Official docs](https://tool.dev/docs)
