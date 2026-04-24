---
name: delivery-readiness-audit
description: Spot-check AC internal consistency and scan for pending revisions on delivery-ready stories. Activated by `/gaai-status --audit` as Section 5. Complements the standard status checks with depth checks that standard status skips for speed.
license: MIT
compatibility: Works with any filesystem-based AI coding agent
metadata:
  author: gaai-framework
  version: "1.0"
  category: cross
  track: cross-cutting
  id: SKILL-CRS-019
  updated_at: 2026-02-23
  tags: [governance, delivery-gate, coherence]
  status: stable
inputs:
  - delivery-ready stories (from /gaai-status Section 1)
  - contexts/artefacts/stories/*.story.md (for each ready story)
  - contexts/backlog/active.backlog.yaml (notes field)
outputs:
  - ac_consistency_issues (structured list)
  - pending_revisions (structured list)
  - delivery_verdict (READY FOR DELIVERY | ISSUES TO RESOLVE FIRST)
---

# Delivery Readiness Audit

## Purpose / When to Activate

Activate via `/gaai-status --audit`. This skill runs **after** the standard status sections (1–4) have already identified delivery-ready stories, memory staleness, and framework health.

This skill adds two depth checks that standard status skips for speed:
