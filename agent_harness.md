# AI Agent Development Guidelines 

## TASK

Each enemy only takes single hit from tower and dies. Enemy should survive for multiple hits before dying.  Fix this issue. 

## Project Paths

- **Project_root:**  `/home/manigupt/Hello/python/control/arcade_games/tower_defence`
- **Source_code:** (Working directory) `/home/manigupt/Hello/python/control/arcade_games/tower_defence/codebase`

## Code Execution & Validation Environment

- **Command to run project:** `cd /home/manigupt/Hello/python/control/arcade_games/tower_defence/codebase && conda run -n myenv python main.py`.
- **Command to run Tests :** `cd /home/manigupt/Hello/python/control/arcade_games/tower_defence/codebase && conda run -n myenv python -m pytest tests/ -v`

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

## Testing Mandates (Non-Negotiable)

Every feature/change **must** include:

- **Unit tests** for new/altered systems & controllers (mock event bus, components).
- **Red → Green → Refactor**: Agent first writes failing test → implements → passes.
- Aim for **>80% coverage** on logic-heavy files (systems/controllers).

Use your language's test framework (e.g., pytest/unittest).