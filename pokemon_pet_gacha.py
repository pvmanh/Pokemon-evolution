#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pokémon Pet Gacha - single-file, dependency-free prototype.
Run: python pokemon_pet_gacha.py
Then open: http://127.0.0.1:8000

Uses only Python standard library. PokeAPI is optional: responses are cached locally,
and a built-in Gen 1/2 fallback keeps the game playable when the API is unavailable.
"""
import json, os, random, threading, time, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8000
ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "poke_cache"
SAVE = ROOT / "player_save.json"
CACHE.mkdir(exist_ok=True)

RARITY_RATE = {"Common": 70, "Rare": 22, "Epic": 7, "Legendary": 1}
GEN1_2 = list(range(1, 252))

# Reliable offline seed data. Online PokeAPI enriches these with real stats/sprites.
SEEDS = {
    1:("Bulbasaur",318,1,"Common"),2:("Ivysaur",405,1,"Rare"),3:("Venusaur",525,1,"Epic"),
    4:("Charmander",309,4,"Common"),5:("Charmeleon",405,4,"Rare"),6:("Charizard",534,4,"Epic"),
    7:("Squirtle",314,7,"Common"),8:("Wartortle",405,7,"Rare"),9:("Blastoise",530,7,"Epic"),
    10:("Caterpie",195,10,"Common"),11:("Metapod",205,10,"Common"),12:("Butterfree",395,10,"Common"),
    13:("Weedle",195,13,"Common"),14:("Kakuna",205,13,"Common"),15:("Beedrill",395,13,"Common"),
    16:("Pidgey",251,16,"Common"),17:("Pidgeotto",349,16,"Common"),18:("Pidgeot",479,16,"Rare"),
    19:("Rattata",253,19,"Common"),20:("Raticate",413,19,"Rare"),
    21:("Spearow",262,21,"Common"),22:("Fearow",442,21,"Rare"),
    23:("Ekans",288,23,"Common"),24:("Arbok",448,23,"Rare"),
    25:("Pikachu",320,25,"Rare"),26:("Raichu",485,25,"Rare"),
    27:("Sandshrew",300,27,"Common"),28:("Sandslash",450,27,"Rare"),
    37:("Vulpix",299,37,"Common"),38:("Ninetales",505,37,"Epic"),
    39:("Jigglypuff",270,39,"Common"),40:("Wigglytuff",435,39,"Rare"),
    41:("Zubat",245,41,"Common"),42:("Golbat",455,41,"Rare"),
    43:("Oddish",320,43,"Common"),44:("Gloom",395,43,"Common"),45:("Vileplume",490,43,"Rare"),
    54:("Psyduck",320,54,"Common"),55:("Golduck",500,54,"Epic"),
    58:("Growlithe",350,58,"Common"),59:("Arcanine",555,58,"Epic"),
    63:("Abra",310,63,"Common"),64:("Kadabra",400,63,"Rare"),65:("Alakazam",500,63,"Epic"),
    66:("Machop",305,66,"Common"),67:("Machoke",405,66,"Rare"),68:("Machamp",505,66,"Epic"),
    74:("Geodude",300,74,"Common"),75:("Graveler",390,74,"Common"),76:("Golem",495,74,"Rare"),
    92:("Gastly",310,92,"Common"),93:("Haunter",405,92,"Rare"),94:("Gengar",500,92,"Epic"),
    95:("Onix",385,95,"Common"),
    104:("Cubone",320,104,"Common"),105:("Marowak",425,104,"Rare"),
    113:("Chansey",450,113,"Rare"),
    115:("Kangaskhan",490,115,"Rare"),
    116:("Horsea",295,116,"Common"),117:("Seadra",440,116,"Rare"),
    120:("Staryu",340,120,"Common"),121:("Starmie",520,120,"Epic"),
    123:("Scyther",500,123,"Epic"),124:("Jynx",455,124,"Rare"),125:("Electabuzz",490,125,"Rare"),126:("Magmar",495,126,"Rare"),
    127:("Pinsir",500,127,"Epic"),128:("Tauros",490,128,"Rare"),
    129:("Magikarp",200,129,"Common"),130:("Gyarados",540,129,"Epic"),
    131:("Lapras",535,131,"Epic"),132:("Ditto",288,132,"Common"),
    133:("Eevee",325,133,"Rare"),134:("Vaporeon",525,133,"Epic"),135:("Jolteon",525,133,"Epic"),136:("Flareon",525,133,"Epic"),
    137:("Porygon",395,137,"Common"),
    138:("Omanyte",355,138,"Common"),139:("Omastar",495,138,"Rare"),140:("Kabuto",355,140,"Common"),141:("Kabutops",495,140,"Rare"),
    142:("Aerodactyl",515,142,"Epic"),143:("Snorlax",540,143,"Epic"),
    144:("Articuno",580,144,"Legendary"),145:("Zapdos",580,145,"Legendary"),146:("Moltres",580,146,"Legendary"),
    147:("Dratini",300,147,"Common"),148:("Dragonair",420,147,"Rare"),149:("Dragonite",600,147,"Legendary"),
    150:("Mewtwo",680,150,"Legendary"),151:("Mew",600,151,"Legendary"),
    152:("Chikorita",318,152,"Common"),153:("Bayleef",405,152,"Rare"),154:("Meganium",525,152,"Epic"),
    155:("Cyndaquil",309,155,"Common"),156:("Quilava",405,155,"Rare"),157:("Typhlosion",534,155,"Epic"),
    158:("Totodile",314,158,"Common"),159:("Croconaw",405,158,"Rare"),160:("Feraligatr",530,158,"Epic"),
    161:("Sentret",215,161,"Common"),162:("Furret",415,161,"Rare"),163:("Hoothoot",262,163,"Common"),164:("Noctowl",442,163,"Rare"),
    165:("Ledyba",265,165,"Common"),166:("Ledian",390,165,"Common"),167:("Spinarak",250,167,"Common"),168:("Ariados",400,167,"Rare"),
    169:("Crobat",535,41,"Epic"),170:("Chinchou",330,170,"Common"),171:("Lanturn",460,170,"Rare"),
    172:("Pichu",205,172,"Common"),173:("Cleffa",218,173,"Common"),174:("Igglybuff",210,174,"Common"),
    175:("Togepi",245,175,"Common"),176:("Togetic",405,175,"Rare"),
    177:("Natu",320,177,"Common"),178:("Xatu",470,177,"Rare"),179:("Mareep",280,179,"Common"),180:("Flaaffy",365,179,"Common"),181:("Ampharos",510,179,"Epic"),
    182:("Bellossom",490,43,"Rare"),183:("Marill",250,183,"Common"),184:("Azumarill",420,183,"Rare"),
    185:("Sudowoodo",410,185,"Rare"),186:("Politoed",500,60,"Epic"),187:("Hoppip",250,187,"Common"),188:("Skiploom",340,187,"Common"),189:("Jumpluff",460,187,"Rare"),
    190:("Aipom",360,190,"Common"),191:("Sunkern",180,191,"Common"),192:("Sunflora",425,191,"Rare"),
    193:("Yanma",390,193,"Common"),194:("Wooper",210,194,"Common"),195:("Quagsire",430,194,"Rare"),
    196:("Espeon",525,133,"Epic"),197:("Umbreon",525,133,"Epic"),198:("Murkrow",405,198,"Rare"),199:("Slowking",490,79,"Rare"),
    200:("Misdreavus",435,200,"Rare"),201:("Unown",336,201,"Common"),202:("Wobbuffet",405,202,"Rare"),
    203:("Girafarig",455,203,"Rare"),204:("Pineco",290,204,"Common"),205:("Forretress",465,204,"Rare"),
    206:("Dunsparce",415,206,"Rare"),207:("Gligar",430,207,"Rare"),208:("Steelix",510,95,"Epic"),
    209:("Snubbull",300,209,"Common"),210:("Granbull",450,209,"Rare"),211:("Qwilfish",440,211,"Rare"),212:("Scizor",500,123,"Epic"),
    213:("Shuckle",505,213,"Epic"),214:("Heracross",500,214,"Epic"),215:("Sneasel",430,215,"Rare"),216:("Teddiursa",330,216,"Common"),217:("Ursaring",500,216,"Epic"),
    218:("Slugma",250,218,"Common"),219:("Magcargo",410,218,"Rare"),220:("Swinub",250,220,"Common"),221:("Piloswine",450,220,"Rare"),
    222:("Corsola",410,222,"Rare"),223:("Remoraid",300,223,"Common"),224:("Octillery",480,223,"Rare"),225:("Delibird",330,225,"Common"),
    226:("Mantine",485,226,"Rare"),227:("Skarmory",465,227,"Rare"),228:("Houndour",330,228,"Common"),229:("Houndoom",500,228,"Epic"),
    230:("Kingdra",540,116,"Epic"),231:("Phanpy",330,231,"Common"),232:("Donphan",500,231,"Epic"),
    233:("Porygon2",515,137,"Epic"),234:("Stantler",465,234,"Rare"),235:("Smeargle",250,235,"Common"),
    236:("Tyrogue",210,236,"Common"),237:("Hitmontop",455,236,"Rare"),238:("Smoochum",305,124,"Common"),239:("Elekid",360,125,"Common"),240:("Magby",365,126,"Common"),
    241:("Miltank",490,241,"Rare"),242:("Blissey",540,113,"Epic"),243:("Raikou",580,243,"Legendary"),244:("Entei",580,244,"Legendary"),245:("Suicune",580,245,"Legendary"),
    246:("Larvitar",300,246,"Common"),247:("Pupitar",410,246,"Rare"),248:("Tyranitar",600,246,"Legendary"),249:("Lugia",680,249,"Legendary"),250:("Ho-Oh",680,250,"Legendary"),251:("Celebi",600,251,"Legendary")
}

# Evolution families: enough to make the virtual-pet progression deterministic offline.
EVOLUTIONS = {
  1:[(2,16),(3,32)],4:[(5,16),(6,36)],7:[(8,16),(9,36)],10:[(11,7),(12,10)],13:[(14,7),(15,10)],
  16:[(17,18),(18,36)],19:[(20,20)],21:[(22,20)],23:[(24,22)],25:[(26,20)],27:[(28,22)],37:[(38,25)],
  39:[(40,25)],41:[(42,22),(169,40)],43:[(44,21),(45,36),(182,36)],54:[(55,33)],58:[(59,36)],63:[(64,16),(65,40)],
  66:[(67,28),(68,40)],74:[(75,25),(76,40)],92:[(93,25),(94,40)],104:[(105,28)],116:[(117,32),(230,40)],120:[(121,30)],
  129:[(130,20)],133:[(134,20),(135,20),(136,20),(196,20),(197,20)],138:[(139,40)],140:[(141,40)],147:[(148,30),(149,55)],
  152:[(153,16),(154,32)],155:[(156,14),(157,36)],158:[(159,18),(160,30)],161:[(162,15)],163:[(164,20)],165:[(166,18)],
  167:[(168,22)],170:[(171,27)],172:[(25,20)],173:[(35,20)],174:[(40,20)],175:[(176,20)],177:[(178,25)],179:[(180,15),(181,30)],
  183:[(184,18)],187:[(188,18),(189,27)],191:[(192,20)],194:[(195,20)],198:[],203:[],204:[(205,31)],209:[(210,23)],
  211:[],213:[],214:[],215:[],216:[(217,30)],218:[(219,38)],220:[(221,33)],223:[(224,25)],228:[(229,24)],231:[(232,25)],
  236:[(237,20)],246:[(247,30),(248,55)]
}

state_lock = threading.RLock()
def default_player():
    return {"player_id":"demo_player","coins":1000,"gacha_tickets":10,"party":[],"pending":None,"selected_slot":1}

def load_player():
    if SAVE.exists():
        try:
            p=json.loads(SAVE.read_text(encoding="utf-8"));
            # Defensive migration / repair.
            base=default_player(); base.update(p)
            base["party"]=base.get("party") or []
            return base
        except Exception: pass
    return default_player()
PLAYER=load_player()

def save_player():
    tmp=SAVE.with_suffix('.tmp')
    tmp.write_text(json.dumps(PLAYER,ensure_ascii=False,indent=2),encoding='utf-8'); os.replace(tmp,SAVE)

def cached_json(key):
    f=CACHE/(key.replace('/','_')+'.json')
    if f.exists():
        try: return json.loads(f.read_text(encoding='utf-8'))
        except Exception: pass

def api_json(path):
    key=path.strip('/').replace('/','_')
    c=cached_json(key)
    if c is not None: return c
    try:
        req=urllib.request.Request('https://pokeapi.co/api/v2/'+path.strip('/'),headers={'User-Agent':'PokemonPetGacha/2.0'})
        with urllib.request.urlopen(req,timeout=7) as r: data=json.loads(r.read().decode('utf-8'))
        (CACHE/(key+'.json')).write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
        return data
    except Exception: return None

def fallback_sprite(pid):
    # Local data URI fallback; no external asset dependency.
    name=SEEDS.get(pid,(f'Pokemon {pid}',300,pid,'Common'))[0]
    hue=(pid*47)%360
    import html
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240"><rect width="240" height="240" rx="30" fill="#111827"/><circle cx="120" cy="105" r="62" fill="hsl({hue},65%,58%)"/><circle cx="95" cy="92" r="10" fill="#fff"/><circle cx="145" cy="92" r="10" fill="#fff"/><circle cx="95" cy="92" r="5"/><circle cx="145" cy="92" r="5"/><path d="M90 125 Q120 150 150 125" fill="none" stroke="#111827" stroke-width="7" stroke-linecap="round"/><text x="120" y="205" text-anchor="middle" font-family="sans-serif" font-size="18" fill="white">{html.escape(name)}</text></svg>'''
    import base64
    return 'data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()

def pokemon(pid):
    # Seed data is the authoritative offline gameplay dataset. We only use PokeAPI
    # opportunistically for richer sprites/stats; a slow/unavailable API never blocks gameplay.
    n, bstv, sid, rarity = SEEDS.get(pid, (f"Pokemon {pid}", 300, pid, "Common"))
    remote = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pid}.png"
    data = api_json(f"pokemon/{pid}")
    if data:
        stats = sum(x.get('base_stat', 0) for x in data.get('stats', []))
        species_url = data.get('species', {}).get('url', '')
        sid2 = int(species_url.rstrip('/').split('/')[-1]) if species_url else sid
        species = api_json(f"pokemon-species/{sid2}") or {}
        legendary = species.get('is_legendary', False) or species.get('is_mythical', False)
        if legendary or stats >= 600: rarity = 'Legendary'
        elif stats >= 500: rarity = 'Epic'
        elif stats >= 400: rarity = 'Rare'
        else: rarity = 'Common'
        n = data.get('name', n).title(); bstv = stats; sid = sid2
        remote = (((data.get('sprites', {}).get('other') or {}).get('official-artwork') or {}).get('front_default')
                  or data.get('sprites', {}).get('front_default') or remote)
    return {'pokemon_id': pid, 'species_id': sid, 'name': n, 'rarity': rarity, 'bst': bstv,
            'sprite': remote, 'fallback_sprite': fallback_sprite(pid)}

def pokemon_fast(pid):
    # Zero-network path used by Gacha. This fixes the old rejection-sampling/network timeout bug.
    n, bstv, sid, rarity = SEEDS.get(pid, (f"Pokemon {pid}", 300, pid, 'Common'))
    return {'pokemon_id': pid, 'species_id': sid, 'name': n, 'rarity': rarity, 'bst': bstv,
            'sprite': f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pid}.png",
            'fallback_sprite': fallback_sprite(pid)}

def roll_rarity(): return random.choices(list(RARITY_RATE),weights=list(RARITY_RATE.values()),k=1)[0]

def gacha():
    # Roll rarity once, then choose directly from the bundled Gen 1/2 pool.
    # No rejection sampling and no live API loop: Gacha is instant and deterministic in structure.
    target = roll_rarity()
    ids = [pid for pid, v in SEEDS.items() if v[3] == target]
    if not ids:
        target = 'Common'; ids = [pid for pid, v in SEEDS.items() if v[3] == target]
    p = pokemon_fast(random.choice(ids))
    p.update(level=1, exp=0, health=100, energy=100, happiness=100, friendship=0,
             last_update=int(time.time()), uid=f"{random.randrange(16**8):08x}")
    return p

def exp_required(level): return max(50,level*level*50)
def decay(p):
    now=int(time.time()); last=int(p.get('last_update',now)); minutes=max(0,(now-last)//60)
    if minutes:
        p['energy']=max(0,p.get('energy',100)-minutes)
        p['happiness']=max(0,p.get('happiness',100)-max(1,minutes//2))
        if p['energy']==0: p['health']=max(0,p.get('health',100)-max(1,minutes//5))
        p['last_update']=now

def add_exp(p,amount):
    p['exp']=int(p.get('exp',0))+amount
    leveled=False
    while p['level']<100 and p['exp']>=exp_required(p['level']):
        p['exp']-=exp_required(p['level']); p['level']+=1; leveled=True
        p['health']=min(100,p['health']+5); p['energy']=min(100,p['energy']+5); p['happiness']=min(100,p['happiness']+10)
    return leveled

def interact(p,action):
    if action=='feed': p['energy']=min(100,p['energy']+15); p['happiness']=min(100,p['happiness']+5); gain=10
    elif action=='play': p['happiness']=min(100,p['happiness']+12); p['energy']=max(0,p['energy']-5); gain=12
    elif action=='pet': p['happiness']=min(100,p['happiness']+8); p['friendship']=min(255,p['friendship']+3); gain=5
    else: raise ValueError('Action không hỗ trợ')
    return add_exp(p,gain)

def evolve(p):
    sid=int(p['species_id']); options=EVOLUTIONS.get(sid,[])
    eligible=[(nid,lvl) for nid,lvl in options if p['level']>=lvl]
    if not eligible: return None
    nid,_=eligible[0]; old=p['name']; q=pokemon(nid)
    p.update({k:q[k] for k in ('pokemon_id','species_id','name','rarity','bst','sprite','fallback_sprite')})
    p['last_update']=int(time.time())
    return {'from':old,'to':p['name'],'level':p['level']}

def public_state():
    for p in PLAYER['party']: decay(p)
    return PLAYER

HTML='''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pokémon Pet Gacha</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b1020;color:#f4f7ff;font-family:system-ui,-apple-system,Segoe UI,sans-serif}.app{max-width:1100px;margin:auto;padding:16px}header{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:18px;border-radius:20px;background:#171f33;border:1px solid #293754;margin-bottom:16px}h1{margin:0;font-size:26px}.wallet{font-weight:800}.party{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card,.empty{background:#171f33;border:1px solid #293754;border-radius:18px;padding:14px;min-height:330px}.card{cursor:pointer;transition:.15s}.card.selected{outline:2px solid #7dd3fc;transform:translateY(-2px)}.empty{display:grid;place-items:center;color:#71809b}.sprite{height:150px;width:100%;object-fit:contain}.name{font-weight:900;font-size:19px}.meta{display:flex;justify-content:space-between;color:#aeb9ca;font-size:13px}.bar{height:9px;background:#303b51;border-radius:9px;overflow:hidden;margin:5px 0 9px}.fill{height:100%;width:0%;transition:.2s}.hp{background:#ef4444}.en{background:#f59e0b}.ha{background:#22c55e}.actions{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:16px 0}.actions button,.gacha button,.modal button{border:0;border-radius:14px;padding:13px 20px;font-weight:900;cursor:pointer;background:#263554;color:#fff}.gacha{text-align:center;padding:22px;background:#171f33;border-radius:18px;border:1px solid #293754}.gacha button{font-size:20px;padding:16px 32px;background:#7c3aed}.status{min-height:24px;color:#aeb9ca}.modal{position:fixed;inset:0;background:#000b;display:grid;place-items:center;padding:20px;z-index:5}.hidden{display:none}.modal-card{background:#121a2b;border:1px solid #3b4b69;border-radius:20px;padding:24px;max-width:560px;width:100%;text-align:center}.modal-card img{width:180px;height:180px;object-fit:contain}.choices{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:14px}.small{font-size:12px;color:#7f8ba2}@media(max-width:750px){.party{grid-template-columns:repeat(2,1fr)}header{flex-direction:column;align-items:flex-start}}@media(max-width:470px){.party{grid-template-columns:1fr}.choices{grid-template-columns:repeat(2,1fr)}}
</style></head><body><div class="app"><header><div><h1>⚡ Pokémon Pet</h1><small>Virtual Pet × Gacha · Gen 1–2</small></div><div class="wallet">💰 <span id="coins">0</span> · 🎟 <span id="tickets">0</span> · ❤️ <span id="count">0</span>/6</div></header><main><section class="party" id="party"></section><section class="actions"><button data-action="feed">🍓 Feed</button><button data-action="play">🎮 Play</button><button data-action="pet">❤️ Pet</button><button id="evolveBtn">✨ Evolve</button></section><section class="gacha"><button id="gachaBtn">🎲 GACHA ×1</button><p class="status" id="status">Đang tải...</p><div class="small">Không cần FastAPI, httpx hay .venv. Dữ liệu game được lưu local.</div></section></main></div><div class="modal hidden" id="modal"><div class="modal-card"><div id="modalContent"></div></div></div><script>
let state=null,selectedSlot=1;const $=id=>document.getElementById(id),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
function pct(v){return Math.max(0,Math.min(100,Number(v)||0))}function bar(label,v,cls){return `<div>${label} ${v}</div><div class="bar"><div class="fill ${cls}" style="width:${pct(v)}%"></div></div>`}
async function api(path,body){const r=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});const d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d}
function render(){if(!state)return;$('coins').textContent=state.coins;$('tickets').textContent=state.gacha_tickets;$('count').textContent=state.party.length;$('party').innerHTML='';for(let i=1;i<=6;i++){const p=state.party[i-1];if(!p){$('party').innerHTML+=`<div class="empty">PET SLOT ${i}<br>Trống</div>`;continue}$('party').innerHTML+=`<article class="card ${selectedSlot===i?'selected':''}" data-slot="${i}"><img class="sprite" src="${p.sprite}" data-fallback="${p.fallback_sprite}" alt="${esc(p.name)}"><div class="name">${esc(p.name)}</div><div class="meta"><span>⭐ ${esc(p.rarity)}</span><span>Lv.${p.level}</span></div>${bar('❤️ HP',p.health,'hp')}${bar('⚡ Energy',p.energy,'en')}${bar('😊 Happiness',p.happiness,'ha')}<div class="meta"><span>EXP ${p.exp}</span><span>♥ ${p.friendship}</span></div></article>`}document.querySelectorAll('.card').forEach(c=>c.onclick=()=>{selectedSlot=Number(c.dataset.slot);render()});document.querySelectorAll('img[data-fallback]').forEach(img=>img.onerror=()=>{if(img.src!==img.dataset.fallback){img.src=img.dataset.fallback}})}
function showPending(p){$('modalContent').innerHTML=`<h2>🎉 Pokémon mới!</h2><img src="${p.sprite}" data-fallback="${p.fallback_sprite}"><h2>${esc(p.name)}</h2><b>⭐ ${esc(p.rarity)}</b><p>Party đã đủ 6 Pokémon.</p><div class="choices"><button id="release">Thả</button>${[1,2,3,4,5,6].map(i=>`<button data-swap="${i}">Đổi Slot ${i}</button>`).join('')}</div>`;$('modal').classList.remove('hidden');$('release').onclick=async()=>{await api('/api/release',{ });state=await api('/api/state');$('modal').classList.add('hidden');render()};document.querySelectorAll('[data-swap]').forEach(b=>b.onclick=async()=>{state=await api('/api/swap',{slot:Number(b.dataset.swap)});$('modal').classList.add('hidden');render()})}
async function refresh(){try{state=await api('/api/state');render();$('status').textContent='Sẵn sàng';}catch(e){$('status').textContent='Lỗi tải game: '+e.message}}
$('gachaBtn').onclick=async()=>{if($('gachaBtn').disabled)return;$('gachaBtn').disabled=true;$('status').textContent='Đang quay...';try{const r=await api('/api/gacha',{});state=r.player;if(r.full)showPending(r.pokemon);else render();$('status').textContent=`🎉 ${r.pokemon.name} · ${r.pokemon.rarity}`;}catch(e){$('status').textContent='❌ '+e.message}finally{$('gachaBtn').disabled=false}};
document.querySelectorAll('.actions button[data-action]').forEach(b=>b.onclick=async()=>{if(!state?.party?.length)return;try{const r=await api('/api/action',{action:b.dataset.action,slot:selectedSlot});state=r.player;render();$('status').textContent=r.leveled?'⬆️ Level Up!':'Đã thực hiện '+b.textContent}catch(e){$('status').textContent='❌ '+e.message}});$('evolveBtn').onclick=async()=>{if(!state?.party?.length)return;try{const r=await api('/api/evolve',{slot:selectedSlot});state=r.player;render();$('status').textContent=r.evolved?`✨ ${r.evolved.from} → ${r.evolved.to}`:r.message}catch(e){$('status').textContent='❌ '+e.message}};
refresh();setInterval(refresh,15000);
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,fmt,*args): pass
    def send_json(self,obj,status=200):
        raw=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def send_html(self):
        raw=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def read_json(self):
        n=int(self.headers.get('Content-Length','0')); return json.loads(self.rfile.read(n) or b'{}')
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/': return self.send_html()
        if path=='/health': return self.send_json({'ok':True,'server':'single-file','python':os.sys.version.split()[0]})
        if path=='/api/state':
            with state_lock: return self.send_json(public_state())
        if path=='/api/test':
            # Pure local smoke test: no network dependency.
            sample=gacha()
            ok=(sample['rarity'] in RARITY_RATE and bool(sample['sprite']) and bool(sample['fallback_sprite'])
                and len(SEEDS) >= 100 and sum(RARITY_RATE.values()) == 100)
            return self.send_json({'ok':ok,'gacha':sample['name'],'rarity':sample['rarity'],'seed_count':len(SEEDS)})
        self.send_json({'error':'Not found'},404)
    def do_POST(self):
        path=urlparse(self.path).path
        try:
            data=self.read_json()
            with state_lock:
                if path=='/api/gacha':
                    if PLAYER['gacha_tickets']<=0: raise ValueError('Không còn vé Gacha.')
                    PLAYER['gacha_tickets']-=1; p=gacha(); full=len(PLAYER['party'])>=6
                    if full: PLAYER['pending']=p
                    else: p['slot']=len(PLAYER['party'])+1;PLAYER['party'].append(p)
                    save_player();return self.send_json({'pokemon':p,'full':full,'player':public_state()})
                if path=='/api/release': PLAYER['pending']=None;save_player();return self.send_json(PLAYER)
                if path=='/api/swap':
                    slot=int(data.get('slot',0));
                    if not PLAYER.get('pending') or not 1<=slot<=6: raise ValueError('Slot không hợp lệ.')
                    incoming=PLAYER['pending'];incoming['slot']=slot;PLAYER['party'][slot-1]=incoming;PLAYER['pending']=None;save_player();return self.send_json(PLAYER)
                if path=='/api/action':
                    slot=int(data.get('slot',0));
                    if not 1<=slot<=len(PLAYER['party']): raise ValueError('Chưa có Pokémon ở slot này.')
                    p=PLAYER['party'][slot-1];decay(p);leveled=interact(p,str(data.get('action')));p['last_update']=int(time.time());save_player();return self.send_json({'player':public_state(),'leveled':leveled})
                if path=='/api/evolve':
                    slot=int(data.get('slot',0));
                    if not 1<=slot<=len(PLAYER['party']): raise ValueError('Slot không hợp lệ.')
                    p=PLAYER['party'][slot-1];decay(p);ev=evolve(p);save_player();return self.send_json({'player':public_state(),'evolved':ev,'message':'Chưa đủ level để tiến hóa.' if not ev else ''})
                raise ValueError('Not found')
        except ValueError as e:self.send_json({'error':str(e)},400)
        except Exception as e:self.send_json({'error':'Server error: '+str(e)},500)

def main():
    print(f'Pokémon Pet Gacha — http://{HOST}:{PORT}')
    print('Single Python file / standard library only / no .venv required.')
    print('Stop with Ctrl+C.')
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
if __name__=='__main__': main()
