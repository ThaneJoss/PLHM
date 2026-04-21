# AGENTS.md

## Project

- The project name is `PLHM`, not `PHLM`.
- Use the current repository root as the working directory.
- Do not assume a fixed absolute path for the local checkout.

## Repository Workflow

- Use Git author `codex <codex@thanejoss.com>`.
- Make code changes in the local repository root for the active checkout.
- Use local Git for `commit` and `push`.
- After each completed change, open a pull request for the user to review.
- Use Chinese for pull request titles and descriptions.
- Target `main` with each pull request and keep the working branch synced with `main`.
- Keep `main` as the primary branch unless the user requests a different branching workflow.

## Privacy and Infrastructure

- Keep private infrastructure details, machine-specific paths, hostnames, SSH settings, and server notes out of the repository.
- Store sensitive operational notes only in local Codex memory or other non-repository local files.
- Do not run local `uv` package installation or execution commands such as `uv sync`, `uv add`, or `uv run` on this machine.
- This machine is only a lightweight jump host; use the remote SSH development server for dependency installation, running code, testing, and debugging.

## GitHub

- The GitHub repository is `https://github.com/ThaneJoss/PLHM`.
