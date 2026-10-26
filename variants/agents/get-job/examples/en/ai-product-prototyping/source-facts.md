# Source Facts · AI Product Prototyping Example

> This is the single source of truth for this fictional teaching example. “Confirmed” below means fixed within the scenario; it does not describe a real person, company, hiring process, or product deployment.

## Scenario boundary

| Field | Fixed value |
| --- | --- |
| Scenario date | January 2026 |
| Target market | United States |
| Working language | US English |
| Candidate | `Candidate Name`, a fictional composite |
| Target role | AI Product Prototyping Intern |
| Company | Fictional early-stage product team |
| Role source | Fictional composite JD written for this repository example |

The example may demonstrate workflow, positioning, and evidence handling. It must not be presented as current market research about a real employer.

## Candidate facts

### Education

| ID | Confirmed fictional fact |
| --- | --- |
| EDU-1 | General University — Main Campus |
| EDU-2 | Bachelor of Arts in Business Analytics and Communication |
| EDU-3 | Minor in Data Analytics and Digital Media |
| EDU-4 | Expected graduation: Spring 2026 |
| EDU-5 | Cumulative GPA: 3.70 |
| EDU-6 | Relevant coursework: Business Statistics, Consumer Insights, Digital Product Strategy, and Professional Communication |

There is no confirmed Major GPA, academic honor, or course grade. None may be added to the resume.

### Experience

| ID | Confirmed fictional fact |
| --- | --- |
| EXP-1 | Marketing Operations Intern, Summer 2024–Present. Collected user feedback and maintained task-status, message, and operating notes. |
| EXP-2 | In the same internship, coordinated follow-ups with project and content teammates. The role was supportive; the candidate did not own the full marketing function. |
| EXP-3 | Campus Program Assistant, January 2025–Present. Supported event registration and check-in and answered participant questions. |
| EXP-4 | Through campus programs, observed recurring friction: sign-up information was scattered, check-in required manual work, and organizers rebuilt attendance records after events. |
| EXP-5 | Research Assistant, Student Business Lab, Summer 2023. Cleaned survey data, created simple charts, prepared a short report, and presented it in class. |
| EXP-6 | Content Creator, ongoing. Produced explanatory content about career topics, campus resources, and digital tools. No audience or performance metric is confirmed. |

### Skills and tools

| ID | Confirmed fictional fact |
| --- | --- |
| SKILL-1 | Uses Excel, Google Sheets, PowerPoint, basic Python, simple database tools, and basic demo pages. |
| SKILL-2 | Speaks English and Mandarin Chinese. |
| SKILL-3 | The experience facts support communication, teamwork, note taking, planning support, and documentation at a general level. |

### EventEase project

| ID | Confirmed fictional fact |
| --- | --- |
| PROJ-1 | In 2026, the candidate turned a generic “Event Sign-up Tool” project into a locally runnable web demo called EventEase. It was not deployed to production. |
| PROJ-2 | The demo covers one small workflow: event registration, participant check-in, an attendance list, and CSV export. It is not a full event-management platform. |
| PROJ-3 | The candidate defined four core data concepts: `event`, `participant`, `signup_status`, and `check_in_time`; then mapped them to forms, stored records, and the export. |
| PROJ-4 | The demo includes QR-based check-in. The rationale was to let participants open a lightweight flow without installing an app. Security and anti-sharing controls were not implemented. |
| PROJ-5 | The CSV export lets an organizer review attendance outside the demo. No measured time saving or operational impact is available. |
| PROJ-6 | The candidate ran small-scope test sessions with classmates and student event organizers. No exact tester count is confirmed. |
| PROJ-7 | Testing exposed two concrete issues: the duplicate-registration error was unclear, and participants could not tell whether check-in had succeeded. The candidate revised the validation copy and added a clearer success state. |
| PROJ-8 | AI coding tools assisted implementation across pages, forms, routes, and lightweight storage. The candidate must not claim to have written every line of code independently. |
| PROJ-9 | The candidate was responsible for problem definition, workflow scope, field selection, test cases, acceptance criteria, and checking whether the demo behaved as intended. |
| PROJ-10 | The candidate can explain the user flow, core fields, major states, test findings, and known limitations. Deep framework internals and production infrastructure are outside the confirmed evidence. |

## Fictional composite JD

The JD is scenario input, not a real posting.

| ID | Fictional requirement |
| --- | --- |
| JD-1 | Turn real operating workflows into requirements, user stories, and a focused prototype scope. |
| JD-2 | Build demo-ready web prototypes with AI-assisted coding, basic interfaces, lightweight storage, and simple reporting. |
| JD-3 | Define data fields, states, transitions, error handling, and low-friction interactions. |
| JD-4 | Test prototypes with users and iterate flows, edge cases, and product copy. |
| JD-5 | Explain product decisions, technical tradeoffs, user risk, and next steps to product and engineering partners. |
| JD-6 | Basic web and debugging literacy is expected; production engineering ownership is not. |

## Allowed evidence connections

These connections are interpretations supported by the facts above:

- `EXP-3` and `EXP-4` may be connected to why the candidate chose the EventEase problem.
- `EXP-1` may support synthesizing messy information into requirements, but it may not be described as formal user research ownership.
- `EXP-5` may support basic data organization and communication, but not advanced analytics.
- `EXP-6` may support clear explanation, but not content growth or audience impact.
- `PROJ-3`, `PROJ-7`, and `PROJ-9` support product judgment and validation ownership.
- `PROJ-8` and `PROJ-10` require explicit AI-assistance and technical-depth boundaries.

## Claim ledger for the tailored resume

| Resume bullet | Required source IDs |
| --- | --- |
| P1-B1 · Problem and scope | EXP-3, EXP-4, PROJ-1, PROJ-2 |
| P1-B2 · Data model | PROJ-3 |
| P1-B3 · AI-assisted implementation | PROJ-8, PROJ-9, PROJ-10 |
| P1-B4 · QR check-in and export | PROJ-4, PROJ-5 |
| P1-B5 · Testing and iteration | PROJ-6, PROJ-7 |
| E1-B1 · Operations information synthesis | EXP-1 |
| E1-B2 · Cross-functional follow-up | EXP-2 |
| E2-B1 · Campus-event workflow observation | EXP-3, EXP-4 |
| E3-B1 · Survey data and reporting | EXP-5 |
| E4-B1 · Explanatory content | EXP-6 |
| Skills section | SKILL-1, SKILL-2, SKILL-3, PROJ-3, PROJ-8, PROJ-9, PROJ-10 |

## Claims that are out of bounds

Do not add any of the following:

- Fall 2026 graduation, Major GPA, academic honors, or individual course grades.
- A precise tester count, user count, adoption metric, conversion rate, accuracy rate, or time-saving result.
- “Shipped,” “launched,” “production-ready,” “used at scale,” or integration with university systems.
- Sole authorship of the implementation or a claim that every line of code was written manually.
- Enterprise security, QR anti-sharing, advanced permissions, or production infrastructure.
- A real company name, real interview sequence, or current market conclusion.
