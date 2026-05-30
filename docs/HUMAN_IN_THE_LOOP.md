# Human-in-the-loop Agentic Coding

SNES Studio is designed around safe, reviewable agent assistance for children.

## Core rule

The helper never silently changes the project. It proposes patches. A kid, mentor, parent, or teacher reviews and applies them.

## Patch lifecycle

```text
Prompt -> Proposed patch -> Review -> Apply -> Validate -> Export
```

## Patch safety

Patches use editor operations such as:

- add scene
- add actor
- add event chain
- add event step
- update actor
- add trigger

They do not write arbitrary source code.

## Classroom language

The UI should explain patches as game-making changes, not opaque code diffs. Generated C is available for mentors and advanced learners.
