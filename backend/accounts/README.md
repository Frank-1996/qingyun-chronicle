# Qingyun player backend

Source and deployment templates only. Production data belongs in /var/lib/qingyun-accounts, never here.

Run tests: python3 -m unittest -q test_accounts

Deployment: upload the reviewed release to /opt/qingyun-accounts, then bash install.sh. The installer tests first, starts a loopback-only systemd service, validates and backs up the existing Caddy configuration, adds only /api/player/* on the existing read host, and enables private backups. It aborts if the existing proxy layout differs.

See ../../docs/V9-NOTES.md for current account, recovery and save semantics. Do not use the private-reader password as a game service credential. No administrator password or production user data is part of this source.
