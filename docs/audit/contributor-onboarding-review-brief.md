# Contributor-onboarding review brief (Derek's instrument, captured 2026-07-29)

*Transcribed from Derek's prompt. The top of the source was cropped; the three surviving
questions from the cropped portion are kept below. Run this against a checkout with NO
prior project context — the reviewer must be fresh eyes by construction.*

---

(from the cropped earlier sections:)
- What would prevent an experienced engineer from making their first pull request?
- Which files would you add or reorganize?
- Which documentation would you consider essential before announcing the project publicly?

## 4. Architectural Documentation
- Are ADRs being used appropriately?
- Which decisions belong in ADRs versus project decisions versus retrospectives?
- Would you recommend introducing another document type (Project Decisions, Governance, RFCs, etc.)?

## 5. Operational Readiness
- Identify anything that could create friction for outside contributors:
  - broken links
  - private references
  - licensing ambiguity
  - public data concerns
  - documentation gaps
  - inconsistent terminology

## 6. Repository Health
Evaluate whether the repository feels:
- alive
- abandoned
- experimental
- production-ready
- research-heavy
- contributor-friendly

Explain why.

## 7. First-Time Contributor Simulation
Imagine you cloned the repository today.

Describe:
- what you'd read first,
- what would confuse you,
- what would impress you,
- what would make you hesitate before contributing.

## 8. High-Leverage Improvements
Recommend the 10 highest ROI improvements that would make the project significantly easier
to understand without requiring major code changes.

Prioritize improvements that:
- reduce cognitive load,
- improve navigation,
- preserve historical context,
- make future maintenance easier,
- help volunteers become productive quickly.

Do not critique implementation quality unless it directly affects maintainability or
contributor onboarding.

The goal is not to redesign the project — it is to reduce the amount of context required
for someone new to successfully contribute.
