# Scheduling & Triggering the Reconciliation Agent

Agent ID: `eb165d7e-c8aa-43d3-84ff-055fbcc961e3`

All commands below use real flags from `duvo agents schedules --help` /
`duvo agents triggers --help` (CLI v1.11.0). Schedules and triggers fire
against the agent's **live** build, so promote the file-attached revision
first (see `aop/revision-with-files.json`).

> Tip: add `--json` to any command to get the raw API response (e.g. the new
> schedule/trigger ID, which you'll need for `update` / `delete`).

---

## 1. Weekly sweep (the routine reconciliation run)

Runs every Monday at 07:00 Europe/Brussels.

```bash
duvo agents schedules create eb165d7e-c8aa-43d3-84ff-055fbcc961e3 \
  --frequency weekly \
  --day monday \
  --time 07:00 \
  --timezone Europe/Brussels
```

List / manage it later:

```bash
duvo agents schedules list eb165d7e-c8aa-43d3-84ff-055fbcc961e3
duvo agents schedules delete eb165d7e-c8aa-43d3-84ff-055fbcc961e3 <schedule-id>
```

---

## 2. Quarter-end rebate run (the contract-overlay run)

The `monthly` frequency only supports a single `--day-of-month`, so a
true "last day of each quarter" needs a **custom cron** expression.

Fires at 18:00 on the last day of Mar, Jun, Sep, Dec
(cron: minute hour day-of-month month day-of-week):

```bash
duvo agents schedules create eb165d7e-c8aa-43d3-84ff-055fbcc961e3 \
  --frequency custom \
  --cron "0 18 L 3,6,9,12 *" \
  --timezone Europe/Brussels
```

If your cron flavor does not support `L` (last-day-of-month), use the
1st of the month *after* each quarter close (Jan/Apr/Jul/Oct) instead:

```bash
duvo agents schedules create eb165d7e-c8aa-43d3-84ff-055fbcc961e3 \
  --frequency custom \
  --cron "0 8 1 1,4,7,10 *" \
  --timezone Europe/Brussels
```

Note: a custom-cron schedule cannot pass a "this is the quarter-end /
rebate run" parameter via the CLI — the agent should infer quarter-end
from the run date (it already does: Step 5 runs "on quarter-end / on
demand"). Per-run input parameters are **dashboard only**.

---

## 3. File-drop / event trigger for new invoice PDFs

Event triggers ARE supported by the CLI (`duvo agents triggers set`), but
**the integration must already be connected to the agent** (OAuth
connections are created in the Duvo dashboard, not via CLI).

Discover the exact integration slug + trigger type for this agent:

```bash
duvo agents triggers types eb165d7e-c8aa-43d3-84ff-055fbcc961e3
```

Available today (from `triggers types`):
`gmail/email_received`, `outlook/email_received`, `googledrive/google_drive_item_event`, etc.

### Option A — invoices arriving by email (Gmail)

```bash
duvo agents triggers set eb165d7e-c8aa-43d3-84ff-055fbcc961e3 \
  --integration gmail \
  --trigger-type email_received \
  --filter-config '{"hasAttachment": true}'
```

(Adjust `--filter-config` to the integration's real filter schema — e.g.
sender, subject, label. Confirm the exact keys in the dashboard or via
`triggers types --json`; the JSON above is illustrative.)

### Option B — invoices dropped into a Google Drive folder

```bash
duvo agents triggers set eb165d7e-c8aa-43d3-84ff-055fbcc961e3 \
  --integration googledrive \
  --trigger-type google_drive_item_event \
  --filter-config '{}'
```

Manage triggers:

```bash
duvo agents triggers list eb165d7e-c8aa-43d3-84ff-055fbcc961e3
duvo agents triggers set  eb165d7e-c8aa-43d3-84ff-055fbcc961e3 \
  --integration gmail --trigger-type email_received --disabled   # pause
```

> **Dashboard only:** creating the OAuth connection (Gmail / Google Drive)
> and the exact `--filter-config` filter schema. The trigger itself is
> CLI-configurable once the connection exists. On a file-drop run the agent
> should scope to the single new invoice (AOP Step 1) and dedup via Agent
> Memory `processed_invoices`.

---

## Other available knobs

- **Case trigger** (fire on new cases in a work queue):
  `duvo agents case-triggers create eb165d7e-c8aa-43d3-84ff-055fbcc961e3 --queue <queue-id> --enabled`
  (an agent may have at most one case trigger).
- **One-shot schedule** (run once, then retire): add `--no-recurring`.
- **Create disabled** then enable in the dashboard: add `--disabled`.

## Schedule frequency cheat-sheet (from `--help`)

`--frequency` one of: `every_5_minutes`, `every_15_minutes`, `hourly`,
`daily`, `workday`, `weekly`, `monthly`, `custom`.
`--time` (HH:MM, 24h) required for daily/workday/weekly/monthly.
`--day` required for weekly. `--day-of-month` (1-31) for monthly.
`--cron` required for custom.
