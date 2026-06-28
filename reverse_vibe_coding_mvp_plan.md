# Reverse Vibe Coding - MVP Plan

## Vision

**Reverse Vibe Coding** is an AI-managed software engineering
apprenticeship platform.

Instead of asking AI to write software, students act as the software
engineer while AI acts as:
-   Tech Lead
-   Mentor
-   Reviewer
-   Product Manager

The goal is to optimize for **engineering competence**, not
time-to-code.

------------------------------------------------------------------------

## Core Value Proposition

Current IDE-native agents (Codex, Cursor, Claude Code) optimize for:

> Ship software as quickly as possible.

Reverse Vibe Coding optimizes for:

> Learn to think and work like a professional software engineer.

The platform focuses on:

-   Software engineering process
-   Architectural reasoning
-   Testing mindset
-   Code review
-   Debugging
-   Communication
-   Reflection
-   Working within existing codebases

------------------------------------------------------------------------

# MVP Philosophy

The MVP intentionally avoids building a custom LLM orchestration
platform.

Students bring their own AI tools:

-   ChatGPT
-   Codex
-   Cursor
-   Claude Code
-   Gemini
-   Ollama/Qwen
-   Aider

Reverse Vibe Coding provides:

-   Randomized project generation
-   SWE curriculum
-   Tasks and scenarios
-   Rubrics
-   Hidden tests
-   Progression system

------------------------------------------------------------------------

# System Architecture

``` text
reverse-vibecoding/
├── templates/
├── generators/
├── scenarios/
├── rubrics/
├── prompts/
├── hidden_tests/
└── rv CLI
```

------------------------------------------------------------------------

# Project Generation

Projects are generated from orthogonal components.

## Project =

``` text
Domain + Stack + Completeness + Scenario + Task Sequence
```

------------------------------------------------------------------------

## Domains (initial)

-   Todo App
-   Habit Tracker
-   Expense Tracker

------------------------------------------------------------------------

## Supported Stacks

Backend:

-   FastAPI
-   Express

Frontend:

-   React
-   Backend-only

Database:

-   SQLite
-   PostgreSQL

------------------------------------------------------------------------

## Completeness Levels

### Level 0 - Greenfield

Student builds nearly everything.

### Level 1 - Skeleton

Folder structure and scaffolding provided.

### Level 2 - Partial Implementation

Architecture exists. Student implements logic.

### Level 3 - Maintenance Mode

Existing application provided.

Student:

-   fixes bugs
-   adds features
-   refactors
-   writes tests

------------------------------------------------------------------------

# Scenario Modifiers

Examples:

-   Authentication
-   RBAC
-   Pagination
-   Rate Limiting
-   Accessibility
-   Performance constraints

------------------------------------------------------------------------

# Hidden Bug Seeds

Examples:

-   Missing validation
-   SQL injection
-   Race condition
-   Off-by-one error

------------------------------------------------------------------------

# Student Workflow

``` bash
rv init
rv start-task
rv test
rv submit
rv reflect
rv next
```

------------------------------------------------------------------------

# LLM Integration Strategy

Reverse Vibe Coding does not host LLMs.

Instead:

1.  Generate repo locally.
2.  Generate mentor prompts.
3.  Student loads prompts into preferred AI agent.

Example mentor instructions:

-   Never write production code directly.
-   Give hints instead of solutions.
-   Ask architectural questions.
-   Require testing.
-   Require justification of decisions.
-   Review code critically.

------------------------------------------------------------------------

# Grading Pipeline

## Deterministic Assessment

### Build Checks

-   Install succeeds
-   Project compiles
-   Application starts

### Tests

-   Unit tests
-   Integration tests
-   End-to-end tests
-   Hidden tests

### Static Analysis

-   Linting
-   Formatting
-   Type checking
-   Coverage

------------------------------------------------------------------------

## Learning Assessment

Students must explain:

-   Architecture
-   File modifications
-   Tradeoffs
-   Edge cases
-   Technical debt

Reflection is mandatory.

------------------------------------------------------------------------

# Git-Based Tracking

Use Git as source of truth.

No custom VCS.

The framework wraps Git operations.

Examples:

``` bash
git init
git commit
git diff
git tag
```

Local metadata:

``` text
.rv/
  progress.json
  project.yaml
  tasks/
  submissions/
```

------------------------------------------------------------------------

# Anti-Cheating Philosophy

Perfect prevention is impossible.

Instead:

AI-generated solutions alone should be insufficient.

Mechanisms:

-   Hidden tests
-   Reflection questions
-   Architectural defense
-   Random debugging questions
-   Follow-up modifications
-   Git history analysis

Students must demonstrate understanding.

------------------------------------------------------------------------

# Future Roadmap

## Phase 1

-   CLI
-   Repo generator
-   Templates
-   Hidden tests
-   Prompt packs

## Phase 2

-   Progress tracking
-   Badges
-   Skill trees

## Phase 3

-   VS Code extension

## Phase 4

-   Optional hosted AI mentor

------------------------------------------------------------------------

# Slogan Ideas

> Stop vibe-coding. Start engineering.

> Learn software engineering under an AI tech lead.

> LeetCode for software engineering.

> Internship simulator for the AI era.
