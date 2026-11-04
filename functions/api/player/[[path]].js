// Same-origin account proxy. No credentials or database are bundled into the public game.
export async function onRequest(context){
  const req=context.request,url=new URL(req.url),path=url.pathname;
  if(!/^\/api\/player\/(?:health|me|register|login|profile|change-password|logout|logout-all|recovery-code|reset-password|saves(?:\/[1-3](?:\/versions(?:\/\d+)?)?)?)$/.test(path))return json(404,{error:'接口不存在'});
  if(!['GET','POST','PUT'].includes(req.method))return json(405,{error:'此操作不受支持'});
  const headers=new Headers();
  for(const key of ['Content-Type','Origin','X-Qingyun-Client','X-Qingyun-CSRF']){const v=req.headers.get(key);if(v)headers.set(key,v);}
  const cookie=req.headers.get('Cookie')?.match(/(?:^|;\s*)__Host-qingyun_player=([^;]*)/);if(cookie)headers.set('Cookie','__Host-qingyun_player='+cookie[1]);
  let body;if(req.method!=='GET'){body=await req.arrayBuffer();if(!body.byteLength||body.byteLength>1600000)return json(413,{error:'请求超过允许大小'});}
  const target='https://read.qingyunlife.cn'+path,controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);
  try{const up=await fetch(target,{method:req.method,headers,body,redirect:'manual',signal:controller.signal});if(up.status>=300&&up.status<400||!(up.headers.get('Content-Type')||'').includes('application/json'))return json(503,{error:'账户服务暂不可用，本机进度仍然保留'});
    const h=new Headers({'Content-Type':'application/json; charset=utf-8','Cache-Control':'private, no-store, max-age=0','Pragma':'no-cache','Vary':'Cookie, Origin','X-Content-Type-Options':'nosniff'}),sc=up.headers.get('Set-Cookie');if(sc?.startsWith('__Host-qingyun_player='))h.set('Set-Cookie',sc);return new Response(up.body,{status:up.status,headers:h});
  }catch{return json(503,{error:'账户服务暂时无法连接，本机进度仍然保留'});}finally{clearTimeout(timer);}
}
function json(status,data){return new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'}});}
