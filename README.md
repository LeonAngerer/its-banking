# its-banking

## Local setup

The Django secret key is read from `banking/banking/secret.json`, which is
ignored by Git. Before running the project, copy `banking/banking/secret.example.json`
to `banking/banking/secret.json` and replace the placeholder with a private,
random key. Do not commit `secret.json`.

The SQLite database (`banking/db.sqlite3`) is also ignored because it can
contain local user and application data.
