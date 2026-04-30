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
| 22:25    | 6:25 PM       | `derek_near_lineup` (also refreshes WoO export) | inherited from run_manifest |
| 22:40 → 03:10, every 15 min | through 11:10 PM | `derek_near_lineup`            | inherited from run_manifest |
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
re-runs `build_wizard_of_odds_public_export.py` from scratch, then
uploads `public_export/wizard_of_odds/` over FTPS (with plain-FTP
fallback because the target vsFTPd 3.0.5 server does not advertise
AUTH TLS). Credentials live in repo secrets (`WOO_FTP_HOST`,
`WOO_FTP_USER`, `WOO_FTP_PASSWORD`, `WOO_FTP_REMOTE_DIR`) and are
masked by the runner — never echo them.

## Public URLs

- Public mirror landing page: served from the FTP target's
  `WOO_FTP_REMOTE_DIR` (configured per-environment).
- Repository preview: `public_export/wizard_of_odds/index.html`,
  always reflective of the most recent local build.

## Honest framing

- All published PMFs are **model-only**. Market columns are reference;
  no probability is adjusted to a book line.
- TOV PMFs come from Phase 8 calibrators with no Phase 10D / 10D.2
  overlay.
- Provisional finality is published deliberately so the public feed
  isn't blocked on confirmed lineups. Consumers reading the
  `monetization_view` should respect `finality_status_public` and the
  `lineup_freshness_rollup`.
