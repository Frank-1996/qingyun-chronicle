"""Isolated Qingyun player accounts and revision-checked cloud saves. Standard library only."""
import argparse,contextlib,datetime,hashlib,hmac,http.cookies,json,math,os,re,secrets,shutil,sqlite3,threading,time,unicodedata
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

PREFIX='/api/player/'
COOKIE='__Host-qingyun_player'
SESSION_SECONDS=7*86400
MAX_BODY=1_600_000
MAX_SAVE=1_500_000
ORIGINS={'https://a.qingyunlife.cn','https://qingyunlife.cn','https://www.qingyunlife.cn','https://qingyun-chronicle.vercel.app','https://read.qingyunlife.cn'}
HASHERS=threading.BoundedSemaphore(2)

class APIError(Exception):
    def __init__(self,status,message,**extra):self.status=status;self.message=message;self.extra=extra

def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def now():return int(time.time())
def password_hash(password,salt):
    with HASHERS:return hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=32768,r=8,p=3,maxmem=64*1024*1024,dklen=32).hex()
def username(value):
    if not isinstance(value,str):raise APIError(400,'请填写用户名')
    value=unicodedata.normalize('NFKC',value).strip()
    if not re.fullmatch(r'[A-Za-z0-9_\u4e00-\u9fff]{2,24}',value):raise APIError(400,'用户名需为2—24个汉字、字母、数字或下划线')
    return value,value.casefold()
def check_password(value,name=''):
    if not isinstance(value,str) or not 12<=len(value)<=128 or len(value.encode())>512:raise APIError(400,'密码需为12—128个字符，可使用长句组合')
    if value.casefold() in {'123456789012','password1234','1234567890123456','qwertyuiop12',name.casefold()} or len(set(value))<4:raise APIError(400,'请使用更难猜测的密码')
    return value
def nickname(value):
    if not isinstance(value,str):raise APIError(400,'昵称格式不正确')
    value=value.strip()
    if not 1<=len(value)<=24 or any(ord(c)<32 for c in value):raise APIError(400,'昵称需为1—24个可显示字符')
    return value
def save_summary(data):
    if not isinstance(data,dict) or data.get('version')!=5:raise APIError(400,'请上传有效的青云纪存档')
    stats=data.get('stats');day=data.get('day');life=data.get('lifespan')
    if not isinstance(stats,list) or len(stats)!=5 or any(type(x) not in (int,float) or not math.isfinite(x) or x<1 for x in stats):raise APIError(400,'存档五维数据无效')
    if type(day)!=int or type(life)!=int or not 70<=life<=150 or not 0<=day<=life*365:raise APIError(400,'存档年龄数据无效')
    name=data.get('name');w=data.get('world') or {}
    if not isinstance(name,str) or not 1<=len(name)<=20 or not isinstance(w,dict):raise APIError(400,'存档角色数据无效')
    path=w.get('path',0);days=w.get('days',0)
    if type(path)!=int or not 0<=path<=4 or type(days)!=int or not 0<=days<=10**14:raise APIError(400,'存档道历数据无效')
    return {'name':name,'age':day//365,'path':path,'cultivationYears':days//365,'day':day}

class Store:
    def __init__(self,root):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);os.chmod(self.root,0o700)
        self.path=self.root/'accounts.sqlite3'
        with self.db() as c:
            c.executescript('''
              CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,username TEXT NOT NULL,username_key TEXT UNIQUE NOT NULL,nickname TEXT NOT NULL,salt TEXT NOT NULL,password_hash TEXT NOT NULL,recovery_hash TEXT NOT NULL,created INTEGER NOT NULL,last_login INTEGER);
              CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),csrf TEXT NOT NULL,expires INTEGER NOT NULL);
              CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id);
              CREATE TABLE IF NOT EXISTS attempts(key TEXT,at INTEGER);
              CREATE INDEX IF NOT EXISTS attempts_key ON attempts(key,at);
              CREATE TABLE IF NOT EXISTS saves(user_id TEXT NOT NULL REFERENCES users(id),slot INTEGER NOT NULL,revision INTEGER NOT NULL,label TEXT NOT NULL,data TEXT NOT NULL,summary TEXT NOT NULL,updated INTEGER NOT NULL,PRIMARY KEY(user_id,slot));
              CREATE TABLE IF NOT EXISTS versions(user_id TEXT NOT NULL,slot INTEGER NOT NULL,revision INTEGER NOT NULL,label TEXT NOT NULL,data TEXT NOT NULL,summary TEXT NOT NULL,updated INTEGER NOT NULL,PRIMARY KEY(user_id,slot,revision));
              CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,user_id TEXT,action TEXT,at INTEGER);
              CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT);
            ''')
            c.execute('PRAGMA max_page_count=131072')
            c.execute('INSERT OR IGNORE INTO meta VALUES(?,?)',('ip_key',secrets.token_hex(32)))
            self.ip_key=c.execute('SELECT value FROM meta WHERE key=?',('ip_key',)).fetchone()[0]
        os.chmod(self.path,0o600)
    @contextlib.contextmanager
    def db(self):
        c=sqlite3.connect(self.path,timeout=10);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA journal_mode=DELETE');c.execute('PRAGMA max_page_count=131072')
        try:
            with c:yield c
        finally:c.close()
    def rate(self,key,limit,seconds):
        at=now()
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE');c.execute('DELETE FROM attempts WHERE at<?',(at-86400,))
            n=c.execute('SELECT count(*) FROM attempts WHERE key=? AND at>?',(key,at-seconds)).fetchone()[0]
            if n>=limit:raise APIError(429,'操作较频繁，请稍后再试',retryAfter=seconds)
            c.execute('INSERT INTO attempts VALUES(?,?)',(key,at))
    def client_key(self,ip):return hmac.new(bytes.fromhex(self.ip_key),ip.encode(),hashlib.sha256).hexdigest()
    def audit(self,c,uid,action):
        c.execute('INSERT INTO audit(user_id,action,at) VALUES(?,?,?)',(uid,action,now()))
        c.execute('DELETE FROM audit WHERE id NOT IN (SELECT id FROM audit ORDER BY id DESC LIMIT 5000)')
    def issue_session(self,c,uid):
        token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(24)
        c.execute('DELETE FROM sessions WHERE expires<?',(now(),))
        c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(digest(token),uid,csrf,now()+SESSION_SECONDS))
        c.execute('DELETE FROM sessions WHERE user_id=? AND token_hash NOT IN (SELECT token_hash FROM sessions WHERE user_id=? ORDER BY expires DESC LIMIT 10)',(uid,uid))
        return token,csrf
    def public_user(self,row):return {'username':row['username'],'nickname':row['nickname'],'createdAt':row['created'],'lastLoginAt':row['last_login']}
    def register(self,name,password,nick,ip):
        name,key=username(name);password=check_password(password,name);nick=nickname(nick or name)
        self.rate('register:'+ip,20,3600)
        salt=secrets.token_hex(16);hashed=password_hash(password,salt);uid=secrets.token_hex(16);recovery=secrets.token_urlsafe(24)
        try:
            with self.db() as c:
                c.execute('BEGIN IMMEDIATE')
                if c.execute('SELECT count(*) FROM users').fetchone()[0]>=1000:raise APIError(503,'当前注册名额已满，请稍后再试')
                c.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?,?,?)',(uid,name,key,nick,salt,hashed,digest(recovery),now(),now()))
                token,csrf=self.issue_session(c,uid);self.audit(c,uid,'register')
                user=self.public_user(c.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone())
        except sqlite3.IntegrityError:raise APIError(409,'该用户名已被使用，请更换')
        return {'user':user,'csrf':csrf,'recoveryCode':recovery},token
    def login(self,name,password,ip):
        _,key=username(name)
        if not isinstance(password,str) or len(password)>128:raise APIError(400,'用户名或密码不正确')
        self.rate('login-ip:'+ip,300,900);self.rate('login-user:'+key,30,900)
        with self.db() as c:r=c.execute('SELECT * FROM users WHERE username_key=?',(key,)).fetchone()
        salt=r['salt'] if r else '0'*32
        expected=r['password_hash'] if r else '0'*64
        valid=hmac.compare_digest(password_hash(password,salt),expected)
        if not r or not valid:raise APIError(401,'用户名或密码不正确')
        with self.db() as c:
            c.execute('UPDATE users SET last_login=? WHERE id=?',(now(),r['id']))
            fresh=c.execute('SELECT password_hash FROM users WHERE id=?',(r['id'],)).fetchone()
            if not hmac.compare_digest(fresh[0],expected):raise APIError(401,'用户名或密码不正确')
            token,csrf=self.issue_session(c,r['id']);self.audit(c,r['id'],'login')
            user=self.public_user(c.execute('SELECT * FROM users WHERE id=?',(r['id'],)).fetchone())
        return {'user':user,'csrf':csrf},token
    def session(self,token):
        if not token or len(token)>200:return None
        with self.db() as c:
            r=c.execute('SELECT users.*,sessions.csrf,sessions.token_hash FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires>?',(digest(token),now())).fetchone()
        return dict(r) if r else None
    def require(self,token,csrf=None):
        r=self.session(token)
        if not r:raise APIError(401,'请先登录账户')
        if csrf is not None and (not isinstance(csrf,str) or not hmac.compare_digest(r['csrf'],csrf)):raise APIError(403,'登录状态校验失败，请刷新后重试')
        return r
    def logout(self,row,all_devices=False):
        with self.db() as c:
            c.execute('DELETE FROM sessions WHERE '+('user_id' if all_devices else 'token_hash')+'=?',(row['id'] if all_devices else row['token_hash'],));self.audit(c,row['id'],'logout_all' if all_devices else 'logout')
    def profile(self,row,nick):
        nick=nickname(nick)
        with self.db() as c:
            c.execute('UPDATE users SET nickname=? WHERE id=?',(nick,row['id']));self.audit(c,row['id'],'profile')
            return self.public_user(c.execute('SELECT * FROM users WHERE id=?',(row['id'],)).fetchone())
    def change_password(self,row,current,new):
        if not isinstance(current,str) or len(current)>128 or not hmac.compare_digest(password_hash(current,row['salt']),row['password_hash']):raise APIError(401,'当前密码不正确')
        new=check_password(new,row['username']);salt=secrets.token_hex(16);hashed=password_hash(new,salt)
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE');fresh=c.execute('SELECT password_hash FROM users WHERE id=?',(row['id'],)).fetchone()
            if not hmac.compare_digest(fresh[0],row['password_hash']):raise APIError(409,'账户状态已变化，请重新登录')
            c.execute('UPDATE users SET salt=?,password_hash=? WHERE id=?',(salt,hashed,row['id']));c.execute('DELETE FROM sessions WHERE user_id=?',(row['id'],));token,csrf=self.issue_session(c,row['id']);self.audit(c,row['id'],'password_change')
        return {'user':self.public_user(row),'csrf':csrf},token
    def new_recovery(self,row,password):
        if not isinstance(password,str) or len(password)>128 or not hmac.compare_digest(password_hash(password,row['salt']),row['password_hash']):raise APIError(401,'当前密码不正确')
        code=secrets.token_urlsafe(24)
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            changed=c.execute('UPDATE users SET recovery_hash=? WHERE id=? AND password_hash=?',(digest(code),row['id'],row['password_hash'])).rowcount
            if changed!=1:raise APIError(409,'账户状态已变化，请重新登录')
            self.audit(c,row['id'],'recovery_rotate')
        return code
    def reset(self,name,code,password,ip):
        _,key=username(name);password=check_password(password,name);self.rate('reset-ip:'+ip,30,3600);self.rate('reset-user:'+key,10,3600)
        with self.db() as c:r=c.execute('SELECT * FROM users WHERE username_key=?',(key,)).fetchone()
        if not isinstance(code,str) or len(code)>100 or not r or not hmac.compare_digest(r['recovery_hash'],digest(code)):raise APIError(401,'用户名或恢复码不正确')
        salt=secrets.token_hex(16);hashed=password_hash(password,salt);new_code=secrets.token_urlsafe(24)
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE');fresh=c.execute('SELECT recovery_hash FROM users WHERE id=?',(r['id'],)).fetchone()
            if not hmac.compare_digest(fresh[0],digest(code)):raise APIError(409,'恢复码已失效')
            c.execute('UPDATE users SET salt=?,password_hash=?,recovery_hash=? WHERE id=?',(salt,hashed,digest(new_code),r['id']));c.execute('DELETE FROM sessions WHERE user_id=?',(r['id'],));self.audit(c,r['id'],'password_reset')
        return {'recoveryCode':new_code}
    def slots(self,uid):
        with self.db() as c:rows=c.execute('SELECT slot,revision,label,summary,updated FROM saves WHERE user_id=? ORDER BY slot',(uid,)).fetchall()
        return [dict(slot=r['slot'],revision=r['revision'],label=r['label'],summary=json.loads(r['summary']),updatedAt=r['updated']) for r in rows]
    def get_save(self,uid,slot,revision=None):
        with self.db() as c:
            r=c.execute('SELECT * FROM '+('versions' if revision is not None else 'saves')+' WHERE user_id=? AND slot=?'+(' AND revision=?' if revision is not None else ''),(uid,slot,revision) if revision is not None else (uid,slot)).fetchone()
        if not r:raise APIError(404,'该存档不存在或版本已超出保留范围')
        return {'slot':slot,'revision':r['revision'],'label':r['label'],'updatedAt':r['updated'],'data':json.loads(r['data'])}
    def versions(self,uid,slot):
        with self.db() as c:rows=c.execute('SELECT revision,label,summary,updated FROM versions WHERE user_id=? AND slot=? ORDER BY revision DESC LIMIT 3',(uid,slot)).fetchall()
        return [dict(revision=r['revision'],label=r['label'],summary=json.loads(r['summary']),updatedAt=r['updated']) for r in rows]
    def put_save(self,uid,slot,base_revision,label,data):
        if type(base_revision)!=int or base_revision<0:raise APIError(400,'存档版本号无效')
        summary=save_summary(data);label=nickname(label or summary['name'])
        try:payload=json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':'))
        except (ValueError,RecursionError):raise APIError(400,'存档包含无效数值或嵌套')
        if len(payload.encode())>MAX_SAVE:raise APIError(413,'存档超过1.5MB，请导出到本机保存')
        self.rate('save:'+uid,120,60)
        if shutil.disk_usage(self.root).free<200*1024*1024:raise APIError(507,'云存档空间暂不足，本机进度仍然保留')
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE');r=c.execute('SELECT revision FROM saves WHERE user_id=? AND slot=?',(uid,slot)).fetchone();current=r[0] if r else 0
            if current!=base_revision:raise APIError(409,'云端有更新，已暂停覆盖；请重新查看云端或选择其他存档槽',currentRevision=current)
            revision=current+1;at=now();summ=json.dumps(summary,ensure_ascii=False)
            c.execute('INSERT OR REPLACE INTO saves VALUES(?,?,?,?,?,?,?)',(uid,slot,revision,label,payload,summ,at));c.execute('INSERT INTO versions VALUES(?,?,?,?,?,?,?)',(uid,slot,revision,label,payload,summ,at))
            c.execute('DELETE FROM versions WHERE user_id=? AND slot=? AND revision NOT IN (SELECT revision FROM versions WHERE user_id=? AND slot=? ORDER BY revision DESC LIMIT 3)',(uid,slot,uid,slot))
        return {'slot':slot,'revision':revision,'updatedAt':at,'summary':summary}
    def stats(self):
        with self.db() as c:return {'users':c.execute('SELECT count(*) FROM users').fetchone()[0],'active_sessions':c.execute('SELECT count(*) FROM sessions WHERE expires>?',(now(),)).fetchone()[0],'save_slots':c.execute('SELECT count(*) FROM saves').fetchone()[0],'database_bytes':self.path.stat().st_size}

class Handler(BaseHTTPRequestHandler):
    server_version='QingyunAccounts'
    def log_message(self,*args):pass
    def reply(self,status,data,cookie=None):
        raw=json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','private, no-store, max-age=0');self.send_header('Pragma','no-cache');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Vary','Cookie, Origin')
        if cookie is not None:
            name='qingyun_player_dev' if self.server.dev else COOKIE
            self.send_header('Set-Cookie',f'{name}={cookie}; Path=/; Max-Age={SESSION_SECONDS if cookie else 0}; HttpOnly; SameSite=Strict'+('' if self.server.dev else '; Secure'))
        self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def token(self):
        c=http.cookies.SimpleCookie()
        try:c.load(self.headers.get('Cookie','')[:8192]);return c.get('qingyun_player_dev' if self.server.dev else COOKIE).value
        except Exception:return ''
    def body(self):
        if self.headers.get_content_type()!='application/json' or self.headers.get('X-Qingyun-Client')!='web-v1':raise APIError(415,'请通过游戏账户界面操作')
        if self.headers.get('Origin','') not in self.server.origins:raise APIError(403,'请求来源不匹配，请从正式游戏页面打开')
        transfer=self.headers.get('Transfer-Encoding','').lower().strip()
        if transfer:
            if transfer!='chunked' or self.headers.get('Content-Length'):raise APIError(400,'请求传输格式无效')
            chunks=[];total=0
            for _ in range(2048):
                line=self.rfile.readline(130)
                if not line.endswith(b'\r\n') or len(line)>128:raise APIError(400,'请求分块无效')
                token=line[:-2].split(b';',1)[0]
                if not re.fullmatch(b'[0-9a-fA-F]+',token):raise APIError(400,'请求分块长度无效')
                n=int(token,16)
                if total+n>MAX_BODY:raise APIError(413,'请求体积过大')
                if n==0:
                    if self.rfile.readline(4)!=b'\r\n':raise APIError(400,'不支持请求尾部附加字段')
                    break
                chunk=self.rfile.read(n)
                if len(chunk)!=n or self.rfile.read(2)!=b'\r\n':raise APIError(400,'请求分块不完整')
                chunks.append(chunk);total+=n
            else:raise APIError(413,'请求分块过多')
            raw=b''.join(chunks)
            if not raw:raise APIError(400,'请求内容为空')
        else:
            try:n=int(self.headers.get('Content-Length','0'))
            except ValueError:raise APIError(400,'请求长度无效')
            if not 1<=n<=MAX_BODY:raise APIError(413,'请求体积过大或为空')
            raw=self.rfile.read(n)
            if len(raw)!=n:raise APIError(400,'请求内容不完整')
        try:value=json.loads(raw,parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
        except (ValueError,RecursionError):raise APIError(400,'请求内容不是有效JSON')
        if not isinstance(value,dict):raise APIError(400,'请求格式不正确')
        return value
    def do_GET(self):self.handle_api('GET')
    def do_POST(self):self.handle_api('POST')
    def do_PUT(self):self.handle_api('PUT')
    def do_DELETE(self):self.reply(405,{'error':'此操作不受支持'})
    def do_OPTIONS(self):self.reply(405,{'error':'仅支持同源游戏入口'})
    def handle_api(self,method):
        self.connection.settimeout(15);path=self.path.split('?',1)[0]
        try:
            if not path.startswith(PREFIX):raise APIError(404,'接口不存在')
            action=path[len(PREFIX):];store=self.server.store;token=self.token()
            if method=='GET' and action=='health':return self.reply(200,{'service':'qingyun-player','version':1})
            if method=='GET' and action=='me':
                r=store.session(token);return self.reply(200,{'user':store.public_user(r) if r else None,'csrf':r['csrf'] if r else None})
            body=self.body() if method in ('POST','PUT') else None
            ip=store.client_key(self.headers.get('X-Real-IP',self.client_address[0])[:100])
            if method=='POST' and action in ('register','login'):
                result,new_token=store.register(body.get('username'),body.get('password'),body.get('nickname'),ip) if action=='register' else store.login(body.get('username'),body.get('password'),ip)
                return self.reply(201 if action=='register' else 200,result,new_token)
            if method=='POST' and action=='reset-password':return self.reply(200,store.reset(body.get('username'),body.get('recoveryCode'),body.get('password'),ip),'')
            row=store.require(token,self.headers.get('X-Qingyun-CSRF','') if method in ('POST','PUT') else None)
            if method=='POST' and action in ('logout','logout-all'):store.logout(row,action=='logout-all');return self.reply(200,{'ok':True},'')
            if method=='POST' and action=='profile':return self.reply(200,{'user':store.profile(row,body.get('nickname'))})
            if method=='POST' and action=='change-password':
                result,new_token=store.change_password(row,body.get('currentPassword'),body.get('password'));return self.reply(200,result,new_token)
            if method=='POST' and action=='recovery-code':return self.reply(200,{'recoveryCode':store.new_recovery(row,body.get('password'))})
            if method=='GET' and action=='saves':return self.reply(200,{'slots':store.slots(row['id'])})
            m=re.fullmatch(r'saves/([1-3])(?:/versions(?:/(\d+))?)?',action)
            if m:
                slot=int(m[1]);revision=int(m[2]) if m[2] else None
                if method=='GET' and action.endswith('/versions'):return self.reply(200,{'versions':store.versions(row['id'],slot)})
                if method=='GET':return self.reply(200,store.get_save(row['id'],slot,revision))
                if method=='PUT' and '/versions' not in action:return self.reply(200,store.put_save(row['id'],slot,body.get('baseRevision'),body.get('label'),body.get('data')))
            raise APIError(404,'接口不存在')
        except APIError as e:self.reply(e.status,{'error':e.message,**e.extra})
        except (sqlite3.Error,OSError,ValueError,TypeError,RecursionError):self.reply(503,{'error':'账户服务暂不可用，本机进度仍然保留'})

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,store,dev=False,origins=None):
        self.store=store;self.dev=dev;self.origins=origins or ORIGINS;self.workers=threading.BoundedSemaphore(8);super().__init__(address,Handler)
    def process_request(self,request,address):
        if not self.workers.acquire(False):self.shutdown_request(request);return
        try:super().process_request(request,address)
        except Exception:self.workers.release();raise
    def process_request_thread(self,request,address):
        try:super().process_request_thread(request,address)
        finally:self.workers.release()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',default='/var/lib/qingyun-accounts');p.add_argument('--port',type=int,default=8791);p.add_argument('--dev',action='store_true');p.add_argument('--stats',action='store_true');p.add_argument('--origin',action='append');args=p.parse_args()
    store=Store(args.data)
    if args.stats:print(json.dumps(store.stats()));raise SystemExit()
    if args.origin and not args.dev:raise SystemExit('--origin is only for loopback development')
    origins=set(args.origin) if args.origin else None
    print('Qingyun player service on loopback',args.port,flush=True);Server(('127.0.0.1',args.port),store,args.dev,origins).serve_forever()
