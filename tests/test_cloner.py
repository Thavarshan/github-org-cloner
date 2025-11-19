"""Tests for the repository cloning logic."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from github_org_cloner.cloner import (
    CloneError,
    clone_all_repositories,
    clone_repository,
)
from github_org_cloner.github_client import Repository


@pytest.fixture
def sample_repo() -> Repository:
    """Create a sample repository for testing."""
    return Repository(
        name="test-repo",
        clone_url="https://github.com/testorg/test-repo.git",
        ssh_url="git@github.com:testorg/test-repo.git",
        description="A test repository",
    )


@pytest.fixture
def sample_repos() -> list[Repository]:
    """Create a list of sample repositories for testing."""
    return [
        Repository(
            name=f"repo{i}",
            clone_url=f"https://github.com/testorg/repo{i}.git",
            ssh_url=f"git@github.com:testorg/repo{i}.git",
            description=f"Repo {i}",
        )
        for i in range(1, 4)
    ]


class TestCloneRepository:
    """Tests for cloning a single repository."""

    def test_clone_repository_success(
        self,
        tmp_path: Path,
        sample_repo: Repository,
    ) -> None:
        """Test successful repository cloning."""
        with patch("github_org_cloner.cloner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            repo_name, success, error = clone_repository(
                sample_repo,
                "testorg",
                tmp_path,
            )

            assert repo_name == "test-repo"
            assert success is True
            assert error is None

            # Verify git clone was called correctly
            expected_path = tmp_path / "testorg" / "test-repo"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[0] == "git"
            assert args[1] == "clone"
            assert args[2] == "https://github.com/testorg/test-repo.git"
            assert args[3] == str(expected_path)

    def test_clone_repository_already_exists(
        self,
        tmp_path: Path,
        sample_repo: Repository,
    ) -> None:
        """Test cloning when repository already exists."""
        # Create the directory to simulate existing repo
        repo_path = tmp_path / "testorg" / "test-repo"
        repo_path.mkdir(parents=True)

        with patch("github_org_cloner.cloner.subprocess.run") as mock_run:
            repo_name, success, error = clone_repository(
                sample_repo,
                "testorg",
                tmp_path,
            )

            assert repo_name == "test-repo"
            assert success is False
            assert error == "Already exists"

            # Verify git clone was NOT called
            mock_run.assert_not_called()

    def test_clone_repository_git_error(
        self,
        tmp_path: Path,
        sample_repo: Repository,
    ) -> None:
        """Test handling of git clone errors."""
        with patch("github_org_cloner.cloner.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=["git", "clone"],
                stderr="fatal: repository not found",
            )

            repo_name, success, error = clone_repository(
                sample_repo,
                "testorg",
                tmp_path,
            )

            assert repo_name == "test-repo"
            assert success is False
            assert "Failed to clone" in error
            assert "fatal: repository not found" in error

    def test_clone_repository_timeout(
        self,
        tmp_path: Path,
        sample_repo: Repository,
    ) -> None:
        """Test handling of clone timeout."""
        with patch("github_org_cloner.cloner.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd=["git", "clone"],
                timeout=300,
            )

            repo_name, success, error = clone_repository(
                sample_repo,
                "testorg",
                tmp_path,
            )

            assert repo_name == "test-repo"
            assert success is False
            assert "timeout" in error.lower()

    def test_clone_repository_git_not_found(
        self,
        tmp_path: Path,
        sample_repo: Repository,
    ) -> None:
        """Test handling when git command is not found."""
        with patch("github_org_cloner.cloner.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git command not found")

            with pytest.raises(CloneError, match="git command not found"):
                clone_repository(sample_repo, "testorg", tmp_path)

    def test_clone_repository_dry_run(
        self,
        tmp_path: Path,
        sample_repo: Repository,
    ) -> None:
        """Test dry run mode doesn't actually clone."""
        with patch("github_org_cloner.cloner.subprocess.run") as mock_run:
            repo_name, success, error = clone_repository(
                sample_repo,
                "testorg",
                tmp_path,
                dry_run=True,
            )

            assert repo_name == "test-repo"
            assert success is True
            assert error is None

            # Verify git clone was NOT called
            mock_run.assert_not_called()

    def test_clone_repository_creates_parent_dir(
        self,
        tmp_path: Path,
        sample_repo: Repository,
    ) -> None:
        """Test that parent directory is created if it doesn't exist."""
        with patch("github_org_cloner.cloner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            clone_repository(sample_repo, "testorg", tmp_path)

            # Verify parent directory was created
            assert (tmp_path / "testorg").exists()


class TestCloneAllRepositories:
    """Tests for cloning multiple repositories."""

    def test_clone_all_sequential(
        self,
        tmp_path: Path,
        sample_repos: list[Repository],
    ) -> None:
        """Test sequential cloning of repositories."""
        with patch("github_org_cloner.cloner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            results = clone_all_repositories(
                repos=sample_repos,
                org_name="testorg",
                base_dir=tmp_path,
                parallel=False,
            )

            assert len(results) == 3
            assert all(success for success, _ in results.values())
            assert mock_run.call_count == 3

    def test_clone_all_parallel(
        self,
        tmp_path: Path,
        sample_repos: list[Repository],
    ) -> None:
        """Test parallel cloning of repositories."""
        with patch("github_org_cloner.cloner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            results = clone_all_repositories(
                repos=sample_repos,
                org_name="testorg",
                base_dir=tmp_path,
                parallel=True,
                max_workers=2,
            )

            assert len(results) == 3
            assert all(success for success, _ in results.values())
            assert mock_run.call_count == 3

    def test_clone_all_empty_list(
        self,
        tmp_path: Path,
    ) -> None:
        """Test cloning with empty repository list."""
        results = clone_all_repositories(
            repos=[],
            org_name="testorg",
            base_dir=tmp_path,
        )

        assert len(results) == 0

    def test_clone_all_mixed_results(
        self,
        tmp_path: Path,
        sample_repos: list[Repository],
    ) -> None:
        """Test cloning with some successes and some failures."""
        # Create first repo directory to simulate it already existing
        (tmp_path / "testorg" / "repo1").mkdir(parents=True)

        with patch("github_org_cloner.cloner.subprocess.run") as mock_run:
            # Second repo succeeds, third repo fails
            mock_run.side_effect = [
                MagicMock(returncode=0),  # repo2 succeeds
                subprocess.CalledProcessError(1, ["git"], stderr="error"),  # repo3 fails
            ]

            results = clone_all_repositories(
                repos=sample_repos,
                org_name="testorg",
                base_dir=tmp_path,
                parallel=False,
            )

            assert len(results) == 3
            assert results["repo1"] == (False, "Already exists")
            assert results["repo2"][0] is True
            assert results["repo3"][0] is False

    def test_clone_all_dry_run(
        self,
        tmp_path: Path,
        sample_repos: list[Repository],
    ) -> None:
        """Test dry run mode for all repositories."""
        with patch("github_org_cloner.cloner.subprocess.run") as mock_run:
            results = clone_all_repositories(
                repos=sample_repos,
                org_name="testorg",
                base_dir=tmp_path,
                dry_run=True,
            )

            assert len(results) == 3
            assert all(success for success, _ in results.values())

            # Verify git clone was never called
            mock_run.assert_not_called()

    def test_clone_all_creates_org_directory(
        self,
        tmp_path: Path,
        sample_repos: list[Repository],
    ) -> None:
        """Test that organization directory is created."""
        with patch("github_org_cloner.cloner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            clone_all_repositories(
                repos=sample_repos,
                org_name="testorg",
                base_dir=tmp_path,
            )

            assert (tmp_path / "testorg").exists()
            assert (tmp_path / "testorg").is_dir()
