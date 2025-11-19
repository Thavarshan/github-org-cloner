"""Tests for the GitHub API client."""

import pytest
import requests
import requests_mock

from github_org_cloner.github_client import (
    GitHubAPIError,
    GitHubClient,
    OrganizationNotFoundError,
    RateLimitError,
    Repository,
)


class TestParseOrgName:
    """Tests for parsing organization names from URLs."""

    def test_parse_basic_url(self) -> None:
        """Test parsing a basic GitHub organization URL."""
        assert GitHubClient.parse_org_name("https://github.com/openai") == "openai"

    def test_parse_url_with_trailing_slash(self) -> None:
        """Test parsing URL with trailing slash."""
        assert GitHubClient.parse_org_name("https://github.com/openai/") == "openai"

    def test_parse_url_without_scheme(self) -> None:
        """Test parsing URL without scheme."""
        assert GitHubClient.parse_org_name("github.com/openai") == "openai"

    def test_parse_url_with_www(self) -> None:
        """Test parsing URL with www prefix."""
        assert GitHubClient.parse_org_name("https://www.github.com/openai") == "openai"

    def test_parse_org_name_with_hyphens(self) -> None:
        """Test parsing org name with hyphens."""
        assert GitHubClient.parse_org_name("https://github.com/my-org-name") == "my-org-name"

    def test_parse_org_name_with_numbers(self) -> None:
        """Test parsing org name with numbers."""
        assert GitHubClient.parse_org_name("https://github.com/org123") == "org123"

    def test_parse_invalid_domain(self) -> None:
        """Test parsing URL from non-GitHub domain."""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            GitHubClient.parse_org_name("https://gitlab.com/openai")

    def test_parse_empty_org_name(self) -> None:
        """Test parsing URL without organization name."""
        with pytest.raises(ValueError, match="No organization name found"):
            GitHubClient.parse_org_name("https://github.com/")

    def test_parse_invalid_org_format(self) -> None:
        """Test parsing invalid organization name format."""
        with pytest.raises(ValueError, match="Invalid organization name format"):
            GitHubClient.parse_org_name("https://github.com/-invalid")


class TestListOrgRepositories:
    """Tests for listing organization repositories."""

    def test_list_repos_single_page(self, requests_mock: requests_mock.Mocker) -> None:
        """Test listing repositories with a single page of results."""
        mock_response = [
            {
                "name": "repo1",
                "clone_url": "https://github.com/testorg/repo1.git",
                "ssh_url": "git@github.com:testorg/repo1.git",
                "description": "Test repo 1",
            },
            {
                "name": "repo2",
                "clone_url": "https://github.com/testorg/repo2.git",
                "ssh_url": "git@github.com:testorg/repo2.git",
                "description": None,
            },
        ]

        requests_mock.get(
            "https://api.github.com/orgs/testorg/repos",
            json=mock_response,
        )

        client = GitHubClient()
        repos = client.list_org_repositories("testorg")

        assert len(repos) == 2
        assert repos[0].name == "repo1"
        assert repos[0].clone_url == "https://github.com/testorg/repo1.git"
        assert repos[0].description == "Test repo 1"
        assert repos[1].name == "repo2"
        assert repos[1].description is None

    def test_list_repos_multiple_pages(self, requests_mock: requests_mock.Mocker) -> None:
        """Test listing repositories with pagination."""
        page1_response = [
            {
                "name": f"repo{i}",
                "clone_url": f"https://github.com/testorg/repo{i}.git",
                "ssh_url": f"git@github.com:testorg/repo{i}.git",
                "description": f"Repo {i}",
            }
            for i in range(1, 101)
        ]

        page2_response = [
            {
                "name": "repo101",
                "clone_url": "https://github.com/testorg/repo101.git",
                "ssh_url": "git@github.com:testorg/repo101.git",
                "description": "Repo 101",
            }
        ]

        requests_mock.get(
            "https://api.github.com/orgs/testorg/repos?per_page=100&page=1&type=all",
            json=page1_response,
            headers={"Link": '<https://api.github.com/orgs/testorg/repos?page=2>; rel="next"'},
        )

        requests_mock.get(
            "https://api.github.com/orgs/testorg/repos?per_page=100&page=2&type=all",
            json=page2_response,
        )

        client = GitHubClient()
        repos = client.list_org_repositories("testorg")

        assert len(repos) == 101
        assert repos[0].name == "repo1"
        assert repos[100].name == "repo101"

    def test_list_repos_empty_org(self, requests_mock: requests_mock.Mocker) -> None:
        """Test listing repositories for an organization with no repos."""
        requests_mock.get(
            "https://api.github.com/orgs/emptyorg/repos",
            json=[],
        )

        client = GitHubClient()
        repos = client.list_org_repositories("emptyorg")

        assert len(repos) == 0

    def test_list_repos_org_not_found(self, requests_mock: requests_mock.Mocker) -> None:
        """Test listing repositories for a non-existent organization."""
        requests_mock.get(
            "https://api.github.com/orgs/nonexistent/repos",
            status_code=404,
            json={"message": "Not Found"},
        )

        client = GitHubClient()
        with pytest.raises(OrganizationNotFoundError, match="Organization 'nonexistent' not found"):
            client.list_org_repositories("nonexistent")

    def test_list_repos_rate_limit(self, requests_mock: requests_mock.Mocker) -> None:
        """Test handling of rate limit errors."""
        requests_mock.get(
            "https://api.github.com/orgs/testorg/repos",
            status_code=403,
            text="rate limit exceeded",
            headers={"X-RateLimit-Reset": "1234567890"},
        )

        client = GitHubClient()
        with pytest.raises(RateLimitError, match="rate limit exceeded"):
            client.list_org_repositories("testorg")

    def test_list_repos_with_token(self, requests_mock: requests_mock.Mocker) -> None:
        """Test that token is included in request headers."""
        mock_response = [
            {
                "name": "repo1",
                "clone_url": "https://github.com/testorg/repo1.git",
                "ssh_url": "git@github.com:testorg/repo1.git",
                "description": "Test repo",
            }
        ]

        adapter = requests_mock.get(
            "https://api.github.com/orgs/testorg/repos",
            json=mock_response,
        )

        client = GitHubClient(token="test_token_123")
        client.list_org_repositories("testorg")

        # Verify Authorization header was sent
        assert adapter.last_request is not None
        assert adapter.last_request.headers["Authorization"] == "token test_token_123"

    def test_list_repos_api_error(self, requests_mock: requests_mock.Mocker) -> None:
        """Test handling of generic API errors."""
        requests_mock.get(
            "https://api.github.com/orgs/testorg/repos",
            status_code=500,
            text="Internal Server Error",
        )

        client = GitHubClient()
        with pytest.raises(GitHubAPIError, match="status 500"):
            client.list_org_repositories("testorg")

    def test_list_repos_network_error(self, requests_mock: requests_mock.Mocker) -> None:
        """Test handling of network errors."""
        requests_mock.get(
            "https://api.github.com/orgs/testorg/repos",
            exc=requests.exceptions.ConnectionError("Network error"),
        )

        client = GitHubClient()
        with pytest.raises(GitHubAPIError, match="Failed to fetch repositories"):
            client.list_org_repositories("testorg")

    def test_list_repos_invalid_json(self, requests_mock: requests_mock.Mocker) -> None:
        """Test handling of invalid JSON responses."""
        requests_mock.get(
            "https://api.github.com/orgs/testorg/repos",
            text="invalid json",
        )

        client = GitHubClient()
        with pytest.raises(GitHubAPIError, match="Failed to parse API response"):
            client.list_org_repositories("testorg")


class TestRepository:
    """Tests for Repository dataclass."""

    def test_repository_creation(self) -> None:
        """Test creating a Repository instance."""
        repo = Repository(
            name="test-repo",
            clone_url="https://github.com/org/test-repo.git",
            ssh_url="git@github.com:org/test-repo.git",
            description="A test repository",
        )

        assert repo.name == "test-repo"
        assert repo.clone_url == "https://github.com/org/test-repo.git"
        assert repo.ssh_url == "git@github.com:org/test-repo.git"
        assert repo.description == "A test repository"

    def test_repository_with_none_description(self) -> None:
        """Test creating a Repository with None description."""
        repo = Repository(
            name="test-repo",
            clone_url="https://github.com/org/test-repo.git",
            ssh_url="git@github.com:org/test-repo.git",
            description=None,
        )

        assert repo.description is None
