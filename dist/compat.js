// JSON-only game saves: these shims cover older mobile webviews without SDKs.
(function(){
 if(!window.structuredClone)window.structuredClone=function(value){return JSON.parse(JSON.stringify(value));};
 if(!window.queueMicrotask)window.queueMicrotask=function(fn){Promise.resolve().then(fn);};
 if(!Object.hasOwn)Object.hasOwn=function(object,key){return Object.prototype.hasOwnProperty.call(object,key);};
 document.documentElement.classList.toggle('in-wechat',/MicroMessenger/i.test(navigator.userAgent));
 var timeout=setTimeout(function(){var loading=document.getElementById('loading-note');if(loading)loading.textContent='加载时间较长，请检查网络后刷新。若微信提示域名无法访问，可复制链接到系统浏览器打开。';},15000);
 window.addEventListener('qingyun-ready',function(){clearTimeout(timeout);});
 window.addEventListener('error',function(event){if(event.target&&event.target.tagName==='SCRIPT'){var loading=document.getElementById('loading-note');if(loading)loading.textContent='游戏文件未能载入，请检查网络后刷新重试。';}},true);
})();
