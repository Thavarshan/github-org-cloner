"""Configuration management for the GitHub organization cloner."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env file from current directory or parent directories
load_dotenv()


@dataclass
class Config:
    """Configuration for the GitHub organization cloner.

    Attributes:
        base_dir: Base directory where repositories will be cloned.
        github_token: GitHub personal access token for API authentication.
        parallel: Whether to clone repositories in parallel.
        max_workers: Maximum number of parallel workers.
        run_setup: Whether to run setup scripts after cloning.
        dry_run: Whether to perform a dry run without actually cloning.
    """

    base_dir: Path
    github_token: Optional[str]
    parallel: bool = False
    max_workers: Optional[int] = None
    run_setup: bool = False
    dry_run: bool = False

    @classmethod
    def from_args(
        cls,
        base_dir: Optional[str] = None,
        github_token: Optional[str] = None,
        parallel: bool = False,
        max_workers: Optional[int] = None,
        run_setup: bool = False,
        dry_run: bool = False,
    ) -> "Config":
        """Create a Config instance from command-line arguments and environment variables.

        Configuration priority (highest to lowest):
        1. Command-line arguments
        2. Environment variables
        3. .env file variables

        Args:
            base_dir: Base directory path (overrides env var if provided).
            github_token: GitHub token (overrides env var if provided).
            parallel: Enable parallel cloning.
            max_workers: Maximum number of parallel workers.
            run_setup: Run setup scripts after cloning.
            dry_run: Perform a dry run without cloning.

        Returns:
            A Config instance.

        Raises:
            ValueError: If base_dir is not provided via argument, environment variable, or .env file.
        """
        # Determine base directory from CLI arg or env var (which includes .env)
        final_base_dir = base_dir or os.getenv("GITHUB_ORG_CLONE_BASE_DIR")

        if not final_base_dir:
            raise ValueError(
                "Base directory must be provided via --base-dir flag, "
                "GITHUB_ORG_CLONE_BASE_DIR environment variable, or .env file"
            )

        # Determine GitHub token from CLI arg or env var (which includes .env)
        final_token = github_token or os.getenv("GITHUB_TOKEN")

        return cls(
            base_dir=Path(final_base_dir).expanduser().resolve(),
            github_token=final_token,
            parallel=parallel,
            max_workers=max_workers,
            run_setup=run_setup,
            dry_run=dry_run,
        )
