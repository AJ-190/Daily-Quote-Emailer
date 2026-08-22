# Required GitHub Secrets and Configuration

This repository's workflow ("Daily Motivational Emails") requires the following GitHub Secrets to be set in Settings → Secrets → Actions:

- `EMAIL_USER` — the sender email address (e.g., your Gmail address).
- `EMAIL_PASS` — the email account password or App Password (for Google accounts, use an App Password; do NOT use your normal Google password unless you understand the security risk).
- `EMAIL_USERS` — the recipient list. Supported formats:
  - Comma-separated: `alice@example.com,bob@example.com`
  - Semicolon-separated: `alice@example.com; bob@example.com`
  - Newline-separated:
    ```
    alice@example.com
    bob@example.com
    ```

Why the workflow failed

- The scheduled workflow was failing with: `Missing required environment variables: EMAIL_USERS`.
- That means the `EMAIL_USERS` secret is not set in this repository's Secrets, so the script (main.py) exits early with an error.

How to add the secrets (GitHub UI)

1. Go to: Settings → Secrets and variables → Actions in the repository.
2. Click "New repository secret" for each secret above.
3. Enter the name (e.g. `EMAIL_USERS`) and the value, then click "Add secret".

Local testing

- The script loads a local `.env` via python-dotenv for convenience (used for local dev only). You can create a `.env` file with the same variable names for testing:

  EMAIL_USER=you@example.com
  EMAIL_PASS=app_password_or_password
  EMAIL_USERS=alice@example.com,bob@example.com

Security note

- Keep `EMAIL_PASS` private — treat it as a secret. Do not commit `.env` to the repo.
- For Google accounts, create and use an App Password (recommended) instead of your account password.

If you want, I can also:
- Add a small workflow change that makes `EMAIL_USERS` an input for manual runs (workflow_dispatch) so you can run it manually with recipients without adding secrets.
- Create a workflow-safe fallback (not recommended for production) that reads recipients from a repository variable instead of a secret.

Commit created: SECRETS.md — contains the instructions above.
