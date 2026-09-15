from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import sqlite3, os, secrets, string, time, re

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), 'game.db')

QUESTIONS = {
1:{'title':'1-кезең. Бәйге','type':'mc','q':'Көсемше тұлғалы сөзді табыңыз.','options':['оқыған','оқып','оқушы','оқиды'],'correct':1,'points':5},
2:{'title':'2-кезең. Тіл сыры','type':'mc','q':'«Күн бұлттанғандықтан, біз жолға шықпадық» сөйлемінің түрін анықтаңыз.','options':['Мезгіл бағыныңқылы сабақтас','Себеп бағыныңқылы сабақтас','Шартты бағыныңқылы сабақтас','Қарсылықты салалас'],'correct':1,'points':5},
3:{'title':'3-кезең. Сөз құрастыр','type':'text','q':'Аралас әріптерден сөз құраңыз: Л А Қ А М','answers':['қалам'],'points':5},
4:{'title':'4-кезең. Мақалды жалғастыр','type':'mc','q':'«Өнер алды — ...» мақалының жалғасын табыңыз.','options':['қызыл тіл','бірлік','білім','еңбек'],'correct':0,'points':5},
5:{'title':'5-кезең. Сөз шебері','type':'words','q':'«ҚАЗАҚСТАН» сөзінің әріптерінен кемінде 6 мағыналы сөз жазыңыз. Сөздерді үтірмен бөліңіз.','valid':['қазақ','қаз','қазан','таза','зат','сан','сана','санақ','санат','ата','ана','ат','аз','азат','ақ','сақ','ас','тас','тақ','таң','асқақ','астана','сақтан','қазақтан','тан','қан','қас','қақ','қат','ақта','атақ','нақ','наз'],'points':6},
6:{'title':'6-кезең. Сөйлемді түзет','type':'text','q':'Берілген ойды әдеби нормаға сай жазыңыз: «Бала доп ойнады».','answers':['бала доп ойнады','бала доппен ойнады'],'points':5},
7:{'title':'7-кезең. Тіл шешендері','type':'essay','q':'«Тіл – білім – болашақ» сөздерін қатыстырып, мағыналы екі құрмалас сөйлем жазыңыз.','points':9},
8:{'title':'СУПЕРФИНАЛ','type':'mc','q':'«Төбе шашы тік тұрды» тұрақты тіркесінің мағынасын табыңыз.','options':['қатты қуанды','қатты қорықты','ренжіді','ұялып қалды'],'correct':1,'points':3}
}

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    c=db(); c.executescript('''
    CREATE TABLE IF NOT EXISTS rooms(code TEXT PRIMARY KEY,current_round INTEGER NOT NULL DEFAULT 1,created_at REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS teams(id INTEGER PRIMARY KEY AUTOINCREMENT,room TEXT NOT NULL,name TEXT NOT NULL,UNIQUE(room,name));
    CREATE TABLE IF NOT EXISTS answers(id INTEGER PRIMARY KEY AUTOINCREMENT,room TEXT NOT NULL,team TEXT NOT NULL,round_no INTEGER NOT NULL,points INTEGER NOT NULL,detail TEXT,UNIQUE(room,team,round_no));
    '''); c.commit(); c.close()
init_db()

def make_room():
    alphabet=string.ascii_uppercase+string.digits
    while True:
        code=''.join(secrets.choice(alphabet) for _ in range(5)); c=db()
        try:
            c.execute('INSERT INTO rooms(code,current_round,created_at) VALUES(?,?,?)',(code,1,time.time())); c.commit(); c.close(); return code
        except sqlite3.IntegrityError: c.close()

def norm(s):
    s=(s or '').lower(); s=re.sub(r'[.,!?;:—–-]',' ',s); return re.sub(r'\s+',' ',s).strip()

def score_answer(r,payload):
    q=QUESTIONS[r]; typ=q['type']
    if typ=='mc':
        try: idx=int(payload.get('answer',-1))
        except: idx=-1
        return (q['points'] if idx==q['correct'] else 0, q['options'][idx] if 0<=idx<len(q['options']) else '')
    if typ=='text':
        ans=str(payload.get('answer','')).strip(); return (q['points'] if any(norm(ans)==norm(x) for x in q['answers']) else 0, ans)
    if typ=='words':
        raw=str(payload.get('answer','')); words=[]
        for x in re.split(r'[,;\n]+',raw):
            x=norm(x)
            if x and x not in words: words.append(x)
        accepted=[w for w in words if w in q['valid']]
        return (min(q['points'],len(accepted)),'Қабылданған сөздер: '+', '.join(accepted))
    if typ=='essay':
        ans=str(payload.get('answer','')).strip(); n=norm(ans); pts=0
        if all(w in n for w in ['тіл','білім','болашақ']): pts+=4
        if len(re.findall(r'[.!?]',ans))>=2 or len(ans)>90: pts+=3
        if len(ans)>=60: pts+=2
        return (min(q['points'],pts),ans)
    return (0,'')

CSS='''body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:linear-gradient(135deg,#e0f2fe,#fef3c7);color:#172033}header{background:linear-gradient(90deg,#173ea5,#2563eb,#0ea5e9);color:#fff;padding:20px;text-align:center;border-bottom:5px solid #f59e0b}.wrap{max-width:980px;margin:20px auto;padding:0 12px}.card{background:#fff;border-radius:20px;padding:18px;box-shadow:0 12px 30px #0002;margin-bottom:14px}input,textarea{width:100%;padding:13px;border:1px solid #cbd5e1;border-radius:12px;font-size:16px;margin:7px 0;box-sizing:border-box}button,.btn{display:inline-block;border:0;border-radius:12px;padding:12px 15px;background:#1d4ed8;color:white;font-weight:800;font-size:15px;cursor:pointer;text-decoration:none}.green{background:#16a34a}.red{background:#dc2626}.option{padding:12px;margin:8px 0;background:#f1f5f9;border:2px solid transparent;border-radius:12px;cursor:pointer}.option.sel{border-color:#2563eb;background:#dbeafe}.hidden{display:none}.ok{color:#16a34a;font-weight:800}.bad{color:#dc2626;font-weight:800}.badge{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:999px;padding:7px 10px;font-weight:800}.score{font-size:20px;font-weight:900;color:#166534}table{width:100%;border-collapse:collapse}th,td{padding:12px;border-bottom:1px solid #e2e8f0;text-align:left}th{background:#dbeafe}.big{font-size:24px;font-weight:900}.linkbox{background:#ecfdf5;border:2px solid #86efac;border-radius:16px;padding:16px}.studentlink{font-size:20px;font-weight:900;color:#166534;word-break:break-all}'''

HOME='''<!doctype html><html lang="kk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Тіл білгірлері LIVE</title><style>{{css}}</style></head><body><header><h1>🏆 ТІЛ БІЛГІРЛЕРІ LIVE</h1><div>7–9 сынып • онлайн командалық сайыс</div></header><div class="wrap"><div class="card"><h2>Мұғалімге</h2><p>Жаңа сайыс бөлмесін ашыңыз.</p><a class="btn green" href="/new-room">Жаңа бөлме ашу</a></div><div class="card"><h2>Командаға</h2><form action="/join" method="get"><label>Бөлме коды</label><input name="room" maxlength="5" placeholder="Мысалы: A7K2P" required><button>Кіру</button></form></div></div></body></html>'''

TEACHER='''<!doctype html><html lang="kk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Мұғалім панелі</title><style>{{css}}</style></head><body><header><h1>🏆 ТІЛ БІЛГІРЛЕРІ — МҰҒАЛІМ ПАНЕЛІ</h1></header><div class="wrap"><div class="card linkbox"><h2>📱 Оқушыларға жіберетін сілтеме</h2><div id="studentLink" class="studentlink"></div><p>Бөлме коды: <b class="big">{{room}}</b></p><button class="green" onclick="copyLink()">Сілтемені көшіру</button> <span id="copyMsg"></span></div><div class="card"><div class="big">Қазіргі кезең: <span id="rnum"></span> — <span id="rtitle"></span></div><div id="buttons"></div></div><div class="card"><h2>📊 LIVE рейтинг</h2><table><thead><tr><th>Орын</th><th>Команда</th><th>Ұпай</th><th>Кезең</th></tr></thead><tbody id="tb"></tbody></table></div><div class="card"><button class="red" onclick="resetAll()">Сайысты тазалау</button></div></div><script>
const room={{room|tojson}},titles={1:'Бәйге',2:'Тіл сыры',3:'Сөз құрастыр',4:'Мақалды жалғастыр',5:'Сөз шебері',6:'Сөйлемді түзет',7:'Тіл шешендері',8:'Суперфинал'};const studentURL=location.origin+'/play/'+room;studentLink.textContent=studentURL;
async function api(p,d){let o={};if(d)o={method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)};return await(await fetch(p,o)).json()} async function setR(r){await api('/api/set-round',{room,round:r});refresh()} async function resetAll(){if(confirm('Осы бөлмедегі командалар мен ұпайлар өшірілсін бе?')){await api('/api/reset',{room});refresh()}} async function copyLink(){try{await navigator.clipboard.writeText(studentURL);copyMsg.textContent='✅ Көшірілді'}catch(e){copyMsg.textContent='Сілтемені қолмен көшіріңіз'}} async function refresh(){const s=await api('/api/state?room='+encodeURIComponent(room));rnum.textContent=s.round;rtitle.textContent=titles[s.round];buttons.innerHTML=Object.keys(titles).map(x=>`<button class="${+x===s.round?'green':''}" onclick="setR(${x})">${x}. ${titles[x]}</button>`).join('');const a=[...s.teams].sort((x,y)=>y.score-x.score);tb.innerHTML=a.length?a.map((t,i)=>`<tr><td>${i==0?'🥇':i==1?'🥈':i==2?'🥉':i+1}</td><td><b>${t.name}</b></td><td class="big">${t.score}</td><td>${t.done}</td></tr>`).join(''):'<tr><td colspan="4">Командалар әлі қосылған жоқ.</td></tr>'}refresh();setInterval(refresh,1200);
</script></body></html>'''

PLAY='''<!doctype html><html lang="kk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Тіл білгірлері LIVE</title><style>{{css}}</style></head><body><header><h1>🏆 ТІЛ БІЛГІРЛЕРІ LIVE</h1><div>Бөлме: {{room}}</div></header><div class="wrap"><div class="card" id="joinCard"><h2>Команда ретінде қосылу</h2><input id="teamName" placeholder="Команда атауы"><button onclick="joinTeam()">Сайысқа қосылу</button><div id="joinMsg"></div></div><div class="card hidden" id="gameCard"><span class="badge" id="roundBadge"></span><h2 id="roundTitle"></h2><div>Команда: <b id="teamLabel"></b></div><div class="score">Жалпы ұпай: <span id="score">0</span></div><hr><div id="task"></div><div id="result"></div></div></div><script>
const room={{room|tojson}},QUESTIONS={{questions|tojson}};let team=localStorage.getItem('tilTeam_'+room)||'',currentRound=0,submittedRounds=JSON.parse(localStorage.getItem('submittedRounds_'+room)||'{}');function norm(s){return(s||'').toLowerCase().replace(/[.,!?;:—–-]/g,' ').replace(/\s+/g,' ').trim()} async function api(path,data){let o={};if(data)o={method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)};return await(await fetch(path,o)).json()} async function joinTeam(){const n=teamName.value.trim();if(!n){joinMsg.innerHTML='<p class="bad">Команда атауын жазыңыз.</p>';return}const x=await api('/api/join',{room,team:n});if(x.ok){team=n;localStorage.setItem('tilTeam_'+room,team);showGame()}else joinMsg.innerHTML='<p class="bad">'+x.error+'</p>'} function showGame(){joinCard.classList.add('hidden');gameCard.classList.remove('hidden');teamLabel.textContent=team;refresh()} function renderTask(r){const q=QUESTIONS[r];roundBadge.textContent='Кезең '+r;roundTitle.textContent=q.title;if(submittedRounds[r]){task.innerHTML='<p class="ok">✅ Бұл кезеңнің жауабы жіберілді. Келесі кезеңді күтіңіз.</p>';return}if(q.type==='mc'){task.innerHTML=`<p><b>${q.q}</b></p>`+q.options.map((o,i)=>`<div class="option" data-i="${i}" onclick="pick(this)">${o}</div>`).join('')+`<button onclick="submitMC()">Жауапты жіберу</button>`}else if(q.type==='text'){task.innerHTML=`<p><b>${q.q}</b></p><input id="ans"><button onclick="submitText()">Жауапты жіберу</button>`}else if(q.type==='words'){task.innerHTML=`<p><b>${q.q}</b></p><textarea id="ans" rows="4"></textarea><button onclick="submitWords()">Жауапты жіберу</button>`}else{task.innerHTML=`<p><b>${q.q}</b></p><textarea id="ans" rows="6"></textarea><button onclick="submitEssay()">Жауапты жіберу</button>`}} function pick(el){document.querySelectorAll('.option').forEach(x=>x.classList.remove('sel'));el.classList.add('sel')} async function send(answer){const x=await api('/api/submit',{room,team,round:currentRound,answer});if(x.ok){submittedRounds[currentRound]=true;localStorage.setItem('submittedRounds_'+room,JSON.stringify(submittedRounds));result.innerHTML=`<p class="ok">✅ Жауап қабылданды. +${x.points} ұпай</p>`;renderTask(currentRound);refresh()}else result.innerHTML='<p class="bad">'+x.error+'</p>'} function submitMC(){const el=document.querySelector('.option.sel');if(!el){result.innerHTML='<p class="bad">Жауапты таңдаңыз.</p>';return}send(+el.dataset.i)} function submitText(){send(ans.value.trim())} function submitWords(){send(ans.value.trim())} function submitEssay(){send(ans.value.trim())} async function refresh(){if(!team)return;const s=await api('/api/state?room='+encodeURIComponent(room));currentRound=s.round;const me=s.teams.find(t=>t.name===team);score.textContent=me?me.score:0;if(currentRound!==window._r){window._r=currentRound;result.innerHTML='';renderTask(currentRound)}} if(team)showGame();setInterval(refresh,1500);
</script></body></html>'''

@app.route('/')
def home(): return render_template_string(HOME,css=CSS)
@app.route('/new-room')
def new_room(): return redirect(url_for('teacher',room=make_room()))
@app.route('/teacher/<room>')
def teacher(room):
    room=room.upper(); c=db(); row=c.execute('SELECT code FROM rooms WHERE code=?',(room,)).fetchone(); c.close()
    if not row:return 'Бөлме табылмады',404
    return render_template_string(TEACHER,css=CSS,room=room)
@app.route('/join')
def join_redirect(): return redirect(url_for('play',room=request.args.get('room','').strip().upper()))
@app.route('/play/<room>')
def play(room):
    room=room.upper(); c=db(); row=c.execute('SELECT code FROM rooms WHERE code=?',(room,)).fetchone(); c.close()
    if not row:return 'Бөлме табылмады',404
    return render_template_string(PLAY,css=CSS,room=room,questions=QUESTIONS)
@app.route('/api/state')
def state_api():
    room=request.args.get('room','').upper(); c=db(); r=c.execute('SELECT current_round FROM rooms WHERE code=?',(room,)).fetchone()
    if not r:c.close();return jsonify(error='Бөлме табылмады'),404
    rows=c.execute('''SELECT t.name,COALESCE(SUM(a.points),0) score,COUNT(a.id) done FROM teams t LEFT JOIN answers a ON a.room=t.room AND a.team=t.name WHERE t.room=? GROUP BY t.name ORDER BY score DESC''',(room,)).fetchall(); teams=[{'name':x['name'],'score':x['score'],'done':x['done']} for x in rows]; c.close(); return jsonify(round=r['current_round'],teams=teams)
@app.post('/api/join')
def join_api():
    d=request.get_json(force=True); room=str(d.get('room','')).upper(); team=str(d.get('team','')).strip()[:40]
    if not team:return jsonify(ok=False,error='Команда атауы бос.')
    c=db();
    if not c.execute('SELECT 1 FROM rooms WHERE code=?',(room,)).fetchone(): c.close(); return jsonify(ok=False,error='Бөлме табылмады.')
    c.execute('INSERT OR IGNORE INTO teams(room,name) VALUES(?,?)',(room,team)); c.commit(); c.close(); return jsonify(ok=True)
@app.post('/api/set-round')
def set_round():
    d=request.get_json(force=True); room=str(d.get('room','')).upper(); rnd=int(d.get('round',1)); c=db(); c.execute('UPDATE rooms SET current_round=? WHERE code=?',(rnd,room)); c.commit(); c.close(); return jsonify(ok=True)
@app.post('/api/reset')
def reset_api():
    d=request.get_json(force=True); room=str(d.get('room','')).upper(); c=db(); c.execute('DELETE FROM answers WHERE room=?',(room,)); c.execute('DELETE FROM teams WHERE room=?',(room,)); c.execute('UPDATE rooms SET current_round=1 WHERE code=?',(room,)); c.commit(); c.close(); return jsonify(ok=True)
@app.post('/api/submit')
def submit_api():
    d=request.get_json(force=True); room=str(d.get('room','')).upper(); team=str(d.get('team','')).strip(); rnd=int(d.get('round',0)); c=db(); rr=c.execute('SELECT current_round FROM rooms WHERE code=?',(room,)).fetchone()
    if not rr:c.close();return jsonify(ok=False,error='Бөлме табылмады.'),404
    if rnd!=rr['current_round']:c.close();return jsonify(ok=False,error='Бұл кезең қазір ашық емес.'),400
    if c.execute('SELECT 1 FROM answers WHERE room=? AND team=? AND round_no=?',(room,team,rnd)).fetchone():c.close();return jsonify(ok=False,error='Бұл кезеңге жауап берілген.'),400
    pts,detail=score_answer(rnd,{'answer':d.get('answer')}); c.execute('INSERT INTO answers(room,team,round_no,points,detail) VALUES(?,?,?,?,?)',(room,team,rnd,pts,detail)); c.commit(); c.close(); return jsonify(ok=True,points=pts)

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
