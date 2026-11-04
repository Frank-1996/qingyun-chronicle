#!/bin/bash
set -euo pipefail
cd /opt/qingyun-accounts
python3 -m unittest -q test_accounts
id qingyunplayer >/dev/null 2>&1 || useradd --system --home /var/lib/qingyun-accounts --shell /usr/sbin/nologin qingyunplayer
install -d -m 700 -o qingyunplayer -g qingyunplayer /var/lib/qingyun-accounts
install -m 644 qingyun-accounts.service qingyun-accounts-backup.service qingyun-accounts-backup.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now qingyun-accounts.service
systemctl restart qingyun-accounts.service
python3 - <<'PY'
import http.client,time
for i in range(30):
 try:
  c=http.client.HTTPConnection('127.0.0.1',8791,timeout=2);c.request('GET','/api/player/health');r=c.getresponse();assert r.status==200;r.read();c.close();break
 except Exception:
  if i==29:raise
  time.sleep(.2)
print('ISOLATED_PLAYER_BACKEND_READY')
PY
python3 activate_proxy.py
systemctl enable --now qingyun-accounts-backup.timer
systemctl start qingyun-accounts-backup.service
runuser -u qingyunplayer -- python3 accounts.py --stats
systemctl is-active qingyun-accounts.service qingyun-accounts-backup.timer caddy qingyun-access.service maobidao-archive-sync.timer qingyun-materials.timer
