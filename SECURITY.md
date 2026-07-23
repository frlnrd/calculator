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
- `agent/`

The agent is also prevented from:

- writing outside the repository directory
- using absolute paths
- traversing directories using `..`

Any attempt to modify protected locations is rejected before files are written.

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
```

The agent does not automatically merge pull requests.

All merges remain under human control.

---

## Branch Management

Each approved issue is implemented on a dedicated branch:

```text
agent/issue-<number>
```

Examples:

```text
agent/issue-12
agent/issue-41
```

Branches are isolated from `main`.

Changes are reviewed through Pull Requests before integration.

Merged feature branches are automatically deleted after successful merge.

---

## State Management

The agent uses a state machine stored in GitHub issue labels.

Current states:

- `agent:waiting-approval`
- `agent:implementing`
- `agent:waiting-review`
- `agent:completed`

Only one state may be active at a time.

State changes are performed automatically by the workflow.

---

## Human Oversight

The repository follows a human-in-the-loop model.

The agent may:

- analyze issues
- propose solutions
- modify code
- create commits
- create pull requests

The agent may not:

- approve its own work
- merge pull requests
- bypass repository protections
- modify protected areas of the repository

Human approval is required before implementation begins.

Human review is required before merging.

---

## Secrets and Credentials

The repository uses GitHub Actions secrets.

Secrets must never be:

- committed to the repository
- written to logs
- included in generated code
- exposed in pull requests

Current workflow secrets include:

- `GROK_API_KEY`

GitHub authentication is performed using the temporary workflow token provided by GitHub Actions.

---

## Vulnerability Reporting

If you discover a security issue in this repository, please contact the repository owner privately rather than opening a public issue.

Please include:

- a description of the issue
- reproduction steps
- affected files or components
- estimated impact

Reports will be reviewed as soon as possible.

---

## Supported Versions

Only the version currently available on the default branch (`main`) is supported.

Experimental branches, including agent-generated branches, are not considered supported releases.

---

## Security Goals

The objectives of this repository are:

- protect the `main` branch
- require human validation before merge
- prevent modification of workflow infrastructure by the agent
- maintain full traceability of AI-generated changes
- preserve a complete audit trail through issues, commits and pull requests

Security takes precedence over automation.

---

## AI Governance

This repository is intended as an educational project for experimenting with AI software agents.

The agent operates under the following principles:

- Human decision remains authoritative.
- AI suggestions are not trusted by default.
- Every code modification must be reviewable.
- Repository protections must remain enforceable even against the agent itself.
- Agent capabilities may evolve over time, but security controls must remain stricter than agent permissions.