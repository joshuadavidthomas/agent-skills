# Research Memory Scripts

Scripts for working with past research documents.

## Available Scripts

| Script | Purpose | Use When |
|--------|---------|----------|
| `list-research.py` | List past research docs with metadata | Starting research, checking what exists |
| `search-research.py` | Search past research by topic or tags | Looking for specific past findings |
| `read-research.py` | Read full content of a research doc | Loading a specific document by path |
| `gather-metadata.py` | Generate frontmatter metadata | Creating a new research document |
| `promote-research.py` | Copy local research to global | Making project research available everywhere |

## Usage

Run scripts by name with arguments as needed. Examples below show the script name and available arguments.

### List recent research

Run `list-research.py` to see recent research docs.

Arguments:
- `--limit N`: Max results (default: 10)
- `--location project|global|both`: Which directory (default: both)

### Search for topic

Run `search-research.py` with a search term to find related research.

Arguments:
- First positional: Search term (required)
- `--tags`: Filter by tags (comma-separated)
- `--limit N`: Max results (default: 5)

### Read full content

Run `read-research.py` with a path to load a research document. Use paths returned by `list-research.py` or `search-research.py`.

### Generate metadata

Run `gather-metadata.py` to get deterministic metadata for research documents.

Returns key-value pairs: `date`, `filename_date`, `cwd`, `repository`, `branch`, `commit`

### Promote to global

Run `promote-research.py` with a filename from `.research/` to copy it to `~/.research/`.

Arguments:
- First positional: Filename in `.research/` (required)
- `--move`: Move instead of copy (removes local)

**User might say:**
- "Make that research available globally"
- "I want to reference this from other projects"
- "Move this to global research"
- "Save this so I can use it elsewhere"

## Research Directories

| Location | Path | Use For |
|----------|------|---------|
| Project | `.research/` | Project-specific research |
| Global | `~/.research/` | Cross-project knowledge |
