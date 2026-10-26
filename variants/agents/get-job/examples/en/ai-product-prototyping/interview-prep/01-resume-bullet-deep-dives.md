# Resume Bullet Deep Dives · AI Product Prototyping Intern

> Every bullet in `resume-after.json` is covered below. Answers may be shortened in conversation, but their facts may not exceed [`../source-facts.md`](../source-facts.md).

## Bullet inventory

| ID | Resume area | Core claim | Source facts |
| --- | --- | --- | --- |
| P1-B1 | EventEase | Turned campus-event friction into one focused registration-to-export workflow | `EXP-3`, `EXP-4`, `PROJ-1`, `PROJ-2` |
| P1-B2 | EventEase | Defined four core fields and mapped them to forms, records, states, and export | `PROJ-3` |
| P1-B3 | EventEase | Used AI-assisted implementation while directing product scope and validation | `PROJ-8`, `PROJ-9`, `PROJ-10` |
| P1-B4 | EventEase | Added QR check-in and CSV export while documenting unresolved limits | `PROJ-4`, `PROJ-5` |
| P1-B5 | EventEase | Used small-scope testing to revise two clarity problems | `PROJ-6`, `PROJ-7` |
| E1-B1 | Marketing Operations | Organized feedback and operating information for review | `EXP-1` |
| E1-B2 | Marketing Operations | Coordinated follow-ups and made handoffs visible | `EXP-2` |
| E2-B1 | Campus Programs | Connected firsthand event support to the EventEase problem | `EXP-3`, `EXP-4` |
| E3-B1 | Student Business Lab | Cleaned survey data and communicated it through simple charts and a report | `EXP-5` |
| E4-B1 | Content Creation | Made unfamiliar information easier to understand through explainers | `EXP-6` |

## Deep dives

### P1-B1 · Problem and focused workflow

**30-second answer**

> While supporting campus programs, I repeatedly saw registration information spread across different places, manual check-in at the event, and organizers rebuilding attendance records afterward. I used that observation to narrow EventEase to one workflow: registration, check-in, attendance review, and CSV export. I intentionally did not try to build a complete event-management platform.

**Likely follow-ups**

- How often did you see this problem?
- Why was a new demo necessary instead of a form and spreadsheet?
- Who is the primary user?
- How did you decide what not to build?

**Evidence boundary**

- The candidate observed recurring friction but has no frequency or cost measurement.
- Existing forms and spreadsheets can solve parts of the problem; the demo explores one connected flow rather than claiming the alternatives are useless.
- The demo is local and fictional within this example, not a production deployment.

### P1-B2 · Core data model

**30-second answer**

> I kept the model deliberately small. `event` identifies the activity, `participant` stores the attendee record, `signup_status` shows where registration stands, and `check_in_time` records attendance. I mapped those fields to the form, stored record, status changes, attendance list, and CSV export so every field had a reason to exist.

**Likely follow-ups**

- Why are those four concepts enough for the demo?
- What state changes occur from sign-up to check-in?
- What would you add for multiple sessions or waitlists?
- What personal data does the demo collect?

**Evidence boundary**

- This is a prototype-level model, not an enterprise schema.
- Multi-session events, waitlists, retention policies, and advanced permissions are not implemented.
- Do not invent a field list beyond the four confirmed concepts unless answering explicitly as a future design proposal.

### P1-B3 · AI-assisted implementation

**30-second answer**

> AI coding tools assisted the implementation of the pages, forms, routes, and lightweight storage. My responsibility was to define the problem, constrain the workflow, choose the fields, write test cases and acceptance criteria, and check whether the generated behavior matched the intended flow. I can explain and debug the prototype at that level, but I would not claim that I wrote every line independently.

**Likely follow-ups**

- Which parts did the AI tool generate?
- What did you do when the generated behavior was wrong?
- Can you explain how the form reaches storage?
- How deep is your frontend or backend knowledge?

**Evidence boundary**

- The candidate can explain the user flow, core records, routes at a functional level, test cases, and observed errors.
- Deep framework internals, production architecture, scaling, and security implementation are outside the confirmed evidence.
- Never replace “AI-assisted” with “independently engineered.”

### P1-B4 · QR check-in and CSV export

**30-second answer**

> I chose QR-based check-in so a participant could open a lightweight flow without installing an app. The CSV export gives the organizer a portable attendance record after the event. Those choices support the narrow workflow, but the demo does not yet address QR sharing, advanced permissions, or production infrastructure.

**Likely follow-ups**

- What happens if someone shares the QR code?
- Why not require an organizer to check people in manually?
- Who uses the CSV and for what?
- Did these features save time?

**Evidence boundary**

- QR anti-sharing and permission controls are unresolved.
- The export's intended use is supported; no time-saving or adoption result was measured.
- Do not say the feature is secure, production-ready, or integrated with university systems.

### P1-B5 · Testing and iteration

**30-second answer**

> I ran small-scope test sessions with classmates and student event organizers. Two points of confusion were consistent enough to act on: the duplicate-registration error did not explain what happened, and participants could not tell whether check-in had succeeded. I rewrote the validation message and added a clearer success state, then checked the flow again.

**Likely follow-ups**

- How many people tested it?
- How did you collect feedback?
- What exactly changed in the interface?
- How do you know the revision was better?

**Evidence boundary**

- No exact tester count or formal usability metric is confirmed.
- The evidence supports two observed issues and two revisions, not statistically validated improvement.
- Say “small-scope testing,” not “user research at scale.”

### E1-B1 · Operations information synthesis

**30-second answer**

> In the marketing operations internship, I collected feedback and maintained task-status, message, and operating notes. The value was making scattered information easier for the team to review. That experience helped me notice how fragmented workflows create avoidable coordination work, but it was not formal product-research ownership.

**Likely follow-ups**

- What information did you organize?
- Did you create the process or follow an existing one?
- How did the team use the notes?

**Evidence boundary**

- The confirmed role is information and execution support.
- There is no confirmed strategy ownership, dashboard, metric improvement, or formal research program.

### E1-B2 · Cross-functional follow-up

**30-second answer**

> I coordinated follow-ups with project and content teammates and kept open items and handoffs visible. It taught me to make responsibilities and next steps explicit, even when I was not the person setting the overall strategy.

**Likely follow-ups**

- Which teammates were involved?
- What did a typical handoff look like?
- Describe a conflict you resolved.

**Evidence boundary**

- The source supports routine coordination, not a specific conflict-resolution story.
- If asked for an example that is not present in the fictional facts, say the example does not specify one rather than creating it.

### E2-B1 · Campus-event workflow observation

**30-second answer**

> As a campus program assistant, I supported registration, answered participant questions, and helped with manual check-in. That gave me direct exposure to scattered sign-up information and the effort of reconstructing attendance afterward. I used those observations to choose the EventEase problem; I did not treat the support role itself as product-management experience.

**Likely follow-ups**

- What did participants find confusing?
- Which problem belonged to organizers versus participants?
- Did the campus program use EventEase?

**Evidence boundary**

- The campus program informed the problem; it did not deploy EventEase.
- Do not imply an institutional pilot, approval, or integration.

### E3-B1 · Survey data and reporting

**30-second answer**

> In the student business lab, I cleaned survey data, made simple charts, prepared a short report, and presented it in class. It is basic evidence that I can organize information and communicate it clearly. I would not describe it as advanced analytics.

**Likely follow-ups**

- What tools did you use?
- What did the survey study?
- What decision did the analysis change?

**Evidence boundary**

- The confirmed facts do not specify the survey topic, tool, sample size, or downstream decision.
- Keep the answer at data cleaning, simple visualization, reporting, and presentation.

### E4-B1 · Explanatory content

**30-second answer**

> I create explainers about career topics, campus resources, and digital tools. The relevant skill is translating unfamiliar information into language a reader can follow, which also helps when I explain a prototype to a nontechnical audience.

**Likely follow-ups**

- Where was the content published?
- How large was the audience?
- Which piece performed best?

**Evidence boundary**

- No platform, audience size, engagement metric, or growth result is confirmed.
- The supported claim is communication practice, not content-performance success.

## Final evidence check

Before using any answer, verify that it preserves four boundaries:

1. Spring 2026 and GPA 3.70 remain unchanged.
2. EventEase remains a locally runnable demo, not a production product.
3. Implementation remains AI-assisted, with the candidate responsible for product definition and validation.
4. Qualitative observations do not become invented counts, rates, or impact metrics.
