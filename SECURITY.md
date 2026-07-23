# Security Policy

## Overview

This repository is used to experiment with an AI-powered GitHub development agent.

The project follows a human-in-the-loop workflow:

1. Issue creation
2. Automated analysis
3. Human approval (`/approve`)
4. Automated implementation on a dedicated branch
5. Pull request creation
6. Human review and approval
7. Merge

No AI-generated change is intended to be merged directly into the `main` branch without human validation.

---

## Repository Security Controls

### Protected Main Branch

The `main` branch is protected.

The following controls are enforced:

- Pull Request required
- At least one approval required before merge
- Conversation resolution required before merge
- Force pushes disabled
- Direct AI modifications to `main` are prohibited

Only repository administrators may bypass these protections when necessary.

---

## AI Agent Restrictions

The agent is allowed to modify application source code only.

The following paths are protected and cannot be modified by the agent:

- `.git/`
- `.github/`
- `scripts/`

The agent is also prevented from:

- writing outside the repository directory
- using absolute paths
- traversing directories using `..`

---

## Pull Request Workflow

All agent-generated modifications must follow this workflow:

```text
Issue
↓
Analysis
↓
Human Approval
↓
Implementation
↓
Pull Request
↓
Human Review
↓
Merge