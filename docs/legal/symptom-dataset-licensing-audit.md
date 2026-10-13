# PawCare — Symptom Dataset Public-Source Licensing Audit (Batch 1)

**Task:** `P1-AI-002` (symptom dataset collection/augmentation + annotation)
**Trace:** `docs/design/symptom-dataset-strategy.md` §2.1 (item 2), `requirements.md` §7
**Date:** 2026-10-13 · **Status:** complete for batch 1

## 1. Why this document exists

The `P1-AI-001` strategy commits the project to applying the *same* licensing
discipline to symptom datasets that `P1-RAG-001` applied to the knowledge base:
no external dataset enters the pool unless its reuse terms are explicitly known,
and the terms are read from the dataset's own license statement — never inferred
from the host platform. This document records that audit for batch 1.

## 2. Decision rule

| Gate | Requirement |
|---|---|
| License stated | A concrete license string must be present on the dataset's own page. "Research use", "see source", or a platform-default with no SPDX id is **ambiguous**. |
| Reuse permitted | Redistribution and derivative use must be permitted (CC BY, CC0, MIT, Apache-2.0, or explicit public domain). Non-commercial / no-derivatives terms bar use in a product. |
| Access | The data must be obtainable without a negotiated agreement we cannot evidence for the FYP. |
| Label compatibility | The dataset's label space must map onto PawCare's symptom/red-flag taxonomy without inventing labels. |

## 3. Candidates reviewed (batch 1)

| Dataset | License (as stated) | Access | Label compatibility | Outcome |
|---|---|---|---|---|
| **PetEVAL** — Farrell et al., *ACL BioNLP 2025* (17,600 annotated veterinary EHRs, UK) | Not an open data license; derived from real clinical EHRs, distributed under an access/ethics agreement | Restricted | ICD-11 syndromic chapters + disease NER — clinical, not owner-style | **Refused** — no auditable open license; real-record access terms exceed batch-1 scope |
| **karenwky/pet-health-symptoms-dataset** — Hugging Face (2,000 LLM-generated rows) | **MIT** | Open download | 5 coarse classes (Digestive/Mobility/Parasites/Skin/Ear) that do **not** cover the 9 red-flag categories; mixes owner + clinical register | **Cleared but deferred** — usable, but its label space would distort the red-flag taxonomy; revisit as auxiliary data in a later batch |
| **Kaggle** "Animal Veterinary Health Dataset", "Veterinary Clinical Dataset" | "Other / specified in description" — no SPDX id | Open download | Varies | **Refused** — ambiguous license fails the gate |
| **Zenodo** "Dog Health Vitals Dataset" (Invoxia) | **CC BY 4.0** | Open download | Physiological signals (ECG, heart/breathing rate) — no symptom text | **Out of scope** — not a symptom/condition text dataset |
| **juliakaraul/Animal-Condition** — GitHub | No license file found | Open | Five binary symptoms, multi-species incl. non-pets | **Refused** — no license; out of species scope |

## 4. Consequence for batch 1

No public dataset is folded into batch-1 labels. Batch 1 is therefore built from
the two remaining strategy sources that are self-contained and license-safe:

1. **knowledge-base-derived seed relationships** (cleared batch-1 KB sources), and
2. **rule-based synthetic augmentation** of owner-style text,

plus a **hand-authored held-out set** (strategy §2.1 item 4) that is frozen and
marked `expert_review_status: pending` until the veterinary advisory contact
(`P0-PD-010`) reviews it.

This decision is mirrored in the artifact manifest's `public_dataset_audit`
field, so the choice travels with the data.

## 5. Re-review trigger

Revisit the "cleared but deferred" entry if a later batch needs more label
diversity than synthetic augmentation provides, and re-run the full audit against
the gate in §2 before any fold-in.
