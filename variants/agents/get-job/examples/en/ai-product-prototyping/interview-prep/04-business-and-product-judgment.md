# Business and Product Judgment Discussion

> High-confidence inferred stage for a fictional/composite role. Basis: the fictional JD explicitly asks for workflow research, product decisions, user-risk awareness, and clear next steps. This is not a confirmed interview at a real company.

## What this stage is likely to evaluate

- Whether the candidate starts from a user workflow rather than from “using AI.”
- Whether scope follows the most important problem instead of becoming a feature list.
- Whether alternatives, failure costs, privacy, and operational ownership are considered.
- Whether the candidate can separate a tested observation from an untested product hypothesis.

## Priority bullet map

| Bullet | Product-judgment angle | Preparation |
| --- | --- | --- |
| P1-B1 | Problem selection and scope | [`01-resume-bullet-deep-dives.md#p1-b1--problem-and-focused-workflow`](01-resume-bullet-deep-dives.md#p1-b1--problem-and-focused-workflow) |
| P1-B4 | Interaction tradeoff and risk | [`01-resume-bullet-deep-dives.md#p1-b4--qr-check-in-and-csv-export`](01-resume-bullet-deep-dives.md#p1-b4--qr-check-in-and-csv-export) |
| P1-B5 | Evidence-driven iteration | [`01-resume-bullet-deep-dives.md#p1-b5--testing-and-iteration`](01-resume-bullet-deep-dives.md#p1-b5--testing-and-iteration) |
| E2-B1 | Firsthand workflow observation | [`01-resume-bullet-deep-dives.md#e2-b1--campus-event-workflow-observation`](01-resume-bullet-deep-dives.md#e2-b1--campus-event-workflow-observation) |

## Product story · 60 seconds

> I did not begin with the goal of adding AI to events. I began with a workflow I had seen while supporting campus programs: sign-up information was scattered, check-in was manual, and organizers reconstructed attendance afterward. I narrowed the demo to registration, check-in, attendance review, and CSV export. AI assistance made it faster to test that flow, but the product decisions were the scope, the four core fields, the QR tradeoff, the test cases, and what remained out of bounds.

## Core questions

### Why build this when forms and spreadsheets already exist?

> Forms and spreadsheets solve important parts of the workflow. The product hypothesis was that a lightweight connected flow could reduce the handoff between registration, on-site check-in, and post-event attendance review. The demo tests that connection; it does not prove that existing tools should be replaced.

**Evidence boundary:** The connected-flow rationale is supported. Superiority, adoption, and time savings are not.

### Who has the stronger problem: participants or organizers?

> Organizers have the broader operational burden because they reconcile information across the event. Participants mainly need a clear, low-friction registration and confirmation experience. That is why the prototype gives organizers the attendance list and export while keeping the participant flow small.

**Evidence boundary:** This is a product interpretation of the confirmed workflow, not a quantified ranking from formal research.

### Why use QR check-in?

> The intended advantage is a lightweight entry point without an app download. The tradeoff is that a shareable QR code can weaken trust in the attendance record. For a production design, I would define who can generate the code, how long it remains valid, and what organizer review is required before assuming the interaction is safe.

**Evidence boundary:** The demo includes the QR flow; the controls described are future design work.

### What did you decide not to build?

> I kept out payments, promotion, messaging, waitlists, multi-session scheduling, and advanced permissions because none was required to test the basic registration-to-attendance loop. The next feature should follow a validated failure in that loop, not a desire to make the feature list longer.

**Evidence boundary:** These exclusions explain scope. They are not features that were built and removed.

### What is the most important metric?

> The example does not have launch data, so I would not claim a north-star metric from results. For a future pilot, I would first define workflow measures such as completed registrations, valid check-ins, and organizer corrections, alongside qualitative reports of confusion. The first goal would be validating reliability and clarity, not maximizing volume.

**Evidence boundary:** These are proposed measures, not observed outcomes.

### What user or data risk matters most?

> The most immediate risks are collecting more participant information than the workflow needs, unclear access to attendance records, and QR sharing. A production path would require explicit data minimization, organizer permissions, retention decisions, and exception handling before broader use.

**Evidence boundary:** Risk identification is supported by the role's product-judgment requirement; no security implementation is claimed.

### Where does AI add value here?

> In this example, AI adds value primarily to the build process: it helps turn a scoped workflow into a testable demo quickly. The participant experience does not need an AI feature merely to qualify as an AI product prototype. The useful question is whether AI shortens the learning loop while the candidate still makes and validates the product decisions.

**Evidence boundary:** Do not invent an LLM feature inside EventEase; none exists in the confirmed facts.

## Prioritization exercise

If the next test shows one of these problems, prioritize in this order:

1. **Incorrect or ambiguous check-in state** — it undermines the core attendance record.
2. **Organizer cannot resolve an exception** — the workflow needs a safe recovery path.
3. **Participant copy is confusing** — improve clarity after state correctness is reliable.
4. **Requests for additional event-management features** — defer until the core loop is dependable.

This is a proposed decision rule for the interview, not a record of work already completed.

## Questions for the interviewer

- “Which user workflow is the team currently trying to make concrete through prototypes?”
- “How does the team decide that a prototype has generated enough evidence to stop, iterate, or move toward production?”
- “When speed and user trust conflict in an AI-assisted workflow, which failure modes does the team treat as unacceptable?”
