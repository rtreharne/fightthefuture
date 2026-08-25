# Fight The Future: Journal Article Plan

## Writing and compiling

The editable LaTeX source is [paper.tex](paper.tex). Open the `writing` folder
in VS Code, save the file, and LaTeX Workshop will compile it and show the PDF
in a VS Code tab. The same document can be built from a terminal with:

```sh
./.latex/bin/latexmk -pdf paper.tex
```

Build files and the generated PDF are ignored by Git.

## Working title

**Fight The Future: A design case for collaborative, agentic-AI-supported coding in higher education**

## Intended publication

- **Journal:** *Journal of Learning Development in Higher Education* (JLDHE)
- **Format:** Case Study
- **Maximum length:** 5,000 words, including title, abstract, keywords and references
- **Approach:** A scholarly design case and critical practitioner reflection, not an empirical evaluation

## Purpose

The article will describe the design and implementation of **Fight The Future**, a live, narrative-driven coding event for University of Liverpool students and staff. It will examine how a short, completable and necessarily collaborative experience can introduce novice participants to Python, VS Code and agent-based AI while preserving human reasoning, verification and accountability.

The article should contribute transferable design principles rather than simply documenting the software.

## Central argument

Agent-based AI is changing programming from an activity centred on manually producing code to one increasingly concerned with specifying problems, directing agents, evaluating outputs, debugging and retaining accountability. Universities therefore need to teach students how to work critically and effectively with coding agents.

However, merely providing access to an AI agent does not guarantee meaningful learning. Fight The Future uses individualised data, deterministic validation, time pressure, narrative progression and engineered interdependence to require participants to reason, verify and collaborate.

## Key design principles

### 1. Bounded immersion

The complete event must last less than two hours. The narrative should generate urgency and investment without demanding an open-ended commitment. This requires minimal onboarding, short stages, reliable infrastructure and facilitator control over timing.

### 2. Designed finishability

Participants should be capable of completing the scenario within the available time. Completion is part of the narrative and learning contract, not an accidental outcome. Difficulty, hints, recovery routes, task length and facilitator interventions must therefore be deliberately calibrated.

### 3. Engineered interdependence

Collaboration must be structurally necessary rather than merely encouraged. Participants receive distinct data or outputs and must combine information to progress. This creates genuine dependency while retaining individual responsibility.

### 4. Human accountability

Participants may use coding agents, but remain responsible for defining the problem, checking the generated code, interpreting results and submitting the correct solution. Fast code generation increases the importance of judgement and verification.

## Reflective themes

### Recruitment and attendance

The event exposed a substantial difference between registration and attendance. As a practical planning assumption, filling a room with approximately 50 participants may require around 100 registrations. The paper must present this as a contextual practitioner observation, not as a universal post-COVID rule. Relevant literature should be used before attributing the pattern to post-COVID changes in engagement.

### Participant attitudes to collaboration

Most participants appeared to understand and accept the collaborative premise. A minority remained seriously reluctant to collaborate even though collaboration had been advertised as a requirement.

The reflection should consider possible explanations without presenting them as research findings:

- preference for individual control;
- assessment-conditioned individualism;
- social anxiety or lack of psychological safety;
- reluctance to expose incomplete work;
- concern about unequal ability or contribution;
- an assumption that coding is intrinsically solitary.

The article should also acknowledge that forced collaboration can create accessibility and inclusion concerns. Future iterations should clarify roles, establish psychological safety and support reluctant participants without removing genuine interdependence.

### Why teach agent-based AI?

Students increasingly need to learn how to:

- specify and decompose problems;
- provide agents with appropriate context;
- inspect generated files and outputs;
- test, verify and debug agent-produced code;
- recognise plausible but incorrect solutions;
- iterate effectively;
- coordinate human and artificial contributors;
- remain accountable for work they did not type manually.

There is also an equity argument: leaving students to acquire these practices informally advantages those who already have technical experience, paid tools or access to knowledgeable communities.

Avoid the unsupported generalisation that “90% of Silicon Valley code is written by AI.” A defensible example is Y Combinator's report that one quarter of its Winter 2025 companies had codebases that were 95% AI-generated. The article should distinguish industry claims, forecasts and independently established evidence.

### Why is higher education behind the curve?

Frame this as a sector-wide tension rather than an unsupported criticism of a named institution. Possible contributors include:

- academic-integrity concerns;
- procurement, privacy and governance requirements;
- rapidly changing tools;
- uneven staff confidence;
- curricula based on manual code production;
- assessment models that equate authorship with typing;
- difficulty distinguishing supported learning from cognitive outsourcing.

The reflective position is that institutional caution is understandable, but avoiding agent-based AI risks preparing students for a professional reality that is already changing.

## Proposed article structure

1. **Introduction: coding education after the arrival of agents**  
   Establish the professional and educational problem, the article's argument and its contribution to Learning Development.

2. **Context and rationale**  
   Introduce the audience, live-event setting, novice-accessible intention and learning objectives.

3. **Fight The Future**  
   Briefly explain the AUGUR narrative, staged missions, individualised datasets, deterministic codes, scoring, teacher podium and collaboration mechanics.

4. **Design requirements and principles**  
   Develop bounded immersion, designed finishability, engineered interdependence and human accountability.

5. **Implementation of the live event**  
   Describe recruitment, intended capacity, duration, delivery sequence, facilitation and the practical use of Python, VS Code and coding agents.

6. **Critical practitioner reflection**  
   Discuss attendance, pacing, completion, facilitator intervention, participant resistance to collaboration, surprises and intended redesigns.

7. **Why universities must teach agent-based development**  
   Connect the case to changing professional practice, AI literacy, verification, accountability and equitable access.

8. **Transferable recommendations**  
   Present concise guidance for educators wishing to run similar short collaborative events.

9. **Limitations and future evaluation**  
   State clearly that no formal participant study was conducted. Outline an ethically approved future evaluation involving participant experience, collaboration, confidence, agent use and learning.

10. **Conclusion**  
    Restate the value of deliberately orchestrated, short and completable agentic-AI learning experiences.

## Evidence boundaries

The article may use:

- system documentation and architecture;
- activity designs and generated materials;
- event timings and non-identifiable operational facts;
- screenshots and interface examples where appropriate;
- the author's clearly labelled practitioner observations and reflections;
- published literature and properly attributed industry evidence.

Without appropriate ethical approval, the article should not retrospectively analyse identifiable participant data, submissions or feedback as research. It must not claim that the event improved learning, confidence, engagement or collaboration.

Use language such as **“was designed to,” “I observed,” “the case suggests”** and **“future evaluation will examine.”** Avoid presenting informal impressions as findings.

## Literature areas to review

- Agentic AI and AI-assisted software development
- AI literacy in higher education
- Novice programming and cognitive outsourcing
- Human oversight, verification and accountability
- Game-based and narrative learning
- Collaborative problem-solving and social interdependence
- Productive failure, scaffolding and task calibration
- Post-COVID participation in voluntary university activities
- Psychological safety, accessibility and resistance to group work

## Immediate writing tasks

- [ ] Write a 150-word structured abstract.
- [ ] Formulate the central problem and contribution in one paragraph.
- [ ] Record an accurate factual timeline of the May 2026 event.
- [ ] Separate documented operational facts from personal recollections.
- [ ] Write a candid first-person event reflection while memories remain available.
- [ ] Identify which screenshots or diagrams genuinely explain the design.
- [ ] Locate scholarly sources for each literature area.
- [ ] Verify all statistics concerning professional adoption of coding agents.
- [ ] Draft the four design principles as the article's principal contribution.
- [ ] Develop an ethics-approved evaluation plan for a future delivery.

## Candidate future research questions

1. How do novice participants use coding agents during a short, scenario-based programming event?
2. How does engineered interdependence affect participants' willingness to collaborate?
3. Which forms of facilitation help participants verify rather than uncritically accept agent-generated code?
4. How do participants understand authorship and accountability when an agent produces much of the code?
5. Which design features predict successful completion within a two-hour event?

## Success criterion for the article

The reader should finish with a clear explanation of why Fight The Future was designed as it was, an honest account of the tensions encountered during delivery, and a set of principles they could apply to their own agentic-AI learning activity.
