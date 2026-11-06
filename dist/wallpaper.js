/* Original procedural landscape. Weather data is fetched only from our authenticated server. */
(() => {
  'use strict';
  const $=id=>document.getElementById(id),canvas=$('landscape'),ctx=canvas.getContext('2d'),motion=$('motion');
  if(!ctx){motion.hidden=true;return;}
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  let paused=reduced.matches,weather=null,mode='neutral',night=true,w=0,h=0,dpr=1,frame=0,last=0,elapsed=0,paths=[],lastFetch=0;
  function localHour(){return Number(new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Shanghai',hour:'2-digit',hour12:false}).format(new Date()))%24;}
  night=localHour()<6||localHour()>=18;
  function rand(i){const v=Math.sin(i*127.1+311.7)*43758.5453;return v-Math.floor(v);}
  function syncButton(){motion.textContent=paused?'开启动效 ▶':'暂停动效 Ⅱ';motion.setAttribute('aria-pressed',String(paused));motion.setAttribute('aria-label',paused?'开启动画':'暂停场景动画');}
  function resize(width=0,height=0){const r=canvas.getBoundingClientRect();w=width||r.width;h=height||r.height;dpr=width?1:Math.min(devicePixelRatio||1,w<650?1.25:1.5);canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);paths=[];
    for(let layer=0;layer<7;layer++){const p=new Path2D();p.moveTo(-20,h+10);for(let i=-2;i<=102;i++){let x=i/100;const base=.48+layer*.068;const ripple=Math.sin(x*9+layer*1.8)*.055+Math.sin(x*21+layer*.7)*.026+Math.cos(x*44+layer)*.012;const summit=Math.exp(-Math.pow((x-(.70+layer*.019))/.12,2))*(.19-layer*.012);const y=h*(base+ripple-summit);p.lineTo(x*w,y);}p.lineTo(w+20,h+10);p.closePath();paths.push(p);}draw();}
  const palettes={
    clear:{day:['#2d5960','#b6bc98','#edd9a2'],night:['#050e20','#143b4d','#d5cca2']},
    cloudy:{day:['#263c4a','#859a94','#c9c3a3'],night:['#0a1527','#294553','#afc2b1']},
    fog:{day:['#3a5960','#a6b9b0','#c1c6ad'],night:['#152a36','#637f82','#a6bfb8']},
    rain:{day:['#182c3e','#587a81','#a3b9b1'],night:['#060e21','#1f3b51','#a3c1c4']},
    snow:{day:['#385466','#b6c7c2','#f2ead5'],night:['#0b1c32','#567483','#dbe7db']},
    storm:{day:['#0b1c30','#344d65','#bbc5c4'],night:['#040b1a','#23394d','#b1c9c8']},
    neutral:{day:['#193b46','#57796d','#d0c59e'],night:['#071524','#28505b','#c8bd92']}
  };
  function ellipseGlow(x,y,rx,ry,color){ctx.save();ctx.translate(x,y);ctx.scale(rx,ry);const g=ctx.createRadialGradient(0,0,0,0,0,1);g.addColorStop(0,color);g.addColorStop(1,'transparent');ctx.fillStyle=g;ctx.fillRect(-1,-1,2,2);ctx.restore();}
  function pavilion(x,y,s){ctx.save();ctx.translate(x,y);ctx.scale(s,s);ctx.fillStyle='#061c26';ctx.fillRect(-12,-24,24,26);ctx.beginPath();ctx.moveTo(-29,-25);ctx.quadraticCurveTo(-8,-25,0,-41);ctx.quadraticCurveTo(8,-25,29,-25);ctx.quadraticCurveTo(10,-18,-29,-25);ctx.fill();ctx.fillRect(-17,1,34,5);ctx.fillStyle='#d6ba7470';ctx.fillRect(-6,-15,4,11);ctx.fillRect(3,-15,4,11);ctx.restore();}
  function draw(){if(!w||!h)return;ctx.clearRect(0,0,w,h);const palette=(palettes[mode]||palettes.neutral)[night?'night':'day'];const sky=ctx.createLinearGradient(0,0,0,h);sky.addColorStop(0,palette[0]);sky.addColorStop(.65,palette[1]);sky.addColorStop(1,'#0b2932');ctx.fillStyle=sky;ctx.fillRect(0,0,w,h);
    const cloudiness=weather?.cloud??35,wind=Math.min(weather?.wind??7,55),t=elapsed;
    if(night&&mode!=='fog'&&mode!=='storm'){for(let i=0;i<65;i++){let x=rand(i+21)*w,y=rand(i+93)*h*.48;const a=(.15+rand(i+1)*.5)*Math.max(0,1-cloudiness/85)*(.8+.2*Math.sin(t*.4+i));ctx.fillStyle=`rgba(222,225,197,${a})`;ctx.beginPath();ctx.arc(x,y,rand(i+3)*.85+.3,0,Math.PI*2);ctx.fill();}}
    const orbX=w*.77,orbY=h*.22;ellipseGlow(orbX,orbY,w*.34,h*.52,night?'#abc8b328':'#ffe4a159');
    if(mode==='clear'||mode==='neutral'||mode==='cloudy'){ctx.save();if(mode==='cloudy')ctx.globalAlpha=Math.max(.06,1-cloudiness/110);ctx.fillStyle=night?'#e5e4c6dd':'#f5ddb5ce';ctx.beginPath();ctx.arc(orbX,orbY,night?21:31,0,Math.PI*2);ctx.fill();if(night){ctx.fillStyle=palette[0];ctx.beginPath();ctx.arc(orbX-8,orbY-7,19,0,Math.PI*2);ctx.fill();}ctx.restore();}
    // Soft auroral shafts, low opacity; no strobe or rapid flashing.
    if(mode==='clear'){ctx.save();ctx.translate(orbX,orbY);ctx.rotate(-.27);for(let i=0;i<4;i++){const g=ctx.createLinearGradient(0,0,0,h);g.addColorStop(0,night?'#c4d7bb09':'#ffe2a319');g.addColorStop(1,'transparent');ctx.fillStyle=g;ctx.beginPath();ctx.moveTo((i-2)*34,-40);ctx.lineTo((i-2)*140-35,h);ctx.lineTo((i-2)*140+50,h);ctx.lineTo((i-2)*34+8,-40);ctx.fill();}ctx.restore();}
    for(let i=0;i<7;i++){const k=i/6;const g=ctx.createLinearGradient(0,h*.25,0,h);g.addColorStop(0,night?`rgb(${41-i*3},${88-i*7},${102-i*8})`:`rgb(${101-i*12},${135-i*14},${127-i*12})`);g.addColorStop(1,night?'#061a28':'#0a3035');ctx.fillStyle=g;ctx.fill(paths[i]);if(mode==='snow'&&i<4){ctx.save();ctx.globalAlpha=.11;ctx.fillStyle='#d6e5dc';ctx.translate(0,-2);ctx.fill(paths[i]);ctx.restore();}
      ellipseGlow(w*(.45+.3*Math.sin(t*.018+i)),h*(.57+i*.055),w*.8,h*.07,(mode==='fog'?'#d2e2ce26':night?'#80bab715':'#e2ddbd20'));
    }
    pavilion(w*.85,h*.79,w<650?.65:1.0);
    // Windborne cloud banks move at a bounded rate influenced by the actual wind speed.
    for(let i=0;i<6;i++){const speed=(.009+wind*.00018)*(1+i*.08);const x=((rand(i+200)+t*speed)%1.65-.3)*w;const y=h*(.17+rand(i+250)*.42);ellipseGlow(x,y,w*(.35+rand(i+300)*.2),h*.065,mode==='storm'?'#06132355':mode==='fog'?'#c1d5c130':night?'#afc6bd22':'#d5dfd01c');}
    // Glimmering water at the foot of the mountains.
    for(let i=0;i<30;i++){const y=h*(.83+i*.0055),x=w*(.60+Math.sin(i*3.1+t*.62)*.10);ctx.strokeStyle=`rgba(192,199,158,${.025+(i%4)*.008})`;ctx.lineWidth=.7;ctx.beginPath();ctx.moveTo(x-i*2,y);ctx.lineTo(x+i*3+20,y);ctx.stroke();}
    if(mode==='rain'||mode==='storm'){const n=w<650?55:110;ctx.strokeStyle=night?'#b1d2dc50':'#d6e3dc55';ctx.lineWidth=.7;for(let i=0;i<n;i++){const speed=120+rand(i+6)*100,x=(rand(i+7)*w+elapsed*(wind*.2+5))%(w+25)-20,y=(rand(i+18)*h+elapsed*speed)%(h+30)-20;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+2+wind*.06,y+8+rand(i+8)*13);ctx.stroke();}}
    if(mode==='snow'){for(let i=0;i<(w<650?45:85);i++){const y=(rand(i+10)*h+elapsed*(9+rand(i+4)*20))%(h+10)-5,x=(rand(i+21)*w+Math.sin(t*.4+i)*9+t*wind*.1)%(w+10);ctx.fillStyle=`rgba(232,241,228,${.2+rand(i+7)*.5})`;ctx.beginPath();ctx.arc(x,y,.6+rand(i+16)*1.6,0,Math.PI*2);ctx.fill();}}
    if(mode==='fog')ellipseGlow(w*.67,h*.55,w,h*.31,night?'#a3bfc126':'#d9e5d23b');
    const vignette=ctx.createRadialGradient(w*.64,h*.42,h*.1,w*.55,h*.5,w*.8);vignette.addColorStop(0,'transparent');vignette.addColorStop(1,'#02121b55');ctx.fillStyle=vignette;ctx.fillRect(0,0,w,h);
    canvas.dataset.scene=mode;canvas.dataset.phase=night?'night':'day';
  }
  function tick(now){frame=0;if(paused||document.hidden)return;if(!last)last=now;if(now-last>=33){elapsed+=Math.min((now-last)/1000,.1);last=now;draw();}frame=requestAnimationFrame(tick);}
  function run(){cancelAnimationFrame(frame);last=0;if(!paused&&!document.hidden)frame=requestAnimationFrame(tick);else draw();}
  motion.onclick=()=>{paused=!paused;syncButton();run();};
  reduced.addEventListener?.('change',e=>{paused=e.matches;syncButton();run();});document.addEventListener('visibilitychange',()=>{run();if(!document.hidden&&Date.now()-lastFetch>600000)loadWeather();});
  function apply(data){weather=data.available?data:null;mode=weather?.scene||'neutral';night=weather?!weather.is_day:localHour()<6||localHour()>=18;
    if(weather){const now=new Date(),rise=new Date(weather.sunrise+'+08:00'),set=new Date(weather.sunset+'+08:00');if(!isNaN(rise)&&!isNaN(set))night=now<rise||now>=set;
      $('weather-temp').textContent=Math.round(weather.temperature)+'°';$('weather-summary').textContent=weather.description+' · 风速 '+Math.round(weather.wind)+' km/h';$('weather-range').textContent=`今日 ${Math.round(weather.low)}°—${Math.round(weather.high)}° · ${weather.date}`;
      $('weather-time').textContent=(weather.stale?'缓存气象 · ':'数值天气 · ')+'数据 '+weather.observed_at.slice(11,16)+' / 更新 '+weather.updated_at.slice(11,16)+'（北京时间）';
      const names={clear:night?'月照山河':'金光万壑',cloudy:'层云过岱',rain:'烟雨泉城',snow:'雪落群山',storm:'风云际会',fog:'云海无涯'};$('scene-name').textContent='济南 · '+(names[mode]||'山河万象')+' · 天气联动';
    }else{$('weather-temp').textContent='—°';$('weather-summary').textContent=data.message||'天气暂不可用';$('weather-range').textContent='山河画卷 · 无实时天气数据';$('weather-time').textContent='固定城市济南 · 无需定位';$('scene-name').textContent='山河画卷 · '+(data.loading?'等待天气同步':'天气暂不可用');}draw();
  }
  const presets={dawn:['clear',false,'岱色初明'],moon:['clear',true,'月照千峰'],mist:['fog',false,'烟雨泉城']};
  let selected='live', current={available:false,loading:true};
  function paint(){
    apply(current);
    if(selected!=='live'){
      const [presetMode,presetNight,name]=presets[selected];
      mode=presetMode;night=presetNight;weather=null;
      $('scene-name').textContent=name+' · 壁纸预设';
      draw();
    }
  }
  const buttons=document.querySelectorAll('[data-scene]');
  for(const button of buttons)button.addEventListener('click',()=>{
    selected=button.dataset.scene;
    for(const other of buttons)other.setAttribute('aria-pressed',String(other===button));
    paint();
  });
  $('download').addEventListener('click',()=>{
    try{
      resize(1920,1080);
      const link=document.createElement('a');
      link.href=canvas.toDataURL('image/png');
      link.download='旧巷听风-'+selected+'.png';
      link.click();
      $('download-status').textContent='已生成 1920 × 1080 PNG。';
    }catch{
      $('download-status').textContent='壁纸生成失败，请重试。';
    }finally{resize();}
  });
  async function loadWeather(){
    lastFetch=Date.now();
    const controller=new AbortController(), timeout=setTimeout(()=>controller.abort(),7000);
    try{
      const url='https://api.open-meteo.com/v1/forecast?latitude=36.65&longitude=117.12&current=temperature_2m,is_day,weather_code,cloud_cover,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset&timezone=Asia%2FShanghai&forecast_days=1';
      const response=await fetch(url,{signal:controller.signal});
      if(!response.ok)throw Error('weather unavailable');
      const {current:c,daily:d}=await response.json();
      const code=c.weather_code;
      if(![code,c.temperature_2m,c.wind_speed_10m,c.cloud_cover].every(Number.isFinite)||!(Math.abs(Date.now()-Date.parse(c.time+'+08:00'))<7200000))throw Error('invalid weather');
      const scene=code>=95?'storm':[71,73,75,77,85,86].includes(code)?'snow':[45,48].includes(code)?'fog':code>=51?'rain':code<=1?'clear':'cloudy';
      const descriptions={storm:'雷雨',snow:'降雪',fog:'雾',rain:'降雨',clear:'晴',cloudy:'多云或阴'};
      current={available:true,temperature:c.temperature_2m,wind:c.wind_speed_10m,cloud:c.cloud_cover,scene,description:descriptions[scene],is_day:!!c.is_day,date:d.time[0],low:d.temperature_2m_min[0],high:d.temperature_2m_max[0],sunrise:d.sunrise[0],sunset:d.sunset[0],observed_at:c.time,updated_at:new Date().toLocaleString('sv-SE',{timeZone:'Asia/Shanghai'}).replace(' ','T')};
    }catch{current={available:false,message:'济南天气暂不可用'};}
    finally{clearTimeout(timeout);}
    paint();
  }
  if(typeof ResizeObserver!=='undefined')new ResizeObserver(()=>resize()).observe(canvas);else window.addEventListener('resize',()=>resize());
  syncButton();resize();run();loadWeather();setInterval(loadWeather,600000);
})();
