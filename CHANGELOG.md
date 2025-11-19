# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-11-19

### Added

- Initial release of GitHub Organization Cloner
- Clone all repositories from a GitHub organization
- Support for sequential and parallel cloning modes
- `.env` file support for easy configuration
- Simple `main.py` entry point (no installation required)
- GitHub API integration with pagination support
- Automatic detection of existing repositories (skips re-cloning)
- Dry-run mode for previewing operations
- Progress tracking and detailed logging
- Post-clone setup detection for multiple project types:
  - Node.js (`package.json`)
  - Python (`pyproject.toml`, `requirements.txt`, `setup.py`)
  - Ruby (`Gemfile`)
  - Go (`go.mod`)
  - Rust (`Cargo.toml`)
  - Makefiles
  - Custom setup scripts (`setup.sh`)
- Configurable via CLI flags, environment variables, or `.env` file
- Comprehensive test suite (57 tests, 80% coverage)
- Full `uv` package manager integration
- Production-quality error handling:
  - Organization not found (404)
  - Rate limit detection
  - Network errors
  - Git clone failures
  - Timeout handling

### Configuration

- Configuration priority: CLI flags > Environment variables > .env file
- Required: `GITHUB_ORG_CLONE_BASE_DIR` (base directory for cloning)
- Optional: `GITHUB_TOKEN` (for higher API rate limits: 60/hr → 5000/hr)

### Documentation

- Comprehensive README with quick start guide
- CLAUDE.md for AI-assisted development
- Full API documentation with Google-style docstrings
- Type hints on all functions (strict mypy configuration)

### Testing

- Unit tests for all core modules
- Mocked external dependencies (GitHub API, git commands)
- pytest configuration with coverage reporting
- All tests pass without network access

[0.1.0]: https://github.com/Thavarshan/github-org-cloner/releases/tag/v0.1.0
