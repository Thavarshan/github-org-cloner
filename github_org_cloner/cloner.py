"""Repository cloning logic with support for sequential and parallel execution."""

import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from .github_client import Repository

logger = logging.getLogger(__name__)


class CloneError(Exception):
    """Raised when a repository clone operation fails."""
    pass


def clone_repository(
    repo: Repository,
    org_name: str,
    base_dir: Path,
    dry_run: bool = False,
) -> tuple[str, bool, Optional[str]]:
    """Clone a single repository.

    Args:
        repo: Repository to clone.
        org_name: Organization name (used for directory structure).
        base_dir: Base directory where repos are cloned.
        dry_run: If True, don't actually clone, just report what would happen.

    Returns:
        A tuple of (repo_name, success, error_message).

    Raises:
        CloneError: If the clone operation fails (when not in dry_run mode).
    """
    target_path = base_dir / org_name / repo.name

    # Check if repository already exists
    if target_path.exists():
        logger.warning(f"Repository '{repo.name}' already exists at {target_path}, skipping")
        return (repo.name, False, "Already exists")

    if dry_run:
        logger.info(f"[DRY RUN] Would clone {repo.name} to {target_path}")
        return (repo.name, True, None)

    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Cloning {repo.name} to {target_path}")

    try:
        # Run git clone
        result = subprocess.run(
            ["git", "clone", repo.clone_url, str(target_path)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per repo
            check=True,
        )

        logger.info(f"Successfully cloned {repo.name}")
        return (repo.name, True, None)

    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to clone {repo.name}: {e.stderr}"
        logger.error(error_msg)
        return (repo.name, False, error_msg)

    except subprocess.TimeoutExpired:
        error_msg = f"Clone timeout for {repo.name} (exceeded 5 minutes)"
        logger.error(error_msg)
        return (repo.name, False, error_msg)

    except FileNotFoundError:
        error_msg = "git command not found. Please ensure git is installed and in your PATH."
        logger.error(error_msg)
        raise CloneError(error_msg)


def clone_all_repositories(
    repos: list[Repository],
    org_name: str,
    base_dir: Path,
    parallel: bool = False,
    max_workers: Optional[int] = None,
    dry_run: bool = False,
) -> dict[str, tuple[bool, Optional[str]]]:
    """Clone all repositories for an organization.

    Args:
        repos: List of repositories to clone.
        org_name: Organization name.
        base_dir: Base directory where repos are cloned.
        parallel: If True, clone repositories in parallel.
        max_workers: Maximum number of parallel workers (only used if parallel=True).
        dry_run: If True, don't actually clone, just report what would happen.

    Returns:
        Dictionary mapping repo names to (success, error_message) tuples.

    Raises:
        CloneError: If git is not available or other critical errors occur.
    """
    if not repos:
        logger.warning("No repositories to clone")
        return {}

    logger.info(f"Found {len(repos)} repositories to clone")

    # Ensure base directory exists
    org_dir = base_dir / org_name
    if not dry_run:
        org_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cloning repositories to: {org_dir}")

    results = {}

    if parallel:
        # Parallel cloning with ThreadPoolExecutor
        logger.info(f"Cloning in parallel with max_workers={max_workers}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all clone tasks
            future_to_repo = {
                executor.submit(
                    clone_repository,
                    repo,
                    org_name,
                    base_dir,
                    dry_run,
                ): repo
                for repo in repos
            }

            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_repo):
                repo = future_to_repo[future]
                try:
                    repo_name, success, error = future.result()
                    results[repo_name] = (success, error)
                    completed += 1
                    logger.info(f"Progress: {completed}/{len(repos)} repositories processed")
                except Exception as e:
                    logger.error(f"Unexpected error cloning {repo.name}: {e}")
                    results[repo.name] = (False, str(e))
                    completed += 1
    else:
        # Sequential cloning
        logger.info("Cloning sequentially")

        for i, repo in enumerate(repos, 1):
            logger.info(f"Progress: {i}/{len(repos)}")
            try:
                repo_name, success, error = clone_repository(
                    repo,
                    org_name,
                    base_dir,
                    dry_run,
                )
                results[repo_name] = (success, error)
            except Exception as e:
                logger.error(f"Unexpected error cloning {repo.name}: {e}")
                results[repo_name] = (False, str(e))

    # Summary
    successful = sum(1 for success, _ in results.values() if success)
    failed = len(results) - successful

    logger.info(f"\nCloning complete: {successful} successful, {failed} failed/skipped")

    return results
