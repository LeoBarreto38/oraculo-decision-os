# GitHub Launch Metadata

Use this checklist when creating the public repository. It contains no credentials and does not create or modify any remote resource.

## Repository identity

- **Suggested name:** `oraculo-decision-os`
- **Expected URL:** `https://github.com/LeoBarreto38/oraculo-decision-os`
- **Description:** `Local-first AI decision operating system for evidence, structured alternatives, red-team analysis, predictions, outcomes and calibration.`
- **Visibility:** Public
- **Homepage:** leave empty until a real documentation/demo URL exists
- **License:** AGPL-3.0

## Topics

Use focused discovery terms, no more than GitHub's limit:

```text
decision-intelligence
decision-support
decision-science
local-first
artificial-intelligence
ai-agents
fastapi
react
typescript
sqlite
knowledge-graph
forecasting
calibration
red-team
human-in-the-loop
open-source
privacy
pwa
```

## Social preview

Upload `docs/assets/github-social-preview.jpg` in **Settings → General → Social preview**. The asset is 1280×640, has a solid background and stays below 1 MB.

## Recommended repository settings

- Enable Issues and Discussions.
- Enable vulnerability reporting.
- Enable the dependency graph, Dependabot alerts and security updates.
- Allow squash merging; automatically delete merged branches.
- Add a `main` branch ruleset after the first push: require CI, block force pushes and require the branch to be up to date.
- Do not require multiple external approvals while the project has only one maintainer.
- Keep Actions token permissions read-only by default.

## First release

Create `v0.1.0` only after CI passes on GitHub. Suggested title: `v0.1.0 Genesis — Public Foundation`. Release notes must distinguish current behavior from roadmap items and call the project early-stage.

## Honest visibility strategy

1. Publish one real workflow GIF or short video using DEMO data.
2. Write a technical launch post explaining the measurable decision loop and why recommendations are kept separate from human choices.
3. Invite criticism around evidence provenance, calibration and human control.
4. Convert feedback into labelled Issues and small releases.
5. Avoid purchased stars, reciprocal-star campaigns, fabricated users, artificial benchmarks or claims of production maturity.

Trustworthy demonstrations and a visible response to feedback create stronger professional signal than inflated metrics.
