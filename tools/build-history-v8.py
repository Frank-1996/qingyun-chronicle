import json,pathlib
r=pathlib.Path(__file__).resolve().parents[1]
rows=json.loads((r/'tools/history-cases.json').read_text(encoding='utf8'))
keys=['id','name','date','fact','dilemma','options','explanation','url']
cases=[dict(zip(keys,row)) for row in rows]
assert len(cases)==32 and len({x['id'] for x in cases})==32
for c in cases:assert len(c['options'])==3 and c['url'].startswith('https://')
(r/'dist/history-cases.js').write_text('// 32 reviewed source-based cases. Scenarios and judgements are original adaptations.\nexport const CASES='+json.dumps(cases,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
print('32 cases / 512 age-role adaptations / 32 late-game historical scenarios')
