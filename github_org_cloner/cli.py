"""Command-line interface for the GitHub organization cloner."""

import argparse
import getpass
import logging
import os
import sys

from . import __version__
from .cloner import clone_all_repositories
from .config import Config
from .github_client import (
    GitHubAPIError,
    GitHubClient,
    OrganizationNotFoundError,
    RateLimitError,
)
from .setup_runner import run_setup_for_all


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.

    Args:
        verbose: If True, set log level to DEBUG, otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


def get_github_token(token_arg: str | None) -> str | None:
    """Get GitHub token from argument, environment, or user input.

    Args:
        token_arg: Token provided via command-line argument.

    Returns:
        GitHub token or None if not provided.
    """
    # First check argument
    if token_arg:
        return token_arg

    # Then check environment variable
    env_token = os.getenv("GITHUB_TOKEN")
    if env_token:
        return env_token

    # Prompt user (securely, without echo)
    print(
        "No GitHub token found. You can continue without a token, but "
        "you'll have lower API rate limits."
    )
    print("Press Enter to continue without a token, or enter a token:")

    try:
        token = getpass.getpass("GitHub token (optional): ")
        return token if token.strip() else None
    except (KeyboardInterrupt, EOFError):
        print("\nNo token provided.")
        return None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Clone all repositories from a GitHub organization.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://github.com/openai --base-dir ~/code
  %(prog)s https://github.com/openai --parallel --max-workers 4
  %(prog)s openai --base-dir ~/code --run-setup --dry-run

Environment Variables:
  GITHUB_ORG_CLONE_BASE_DIR  Base directory for cloning (can be overridden by --base-dir)
  GITHUB_TOKEN               GitHub personal access token for API authentication
        """,
    )

    parser.add_argument(
        "org_url",
        nargs="?",
        help="GitHub organization URL (e.g., https://github.com/openai) or name",
    )

    parser.add_argument(
        "--base-dir",
        help="Base directory where repositories will be cloned "
        "(overrides GITHUB_ORG_CLONE_BASE_DIR env var)",
    )

    parser.add_argument(
        "--token",
        help="GitHub personal access token (overrides GITHUB_TOKEN env var)",
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Clone repositories in parallel",
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of parallel workers (default: number of CPUs)",
    )

    parser.add_argument(
        "--run-setup",
        action="store_true",
        help="Run setup scripts after cloning repositories",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually cloning",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser.parse_args()


def get_org_url(org_url_arg: str | None) -> str:
    """Get organization URL from argument or user input.

    Args:
        org_url_arg: Organization URL provided via command-line argument.

    Returns:
        Organization URL.
    """
    if org_url_arg:
        return org_url_arg

    # Prompt user for org URL
    try:
        org_url = input("Enter GitHub organization URL (e.g., https://github.com/openai): ")
        if not org_url.strip():
            print("Error: Organization URL cannot be empty.", file=sys.stderr)
            sys.exit(1)
        return org_url.strip()
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    args = parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    # Get organization URL
    org_url = get_org_url(args.org_url)

    # Get GitHub token
    github_token = get_github_token(args.token)

    # Create configuration
    try:
        config = Config.from_args(
            base_dir=args.base_dir,
            github_token=github_token,
            parallel=args.parallel,
            max_workers=args.max_workers,
            run_setup=args.run_setup,
            dry_run=args.dry_run,
        )
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"GitHub Organization Cloner v{__version__}")
    logger.info(f"Base directory: {config.base_dir}")

    if config.dry_run:
        logger.info("DRY RUN MODE - No repositories will be cloned")

    # Initialize GitHub client
    client = GitHubClient(token=config.github_token)

    # Parse organization name from URL
    try:
        org_name = client.parse_org_name(org_url)
        logger.info(f"Organization: {org_name}")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Fetch repositories
    try:
        logger.info(f"Fetching repositories for {org_name}...")
        repos = client.list_org_repositories(org_name)
    except OrganizationNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except RateLimitError as e:
        logger.error(str(e))
        sys.exit(1)
    except GitHubAPIError as e:
        logger.error(f"GitHub API error: {e}")
        sys.exit(1)

    if not repos:
        logger.warning(f"No repositories found for organization '{org_name}'")
        sys.exit(0)

    # Clone repositories
    try:
        results = clone_all_repositories(
            repos=repos,
            org_name=org_name,
            base_dir=config.base_dir,
            parallel=config.parallel,
            max_workers=config.max_workers,
            dry_run=config.dry_run,
        )
    except Exception as e:
        logger.error(f"Error during cloning: {e}")
        sys.exit(1)

    # Run setup if requested and not in dry-run mode
    if config.run_setup and not config.dry_run:
        # Get paths of successfully cloned repos
        successful_repos = [
            config.base_dir / org_name / repo_name
            for repo_name, (success, _) in results.items()
            if success
        ]

        if successful_repos:
            run_setup_for_all(successful_repos, auto_run=True)

    # Check if any clones failed
    failed_repos = [repo_name for repo_name, (success, _) in results.items() if not success]

    if failed_repos:
        logger.warning(f"\nSome repositories failed to clone: {', '.join(failed_repos)}")
        sys.exit(1)

    logger.info("\nAll done!")


if __name__ == "__main__":
    main()
