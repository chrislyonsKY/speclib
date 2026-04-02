# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ |

## Reporting a Vulnerability

**Do not report security vulnerabilities through public GitHub Issues.**

To report a vulnerability:

1. Email **chris@chrislyons.dev** with the subject line:
   `[Security] speclib — brief description`
2. Include:
   - A description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested mitigations (optional)

You will receive an acknowledgment within **72 hours**. We aim to triage and respond
with a timeline within **7 days**.

## Disclosure Policy

We follow [responsible disclosure](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure).
Please allow us reasonable time to patch before public disclosure.

## Scope

**In scope:**
- Vulnerabilities in project source code
- Dependency vulnerabilities introduced by this project's configuration
- FastAPI server security issues

**Out of scope:**
- Vulnerabilities in upstream dependencies (report to upstream maintainer)
- Issues in development/test tooling not shipped with the project

## Security Updates

Security fixes are documented in [CHANGELOG.md](CHANGELOG.md) under the `### Security` heading.
