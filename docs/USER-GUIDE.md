# User Guide

Oráculo turns a decision into a traceable loop: context, alternatives, evidence, recommendation, human choice and observed outcome.

## 1. Replace the demo context

On a fresh installation, records beginning with `DEMO:` are synthetic examples. Use them to explore the interface, then create your own goal and project. Never put secrets in titles, descriptions or evidence intended for an external model.

## 2. Define a measurable goal

Open **Goals** and record:

- a concrete target;
- current value and unit;
- priority and optional deadline;
- what observable result would count as progress.

A goal should help decide between actions, not merely describe an aspiration.

## 3. Connect execution to projects

Open **Projects** and create the workstreams competing for time or capital. Record status, strategic value, risk, validation level and one specific next action. Use **Today** for a small number of priorities that move an active goal.

## 4. State hypotheses before treating them as facts

Open **Hypotheses** and document the assumption, prior probability, test, success condition, failure condition and due date. Update probability only when new evidence warrants it.

## 5. Create a structured decision

Open **Decisions** and write one answerable question. Add at least two genuine alternatives, including the option to delay or gather more evidence when appropriate.

For each option, assess upside, downside, cost, time, reversibility, strategic alignment, evidence strength, execution risk, opportunity cost and uncertainty. These values create a comparative heuristic, not an objective probability.

## 6. Add evidence with provenance

Separate observations from model inference. Record source, capture date, reliability and freshness. Evidence can support or contradict a specific option. Missing evidence should remain visible rather than being filled with confident narrative.

## 7. Analyze locally or with AI

Deterministic analysis works without an external provider. Optional AI analysis sends selected context through the backend and may generate provider charges. Critical decisions can request a separate red-team pass that challenges assumptions and hidden risks.

Review the context, recommendation, evidence, assumptions, confidence and change conditions. The analysis is advice, not authorization.

## 8. Record the human decision

Choose an option explicitly, explain your rationale and set a review date. The human choice is stored separately from the system recommendation so disagreement remains auditable.

## 9. Close the loop

When the result becomes observable, record the outcome and resolve predictions. Calibration metrics become useful only after enough honest predictions and outcomes exist. Do not rewrite earlier probabilities after seeing the result.

## Daily and weekly rhythm

Daily:

1. Review **Today** and alerts.
2. Select concrete priorities.
3. Record blockers and new evidence.
4. Complete the check-in.

Weekly:

1. Review active goals and stalled projects.
2. Resolve expired hypotheses and predictions.
3. Revisit decisions at their review date.
4. Create a backup before structural changes.

## Backup

From `backend`, with the virtual environment active:

```bash
python -m app.cli backup
```

Backups may contain private decisions and evidence and are not encrypted by Oráculo. Store them accordingly.
