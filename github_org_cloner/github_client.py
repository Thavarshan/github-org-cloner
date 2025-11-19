"""GitHub API client for fetching organization repositories."""

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests


@dataclass
class Repository:
    """Represents a GitHub repository.

    Attributes:
        name: Repository name.
        clone_url: HTTPS clone URL.
        ssh_url: SSH clone URL.
        description: Repository description.
    """

    name: str
    clone_url: str
    ssh_url: str
    description: Optional[str]


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    pass


class OrganizationNotFoundError(GitHubAPIError):
    """Raised when an organization is not found."""
    pass


class RateLimitError(GitHubAPIError):
    """Raised when GitHub API rate limit is exceeded."""
    pass


class GitHubClient:
    """Client for interacting with the GitHub REST API."""

    BASE_URL = "https://api.github.com"
    PER_PAGE = 100  # Maximum allowed by GitHub API

    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub client.

        Args:
            token: GitHub personal access token for authentication.
        """
        self.token = token
        self.session = requests.Session()

        if self.token:
            self.session.headers["Authorization"] = f"token {self.token}"

        self.session.headers["Accept"] = "application/vnd.github.v3+json"

    @staticmethod
    def parse_org_name(url: str) -> str:
        """Parse organization name from a GitHub URL.

        Args:
            url: GitHub organization URL (e.g., https://github.com/openai).

        Returns:
            Organization name.

        Raises:
            ValueError: If the URL format is invalid.

        Examples:
            >>> GitHubClient.parse_org_name("https://github.com/openai")
            'openai'
            >>> GitHubClient.parse_org_name("https://github.com/openai/")
            'openai'
            >>> GitHubClient.parse_org_name("github.com/openai")
            'openai'
        """
        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        parsed = urlparse(url)

        # Check if it's a GitHub URL
        if parsed.netloc not in ("github.com", "www.github.com"):
            raise ValueError(f"Invalid GitHub URL: {url}")

        # Extract path components
        path = parsed.path.strip("/")
        parts = path.split("/")

        if not parts or not parts[0]:
            raise ValueError(f"No organization name found in URL: {url}")

        # Return the first path component as org name
        org_name = parts[0]

        # Validate org name format (GitHub username/org rules)
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$", org_name):
            raise ValueError(f"Invalid organization name format: {org_name}")

        return org_name

    def list_org_repositories(self, org_name: str) -> list[Repository]:
        """List all repositories for a GitHub organization.

        Args:
            org_name: Name of the GitHub organization.

        Returns:
            List of Repository objects.

        Raises:
            OrganizationNotFoundError: If the organization doesn't exist.
            RateLimitError: If API rate limit is exceeded.
            GitHubAPIError: For other API errors.
        """
        repositories = []
        page = 1

        while True:
            url = f"{self.BASE_URL}/orgs/{org_name}/repos"
            params = {
                "per_page": self.PER_PAGE,
                "page": page,
                "type": "all",  # Include all repo types
            }

            try:
                response = self.session.get(url, params=params, timeout=30)
            except requests.RequestException as e:
                raise GitHubAPIError(f"Failed to fetch repositories: {e}") from e

            # Handle specific status codes
            if response.status_code == 404:
                raise OrganizationNotFoundError(
                    f"Organization '{org_name}' not found. "
                    "Please check the organization name and try again."
                )
            elif response.status_code == 403:
                # Check if it's a rate limit error
                if "rate limit" in response.text.lower():
                    reset_time = response.headers.get("X-RateLimit-Reset", "unknown")
                    raise RateLimitError(
                        f"GitHub API rate limit exceeded. "
                        f"Rate limit resets at: {reset_time}. "
                        "Consider providing a GitHub token for higher limits."
                    )
                else:
                    raise GitHubAPIError(
                        f"Access forbidden (403): {response.text}"
                    )
            elif response.status_code != 200:
                raise GitHubAPIError(
                    f"GitHub API request failed with status {response.status_code}: "
                    f"{response.text}"
                )

            # Parse response
            try:
                repos_data = response.json()
            except ValueError as e:
                raise GitHubAPIError(f"Failed to parse API response: {e}") from e

            # If no repos returned, we've reached the end
            if not repos_data:
                break

            # Convert to Repository objects
            for repo_data in repos_data:
                repositories.append(
                    Repository(
                        name=repo_data["name"],
                        clone_url=repo_data["clone_url"],
                        ssh_url=repo_data["ssh_url"],
                        description=repo_data.get("description"),
                    )
                )

            # Check if there are more pages
            # GitHub uses Link header for pagination
            link_header = response.headers.get("Link", "")
            if 'rel="next"' not in link_header:
                break

            page += 1

        return repositories
