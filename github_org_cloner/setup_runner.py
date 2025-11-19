"""Post-clone setup runner for repositories."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def run_optional_setup(repo_path: Path, auto_run: bool = False) -> None:
    """Run optional setup steps for a cloned repository.

    This function detects the project type and either runs setup automatically
    or provides helpful suggestions to the user.

    Args:
        repo_path: Path to the cloned repository.
        auto_run: If True, automatically run setup scripts when found.
                  If False, only provide suggestions.
    """
    if not repo_path.exists() or not repo_path.is_dir():
        logger.warning(f"Repository path does not exist: {repo_path}")
        return

    logger.info(f"Checking for setup options in {repo_path.name}")

    # Check for setup.sh script
    setup_script = repo_path / "setup.sh"
    if setup_script.exists():
        if auto_run:
            logger.info(f"Found setup.sh in {repo_path.name}, running it...")
            try:
                result = subprocess.run(
                    ["bash", str(setup_script)],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    check=True,
                )
                logger.info(f"Setup script completed successfully for {repo_path.name}")
                if result.stdout:
                    logger.debug(f"Setup output: {result.stdout}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Setup script failed for {repo_path.name}: {e.stderr}")
            except subprocess.TimeoutExpired:
                logger.error(f"Setup script timeout for {repo_path.name} (exceeded 5 minutes)")
        else:
            logger.info(
                f"  Found setup.sh in {repo_path.name}. " "Run it manually or use --run-setup flag."
            )

    # Check for Node.js project
    package_json = repo_path / "package.json"
    if package_json.exists():
        logger.info(
            f"  Detected Node.js project in {repo_path.name}. "
            "You may want to run 'npm install' or 'yarn install'."
        )

    # Check for Python project
    pyproject_toml = repo_path / "pyproject.toml"
    requirements_txt = repo_path / "requirements.txt"
    setup_py = repo_path / "setup.py"

    if pyproject_toml.exists() or requirements_txt.exists() or setup_py.exists():
        logger.info(
            f"  Detected Python project in {repo_path.name}. "
            "You may want to create a virtual environment and install dependencies:"
        )
        if pyproject_toml.exists():
            logger.info("    python -m venv venv && source venv/bin/activate && pip install -e .")
        elif requirements_txt.exists():
            logger.info(
                "    python -m venv venv && source venv/bin/activate && "
                "pip install -r requirements.txt"
            )

    # Check for Ruby project
    gemfile = repo_path / "Gemfile"
    if gemfile.exists():
        logger.info(
            f"  Detected Ruby project in {repo_path.name}. " "You may want to run 'bundle install'."
        )

    # Check for Go project
    go_mod = repo_path / "go.mod"
    if go_mod.exists():
        logger.info(
            f"  Detected Go project in {repo_path.name}. " "You may want to run 'go mod download'."
        )

    # Check for Rust project
    cargo_toml = repo_path / "Cargo.toml"
    if cargo_toml.exists():
        logger.info(
            f"  Detected Rust project in {repo_path.name}. " "You may want to run 'cargo build'."
        )

    # Check for Makefile
    makefile = repo_path / "Makefile"
    if makefile.exists():
        logger.info(
            f"  Found Makefile in {repo_path.name}. "
            "You may want to check 'make help' or run 'make'."
        )


def run_setup_for_all(
    repo_paths: list[Path],
    auto_run: bool = False,
) -> None:
    """Run setup checks for multiple repositories.

    Args:
        repo_paths: List of repository paths to check.
        auto_run: If True, automatically run setup scripts when found.
    """
    if not repo_paths:
        return

    logger.info(f"\nChecking setup options for {len(repo_paths)} repositories...")

    for repo_path in repo_paths:
        run_optional_setup(repo_path, auto_run)
