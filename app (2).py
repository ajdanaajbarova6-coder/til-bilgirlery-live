from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import sqlite3, os, secrets, string, time, re

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), 'game.db')

ROUNDS = {
    1: {'title':'Бәйге','questions':[
        {'type':'mc','q':'Көсемше тұлғалы сөзді табыңыз.','options':['оқыған','оқып','оқушы','оқиды'],'correct':1,'points':2},
        {'type':'mc','q':'Есімше тұлғалы сөзді табыңыз.','options':['жазып','жазған','жазу','жазады'],'correct':1,'points':2},
        {'type':'mc','q':'Тәуелдік жалғаулы сөзді табыңыз.','options':['кітаптар','кітабым','кітапқа','кітаппен'],'correct':1,'points':2},
        {'type':'mc','q':'«Себебі» сөзі қай шылау түріне жатады?','options':['Септеулік','Жалғаулық','Демеулік','Одағай'],'correct':1,'points':2},
        {'type':'mc','q':'Тұрақты тіркесті табыңыз.','options':['ақ қар','қол ұшын беру','үлкен үй','жақсы оқу'],'correct':1,'points':2},
    ]},
    2: {'title':'Тіл сыры','questions':[
        {'type':'mc','q':'«Күн бұлттанғандықтан, біз жолға шықпадық» сөйлемінің түрін анықтаңыз.','options':['Мезгіл бағыныңқылы сабақтас','Себеп бағыныңқылы сабақтас','Шартты бағыныңқылы сабақтас','Қарсылықты салалас'],'correct':1,'points':3},
        {'type':'mc','q':'«Егер жақсы дайындалсаң, сайыста жеңесің» — қай сабақтас?','options':['Шартты бағыныңқылы','Себеп бағыныңқылы','Қимыл-сын бағыныңқылы','Мақсат бағыныңқылы'],'correct':0,'points':3},
        {'type':'mc','q':'«Ол кітап оқыды да, кейін пікірін айтты» сөйлемінің түрі:','options':['Салалас құрмалас','Сабақтас құрмалас','Жай сөйлем','Атаулы сөйлем'],'correct':0,'points':3},
        {'type':'mc','q':'Құрмалас сөйлемде жай сөйлемдерді байланыстыратын құралды табыңыз.','options':['Жалғаулық шылау','Көптік жалғауы','Жұрнақ','Дыбыс үндестігі'],'correct':0,'points':3},
    ]},
    3: {'title':'Сөз құрастыр','questions':[
        {'type':'text','q':'Аралас әріптерден сөз құраңыз: Л А Қ А М','answers':['қалам'],'points':3},
        {'type':'text','q':'Аралас әріптерден сөз құраңыз: М І Б І Л','answers':['білім'],'points':3},
        {'type':'text','q':'Аралас әріптерден сөз құраңыз: Қ А Ш А Л О Б','answers':['болашақ'],'points':3},
    ]},
    4: {'title':'Мақалды жалғастыр','questions':[
        {'type':'mc','q':'«Өнер алды — ...»','options':['қызыл тіл','білім','бірлік','еңбек'],'correct':0,'points':2},
        {'type':'mc','q':'«Оқу — білім бұлағы, ...»','options':['білім — өмір шырағы','еңбек — береке','тіл — қазына','дос — тірек'],'correct':0,'points':2},
        {'type':'mc','q':'«Тіл тас жарады, ...»','options':['тас жармаса бас жарады','ақылдан сөз туады','сөз сүйектен өтеді','өнерлі өрге жүзеді'],'correct':0,'points':2},
        {'type':'mc','q':'«Білекті бірді жығар, ...»','options':['білімді мыңды жығар','досы көпті жау алмайды','еңбек түбі — береке','тілден артық қазына жоқ'],'correct':0,'points':2},
    ]},
    5: {'title':'Сөз шебері','questions':[
        {'type':'words','q':'«ҚАЗАҚСТАН» сөзінің әріптерінен мүмкіндігінше көп мағыналы сөз жазыңыз. Сөздерді үтірмен бөліңіз.','valid':['қазақ','қаз','қазан','таза','зат','сан','сана','санақ','санат','ата','ана','ат','аз','азат','ақ','сақ','ас','тас','тақ','таң','асқақ','астана','сақтан','қазақтан','тан','қан','қас','қақ','қат','ақта','атақ','нақ','наз','сат','саз','қаза','қанат'],'points':10},
    ]},
    6: {'title':'Сөйлемді түзет','questions':[
        {'type':'text','q':'Сөйлемді әдеби нормаға сай жазыңыз: «Бала доп ойнады».','answers':['бала доп ойнады','бала доппен ойнады'],'points':3},
        {'type':'text','q':'Сөздердің орнын түзетіңіз: «Мен кітап қызықты оқыдым».','answers':['мен қызықты кітап оқыдым'],'points':3},
        {'type':'text','q':'Шақ қателігін түзетіңіз: «Мен кеше мектепке барамын».','answers':['мен кеше мектепке бардым'],'points':3},
    ]},
    7: {'title':'Тіл шешендері','questions':[
        {'type':'essay','q':'«Тіл – білім – болашақ» сөздерін қатыстырып, мағыналы екі құрмалас сөйлем жазыңыз.','points':10},
    ]},
    8: {'title':'Суперфинал','questions':[
        {'type':'mc','q':'«Төбе шашы тік тұрды» тұрақты тіркесінің мағынасын табыңыз.','options':['қатты қуанды','қатты қорықты','ренжіді','ұялып қалды'],'correct':1,'points':5},
    ]}
}

def con():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    c = con()
    c.execute('CREATE TABLE IF NOT EXISTS rooms(code TEXT PRIMARY KEY,current_round INTEGER DEFAULT 1,created_at REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS teams(id INTEGER PRIMARY KEY AUTOINCREMENT,room TEXT,name TEXT,UNIQUE(room,name))')
    cols = [x['name'] for x in c.execute('PRAGMA table_info(answers)').fetchall()]
    if cols and 'question_no' not in cols:
        c.execute('DROP TABLE answers')
    c.execute('CREATE TABLE IF NOT EXISTS answers(id INTEGER PRIMARY KEY AUTOINCREMENT,room TEXT,team TEXT,round_no INTEGER,question_no INTEGER,points INTEGER,detail TEXT,UNIQUE(room,team,round_no,question_no))')
    c.commit(); c.close()
init()

def make_room():
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(chars) for _ in range(5))
        c = con()
        try:
            c.execute('INSERT INTO rooms VALUES(?,?,?)',(code,1,time.time()))
            c.commit(); c.close(); return code
        except sqlite3.IntegrityError:
            c.close()

def norm(s):
    s = re.sub(r'[.,!?;:—–-]',' ',str(s or '').lower())
    return re.sub(r'\s+',' ',s).strip()

def score_answer(r,q,a):
    x = ROUNDS[r]['questions'][q]
    if x['type'] == 'mc':
        try: i = int(a)
        except: i = -1
        return (x['points'] if i == x['correct'] else 0, x['options'][i] if 0 <= i < len(x['options']) else '')
    if x['type'] == 'text':
        a = str(a or '').strip()
        return (x['points'] if any(norm(a)==norm(z) for z in x['answers']) else 0, a)
    if x['type'] == 'words':
        words=[]
        for z in re.split(r'[,;\n]+',str(a or '')):
            z=norm(z)
            if z and z not in words: words.append(z)
        ok=[z for z in words if z in x['valid']]
        return min(x['points'],len(ok)), 'Қабылданған: '+', '.join(ok)
    a=str(a or '').strip(); n=norm(a); p=0
    if all(w in n for w in ['тіл','білім','болашақ']): p += 4
    if len(re.findall(r'[.!?]',a)) >= 2 or len(a) > 90: p += 3
    if len(a) >= 60: p += 3
    return min(x['points'],p), a

CSS="""*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,Arial;background:linear-gradient(135deg,#e0f2fe,#fef3c7);color:#172033}header{background:linear-gradient(90deg,#173ea5,#2563eb,#0ea5e9);color:#fff;padding:20px;text-align:center;border-bottom:5px solid #f59e0b}.wrap{max-width:1100px;margin:20px auto;padding:0 12px}.card{background:#fff;border-radius:20px;padding:18px;box-shadow:0 12px 30px #0002;margin-bottom:14px}input,textarea{width:100%;padding:13px;border:1px solid #cbd5e1;border-radius:12px;font-size:16px;margin:7px 0}button,.btn{display:inline-block;border:0;border-radius:12px;padding:12px 15px;background:#1d4ed8;color:#fff;font-weight:800;font-size:15px;cursor:pointer;text-decoration:none}.green{background:#16a34a!important}.red{background:#dc2626!important}.option{padding:12px;margin:8px 0;background:#f1f5f9;border:2px solid transparent;border-radius:12px;cursor:pointer}.option.sel{border-color:#2563eb;background:#dbeafe}.hidden{display:none}.ok{color:#16a34a;font-weight:800}.bad{color:#dc2626;font-weight:800}.badge{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:999px;padding:7px 10px;font-weight:800}.score,.big{font-size:20px;font-weight:900}.linkbox{background:#ecfdf5;border:2px solid #86efac}.studentlink{font-size:20px;font-weight:900;color:#166534;word-break:break-all}table{width:100%;border-collapse:collapse}th,td{padding:12px;border-bottom:1px solid #e2e8f0;text-align:left}th{background:#dbeafe}.progress{height:12px;background:#e5e7eb;border-radius:999px;overflow:hidden;margin:12px 0}.bar{height:100%;background:linear-gradient(90deg,#22c55e,#0ea5e9);transition:.3s}"""

HOME="""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><style>{{css}}</style></head><body><header><h1>🏆 ТІЛ БІЛГІРЛЕРІ LIVE</h1><div>7–9 сынып • онлайн командалық сайыс</div></header><div class='wrap'><div class='card'><h2>Мұғалімге</h2><a class='btn green' href='/new-room'>Жаңа бөлме ашу</a></div><div class='card'><h2>Командаға</h2><form action='/join'><input name='room' maxlength='5' placeholder='Бөлме коды' required><button>Кіру</button></form></div></div></body></html>"""

TEACHER="""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><style>{{css}}</style></head><body><header><h1>🏆 Мұғалім панелі</h1></header><div class='wrap'><div class='card linkbox'><h2>📱 Оқушыларға жіберетін сілтеме</h2><div id='link' class='studentlink'></div><p>Бөлме коды: <b class='big'>{{room}}</b></p><button class='green' onclick='copyLink()'>Сілтемені көшіру</button></div><div class='card'><h2>Қазіргі кезең: <span id='rt'></span></h2><div id='buttons'></div></div><div class='card'><h2>📊 LIVE рейтинг</h2><table><thead><tr><th>Орын</th><th>Команда</th><th>Ұпай</th><th>Жауап саны</th></tr></thead><tbody id='tb'></tbody></table></div><div class='card'><button class='red' onclick='resetAll()'>Сайысты тазалау</button></div></div><script>
const room={{room|tojson}},titles={{titles|tojson}},studentUrl=location.origin+'/play/'+room;document.getElementById('link').textContent=studentUrl;
async function api(p,d){let o={};if(d)o={method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)};let r=await fetch(p,o);return await r.json()}
async function setr(r){await api('/api/set-round',{room,round:r});refresh()}
async function resetAll(){if(confirm('Тазалансын ба?')){await api('/api/reset',{room});refresh()}}
async function copyLink(){await navigator.clipboard.writeText(studentUrl)}
async function refresh(){let s=await api('/api/state?room='+room);document.getElementById('rt').textContent=s.round+' — '+titles[s.round];document.getElementById('buttons').innerHTML=Object.keys(titles).map(x=>`<button class='${+x===s.round?'green':''}' onclick='setr(${x})'>${x}. ${titles[x]}</button>`).join('');let a=[...s.teams].sort((x,y)=>y.score-x.score);document.getElementById('tb').innerHTML=a.length?a.map((t,i)=>`<tr><td>${i==0?'🥇':i==1?'🥈':i==2?'🥉':i+1}</td><td><b>${t.name}</b></td><td>${t.score}</td><td>${t.done}</td></tr>`).join(''):'<tr><td colspan=4>Командалар әлі қосылған жоқ.</td></tr>'}
refresh();setInterval(refresh,1200);
</script></body></html>"""

PLAY="""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><style>{{css}}</style></head><body><header><h1>🏆 ТІЛ БІЛГІРЛЕРІ LIVE</h1><div>Бөлме: {{room}}</div></header><div class='wrap'><div class='card' id='joinCard'><h2>Команда ретінде қосылу</h2><input id='teamName' placeholder='Команда атауы'><button onclick='joinTeam()'>Қосылу</button><div id='msg'></div></div><div class='card hidden' id='gameCard'><span class='badge' id='badge'></span><h2 id='title'></h2><div id='count'></div><div class='progress'><div id='bar' class='bar'></div></div><div>Команда: <b id='teamLabel'></b></div><div class='score'>Жалпы ұпай: <span id='score'>0</span></div><hr><div id='task'></div><div id='result'></div></div></div><script>
const room={{room|tojson}},R={{rounds|tojson}};
let team=localStorage.getItem('team_'+room)||'',cr=0,answered=[];
async function api(p,d){let o={};if(d)o={method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)};let r=await fetch(p,o);let j=await r.json();if(!r.ok)throw new Error(j.error||'Қате');return j}
async function joinTeam(){let n=document.getElementById('teamName').value.trim();if(!n)return;try{let x=await api('/api/join',{room,team:n});if(x.ok){team=n;localStorage.setItem('team_'+room,team);showGame()}}catch(e){document.getElementById('msg').innerHTML='<p class=bad>'+e.message+'</p>'}}
async function showGame(){document.getElementById('joinCard').classList.add('hidden');document.getElementById('gameCard').classList.remove('hidden');document.getElementById('teamLabel').textContent=team;await refresh()}
function pick(e){document.querySelectorAll('.option').forEach(x=>x.classList.remove('sel'));e.classList.add('sel')}
function render(){let rd=R[cr],qs=rd.questions,i=qs.findIndex((_,j)=>!answered.includes(j));document.getElementById('badge').textContent='Кезең '+cr;document.getElementById('title').textContent=cr+'. '+rd.title;if(i<0){document.getElementById('count').textContent=qs.length+'/'+qs.length+' тапсырма орындалды';document.getElementById('bar').style.width='100%';document.getElementById('task').innerHTML='<p class="ok">✅ Кезең аяқталды. Келесі кезеңді күтіңіз.</p>';return}let q=qs[i];document.getElementById('count').textContent=(i+1)+'/'+qs.length+' сұрақ';document.getElementById('bar').style.width=Math.round(i/qs.length*100)+'%';if(q.type==='mc'){document.getElementById('task').innerHTML=`<p><b>${q.q}</b></p>`+q.options.map((o,j)=>`<div class='option' data-i='${j}' onclick='pick(this)'>${o}</div>`).join('')+`<button onclick='submitMC(${i})'>Жауапты жіберу</button>`}else{document.getElementById('task').innerHTML=`<p><b>${q.q}</b></p><textarea id='ans' rows='${q.type==='essay'?6:3}'></textarea><button onclick='submitText(${i})'>Жауапты жіберу</button>`}}
async function sendAnswer(q,a){try{let x=await api('/api/submit',{room,team,round:cr,question:q,answer:a});document.getElementById('result').innerHTML=`<p class="ok">✅ +${x.points} ұпай</p>`;answered=x.answered||[...answered,q];document.getElementById('score').textContent=x.score;setTimeout(()=>{document.getElementById('result').innerHTML='';render()},450)}catch(e){document.getElementById('result').innerHTML='<p class="bad">'+e.message+'</p>'}}
function submitMC(q){let e=document.querySelector('.option.sel');if(!e){document.getElementById('result').innerHTML='<p class="bad">Жауапты таңдаңыз.</p>';return}sendAnswer(q,+e.dataset.i)}
function submitText(q){let v=document.getElementById('ans').value.trim();if(!v){document.getElementById('result').innerHTML='<p class="bad">Жауап жазыңыз.</p>';return}sendAnswer(q,v)}
async function refresh(){if(!team)return;try{let s=await api('/api/team-state?room='+room+'&team='+encodeURIComponent(team));document.getElementById('score').textContent=s.score||0;let changed=cr!==s.round;cr=s.round;answered=s.answered||[];if(changed)document.getElementById('result').innerHTML='';render()}catch(e){console.error(e)}}
if(team)showGame();setInterval(refresh,1500);
</script></body></html>"""

@app.route('/')
def home(): return render_template_string(HOME,css=CSS)
@app.route('/new-room')
def newroom(): return redirect(url_for('teacher',room=make_room()))
@app.route('/teacher/<room>')
def teacher(room):
    room=room.upper(); c=con(); ok=c.execute('SELECT 1 FROM rooms WHERE code=?',(room,)).fetchone(); c.close()
    if not ok:return 'Бөлме табылмады',404
    return render_template_string(TEACHER,css=CSS,room=room,titles={k:v['title'] for k,v in ROUNDS.items()})
@app.route('/join')
def joinredirect(): return redirect(url_for('play',room=request.args.get('room','').upper()))
@app.route('/play/<room>')
def play(room):
    room=room.upper(); c=con(); ok=c.execute('SELECT 1 FROM rooms WHERE code=?',(room,)).fetchone(); c.close()
    if not ok:return 'Бөлме табылмады',404
    return render_template_string(PLAY,css=CSS,room=room,rounds=ROUNDS)
@app.route('/api/state')
def state():
    room=request.args.get('room','').upper(); c=con(); rr=c.execute('SELECT current_round FROM rooms WHERE code=?',(room,)).fetchone()
    if not rr:c.close();return jsonify(error='Бөлме жоқ'),404
    rows=c.execute('SELECT t.name,COALESCE(SUM(a.points),0) score,COUNT(a.id) done FROM teams t LEFT JOIN answers a ON a.room=t.room AND a.team=t.name WHERE t.room=? GROUP BY t.name',(room,)).fetchall(); c.close()
    return jsonify(round=rr['current_round'],teams=[dict(x) for x in rows])
@app.route('/api/team-state')
def teamstate():
    room=request.args.get('room','').upper(); team=request.args.get('team',''); c=con(); rr=c.execute('SELECT current_round FROM rooms WHERE code=?',(room,)).fetchone()
    if not rr:c.close();return jsonify(error='Бөлме жоқ'),404
    rnd=rr['current_round']; ans=[x['question_no'] for x in c.execute('SELECT question_no FROM answers WHERE room=? AND team=? AND round_no=? ORDER BY question_no',(room,team,rnd))]; sc=c.execute('SELECT COALESCE(SUM(points),0) s FROM answers WHERE room=? AND team=?',(room,team)).fetchone()['s']; c.close()
    return jsonify(round=rnd,answered=ans,score=sc)
@app.post('/api/join')
def joinapi():
    d=request.get_json(); room=str(d.get('room','')).upper(); team=str(d.get('team','')).strip()[:40]; c=con()
    if not c.execute('SELECT 1 FROM rooms WHERE code=?',(room,)).fetchone():c.close();return jsonify(ok=False,error='Бөлме табылмады'),404
    c.execute('INSERT OR IGNORE INTO teams(room,name) VALUES(?,?)',(room,team)); c.commit(); c.close(); return jsonify(ok=True)
@app.post('/api/set-round')
def setround():
    d=request.get_json(); c=con(); c.execute('UPDATE rooms SET current_round=? WHERE code=?',(int(d['round']),str(d['room']).upper())); c.commit(); c.close(); return jsonify(ok=True)
@app.post('/api/reset')
def resetapi():
    d=request.get_json(); room=str(d['room']).upper(); c=con(); c.execute('DELETE FROM answers WHERE room=?',(room,)); c.execute('DELETE FROM teams WHERE room=?',(room,)); c.execute('UPDATE rooms SET current_round=1 WHERE code=?',(room,)); c.commit(); c.close(); return jsonify(ok=True)
@app.post('/api/submit')
def submit():
    d=request.get_json(); room=str(d['room']).upper(); team=str(d['team']); rnd=int(d['round']); q=int(d['question']); c=con(); rr=c.execute('SELECT current_round FROM rooms WHERE code=?',(room,)).fetchone()
    if not rr or rr['current_round']!=rnd:c.close();return jsonify(ok=False,error='Бұл кезең қазір ашық емес'),400
    if q<0 or q>=len(ROUNDS[rnd]['questions']):c.close();return jsonify(ok=False,error='Сұрақ табылмады'),400
    if c.execute('SELECT 1 FROM answers WHERE room=? AND team=? AND round_no=? AND question_no=?',(room,team,rnd,q)).fetchone():c.close();return jsonify(ok=False,error='Бұл сұраққа жауап берілген'),400
    pts,detail=score_answer(rnd,q,d.get('answer')); c.execute('INSERT INTO answers(room,team,round_no,question_no,points,detail) VALUES(?,?,?,?,?,?)',(room,team,rnd,q,pts,detail)); c.commit()
    answered=[x['question_no'] for x in c.execute('SELECT question_no FROM answers WHERE room=? AND team=? AND round_no=? ORDER BY question_no',(room,team,rnd))]
    total=c.execute('SELECT COALESCE(SUM(points),0) s FROM answers WHERE room=? AND team=?',(room,team)).fetchone()['s']; c.close()
    return jsonify(ok=True,points=pts,answered=answered,score=total)

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
