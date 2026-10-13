"""PawCare — cleared knowledge-source registry + ingestion license gate.

Task: P1-RAG-003. Trace: docs/design/rag-ingestion-pipeline-design.md §2, §7.1,
docs/legal/knowledge-source-licensing-tracker.md.

This is the machine-readable mirror of the licensing tracking sheet. The
pipeline refuses to ingest any document whose ``source_id`` is not present here
with ``status == "cleared"`` and a concrete license string. "Found on the
internet" is not a license, and neither is the publisher's reputation: every
entry below was verified against the source's own copyright notice (see the
tracking sheet), and the ``license`` string is copied from that notice verbatim
rather than inferred from the journal's general policy.

To add a source: confirm its license on the source's own terms-of-use/copyright
page, add a row to ``docs/legal/knowledge-source-licensing-tracker.md``, then
add the entry here. Do not add a source that is still ambiguous.
"""

from __future__ import annotations

from app.services.knowledge_base.types import SourceRecord

# A license string that cannot be used to prove reuse rights.
_UNUSABLE_LICENSES = {"", "tbd", "unknown", "n/a", "none", "all rights reserved"}


class LicenseError(ValueError):
    """Raised when a document's source is missing, restricted, or ambiguous."""


_SOURCES: tuple[SourceRecord, ...] = (
    SourceRecord(
        source_id="fda-xylitol",
        title="Paws Off! Xylitol Is Toxic to Dogs",
        publisher="U.S. Food and Drug Administration (FDA)",
        source_url=(
            "https://www.fda.gov/animal-veterinary/animal-health-literacy/"
            "paws-xylitol-toxic-dogs"
        ),
        license="Public domain (U.S. Government work, 17 U.S.C. 105)",
        license_url="https://www.usa.gov/government-copyright",
        attribution_required=False,
        redistribution_permitted=True,
        status="cleared",
        verified="2026-10-13",
        species_applicability=("dog",),
        body_system_tags=("toxicology", "gastrointestinal", "neurologic"),
        content_type="public_health_resource",
        notes="U.S. federal government work; not subject to copyright in the U.S.",
    ),
    SourceRecord(
        source_id="frontiers-household-toxins",
        title="Household Food Items Toxic to Dogs and Cats",
        publisher="Frontiers in Veterinary Science",
        source_url=(
            "https://www.frontiersin.org/journals/veterinary-science/articles/"
            "10.3389/fvets.2016.00026/full"
        ),
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution_required=True,
        redistribution_permitted=True,
        status="cleared",
        verified="2026-10-13",
        species_applicability=("dog", "cat"),
        body_system_tags=("toxicology", "gastrointestinal", "renal", "hematologic"),
        content_type="journal_article",
        notes="DOI 10.3389/fvets.2016.00026; PMC4801869.",
    ),
    SourceRecord(
        source_id="frontiers-hemorrhage",
        title=(
            "Volume Resuscitation in the Acutely Hemorrhaging Patient: "
            "Historic Use to Current Applications"
        ),
        publisher="Frontiers in Veterinary Science",
        source_url=(
            "https://www.frontiersin.org/journals/veterinary-science/articles/"
            "10.3389/fvets.2021.638104/full"
        ),
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution_required=True,
        redistribution_permitted=True,
        status="cleared",
        verified="2026-10-13",
        species_applicability=("dog", "cat"),
        body_system_tags=("cardiovascular", "hematologic"),
        content_type="journal_article",
        notes="DOI 10.3389/fvets.2021.638104; PMC8357988.",
    ),
    SourceRecord(
        source_id="mdpi-gdv",
        title="Gastric Dilatation-Volvulus in Dogs: Analysis of 130 Cases in a Single Institution",
        publisher="Animals (MDPI)",
        source_url="https://www.mdpi.com/2076-2615/15/4/579",
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution_required=True,
        redistribution_permitted=True,
        status="cleared",
        verified="2026-10-13",
        species_applicability=("dog",),
        body_system_tags=("gastrointestinal",),
        content_type="journal_article",
        notes="DOI 10.3390/ani15040579; PMC11851494.",
    ),
    SourceRecord(
        source_id="mdpi-heat-illness",
        title=(
            "Risk Factors for Severe and Fatal Heat-Related Illness in UK Dogs "
            "- A VetCompass Study"
        ),
        publisher="Veterinary Sciences (MDPI)",
        source_url="https://www.mdpi.com/2306-7381/9/5/231",
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution_required=True,
        redistribution_permitted=True,
        status="cleared",
        verified="2026-10-13",
        species_applicability=("dog",),
        body_system_tags=("environmental", "cardiovascular", "neurologic"),
        content_type="journal_article",
        notes="DOI 10.3390/vetsci9050231; PMC9144152.",
    ),
    SourceRecord(
        source_id="mdpi-acute-seizures",
        title="Emergency Approach to Acute Seizures in Dogs and Cats",
        publisher="Veterinary Sciences (MDPI)",
        source_url="https://www.mdpi.com/2306-7381/11/6/277",
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution_required=True,
        redistribution_permitted=True,
        status="cleared",
        verified="2026-10-13",
        species_applicability=("dog", "cat"),
        body_system_tags=("neurologic",),
        content_type="journal_article",
        notes="DOI 10.3390/vetsci11060277; PMC11209469.",
    ),
    SourceRecord(
        source_id="mdpi-emergency-dyspnea-cats",
        title="Emergency Dyspnea in 258 Cats: Insights from the French RAPID CAT Study",
        publisher="Veterinary Sciences (MDPI)",
        source_url="https://www.mdpi.com/2306-7381/12/3/242",
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution_required=True,
        redistribution_permitted=True,
        status="cleared",
        verified="2026-10-13",
        species_applicability=("cat",),
        body_system_tags=("respiratory", "cardiovascular"),
        content_type="journal_article",
        notes="DOI 10.3390/vetsci12030242; PMC11946846.",
    ),
    SourceRecord(
        source_id="mdpi-trauma-att",
        title="Prognostic Performance of ATT and mGCS Scores in Dogs and Cats with Traumatic Injury",
        publisher="Veterinary Sciences (MDPI)",
        source_url="https://www.mdpi.com/2306-7381/12/11/1081",
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution_required=True,
        redistribution_permitted=True,
        status="cleared",
        verified="2026-10-13",
        species_applicability=("dog", "cat"),
        body_system_tags=("trauma", "neurologic", "musculoskeletal"),
        content_type="journal_article",
        notes="DOI 10.3390/vetsci12111081; PMC12656801.",
    ),
    SourceRecord(
        source_id="jvim-feline-urethral-obstruction",
        title=(
            "Occurrence and clinical management of urethral obstruction in male "
            "cats under primary veterinary care in the United Kingdom in 2016"
        ),
        publisher="Journal of Veterinary Internal Medicine (Wiley)",
        source_url="https://onlinelibrary.wiley.com/doi/10.1111/jvim.16389",
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution_required=True,
        redistribution_permitted=True,
        status="cleared",
        verified="2026-10-13",
        species_applicability=("cat",),
        body_system_tags=("urinary",),
        content_type="journal_article",
        notes="DOI 10.1111/jvim.16389; PMC8965234. Per-article CC BY (JVIM is per-article, not journal-wide).",
    ),
)

#: ``source_id`` -> :class:`SourceRecord`. Only ``status == "cleared"`` is ingestable.
CLEARED_SOURCES: dict[str, SourceRecord] = {s.source_id: s for s in _SOURCES}


def get_source(source_id: str) -> SourceRecord | None:
    """Return the registry entry for ``source_id``, or ``None`` if unknown."""
    return CLEARED_SOURCES.get(source_id)


def require_cleared(source_id: str, license: str | None = None) -> SourceRecord:
    """Gate a document for ingestion, or raise :class:`LicenseError`.

    Rules, in order:

    1. the ``source_id`` must exist in the registry;
    2. the entry's ``status`` must be ``"cleared"``;
    3. the entry's license must be a concrete, usable string;
    4. redistribution must be permitted for derivatives;
    5. if the caller passes a ``license`` string, it must match the registry's,
       so a document cannot relabel itself under a different license.
    """
    record = CLEARED_SOURCES.get(source_id)
    if record is None:
        raise LicenseError(
            f"source_id {source_id!r} is not in the cleared registry; add it to "
            "docs/legal/knowledge-source-licensing-tracker.md and source_registry.py first"
        )
    if record.status != "cleared":
        raise LicenseError(
            f"source {source_id!r} has status {record.status!r}; only 'cleared' sources are ingestable"
        )
    if record.license.strip().lower() in _UNUSABLE_LICENSES:
        raise LicenseError(
            f"source {source_id!r} has no usable license ({record.license!r}); refusing to ingest"
        )
    if not record.redistribution_permitted:
        raise LicenseError(
            f"source {source_id!r} does not permit redistribution/derivative use"
        )
    if license is not None and _normalize(license) != _normalize(record.license):
        raise LicenseError(
            f"source {source_id!r} declared license {license!r} does not match the "
            f"registered license {record.license!r}"
        )
    return record


def _normalize(license: str) -> str:
    return " ".join(license.lower().split())
