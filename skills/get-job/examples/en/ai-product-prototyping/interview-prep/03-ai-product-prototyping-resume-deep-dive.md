# AI Product Prototyping and Resume Deep Dive

> High-confidence inferred stage for a fictional/composite role. Basis: the fictional JD explicitly requires a working demo, structured fields and states, basic debugging literacy, and clear explanation of technical tradeoffs. This is not a confirmed interview at a real company.

## What this stage is likely to evaluate

- Whether EventEase can be explained as a real, coherent local demo within the scenario.
- Whether the candidate separates product responsibility from AI-assisted implementation.
- Whether the fields, states, routes, tests, and limitations are understood beyond surface-level feature names.
- Whether follow-up questions produce evidence and boundaries rather than invented depth.

## Priority bullet map

| Bullet | Why it matters in this stage | Preparation |
| --- | --- | --- |
| P1-B1 | Establishes the problem and scope before implementation detail | [`01-resume-bullet-deep-dives.md#p1-b1--problem-and-focused-workflow`](01-resume-bullet-deep-dives.md#p1-b1--problem-and-focused-workflow) |
| P1-B2 | Tests whether the candidate understands the data behind the flow | [`01-resume-bullet-deep-dives.md#p1-b2--core-data-model`](01-resume-bullet-deep-dives.md#p1-b2--core-data-model) |
| P1-B3 | Tests code attribution and technical boundaries | [`01-resume-bullet-deep-dives.md#p1-b3--ai-assisted-implementation`](01-resume-bullet-deep-dives.md#p1-b3--ai-assisted-implementation) |
| P1-B4 | Tests interaction rationale and awareness of production gaps | [`01-resume-bullet-deep-dives.md#p1-b4--qr-check-in-and-csv-export`](01-resume-bullet-deep-dives.md#p1-b4--qr-check-in-and-csv-export) |
| P1-B5 | Tests whether feedback changed the product | [`01-resume-bullet-deep-dives.md#p1-b5--testing-and-iteration`](01-resume-bullet-deep-dives.md#p1-b5--testing-and-iteration) |

## Opening · 30 seconds

> EventEase is a locally runnable web demo for a narrow campus-event workflow: registration, QR-based check-in, attendance review, and CSV export. I chose the problem from friction I observed while supporting campus programs. AI coding tools assisted implementation, while I was responsible for defining the workflow, selecting the fields, writing test cases and acceptance criteria, and reviewing whether the generated behavior worked as intended.

## Core questions

### Walk me through the demo from start to finish.

> An organizer creates an `event`. A participant registers, creating or updating the `participant` record and `signup_status`. At the event, the participant opens the QR-based check-in flow; a successful action records `check_in_time`. The organizer can then review the attendance list and export it as CSV. The demo intentionally stops at that small loop rather than expanding into a full event platform.

**Boundary:** Do not add waitlists, reminders, payments, multiple sessions, or university integrations; none is confirmed in the source facts.

### What did the AI tool do, and what did you do?

> The AI tool assisted with code for the pages, forms, routes, and lightweight storage. I supplied the workflow and constraints, selected the core fields, defined expected states and errors, wrote test cases and acceptance criteria, and checked the behavior. When something did not match the intended flow, I used the failing behavior and expected outcome to guide the next iteration. I can explain the prototype at that level, but I would not claim to have written every line independently.

**Boundary:** Do not name a framework, model, prompt sequence, or debugging incident that is not in the fact ledger.

### Why these four fields?

> They are the minimum concepts required for the demo's output. `event` identifies what someone is attending. `participant` represents the attendee record. `signup_status` distinguishes the registration state. `check_in_time` provides the attendance event used in the list and export. A field had to support the workflow or it stayed out of the prototype.

**Boundary:** This is a product-level explanation of a small model, not a claim of advanced database design.

### What did testing reveal?

> Small-scope sessions exposed two clarity failures. A duplicate registration produced an error that did not explain what had happened, and a completed check-in did not create a clear enough success signal. I revised the validation copy and made the success state more visible, then reviewed the flow again.

**Boundary:** There is no tester count, usability score, conversion result, or statistical validation.

### What is the weakest part of the demo?

> The QR flow is convenient but not production-safe. The demo does not handle QR sharing, advanced permissions, or production infrastructure. That is the clearest gap between a useful prototype and a deployable system.

**Boundary:** Naming a next step is allowed; implying that it has already been built is not.

### How would you debug a failed check-in?

> I would first reproduce the exact state: which event, participant record, and signup status existed before the action. Then I would check whether the route received the expected identifier, whether the record update occurred, and whether the interface reflected the returned state. I would turn the failure into a repeatable test before changing the implementation.

**Boundary:** This is a proposed debugging method consistent with the candidate's confirmed prototype-level literacy, not a story about a specific incident that already happened.

## Demo narration checklist

- State “locally runnable demo” before showing the flow.
- Show the organizer and participant perspectives separately.
- Name the four core fields once; do not turn the walkthrough into a database lecture.
- Show the duplicate-registration message and check-in success state as examples of test-driven iteration.
- Close with one limitation and one next validation step.
- If the demo is unavailable, describe the flow honestly; do not pretend it is live.

## Questions for the interviewer

- “At this stage, how does the team divide responsibility between product judgment, AI-assisted prototyping, and production engineering?”
- “What evidence does the team need before a prototype moves into a production build?”
- “Which prototype failure is most expensive for your users: an incorrect result, an unclear state, or a broken workflow?”
