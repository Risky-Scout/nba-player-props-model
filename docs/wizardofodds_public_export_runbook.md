# Wizard of Odds public export runbook

This runbook covers the **monetization** feed published to the public
WoO portal. It runs on its own schedule, distinct from Derek's
evaluation feed.

## Why two feeds?

Derek and Wizard of Odds have different goals:

- **Derek (evaluation)** — needs an evaluation-grade forward feed
  produced near lineup time so calibration, CLV, and roster-change
  evaluation use the freshest information.
- **Wizard of Odds (monetization)** — needs a public odds page earlier
  in the day so users can see model predictions, click affiliate odds
  buttons, and enter the sportsbook funnel before lineups confirm.

Mixing the two would either delay the monetization feed (bad for
users, bad for revenue) or contaminate Derek's evaluation snapshot
with a "first market reaction" view (bad for science). Phase 12D-amend
split them.

## Schedule

| time UTC | time ET (EDT) | wrapper mode                  | finality_status_public      |
|----------|---------------|-------------------------------|-----------------------------|
| 15:00    | 11:00 AM      | `woo_morning_monetization`    | `PROVISIONAL_EARLY_MARKET`  |
| 18:00    | 2:00 PM       | `woo_afternoon_refresh`       | `PROVISIONAL_EARLY_MARKET`  |
| 20:00    | 4:00 PM       | `woo_afternoon_refresh`       | `PROVISIONAL_EARLY_MARKET`  |
| 22:25    | 6:25 PM       | `derek_pre_tipoff_refresh` (also refreshes WoO export) | inherited from run_manifest |
| 22:40 → 03:10, every 15 min | through 11:10 PM | `derek_pre_tipoff_refresh`            | inherited from run_manifest |
| 03:25    | 11:25 PM      | `close_lock` (also refreshes WoO export) | inherited from run_manifest |

The early monetization runs intentionally publish before lineups
confirm — `finality_status_public=PROVISIONAL_EARLY_MARKET` warns
consumers of the public feed that the projection is provisional and
will be refreshed as lineups land.

## Output layout

`scripts/build_wizard_of_odds_public_export.py` writes to
`public_export/wizard_of_odds/`:

```
public_export/wizard_of_odds/
    manifest.json                # built_at_utc, dates, latest pointer,
                                 # affiliate_config provenance
    index.html                   # browsable directory page
    latest/                      # mirror of the most recent date
    <YYYY-MM-DD>/
        fair_odds_board.{csv,parquet,jsonl}
        full_pmfs_wide.{csv,parquet}
        full_pmfs_outcome_level.{csv,parquet}
        market_comparison.{csv,parquet}
        publishable_edges.{csv,parquet}
        monetization_view.{csv,parquet,jsonl}    # Phase 12D-amend
        run_manifest.json
        README.md
```

`monetization_view` enriches each `market_comparison` row with:

- `affiliate_url` — the affiliate-tracked link to the book's full odds
  page (null when no mapping is configured).
- `odds_button_url` — the affiliate-tracked link for the on-page
  "Bet Now" button (null when no mapping is configured).
- `monetization_status` — `active` when affiliate mapping is in place
  for the row's book, otherwise `needs_affiliate_mapping`.
- `snapshot_type_public` — `woo_morning_monetization`,
  `woo_afternoon_refresh`, or whatever the upstream run manifest
  recorded (e.g. `pre_close`, `close_lock`).
- `snapshot_time_utc_public` — copy of the canonical
  `snapshot_time_utc`.
- `finality_status_public` — `PROVISIONAL_EARLY_MARKET` for early
  WoO runs; otherwise inherited from the canonical run manifest.
- `lineup_freshness_rollup` — JSON-serialised count rollup so the
  public consumer can see at a glance whether lineups were confirmed.
- `availability_freshness_status`, `odds_freshness_status` — recorded
  verbatim from the freshness manifest.

## Affiliate mapping

The script reads `config/wizardofodds_affiliate_links.json`:

```json
{
  "version": 1,
  "default_button_label": "Bet at <book>",
  "books": {
    "draftkings": {
      "affiliate_url": "https://aff.example/dk?subid={market_key}",
      "odds_button_url": "https://aff.example/dk-odds?subid={market_key}",
      "active": true
    },
    "fanduel": {
      "affiliate_url": "https://aff.example/fd",
      "odds_button_url": "https://aff.example/fd-odds",
      "active": true
    }
  }
}
```

Hard rule: **affiliate URLs are never fabricated.** When the file is
absent, the `books` map is empty, or a book has `active=false`, the
URL fields stay null and `monetization_status=needs_affiliate_mapping`.
Activating a new book requires a real-world affiliate agreement and
an explicit edit to this config.

The config file is **not** committed to the repo by default — it
contains revenue-generating subids — but the script's behaviour is
fully defined whether the file exists or not.

## FTP deploy

`.github/workflows/wizard_of_odds_ftp_deploy.yml` runs on
`workflow_run` completion of the daily PMF delivery workflow. It
re-runs `build_wizard_of_odds_public_export.py --all-available` from
scratch, then runs `verify_wizard_of_odds_public_export.py` (Phase 12E
pre-flight) and uploads `public_export/wizard_of_odds/` over FTPS
(with plain-FTP fallback because the target vsFTPd 3.0.5 server does
not advertise AUTH TLS). Credentials live in repo secrets
(`WOO_FTP_HOST`, `WOO_FTP_USER`, `WOO_FTP_PASSWORD`,
`WOO_FTP_REMOTE_DIR`) and are masked by the runner — never echo them.

### Manual deploy from a local checkout

```bash
python3 scripts/build_wizard_of_odds_public_export.py --all-available
python3 scripts/verify_wizard_of_odds_public_export.py
python3 scripts/deploy_wizard_of_odds_ftp.py --allow-plain --check-connection
python3 scripts/deploy_wizard_of_odds_ftp.py --allow-plain
```

The verify step short-circuits the deploy when any of the gates fail
(file presence, row counts > 0, monetization columns, no secret leaks,
PMF sums). `--all-available` is the explicit alias for "build every
date with a `wizard_of_odds/run_manifest.json`"; it is also the
default when `--date` is omitted, but the flag is accepted so
workflows and runbooks can spell out intent.

### Manual deploy from GitHub Actions (workflow_dispatch)

In **Actions → Wizard of Odds — FTP Deploy → Run workflow**, the
default inputs are the production-deploy settings:

| input         | default | when to override                                    |
|---------------|---------|-----------------------------------------------------|
| `check_only`  | `false` | Set `true` to run a no-upload login/`cwd` test.     |
| `walk_only`   | `false` | Set `true` to walk local files only (no FTP at all).|
| `allow_plain` | `true`  | Set `false` once the target enables AUTH TLS.       |

Required secrets (configured at repo → Settings → Secrets → Actions):

- `WOO_FTP_HOST`
- `WOO_FTP_USER`
- `WOO_FTP_PASSWORD`
- `WOO_FTP_REMOTE_DIR` — must equal the path the WoO operator
  configured (currently `/odds-scanner/predictions/`).

A preflight step in the workflow exits non-zero with the message
`Missing WOO_FTP_REMOTE_DIR secret; expected /odds-scanner/predictions/`
if the remote-dir secret is empty, before any login attempt.

### Phase 12F — root cause of the previous failures

The `wizard_of_odds_ftp_deploy.yml` workflow was missing a
`pip install` step. `build_wizard_of_odds_public_export.py` imports
pandas inside `_write_monetization_view`; without it the build
silently dropped the `monetization_view.csv` files (the catch in
`build()` swallowed the `ModuleNotFoundError`), and the verifier then
correctly failed with `latest/monetization_view.csv exists`. Fixed in
Phase 12F by:

1. Adding `pip install pandas pyarrow numpy` to the deploy workflow.
2. Removing the silent-skip catch in `build()` so future dependency
   regressions fail loudly during the build step instead of leaving
   an incomplete export to the verifier.
3. Adding the explicit secrets preflight described above.

## Public URLs

- Public mirror landing page: served from the FTP target's
  `WOO_FTP_REMOTE_DIR` (configured per-environment).
- Repository preview: `public_export/wizard_of_odds/index.html`,
  always reflective of the most recent local build.

### Verifying the upload

The HTTP URL on `dev.wizardofodds.com` is **expected to return
401 Unauthorized** because that host is fronted by Basic Auth. This is
unrelated to the FTP deploy; do not interpret a 401 as a deploy
failure.

To confirm an upload landed:

1. Check the FTP target directly with CyberDuck, FileZilla, or
   `ftp` CLI; or run
   `python3 scripts/deploy_wizard_of_odds_ftp.py --allow-plain --check-connection`
   which lists the remote directory.
2. To browse the HTTP URL, use a browser that lets you supply the
   `dev.wizardofodds.com` Basic Auth credentials (operator-managed,
   not stored in this repo).

A successful deploy leaves these entries at the FTP root (verified
end-to-end in Phase 12E):

```
index.html
manifest.json
latest/
2026-04-27/
2026-04-29/
... (one folder per delivered date)
```

Inside `latest/`:

```
fair_odds_board.{csv,parquet,jsonl}
market_comparison.{csv,parquet}
publishable_edges.{csv,parquet}
monetization_view.{csv,parquet,jsonl}
full_pmfs_wide.{csv,parquet}
full_pmfs_outcome_level.{csv,parquet}
run_manifest.json
README.md
```

## Honest framing

- All published PMFs are **model-only**. Market columns are reference;
  no probability is adjusted to a book line.
- TOV PMFs come from Phase 8 calibrators with no Phase 10D / 10D.2
  overlay.
- Provisional finality is published deliberately so the public feed
  isn't blocked on confirmed lineups. Consumers reading the
  `monetization_view` should respect `finality_status_public` and the
  `lineup_freshness_rollup`.

## Known external blockers

The following items live outside this repo and the FTP deploy
pipeline. They do not block the data upload itself; they block the
WoO public *site* from rendering odds buttons that earn revenue.

1. **HTTP 401 on `dev.wizardofodds.com`.** The dev domain is behind
   HTTP Basic Auth. Any browser hit without credentials returns 401.
   This is **not** a deploy failure — confirm uploads via FTP, not
   HTTP. Production hosts may have a different auth posture; ask the
   WoO operator.
2. **FTP/CyberDuck verification** is the canonical way to confirm a
   deploy. The `--check-connection` mode logs into the target,
   `cwd`s into the remote dir, and lists entries — sufficient to
   confirm credentials and path are correct without uploading.
3. **Affiliate/sub-id mapping.** Until WoO's official sportsbook
   affiliate agreement and per-book sub-ids are recorded in
   `config/wizardofodds_affiliate_links.json`, every row in
   `monetization_view.csv` ships with `monetization_status=needs_affiliate_mapping`
   and blank `affiliate_url` / `odds_button_url`. **This is the
   correct, expected state** until that mapping is delivered. The
   pipeline never fabricates affiliate URLs.
4. The `config/wizardofodds_affiliate_links.json` file is **not**
   committed to this repo because it carries revenue-attribution
   sub-ids. Operators add it locally on the deploy host (or as a
   GitHub Actions secret) and the build picks it up automatically.
