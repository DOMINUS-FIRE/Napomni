<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Napomni ✨</title>
  <style>
    :root{
      --bg1:#f7eefc; --bg2:#fdf7ff; --card:#ffffffcc;
      --text:#2b2233; --muted:#6e5f7a; --stroke:#e7d8f2;
      --accent:#b65cff; --accent2:#ff5ca8;
      --shadow: 0 18px 55px rgba(35, 14, 56, .14);
      --radius: 22px;
      --completed: #a0a0a0;
      --completed-bg: #f5f5f5;
    }
    *{box-sizing:border-box}
    body{
      margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
      color:var(--text);
      background: radial-gradient(1200px 600px at 80% 10%, #ffd6ea 0%, transparent 55%),
                  radial-gradient(900px 500px at 20% 0%, #e0d1ff 0%, transparent 55%),
                  linear-gradient(180deg, var(--bg1), var(--bg2));
      min-height:100vh; display:flex; justify-content:center; padding:28px 14px 60px;
    }
    .wrap{width:min(980px, 100%)}
    header{display:flex; align-items:flex-end; justify-content:space-between; gap:14px; margin-bottom:18px;}
    h1{margin:0; font-size: clamp(28px, 3.6vw, 44px);}
    .muted{color:var(--muted)}
    .right{display:flex; gap:10px; flex-wrap:wrap; justify-content:flex-end;}
    .pill{padding:10px 14px; border:1px solid var(--stroke); border-radius:999px; background:#fff8ff; color:var(--muted);
      font-weight:800; font-size:13px; display:inline-flex; align-items:center; gap:8px;}
    .grid{display:grid; grid-template-columns: 1.05fr .95fr; gap:18px;}
    @media (max-width: 860px){ .grid{grid-template-columns:1fr} header{flex-direction:column; align-items:flex-start} .right{justify-content:flex-start} }

    .card{background:var(--card); border:1px solid var(--stroke); border-radius:var(--radius); box-shadow:var(--shadow); overflow:hidden; backdrop-filter: blur(8px);}
    .card .hd{padding:18px 18px 10px; display:flex; align-items:center; justify-content:space-between; gap:10px;}
    .card .bd{padding:0 18px 18px;}

    label{display:block; font-size:13px; font-weight:900; color:#45324f; margin:12px 0 6px;}
    input[type="text"], input[type="datetime-local"], textarea{
      width:100%; padding:12px 12px; border:1px solid var(--stroke); border-radius:14px; background:#fff; outline:none; font-size:14px;
    }
    textarea{min-height:100px; resize:vertical}
    .row{display:grid; grid-template-columns: 1fr 1fr; gap:12px;}
    @media (max-width: 520px){ .row{grid-template-columns:1fr} }

    .btns{display:flex; gap:10px; flex-wrap:wrap; margin-top:14px;}
    button{border:0; border-radius:14px; padding:12px 14px; font-weight:900; cursor:pointer; transition: transform .06s ease; font-size:14px;}
    button:active{transform:translateY(1px)}
    .primary{background: linear-gradient(135deg, var(--accent), var(--accent2)); color:white; box-shadow: 0 12px 35px rgba(182, 92, 255, .28);}
    .ghost{background:#fff; border:1px solid var(--stroke); color:#4b3a57;}
    .danger{background:#fff1f6; border:1px solid #ffd1e6; color:#8a1a4b;}
    .success{background:#e6ffe6; border:1px solid #b3ffb3; color:#1a7a1a;}

    .listTop{display:flex; align-items:center; gap:10px; padding:10px 18px 0;}
    .search{flex:1}
    .filter-tabs{
      display:flex; gap:8px; margin:10px 18px 0; padding-bottom:8px; border-bottom:1px solid var(--stroke);
    }
    .filter-tab{
      padding:6px 12px; border-radius:30px; background:#fff; border:1px solid var(--stroke); font-size:13px; font-weight:900; cursor:pointer;
    }
    .filter-tab.active{
      background:var(--accent); border-color:var(--accent); color:white;
    }
    .note{padding:14px 16px; border:1px solid var(--stroke); background:#fff; border-radius:18px; margin-top:12px;
      display:grid; grid-template-columns: 1fr auto; gap:10px; align-items:start; transition: opacity 0.2s;
    }
    .note.completed{
      opacity:0.7;
      background:var(--completed-bg);
      border-color:#d0d0d0;
    }
    .note.completed h3{
      text-decoration: line-through;
      color:var(--completed);
    }
    .note h3{margin:0 0 6px; font-size:16px}
    .note .meta{font-size:12px; color:var(--muted); font-weight:900}
    .note .txt{white-space:pre-wrap; margin-top:8px; color:#3b2a47}
    .completed .txt{color:#888}
    .thumb{
      width:84px; height:84px; border-radius:14px; border:1px solid var(--stroke); 
      object-fit:cover; background:#faf7ff; cursor:pointer;
      transition: transform 0.1s ease, box-shadow 0.1s ease;
    }
    .thumb:hover{
      transform:scale(1.02);
      box-shadow:0 4px 12px rgba(0,0,0,0.1);
    }
    .thumb-placeholder{
      width:84px; height:84px; border-radius:14px; border:1px dashed var(--stroke);
      display:flex; align-items:center; justify-content:center;
      color:var(--muted); font-weight:900; cursor:default;
    }
    .actions{display:flex; gap:8px; margin-top:10px; flex-wrap:wrap}
    .small{padding:9px 10px; border-radius:12px; font-size:13px;}

    /* Модальное окно для фото */
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0,0,0,0.9);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.2s ease, visibility 0.2s ease;
      backdrop-filter: blur(5px);
    }
    .modal-overlay.active {
      opacity: 1;
      visibility: visible;
    }
    .modal-content {
      max-width: 90vw;
      max-height: 90vh;
      position: relative;
      transform: scale(0.9);
      transition: transform 0.2s ease;
    }
    .modal-overlay.active .modal-content {
      transform: scale(1);
    }
    .modal-image {
      max-width: 100%;
      max-height: 90vh;
      border-radius: 12px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.4);
      border: 2px solid rgba(255,255,255,0.1);
    }
    .modal-close {
      position: absolute;
      top: -40px;
      right: 0;
      background: rgba(255,255,255,0.2);
      color: white;
      border: none;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      font-size: 24px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s ease;
    }
    .modal-close:hover {
      background: rgba(255,255,255,0.3);
    }
    .modal-caption {
      position: absolute;
      bottom: -40px;
      left: 0;
      color: white;
      font-size: 14px;
      opacity: 0.8;
    }

    .toast{position:fixed; left:50%; transform:translateX(-50%); bottom:18px; background:#1d1226; color:#fff;
      padding:10px 14px; border-radius:999px; opacity:0; pointer-events:none; transition:opacity .2s ease, transform .2s ease;
      box-shadow:0 18px 40px rgba(0,0,0,.25); font-weight:900; font-size:13px;}
    .toast.show{opacity:1; transform:translateX(-50%) translateY(-4px)}
    .hint{font-size:12px; font-weight:800; margin-top:10px;}
    .connected{font-weight:900; color:#2d7a45;}
    .notconnected{font-weight:900; color:#8a1a4b;}
    .modeEdit{display:inline-block; margin-left:8px; font-size:12px; font-weight:900; color:#5a2e7a;}
    .badge-completed{
      display:inline-block; background:#e0e0e0; color:#555; font-size:11px; font-weight:900; 
      padding:3px 8px; border-radius:30px; margin-left:8px;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div>
        <h1>Napomni ✨</h1>
        <div class="muted" style="margin-top:6px; font-weight:900;">Добавляй напоминания — они придут в Telegram.</div>
      </div>
      <div class="right">
      </div>
    </header>

    <div class="grid">
      <section class="card">
        <div class="hd">
          <div style="font-weight:900;">Новое напоминание <span id="editBadge" class="modeEdit" style="display:none;">(редактирование)</span></div>
          <button class="ghost small" id="connectBtn">Подключить Telegram ↗</button>
        </div>
        <div class="bd">
          <div id="connStatus" class="hint notconnected">Не подключено. Нажми “Подключить Telegram”.</div>

          <label>Заголовок</label>
          <input id="title" type="text" placeholder="Например: выпить таблетки" maxlength="80" />

          <div class="row">
            <div>
              <label>Время</label>
              <input id="when" type="datetime-local" />
            </div>
            <div>
              <label>Фото (по желанию)</label>
              <input id="photo" type="file" accept="image/*" />
            </div>
          </div>

          <label>Описание</label>
          <textarea id="desc" placeholder="Коротко и понятно 😊"></textarea>

          <div class="btns">
            <button class="primary" id="saveBtn">Сохранить</button>
            <button class="ghost" id="cancelEditBtn" style="display:none;">Отмена</button>
            <button class="ghost" id="clearBtn">Очистить</button>
          </div>

          <div class="hint muted">
            Нельзя ставить время “на сейчас” или в прошлое — только на будущее.
          </div>
        </div>
      </section>

      <section class="card">
        <div class="hd" style="padding-bottom:6px">
          <div style="font-weight:900;">Мои напоминания</div>
          <div style="display:flex; gap:6px;">
            <button class="success small" id="hideCompletedBtn">Скрыть выполн.</button>
            <button class="danger small" id="wipeBtn">Удалить все</button>
          </div>
        </div>
        <div class="listTop">
          <input class="search" id="q" type="text" placeholder="Поиск..." />
        </div>
        <div class="filter-tabs" id="filterTabs">
          <span class="filter-tab active" data-filter="all">Все</span>
          <span class="filter-tab" data-filter="active">Активные</span>
          <span class="filter-tab" data-filter="completed">Выполненные</span>
        </div>
        <div class="bd" id="list"></div>
      </section>
    </div>
  </div>

  <!-- Модальное окно для фото -->
  <div class="modal-overlay" id="photoModal" onclick="closeModal()">
    <div class="modal-content" onclick="event.stopPropagation()">
      <button class="modal-close" onclick="closeModal()">×</button>
      <img class="modal-image" id="modalImage" src="" alt="Превью">
      <div class="modal-caption" id="modalCaption"></div>
    </div>
  </div>

  <div class="toast" id="toast">OK</div>

<script>
  // ======================
  // НАСТРОЙКА (1 строка)
  // ======================
  const API_BASE = "https://napomni.onrender.com"; // <-- если поменяешь домен Render, меняешь ТУТ

  const BOT_USERNAME = "napominalshik_fai_bot";
  const LS_NOTES = "napomni_notes_v7"; // Увеличил версию
  const LS_CLIENT = "napomni_client_id_v5";
  const LS_FILTER = "napomni_filter_v1";

  const el = (id)=>document.getElementById(id);
  const toastEl = el("toast");
  const showToast = (t)=>{
    toastEl.textContent = t;
    toastEl.classList.add("show");
    setTimeout(()=>toastEl.classList.remove("show"), 1700);
  };

  // Функции для модального окна
  const modalOverlay = el("photoModal");
  const modalImage = el("modalImage");
  const modalCaption = el("modalCaption");

  function openModal(imageSrc, caption) {
    modalImage.src = imageSrc;
    modalCaption.textContent = caption || "Фото";
    modalOverlay.classList.add("active");
    document.body.style.overflow = "hidden"; // запрещаем прокрутку
  }

  function closeModal() {
    modalOverlay.classList.remove("active");
    document.body.style.overflow = ""; // возвращаем прокрутку
  }

  // Закрытие по Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modalOverlay.classList.contains("active")) {
      closeModal();
    }
  });

  function uuidShort(){
    const a = Math.random().toString(16).slice(2,10);
    const b = Date.now().toString(16).slice(-6);
    return (a+b).slice(0, 20);
  }

  function getClientId(){
    let id = localStorage.getItem(LS_CLIENT);
    if(!id){
      id = uuidShort();
      localStorage.setItem(LS_CLIENT, id);
    }
    return id;
  }

  function escapeHtml(s){
    return (s||"").replace(/[&<>"']/g, m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
  }

  async function fileToBase64(file){
    return new Promise((resolve,reject)=>{
      const r = new FileReader();
      r.onload = ()=>resolve(r.result);
      r.onerror = ()=>reject(new Error("read error"));
      r.readAsDataURL(file);
    });
  }

  const loadNotes = ()=> { 
    try { 
      const notes = JSON.parse(localStorage.getItem(LS_NOTES) || "[]");
      // Добавляем поле completed, если его нет
      return notes.map(n => ({ ...n, completed: n.completed || false }));
    } catch { 
      return []; 
    } 
  };
  
  const saveNotes = (arr)=> localStorage.setItem(LS_NOTES, JSON.stringify(arr));

  function fmt(dtISO){
    try{
      const d = new Date(dtISO);
      return d.toLocaleString("ru-RU", {year:"numeric", month:"2-digit", day:"2-digit", hour:"2-digit", minute:"2-digit"});
    }catch{ return dtISO; }
  }

  function validateWhen(datetimeLocalValue){
    if(!datetimeLocalValue) return {ok:false, msg:"Нужно время"};
    const selected = new Date(datetimeLocalValue);
    if(isNaN(selected.getTime())) return {ok:false, msg:"Неверное время"};

    const now = new Date();
    if(selected.getTime() <= now.getTime()){
      return {ok:false, msg:"Нельзя ставить на текущее время или в прошлое"};
    }
    return {ok:true};
  }

  // Текущий фильтр
  let currentFilter = localStorage.getItem(LS_FILTER) || "all";

  function setFilter(filter) {
    currentFilter = filter;
    localStorage.setItem(LS_FILTER, filter);
    
    document.querySelectorAll('.filter-tab').forEach(tab => {
      const tabFilter = tab.dataset.filter;
      if (tabFilter === filter) {
        tab.classList.add('active');
      } else {
        tab.classList.remove('active');
      }
    });
    
    render();
  }

  document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      setFilter(tab.dataset.filter);
    });
  });

  function render(){
    const q = (el("q").value || "").trim().toLowerCase();
    const list = el("list");
    let notes = loadNotes();
    
    notes = notes.filter(n => {
      if (currentFilter === 'active') return !n.completed;
      if (currentFilter === 'completed') return n.completed;
      return true;
    });
    
    notes = notes.filter(n => !q || (n.title + n.desc).toLowerCase().includes(q));
    
    notes.sort((a,b) => {
      if (a.completed !== b.completed) {
        return a.completed ? 1 : -1;
      }
      return new Date(a.when) - new Date(b.when);
    });

    list.innerHTML = "";
    if(!notes.length){
      list.innerHTML = `<div class="muted" style="padding:14px 2px; font-weight:900;">Пока пусто ✨</div>`;
      return;
    }

    for(const n of notes){
      const wrap = document.createElement("div");
      wrap.className = "note" + (n.completed ? " completed" : "");
      
      const left = document.createElement("div");
      
      let statusHtml = '';
      if (n.completed) {
        statusHtml = '<span class="badge-completed">✅ Выполнено</span>';
      }
      
      left.innerHTML = `
        <div class="meta">${fmt(n.when)} ${statusHtml}</div>
        <h3>${escapeHtml(n.title || "Без названия")}</h3>
        ${n.desc ? `<div class="txt">${escapeHtml(n.desc)}</div>` : ""}
        <div class="actions">
          ${!n.completed ? `
            <button class="ghost small" data-act="edit">Редакт.</button>
            <button class="danger small" data-act="del">Удалить</button>
          ` : `
            <button class="ghost small" data-act="del">Удалить</button>
          `}
        </div>
        ${!n.completed ? `
          <div class="muted" style="font-size:12px; margin-top:8px; font-weight:900;">
            ⏳ ожидает отправки в Telegram
          </div>
        ` : ''}
      `;
      wrap.appendChild(left);

      // Контейнер для фото или плейсхолдера
      if(n.photo){
        const img = document.createElement("img");
        img.className = "thumb";
        img.src = n.photo;
        img.alt = "Фото к напоминанию";
        img.title = "Нажмите для увеличения";
        
        // Добавляем обработчик клика для открытия модального окна
        img.addEventListener("click", (e) => {
          e.stopPropagation(); // предотвращаем всплытие события
          openModal(n.photo, n.title);
        });
        
        wrap.appendChild(img);
      }else{
        const ph = document.createElement("div");
        ph.className = "thumb-placeholder";
        ph.textContent = "📷";
        wrap.appendChild(ph);
      }

      // Обработчики кнопок
      wrap.addEventListener("click", async (e)=>{
        const btn = e.target.closest("button");
        if(!btn) return;
        const act = btn.dataset.act;
        e.stopPropagation();

        if(act==="del"){
          await deleteReminder(n.id);
          return;
        }

        if(act==="edit"){
          startEdit(n.id);
          return;
        }
      });

      list.appendChild(wrap);
    }
  }

  async function checkConnected(){
    const client_id = getClientId();
    try{
      const r = await fetch(API_BASE + "/status?client_id=" + encodeURIComponent(client_id), {method:"GET"});
      const j = await r.json();
      const st = el("connStatus");
      if(j && j.connected){
        st.textContent = "Подключено ✅ Можно добавлять напоминания.";
        st.className = "hint connected";
        return true;
      }else{
        st.textContent = "Не подключено. Нажми “Подключить Telegram”.";
        st.className = "hint notconnected";
        return false;
      }
    }catch{
      const st = el("connStatus");
      st.textContent = "Сервер недоступен. Проверь Render.";
      st.className = "hint notconnected";
      return false;
    }
  }

  el("connectBtn").addEventListener("click", ()=>{
    const client_id = getClientId();
    const deep = "https://t.me/" + BOT_USERNAME + "?start=" + encodeURIComponent(client_id);
    window.open(deep, "_blank");
    showToast("Открой бота и нажми Start");
  });

  async function apiPost(path, payload){
    const r = await fetch(API_BASE + path, {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });
    const j = await r.json().catch(()=>null);
    if(!r.ok) throw new Error((j && (j.detail || j.error)) || ("http_" + r.status));
    return j;
  }

  async function refreshFromServer(){
    const client_id = getClientId();
    try{
      const r = await fetch(API_BASE + "/list?client_id=" + encodeURIComponent(client_id), {method:"GET"});
      const j = await r.json();
      if(!j || !Array.isArray(j.items)) return;

      const serverItems = j.items;
      const local = loadNotes();
      
      const serverMap = new Map();
      serverItems.forEach(item => serverMap.set(String(item.id), item));
      
      let changed = false;
      const updated = local.map(localNote => {
        const serverNote = serverMap.get(String(localNote.id));
        if (serverNote) {
          serverMap.delete(String(localNote.id));
          return localNote;
        } else {
          changed = true;
          return { ...localNote, completed: true };
        }
      });
      
      serverMap.forEach((item, id) => {
        changed = true;
        updated.push({
          id: item.id,
          title: item.title,
          desc: item.desc,
          when: item.when,
          photo: item.photo,
          completed: false
        });
      });
      
      if (changed) {
        saveNotes(updated);
        render();
      }
    } catch(e){
      console.log("Sync error:", e);
    }
  }

  let editingId = null;

  function startEdit(id){
    const n = loadNotes().find(x=>x.id===id);
    if(!n || n.completed) {
      showToast("Нельзя редактировать выполненное");
      return;
    }

    editingId = id;
    el("editBadge").style.display = "";
    el("cancelEditBtn").style.display = "";

    el("title").value = n.title || "";
    el("desc").value = n.desc || "";
    el("when").value = (n.when || "").slice(0,16);
    el("photo").value = "";
    showToast("Редактирование");
  }

  function stopEdit(){
    editingId = null;
    el("editBadge").style.display = "none";
    el("cancelEditBtn").style.display = "none";
    el("title").value=""; el("desc").value=""; el("when").value=""; el("photo").value="";
  }

  el("cancelEditBtn").addEventListener("click", ()=>{
    stopEdit();
    showToast("Отмена");
  });

  async function deleteReminder(id){
    try{
      await apiPost("/delete", {client_id: getClientId(), id});
    } catch(e){
      // даже если сервер недоступен — уберём локально
    }
    saveNotes(loadNotes().filter(x=>x.id!==id));
    render();
    if(editingId === id) stopEdit();
    showToast("Удалено");
  }

  async function upsertReminder(note){
    const arr = loadNotes();
    const idx = arr.findIndex(x=>x.id===note.id);
    if(idx>=0) {
      note.completed = arr[idx].completed || false;
      arr[idx] = note;
    } else {
      note.completed = false;
      arr.push(note);
    }
    saveNotes(arr);
    render();

    await apiPost("/upsert", {
      client_id: getClientId(),
      id: note.id,
      title: note.title,
      desc: note.desc,
      when: note.when,
      photo: note.photo || null
    });
  }

  el("saveBtn").addEventListener("click", async ()=>{
    const title = (el("title").value || "").trim();
    const whenVal = (el("when").value || "").trim();
    const desc = (el("desc").value || "").trim();
    const file = el("photo").files[0];

    if(!title){ showToast("Нужен заголовок"); return; }

    const val = validateWhen(whenVal);
    if(!val.ok){ showToast(val.msg); return; }

    const connected = await checkConnected();
    if(!connected){ showToast("Сначала подключи Telegram"); return; }

    let photo64 = null;
    if(file){
      try{ photo64 = await fileToBase64(file); }catch{}
    }

    const id = editingId || (uuidShort() + "-" + Date.now().toString(16));
    const existing = loadNotes().find(x=>x.id===id);

    if (editingId && existing?.completed) {
      showToast("Нельзя редактировать выполненное напоминание");
      return;
    }

    const note = {
      id,
      title,
      desc,
      when: new Date(whenVal).toISOString(),
      photo: (photo64 !== null) ? photo64 : (existing ? existing.photo : null)
    };

    try{
      await upsertReminder(note);
      showToast(editingId ? "Обновлено ✅" : "Создано ✅");
      stopEdit();
    }catch(e){
      showToast("Не отправлено: " + String(e.message || e));
    }
  });

  el("clearBtn").addEventListener("click", ()=>{
    el("title").value=""; el("desc").value=""; el("when").value=""; el("photo").value="";
    showToast("Очищено");
  });

  el("wipeBtn").addEventListener("click", async ()=>{
    if (!confirm("Точно удалить ВСЕ напоминания?")) return;
    
    try{
      await apiPost("/wipe", {client_id: getClientId()});
    } catch(e){}
    saveNotes([]);
    render();
    stopEdit();
    showToast("Удалено всё");
  });

  el("hideCompletedBtn").addEventListener("click", ()=>{
    if (currentFilter === 'active') {
      setFilter('all');
    } else {
      setFilter('active');
    }
  });

  el("q").addEventListener("input", render);

  // Инициализация
  setFilter(currentFilter);
  checkConnected();
  setInterval(refreshFromServer, 5000);
</script>
</body>
</html>
