# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of GitHub Organization Cloner seriously. If you have discovered a security vulnerability, we appreciate your help in disclosing it to us responsibly.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to the project maintainers. You should receive a response within 48 hours.

Please include the following information in your report:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## What to Expect

After you submit a vulnerability report, we will:

1. Confirm receipt of your vulnerability report
2. Provide an estimated timeline for a fix
3. Notify you when the vulnerability is fixed
4. Credit you for the discovery (unless you prefer to remain anonymous)

## Security Considerations

When using this tool, please keep in mind:

### GitHub Token Security

- **Never commit your GitHub token** to version control
- Store tokens in `.env` file (already in `.gitignore`)
- Use tokens with minimal required permissions (only `repo` scope needed for public repos)
- Consider using fine-grained personal access tokens with specific repository access
- Rotate tokens regularly

### Cloned Repository Security

- Be aware that cloning repositories downloads all code and history
- Review the repositories you're cloning, especially from unknown organizations
- Cloned repositories may contain secrets or sensitive data in their history
- Consider running security scans on cloned repositories

### File System Security

- The tool creates directories and writes files to your filesystem
- Ensure the `GITHUB_ORG_CLONE_BASE_DIR` is in a safe location
- Be cautious when running with elevated privileges

### Network Security

- All GitHub API requests use HTTPS
- Tokens are transmitted securely
- Consider using VPN when accessing sensitive repositories

## Known Security Limitations

- This tool does not scan cloned repositories for secrets or malware
- Git hooks in cloned repositories are preserved and could execute code
- No signature verification is performed on cloned content

## Best Practices

1. Use read-only tokens when possible
2. Run in an isolated environment for untrusted organizations
3. Review `.env` file permissions (should be 600 or 400)
4. Keep the tool updated to the latest version
5. Enable two-factor authentication on your GitHub account

## Dependencies

We regularly update dependencies to patch known vulnerabilities. Run `uv sync` regularly to get the latest security patches.
