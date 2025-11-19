"""Tests for the command-line interface."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from github_org_cloner.cli import get_github_token, get_org_url, main, parse_args
from github_org_cloner.github_client import OrganizationNotFoundError, RateLimitError


class TestParseArgs:
    """Tests for command-line argument parsing."""

    def test_parse_args_with_org_url(self) -> None:
        """Test parsing with organization URL provided."""
        test_args = ["prog", "https://github.com/openai"]
        with patch.object(sys, "argv", test_args):
            args = parse_args()
            assert args.org_url == "https://github.com/openai"

    def test_parse_args_with_base_dir(self) -> None:
        """Test parsing with base directory flag."""
        test_args = ["prog", "--base-dir", "/tmp/repos"]
        with patch.object(sys, "argv", test_args):
            args = parse_args()
            assert args.base_dir == "/tmp/repos"

    def test_parse_args_with_parallel(self) -> None:
        """Test parsing with parallel flag."""
        test_args = ["prog", "--parallel"]
        with patch.object(sys, "argv", test_args):
            args = parse_args()
            assert args.parallel is True

    def test_parse_args_with_max_workers(self) -> None:
        """Test parsing with max workers option."""
        test_args = ["prog", "--max-workers", "4"]
        with patch.object(sys, "argv", test_args):
            args = parse_args()
            assert args.max_workers == 4

    def test_parse_args_with_run_setup(self) -> None:
        """Test parsing with run-setup flag."""
        test_args = ["prog", "--run-setup"]
        with patch.object(sys, "argv", test_args):
            args = parse_args()
            assert args.run_setup is True

    def test_parse_args_with_dry_run(self) -> None:
        """Test parsing with dry-run flag."""
        test_args = ["prog", "--dry-run"]
        with patch.object(sys, "argv", test_args):
            args = parse_args()
            assert args.dry_run is True

    def test_parse_args_with_verbose(self) -> None:
        """Test parsing with verbose flag."""
        test_args = ["prog", "--verbose"]
        with patch.object(sys, "argv", test_args):
            args = parse_args()
            assert args.verbose is True

    def test_parse_args_combined(self) -> None:
        """Test parsing with multiple flags combined."""
        test_args = [
            "prog",
            "https://github.com/openai",
            "--base-dir",
            "/tmp/repos",
            "--parallel",
            "--max-workers",
            "8",
            "--run-setup",
        ]
        with patch.object(sys, "argv", test_args):
            args = parse_args()
            assert args.org_url == "https://github.com/openai"
            assert args.base_dir == "/tmp/repos"
            assert args.parallel is True
            assert args.max_workers == 8
            assert args.run_setup is True


class TestGetOrgUrl:
    """Tests for getting organization URL."""

    def test_get_org_url_from_arg(self) -> None:
        """Test getting org URL when provided as argument."""
        url = get_org_url("https://github.com/openai")
        assert url == "https://github.com/openai"

    def test_get_org_url_from_input(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting org URL from user input."""
        monkeypatch.setattr("builtins.input", lambda _: "https://github.com/openai")
        url = get_org_url(None)
        assert url == "https://github.com/openai"

    def test_get_org_url_empty_input(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling of empty user input."""
        monkeypatch.setattr("builtins.input", lambda _: "")

        with pytest.raises(SystemExit) as exc_info:
            get_org_url(None)

        assert exc_info.value.code == 1

    def test_get_org_url_keyboard_interrupt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling of keyboard interrupt."""
        monkeypatch.setattr("builtins.input", MagicMock(side_effect=KeyboardInterrupt))

        with pytest.raises(SystemExit) as exc_info:
            get_org_url(None)

        assert exc_info.value.code == 1


class TestGetGitHubToken:
    """Tests for getting GitHub token."""

    def test_get_token_from_arg(self) -> None:
        """Test getting token when provided as argument."""
        token = get_github_token("test_token_123")
        assert token == "test_token_123"

    def test_get_token_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting token from environment variable."""
        monkeypatch.setenv("GITHUB_TOKEN", "env_token_456")
        token = get_github_token(None)
        assert token == "env_token_456"

    def test_get_token_from_input(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting token from user input."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setattr("getpass.getpass", lambda _: "input_token_789")

        token = get_github_token(None)
        assert token == "input_token_789"

    def test_get_token_empty_input(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling of empty token input."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setattr("getpass.getpass", lambda _: "")

        token = get_github_token(None)
        assert token is None

    def test_get_token_keyboard_interrupt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling of keyboard interrupt when prompting for token."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setattr("getpass.getpass", MagicMock(side_effect=KeyboardInterrupt))

        token = get_github_token(None)
        assert token is None


class TestMainFunction:
    """Tests for main CLI function."""

    @patch("github_org_cloner.cli.get_github_token")
    @patch("github_org_cloner.cli.clone_all_repositories")
    @patch("github_org_cloner.cli.GitHubClient")
    def test_main_success(
        self,
        mock_client_class: MagicMock,
        mock_clone_all: MagicMock,
        mock_get_token: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test successful execution of main function."""
        # Setup
        monkeypatch.setenv("GITHUB_ORG_CLONE_BASE_DIR", str(tmp_path))
        test_args = ["prog", "https://github.com/testorg"]

        # Mock token retrieval
        mock_get_token.return_value = None

        # Mock GitHub client
        mock_client = MagicMock()
        mock_client.parse_org_name.return_value = "testorg"
        mock_client.list_org_repositories.return_value = [
            MagicMock(name="repo1"),
            MagicMock(name="repo2"),
        ]
        mock_client_class.return_value = mock_client

        # Mock clone results
        mock_clone_all.return_value = {
            "repo1": (True, None),
            "repo2": (True, None),
        }

        with patch.object(sys, "argv", test_args):
            main()

        # Verify client was called
        mock_client.list_org_repositories.assert_called_once_with("testorg")
        mock_clone_all.assert_called_once()

    @patch("github_org_cloner.cli.get_github_token")
    @patch("github_org_cloner.cli.GitHubClient")
    def test_main_missing_base_dir(
        self,
        mock_client_class: MagicMock,
        mock_get_token: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test error when base directory is not configured."""
        monkeypatch.delenv("GITHUB_ORG_CLONE_BASE_DIR", raising=False)
        test_args = ["prog", "https://github.com/testorg"]

        mock_get_token.return_value = None

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    @patch("github_org_cloner.cli.get_github_token")
    @patch("github_org_cloner.cli.GitHubClient")
    def test_main_org_not_found(
        self,
        mock_client_class: MagicMock,
        mock_get_token: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test error when organization is not found."""
        monkeypatch.setenv("GITHUB_ORG_CLONE_BASE_DIR", str(tmp_path))
        test_args = ["prog", "https://github.com/nonexistent"]

        mock_get_token.return_value = None

        # Mock GitHub client to raise OrganizationNotFoundError
        mock_client = MagicMock()
        mock_client.parse_org_name.return_value = "nonexistent"
        mock_client.list_org_repositories.side_effect = OrganizationNotFoundError(
            "Organization not found"
        )
        mock_client_class.return_value = mock_client

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    @patch("github_org_cloner.cli.get_github_token")
    @patch("github_org_cloner.cli.GitHubClient")
    def test_main_rate_limit(
        self,
        mock_client_class: MagicMock,
        mock_get_token: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test error when rate limit is exceeded."""
        monkeypatch.setenv("GITHUB_ORG_CLONE_BASE_DIR", str(tmp_path))
        test_args = ["prog", "https://github.com/testorg"]

        mock_get_token.return_value = None

        # Mock GitHub client to raise RateLimitError
        mock_client = MagicMock()
        mock_client.parse_org_name.return_value = "testorg"
        mock_client.list_org_repositories.side_effect = RateLimitError("Rate limit exceeded")
        mock_client_class.return_value = mock_client

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    @patch("github_org_cloner.cli.get_github_token")
    @patch("github_org_cloner.cli.clone_all_repositories")
    @patch("github_org_cloner.cli.GitHubClient")
    def test_main_no_repos(
        self,
        mock_client_class: MagicMock,
        mock_clone_all: MagicMock,
        mock_get_token: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test handling of organization with no repositories."""
        monkeypatch.setenv("GITHUB_ORG_CLONE_BASE_DIR", str(tmp_path))
        test_args = ["prog", "https://github.com/emptyorg"]

        mock_get_token.return_value = None

        # Mock GitHub client to return no repos
        mock_client = MagicMock()
        mock_client.parse_org_name.return_value = "emptyorg"
        mock_client.list_org_repositories.return_value = []
        mock_client_class.return_value = mock_client

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with 0 (success) but warning about no repos
            assert exc_info.value.code == 0

        # Verify clone was NOT called
        mock_clone_all.assert_not_called()

    @patch("github_org_cloner.cli.get_github_token")
    @patch("github_org_cloner.cli.run_setup_for_all")
    @patch("github_org_cloner.cli.clone_all_repositories")
    @patch("github_org_cloner.cli.GitHubClient")
    def test_main_with_setup(
        self,
        mock_client_class: MagicMock,
        mock_clone_all: MagicMock,
        mock_setup: MagicMock,
        mock_get_token: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test main function with --run-setup flag."""
        monkeypatch.setenv("GITHUB_ORG_CLONE_BASE_DIR", str(tmp_path))
        test_args = ["prog", "https://github.com/testorg", "--run-setup"]

        mock_get_token.return_value = None

        # Mock GitHub client
        mock_client = MagicMock()
        mock_client.parse_org_name.return_value = "testorg"
        mock_client.list_org_repositories.return_value = [MagicMock(name="repo1")]
        mock_client_class.return_value = mock_client

        # Mock clone results
        mock_clone_all.return_value = {"repo1": (True, None)}

        with patch.object(sys, "argv", test_args):
            main()

        # Verify setup was called
        mock_setup.assert_called_once()
        call_args = mock_setup.call_args[0]
        assert len(call_args[0]) == 1  # One successful repo
        assert call_args[0][0] == tmp_path / "testorg" / "repo1"

    @patch("github_org_cloner.cli.get_github_token")
    @patch("github_org_cloner.cli.clone_all_repositories")
    @patch("github_org_cloner.cli.GitHubClient")
    def test_main_with_failures(
        self,
        mock_client_class: MagicMock,
        mock_clone_all: MagicMock,
        mock_get_token: MagicMock,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test main function when some clones fail."""
        monkeypatch.setenv("GITHUB_ORG_CLONE_BASE_DIR", str(tmp_path))
        test_args = ["prog", "https://github.com/testorg"]

        mock_get_token.return_value = None

        # Mock GitHub client
        mock_client = MagicMock()
        mock_client.parse_org_name.return_value = "testorg"
        mock_client.list_org_repositories.return_value = [
            MagicMock(name="repo1"),
            MagicMock(name="repo2"),
        ]
        mock_client_class.return_value = mock_client

        # Mock clone results with one failure
        mock_clone_all.return_value = {
            "repo1": (True, None),
            "repo2": (False, "Clone failed"),
        }

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
