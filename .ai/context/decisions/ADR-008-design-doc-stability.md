# ADR-008: Design Documentation Stability

## Status

Accepted

## Context

The project has design documentation in `documents/md/` (SRS, SDD, Project Proposal) that will be finalized after the system is built. AI coordination files should summarize and operationalize these documents without requiring changes to them.

## Decision

Keep design documents intact and treated as canonical reference material.
All `.ai/` files and implementation decisions are derived from but do not modify the design documents.
If a contradiction appears between implementation and design, raise it explicitly rather than changing the design.

## Consequences

- Design documents remain the single source of truth for project scope and requirements.
- Implementation experience is captured in ADRs and memory, not by editing the original proposal.
- Easier to produce a final "as-built" report by comparing design documents with final implementation.
