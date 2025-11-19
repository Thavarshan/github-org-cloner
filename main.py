#!/usr/bin/env python3
"""Simple entry point for github-org-cloner.

This allows you to run the tool directly with:
    python main.py <org-url>

Without having to install the package first.
"""

from github_org_cloner.cli import main

if __name__ == "__main__":
    main()
