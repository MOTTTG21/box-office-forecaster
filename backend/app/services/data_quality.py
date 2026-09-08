"""Runs the deterministic anomaly checks (anomaly_detection.py) and asks Claude for a one-line,
plain-English explanation of each flagged issue - but only the first time an issue appears, or
if its underlying numbers change; the explanation is cached in data_anomalies afterward, so a
page view doesn't re-call the API for anomalies that haven't changed. Claude only ever sees the
exact fields a rule already flagged and is explicitly told not to introduce any new fact: it
explains a contradiction the rule already found, it never originates one. That's the same
"flag, don't silently correct" boundary this project draws everywhere else data quality comes up
(see the about page) - just applied to the database itself instead of a single number.

If the Claude call fails (no API key configured yet, rate limited, network error), the anomaly
still gets recorded with ai_explanation left blank rather than the whole page breaking.
"""

import httpx
from sqlalchemy.orm import Session

from app.models import DataAnomaly
from app.services.anomaly_detection import Anomaly, find_anomalies
from app.services.anthropic_client import anthropic_client

EXPLANATION_PROMPT = """A deterministic rule in a movie box office database flagged the row below as a
likely data quality issue. Explain in ONE plain, neutral sentence why this specific combination of
values looks wrong. Do not state any fact beyond what's given here - you don't have access to the
real-world correct value, only the flagged contradiction itself.

Movie: {title}
Rule: {rule_name}
Flagged detail: {detail}"""


def _explain(anomaly: Anomaly) -> str | None:
    prompt = EXPLANATION_PROMPT.format(title=anomaly.movie.title, rule_name=anomaly.rule_name, detail=anomaly.detail)
    try:
        return anthropic_client.complete(prompt)
    except httpx.HTTPError:
        return None


def refresh_data_anomalies(db: Session) -> list[DataAnomaly]:
    found = find_anomalies(db)
    found_by_key = {(a.movie.id, a.rule_name): a for a in found}
    existing_by_key = {(row.movie_id, row.rule_name): row for row in db.query(DataAnomaly).all()}

    for key, row in existing_by_key.items():
        if key not in found_by_key:
            db.delete(row)

    result_rows: list[DataAnomaly] = []
    for key, anomaly in found_by_key.items():
        row = existing_by_key.get(key)
        if row is not None and row.detail == anomaly.detail:
            result_rows.append(row)
            continue

        explanation = _explain(anomaly)
        if row is None:
            row = DataAnomaly(
                movie_id=anomaly.movie.id,
                rule_name=anomaly.rule_name,
                severity=anomaly.severity,
                detail=anomaly.detail,
                ai_explanation=explanation,
            )
            db.add(row)
        else:
            row.severity = anomaly.severity
            row.detail = anomaly.detail
            row.ai_explanation = explanation
        result_rows.append(row)

    db.commit()
    return result_rows
