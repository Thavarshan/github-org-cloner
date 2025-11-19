# Contributing to GitHub Organization Cloner

Thank you for your interest in contributing to GitHub Organization Cloner! We welcome contributions from the community.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (command you ran, expected vs actual behavior)
- **Include your environment details** (OS, Python version, uv version)
- **Add any relevant logs or error messages**

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **Include examples** of how it would work

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Set up your development environment:**

   ```bash
   uv venv
   source .venv/bin/activate
   uv sync --all-extras
   cp .env.example .env
   # Edit .env with test configuration
   ```

3. **Make your changes:**
   - Write clear, commented code
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Ensure all tests pass:**

   ```bash
   pytest
   black github_org_cloner tests
   ruff check github_org_cloner tests
   mypy github_org_cloner
   ```

5. **Commit your changes:**
   - Use clear, descriptive commit messages
   - Reference related issues (e.g., "Fixes #123")

6. **Push to your fork** and submit a pull request

## Development Guidelines

### Code Style

- **Python 3.11+** syntax required
- **Type hints** on all functions (strict mypy configuration)
- **Google-style docstrings** for all public functions
- **Line length:** 100 characters max
- **Formatting:** Use `black` (runs automatically)
- **Linting:** Use `ruff` (runs automatically)

### Testing

- Write tests for all new features
- Maintain >75% overall test coverage
- Core modules should have >95% coverage
- Use mocking for external dependencies (GitHub API, git commands)
- Tests should be fast and not require network access

### Documentation

- Update README.md for user-facing changes
- Update CLAUDE.md for architecture changes
- Add docstrings for new functions/classes
- Update CHANGELOG.md with your changes

## Package Management

**IMPORTANT:** This project uses `uv` exclusively.

- ✅ Use `uv sync` for dependencies
- ✅ Use `uv sync --all-extras` for dev dependencies
- ❌ Do NOT use `pip` commands

## Project Structure

```
github_org_cloner/
├── cli.py              # Command-line interface
├── config.py           # Configuration with .env support
├── github_client.py    # GitHub API integration
├── cloner.py           # Cloning logic
└── setup_runner.py     # Post-clone setup detection
```

## Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_github_client.py

# With coverage report
pytest --cov=github_org_cloner --cov-report=html

# Single test
pytest tests/test_cli.py::TestMainFunction::test_main_success -v
```

## Code Quality Checks

```bash
# Format code
black github_org_cloner tests

# Lint
ruff check github_org_cloner tests

# Type check
mypy github_org_cloner
```

## Release Process

(For maintainers)

1. Update version in `github_org_cloner/__init__.py` and `pyproject.toml`
2. Update CHANGELOG.md
3. Create a git tag: `git tag -a v0.x.0 -m "Release v0.x.0"`
4. Push tag: `git push origin v0.x.0`

## Questions?

Feel free to open an issue for any questions or discussions!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
