# PawCare — Symptom Dataset Strategy & Annotation Guideline (P1-AI-001)

**Status:** Draft complete — this is the specification for the later dataset collection and annotation batch (`P1-AI-002`).
**Trace:** `requirements.md` §7, `plan.md` §3, `design/safety/safety-rules-v1.md`

## 1. Objective

PawCare needs a symptom dataset that supports the triage and assessment pipeline without relying on vague or unlabeled public text. This dataset must be usable for:

- symptom extraction from owner-written text,
- normalization of free-text symptoms into canonical symptom concepts,
- severity and duration tagging,
- urgency mapping to the same emergency / urgent / routine / home-care logic used by the Safety Layer,
- evaluation on a held-out expert-validated sample.

This task is explicitly a design gate: the project does not collect or annotate real data yet; it defines the standard first.

## 2. Dataset strategy

### 2.1 Hybrid data design

The dataset will be built from a hybrid strategy rather than a single source:

1. Knowledge-base-derived symptom / condition patterns
   - Extract symptom-condition-urgency relationships from the cleared veterinary sources identified in `P1-RAG-001`.
   - Use those relationships to anchor the label schema and create high-quality seed examples.
   - Treat the knowledge base as a source of clinically grounded symptom clusters and urgency priors, not as the training data itself.

2. Public veterinary/public-health datasets
   - Search for openly licensed or permissioned veterinary, animal-health, or public-health symptom datasets.
   - Apply the same licensing gate as `P1-RAG-001`: no dataset enters the pool unless its reuse terms are explicitly known.
   - Use public datasets only when they are compatible with the project’s safety and attribution rules.

3. Synthetic augmentation of owner-style symptom text
   - Generate paraphrased owner statements from canonical symptom patterns.
   - Use controlled, rule-based variation: duration, severity, appetite change, behavior, and location/body-system modifiers.
   - Keep synthetic examples clearly marked as synthetic so they can be evaluated separately if needed.

4. Expert-validated held-out set
   - Reserve a fixed expert-reviewed sample for final evaluation.
   - This set is not used to tune the model; it is used to measure whether the annotation rules and label definitions stay stable.
   - It should cover emergency, urgent, routine, and low-information cases.

### 2.2 Why this is necessary

The project’s problem is not just “classify text”; it is “classify owner-language symptom text in a way that remains safe, explainable, and legally grounded.” Real owner-style descriptions are more variable than clinical terminology, so the dataset must capture both:

- the clinical concept, and
- the way the owner actually phrases it.

## 3. Annotation unit

A single annotation unit is one span of text referring to a symptom or symptom modifier.

Examples:

- `vomiting`
- `lethargic`
- `not eating for 2 days`
- `strained urination`
- `bloody diarrhea`
- `limping on the left front leg`

Each relevant span is annotated with:

- `symptom_label` (canonical concept)
- `severity` (mild / moderate / severe / unknown)
- `duration` (hours / days / weeks / unknown)
- `body_system` (GI, respiratory, urinary, neurologic, dermal, musculoskeletal, general)
- `behavior_modifier` (e.g. lethargic, restless, hiding, panting)
- `owner_style` (normal text / synthetic / paraphrased / normalized)

The annotation is not a full diagnosis label; it is a symptom evidence layer used downstream by the classifier and safety layer.

## 4. Annotation guideline

### 4.1 What counts as a symptom entity

Annotate a phrase when it communicates a sign or symptom that could matter to a clinician or the safety layer.

Include:

- explicit symptoms: `vomiting`, `diarrhea`, `coughing`, `limping`
- symptom phrases: `not eating for 2 days`, `straining to urinate`, `breathing hard`
- behavior observations that matter clinically: `lethargic`, `hiding`, `panting`, `seems weak`
- abnormal excretions or visible signs: `bloody stool`, `cloudy eyes`, `swollen paw`

Do not annotate:

- general wellness statements with no health concern: `happy`, `friendly`, `normal appetite`
- non-clinical environment words: `home`, `yard`, `bed`, `toy`
- treatment or medication names unless they are directly relevant to the symptom context and not purely a record field
- speculation that is clearly not a symptom: `maybe allergies`, `could be upset` unless the wording is medically actionable

### 4.2 What counts as a modifier

Tag modifiers separately when they change interpretation or urgency.

Examples:

- `duration`: `for 3 days`, `since last night`
- `severity`: `severe`, `very weak`, `worse than yesterday`
- `behavior`: `lethargic`, `restless`, `panting`, `hiding`, `crying`
- `appetite`: `not eating`, `refusing food`, `eating less`
- `location`: `left hind leg`, `abdomen`, `face`

Modifiers should be attached to their symptom phrase when they are clearly part of the same clinical statement.

### 4.3 Multi-label rule

One owner sentence may contain multiple symptom spans. Example:

> `Dog has been vomiting for 2 days, is lethargic, and not eating.`

This should produce annotations for:

- `vomiting` + duration `2 days`
- `lethargic`
- `not eating`

Do not force a single label if the text contains several independent clinical observations.

### 4.4 Ambiguous or low-confidence phrases

If the phrase is uncertain or implies the user is guessing, annotate only the symptom-like material and do not convert it into a diagnosis.

Example:

> `Maybe she has a stomach issue.`

This is not a diagnosis; annotate only the medically relevant symptom signal if present. If no symptom is explicit, count it as `uncertain_symptom_context` and do not force a condition label.

### 4.5 Red-flag language

Red-flag symptoms are not separate labels by default; they are a downstream safety classification. However, the annotation guideline must make them easy to recognize in text.

Examples to flag for safety review:

- difficulty breathing / open-mouth breathing
- collapse / unresponsive / fainting
- seizures
- repeated vomiting with blood
- severe lethargy or weakness
- suspected poisoning / toxin exposure
- straining to urinate with no output
- severe abdominal pain / bloating
- pale gums / blue gums

These should be annotated as symptom evidence, then the downstream Safety Layer applies the emergency rules.

## 5. Worked examples

### Example A

> `My dog has been vomiting for 2 days, is very weak, and won't eat.`

Annotations:

- `vomiting` — duration: 2 days
- `weak` / `very weak` — severity: severe
- `won't eat` — appetite modifier: no appetite

Interpretation:

- clinically meaningful symptom cluster
- should be triaged as urgent or emergency depending on additional context

### Example B

> `Cat is sneezing and has watery eyes, but otherwise playful.`

Annotations:

- `sneezing`
- `watery eyes`
- `playful` — not a symptom; this is a normal-behavior note, not a medical red flag

Interpretation:

- lower urgency than a systemic illness
- still useful for a routine symptom case

### Example C

> `Dog collapsed and is breathing hard after eating chocolate.`

Annotations:

- `collapsed`
- `breathing hard`
- `after eating chocolate` — toxin-context phrase; not a symptom label in itself but important to the safety pipeline

Interpretation:

- emergency class; route through the Safety Layer immediately

### Example D

> `She seems a bit off today, maybe upset stomach.`

Annotations:

- `a bit off` — low-confidence, vague symptom-like note
- `upset stomach` — symptom-like phrase but vague; keep as low-confidence text, do not overfit to a diagnosis

Interpretation:

- uncertain, insufficient-information case; not enough for a confident condition label

## 6. Dataset split and quality gate

### 6.1 Data split

Use a fixed split policy:

- train: 70%
- validation: 15%
- test: 15%
- expert-held-out: separate, not mixed into any training split

The held-out expert set must be manually reviewed and frozen before model evaluation.

### 6.2 Annotation quality checks

Before any model training begins, the annotation guideline must pass three checks:

1. Two annotators independently label the same 30–50 examples.
2. Agreement is calculated for symptom span match and label consistency.
3. Any disagreements are folded into the guideline before the full batch begins.

This is the key quality gate for `P1-AI-001` — if the guideline is not stable, the dataset collection step will drift and inject noise into the model.

## 7. Risks and guardrails

- Do not label a symptom as a diagnosis.
- Do not use real pet-owner data without consent.
- Do not train on datasets whose licensing is unclear.
- Do not collapse clinical severity into generic emotion words; `lethargic`, `weak`, `collapsed` are not the same label.
- Keep red-flag content separate from routine cases in evaluation so emergency recall is measurable.

## 8. Exit criteria for this task

This task is complete when all of the following are documented in the project design set:

- the hybrid dataset strategy is explicitly written down,
- the licensing policy for external datasets is stated and consistent with `P1-RAG-001`,
- the annotation units and label schema are defined,
- worked examples cover routine, ambiguous, and red-flag cases,
- the data split and annotation quality gate are specified,
- the document is specific enough that `P1-AI-002` can run the annotation batch without re-deciding the rules mid-flight.

That is the acceptance threshold for the backlog item.
