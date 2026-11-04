"""Compile reviewed ORIGINAL material-library proposals, never publicise private raw archives."""
import importlib.util,json,hashlib,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
source=root/'tools'/'material-drafts.py' # reviewed snapshot of qingyun-materials/designs.py
spec=importlib.util.spec_from_file_location('drafts',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
countries=[]
for i in range(100):
 a,b=divmod(i,10);p=m.POLITIES[a];g=m.PROFILES[b]
 countries.append(dict(id=i,name='澄川' if i==0 else '青云玄沧霁岚昭澜岳星'[a]+'衡宁渊川原泽岐岑朔辰'[b]+'国',polity=p[0],checks=p[1],hiring=p[2],land=g[0],economy=g[1],crisis=g[2],response=g[3],population=1500000000 if i==0 else (8+a*13+b*7)*1000000,affinity=b%5,partner=(i+1)%100,rival=(i+17)%100))
data=dict(schema=1,revision='worlds-0.7.0',provenance=dict(source='青云纪素材库原创设定草案',file='qingyun-materials/designs.py',sha256=hashlib.sha256(source.read_bytes()).hexdigest(),reviewed='2026-11-04',use='采用原创等级、政体及地理组合；事件、数值和世界规则为游戏原创。未复制私有采集正文。'),countries=countries,immortals=m.IMMORTALS,gods=m.GOD_RANKS,domains=[dict(name=x,duty=y,crisis=z,affinity=i%5) for i,(x,y,z) in enumerate(m.DOMAINS)],cosmic=['宇宙法则执掌者','万域协调者','宇宙秩序守护者','宇宙之主'],multiverse=['界外行者','多宇宙联络者','世界群守护者','多元秩序共议者'],planets=[dict(id=i,name=n,law=l,focus=i%5,hazard=h) for i,(n,l,h) in enumerate([('澄川星','五行均衡','灵脉淤塞'),('苍海星','潮汐共振','海陆争衡'),('赤曜星','焰能循环','火脉失控'),('玄冰星','热量守恒','长夜寒潮'),('森罗星','生灵共生','物种衰退'),('浮岚星','气流浮陆','浮岛坠落'),('金衡星','器道契约','工造垄断'),('玉沙星','水土节律','绿洲枯竭'),('镜月星','记忆映照','史籍分歧'),('雷泽星','雷磁流转','风暴迁移'),('太素星','灵气稀薄','资源争夺'),('归墟星','空间折叠','航路失联')])],universes=[dict(id=i,name=n,rule=r,focus=i%5) for i,(n,r) in enumerate([('青云本宇宙','五维共同成长'),('流光宇宙','时间流速差异'),('寂海宇宙','灵气潮涨潮落'),('镜尘宇宙','记忆决定认同'),('万木宇宙','生命互相依存'),('星炉宇宙','能量转换有代价'),('无声宇宙','意义依靠共识'),('重霄宇宙','重力塑造疆界'),('回环宇宙','历史周期重现')])])
(root/'dist/world-data.js').write_text('// Generated from original material-library proposals. Run python tools/build-worlds.py\nexport const WORLD='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
print('Compiled: 100 countries / 12 planets / 9 universes / 27 ranks / 20 divine domains')
