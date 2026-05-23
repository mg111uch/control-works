# AI Agent Development Guidelines 

## TASK

Fix the issues in the game using code fixes given in `@python/dota2/claudeSonnet4_5/code_fixes.md` .  Currently all tests pass.

## Code Execution & Validation Environment

- **Command to Run Game:** `cd python/dota2/claudeSonnet4_5/dota2_gym && conda run -n myenv python main.py`.
- **Command to Run Test :** `cd python/dota2/claudeSonnet4_5/dota2_gym && conda run -n myenv python -m pytest tests/ -v --tb=short 2>&1 | tail -20`

## Project files

- **Base_path:**  `/home/manigupt/Hello/python/dota2/claudeSonnet4_5/code_atlas.md`
- **Children_path:**  `/home/manigupt/Hello/python/dota2/claudeSonnet4_5/children`
- **Source_code:** (Working directory) `/home/manigupt/Hello/python/dota2/claudeSonnet4_5/dota2_gym`

## Codebase Atlas Navigation Flow

- You are not allowed to understand full source code. Only work with task based scope.
- Use this flow to read relevant source files instead of reading full source code.
    1. Agent reads code_atlas.md → Gets overview, entry points, critical deps
    2. Agent identifies relevant module → Reads specific children/X.md
    3. Agent needs implementation details → Reads actual source file

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
- **Integration smoke tests** for core loops (input → ECS tick → render).
- **View tests** — at minimum property assertions (position, visibility) + visual smoke checklist.
- Controller examples: input → command/event mapping, mode switching, buffering.
- **Red → Green → Refactor**: Agent first writes failing test → implements → passes.
- Aim for **>80% coverage** on logic-heavy files (systems/controllers).

Use your language's test framework (e.g., pytest/unittest).