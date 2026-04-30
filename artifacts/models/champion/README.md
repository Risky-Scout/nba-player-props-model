# artifacts/models/champion/

This directory holds backups of prior champion artifacts after a successful
promotion. Each backup is a snapshot named `v_<timestamp>/` containing the
model pickles that used to live at `artifacts/models/`.

Pickles in subdirectories are gitignored; the registry under
`artifacts/models/registry/` is the source of truth for champion identity.
