// Replace empty pools with licensed audio URLs; the synthesis fallback works offline.
export const MUSIC={positive:[],negative:[]};
let context,current;
export async function playHint(positive){stop();const pool=positive?MUSIC.positive:MUSIC.negative;if(pool.length){current=new Audio(pool[Math.floor(Math.random()*pool.length)]);await current.play();return;}context=new (window.AudioContext||window.webkitAudioContext)();await context.resume();const root=(positive?261.63:220)*2**(Math.floor(Math.random()*5)/12);const notes=positive?[0,4,7,12,7,9,12,16]:[0,3,7,3,-2,0,-5,0];notes.forEach((n,i)=>{const t=context.currentTime+i*.3;[1,.5].forEach((mul,j)=>{const o=context.createOscillator(),g=context.createGain();o.type=positive?'triangle':'sine';o.frequency.value=root*2**(n/12)*mul;g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(j?.06:.13,t+.04);g.gain.exponentialRampToValueAtTime(.001,t+.5);o.connect(g);g.connect(context.destination);o.start(t);o.stop(t+.55);});});}
export function stop(){if(current){current.pause();current=null;}if(context){context.close().catch(()=>{});context=null;}}

