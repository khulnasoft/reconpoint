---
description: Guidelines for using Secator within reconPoint, including how to list workflows/scans/tasks and where to find tool documentation.
---

# reconPoint – Secator usage

## Scope

Use this rule when working on features that interact with **Secator**:

- Scan workflows and tasks
- Orchestration of scans from the web UI
- Debugging or listing available workflows/scans/tasks

## Listing Secator configurations

Run these commands **inside the web container** to list available configurations:

```bash
docker exec -it reconpoint-web-1 bash -c \
  "poetry run -C /home/reconpoint/reconpoint python3 -c 'from secator.loader import get_configs_by_type; print(get_configs_by_type(\"workflow\"))'"
```

```bash
docker exec -it reconpoint-web-1 bash -c \
  "poetry run -C /home/reconpoint/reconpoint python3 -c 'from secator.loader import get_configs_by_type; print(get_configs_by_type(\"scan\"))'"
```

```bash
docker exec -it reconpoint-web-1 bash -c \
  "poetry run -C /home/reconpoint/reconpoint python3 -c 'from secator.loader import get_configs_by_type; print(get_configs_by_type(\"task\"))'"
```

These commands show the different elements that Secator exposes (workflows, scans, tasks).

## Documentation and tools

- Main documentation: see [Secator docs](https://github.com/freelabz/secator-docs).
- Secator repository (including tools overview): [Secator repo](https://github.com/freelabz/secator).
- For the detailed list of integrated tools (recon, HTTP, fuzzers, vuln scanners), see the project skill:
  - Skill: `reconpoint-context`
  - Reference file: `.cursor/skills/reconpoint-context/references/secator-tools.md`

## Integration guidelines

- Orchestrate Secator from dedicated service/orchestrator modules; avoid mixing orchestration logic directly into views when possible.
- Validate all user input before passing it into Secator configurations (targets, scopes, workflow names, etc.).
- Do not duplicate Secator configuration parsing logic in multiple places; reuse shared helpers/modules.

