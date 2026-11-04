export const DESTINIES=[
 {id:'ordinary',name:'平常人家',text:'不偏一端，五维成长均衡提升2%。',focus:null},
 {id:'scholar',name:'书香门第',text:'智成长提升15%，其他维度不变。',focus:1},
 {id:'artisan',name:'百工传家',text:'劳成长提升15%，其他维度不变。',focus:4},
 {id:'benevolent',name:'仁厚家风',text:'德成长提升15%，其他维度不变。',focus:0},
 {id:'vigorous',name:'筋骨强健',text:'体成长提升15%，其他维度不变。',focus:2},
 {id:'artist',name:'艺事熏陶',text:'美成长提升15%，其他维度不变。',focus:3},
 {id:'traveller',name:'四海为家',text:'星球、宇宙穿行修为消耗由20降至15。',focus:null},
 {id:'late',name:'大器晚成',text:'凡间40岁后及修行篇五维成长提升12%。',focus:null}
];
export const destiny=s=>DESTINIES.find(d=>d.id===s.destiny)||DESTINIES[0];
export function destinyRate(s,index){const d=destiny(s);return d.id==='ordinary'?1.02:d.focus===index?1.15:d.id==='late'&&(s.world?.path>0||s.day>=40*365)?1.12:1;}
export const travelCost=s=>destiny(s).id==='traveller'?15:20;
