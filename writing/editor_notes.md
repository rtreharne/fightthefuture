# IJDL editorial notes on *Fight The Future*

## Provisional editorial decision

- **Recommendation: return to authors before peer review, with encouragement to submit a substantially redesigned manuscript.** The project is strongly aligned with the *International Journal of Designs for Learning* (IJDL), but the present article is not yet written as an IJDL design case.

- **The intervention itself is suitable.** IJDL publishes descriptions of artifacts, environments, and experiences created to support learning. A narrative coding event built around personalised datasets, coding agents, staged collaboration, a shared podium, and facilitator controls is exactly the kind of designed learning experience that can provide useful precedent for other designers.

- **The current manuscript points in the wrong direction.** It devotes too much space to arguing what universities should teach, proposing transferable principles, and outlining a future effectiveness study. IJDL does not require a design case to prove effectiveness. It does require a rich, transparent account of how the design came to be, which decisions shaped it, what constraints mattered, and where the design failed or changed.

- **A publishable IJDL case is present but largely unwritten.** The implemented system contains considerably more design knowledge than the manuscript reveals. The paper needs to move that knowledge into the foreground.

## Fit with IJDL

- **The manuscript falls within IJDL's scope.** IJDL accepts design cases from every field and permits evidence of effectiveness where it serves the case, but such evidence should not displace the descriptive account of how the intervention was created. See the current [IJDL author guidelines](https://scholarworks.iu.edu/journals/index.php/ijdl/about/submissions).

- **The most valuable contribution is design precedent.** Readers should be able to experience the design vicariously and understand enough of its form, context, constraints, and development to inform their own judgement. They do not need to be persuaded that the four principles are universally correct.

- **The event contains several potentially strong precedents.** These include deterministic personalised datasets, stage-specific code generation, a checker separated from progression, group validation through summed codes, collaboration sizes that escalate across stages, facilitator overrides, and an offline contingency generator.

- **The manuscript should identify one principal design contribution.** The strongest candidate is the podium mechanism that turns a private computational output into a stage-aligned group contribution. The narrative, finishability measures, and facilitator controls can then be analysed as supporting design decisions rather than competing headline contributions.

- **The present title is too argumentative and too broad.** A more suitable title would be *Designing Fight The Future: A Narrative, Agent-Supported Collaborative Coding Event*. This names the designed experience without claiming a general solution for higher education.

## Fundamental revision required

- **Replace the current argumentative spine with a design narrative.** The manuscript should answer: What problem prompted the design? What alternatives were considered? Why were personalised datasets chosen? Why did collaboration increase from one to two, four, and eight? Why was validation separated between a personal checker and a public podium? Which decisions changed during development, testing, and delivery?

- **Provide a design chronology.** The reader currently encounters a finished system with little sense of how it emerged. Describe the original brief, early prototypes, abandoned ideas, technical discoveries, rehearsal or testing, final delivery, and post-event redesign decisions.

- **Make the authors' relationship to the design explicit.** IJDL asks authors to explain their role in the project. State who conceived the event, who designed the learning sequence, who built the software, who wrote the narrative and datasets, who facilitated the session, and how those perspectives shape the account.

- **Describe the actual design context.** Include the event date, location or delivery mode, intended audience, advertised prerequisites, registration and attendance figures, available time, room configuration, device conditions, facilitator numbers, and institutional constraints where disclosure is permissible.

- **Distinguish three layers that are currently blended together.** The learning design is the staged participant experience. The technical implementation is the Django application and its validation logic. The live orchestration is the facilitator's management of timing, grouping, and exceptions. Each layer should be described, then their dependencies should be made visible.

## Design decisions that need analysis

- **Personalised data requires a design rationale.** Explain why participants could not all solve the same dataset. Discuss how individualisation affected answer sharing, validation, technical complexity, contingency planning, and the need for each participant to contribute.

- **The checker and podium separation is promising but underexplained.** The checker confirms an individual output, while the podium controls collective progression. Explain why one interface did not perform both functions and what behaviour the separation was intended to produce.

- **The summed-code mechanism needs a complete worked example.** The current `368611 + 858808 = 1227419` example is useful, but it should be represented visually and connected to the interface states. Show what each participant sees, what they communicate, what is entered at the podium, how the system identifies the pair, and what changes after acceptance.

- **The escalating group sizes need evidence of design reasoning.** Why powers of two? Why end with eight? Was the rule driven by pedagogy, narrative escalation, expected attendance, software convenience, or room management? What other progressions were considered?

- **Explain the fallback and facilitator override as design compromises.** These are not peripheral administration. They expose a central tension between authentic dependency and finishability. Describe the conditions that activate the fallback, why unrestricted solo progression was rejected, and how the final mechanism balances the two goals.

- **The four technical stages should be presented as a designed sequence.** The manuscript lists them but does not fully explain progression in support, complexity, disciplinary knowledge, openness of the prompt, agent autonomy, or verification demand.

- **The coding agent itself is underspecified.** Name the tool and relevant version used during the event. Explain what "agent mode" allowed it to do, what files or terminal actions it could perform, what participants were told about its limitations, and why "agentic AI" is an accurate term. If it merely generated text or code snippets, use a more precise label.

- **The orientation is a substantial part of the design.** Device choice, operating system, language selection, installation checks, agent login, and a test script all precede the game. Explain how this onboarding was designed, how long it was expected to take, and how it affected the two-hour boundary.

## Missing visual and material evidence

- **The absence of figures is a major weakness for IJDL.** Full design cases are normally rich representations, not text-only descriptions. The journal expects illustrations or multimedia assets and typically publishes text cases of 5,000 to 9,000 words with multiple visuals.

- **Add a participant-flow diagram.** It should show joining, orientation, personal terminal, dataset download, agent interaction, script execution, personal checking, peer grouping, code summation, podium validation, and progression.

- **Add a system diagram.** Show the relationship between a run, participant, stage, dataset, personal code, checker, podium submission, and facilitator dashboard. Keep the diagram conceptual rather than reproducing the database schema.

- **Include annotated interface screenshots.** The most useful views are the personal terminal, stage instructions, personal checker, podium, accepted group message, and facilitator dashboard. Remove all identifying participant information.

- **Include one compact artifact sequence.** A stage prompt, a short agent-generated code excerpt, terminal output, checker response, and podium result would demonstrate the design more effectively than a prose assertion that students remained accountable.

- **Show the contingency design.** An image of a generated offline participant pack and answer sheet would make infrastructure resilience visible as part of the design.

- **Provide meaningful alt text and accessible contrast.** IJDL requires built-in document styles, proper list semantics, alt text, sufficient colour contrast, descriptive links, document-language metadata, and an accessibility check before submission.

- **Do not rely on external project links as article content.** IJDL requires publication assets to be stored in its journal system and does not permit external links except standard references. Relevant project materials must be embedded, submitted as assets, or described within the article.

## Reflection, problems, and failure analysis

- **The manuscript is too polished around the design and too speculative around the participants.** IJDL asks for transparent discussion of problems and failure. Replace generic confidence in the mechanism with specific moments when it did not behave as intended.

- **Report what happened to the two-hour plan.** Did orientation overrun? Which stage caused queues or stalled groups? Did the group-of-eight requirement become feasible? How often did facilitators intervene? If records are unavailable, say which recollections are being used and why they are incomplete.

- **The attendance problem belongs in the design analysis.** Report actual registration and attendance figures where ethically and institutionally permissible. Explain how the discrepancy affected assumptions embedded in the collaboration sizes.

- **Reluctance to collaborate should be framed as a design encounter, not a participant deficit.** The useful question is what the design required socially, what signals or support it provided, and where those provisions were insufficient. Avoid guessing why unnamed participants behaved as they did.

- **The extra-curricular context must shape the analysis.** Attendees opted into an event advertised as collaborative. Explain why the design might behave differently in a compulsory module without turning this case into a general argument about all higher education.

- **Interrogate the intended peer-support mechanism.** Requiring a quicker participant to wait may encourage explanation, but it may also encourage answer sharing, resentment, passive dependence, or domination. Distinguish the system's evidence of co-progression from evidence of peer learning, which the case does not currently possess.

- **Discuss the accessibility failures and risks concretely.** Time pressure, public group formation, movement around a room, spoken coordination, device requirements, account creation, visual interfaces, and rapidly changing groups may all exclude participants. Describe what was designed to address these risks and what remained unresolved.

- **Describe post-event design changes.** A strong case should show how delivery altered the designers' understanding. State which mechanics, instructions, thresholds, interfaces, or facilitation plans would now be changed and what experience prompted each change.

## Claims and generalisation

- **Remove the claim that the case establishes four transferable principles.** IJDL design cases provide precedent, not generalisable findings. The principles can remain as intentions that guided this particular design, but they should not be presented as validated recommendations for other institutions.

- **Reduce or remove "Why Universities Must Teach Agent-Based Development."** That section reads as a position paper and pulls attention away from the designed artifact. Retain only the context needed to explain why the authors chose to build this event.

- **Shorten the future-evaluation section radically.** Seven research questions and a mixed-methods protocol are disproportionate in a descriptive design case. A brief note can identify the two most important unresolved questions, such as whether code combination produces substantive peer explanation and whether verification behaviour transfers beyond the event.

- **Do not claim that the event developed judgement.** The system required observable actions such as checking and code combination. It did not establish understanding, learning, confidence, collaboration quality, or transfer.

- **Treat "designed finishability" as a local design intention.** The phrase may be useful, but it is not yet a demonstrated principle. Show how it influenced concrete choices and where the event challenged it.

- **Use social interdependence literature to illuminate the design, not certify it.** Structural dependency is visible in the system. Positive educational interdependence is an interpretation that requires caution.

## Scholarship and precedent

- **The literature should support design reasoning rather than simulate an outcome study.** Retain sources that explain code-generation risks, social interdependence, scaffolding, game-based learning, and human oversight, but connect each source to a documented design choice.

- **Add learning-design precedent.** The paper needs comparison with educational escape rooms, coding hackathons, collaborative programming events, narrative simulations, and existing AI-literacy designs. This will help readers see what the podium and personalised-code mechanisms add.

- **Engage with design-case methodology.** Explain why this form of reporting is appropriate and how design knowledge differs from empirical generalisation. IJDL's own design-case literature is the obvious starting point.

- **Use recent IJDL AI cases as comparators.** Relevant examples include cases on AI course assistants, AI literacy curricula, educational game development, and AI tools for Learning and Development practitioners. The comparison should identify differences in design problem and form, not merely establish that AI is fashionable.

- **The current bibliography is credible but incomplete for IJDL.** It is weighted towards computing education and general educational psychology. It says little about design process, experiential event design, or design precedent.

## Ethics and participant representation

- **State the ethical basis for the account.** A descriptive design case can rely on design artifacts and non-identifiable operational facts, but observations about participant behaviour still require care. Explain whether ethical review or an institutional determination was sought and which participant data were excluded.

- **Do not retrospectively convert feedback or submissions into research data without approval.** The application contains feedback and progression records. Their technical existence does not authorise scholarly analysis.

- **Label synthetic examples unambiguously.** The Stage 2 codes come from a generated contingency pack. They are design artifacts, not participant outcomes.

- **Protect identities in visuals.** Screenshots of the podium, dashboard, logs, feedback, or personal terminals must use test data and remove names, identifiers, timestamps, and any metadata that could identify attendees.

- **Acknowledge the missing participant perspective.** This is a designer's case. It should not attribute motives or experiences to attendees who are not represented as co-authors or research participants.

## Generative AI policy risk

- **This is the most serious submission issue.** IJDL discourages AI tools from generating manuscript text. It does not impose an absolute ban, but it requires deliberate, disclosed, and verifiable use.

- **The current manuscript has received extensive AI assistance.** The assistance has included drafting, structural revision, source discovery, reference checking, software inspection, LaTeX editing, and editorial critique. Submitting without full disclosure would breach the [IJDL GenAI policy](https://scholarworks.iu.edu/journals/index.php/ijdl/about/submissions).

- **Contact the editors before undertaking a full IJDL conversion.** Explain candidly how the draft was produced and ask whether an author-led rewrite with a detailed disclosure would be considered. This is preferable to investing heavily in a manuscript that the policy may render editorially difficult.

- **The final disclosure must name the system and describe its use.** IJDL requires authors to include relevant tools, prompts, and methods in the body or an appendix. A generic statement that AI improved grammar would be inaccurate.

- **The human authors must perform and document verification.** Every reference, event fact, software description, interpretation, and claim must be checked against primary sources or project records. The authors remain responsible for bias, errors, plagiarism, and misinformation.

- **An author-led rewrite is advisable.** The submitted prose should clearly embody the authors' own analysis and recollection of design decisions. AI can assist with later clarity and proofreading if disclosed, but it should not substitute for the intellectual work that IJDL expects designers to share.

## Structure and writing

- **Rebuild the article around the design rather than preserving the present section order.** A suitable structure might be: design context, design brief and constraints, design process, designed experience, critical design decisions, implementation and breakdowns, post-delivery reflection, and conclusion.

- **Merge the current event-description and implementation sections.** The participant experience and software behaviour should be shown together at the point where each design decision is discussed.

- **Replace repeated accountability claims with one worked sequence.** The Stage 2 artifact chain can show specification, generation, inspection, execution, verification, peer coordination, and progression.

- **Use first person consistently.** Design knowledge is situated. The authors should state what they intended, noticed, changed, and would now reconsider rather than hiding behind "the first author" or impersonal claims.

- **The RStudio opening anecdote is not central to the case.** Retain it only if it genuinely shaped the design brief. Otherwise, begin with the practical design problem of creating a short event for participants with varied prior coding experience.

- **Avoid deficit language.** Participants should not be divided into "capable" and "less capable" groups. Describe variation in prior experience, task familiarity, and confidence without turning those differences into fixed identities.

- **The current 4,400-word length is below IJDL's usual range.** Text cases are generally 5,000 to 9,000 words and include several illustrations or multimedia assets. Use additional space for design history, representations, constraints, and failure analysis, not broader claims about the sector.

- **The abstract should describe the artifact and design context.** It can be up to 250 words. It should state what was designed, for whom, under what constraints, which decisions the case examines, and what tensions emerged.

## Submission compliance

- **Use the IJDL Microsoft Word design-case template.** The current LaTeX PDF is a drafting artifact, not a compliant submission. The template uses built-in styles and IJDL's layout conventions.

- **Prepare the manuscript for anonymous review.** Remove author names and affiliations from the manuscript. The guidance recognises that complete anonymity may be impossible in descriptive cases, but explicit author identification should still be omitted.

- **Convert the reference list to APA 7.** The current `apalike` bibliography is not compliant. Include DOI or URL markers where available.

- **Use a text abstract under 250 words.** Ensure it describes the designed artifact rather than claiming findings that were not evaluated.

- **Embed figures at the appropriate points.** Do not place them all at the end. Use accessible captions and alt text, and submit assets through IJDL's journal system.

- **Complete the accessibility requirements.** Use proper heading styles, semantic lists, table headers, sufficient contrast, descriptive links, language metadata, and the Word accessibility checker.

- **Include a complete GenAI disclosure in the manuscript and submission correspondence.** This must cover both the event's use of coding agents and the manuscript's use of AI during authorship.

- **Expect a developmental but exacting review process.** IJDL desk-screens submissions for scope and design-case form before assigning two peer reviewers. Its guidance estimates that publication can take up to 40 weeks.

## Revision priorities

- **Priority 1: contact IJDL about the extent of AI-assisted authorship.** Resolve this before investing in conversion and visual production.

- **Priority 2: retrieve the design history from project records and the authors' recollections.** Build a chronology of decisions, alternatives, prototypes, compromises, delivery events, and redesign intentions.

- **Priority 3: choose the central design precedent.** Make the personalised-code and podium mechanism the likely centre, with narrative, finishability, validation, and facilitation arranged around it.

- **Priority 4: create visual representations.** Produce the participant flow, conceptual system diagram, interface sequence, and worked Stage 2 artifact chain using test data.

- **Priority 5: replace general claims with situated reflection.** Remove the sector manifesto and most of the research protocol. Add what the designers did, why they did it, what went wrong, and what they would change.

- **Priority 6: address ethics and accessibility.** Define permissible operational evidence, exclude unauthorised participant data, and analyse the actual barriers created by the design.

- **Priority 7: convert to IJDL format.** Use the Word template, APA 7, accessible styles, embedded assets, anonymisation, and the required disclosure.

## Bottom line

- **Strong venue fit, weak manuscript fit.** *Fight The Future* is a credible IJDL design case because it is a deliberately constructed learning experience with distinctive mechanisms and meaningful design tensions.

- **Not ready for IJDL peer review.** The present manuscript suppresses the design process, offers almost no visual precedent, generalises too freely, and contains insufficient failure analysis.

- **The revision is substantial but strategically clear.** Write the article as an honest account of design knowledge in practice. The event does not need to prove that it improved learning. It needs to let other designers see how and why it took this form, where that form broke down, and what the designers learned about the design itself.

## Writer rebuttal and revision record

The responses below refer to the fully rewritten LaTeX manuscript dated 25 August 2026. Writer responses are shown in teal to distinguish them from the editorial review.

- <span style="color: #0B6E75"><strong>Writer response to the provisional decision: addressed.</strong> We accept the editor's diagnosis that the earlier article was argued as a position paper rather than presented as a design case. The manuscript has been rebuilt rather than incrementally revised. Its organising question is now how the design prevented rapid personal completion from making peers irrelevant. The podium mechanism is the central precedent. Sector-level advocacy, transferable principles, and claims of educational effectiveness have been removed.</span>

- <span style="color: #0B6E75"><strong>Writer response on IJDL fit: addressed.</strong> The title is now <em>Designing Fight The Future: A Narrative, Agent-Supported Collaborative Coding Event</em>. The abstract and conclusion identify a situated designed experience rather than a general solution for higher education. The paper now cites Boling's account of design cases and explicitly distinguishes design precedent from empirical generalisation.</span>

- <span style="color: #0B6E75"><strong>Writer response on the design narrative: substantially addressed.</strong> The revised design-process section is organised around the conditions of a live room rather than a production chronology. It explains why the five-step orientation, personal checker, podium, facilitator controls, offline pack, and Stage 4 helpers were necessary. The manuscript also separates the learning, application, and orchestration layers. This keeps attention on educationally consequential decisions and their tradeoffs.</span>

- <span style="color: #0B6E75"><strong>Writer response on author relationship and context: partly addressed.</strong> The lead designer is identified as the person who conceived the event, developed the sequence and application, generated datasets, and facilitated delivery. This statement must be verified by all authors before submission. The paper identifies the May 2026 University of Liverpool setting, voluntary staff and student audience, two-hour design target, available device types, supported languages, and advertised collaboration requirement. Exact attendance, registration totals, room layout, facilitator count, timings, interventions, and completion rates are unavailable in an ethically reportable record. We have refused to invent them.</span>

- <span style="color: #0B6E75"><strong>Writer response on critical design decisions: addressed.</strong> Separate subsections now analyse personalisation, the split between private checking and public progression, the one-two-four-eight sequence, facilitator caps, stranded-player fallback, narrative urgency, accessibility, and the limited meaning of agent mode. Where rationale is reconstructed rather than documented contemporaneously, the manuscript labels it as retrospective and identifies plausible alternatives such as fixed pairs or a shallower group progression.</span>

- <span style="color: #0B6E75"><strong>Writer response on the worked example: addressed.</strong> Stage 2 now includes the task specification, a compact Python solution based on the reference implementation, the synthetic output <code>368611</code>, the second synthetic output <code>858808</code>, and the podium total <code>1227419</code>. The text follows the participant from prompt and generated code through inspection, local execution, personal checking, peer contact, code exchange, summation, and group progression. It states clearly that the software recorded co-progression, not explanation or peer learning.</span>

- <span style="color: #0B6E75"><strong>Writer response on visual and material evidence: partly addressed.</strong> The revised manuscript includes a full-page vector participant-journey figure with three visually distinct lanes for entering, making, and collaborating. It also includes a stage-progression table and a formatted code artifact. The figure uses numbering as well as colour and its caption provides a textual account. Interface screenshots and a separate conceptual data-model diagram remain desirable. They have not been added because suitable anonymised test captures have not yet been produced. This is a remaining production task rather than a reason to substitute participant data.</span>

- <span style="color: #0B6E75"><strong>Writer response on failure and reflection: substantially addressed.</strong> The revised case acknowledges missing operational records, attendance risk, uneven pacing, waiting, participant reluctance, ambiguity in peer interaction, and the fragility of an eight-person threshold. It treats reluctance as an encounter with the design rather than a participant deficit. It identifies specific redesigns including advance orientation, configurable thresholds, a shorter Stage 4, a peer-request queue, structured roles, non-public participation routes, accessibility testing, and explicit verification gates.</span>

- <span style="color: #0B6E75"><strong>Writer response on the extra-curricular audience: addressed.</strong> Voluntary attendance is now established in the design context and returned to in the delivery reflection. The manuscript argues that advance warning and freedom to leave differ materially from a compulsory module. It does not recommend direct transfer. Stable groups, accessible routes, individual practice, explicit learning outcomes, and assessment protections are identified as prerequisites for module use.</span>

- <span style="color: #0B6E75"><strong>Writer response on claims and generalisation: addressed.</strong> The four transferable principles and the section titled "Why Universities Must Teach Agent-Based Development" have been removed. Designed finishability remains only as a name for a local design intention. Social interdependence theory is used to interpret an intended relationship between goals, not to certify educational interdependence. Claims that the event developed judgement, confidence, collaboration, or learning have been removed.</span>

- <span style="color: #0B6E75"><strong>Writer response on future evaluation: addressed.</strong> The seven-question protocol has been replaced by two focused questions. The first asks what interactions actually occur when verified personal outputs are made collectively necessary. The second asks which verification practices transfer when deterministic checking is removed. Suggested evidence distinguishes system operation, interaction, and transfer rather than treating completion or satisfaction as learning.</span>

- <span style="color: #0B6E75"><strong>Writer response on scholarship and precedent: partly addressed.</strong> The bibliography now includes design-case methodology, a systematic review of educational escape rooms, and recent IJDL cases involving generative AI, immersive game development, and critique of AI output. Existing computing-education, AI-literacy, statistical-coding, social-interdependence, psychological-safety, and human-accountability sources have been retained only where they illuminate a documented design decision. A fuller comparison with coding hackathons and collaborative programming events would still strengthen the precedent review.</span>

- <span style="color: #0B6E75"><strong>Writer response on ethics and participant representation: addressed.</strong> A dedicated ethics and data statement limits the case to design artifacts, application behaviour, synthetic contingency data, and practitioner reflection. It excludes participant submissions, feedback, and identifiable logs. Synthetic usernames and codes are labelled. Missing participant voice is acknowledged through repeated distinctions between designer recollection, system behaviour, and participant experience.</span>

- <span style="color: #0B6E75"><strong>Writer response on generative AI authorship: disclosed, with editor contact outstanding.</strong> The manuscript identifies GitHub Copilot as the event tool and records that its exact model was not preserved. It also states that OpenAI Codex using GPT-5 inspected project files, supported restructuring and drafting, located candidate sources, edited LaTeX, and developed the vector figure. Human responsibility and verification are stated. A prompt and workflow appendix still needs to be assembled, and the authors must contact IJDL before submission to confirm that the disclosed authoring process is acceptable.</span>

- <span style="color: #0B6E75"><strong>Writer response on structure and length: addressed.</strong> The article now proceeds through design context, evidence boundaries, brief and constraints, design rationale, designed experience, central mechanism, critical decisions, delivery reflection, future questions, and conclusion. The RStudio anecdote is retained because it explains the problem of syntax without purpose that shaped the brief. The rewritten draft exceeds 5,000 words before the bibliography and uses the added space for implementation detail, representations, tradeoffs, and failure analysis.</span>

- <span style="color: #0B6E75"><strong>Writer response on submission compliance: not yet complete.</strong> The abstract is below 250 words and the review copy is anonymised. The current LaTeX document remains a development artifact. Conversion to the IJDL Word template, APA 7 formatting, semantic styles, final alt text, accessibility checking, embedded production assets, complete anonymisation, and the prompt appendix must occur after the substantive text is approved. The local bibliography style is not represented as final APA 7 output.</span>

- <span style="color: #0B6E75"><strong>Writer request for reconsideration.</strong> We agree that the original manuscript was not ready for peer review. The rewritten version now presents the design process, central precedent, worked artifact chain, visual participant journey, technical and facilitation layers, ethical boundaries, failures, and redesign implications requested by the editor. We ask that suitability be reconsidered after factual verification by both authors, production of anonymised interface images, conversion to the IJDL template, and an explicit editorial decision on the disclosed use of generative AI.</span>
