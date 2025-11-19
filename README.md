# GitHub Organization Cloner

A production-quality Python CLI tool to clone all repositories from a GitHub organization with support for parallel execution and post-clone setup automation.

## Features

- **Organization Repository Discovery**: Automatically fetches all repositories from a GitHub organization using the GitHub REST API
- **Parallel Cloning**: Clone multiple repositories concurrently with configurable worker count
- **Smart Setup Detection**: Automatically detects project types (Node.js, Python, Ruby, Go, Rust) and provides setup suggestions
- **Dry Run Mode**: Preview what would be cloned without actually cloning
- **Robust Error Handling**: Gracefully handles network errors, rate limits, and git failures
- **Progress Tracking**: Real-time progress updates during cloning operations
- **Flexible Configuration**: Configure via `.env` file, environment variables, or CLI flags
- **Simple Entry Point**: Run directly with `python main.py` without installation

## Requirements

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (recommended package manager)
- Git installed and available in PATH
- GitHub personal access token (optional but recommended for higher API rate limits)

## Quick Start

```bash
# 1. Clone this repository
git clone https://github.com/Thavarshan/github-org-cloner.git
cd github-org-cloner

# 2. Set up environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# 3. Create your .env file from the example
cp .env.example .env
# Edit .env and set GITHUB_ORG_CLONE_BASE_DIR=~/code

# 4. Run it!
python main.py https://github.com/openai
```

That's it! The tool will clone all repositories from the specified organization.

## Installation

### Using uv (recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to the project directory
cd github-org-cloner

# Create virtual environment and sync dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# Optional: Install in development mode to get the CLI command
uv sync --all-extras
```

## Configuration

Configuration priority (highest to lowest):

1. **Command-line arguments**
2. **Environment variables**
3. **.env file** (recommended for easy setup)

### Using .env File (Easiest!)

Copy the example file and edit it:

```bash
cp .env.example .env
```

Then edit `.env`:

```bash
# Required: Where to clone repositories
GITHUB_ORG_CLONE_BASE_DIR=~/code

# Optional: GitHub token for higher rate limits (60/hr → 5000/hr)
GITHUB_TOKEN=ghp_your_token_here
```

### Alternative: Environment Variables

```bash
export GITHUB_ORG_CLONE_BASE_DIR=~/code
export GITHUB_TOKEN=ghp_your_token_here
```

### Alternative: CLI Flags

```bash
python main.py https://github.com/openai --base-dir ~/code --token ghp_your_token
```

### Getting a GitHub Token

For higher API rate limits (60 requests/hour → 5000 requests/hour):

1. Go to [GitHub Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Generate new token (classic)
3. Select `public_repo` scope (or `repo` for private repos)
4. Copy the token to your `.env` file

## Usage

### Basic Usage

If you've set up your `.env` file, it's super simple:

```bash
# Using the simple entry point
python main.py https://github.com/openai

# Or using the installed CLI command (after uv sync --all-extras)
github-org-cloner https://github.com/openai
```

This will clone all repositories to `~/code/openai/repo-name` (based on your `.env` configuration).

### Interactive Mode

If you don't provide the organization URL as an argument, you'll be prompted:

```bash
python main.py
# Enter GitHub organization URL (e.g., https://github.com/openai): https://github.com/openai
```

### Parallel Cloning

Clone repositories in parallel for faster execution:

```bash
# Use default number of workers (CPU count)
python main.py https://github.com/openai --parallel

# Specify maximum number of workers
python main.py https://github.com/openai --parallel --max-workers 8
```

### Dry Run

Preview what would be cloned without actually cloning:

```bash
python main.py https://github.com/openai --dry-run
```

### Setup Detection

After cloning, detect project types and optionally run setup scripts:

```bash
# Show setup suggestions (default behavior)
python main.py https://github.com/openai

# Automatically run setup.sh scripts if found
python main.py https://github.com/openai --run-setup
```

The tool will detect and provide suggestions for:

- **Node.js** projects (`package.json`)
- **Python** projects (`pyproject.toml`, `requirements.txt`, `setup.py`)
- **Ruby** projects (`Gemfile`)
- **Go** projects (`go.mod`)
- **Rust** projects (`Cargo.toml`)
- **Makefiles**
- **Custom setup scripts** (`setup.sh`)

### Verbose Logging

Enable debug logging for troubleshooting:

```bash
python main.py https://github.com/openai --verbose
```

### Complete Example

```bash
# With .env file configured, just run:
python main.py https://github.com/openai --parallel --max-workers 4 --run-setup
```

## Command-Line Reference

```
usage: github-org-cloner [-h] [--base-dir BASE_DIR] [--token TOKEN] [--parallel]
                         [--max-workers MAX_WORKERS] [--run-setup] [--dry-run]
                         [--verbose] [--version]
                         [org_url]

Clone all repositories from a GitHub organization.

positional arguments:
  org_url               GitHub organization URL (e.g., https://github.com/openai) or name

options:
  -h, --help            show this help message and exit
  --base-dir BASE_DIR   Base directory where repositories will be cloned
                        (overrides GITHUB_ORG_CLONE_BASE_DIR env var)
  --token TOKEN         GitHub personal access token (overrides GITHUB_TOKEN env var)
  --parallel            Clone repositories in parallel
  --max-workers MAX_WORKERS
                        Maximum number of parallel workers (default: number of CPUs)
  --run-setup           Run setup scripts after cloning repositories
  --dry-run             Show what would be done without actually cloning
  --verbose, -v         Enable verbose logging
  --version             show program's version number and exit

Environment Variables:
  GITHUB_ORG_CLONE_BASE_DIR  Base directory for cloning (can be overridden by --base-dir)
  GITHUB_TOKEN               GitHub personal access token for API authentication
```

## Development

### Running Tests

```bash
# Sync dev dependencies with uv
uv sync --all-extras

# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_github_client.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=github_org_cloner --cov-report=html
```

### Code Quality

The project uses several tools for code quality:

```bash
# Format code with black
black github_org_cloner tests

# Lint with ruff
ruff check github_org_cloner tests

# Type checking with mypy
mypy github_org_cloner
```

### Project Structure

```
github-org-cloner/
├── github_org_cloner/
│   ├── __init__.py          # Package metadata
│   ├── cli.py               # Command-line interface
│   ├── config.py            # Configuration management
│   ├── github_client.py     # GitHub API client
│   ├── cloner.py            # Repository cloning logic
│   └── setup_runner.py      # Post-clone setup detection
├── tests/
│   ├── __init__.py
│   ├── test_cli.py          # CLI tests
│   ├── test_github_client.py # GitHub client tests
│   └── test_cloner.py       # Cloner tests
├── pyproject.toml           # Project configuration and dependencies
└── README.md                # This file
```

## How It Works

1. **Parse Organization**: Extracts the organization name from the provided GitHub URL
2. **Fetch Repositories**: Uses the GitHub REST API to fetch all repositories (handles pagination automatically)
3. **Clone Repositories**: Clones each repository to `<base_dir>/<org_name>/<repo_name>`
   - Sequential mode: Clones one repository at a time
   - Parallel mode: Clones multiple repositories concurrently using ThreadPoolExecutor
4. **Setup Detection**: After cloning (if requested), scans each repository for project type indicators and setup scripts

## Error Handling

The tool handles various error scenarios gracefully:

- **Organization not found**: Clear error message with suggestions
- **Rate limit exceeded**: Displays rate limit reset time and suggests using a token
- **Git clone failures**: Logs errors but continues with remaining repositories
- **Network issues**: Retries are handled by the requests library
- **Existing repositories**: Skips repositories that already exist locally

## GitHub API Rate Limits

- **Without authentication**: 60 requests per hour
- **With authentication**: 5000 requests per hour

Each organization query uses at least 1 request, plus additional requests for pagination (1 request per 100 repositories).

## License

MIT License - feel free to use this tool for any purpose.

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `pytest`
2. Code is formatted: `black github_org_cloner tests`
3. Linting passes: `ruff check github_org_cloner tests`
4. Type checking passes: `mypy github_org_cloner`

## Troubleshooting

### "git command not found"

Ensure git is installed and available in your PATH:

```bash
git --version
```

### "Base directory must be provided"

Set the `GITHUB_ORG_CLONE_BASE_DIR` environment variable or use the `--base-dir` flag.

### "Rate limit exceeded"

Provide a GitHub personal access token via `GITHUB_TOKEN` environment variable or `--token` flag.

### Repositories already exist

The tool skips existing repositories by default. To re-clone, delete the repository directory first.
