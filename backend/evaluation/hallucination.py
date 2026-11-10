def annotations_complete(rows):
    return all(r.get("annotation") is not None for r in rows)


def claim_counts(rows):
    non_abstained = [r for r in rows if not r.get("abstained")]
    complete = annotations_complete(non_abstained)
    claims = [c for r in non_abstained if r.get("annotation") for c in r["annotation"]["claims"]]
    unsupported = sum(not c["supported"] for c in claims)
    incidents = [float(any(not c["supported"] for c in r["annotation"]["claims"]))
                 for r in non_abstained if r.get("annotation")]
    pairs = [(sum(not c["supported"] for c in r["annotation"]["claims"]), len(r["annotation"]["claims"]))
             for r in non_abstained if r.get("annotation")]
    return {"complete": complete, "non_abstained": len(non_abstained), "unsupported": unsupported,
            "total_claims": len(claims), "incidents": incidents, "claim_pairs": pairs,
            "reviewed": sum(r.get("annotation") is not None for r in non_abstained)}
