# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import sqlite3, os, secrets, string, time, re

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "game.db")

ROUNDS = {
    1: {"title":"Бәйге","questions":[
        {"type":"mc","q":"«Әдемі» сөзі қай сөз табына жатады?","options":["Зат есім","Сын есім","Етістік","Сан есім"],"correct":1,"points":2},
        {"type":"mc","q":"Көптік жалғаулы сөзді табыңыз.","options":["кітап","кітаптар","кітапқа","кітаппен"],"correct":1,"points":2},
        {"type":"mc","q":"«Оқиды» сөзі нені білдіреді?","options":["Зат","Сапа","Қимыл","Сан"],"correct":2,"points":2},
        {"type":"mc","q":"Тәуелдік жалғаулы сөзді табыңыз.","options":["мектеп","мектепке","мектебім","мектептер"],"correct":2,"points":2},
        {"type":"mc","q":"Антоним жұбын табыңыз.","options":["үлкен — кіші","әдемі — сұлу","жылдам — тез","батыр — ержүрек"],"correct":0,"points":2}
    ]},
    2: {"title":"Тіл сыры","questions":[
        {"type":"mc","q":"«Мен мектепке бардым» сөйлеміндегі етістік қайсы?","options":["Мен","мектепке","бардым","мектеп"],"correct":2,"points":2},
        {"type":"mc","q":"«Қызыл алма» тіркесінде сын есім қайсы?","options":["қызыл","алма","қызыл алма","жоқ"],"correct":0,"points":2},
        {"type":"mc","q":"«Біз кітап оқимыз» сөйлемінде бастауыш қайсы?","options":["кітап","оқимыз","Біз","жоқ"],"correct":2,"points":2},
        {"type":"mc","q":"Дұрыс сөйлемді табыңыз.","options":["Мен кеше мектепке бардым.","Мен кеше мектепке барамын.","Кеше мен мектеп бардым.","Мен мектеп кеше бардым."],"correct":0,"points":2}
    ]},
    3: {"title":"Сөз құрастыр","questions":[
        {"type":"text","q":"Аралас әріптерден сөз құраңыз: Л А Қ А М","answers":["қалам"],"points":3},
        {"type":"text","q":"Аралас әріптерден сөз құраңыз: М І Л І Б","answers":["білім"],"points":3},
        {"type":"text","q":"Аралас әріптерден сөз құраңыз: П Е Т К Е М","answers":["мектеп"],"points":3}
    ]},
    4: {"title":"Мақалды жалғастыр","questions":[
        {"type":"mc","q":"«Оқу — білім бұлағы, ...»","options":["білім — өмір шырағы","еңбек — береке","дос — тірек","тіл — қазына"],"correct":0,"points":2},
        {"type":"mc","q":"«Өнер алды — ...»","options":["қызыл тіл","білім","еңбек","бірлік"],"correct":0,"points":2},
        {"type":"mc","q":"«Тіл тас жарады, ...»","options":["тас жармаса бас жарады","еңбек бәрін жеңбек","дос жылатып айтады","оқу инемен құдық қазғандай"],"correct":0,"points":2},
        {"type":"mc","q":"«Отан — ...»","options":["оттан да ыстық","алтын бесік","білім кілті","достық мекені"],"correct":0,"points":2}
    ]},
    5: {"title":"Сөз шебері","questions":[
        {"type":"words","q":"«ҚАЗАҚСТАН» сөзінің әріптерінен білетін сөздеріңізді жазыңыз. Сөздерді үтірмен бөліңіз.",
         "valid":["қазақ","қаз","қазан","таза","зат","сан","сана","санақ","ата","ана","ат","аз","ақ","сақ","ас","тас","тақ","таң","астана","тан","қан","қас","қақ","ақта","атақ","сат","саз","қаза"],"points":8}
    ]},
    6: {"title":"Сөйлемді түзет","questions":[
        {"type":"text","q":"Сөйлемді дұрыс жазыңыз: «Мен кеше мектепке барамын».","answers":["мен кеше мектепке бардым"],"points":3},
        {"type":"text","q":"Сөздердің орнын түзетіңіз: «Мен кітап қызықты оқыдым».","answers":["мен қызықты кітап оқыдым"],"points":3},
        {"type":"text","q":"Мағынасы дұрыс нұсқаны жазыңыз: «Бала доп ойнады».","answers":["бала доп ойнады","бала доппен ойнады"],"points":3}
    ]},
    7: {"title":"Тіл шешендері","questions":[
        {"type":"essay","q":"«Достық», «мектеп», «білім» сөздерін қатыстырып, 2 қарапайым сөйлем жазыңыз.","points":6}
    ]},
    8: {"title":"Суперфинал","questions":[
        {"type":"mc","q":"«Қол ұшын беру» тіркесінің мағынасын табыңыз.","options":["көмектесу","қорқу","ренжу","күлу"],"correct":0,"points":3}
    ]}
}

def con():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = con()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS rooms(
      code TEXT PRIMARY KEY,
      current_round INTEGER NOT NULL DEFAULT 1,
      created_at REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS teams(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      room TEXT NOT NULL,
      name TEXT NOT NULL,
      UNIQUE(room,name)
    );
    CREATE TABLE IF NOT EXISTS answers(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      room TEXT NOT NULL,
      team TEXT NOT NULL,
      round_no INTEGER NOT NULL,
      question_no INTEGER NOT NULL,
      points INTEGER NOT NULL,
      detail TEXT,
      UNIQUE(room,team,round_no,question_no)
    );
    """)
    cols = [r["name"] for r in c.execute("PRAGMA table_info(answers)").fetchall()]
    if "question_no" not in cols:
        c.execute("DROP TABLE answers")
        c.execute("""
        CREATE TABLE answers(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          room TEXT NOT NULL,
          team TEXT NOT NULL,
          round_no INTEGER NOT NULL,
          question_no INTEGER NOT NULL,
          points INTEGER NOT NULL,
          detail TEXT,
          UNIQUE(room,team,round_no,question_no)
        )
        """)
    c.commit()
    c.close()

init_db()

def make_room():
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(chars) for _ in range(5))
        c = con()
        try:
            c.execute("INSERT INTO rooms(code,current_round,created_at) VALUES(?,?,?)",(code,1,time.time()))
            c.commit()
            c.close()
            return code
        except sqlite3.IntegrityError:
            c.close()

def norm(s):
    s = re.sub(r"[.,!?;:—–-]", " ", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

def calc_score(rnd, qno, answer):
    q = ROUNDS[rnd]["questions"][qno]
    if q["type"] == "mc":
        try: idx = int(answer)
        except: idx = -1
        return (q["points"] if idx == q["correct"] else 0,
                q["options"][idx] if 0 <= idx < len(q["options"]) else "")
    if q["type"] == "text":
        a = str(answer or "").strip()
        ok = any(norm(a) == norm(x) for x in q["answers"])
        return (q["points"] if ok else 0, a)
    if q["type"] == "words":
        words = []
        for w in re.split(r"[,;\n]+", str(answer or "")):
            w = norm(w)
            if w and w not in words:
                words.append(w)
        accepted = [w for w in words if w in q["valid"]]
        return min(q["points"], len(accepted)), "Қабылданған: " + ", ".join(accepted)
    a = str(answer or "").strip()
    n = norm(a)
    pts = 0
    if all(w in n for w in ["достық","мектеп","білім"]): pts += 3
    if len(re.findall(r"[.!?]", a)) >= 2 or len(a) > 45: pts += 2
    if len(a) >= 30: pts += 1
    return min(q["points"], pts), a

CSS = """
*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:linear-gradient(135deg,#e0f2fe,#fef3c7);color:#172033}
header{background:linear-gradient(90deg,#173ea5,#2563eb,#0ea5e9);color:#fff;padding:20px;text-align:center;border-bottom:5px solid #f59e0b}
.wrap{max-width:1100px;margin:20px auto;padding:0 12px}.card{background:#fff;border-radius:20px;padding:18px;box-shadow:0 12px 30px #0002;margin-bottom:14px}
input,textarea{width:100%;padding:13px;border:1px solid #cbd5e1;border-radius:12px;font-size:16px;margin:7px 0}
button,.btn{display:inline-block;border:0;border-radius:12px;padding:12px 15px;background:#1d4ed8;color:#fff;font-weight:800;font-size:15px;cursor:pointer;text-decoration:none}
.green{background:#16a34a!important}.red{background:#dc2626!important}.option{padding:12px;margin:8px 0;background:#f1f5f9;border:2px solid transparent;border-radius:12px;cursor:pointer}
.option.sel{border-color:#2563eb;background:#dbeafe}.hidden{display:none}.ok{color:#16a34a;font-weight:800}.bad{color:#dc2626;font-weight:800}
.badge{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:999px;padding:7px 10px;font-weight:800}.score,.big{font-size:20px;font-weight:900}
.linkbox{background:#ecfdf5;border:2px solid #86efac}.studentlink{font-size:20px;font-weight:900;color:#166534;word-break:break-all}
table{width:100%;border-collapse:collapse}th,td{padding:12px;border-bottom:1px solid #e2e8f0;text-align:left}th{background:#dbeafe}
.progress{height:12px;background:#e5e7eb;border-radius:999px;overflow:hidden;margin:12px 0}.bar{height:100%;background:linear-gradient(90deg,#22c55e,#0ea5e9);transition:.3s}
"""

HOME = """<!doctype html><html lang="kk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{{css}}</style></head>
<body><header><h1>🏆 ТІЛ БІЛГІРЛЕРІ LIVE</h1><div>7–9 сынып • қазақ тілі Т2 • командалық сайыс</div></header>
<div class="wrap"><div class="card"><h2>Мұғалімге</h2><a class="btn green" href="/new-room">Жаңа бөлме ашу</a></div>
<div class="card"><h2>Командаға</h2><form action="/join"><input name="room" maxlength="5" placeholder="Бөлме коды" required><button>Кіру</button></form></div></div></body></html>"""

TEACHER = """<!doctype html><html lang="kk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{{css}}</style></head>
<body><header><h1>🏆 Мұғалім панелі</h1></header><div class="wrap">
<div class="card linkbox"><h2>📱 Оқушыларға жіберетін сілтеме</h2><div id="link" class="studentlink"></div><p>Бөлме коды: <b class="big">{{room}}</b></p><button class="green" onclick="copyLink()">Сілтемені көшіру</button></div>
<div class="card"><h2>Қазіргі кезең: <span id="rt"></span></h2><div id="buttons"></div></div>
<div class="card"><h2>📊 LIVE рейтинг</h2><table><thead><tr><th>Орын</th><th>Команда</th><th>Ұпай</th><th>Жауап саны</th></tr></thead><tbody id="tb"></tbody></table></div>
<div class="card"><button class="red" onclick="resetAll()">Сайысты тазалау</button></div></div>
<script>
const room={{room|tojson}},titles={{titles|tojson}},studentURL=location.origin+"/play/"+room;
document.getElementById("link").textContent=studentURL;
async function api(p,d){let o={};if(d)o={method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)};return await(await fetch(p,o)).json()}
async function setRound(r){await api("/api/set-round",{room,round:r});refresh()}
async function resetAll(){if(confirm("Тазалансын ба?")){await api("/api/reset",{room});refresh()}}
async function copyLink(){await navigator.clipboard.writeText(studentURL)}
async function refresh(){
 const s=await api("/api/state?room="+room+"&_="+Date.now());
 rt.textContent=s.round+" — "+titles[s.round];
 buttons.innerHTML=Object.keys(titles).map(x=>`<button class="${+x===s.round?'green':''}" onclick="setRound(${x})">${x}. ${titles[x]}</button>`).join("");
 const a=[...s.teams].sort((x,y)=>y.score-x.score);
 tb.innerHTML=a.length?a.map((t,i)=>`<tr><td>${i==0?'🥇':i==1?'🥈':i==2?'🥉':i+1}</td><td><b>${t.name}</b></td><td>${t.score}</td><td>${t.done}</td></tr>`).join(""):'<tr><td colspan="4">Командалар әлі қосылған жоқ.</td></tr>';
}
refresh();setInterval(refresh,1200);
</script></body></html>"""

PLAY = """<!doctype html><html lang="kk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{{css}}</style></head>
<body><header><h1>🏆 ТІЛ БІЛГІРЛЕРІ LIVE</h1><div>Бөлме: {{room}}</div></header><div class="wrap">
<div class="card" id="joinCard"><h2>Команда ретінде қосылу</h2><input id="teamName" placeholder="Команда атауы"><button onclick="joinTeam()">Қосылу</button></div>
<div class="card hidden" id="gameCard"><span class="badge" id="badge"></span><h2 id="title"></h2><div id="count"></div>
<div class="progress"><div id="bar" class="bar"></div></div><div>Команда: <b id="teamLabel"></b></div><div class="score">Жалпы ұпай: <span id="score">0</span></div><hr>
<div id="task"></div><div id="result"></div></div></div>
<script>
const room={{room|tojson}},R={{rounds|tojson}};
let team=localStorage.getItem("team_"+room)||"",currentRound=0,answered=[];
async function api(p,d){let o={};if(d)o={method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)};return await(await fetch(p,o)).json()}
async function joinTeam(){const n=document.getElementById("teamName").value.trim();if(!n)return;const x=await api("/api/join",{room,team:n});if(x.ok){team=n;localStorage.setItem("team_"+room,team);showGame()}}
async function showGame(){document.getElementById("joinCard").classList.add("hidden");document.getElementById("gameCard").classList.remove("hidden");document.getElementById("teamLabel").textContent=team;await api("/api/join",{room,team});await refresh()}
function pick(el){document.querySelectorAll(".option").forEach(x=>x.classList.remove("sel"));el.classList.add("sel")}
function render(){
 const rd=R[currentRound],qs=rd.questions,next=qs.findIndex((_,i)=>!answered.includes(i));
 badge.textContent="Кезең "+currentRound;title.textContent=currentRound+"-кезең. "+rd.title;
 if(next===-1){count.textContent=qs.length+"/"+qs.length+" тапсырма орындалды";bar.style.width="100%";task.innerHTML='<p class="ok">✅ Бұл кезең толық аяқталды. Келесі кезеңді күтіңіз.</p>';return}
 const q=qs[next];count.textContent=(next+1)+"/"+qs.length+" сұрақ";bar.style.width=Math.round(next/qs.length*100)+"%";
 if(q.type==="mc"){task.innerHTML=`<p><b>${q.q}</b></p>`+q.options.map((o,j)=>`<div class="option" data-i="${j}" onclick="pick(this)">${o}</div>`).join("")+`<button onclick="submitMC(${next})">Жауапты жіберу</button>`}
 else{task.innerHTML=`<p><b>${q.q}</b></p><textarea id="ans" rows="${q.type==='essay'?5:3}"></textarea><button onclick="submitText(${next})">Жауапты жіберу</button>`}
}
async function sendAnswer(qno,answer){
 const x=await api("/api/submit",{room,team,round:currentRound,question:qno,answer});
 if(!x.ok){result.innerHTML='<p class="bad">'+(x.error||"Қате")+'</p>';return}
 result.innerHTML=`<p class="ok">✅ Жауап қабылданды. +${x.points} ұпай</p>`;
 await refresh();
 setTimeout(()=>result.innerHTML="",600);
}
function submitMC(qno){const el=document.querySelector(".option.sel");if(!el){result.innerHTML='<p class="bad">Жауапты таңдаңыз.</p>';return}sendAnswer(qno,+el.dataset.i)}
function submitText(qno){const el=document.getElementById("ans"),v=el.value.trim();if(!v){result.innerHTML='<p class="bad">Жауап жазыңыз.</p>';return}sendAnswer(qno,v)}
async function refresh(){if(!team)return;const s=await api("/api/team-state?room="+encodeURIComponent(room)+"&team="+encodeURIComponent(team)+"&_="+Date.now());currentRound=s.round;answered=s.answered||[];score.textContent=s.score||0;render()}
if(team)showGame();setInterval(refresh,1500);
</script></body></html>"""

@app.route("/")
def home():
    return render_template_string(HOME,css=CSS)

@app.route("/new-room")
def new_room():
    return redirect(url_for("teacher",room=make_room()))

@app.route("/teacher/<room>")
def teacher(room):
    room=room.upper()
    c=con(); ok=c.execute("SELECT 1 FROM rooms WHERE code=?",(room,)).fetchone(); c.close()
    if not ok:return "Бөлме табылмады",404
    return render_template_string(TEACHER,css=CSS,room=room,titles={k:v["title"] for k,v in ROUNDS.items()})

@app.route("/join")
def join_redirect():
    return redirect(url_for("play",room=request.args.get("room","").upper()))

@app.route("/play/<room>")
def play(room):
    room=room.upper()
    c=con(); ok=c.execute("SELECT 1 FROM rooms WHERE code=?",(room,)).fetchone(); c.close()
    if not ok:return "Бөлме табылмады",404
    return render_template_string(PLAY,css=CSS,room=room,rounds=ROUNDS)

@app.route("/api/state")
def state_api():
    room=request.args.get("room","").upper()
    c=con(); rr=c.execute("SELECT current_round FROM rooms WHERE code=?",(room,)).fetchone()
    if not rr:c.close();return jsonify(error="Бөлме жоқ"),404
    rows=c.execute("SELECT t.name,COALESCE(SUM(a.points),0) score,COUNT(a.id) done FROM teams t LEFT JOIN answers a ON a.room=t.room AND a.team=t.name WHERE t.room=? GROUP BY t.name",(room,)).fetchall()
    c.close()
    return jsonify(round=rr["current_round"],teams=[dict(x) for x in rows])

@app.route("/api/team-state")
def team_state():
    room=request.args.get("room","").upper()
    team=request.args.get("team","")
    c=con(); rr=c.execute("SELECT current_round FROM rooms WHERE code=?",(room,)).fetchone()
    if not rr:c.close();return jsonify(error="Бөлме жоқ"),404
    rnd=rr["current_round"]
    ans=[x["question_no"] for x in c.execute("SELECT question_no FROM answers WHERE room=? AND team=? AND round_no=? ORDER BY question_no",(room,team,rnd)).fetchall()]
    sc=c.execute("SELECT COALESCE(SUM(points),0) s FROM answers WHERE room=? AND team=?",(room,team)).fetchone()["s"]
    c.close()
    return jsonify(round=rnd,answered=ans,score=sc)

@app.post("/api/join")
def join_api():
    d=request.get_json(force=True); room=str(d.get("room","")).upper(); team=str(d.get("team","")).strip()[:40]
    c=con()
    if not c.execute("SELECT 1 FROM rooms WHERE code=?",(room,)).fetchone():c.close();return jsonify(ok=False,error="Бөлме табылмады")
    c.execute("INSERT OR IGNORE INTO teams(room,name) VALUES(?,?)",(room,team));c.commit();c.close()
    return jsonify(ok=True)

@app.post("/api/set-round")
def set_round():
    d=request.get_json(force=True); c=con()
    c.execute("UPDATE rooms SET current_round=? WHERE code=?",(int(d["round"]),str(d["room"]).upper()));c.commit();c.close()
    return jsonify(ok=True)

@app.post("/api/reset")
def reset_api():
    d=request.get_json(force=True);room=str(d["room"]).upper();c=con()
    c.execute("DELETE FROM answers WHERE room=?",(room,));c.execute("DELETE FROM teams WHERE room=?",(room,));c.execute("UPDATE rooms SET current_round=1 WHERE code=?",(room,));c.commit();c.close()
    return jsonify(ok=True)

@app.post("/api/submit")
def submit_api():
    d=request.get_json(force=True);room=str(d["room"]).upper();team=str(d["team"]);rnd=int(d["round"]);qno=int(d["question"])
    if rnd not in ROUNDS or qno<0 or qno>=len(ROUNDS[rnd]["questions"]):return jsonify(ok=False,error="Тапсырма табылмады"),400
    c=con();rr=c.execute("SELECT current_round FROM rooms WHERE code=?",(room,)).fetchone()
    if not rr or rr["current_round"]!=rnd:c.close();return jsonify(ok=False,error="Бұл кезең қазір ашық емес"),400
    if c.execute("SELECT 1 FROM answers WHERE room=? AND team=? AND round_no=? AND question_no=?",(room,team,rnd,qno)).fetchone():c.close();return jsonify(ok=False,error="Бұл сұраққа жауап берілген"),400
    pts,detail=calc_score(rnd,qno,d.get("answer"))
    c.execute("INSERT INTO answers(room,team,round_no,question_no,points,detail) VALUES(?,?,?,?,?,?)",(room,team,rnd,qno,pts,detail));c.commit();c.close()
    return jsonify(ok=True,points=pts)

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
