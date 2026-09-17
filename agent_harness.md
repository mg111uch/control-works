## Project Paths

- **Project_root:**  `/home/manigupt/Hello/control-works`
- **Source_code:** (Working directory) `/home/manigupt/Hello/control-works`

## Code Execution & Validation Environment

- **Command to run project:** `conda run -n myenv python <subdir>/<script>.py` from `/home/manigupt/Hello/control-works`
- Conda env `myenv` is shared with the PIE repo (`/home/manigupt/Hello/Agentic_Unit_PIE`); install NOTHING without user approval.

## Core principles

- **Small scope always** — Never ask the agent to change >3 files at once or understand the full codebase.
- **Strict modularity** — Single responsibility, clear interfaces, minimal coupling.
- **Test-first mindset** — Tests are the safety net for AI-generated code.
- **Human-in-the-loop** — Agent proposes → you review → apply → test → commit.
- Optimize for handling large codebases while maintaining output quality.

## File & Module Size Rules

- Max **400–500 lines** per file (including tests & comments).
- **One public class/struct/interface** per file (ECS: one component OR one system).
- Split large files ruthlessly when they exceed 500 LOC or violate single responsibility.
