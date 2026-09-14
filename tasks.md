# Fight The Future Consultancy: One-Month Execution Plan

Start: **Wednesday 26 August 2026**

Finish: **Friday 25 September 2026**

Launch-readiness target: **Saturday 26 September 2026**

Target outcome: **Fight The Future is ready to sell, scope and schedule as a University of Liverpool CONSULT service, with the governance route recorded, the standard offer costed, the delivery pack tested, 25 qualified prospects identified, three buyer conversations requested or completed, and one credible pilot opportunity in progress.**

The first paid delivery may happen later because University contracting and client procurement are outside this sprint's control. The two-year commercial target remains eight paid external events and at least £10,000 cumulative personal take-home; a checklist cannot guarantee sales.

Primary commercial plan: [CONSULT/business_plan.md](CONSULT/business_plan.md)

Short summary: [CONSULT/summary.md](CONSULT/summary.md)

## Daily operating rules

- Open this file once each day and ask Codex to complete the **first unchecked dated task**.
- Complete no more than one dated checkbox per calendar day. A task may be continued on the next day if its definition of done has not been met.
- Give the task up to **30 minutes of your attention**. Codex may continue local research, drafting, implementation and testing after that.
- Use the **Daily Master Prompt** below. The dated task already tells Codex which specialist prompt also applies.
- Codex must inspect the relevant existing files before editing and preserve unrelated work.
- Codex changes `[ ]` to `[x]` only when the stated definition of done is met. It then adds a short `Completed:` line containing the date and evidence.
- If the controllable work is complete but an external answer is pending, Codex may mark the dated task complete only after recording the dependency in the **External blocker register**, including owner, submission date and follow-up date.
- Codex must not claim that an email, form, meeting, approval, booking, deployment or purchase occurred without evidence from you or the relevant system.
- Codex may research, draft, edit local files, run local tests and prepare submission-ready material without asking. It must obtain your confirmation before sending messages, submitting forms, changing live services, spending money, publishing prices, contacting prospects or making contractual commitments.
- Do not publish the £5,000 price or approach cold prospects until the institutional route, intellectual-property position and representative costing are credible.
- Do not sign contracts or agree client terms outside the University CONSULT process.
- Do not analyse historic participant submissions, feedback or identifiable logs as research data.
- Do not claim that the event has been proven to improve learning, confidence, collaboration or AI literacy. Use language such as `designed to`, `provides practice in` and `prompts participants to`.
- Use synthetic data for screenshots, demonstrations, rehearsals and client materials.
- Keep one flagship offer. Do not build the wider product suite during this sprint.
- The working standard package remains **£5,000 plus VAT**, travel and accommodation at cost, for up to 40 participants. One tightly controlled founding-partner event may be **£3,500 plus VAT**. Both remain subject to CONSULT approval and costing.
- Do not silently expand bespoke scope. New stories, discipline-specific datasets, client-system integrations and formal evaluations are separately scoped work.
- Do not commit, discard or overwrite unrelated changes. Create a task-specific Git commit only when the dated task explicitly requires one or you ask for it.

## Status notation

- `[ ]` — not complete; this remains in the execution queue.
- `[x]` — definition of done met; evidence must be recorded beneath the task.
- `WAITING` — today's controllable action is complete but an external dependency remains. Record it in the blocker register and continue to the next unchecked task on the next day.
- `BLOCKED` — the task cannot safely progress and no useful local work remains. Codex must record the exact decision or authority needed and leave the box unchecked.

## Daily Master Prompt

Paste this into Codex each day:

```text
Work on the Fight The Future consultancy launch in the current repository.

Read tasks.md, CONSULT/business_plan.md and the files directly relevant to the first
unchecked dated task. Complete that one task now. Also follow the specialist prompt
named by the task. Make safe, in-scope assumptions and do every local action you can
without asking me to choose among equivalent implementation details.

You may inspect, research, draft, edit local files and run non-destructive checks and
tests. Do not send messages, submit forms, change live services, spend money, publish
material, contact people or make contractual commitments without my explicit approval.
Prepare those actions fully, then show me only the precise action or approval needed.

Preserve unrelated work and personal data. Use synthetic examples. Keep claims within
the evidence boundaries in tasks.md. Verify current external facts against authoritative
sources and cite them in the relevant artifact.

Do not mark the task complete merely because a draft or plan exists. Check its stated
definition of done. When it is met, change its checkbox to [x], add a concise Completed
line with date and evidence, update the external blocker register and completion log,
and report:
1. outcome,
2. files created or changed,
3. checks or tests performed,
4. any blocker and its next follow-up date,
5. the single next manual action, only if genuinely required.

Do the task now; do not stop after proposing a plan and do not start the next dated task.
```

## Specialist prompt: governance and external actions

Use when a dated task says **Governance Prompt**:

```text
Prepare the governance or external action completely using the supplied CONSULT
guidance and the current business plan. Distinguish quoted policy, reasonable
interpretation and questions that only an authorised University representative can
answer. Do not present old guidance as current policy.

Produce a concise, send-ready email, form response, agenda or decision record. Include
the standard event scope, honest time assumptions, price status and the exact questions
needed to resolve classification, FEC, net-income treatment, local allocation, payroll,
IP, VAT, hosting, software licensing and use of University resources as relevant.

Do not send or submit it. Show the user the final recipient, subject and attachment list,
then request one explicit approval. After the user confirms submission, record the date,
owner and follow-up date in tasks.md. Never fabricate approval or infer it from silence.
```

## Specialist prompt: commercial asset

Use when a dated task says **Commercial Asset Prompt**:

```text
Create the named commercial asset for a UK doctoral-training or researcher-development
buyer. Lead with the buyer's programme need, the participant experience and the practical
value of verification and cohort interaction. Keep the product bounded and repeatable.

Use plain, credible language. Say the event is designed to provide practice; do not claim
measured learning impact. Preserve the £5,000 plus VAT working price, travel at cost,
up-to-40 capacity, standard exclusions and founding-partner guardrails unless written
CONSULT evidence requires a change.

Cross-check every factual statement against the repository or a cited authoritative
source. Reuse approved wording across assets, remove internal deliberation from client
copy, use accessible Markdown structure and finish with a client-ready artifact rather
than an outline.
```

## Specialist prompt: product and technical work

Use when a dated task says **Product Prompt**:

```text
Implement the named product-readiness task in the current Django repository.

Inspect the existing application, tests, deployment configuration, contingency generator
and documentation before editing. Preserve existing participant progress, routes, stage
codes, narrative identity and personal/group validation behaviour. Use synthetic test
data and never expose historic participant information.

Prefer the smallest safe change that makes the standard event more reliable, accessible
or repeatable. Add or update focused tests for changed behaviour. Run the focused suites,
Django system checks and migration consistency checks. Review the diff for secrets,
hard-coded production credentials, unrelated changes and generated artifacts.

Do not deploy or mutate a live event. Do not hide failures. Finish with working code or a
verified operational artifact, test evidence and any remaining manual live-environment
check. Do not commit unless the dated task or user requests it.
```

## Specialist prompt: prospecting and discovery

Use when a dated task says **Market Prompt**:

```text
Complete the named market-validation task for Fight The Future.

Research only relevant institutional buyers: UK CDTs, doctoral focal awards, Doctoral
Training Partnerships, doctoral colleges, researcher-development teams, research
institutes and closely related programmes. Prioritise mixed-discipline or data-rich
cohorts over pure computer-science cohorts. Use current official programme or university
pages and publicly listed professional contact routes. Do not collect private contact
details and do not contact students.

For every prospect record organisation, programme, official URL, buyer role, named
professional contact when publicly listed, public contact route, cohort/fit evidence,
warm route, status, last action, next action and source. Do not invent names, budgets,
emails, demand or relationships. Deduplicate by programme and organisation.

Draft tailored approaches when requested, but do not send them. Do not describe interest
as validation unless a buyer supplies a concrete next step involving date, budget,
procurement or proposal. Keep objections verbatim and separate evidence from inference.
```

## Specialist prompt: rehearsal and launch audit

Use when a dated task says **Rehearsal Prompt**:

```text
Prepare or run the named rehearsal/readiness task using synthetic participants.

Exercise the complete client and participant journey: preflight, joining, orientation,
agent-access fallback, four stages, personal checking, collaboration, podium matching,
facilitator interventions, completion, debrief and recovery. Simulate low attendance,
uneven pacing, inaccessible public partner-finding, account failure, loss of connectivity,
pause/resume, stranded participants and offline contingency operation.

Record expected result, actual result, severity, evidence, owner and retest status. Fix
launch-critical local defects within scope and retest them. Put enhancements that are not
required for safe sale into a later backlog. Do not report a rehearsal with real people as
completed unless the user confirms attendance and execution.
```

## Fixed offer and decision gates

- Product: `Fight The Future — agent-supported collaborative coding mission`
- Buyer: UK CDT, doctoral programme or researcher-development team
- Format: approximately two hours, normally embedded in a half-day client package
- Standard capacity: up to 40 participants with one lead facilitator, subject to dry-run and risk-assessment evidence
- Standard working fee: £5,000 plus VAT
- Founding-partner working fee: £3,500 plus VAT for one minimally customised evidence-building delivery
- Travel and accommodation: charged separately at cost
- Standard customisation: cohort name, agreed welcome text, run configuration and debrief emphasis
- Separate scope: new narrative, discipline-specific datasets, client-system integration, extra facilitator, formal evaluation, delivery outside the UK
- Financial gate: standard-event confirmed FEC and direct costs at or below £2,250, or a revised price/inclusion model approved before sale
- Governance gate: written authority for institutional route, IP use and personal payroll allocation in principle
- Product gate: complete runbook, accessible participation route, recovery plan, technical-readiness pack and successful rehearsal
- Market gate: at least one qualified buyer willing to discuss a date, budget, procurement route or written proposal

## External blocker register

Codex maintains this table whenever a task becomes `WAITING` or `BLOCKED`.

| Dependency | Owner | Submitted | Follow up | Status/evidence |
| --- | --- | --- | --- | --- |
| None recorded yet | — | — | — | — |

## Completion log

Codex adds one row whenever it marks a dated task complete.

| Date completed | Task date | Evidence | Next dependency |
| --- | --- | --- | --- |
| 2026-08-26 | 2026-08-26 | `CONSULT/business_plan.md`, `CONSULT/summary.md` and this execution tracker created | Begin governance submission pack |

## Dated checklist

### Week 1 — authority and commercial foundations

- [x] **2026-08-26 — Establish the commercial plan and daily execution tracker.** Inspect the supplied CONSULT materials, repository and existing event design; define the institutional route, flagship offer, working price, two-year income objective, one-month launch target, decision gates and daily operating method. Create a detailed plan and a self-updating task tracker that lets Codex execute one bounded task per day without losing evidence or overstepping external approval boundaries. **Done when:** `CONSULT/business_plan.md`, `CONSULT/summary.md` and `tasks.md` exist, agree on the main assumptions, and identify current guidance and external confirmation as separate things.

  Completed: **2026-08-26** — created the business plan, concise summary and this 31-day execution system; preserved CONSULT confirmation, IP and FEC as explicit gates.

- [ ] **2026-08-27 — Build the CONSULT governance submission pack.** Use the **Governance Prompt**. Create `CONSULT/launch/governance_request.md` containing: a one-page description of the standard event; buyer, duration and capacity; included and excluded work; an honest activity/time breakdown for preparation, administration, delivery, travel and follow-up; the £5,000 plus VAT price marked as provisional; the £3,500 founding-partner condition; intended use of the hosted app and University identity; and numbered questions covering classification as consultancy/CPD, representative FEC/non-FEC costing, net income, local allocation, personal payroll approval, IP, VAT, insurance, hosting/licences and authority to market. Add separate send-ready emails for the line manager/approver and CONSULT, with recipients left as explicit placeholders if unknown. **Done when:** the pack is complete enough to send without further substantive drafting, every assumption can be traced to the plan or supplied guidance, and the only remaining action is entering recipient details and approving submission.

- [ ] **2026-08-28 — Submit the authority and costing requests.** Use the **Governance Prompt**. Recheck yesterday's pack for accuracy, fill the real recipient details supplied by the user, prepare the final attachment list, and show the exact outgoing messages for approval. The user sends the line-manager/approver request and the CONSULT classification/costing request through the appropriate University channel. Record submission evidence, responsible owners and follow-up dates in the blocker register; never store sensitive correspondence unnecessarily. **Done when:** both requests have actually been submitted or the correct University submission route has been used, and outstanding answers are recorded as `WAITING`. A fully submitted request counts as completion even though the external decisions remain pending.

- [ ] **2026-08-29 — Create the intellectual-property and asset-use inventory.** Use the **Governance Prompt**. Inspect the repository and produce `CONSULT/launch/ip_asset_register.md` listing the Fight The Future name and visual identity, Django application, stage logic, narrative, datasets and generators, contingency tools, participant/facilitator materials, prior internal delivery, University resources used, third-party software/services, authors/contributors where known, and unresolved ownership/licensing questions. Distinguish source-code ownership, brand use, hosted access, client retention, reusable adaptations and future bespoke work. Do not make a legal conclusion. **Done when:** every material asset category has an evidence/source field, likely rights holder or `UNKNOWN`, intended consultancy use, client-use boundary and exact question requiring written confirmation.

- [ ] **2026-08-30 — Build the representative event costing model.** Use the **Governance Prompt**. Create `CONSULT/launch/costing_model.md` and a machine-readable `CONSULT/launch/costing_model.csv`. Model discovery, configuration, administration, technical readiness, standard preparation, rehearsal, delivery, follow-up, sponsor report, maintenance allocation, travel time, direct platform cost, extra facilitator and contingency. Show founding, standard and higher-FEC cases; calculate revenue excluding VAT, FEC/direct cost, payroll fund and estimated take-home using the planning assumptions in the business plan. Clearly flag formulas and assumptions awaiting CONSULT confirmation. **Done when:** changing price or confirmed cost produces an auditable result, hidden unpaid labour is visible, the £2,250 gate can be tested, and no planning figure is presented as approved tax or University advice.

- [ ] **2026-08-31 — Freeze the standard package and customisation boundary.** Use the **Commercial Asset Prompt**. Create `CONSULT/launch/offer_specification.md` as the internal source of truth for the flagship: client journey, participant experience, duration, capacity, inclusions, exclusions, standard configuration, separately priced changes, accessibility responsibilities, technical prerequisites, evaluation boundary, deliverables, travel treatment, cancellation/rescheduling questions for CONSULT, evidence limitations and a clear `not offered` list. Reconcile contradictions with the business plan rather than duplicating them. **Done when:** a future proposal can be checked line-by-line against this file and a bespoke request can be classified as included, chargeable or declined without inventing policy.

- [ ] **2026-09-01 — Set workload capacity, delivery calendar and risk controls.** Use the **Governance Prompt**. Create `CONSULT/launch/capacity_and_risks.md` containing realistic founder hours for one standard event, protected University-role boundaries, maximum event volume, lead times, travel constraints, 41–60 participant second-facilitator rule, decline conditions and a risk register with likelihood, impact, early warning, control, owner and review date. Include financial, IP, technical, accessibility, attendance, procurement, evidence-claim, scope-creep and core-employment risks. **Done when:** the eight-event plan fits a visible capacity model, each principal risk has a preventive control and contingency, and any line-manager decision is listed in the blocker register.

- [ ] **2026-09-02 — Run the week-one governance checkpoint.** Use the **Governance Prompt**. Review every response received, update `governance_request.md`, the IP register, costing model, offer specification and blocker register with dated evidence, and send or prepare concise follow-ups for missing answers. Create `CONSULT/launch/governance_decision.md` with red/amber/green status for institutional route, classification, FEC, net income, local allocation, payroll, IP, VAT, insurance, hosting/licences and marketing authority. Do not turn silence into approval. **Done when:** every decision has evidence, owner and next date; any due follow-up has actually been sent with approval; and the file states whether price may be published, warm discovery may begin, and a proposal may enter CONSULT.

### Week 2 — productise the delivery

- [ ] **2026-09-03 — Write the standard delivery runbook.** Use the **Commercial Asset Prompt**. Create `CONSULT/delivery/runbook.md` covering four-to-six-weeks-before, two-weeks-before, two-days-before, room setup, participant arrival, orientation, mission briefing, each stage, collaboration transitions, breaks, interventions, debrief, shutdown and five-day follow-up. Give each live segment a target time, facilitator cue, participant state, dashboard action, failure signal, recovery decision and artifact required. Distinguish client, facilitator, venue IT and participant responsibilities. **Done when:** a trained colleague unfamiliar with the code can understand how to prepare and co-facilitate the standard event, and all unresolved decisions are labelled rather than improvised.

- [ ] **2026-09-04 — Create the technical-readiness and participant preflight pack.** Use the **Commercial Asset Prompt**. Create `CONSULT/delivery/technical_readiness.md` for the client's IT/operations team and `CONSULT/delivery/participant_preflight.md` for attendees. Cover supported devices, operating systems, browsers, VS Code, Python/R/JavaScript choices, GitHub Copilot or agreed alternative access, accounts, extensions, downloads, network/firewall needs, room display, power, accessibility, test script, data policy, support contact and an account-free fallback. Keep instructions accessible and platform-specific only where necessary. **Done when:** client readiness can be confirmed with a checklist, a participant can prove the basic edit-run workflow before arrival, and failure of agent access does not automatically exclude participation.

- [ ] **2026-09-05 — Design the accessible collaboration route.** Use the **Commercial Asset Prompt**. Create `CONSULT/delivery/accessibility_and_inclusion.md` covering advance disclosure, adjustment discovery, structured roles, stable-team option, facilitator-mediated matching, text-based or seated partner finding, non-public contribution, keyboard use, contrast, reduced motion, screen-reader considerations, breaks, sound, room movement, account access, anxiety and escalation. Add exact facilitator scripts and a mapping from barrier to alternative route while preserving personal contribution and group progression. **Done when:** public movement or confidence is no longer a hidden prerequisite on paper, responsibilities between client and facilitator are explicit, and technical items needing implementation are placed in a bounded backlog.

- [ ] **2026-09-06 — Establish the technical baseline and remove launch-critical configuration risk.** Use the **Product Prompt**. Run the existing Django tests, system checks, migration consistency checks and contingency-generator smoke test; inspect `config/settings.py`, `.env.example`, `render.yaml`, authentication, teacher controls, logging, allowed hosts, secret handling, static assets, persistence and recovery assumptions. Fix only launch-critical local defects supported by tests, especially unsafe production defaults or credential exposure. Create `CONSULT/delivery/technical_baseline.md` with commands, results, environment variables, known limitations and live checks still requiring explicit approval. **Done when:** local checks pass or every pre-existing failure is documented with severity; no real secret is introduced; synthetic player flows still work; and deployment mutation remains a separate approved action.

- [ ] **2026-09-07 — Verify contingency, reset and recovery operations.** Use the **Product Prompt**. Exercise contingency-pack generation for synthetic cohorts representing low attendance, a standard cohort and maximum standard capacity; verify instructions, answer sheet, deterministic solutions and safe filenames. Document hosted outage, loss of connectivity, agent-account failure, late arrival, absent participant, uneven stage distribution, facilitator lockout, pause/resume, mistaken suspension and reset recovery in `CONSULT/delivery/recovery_playbook.md`. Add tests or scripts where repeatable verification is missing. **Done when:** each named failure has detection, immediate action, data consequence, participant communication, recovery/abort threshold and retest evidence, and the generated packs contain no historic participant identity.

- [ ] **2026-09-08 — Produce the buyer proposition and sample agenda.** Use the **Commercial Asset Prompt**. Create `CONSULT/sales/one_page_proposition.md` and `CONSULT/sales/sample_agenda.md`. The proposition must state the buyer problem, who the event is for, what participants actually do, the personal-checker/collective-podium distinction, intended learning actions, cohort value, format, prerequisites, included deliverables, evidence limitations, working commercial route and one clear call to action. The agenda must fit the promised package and include setup, mission, debrief and contingency time. **Done when:** both assets are concise, consistent with the offer specification and ready for design/export after governance approval; internal financial calculations and unsupported claims are absent.

- [ ] **2026-09-09 — Complete the proposal and sponsor-report toolkit.** Use the **Commercial Asset Prompt**. Create `CONSULT/sales/proposal_template.md`, `CONSULT/sales/sponsor_report_template.md`, `CONSULT/sales/facilitator_profile.md` and `CONSULT/sales/evidence_safe_case.md`. The proposal must include objectives, scope, client responsibilities, accessibility/technical discovery, price placeholder controlled by the governance gate, exclusions, assumptions, University contracting route and validity. The sponsor report must separate attendance/system operation, participant reaction, incidents and recommendations from evidence of learning. **Done when:** a qualified opportunity can be turned into a truthful first proposal without rewriting the core offer, and all placeholders are explicit and searchable.

### Week 3 — validate the market

- [ ] **2026-09-10 — Create the prospect pipeline and qualification rules.** Use the **Market Prompt**. Create `CONSULT/sales/prospects.csv`, `CONSULT/sales/pipeline.md` and `CONSULT/sales/discovery_guide.md`. Define qualification, disqualification and evidence standards; required pipeline fields; stages from `RESEARCHED` through `BOOKED`, `DECLINED` or `DORMANT`; discovery questions; next-action discipline; privacy boundaries; and rules for warm introductions versus cold professional approaches. **Done when:** the empty pipeline structure validates cleanly, discovery can be conducted without giving away bespoke design work, and a prospect cannot be labelled interested or qualified without sourced evidence.

- [ ] **2026-09-11 — Research the first ten qualified prospects.** Use the **Market Prompt**. Add prospects 1–10, beginning with Liverpool-linked external CDTs, focal awards, Doctoral Training Partnerships and doctoral-development programmes. Use current official sources; record the programme need/fit, professional buyer role, named public contact where available, warm route and next action. Do not send anything. **Done when:** ten non-duplicate rows meet the qualification rules, every material field has a source or `UNKNOWN`, and at least three have a plausible warm route.

- [ ] **2026-09-12 — Complete the 25-account prospect list.** Use the **Market Prompt**. Research and add prospects 11–25 across data-rich bioscience, health, environment, chemistry, engineering and materials programmes plus cross-faculty researcher-development teams. Balance fit and reachability rather than padding the list. Quality-check all 25 for current programme status, duplicates, buyer relevance, public contact provenance and a concrete next action. **Done when:** exactly 25 qualified, sourced accounts exist; pure-computing or irrelevant entries are excluded or justified; and the pipeline summary reports segment, warm-route and contact-readiness counts.

- [ ] **2026-09-13 — Prepare and request the first five introductions or conversations.** Use the **Market Prompt**. Select the five strongest warm or near-warm prospects. Draft a tailored message for each that refers to a real programme feature, uses the approved proposition, asks for a 20-minute discovery conversation and does not imply approval, proven impact or a fixed public price before the governance gate. Show all five messages and recipients for user approval; the user sends them. **Done when:** five valid requests have actually been sent, each pipeline row records date/status/follow-up, or the user's controllable work is recorded as `WAITING` after the approved introduction request went to the warm intermediary.

- [ ] **2026-09-14 — Prepare and request five more buyer conversations.** Use the **Market Prompt**. Process replies first, then select prospects 6–10 using evidence of fit and route. Draft and, after explicit approval, send five tailored professional approaches or warm-introduction requests. Do not bulk-send identical copy. Record replies verbatim enough to preserve meaning, without unnecessary personal data, and set a dated next action. **Done when:** ten cumulative valid approaches/requests have been made, all responses and opt-outs are respected, and no row is left without a next action.

- [ ] **2026-09-15 — Prepare and conduct discovery conversations.** Use the **Market Prompt**. Review scheduled conversations, create a one-page brief for each, and help the user run any calls occurring today. Capture only professional notes: current provision, problem, cohort, timing, technical environment, accessibility/policy constraints, success condition, budget owner, procurement route, repeat potential and agreed next step. If fewer than three calls are scheduled, prepare concise follow-ups and offer specific time windows with approval. **Done when:** all conversations held to date have structured notes and follow-ups, and at least three buyers have either completed a conversation or accepted/suggested a concrete scheduling step; outstanding meetings are recorded as `WAITING`, not falsely completed.

- [ ] **2026-09-16 — Synthesize market evidence and identify the pilot opportunity.** Use the **Market Prompt**. Create `CONSULT/sales/market_validation.md` summarising sourced patterns across conversations and written replies: problem intensity, preferred format, price reaction, cohort size, timing, procurement, technical/accessibility concerns, objections and requested changes. Keep direct buyer evidence separate from inference. Score opportunities against fit, authority, need, timing, route, repeat potential and bespoke burden. Select one founding-partner candidate only if evidence supports it and draft the next-step message or proposal brief for approval. **Done when:** one opportunity has a credible date/budget/procurement/proposal next step or the document honestly states that the market gate is not yet met and specifies the next five validation actions.

### Week 4 — prove readiness

- [ ] **2026-09-17 — Recruit and schedule the full rehearsal.** Use the **Rehearsal Prompt**. Protect a rehearsal slot before 24 September and prepare a concise invitation for 8–16 representative adult testers with varied coding confidence. State duration, technical prerequisites, collaboration requirement, accessibility contact, synthetic-data use and what feedback will be collected. After user approval, send invitations through appropriate professional/personal routes and create `CONSULT/rehearsal/attendance_plan.md` with confirmations, roles, equipment, room/online setup and a fallback if fewer than eight attend. **Done when:** a dated rehearsal is genuinely scheduled, invitations are sent, and the attendance/collaboration plan remains viable at 4, 8 and 16 testers.

- [ ] **2026-09-18 — Build the rehearsal protocol and evidence pack.** Use the **Rehearsal Prompt**. Create `CONSULT/rehearsal/protocol.md`, `CONSULT/rehearsal/issue_log.csv` and `CONSULT/rehearsal/facilitator_checklist.md`. Define test scenarios, timings, synthetic users, group thresholds, observation boundaries, non-identifiable operational measures, participant reaction questions, accessibility checks, stop conditions, severity definitions and evidence capture. Include simulations for agent failure, connection loss, low attendance, uneven progress and a stranded participant. **Done when:** another facilitator could execute and record the rehearsal consistently, real participant research is not smuggled into operational testing, and every launch gate maps to at least one check.

- [ ] **2026-09-19 — Run a solo technical dress rehearsal.** Use the **Rehearsal Prompt** and **Product Prompt**. On a clean local/test environment, generate a fresh synthetic run and execute the complete journey using enough test users to exercise group sizes 1, 2, 4 and 8; verify downloads, Python and R reference solutions, checker behaviour, podium matching, ambiguity handling, collaboration cap, stranded fallback, suspension, pause/resume, completion, feedback boundary and contingency answer sheet. Record timings and defects. Fix and retest launch-critical local failures only. **Done when:** the end-to-end synthetic flow has reproducible evidence, every critical/high defect is fixed or explicitly blocks launch, and the repository test suite and system checks pass after changes.

- [ ] **2026-09-20 — Perform the accessibility and client-document review.** Use the **Rehearsal Prompt**. Audit the participant flow and delivery documents against the accessibility routes defined on 5 September. Check keyboard navigation, focus visibility, headings/labels, colour contrast, reduced motion, zoom/reflow, screen-reader announcements where testable, plain-language instructions, non-public matching, seated participation and account-free fallback. Repair bounded high-impact issues and create `CONSULT/delivery/accessibility_review.md` with method, result, limitations, owner and retest. **Done when:** no known critical barrier is hidden, automated checks are not represented as proof of accessibility, and remaining needs form explicit client-discovery questions or launch blockers.

- [ ] **2026-09-21 — Conduct the full timed group rehearsal.** Use the **Rehearsal Prompt**. Run the scheduled rehearsal with confirmed testers and the facilitator checklist. The user controls the real-world session; Codex prepares materials and may analyse only the agreed non-identifiable operational record. Time orientation and stages; exercise collaboration and at least one controlled failure; capture system incidents, overrides, accessibility issues and debrief reactions without claiming learning outcomes. **Done when:** the user confirms the rehearsal occurred, actual attendance and timings are recorded, every issue has severity/owner/retest status, and the dry-run gate is marked pass, conditional pass or fail with reasons. If attendance fails, run the documented smaller-cohort rehearsal and reschedule only if the evidence gap is material.

- [ ] **2026-09-22 — Triage rehearsal findings and repair launch-critical defects.** Use the **Rehearsal Prompt** and **Product Prompt**. Review the issue log; classify defects as launch blocker, must-fix, later improvement or observation. Repair all safe in-scope blocker/must-fix code and documentation issues, add regression tests, rerun affected scenarios and update the log. Create `CONSULT/rehearsal/rehearsal_report.md` summarising actual conditions, evidence, deviations and readiness without promotional spin. **Done when:** every blocker is closed with retest evidence or remains explicitly blocking; no critical defect is relabelled to force launch; and optional enhancements are parked outside the sprint.

- [ ] **2026-09-23 — Finalise the risk assessment and delivery checklist.** Use the **Rehearsal Prompt**. Update the capacity/risk register from rehearsal evidence and create `CONSULT/delivery/event_checklist.md` covering contract handoff, client discovery, accessibility, IT, participant communication, run creation, backup, offline packs, room setup, live decisions, incident handling, data handling, close-down, sponsor report, invoice/payment confirmation and payroll timing. Add go/no-go thresholds and named owners. **Done when:** each rehearsal lesson either changes a control or is explicitly accepted with rationale, and one checklist governs preparation rather than scattered notes.

- [ ] **2026-09-24 — Assemble the client-ready sales and delivery pack.** Use the **Commercial Asset Prompt**. Reconcile the proposition, agenda, offer specification, proposal, facilitator profile, evidence-safe case, technical-readiness sheet, participant preflight, accessibility route and sponsor report. Create `CONSULT/launch/client_pack_index.md` naming the authoritative version, audience, status and export need of every asset. Remove contradictory prices, capacities, claims and responsibilities. Produce a proposal brief for the leading pilot only if the market and governance gates permit it; otherwise label it `DRAFT — NOT FOR ISSUE`. **Done when:** every client-facing asset has one owner/version/status, passes a claims and accessibility review, and the pack can support a real CONSULT proposal without hidden bespoke work.

- [ ] **2026-09-25 — Run the launch-readiness audit and close the sprint.** Use the **Rehearsal Prompt** and **Governance Prompt**. Create `CONSULT/launch/readiness_report.md` with red/amber/green evidence for governance, IP, cost, payroll, price, product, accessibility, technical reliability, rehearsal, sales assets, 25-account pipeline, ten approaches, three buyer conversations and pilot opportunity. Reconcile the blocker register and state exactly what may be sold, published, proposed or scheduled. Add a 30/60/90-day execution section tied to first proposal, first booking, three paid events and validated repeat-delivery cost. **Done when:** every gate has evidence and owner; the consultancy is honestly labelled `READY`, `CONDITIONALLY READY` or `NOT READY`; no outstanding approval is assumed; and the single next commercial action is recorded.

## If energy or confidence is low

Paste this into Codex:

```text
I am resuming the first unchecked task in tasks.md and have ten minutes of attention.
Perform every safe repository action you can. Break the remaining user-only portion into
individual actions and show me only the next one. Do not discuss broad strategy, add
features or ask me to choose among equivalent approaches. Do not mark the task complete
until its definition of done is met; record partial progress beneath it so tomorrow starts
from evidence rather than from scratch.
```

Doing the one action shown counts as maintaining the daily habit. Continue the same checkbox tomorrow if necessary.

## If a task fails

Paste this into Codex with the error or evidence:

```text
Diagnose this within the current dated task. Implement the safest in-scope fix, test or
verify it, update the task evidence and tell me exactly what remains. Preserve unrelated
work and do not weaken a launch gate merely to mark the checkbox complete.
```

## After launch readiness

Do not extend this dated checklist during the sprint. On 25 September, use the readiness report to create the next bounded plan. Expected milestones are:

- **31 October 2026:** first qualified proposal;
- **31 January 2027:** first external booking or delivery;
- **31 August 2027:** three paid events and year-one cost evidence;
- **28 February 2028:** at least one repeat/referral and demonstrated repeatability;
- **31 August 2028:** eight paid events and at least £10,000 cumulative personal take-home, subject to actual CONSULT cost and payroll treatment.
