# Delivery and Self-Introduction · AI Product Prototyping Intern

> Fixed preparation file for the fictional candidate. The goal is calm, precise communication: lead with the strongest evidence, state AI assistance naturally, and keep every boundary intact.

## Speaking posture

| Do | Avoid |
| --- | --- |
| Start with the workflow problem and product decision | Start by apologizing for a nontraditional background |
| Describe AI assistance in one clear sentence | Wait for the interviewer to expose an exaggerated code claim |
| Use concrete fields, states, and test findings | Hide behind generic phrases such as “I did product strategy” |
| Name unresolved risks without drama | Pretend a local demo is production-ready |
| Pause and state the evidence limit when needed | Fill a gap with a made-up number or technical detail |

## Self-introduction · 45 seconds

> I study Business Analytics and Communication, and the project that best represents how I work is EventEase, a local web demo for campus event registration and check-in. I started from friction I had seen while supporting campus programs, narrowed it to one registration-to-attendance workflow, defined the core fields and states, and used AI-assisted implementation to build and test the demo. I was responsible for the product scope, field choices, test cases, acceptance criteria, and review. I am interested in AI product prototyping because it combines the work I am strongest at: making a messy workflow concrete, building something testable, and learning from where users get confused.

## Keyword card

- Business Analytics and Communication
- EventEase
- Campus-event friction
- Focused workflow
- Four core fields
- AI-assisted implementation
- Product decisions and acceptance criteria
- Small-scope testing
- Two clarity fixes
- Locally runnable, not production

Use the card to recall the sequence. Do not read the full introduction from the screen.

## Project walkthrough · EventEase

### Context

> While supporting campus programs, I saw sign-up information spread across different places, manual check-in at the event, and organizers rebuilding attendance records afterward.

### My responsibility

> I defined the problem, kept the scope to registration, check-in, attendance review, and CSV export, selected the core fields, wrote test cases and acceptance criteria, and reviewed whether the demo behaved as intended. AI coding tools assisted implementation of the pages, forms, routes, and lightweight storage.

### How the flow works

> An organizer creates an event. A participant registers, which creates or updates the participant record and `signup_status`. At the event, the participant opens the QR-based check-in flow, and a successful action records `check_in_time`. The organizer can review the attendance list and export it as CSV.

### What testing changed

> Small-scope sessions showed that the duplicate-registration error was unclear and the check-in confirmation was too easy to miss. I rewrote the validation message and added a clearer success state, then checked the flow again.

### Limitations and next step

> It is a local demo. It does not have production permissions, QR anti-sharing controls, or production infrastructure. Before adding more features, I would first define organizer access and test an exception flow for duplicate or invalid check-ins.

## Honest boundary lines

| If asked | Grounded answer |
| --- | --- |
| “Did you write all the code?” | “No. Implementation was AI-assisted. I can explain the flow, fields, major states, tests, and how I reviewed generated behavior, but I would not claim independent authorship of every line.” |
| “How many users did you have?” | “This was small-scope testing, not a launch. The example does not support an exact tester or user count.” |
| “How much time did it save?” | “I did not measure a time-saving result. The CSV export was designed to reduce manual reconstruction, but that remains a product hypothesis.” |
| “Is the QR flow secure?” | “Not at a production standard. QR sharing and permissions are known limitations that would need design and engineering work.” |
| “Can you explain the full stack?” | “I can explain the user flow, records, major routes, states, and debugging at the prototype level. Deep framework internals and production infrastructure are outside the depth I can defend.” |
| “Was EventEase used by the campus program?” | “No institutional deployment is part of this example. The program experience informed the problem; the demo remained local.” |

## Practice actions

- Record the 45-second introduction once; remove apologies, filler, and any claim not in `source-facts.md`.
- Deliver the project walkthrough in 90 seconds, then answer the same story in 30 seconds.
- Draw `event`, `participant`, `signup_status`, and `check_in_time`, and narrate one registration-to-check-in transition.
- Practice the code-attribution line three times until it sounds direct rather than defensive.
- Ask a friend to interrupt with “How many?”, “Did you write it?”, and “Was it deployed?”; answer without inventing detail.
