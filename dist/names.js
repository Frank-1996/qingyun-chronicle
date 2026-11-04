import {NAME_GROUPS,NAME_PARTS} from './names-data.js?v=0.9.0';
export const NAME_BANK=Object.values(NAME_GROUPS).flat();
export const COMPOUND_SURNAMES=['欧阳','司马','上官','诸葛','夏侯','东方','皇甫','慕容'];
export const NAME_STYLES=[['plain','朴实日常'],['modern','当代姓名'],['classic','传统文雅'],['two','两个字'],['three','三个字'],['compound','少量复姓']];
const SURNAME_POOL=NAME_PARTS.surnames.flatMap((s,i)=>Array(i<10?8:i<30?4:i<60?2:1).fill(s));
const GIVEN=[...new Set([...NAME_PARTS.male,...NAME_PARTS.female,...NAME_PARTS.single,...NAME_PARTS.modern,...NAME_PARTS.classical])];
export const surnameOf=name=>COMPOUND_SURNAMES.find(s=>name.startsWith(s))||name.slice(0,1);
const pick=(a,rnd)=>a[Math.min(a.length-1,Math.floor(rnd()*a.length))];
export function randomName(rnd=Math.random,surname,style='plain',gender){const common=gender==='男'?NAME_PARTS.male:gender==='女'?NAME_PARTS.female:[...NAME_PARTS.male,...NAME_PARTS.female];const x=rnd();const family=surname||(style==='compound'?pick(COMPOUND_SURNAMES,rnd):!['two','three'].includes(style)&&x>=.98?pick(COMPOUND_SURNAMES,rnd):pick(SURNAME_POOL,rnd));const singles=gender==='男'?[...'伟强军勇杰涛明平刚华斌磊超鹏飞峰龙波辉亮健成浩凯松林东旭阳博宇航昊晨然睿诚毅宁安']:gender==='女'?[...'敏静丽娟艳芳燕玲婷倩慧娜霞梅兰珍琴红英萍欣悦佳洁颖雪丹露妍蕾蓉晶雯菲莉芬芸珊琳瑶薇宁安']:NAME_PARTS.single;const pool=style==='two'?singles:style==='modern'?NAME_PARTS.modern:style==='classic'?NAME_PARTS.classical:style==='three'?common:style==='compound'?NAME_PARTS.classical:x<.25?singles:common;return family+pick(pool,rnd);}
export function unusedName(rnd,used,surname){for(let i=0;i<200;i++){const name=randomName(rnd,surname);if(!used.has(name))return name;}const pool=surname?GIVEN.map(g=>surname+g):NAME_BANK;const found=pool.find(n=>!used.has(n));if(!found)throw Error('姓名库已用尽');return found;}
export const nameAt=n=>NAME_BANK[((n%NAME_BANK.length)+NAME_BANK.length)%NAME_BANK.length];
