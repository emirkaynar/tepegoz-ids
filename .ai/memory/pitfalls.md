# Pitfalls

## Purpose

Record mistakes to avoid, especially around performance, deployment, and noisy task updates.

## Entries

- Do not turn the sprint file into a log of tiny implementation steps.
- Do not split the same decision across multiple memory systems.
- Do not add payload-inspection logic where metadata-only analysis is required.
- Avoid unbounded flow state; set flow timeouts and periodic cleanup to prevent memory leaks.
- Do not optimize for code elegance before measuring actual performance.
- Do not introduce new dependencies or library imports without checking against approved tech stack.
- Do not push Tier 2 ML work into active sprints unless a clear implementation decision is made and approved.
