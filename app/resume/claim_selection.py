"""Deterministic selection of interview-worthy resume claims."""


def select_core_claims(
    claims: list[dict],
    profile: dict,
    *,
    per_entry: int = 3,
    total: int = 15,
) -> list[dict]:
    """Keep a bounded set of non-education claims in their ranked order."""
    valid_entry_ids = {
        entry.get("entry_id")
        for section in ("experiences", "projects", "research")
        for entry in profile.get(section, [])
        if entry.get("entry_id")
    }
    counts: dict[str, int] = {}
    seen: set[tuple[str, str]] = set()
    selected: list[dict] = []

    for claim in claims:
        entry_id = claim.get("entry_id")
        if valid_entry_ids and entry_id not in valid_entry_ids:
            continue
        if counts.get(entry_id, 0) >= per_entry:
            continue
        text = " ".join(str(claim.get("claim_text", "")).lower().split())
        key = (str(entry_id), text)
        if key in seen:
            continue
        seen.add(key)
        counts[entry_id] = counts.get(entry_id, 0) + 1
        selected.append(claim)
        if len(selected) >= total:
            break

    return selected
