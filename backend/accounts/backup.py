"""Daily private SQLite backup, retaining three completed snapshots."""
import datetime,os,sqlite3
from pathlib import Path
root=Path('/var/lib/qingyun-accounts');folder=root/'backups';folder.mkdir(mode=0o700,exist_ok=True)
target=folder/('accounts-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')+'.sqlite3')
temporary=folder/'backup.pending'
with sqlite3.connect(root/'accounts.sqlite3') as source,sqlite3.connect(temporary) as destination:source.backup(destination)
os.chmod(temporary,0o600);os.replace(temporary,target)
for p in sorted(folder.glob('accounts-????????.sqlite3'),reverse=True)[3:]:
    if p.resolve().parent==folder.resolve():p.unlink()
print('Private account backup complete')
