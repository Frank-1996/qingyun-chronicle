import concurrent.futures,http.client,json,tempfile,threading,unittest
from pathlib import Path
from accounts import Store,Server,APIError,COOKIE,PREFIX

P1='test-only-passphrase-alpha';P2='test-only-passphrase-beta'
def fixture(name='王建平'):return dict(version=5,name=name,day=365,lifespan=90,stats=[25,25,25,25,25])

class AccountsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
        self.a,self.at=self.store.register('测试账户',P1,'测试玩家','ip-a')
        self.ar=self.store.require(self.at)
    def tearDown(self):self.tmp.cleanup()
    def test_hashes_and_sessions_are_not_plaintext(self):
        raw=self.store.path.read_bytes()
        for sensitive in [P1,self.at,self.a['recoveryCode']]:self.assertNotIn(sensitive.encode(),raw)
        self.assertIsNone(self.store.session('guess'))
        self.assertNotIn('password_hash',self.a['user']);self.assertNotIn('recovery_hash',self.a['user'])
    def test_unicode_username_uniqueness_and_password_rules(self):
        self.store.register('Alice_01',P1,None,'other-ip')
        with self.assertRaises(APIError) as e:self.store.register('ＡＬＩＣＥ_01',P1,None,'other-ip')
        self.assertEqual(e.exception.status,409)
        for name,pwd in [('x',P1),('valid_name','111111111111'),('bad/name',P1)]:
            with self.assertRaises(APIError):self.store.register(name,pwd,None,'other-ip')
    def test_login_logout_and_password_change_revoke_other_devices(self):
        b,bt=self.store.login('测试账户',P1,'ip-b');self.assertTrue(self.store.session(bt))
        with self.assertRaises(APIError):self.store.login('测试账户','not-the-password','ip-b')
        result,new=self.store.change_password(self.ar,P1,P2)
        self.assertIsNone(self.store.session(self.at));self.assertIsNone(self.store.session(bt));self.assertTrue(self.store.session(new))
        with self.assertRaises(APIError):self.store.login('测试账户',P1,'ip-b')
        self.store.logout(self.store.require(new),True);self.assertIsNone(self.store.session(new))
    def test_recovery_is_single_use_and_revokes_every_session(self):
        result=self.store.reset('测试账户',self.a['recoveryCode'],P2,'ip')
        self.assertIsNone(self.store.session(self.at))
        with self.assertRaises(APIError):self.store.reset('测试账户',self.a['recoveryCode'],P1,'ip')
        self.store.reset('测试账户',result['recoveryCode'],P1,'ip')
        self.assertTrue(self.store.login('测试账户',P1,'ip')[1])
    def test_csrf_is_bound_to_the_current_session(self):
        with self.assertRaises(APIError) as e:self.store.require(self.at,'wrong')
        self.assertEqual(e.exception.status,403)
        self.assertEqual(self.store.require(self.at,self.a['csrf'])['id'],self.ar['id'])
    def test_old_password_snapshot_cannot_rotate_recovery_after_password_changed(self):
        self.store.change_password(self.ar,P1,P2)
        with self.assertRaises(APIError) as e:self.store.new_recovery(self.ar,P1)
        self.assertEqual(e.exception.status,409)
    def test_save_isolation_revision_conflicts_and_version_retention(self):
        for revision in range(5):self.store.put_save(self.ar['id'],1,revision,'测试存档',fixture(str(revision)))
        with self.assertRaises(APIError) as e:self.store.put_save(self.ar['id'],1,0,'旧设备',fixture('stale'))
        self.assertEqual(e.exception.status,409);self.assertEqual(self.store.get_save(self.ar['id'],1)['data']['name'],'4')
        self.assertEqual([x['revision'] for x in self.store.versions(self.ar['id'],1)],[5,4,3])
        other,token=self.store.register('另一个人',P1,None,'ip-other');uid=self.store.require(token)['id']
        self.assertEqual(self.store.slots(uid),[])
        with self.assertRaises(APIError):self.store.get_save(uid,1)
        with self.assertRaises(APIError):self.store.get_save(self.ar['id'],1,1)
    def test_concurrent_writers_do_not_silently_overwrite(self):
        def write(name):
            try:self.store.put_save(self.ar['id'],1,0,name,fixture(name));return 'ok'
            except APIError as e:return e.status
        with concurrent.futures.ThreadPoolExecutor(2) as ex:results=list(ex.map(write,['device-a','device-b']))
        self.assertEqual(sorted(map(str,results)),['409','ok'])
    def test_limits_reject_bad_saves_and_apply_login_throttling(self):
        for bad in [None,{},dict(fixture(),stats=[float('inf')]*5),dict(fixture(),day=10**9)]:
            with self.assertRaises(APIError):self.store.put_save(self.ar['id'],1,0,'bad',bad)
        data=fixture();data['padding']='x'*1_500_001
        with self.assertRaises(APIError) as e:self.store.put_save(self.ar['id'],1,0,'large',data)
        self.assertEqual(e.exception.status,413)
        for _ in range(3):self.store.rate('test',3,60)
        with self.assertRaises(APIError) as e:self.store.rate('test',3,60)
        self.assertEqual(e.exception.status,429)

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.store=Store(cls.tmp.name);cls.server=Server(('127.0.0.1',0),cls.store)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.tmp.cleanup()
    def request(self,path,method='GET',data=None,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
        h={'Origin':'https://qingyunlife.cn','Content-Type':'application/json','X-Qingyun-Client':'web-v1',**(headers or {})}
        c.request(method,PREFIX+path,body=json.dumps(data).encode() if data is not None else None,headers=h);r=c.getresponse();raw=r.read();out=(r.status,dict(r.getheaders()),json.loads(raw));c.close();return out
    def test_authentication_http_contract(self):
        code,h,result=self.request('register','POST',dict(username='http_tester',password=P1,nickname='测试'))
        self.assertEqual(code,201);self.assertIn('Secure',h['Set-Cookie']);self.assertIn('HttpOnly',h['Set-Cookie']);self.assertIn('SameSite=Strict',h['Set-Cookie']);self.assertIn('no-store',h['Cache-Control']);self.assertNotIn('Access-Control-Allow-Origin',h)
        cookie=h['Set-Cookie'].split(';')[0]
        self.assertEqual(self.request('me',headers={'Cookie':cookie})[2]['user']['username'],'http_tester')
        self.assertEqual(self.request('saves/1','PUT',dict(baseRevision=0,label='测试',data=fixture()),{'Cookie':cookie})[0],403)
        self.assertEqual(self.request('saves/1','PUT',dict(baseRevision=0,label='测试',data=fixture()),{'Cookie':cookie,'X-Qingyun-CSRF':result['csrf']})[0],200)
        self.assertEqual(self.request('saves/1')[0],401)
    def test_origin_and_content_type_rejected_before_mutation(self):
        for origin in ['https://evil.example','null','']:
            self.assertEqual(self.request('register','POST',dict(username='bad_origin',password=P1),{'Origin':origin})[0],403)
        self.assertEqual(self.request('register','POST',dict(username='bad_type',password=P1),{'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.request('health')[0],200)
        self.assertEqual(self.request('saves/4','GET')[0],401)
    def test_chunked_proxy_requests_are_supported_and_bounded(self):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
        headers={'Origin':'https://qingyunlife.cn','Content-Type':'application/json','X-Qingyun-Client':'web-v1','Transfer-Encoding':'chunked'}
        raw=json.dumps(dict(username='chunk_tester',password=P1)).encode()
        c.request('POST',PREFIX+'register',body=iter([raw[:20],raw[20:]]),headers=headers,encode_chunked=True)
        r=c.getresponse();self.assertEqual(r.status,201);r.read();c.close()

if __name__=='__main__':unittest.main()
