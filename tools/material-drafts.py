"""Versioned, original game-design proposals, explicitly separate from collected history."""
import json

IMMORTALS=['启灵','养气','筑基','凝元','结丹','化婴','炼神','合道','渡劫','飞升']
GOD_RANKS=['候补神使','乡域守神','城域正神','州域司神','国域主神','洲域大神','星域神君','法则神尊','至高神议席']
DOMAINS=[('山岳','地脉修复','山崩'),('江河','调蓄水脉','洪涝'),('海洋','护航与潮汐','海啸'),
 ('雷霆','裁决违誓','雷灾'),('风雨','调和气候','旱灾'),('农桑','守护耕作','歉收'),
 ('医药','救治疫病','瘟疫'),('文教','传承知识','失学'),('工造','维护工程','工程事故'),
 ('商贸','守护契约','信用危机'),('司法','平反与审判','冤案'),('武备','守卫边界','入侵'),
 ('星辰','维护星路','星轨偏移'),('日光','维持昼序','日蚀异变'),('月华','维持夜序','潮汐失衡'),
 ('火焰','调节火源','火灾'),('森林','修复生态','枯萎'),('道路','维护通行','道路断绝'),
 ('记忆','保存文明档案','历史遗失'),('界门','维护域间通道','空间裂隙')]
POLITIES=[('议政共和','议院与行政院相互制衡','公开考试与任期考评'),('君主立宪','王室礼仪与民选内阁并存','议会问责与专业文官'),
 ('联邦共和','中央与成员邦分权','联邦及地方双轨考试'),('城邦联盟','城市议会协商共同事务','城邦历练与联盟选任'),
 ('贤议制','教育院与公民议事厅共议','公开论策与基层实践'),('海港商议制','港口议会管理航路与关税','契约信用与港务履历'),
 ('山地自治联邦','山谷自治与联邦协调','地方服务与跨谷轮岗'),('草原共议制','季节议会协调迁徙与牧场','调解经验与资源治理'),
 ('工造议政制','专业院与公民院共同审议','工程责任与公共考试'),('绿洲联合制','水务议会与行政官分工','配水公平与生态绩效')]
PROFILES=[('平原农耕','粮食与水利','洪旱交替','兴修水利与减免税赋'),('滨海航贸','航运与造船','风暴与贸易中断','救援船队与信用重建'),
 ('高原矿业','采矿与道路','矿难与道路断裂','工安整顿与运输保障'),('河谷学城','教育与档案','人才外流','扩大学额与知识共享'),
 ('林地药乡','林业与医药','疫病与森林退化','医疗支援与封育更新'),('沙洲商路','驿站与节水','缺水与商路阻断','公平配水与联合护路'),
 ('群岛渔国','渔业与海运','海难与资源衰退','救生体系与休渔补偿'),('雪岭工邦','机械与保温','寒灾与能源短缺','民生供暖与技术援助'),
 ('湖泽稻乡','稻作与湿地','堤坝失修','公开预算与生态治理'),('丘陵百工','手工业与集市','订单萎缩与质量事故','保障工匠与追溯责任')]

def records(m,db):
 refs={}
 for cat in ['countries','immortals','gods']:
  refs[cat]=[dict(id=r[0],url=r[1],title=r[2],body_sha256=r[3]) for r in db.execute(
   "SELECT id,url,title,latest FROM resources WHERE category=? AND source LIKE 'Kanripo %' ORDER BY id LIMIT 3",(cat,))]
 def draft(key,title,cat,payload):
  payload.update({'kind':'原创游戏设定草案','schema_version':1,'status':'待策划审核，未写入游戏',
   'reference_volumes':refs.get(cat,[]),'reference_use':'仅为命名、事件与职能的灵感线索；游戏机制与数值均为原创提案，非古籍史实。',
   'five_dimensions':'体是物质基础，劳是根本实践途径，德统领方向，智提供能力，美丰富精神。五维共同影响成长。'})
  return dict(url='qingyun://design/'+key,title=title,category=cat,source=m.DESIGN_SOURCE,
   license='原创草案；引用材料进入正式游戏前另行核对许可和版本。',revision='rules-v1',
   text=json.dumps(payload,ensure_ascii=False,sort_keys=True),review='设计提案与原始资料分开统计；未经玩家平衡测试。')
 for i,name in enumerate(IMMORTALS):
  yield draft('immortals/'+str(i+1),f'飞升等级 {i+1:02d} · {name}','immortals',
   {'rank':i+1,'name':name,'next':IMMORTALS[i+1] if i+1<len(IMMORTALS) else '候补神使',
    'gates':{'五维修为总量':500*(i+1)**2,'最低单维':30*(i+1),'实践任务':2*(i+1),'方向考验':'年度抉择与济世行为累计'},
    'failure':'保留修行进度，触发修复任务；不得靠单维刷点无条件晋级',
    'scope':'同一宇宙内修行；飞升后进入神职考核'} )
 for i,name in enumerate(GOD_RANKS):
  yield draft('god-ranks/'+str(i+1),f'神阶 {i+1:02d} · {name}','gods',
   {'rank':i+1,'name':name,'authority':'由乡域逐步扩至星域、法则议会；仍属于一个宇宙',
    'gates':{'履职功绩':1000*(i+1)**2,'治理周期':i+1,'最低五维均衡比':0.35},
    'promotion':'完成本级神职事件、跨领域协作与公议考核','next':GOD_RANKS[i+1] if i+1<len(GOD_RANKS) else '宇宙法则执掌者'})
 for i,(name,duty,crisis) in enumerate(DOMAINS):
  yield draft('domains/'+str(i+1),name+'神 · 神职草案','gods',
   {'domain':name,'duty':duty,'annual_event':crisis,'choices':['短期压制危机','公平分配资源并修复制度','向相邻神职求援并公开代价'],
    'decision_rule':'正确答案依资源、能力、损失与合作条件判定，不能固定选项序号。',
    'mechanism':'神阶决定权能范围，神职决定职责；同一神阶可以拥有不同神职。','conflict':'扩大神权须承担更高治理责任，失职可能降阶或更换神职'})
 prefixes=['青','云','玄','沧','霁','岚','昭','澜','岳','星']
 suffixes=['衡','宁','渊','川','原','泽','岐','岑','朔','辰']
 for i in range(100):
  a,b=divmod(i,10);name=prefixes[a]+suffixes[b]+'国';polity,checks,hiring=POLITIES[a];land,economy,crisis,response=PROFILES[b]
  yield draft('countries/'+str(i+1),f'百国 {i+1:03d} · {name}','countries',
   {'country_id':f'QY-{i+1:03d}','name':name,'polity':polity,'checks':checks,'civil_service':hiring,
    'geography':land,'economy':economy,'education':'学前、幼儿园、小学、中学、高等教育；年龄与学段匹配',
    'administration':['社区','县域','州域','中央'],'departments':['民政','教育','财政','水务','司法','工造'],
    'annual_crisis':crisis,'candidate_policy':response,'diplomacy':{'partner':f'QY-{(i+1)%100+1:03d}','tension':f'QY-{(i+17)%100+1:03d}'},
    'officer_mapping':'青云本国保留既有职级；其他国以职责范围映射，不把所有历史政体混成同一官制。',
    'population':'待人口模型与平衡设计；原青云国家15亿人口设定保持不变',
    'playable_difference':'政体决定任用约束，地理决定资源和灾害；两轴组合形成100国策划框架，尚需独立故事深化'})
 for cat,names in [('universe',['宇宙法则执掌者','万域协调者','宇宙秩序守护者','宇宙之主']),
                   ('multiverse',['界外行者','多宇宙联络者','世界群守护者','多元秩序共议者'])]:
  for i,name in enumerate(names):
   yield draft(cat+'/'+str(i+1),name+' · 后期等级草案',cat,
    {'rank':i+1,'name':name,'unlock':'完成至高神议席考核' if cat=='universe' else '先成为宇宙之主，才开放多元宇宙',
     'challenge':'在不同领域或宇宙的规则冲突中达成协作，承担资源与治理代价',
     'rule':'科普宇宙学只是灵感；跨宇宙权能是虚构机制，不声称科学已证实。'})

def organize(m,db):
 result={'new':0,'revision':0,'duplicate_source':0,'unchanged':0}
 for record in records(m,db):result[m.save(db,record)]+=1
 return result
