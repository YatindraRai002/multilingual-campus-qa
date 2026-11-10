def language_gap(groups):
    # Groups must come from ONE dataset population, never mix English SQuAD with IndicQA.
    scored = {lang: metrics["accuracy"]["value"] for lang, metrics in groups.items()
              if metrics["accuracy"]["value"] is not None}
    complete = len(scored) >= 2 and len(scored) == len(groups)
    return {"value": max(scored.values())-min(scored.values()) if complete else None,
            "unit": "percentage_points", "status": "scored" if complete else "pending",
            "languages": sorted(scored), "definition": "Highest minus lowest validated language accuracy within the same source dataset.",
            "note": "This is a descriptive gap; different source datasets are never treated as parallel populations."}
