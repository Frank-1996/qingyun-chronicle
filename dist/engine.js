export const KEYS=['德','智','体','美','劳'];
export const RANKS=['二级科员','一级科员','四级主任科员','三级主任科员','二级主任科员','一级主任科员','四级调研员','三级调研员','二级调研员','一级调研员','二级巡视员','一级巡视员'];
export const OFFICES=['未任职','乡科级副职','乡科级正职','县处级副职','县处级正职','厅局级副职','厅局级正职','省部级副职','省部级正职','国家级副职','国家级正职 · 国家主席'];
export const ACTIVITIES=[{name:'读书明理',icon:'卷',desc:'阅读、求知与独立思考',gain:[.3,1,.1,.2,.2]},{name:'身体力行',icon:'行',desc:'运动、休息与健康生活',gain:[.1,.2,1,.3,.3]},{name:'躬身实践',icon:'耕',desc:'在劳动中发现真实问题',gain:[.5,.4,.3,.1,1]},{name:'心怀他人',icon:'仁',desc:'倾听、照护与公共服务',gain:[1,.3,.2,.3,.4]},{name:'观物审美',icon:'境',desc:'音乐、绘画与感受生活',gain:[.3,.4,.2,1,.2]}];
const STORIES=[
 ['看见他人','伙伴的作品被误认为是你的，大家正在夸奖你。',['说明作品的真正作者','顺势接受称赞','责怪伙伴没有署名'],0],
 ['求知之路','你遇到一个没有标准答案的问题。',['照抄最受欢迎的答案','查证资料，再做小实验','干脆跳过问题'],1],
 ['一起完成','集体劳动任务比预计更繁重。',['只完成最容易被看见的部分','催促别人加快速度','分工协作，自己也参与最辛苦的工作'],2],
 ['时间的分配','繁重的任务与身体疲劳同时到来。',['通宵硬撑，忽视不适','安排休息、分清轻重并寻求协作','完全推给别人'],1],
 ['审美的价值','社区准备改造一处公共空间。',['先听使用者的需要，兼顾实用与美感','只做醒目的外观','只看最低报价'],0],
 ['实地调研','你负责的项目，报表与居民感受并不一致。',['把不一致的数据删掉','要求大家统一口径','走访现场，公开差异并修订方案'],2],
 ['有限的预算','澄川的公共预算需要作出取舍。',['依据需求和证据，优先保障基本服务','平均分配而不核实需要','全部用于显眼的大项目'],0],
 ['面对失误','你的方案出现偏差，伙伴建议暂时隐瞒。',['等问题自行消失','说明事实、承担责任并及时纠偏','将责任全部转交他人'],1],
 ['长远与眼前','一个短期收益高的方案，可能带来长期损害。',['只看今年的成绩','跳过评估立即执行','公开评估代价，寻找可持续的替代方案'],2],
 ['倾听不同','讨论中，一位年轻成员提出了反对意见。',['邀请说明证据，再共同验证','以资历结束讨论','将意见排除在记录之外'],0]
];
export function create(name='林知远',stats=[20,20,20,20,20],lifespan=90,seed=Date.now()>>>0){if(!Array.isArray(stats)||stats.length!==5||stats.some(x=>!Number.isInteger(x)||x<5||x>60)||stats.reduce((a,b)=>a+b,0)!==100)throw Error('五维初始属性须合计100，每项5–60');if(!Number.isInteger(lifespan)||lifespan<70||lifespan>110)throw Error('寿命须为70–110岁');return {version:1,name:String(name).trim().slice(0,20)||'林知远',stats:[...stats],lifespan,seed,day:0,merit:0,insight:0,correct:0,decisions:0,logs:[],history:[],pending:false,ended:false};}
export const age=s=>Math.floor(s.day/365);
export function career(s){const a=age(s);if(a<22)return {rank:a<6?'幼年 · 初识世界':a<18?'学生 · 求知成长':'青年 · 准备入职',office:'尚未任职',level:'—',progress:0};const target=Math.floor(s.lifespan*.8);const p=Math.min(1,Math.max(0,(a-22)/(target-22)-Math.max(0,(s.decisions-s.correct)*.012-(s.day?s.insight/s.day:0)*.02)));return {rank:RANKS[Math.min(11,Math.floor(p*11))],office:OFFICES[Math.min(10,Math.floor(p*10))],level:Math.max(1,27-Math.floor(p*26)),progress:p};}
export function event(s){const y=age(s), ix=(Math.imul((y+1),2654435761)^(s.seed>>>0))>>>0;const story=STORIES[ix%(y<18?5:STORIES.length)],rotation=(ix>>>8)%3;return {title:story[0],text:(y<6?'在家人的陪伴与引导下，':y<18?'成长途中，':'这一年，')+story[1],options:[0,1,2].map(i=>story[2][(i+rotation)%3]),answer:(story[3]-rotation+3)%3};}
function log(s,text){s.logs.unshift({day:s.day,text});s.logs=s.logs.slice(0,120);}
export function advance(s,days,activity=0){if(s.pending||s.ended)return 0;if(![1,7,30,365].includes(days)||!ACTIVITIES[activity])throw Error('无效行动');const n=Math.min(days,365-s.day%365,s.lifespan*365-s.day);const quality=days===1?1:days===7?.85:days===30?.68:.5;for(let d=0;d<n;d++){const health=.55+Math.min(100,s.stats[2])/200,practice=.65+Math.min(100,s.stats[4])/285;const direction=.75+Math.min(100,s.stats[0])/400;ACTIVITIES[activity].gain.forEach((g,i)=>{const factor=i===2?1:health*practice*direction;s.stats[i]=Math.min(100,s.stats[i]+g*.022*factor);});s.merit+=quality*(.7+s.stats[0]/200+s.stats[1]/250+s.stats[3]/400+s.stats[4]/200);s.insight+=quality;s.day++;}log(s,`${ACTIVITIES[activity].name} · ${n}天，成长汇报 +${(n*quality).toFixed(1)}；五维共同成长。`);if(s.day%365===0)s.pending=true;return n;}
export function decide(s,index){if(!s.pending||![0,1,2].includes(index))return null;const e=event(s),ok=index===e.answer;s.decisions++;if(ok){s.correct++;s.merit+=100;s.stats=s.stats.map(x=>Math.min(100,x+.5));}else{s.merit+=20;}const report=s.insight/Math.max(1,s.day),detail=report>.9?'你逐日积累的记录，让这一年的成长脉络清晰可见。':report>.7?'阶段汇报保留了主要线索，部分细节已在快进中略去。':'快进留下了概览，一些生活细节与观察奖励已被略去。';const item={age:age(s),ok,title:e.title,choice:e.options[index],report:detail};s.history.unshift(item);log(s,`年度抉择：${ok?'方向正确':'尚有遗憾'}。${detail}`);s.pending=false;if(s.day>=s.lifespan*365){s.ended=true;log(s,'人生终章：你留下的，是每一天与每一次选择。');}return item;}
export function validate(s){if(!s||s.version!==1||typeof s.name!=='string'||s.name.length>20||!Number.isInteger(s.seed)||!Array.isArray(s.stats)||s.stats.length!==5||s.stats.some(x=>!Number.isFinite(x)||x<5||x>100)||!Number.isInteger(s.lifespan)||s.lifespan<70||s.lifespan>110||!Number.isInteger(s.day)||s.day<0||s.day>s.lifespan*365||!Number.isInteger(s.correct)||!Number.isInteger(s.decisions)||s.correct<0||s.correct>s.decisions||s.decisions>Math.floor(s.day/365)||!Number.isFinite(s.merit)||s.merit<0||!Number.isFinite(s.insight)||s.insight<0||s.insight>s.day||typeof s.pending!=='boolean'||typeof s.ended!=='boolean'||(s.pending&&s.day%365!==0)||!Array.isArray(s.logs)||!Array.isArray(s.history))throw Error('存档格式无效');return s;}

