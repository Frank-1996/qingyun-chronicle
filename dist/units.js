import {nameAt} from './names.js?v=0.5.0';
// Fictional regions and agencies model Chinese naming patterns; not a real staffing registry.
export const PROVINCES=['江岚省','海宁省','北川省','云泽省','长宁省','东岭省','南原省','西岳省','松江省','青岚省','锦州省','清河省','星湖省','安陵省','明海省','平原省'];
const departments=['教育','财政','民政','司法','人力资源和社会保障','自然资源','生态环境','住房和城乡建设','交通运输','水利','农业农村','商务','文化和旅游','应急管理','审计','市场监督管理'];
export const UNITS=[];
for(let p=0;p<PROVINCES.length;p++){
 const province=PROVINCES[p];
 for(let d=0;d<departments.length;d++)UNITS.push({id:`p${p}d${d}`,name:province+departments[d]+(d===15?'局':'厅'),province,city:'',county:'',level:'省级',department:departments[d]});
 for(let c=0;c<8;c++){
  const city=c===0&&p<3?['临江市','望海市','松原市'][p]:['东','南','西','北','新','平','清','安'][c]+['岚','宁','川','泽','岭','原','岳','江','岚湖','锦','星','河','湖','陵','海','丰'][p]+'市';
  for(let d=0;d<departments.length;d++)UNITS.push({id:`p${p}c${c}d${d}`,name:city+departments[d]+'局',province,city,county:'',level:'市级',department:departments[d]});
  for(let k=0;k<3;k++){
   const county=c===0&&p<3&&k===0?['青禾县','清浦县','平山县'][p]:city.slice(0,-1)+['清源县','和安县','长丰县'][k];
   for(let d=0;d<8;d++)UNITS.push({id:`p${p}c${c}k${k}d${d}`,name:county+departments[d]+'局',province,city,county,level:'县级',department:departments[d]});
  }
 }
}
for(let d=0;d<departments.length;d++)UNITS.push({id:`n${d}`,name:'澄川'+departments[d]+'部',province:'京川首都',city:'京川市',county:'',level:'国家级',department:departments[d]});
const index=new Map(UNITS.map(u=>[u.id,u]));
export const getUnit=id=>index.get(id);
export function appointment(s){if(s.stage!=='work')return {title:'学生',unit:null};const tier=Math.min(10,Math.floor((s.progress+1e-9)*10)),p=s.place%3,d=(s.seed>>>3)%8;let id=tier<=2?`p${p}c0k0d${d}`:tier<=4?`p${p}d${d}`:tier<=6?`p${p}c0d${d}`:tier<=8&&s.progress<.86?`p${p}d${d}`:`n${d}`;const title=['科员','副科长','科长','副处长','处长','副局长','局长','副厅长',s.progress>=.86?'部长':'厅长','国家副主席','国家主席'][tier];return {title:s.retired?'原'+title:title,unit:tier===10?{id:'presidency',name:'澄川国家主席办公室',province:'京川首都',city:'京川市',level:'国家级'}:getUnit(id)};}
export function unitHead(u){const n=Math.max(0,UNITS.indexOf(u));return {name:nameAt(n*37),title:u.name.endsWith('部')?'部长':u.name.endsWith('厅')?'厅长':'局长',unit:u.name};}
export function meetOfficial(s,emit){if(s.stage!=='work'||s.retired)return;const own=appointment(s),tier=Math.floor(s.progress*10),n=(s.seed+Math.floor(s.day/365)*17)>>>0;const candidates=UNITS.filter(u=>u.province===own.unit.province||tier>=7&&u.level==='国家级');const u=candidates[n%candidates.length],head=unitHead(u).title;const titles=tier<3?['科长','副科长',head]:u.level==='省级'?['处长','副处长',head]:u.level==='国家级'?['司长','副司长','部长']:['科长','副局长','局长'];const title=titles[n%titles.length],name=nameAt(n);const key=u.id+title+name;if(s.contacts.some(c=>c.id===key))return;const c={id:key,name,title,unitId:u.id,metAt:Math.floor(s.day/365)};s.contacts.unshift(c);s.contacts=s.contacts.slice(0,60);emit('contact',`工作往来中，你结识了${u.name}的${name}${title}。`);}

