# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**github-org-cloner** is a production-quality CLI tool that clones all repositories from a GitHub organization. It uses the GitHub REST API to fetch repository metadata, then clones them locally with support for parallel execution and post-clone setup detection.

## Development Setup

```bash
# Using uv (the only supported package manager - no pip!)
uv venv
source .venv/bin/activate
uv sync --all-extras

# Set up your .env file for testing
cp .env.example .env
# Edit .env and add GITHUB_ORG_CLONE_BASE_DIR=~/code
```

## Testing

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_github_client.py

# Run single test
pytest tests/test_cli.py::TestMainFunction::test_main_success -v

# Run with coverage report
pytest --cov=github_org_cloner --cov-report=html
```

## Code Quality Tools

```bash
# Format code (line length: 100)
black github_org_cloner tests

# Lint
ruff check github_org_cloner tests

# Type check (strict mode enabled)
mypy github_org_cloner
```

## Running the CLI

```bash
# Simple entry point (uses .env file)
python main.py https://github.com/openai

# Or use the installed CLI command
github-org-cloner https://github.com/openai

# With all options
python main.py https://github.com/openai \
  --parallel \
  --max-workers 4 \
  --run-setup \
  --dry-run \
  --verbose
```

## Architecture

### Module Responsibilities

The codebase follows a clean separation of concerns:

1. **cli.py** - Entry point and user interaction
   - Argument parsing with `argparse`
   - Interactive prompts for missing configuration
   - Orchestrates the entire clone workflow
   - Handles all user-facing logging and error messages

2. **config.py** - Configuration resolution
   - Loads `.env` file automatically using `python-dotenv`
   - Merges .env, environment variables, and CLI arguments
   - Priority: CLI arguments > Environment variables > .env file
   - Validates required configuration (base_dir)

3. **github_client.py** - GitHub API integration
   - Parses and validates organization URLs
   - Handles GitHub REST API pagination automatically
   - Contains custom exceptions: `OrganizationNotFoundError`, `RateLimitError`, `GitHubAPIError`
   - Returns `Repository` dataclass instances

4. **cloner.py** - Repository cloning logic
   - Supports both sequential and parallel cloning modes
   - Uses `ThreadPoolExecutor` for parallel execution
   - Returns results dictionary: `{repo_name: (success: bool, error: Optional[str])}`
   - Handles existing repositories (skips with warning)

5. **setup_runner.py** - Post-clone setup detection
   - Detects project types (Node, Python, Ruby, Go, Rust)
   - Safe by default (only suggests actions, doesn't run unless `--run-setup`)
   - When `auto_run=True`, executes `setup.sh` scripts if present

### Data Flow

```text
.env file (optional)
  ↓
CLI (argparse)
  → Config.from_args() [loads dotenv]
  → GitHubClient.list_org_repositories()
  → clone_all_repositories()
  → run_setup_for_all() (optional)
```

### Key Design Patterns

- **Configuration Priority**: CLI flags > Environment variables > .env file > Interactive prompts
- **Simple Entry Point**: `main.py` allows running without installation (`python main.py <org>`)
- **Error Handling**: Each module raises specific exceptions caught by CLI for user-friendly messages
- **Testability**: All external calls (GitHub API, git subprocess) are mocked in tests
- **Return Values**: Functions return structured data (tuples, dicts) rather than relying on side effects

## Testing Strategy

### Mocking Patterns

1. **GitHub API**: Use `requests-mock` to mock HTTP responses

   - Test pagination by mocking multiple pages
   - Test error codes (404, 403 for rate limits)

2. **Git Operations**: Mock `subprocess.run` to avoid actual git clones

   - Check command arguments passed to subprocess
   - Test timeout and error scenarios

3. **User Input**: Use `monkeypatch` to mock `input()` and `getpass.getpass()`

   - For CLI tests, patch `get_github_token()` to avoid stdin issues with pytest

4. **Filesystem**: Use pytest's `tmp_path` fixture for temporary directories

### Test Coverage Expectations

- Maintain >75% overall coverage
- Core modules (config, github_client) should have >95% coverage
- Test both success paths and error conditions

## Important Implementation Details

### GitHub API Pagination

The `list_org_repositories()` method handles pagination automatically by:

- Setting `per_page=100` (GitHub's maximum)
- Checking the `Link` header for `rel="next"`
- Continuing until no repos are returned or no next link

### Parallel Cloning Safety

- Uses `ThreadPoolExecutor` (not `ProcessPoolExecutor`) since git clone is I/O-bound
- Default `max_workers=None` lets Python choose based on CPU count
- Each clone operation is independent and handles its own errors
- Results are aggregated after all futures complete

### Configuration Validation

The `Config.from_args()` classmethod raises `ValueError` if:

- `base_dir` is not provided via argument, environment variable, or .env file
- This is caught in `cli.py` main() and exits with code 1

### Exit Codes

- `0`: Success (all repos cloned or no repos found)
- `1`: Error (missing config, org not found, rate limit, or any clone failures)

## Type Hints

This project uses **strict mypy configuration**:

- All functions must have complete type hints (args and return values)
- Use Python 3.11+ syntax: `list[Foo]` not `List[Foo]`, `str | None` not `Optional[str]`
- The `Repository` dataclass uses `Optional[str]` for nullable description field

## Common Gotchas

1. **CLI Tests**: Always mock `get_github_token()` to avoid stdin reading issues in pytest
2. **URL Parsing**: The `parse_org_name()` method adds scheme if missing, so `github.com/openai` is valid
3. **Existing Repos**: The cloner skips (not overwrites) existing directories - this is intentional
4. **Dry Run**: When `dry_run=True`, no directories are created and no git commands run
5. **Setup Runner**: By default only suggests actions; only runs scripts when `--run-setup` flag is used

## Configuration Files

### .env File

The project uses `python-dotenv` to load environment variables from a `.env` file:

- `.env` - User configuration (git ignored)
- `.env.example` - Template showing available variables

### Environment Variables

- `GITHUB_ORG_CLONE_BASE_DIR`: Required (or use `--base-dir` flag or set in .env)
- `GITHUB_TOKEN`: Optional but recommended for higher API rate limits (60/hour → 5000/hour)

## Package Management

**IMPORTANT**: This project uses `uv` exclusively. Do not use `pip` commands in documentation or code changes.

- Use `uv sync` instead of `pip install`
- Use `uv sync --all-extras` for development dependencies
- The `pyproject.toml` includes `python-dotenv` as a core dependency
