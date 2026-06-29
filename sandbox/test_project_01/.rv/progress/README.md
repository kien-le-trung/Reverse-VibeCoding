# Reverse VibeCoding Progress

This directory records what the coding agent changed, what evidence was reviewed, and what follow-up work remains.

Progress entries should be written by the operator after review, not before implementation. Do not ask the coding agent to maintain these logs; ask only for missing facts or evidence that cannot be inspected directly.

When creating or updating progress files, read `.agents/schemas/progress.schema.yaml` and keep the YAML front matter aligned with it.

Suggested naming:

- `001_understand_repo.md`
- `002_add_feature.md`
- `003_review_changes.md`

Each progress entry should include:

- task or feature completed
- what the coding agent changed or investigated
- acceptance status
- concepts explained, if any
- evidence reviewed, such as code paths, commands, screenshots, or tests
- mistakes, rework, or design tradeoffs discussed
- remaining gaps or next implementation target
