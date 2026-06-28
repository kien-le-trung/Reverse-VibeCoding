# Engineering Review Rubric

Use this rubric whenever you evaluate student-written code. Read it before giving code review feedback, then ground your comments in the rubric instead of personal preference.

The goal is not just working code. The student's code should be correct, maintainable, understandable, and aligned with common professional engineering practice.

## Correctness

- Requirements are implemented.
- Edge cases are handled deliberately.
- Error states are explicit and testable.
- Behavior is deterministic and does not depend on accidental global state unless the task explicitly allows it.
- Inputs are validated at the right boundary.
- API responses use appropriate status codes and response shapes.

## Design

- Domain model fits the problem.
- Responsibilities are separated clearly.
- Code is easy to change without broad rewrites.
- Route/controller code, domain logic, and persistence concerns are not unnecessarily mixed.
- Names describe intent and match the domain vocabulary.
- Abstractions are introduced only when they reduce real complexity.
- The implementation follows the surrounding codebase's style and conventions.
- Security, privacy, and data-integrity implications are considered for the task scope.

## Testing

- Core behavior has automated coverage.
- Failure paths are represented.
- Tests prove behavior instead of implementation details.
- Tests are small enough to diagnose failures quickly.
- Test data is isolated so test order does not matter.
- Important edge cases are covered before polishing less important cases.
- Manual checks are named when automated tests are not yet practical.

## Communication

- Tradeoffs are explained.
- Technical debt is named.
- Reflection shows understanding of the final code.
- Review feedback is specific, actionable, and prioritized by risk.
- Findings distinguish correctness issues from style preferences.
- The student can explain why the implementation belongs at the chosen boundary.

## Review Output

When reviewing code, lead with the most important issues first. Prefer this structure:

1. Correctness or behavioral risks.
2. Design and boundary concerns.
3. Missing or weak tests.
4. Smaller maintainability or readability improvements.
5. One short note on what the student did well only if it helps reinforce a practice.

Do not rewrite the solution for the student. Point to the relevant file or function, explain the issue, and ask the student for the next small fix.
