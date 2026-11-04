"""Add only the deliberately public game-account API; keep private service routes protected."""
from pathlib import Path
import datetime,http.client,os,re,subprocess
config=Path('/etc/caddy/Caddyfile');original=config.read_text()
marker='# QINGYUN_PLAYER_API_V1'
if marker not in original:
    # Match the verified original gateway block, preserving every upstream/header setting.
    pattern=r'(?m)^\treverse_proxy 127\.0\.0\.1:8790 \{\n(?:\t\t[^\n]*\n)*\t\}'
    matches=list(re.finditer(pattern,original))
    if len(matches)!=1 or 'read.qingyunlife.cn, materials.qingyunlife.cn, studio.qingyunlife.cn {' not in original:raise SystemExit('Unexpected Caddy layout; no configuration changed')
    old=matches[0].group()
    replacement='''
    # QINGYUN_PLAYER_API_V1
    @player_api {
        host read.qingyunlife.cn
        path /api/player/*
    }
    handle @player_api {
        request_body {
            max_size 1600000
        }
        reverse_proxy 127.0.0.1:8791 {
            header_up Host {host}
            header_up X-Real-IP {remote_host}
            header_up Cookie "__Host-qingyun_player={http.request.cookie.__Host-qingyun_player}"
        }
    }
    handle {
'''+''.join('\t'+line+'\n' for line in old.splitlines())+'    }'
    candidate=original[:matches[0].start()]+replacement+original[matches[0].end():]
    pending=config.with_name('Caddyfile.player-pending');pending.write_text(candidate)
    subprocess.run(['caddy','validate','--config',str(pending),'--adapter','caddyfile'],check=True,capture_output=True)
    backups=Path('/root/qingyun-accounts-backups');backups.mkdir(mode=0o700,exist_ok=True)
    backup=backups/('Caddyfile-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    with backup.open('x') as f:f.write(original)
    os.chmod(backup,0o600);os.replace(pending,config)
    try:subprocess.run(['systemctl','restart','caddy'],check=True)
    except Exception:
        config.write_text(original);subprocess.run(['systemctl','restart','caddy'],check=True);raise
for host in ['read.qingyunlife.cn','materials.qingyunlife.cn','studio.qingyunlife.cn']:
    c=http.client.HTTPConnection('127.0.0.1',8790,timeout=3);c.request('GET','/',headers={'Host':host,'X-Forwarded-Proto':'https'});r=c.getresponse();assert r.status==303,(host,r.status);r.read();c.close()
print('PLAYER_API_ROUTED; PRIVATE_GATEWAY_STILL_ENFORCES_LOGIN')
