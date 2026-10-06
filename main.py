#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Key Tester - kiểm tra API key của nhiều provider qua giao diện web.
Chạy:  python api_tester.py     (không cần cài thêm gì, chỉ cần Python 3.8+)
Trình duyệt tự mở http://127.0.0.1:8765. Key chỉ đi từ máy bạn tới provider.
"""
import json, threading, time, urllib.error, urllib.parse, urllib.request, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def call(p):
    kind, base, key = p["kind"], p["base"].strip().rstrip("/"), p["key"].strip()
    model, act = p.get("model", "").strip(), p["action"]
    if not base.startswith(("http://", "https://")):
        raise ValueError("Base URL phải bắt đầu bằng http:// hoặc https://")
    h = {"Content-Type": "application/json", "User-Agent": "api-tester/1.0"}
    if kind == "anthropic":
        h.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
    elif kind == "gemini":
        h["x-goog-api-key"] = key
    else:
        h["Authorization"] = "Bearer " + key
    data, method = None, "GET"
    if act == "models":
        path = {"anthropic": "/v1/models?limit=1000", "gemini": "/v1beta/models?pageSize=1000"}.get(kind, "/models")
    else:
        method = "POST"
        msgs, sysm, mt = p.get("messages", []), p.get("system", ""), int(p.get("max_tokens", 256))
        if kind == "anthropic":
            path = "/v1/messages"
            d = {"model": model, "max_tokens": mt, "messages": msgs}
            if sysm:
                d["system"] = sysm
        elif kind == "gemini":
            path = "/v1beta/models/%s:generateContent" % urllib.parse.quote(model.replace("models/", ""), safe="")
            d = {"contents": [{"role": "model" if m["role"] == "assistant" else "user",
                               "parts": [{"text": m["content"]}]} for m in msgs],
                 "generationConfig": {"maxOutputTokens": mt}}
            if sysm:
                d["systemInstruction"] = {"parts": [{"text": sysm}]}
        else:
            path = "/chat/completions"
            d = {"model": model, "messages": ([{"role": "system", "content": sysm}] if sysm else []) + msgs}
            d["max_completion_tokens" if kind == "openai" else "max_tokens"] = mt
        data = json.dumps(d).encode()
    req = urllib.request.Request(base + path, data=data, headers=h, method=method)
    t = time.perf_counter()
    try:
        r = urllib.request.urlopen(req, timeout=120)
        st, hd, raw = r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        st, hd, raw = e.code, e.headers, e.read()
    except Exception as e:
        return {"status": 0, "ms": (time.perf_counter() - t) * 1000, "headers": {}, "body": "Lỗi kết nối: %s" % e}
    txt = raw.decode("utf-8", "replace")
    try:
        body = json.loads(txt)
    except ValueError:
        body = txt
    return {"status": st, "ms": (time.perf_counter() - t) * 1000,
            "headers": {k.lower(): v for k, v in hd.items()}, "body": body}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, b, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._send(PAGE.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            out = call(json.loads(self.rfile.read(n)))
        except Exception as e:
            out = {"status": 0, "ms": 0, "headers": {}, "body": "Lỗi: %s" % e}
        self._send(json.dumps(out).encode("utf-8"), "application/json")


PAGE = r"""<!doctype html><html lang="vi"><meta charset="utf-8"><title>API Key Tester</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0f1115;--card:#181b22;--bd:#2a2f3a;--tx:#e6e8ee;--mu:#8b92a3;--ac:#6ea8fe;--ok:#4ade80;--er:#f87171;--wa:#fbbf24}
*{box-sizing:border-box}body{margin:0;font:14px/1.5 system-ui,sans-serif;background:var(--bg);color:var(--tx)}
.w{max-width:960px;margin:0 auto;padding:20px}h1{font-size:20px;margin:0 0 14px}h3{margin:0 0 6px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px;margin-bottom:14px}
.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}
label{display:block;color:var(--mu);font-size:12px;margin-bottom:3px}
input,select,textarea,button{font:inherit;color:inherit;background:#0f1218;border:1px solid var(--bd);border-radius:7px;padding:7px 9px;width:100%}
input[type=checkbox]{width:auto}
button{background:var(--ac);color:#0b1220;border:0;font-weight:600;cursor:pointer;width:auto;padding:7px 16px}
button:disabled{opacity:.5}.tabs{display:flex;gap:6px;margin-bottom:12px}
.tabs button{background:#232834;color:var(--mu)}.tabs button.on{background:var(--ac);color:#0b1220}
.row{display:flex;gap:8px;align-items:end;flex-wrap:wrap;margin-bottom:10px}.row>div{flex:1;min-width:110px}
table{width:100%;border-collapse:collapse;font-size:12.5px}td{border-bottom:1px solid var(--bd);padding:4px 6px;word-break:break-all}
.ok{color:var(--ok)}.er{color:var(--er)}.wa{color:var(--wa)}.mu{color:var(--mu)}.p{display:none}.p.on{display:block}
pre{background:#0f1218;border:1px solid var(--bd);border-radius:7px;padding:9px;overflow:auto;max-height:300px;white-space:pre-wrap;font-size:12px}
.m{padding:8px 11px;border-radius:9px;margin:6px 0;white-space:pre-wrap}.u{background:#232b3d;margin-left:15%}.a{background:#1d2a24;margin-right:15%}
#chat{max-height:420px;overflow:auto;margin-bottom:10px}
</style>
<div class="w"><h1>API Key Tester</h1>
<div class="card"><div class="g">
<div><label>Provider</label><select id="prov"></select></div>
<div><label>Base URL</label><input id="base"></div>
<div><label>API key</label><input id="key" type="password" placeholder="dán key vào đây"></div>
<div><label>Model (bấm Kiểm tra để nạp danh sách)</label><input id="model" list="ml"><datalist id="ml"></datalist></div>
</div><label style="margin-top:8px"><input type="checkbox" id="rem"> Nhớ cấu hình trong trình duyệt này (lưu key ở localStorage)</label></div>

<div class="tabs"><button class="on" data-t="c">Kiểm tra</button><button data-t="h">Chat</button><button data-t="b">Burst test</button><button data-t="w">Theo dõi</button></div>

<div class="p on" id="c"><button onclick="check()">Chạy kiểm tra key</button><div id="co" style="margin-top:12px"></div></div>

<div class="p" id="h"><div class="card"><div id="chat"></div>
<div class="row"><div style="flex:3"><label>System prompt (tuỳ chọn)</label><input id="sys"></div><div><label>Max tokens</label><input id="mt" type="number" value="512"></div><button class="s" onclick="H=[];$('#chat').innerHTML=''" style="background:#2a2f3a;color:var(--tx)">Xoá chat</button></div>
<div class="row"><div style="flex:5"><textarea id="cin" rows="2" placeholder="Nhập tin nhắn, Enter để gửi (Shift+Enter xuống dòng)"></textarea></div><button id="sb" onclick="send()">Gửi</button></div></div></div>

<div class="p" id="b"><div class="card"><div class="row"><div><label>Số request</label><input id="bn" type="number" value="20"></div><div><label>Chạy song song</label><input id="bw" type="number" value="5"></div><button id="bb" onclick="burst()">Chạy</button></div>
<div id="bs" class="mu">Gửi nhiều request nhỏ cùng lúc để xem khi nào bị 429.</div><table id="bo"></table></div></div>

<div class="p" id="w"><div class="card"><div class="row"><div><label>Ping mỗi (giây, tối thiểu 5)</label><input id="wi" type="number" value="30"></div><button id="wb" onclick="watch()">Bắt đầu</button></div>
<div id="ws" class="mu">Ping định kỳ để xem key có sống ổn định không. Tự dừng nếu key bị thu hồi / hết credit.</div><table id="wo"></table></div></div>
</div>
<script>
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const PR={OpenAI:['openai','https://api.openai.com/v1','gpt-4o-mini'],
Anthropic:['anthropic','https://api.anthropic.com','claude-haiku-4-5-20251001'],
'Google Gemini':['gemini','https://generativelanguage.googleapis.com','gemini-2.5-flash'],
OpenRouter:['compat','https://openrouter.ai/api/v1','openai/gpt-4o-mini'],
Groq:['compat','https://api.groq.com/openai/v1','llama-3.1-8b-instant'],
DeepSeek:['compat','https://api.deepseek.com','deepseek-chat'],
Mistral:['compat','https://api.mistral.ai/v1','mistral-small-latest'],
xAI:['compat','https://api.x.ai/v1','grok-3-mini'],
'Together AI':['compat','https://api.together.xyz/v1','meta-llama/Llama-3.3-70B-Instruct-Turbo'],
'Tùy chỉnh (OpenAI-compatible)':['compat','','']};
$('#prov').innerHTML=Object.keys(PR).map(k=>`<option>${k}</option>`).join('');
const kind=()=>PR[$('#prov').value][0];
function setProv(){const p=PR[$('#prov').value];$('#base').value=p[1];$('#model').value=p[2];$('#ml').innerHTML=''}
$('#prov').onchange=setProv;
const S=JSON.parse(localStorage.getItem('apit')||'{}');
if(S.prov){$('#prov').value=S.prov;$('#base').value=S.base;$('#key').value=S.key||'';$('#model').value=S.model;$('#rem').checked=true}else setProv();
function save(){$('#rem').checked?localStorage.setItem('apit',JSON.stringify({prov:$('#prov').value,base:$('#base').value,key:$('#key').value,model:$('#model').value})):localStorage.removeItem('apit')}
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tabs button,.p').forEach(x=>x.classList.remove('on'));b.classList.add('on');$('#'+b.dataset.t).classList.add('on')});

async function run(action,x={}){save();const t=performance.now();
 try{const r=await fetch('/api/run',{method:'POST',body:JSON.stringify({kind:kind(),base:$('#base').value,key:$('#key').value,model:$('#model').value,action,...x})});return await r.json()}
 catch(e){return{status:0,ms:performance.now()-t,headers:{},body:String(e)}}}
const ping=()=>run('chat',{messages:[{role:'user',content:'hi'}],max_tokens:8});
function ex(b){const k=kind();let text='',i,o;if(typeof b!='object'||!b)return{text:String(b||'')};
 if(k=='anthropic'){text=(b.content||[]).filter(x=>x.type=='text').map(x=>x.text).join('');i=b.usage?.input_tokens;o=b.usage?.output_tokens}
 else if(k=='gemini'){text=(b.candidates?.[0]?.content?.parts||[]).map(p=>p.text||'').join('');i=b.usageMetadata?.promptTokenCount;o=b.usageMetadata?.candidatesTokenCount}
 else{text=b.choices?.[0]?.message?.content||'';i=b.usage?.prompt_tokens;o=b.usage?.completion_tokens}
 return{text,i,o}}
const emsg=b=>typeof b=='object'&&b?(b.error?.message||(typeof b.error=='string'?b.error:'')||b.message||JSON.stringify(b).slice(0,250)):String(b).slice(0,250);
const dead=r=>[401,403].includes(r.status)||/credit|quota|balance|billing|insufficient|payment/i.test(emsg(r.body));
function why(r){if(/credit|quota|balance|billing|insufficient|payment/i.test(emsg(r.body)))return'Hết credit / quota / chưa nạp tiền';
 return({0:'Không kết nối được tới provider',400:'Request sai (kiểm tra model)',401:'API key sai hoặc đã bị thu hồi',402:'Hết số dư',403:'Key không có quyền',404:'Không tìm thấy (sai model hoặc Base URL?)',429:'Bị rate limit',500:'Lỗi phía provider',503:'Provider quá tải',529:'Provider quá tải'})[r.status]||'Lỗi'}
const remh=h=>Object.entries(h||{}).filter(([k])=>/remaining/i.test(k)).map(([k,v])=>k.replace(/^(anthropic-|x-)?ratelimit-/,'')+'='+v).join(' ');
function hdrs(h){const all=Object.entries(h||{}),rl=all.filter(([k])=>/rate|limit|remaining|reset|retry-after|request-id|organization/i.test(k));
 const t=a=>'<table>'+a.map(([k,v])=>`<tr><td class=mu>${esc(k)}</td><td>${esc(v)}</td></tr>`).join('')+'</table>';
 return(rl.length?'<b>Rate limit / quota</b>'+t(rl):'<span class=mu>Provider không trả header rate-limit.</span>')+`<details><summary class=mu>Tất cả headers (${all.length})</summary>${t(all)}</details>`}

async function check(){const o=$('#co');o.textContent='Đang kiểm tra…';
 const m=await run('models'),p=await ping(),good=p.status==200,e=ex(p.body);let ids=[];
 if(m.status==200&&m.body){const b=m.body;ids=(Array.isArray(b)?b:b.data||b.models||[]).map(x=>(x.id||x.name||'').replace('models/',''));$('#ml').innerHTML=ids.map(i=>`<option value="${esc(i)}">`).join('')}
 o.innerHTML=`<div class=card><h3 class=${good?'ok':'er'}>${good?'✔ Key hoạt động':'✘ Không gọi được: '+why(p)}</h3>
 <div>HTTP ${p.status} · ${p.ms.toFixed(0)} ms${e.i!=null?` · token in/out: ${e.i}/${e.o}`:''}</div>${good?'':`<pre>${esc(emsg(p.body))}</pre>`}
 <div>Models: ${m.status==200?`<span class=ok>${ids.length} model</span> (đã nạp vào ô Model)`:`<span class=er>HTTP ${m.status} – ${why(m)}</span>`}</div></div>
 <div class=card>${hdrs(Object.keys(p.headers||{}).length?p.headers:m.headers)}</div>
 ${ids.length?`<details class=card><summary>Danh sách model</summary><pre>${esc(ids.join('\n'))}</pre></details>`:''}
 <div class=mu>Lưu ý: API key thường không trả số dư hay ngày hết hạn – xem ở trang billing của provider. Dùng tab "Theo dõi" để kiểm tra độ ổn định.</div>`}

let H=[];
function add(c,t,meta,r){const d=document.createElement('div');d.className='m '+c;d.textContent=t;
 if(meta){const s=document.createElement('div');s.className='mu';s.style.fontSize='12px';s.textContent=meta;d.append(s);
  const x=document.createElement('details'),p=document.createElement('pre');x.innerHTML='<summary class=mu>JSON thô + headers</summary>';p.textContent=JSON.stringify({headers:r.headers,body:r.body},null,2);x.append(p);d.append(x)}
 $('#chat').append(d);d.scrollIntoView()}
async function send(){const q=$('#cin').value.trim();if(!q)return;$('#cin').value='';H.push({role:'user',content:q});add('u',q);$('#sb').disabled=true;
 const r=await run('chat',{messages:H,system:$('#sys').value,max_tokens:+$('#mt').value||512});$('#sb').disabled=false;
 if(r.status!=200){H.pop();add('a','❌ '+why(r)+'\n'+emsg(r.body));return}
 const e=ex(r.body);H.push({role:'assistant',content:e.text});
 add('a',e.text||'(rỗng)',`HTTP ${r.status} · ${r.ms.toFixed(0)} ms · in ${e.i??'?'} / out ${e.o??'?'} token · ${remh(r.headers)}`,r)}
$('#cin').onkeydown=e=>{if(e.key=='Enter'&&!e.shiftKey){e.preventDefault();send()}};

async function burst(){const n=+$('#bn').value||20,w=+$('#bw').value||5,o=$('#bo');o.innerHTML='';let i=0,c={},ms=[];$('#bb').disabled=true;
 await Promise.all(Array.from({length:w},async()=>{while(i<n){const k=++i,r=await ping();c[r.status]=(c[r.status]||0)+1;if(r.status==200)ms.push(r.ms);
  o.insertAdjacentHTML('beforeend',`<tr><td>#${k}</td><td class=${r.status==200?'ok':r.status==429?'wa':'er'}>${r.status}</td><td>${r.ms.toFixed(0)} ms</td><td class=mu>${esc(r.status==200?remh(r.headers):emsg(r.body).slice(0,90))}</td></tr>`)}}));
 ms.sort((a,b)=>a-b);
 $('#bs').innerHTML=`Kết quả: ${JSON.stringify(c)}${ms.length?` · p50 ${ms[ms.length>>1].toFixed(0)} ms / max ${ms.at(-1).toFixed(0)} ms`:''} ${c[429]?'<span class=wa>– đã chạm rate limit (429)</span>':''}`;$('#bb').disabled=false}

let wt=null,wc={},wn=0;
function watch(){if(wt){clearInterval(wt);wt=null;$('#wb').textContent='Bắt đầu';return}
 wc={};wn=0;$('#wo').innerHTML='';$('#wb').textContent='Dừng';
 const tick=async()=>{const r=await ping();wn++;wc[r.status]=(wc[r.status]||0)+1;
  $('#wo').insertAdjacentHTML('afterbegin',`<tr><td>${new Date().toLocaleTimeString()}</td><td class=${r.status==200?'ok':'er'}>${r.status}</td><td>${r.ms.toFixed(0)} ms</td><td class=mu>${esc(r.status==200?remh(r.headers):emsg(r.body).slice(0,90))}</td></tr>`);
  $('#ws').textContent=`${wn} lần · thành công ${wc[200]||0} (${((wc[200]||0)/wn*100).toFixed(0)}%)`;
  if(dead(r)&&wt){watch();$('#ws').textContent+=' · key không còn dùng được → đã dừng'}};
 tick();wt=setInterval(tick,Math.max(5,+$('#wi').value||30)*1000)}
</script></html>"""


if __name__ == "__main__":
    port = 8765
    while True:
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            port += 1
    url = "http://127.0.0.1:%d" % port
    print("API Key Tester đang chạy tại %s  (Ctrl+C để thoát)" % url)
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
