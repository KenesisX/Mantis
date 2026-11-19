"use strict";
// MANTIS dashboard — talks to the stdlib JSON API.

const $ = (id) => document.getElementById(id);
let STATE = null;
let SPELLS = [];
let STAGES = [];

async function api(path, body) {
  const opt = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : {};
  const r = await fetch(path, opt);
  return r.json();
}

function toast(msg) {
  const t = document.createElement("div");
  t.className = "toast";
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2600);
}

function shake(effect) {
  const root = $("shake-root");
  const cls = effect === "scream" ? "scream" : "shake";
  root.classList.remove("shake", "scream");
  void root.offsetWidth;
  root.classList.add(cls);
  setTimeout(() => root.classList.remove(cls), 1200);
}

// ---- rendering ------------------------------------------------------- //
function render(s) {
  if (!s) return;
  STATE = s;
  $("pet-name").textContent = s.name;
  $("rank").textContent = s.rank;
  $("level").textContent = s.level;
  $("age").textContent = "age " + s.age;
  $("xp-text").textContent = `${s.xp} / ${s.xp_to_next}`;
  $("xp-fill").style.width = s.xp_pct + "%";
  $("psy-text").textContent = `${Math.round(s.psyche)} / ${Math.round(s.psyche_max)}`;
  $("psy-fill").style.width = (s.psyche_pct ?? 0) + "%";
  $("dark-text").textContent = Math.round(s.darkness);
  $("dark-fill").style.width = (s.darkness ?? 0) + "%";
  $("souls").textContent = s.souls ?? 0;
  $("infamy").textContent = s.infamy ?? 0;
  // battery chip
  const bat = $("battery");
  if (s.battery) {
    const p = Math.round(s.battery.percent);
    bat.classList.remove("hidden", "low", "crit");
    if (p <= 10) bat.classList.add("crit"); else if (p <= 20) bat.classList.add("low");
    $("batt-fill").style.width = Math.max(4, p) + "%";
    $("batt-pct").textContent = p + "%" + (s.battery.charging ? "⚡" : "");
  } else {
    bat.classList.add("hidden");
  }
  // inner mind (adaptive coach)
  if (s.coach) renderCoach(s.coach);
  // keeper / persona
  if (s.reading) { const r = $("reading"); if (r) r.textContent = s.reading; }
  if (s.persona) renderPersona(s.persona);
  // academy
  if (s.academy) renderAcademy(s.academy);
  // security posture
  if (s.posture) {
    const p = s.posture;
    const g = $("pos-grade");
    g.textContent = p.grade;
    g.className = "posgrade " + (p.grade === "?" ? "unknown" : p.grade.toLowerCase());
    $("pos-score").textContent = (p.score == null ? "—" : p.score) + " / 100  (" +
      p.known + "/" + p.total + " wards)";
    $("tab-posture").innerHTML = (p.components || []).map((c) =>
      `<div class="prow"><span class="k"><span class="pg ${c.grade === "?" ? "unknown" : c.grade}">${c.grade}</span>
        ${esc(c.label)}</span><span class="v">${c.score == null ? "— " + esc(c.note) : c.score + " · " + esc(c.note)}</span></div>`
    ).join("");
  }
  // evolution stage
  if (s.stage) {
    $("evo-current").textContent = `LV${s.stage.lvl} · ${s.stage.label}`;
    renderEvo(s.stage.lvl);
  }
  // darkness tints the whole page
  document.body.style.setProperty("--dark-level", (s.darkness ?? 0) / 100);
  document.getElementById("shake-root").style.filter =
    s.darkness > 70 ? "contrast(1.12) brightness(.92)" : "none";
  $("n-hunger").style.width = s.needs.hunger + "%";
  $("n-energy").style.width = s.needs.energy + "%";
  $("n-focus").style.width = s.needs.focus + "%";
  $("n-sanity").style.width = s.needs.sanity + "%";
  $("speech").textContent = s.phrase;

  // face expression
  const mask = $("mask");
  mask.setAttribute("class", "mask " + (s.face_web || "watching"));

  // counters
  const st = s.stats;
  $("counters").innerHTML = [
    ["kills", "severed"], ["kidnappings", "kidnapped"], ["possessions", "possessed"],
    ["souls_harvested", "harvested"], ["networks_sensed", "minds heard"],
    ["spells_cast", "spells"], ["meditations", "meditations"], ["best_level", "peak lv"],
  ].map(([k, lbl]) => `<div class="c"><b>${st[k] ?? 0}</b><span>${lbl}</span></div>`).join("");

  // captives bar + tab
  const pawns = s.pawns || [];
  $("pawnbar").textContent = pawns.length
    ? `${pawns.length} mind(s) held captive — ready to harvest.`
    : "No minds captured.";
  renderList("tab-pawns", pawns, (p) =>
    `<div class="row"><span class="k">${p.deed === "kidnap" ? "⛓" : "🌀"} ${esc(p.who)}</span>
      <span class="v">${esc(p.deed)}</span></div>`);

  renderLog(s.log);
  renderList("tab-nets", s.known_networks, (n) =>
    `<div class="row"><span class="k">📡 ${esc(n.ssid)}</span>
      <span class="v">${n.signal ?? "?"}% · ${esc(n.security || "?")}${n.sim ? " · sim" : ""}</span></div>`);
  renderList("tab-devs", s.known_devices, (d) =>
    `<div class="row"><span class="k">👤 ${esc(d.ip)}</span>
      <span class="v">${esc(d.name || "unknown")}${d.sim ? " · sim" : ""}</span></div>`);
  $("tab-ach").innerHTML = (s.achievements && s.achievements.length)
    ? s.achievements.map((a) => `<span class="badge">★ ${esc(a)}</span>`).join("")
    : `<div class="logline">No relics yet. Grow stronger.</div>`;
}

function renderLog(log) {
  $("tab-log").innerHTML = (log || []).slice().reverse().map((e) =>
    `<div class="logline ${esc(e.kind)}"><span class="ts">${esc(e.ts)}</span>${esc(e.text)}</div>`
  ).join("");
}

function renderList(id, items, fn) {
  const el = $(id);
  if (!items || !items.length) { el.innerHTML = `<div class="logline">Nothing sensed yet.</div>`; return; }
  el.innerHTML = items.slice().reverse().map(fn).join("");
}

function renderSpells() {
  $("spellgrid").innerHTML = SPELLS.map((sp) => `
    <div class="spell ${sp.unlocked ? "" : "locked"}" data-spell="${sp.id}">
      <span class="school">${esc(sp.school)}</span>
      <div class="g">${sp.glyph}</div>
      <div class="nm">${esc(sp.name)}</div>
      <div class="meta"><span class="cost">◈${sp.psyche_cost}</span> ·
        <span class="xpv">+${sp.xp}xp</span>
        ${sp.unlocked ? "" : ` · 🔒lv${sp.min_level}`}</div>
      <div class="d">${esc(sp.desc)}</div>
    </div>`).join("");
  document.querySelectorAll(".spell").forEach((el) => {
    el.addEventListener("click", () => doCast(el.dataset.spell));
  });
}

const esc = (s) => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// ---- actions --------------------------------------------------------- //
async function doAction(action) {
  const res = await api("/api/action", { action });
  if (res.message) toast(res.message);
  if (res.state) render(res.state);
}

async function doCast(spellId) {
  const sp = SPELLS.find((x) => x.id === spellId);
  if (sp && !sp.unlocked) { toast(`🔒 Locked — reach level ${sp.min_level}`); return; }
  const res = await api("/api/cast", { spell: spellId });
  if (!res.ok) { toast("✖ " + (res.error || "cast failed")); if (res.state) render(res.state); return; }
  const r = res.result || {};
  if (r.effect === "shake") shake("shake");
  if (r.effect === "scream") shake("scream");
  showModal(r);
  if (res.state) render(res.state);
  // refresh spellbook unlock state
  const sres = await api("/api/spells");
  SPELLS = sres.spells; renderSpells();
}

async function doDeed(deed) {
  const res = await api("/api/deed", { deed });
  if (!res.ok) { toast("✖ " + (res.error || "blocked")); if (res.state) render(res.state); return; }
  shake("shake");
  toast(res.summary || "deed done");
  if (res.state) render(res.state);
  refreshSpellsUnlock();
}

async function doHarvest() {
  const res = await api("/api/harvest", {});
  toast(res.ok ? (res.summary || "harvested") : ("✖ " + (res.error || "nothing to harvest")));
  if (res.state) render(res.state);
}

async function loadShop() {
  const res = await api("/api/augments");
  const augs = res.augments || [];
  $("shopgrid").innerHTML = augs.map((a) => {
    const cls = a.maxed ? "aug maxed" : (a.affordable ? "aug" : "aug poor");
    const price = a.maxed ? "MAX" : `◇${a.cost}`;
    return `<div class="${cls}" data-aug="${a.id}">
      <span class="atier">T${a.tier}/${a.max_tier}</span>
      <div class="ag">${a.glyph}</div><div class="an">${esc(a.name)}</div>
      <div class="ad">${esc(a.desc)}</div>
      <div class="acost">${price}</div></div>`;
  }).join("");
  document.querySelectorAll(".aug").forEach((el) =>
    el.addEventListener("click", () => doBuy(el.dataset.aug)));
}

async function doBuy(id) {
  const res = await api("/api/buy", { augment: id });
  toast(res.ok ? `Augment → tier ${res.tier} (−◇${res.spent})` : ("✖ " + (res.error || "cannot buy")));
  if (res.state) render(res.state);
  loadShop();
}

let PERSONA_BUILT = false;
let INTEREST_CATALOG = {};
async function buildPersonaControls() {
  let meta;
  try { meta = await api("/api/persona"); } catch (e) { return; }
  INTEREST_CATALOG = meta.interests || {};
  const ints = $("pf-interests");
  if (ints) {
    ints.innerHTML = Object.entries(INTEREST_CATALOG).map(([k, label]) =>
      `<span class="ichip" data-int="${k}">${esc(label)}</span>`).join("");
    ints.querySelectorAll(".ichip").forEach((c) =>
      c.addEventListener("click", () => c.classList.toggle("on")));
  }
  const tr = $("pf-traits");
  if (tr) {
    tr.innerHTML = (meta.traits || []).map((t) =>
      `<div class="traitrow"><label>${t}</label>
        <input type="range" min="0" max="100" data-trait="${t}" id="tr-${t}">
        <b id="trv-${t}">50</b></div>`).join("");
    (meta.traits || []).forEach((t) => {
      const el = $("tr-" + t);
      if (el) el.addEventListener("input", () => { $("trv-" + t).textContent = el.value; });
    });
  }
  PERSONA_BUILT = true;
  const sv = $("pf-save");
  if (sv) sv.addEventListener("click", savePersona);
}

function renderPersona(p) {
  if (!PERSONA_BUILT) return;
  if (document.activeElement && document.activeElement.closest &&
      document.activeElement.closest(".keeper-panel")) return;  // don't stomp edits
  if ($("pf-keeper")) $("pf-keeper").value = p.keeper || "";
  if ($("pf-mantis")) $("pf-mantis").value = (window.STATE && STATE.name) || "";
  if ($("pf-exp")) $("pf-exp").value = p.experience || "beginner";
  if ($("pf-style")) $("pf-style").value = p.style || "poetic";
  document.querySelectorAll(".ichip").forEach((c) =>
    c.classList.toggle("on", (p.interests || []).includes(c.dataset.int)));
  Object.entries(p.traits || {}).forEach(([t, v]) => {
    const el = $("tr-" + t); if (el) { el.value = v; const b = $("trv-" + t); if (b) b.textContent = v; }
  });
}

async function savePersona() {
  const interests = Array.from(document.querySelectorAll(".ichip.on")).map((c) => c.dataset.int);
  const traits = {};
  document.querySelectorAll("[data-trait]").forEach((el) => traits[el.dataset.trait] = +el.value);
  const body = {
    keeper: $("pf-keeper").value, mantis_name: $("pf-mantis").value,
    experience: $("pf-exp").value, style: $("pf-style").value,
    interests, traits, configured: true,
  };
  const res = await api("/api/persona", body);
  if (res.reading) $("reading").textContent = res.reading;
  toast("🧠 MANTIS attunes to you");
  if (res.state) render(res.state);
}

let LESSON_LOCK = false;   // don't re-render the lesson card mid-answer
function renderAcademy(a) {
  $("acad-rank").textContent = a.tier;
  $("acad-fill").style.width = (a.pct || 0) + "%";
  $("acad-meta").textContent =
    `${a.completed} / ${a.total} lessons · ${a.knowledge_xp} knowledge · quiz ${a.quiz_accuracy}%`;
  if (LESSON_LOCK) return;
  const el = $("lesson");
  if (!a.next) {
    el.className = "lesson done";
    el.innerHTML = `<div class="ldone">✓ All ${a.total} lessons complete — mastery achieved.</div>`;
    return;
  }
  const L = a.next;
  el.className = "lesson";
  el.innerHTML =
    `<div class="ltopic">${esc(L.topic)} · TIER ${L.tier}${L.spell ? " · spell: " + esc(L.spell) : ""}</div>
     <div class="ltitle">${esc(L.title)}</div>
     <div class="lbody">${esc(L.body)}</div>
     <div class="ltip">💡 ${esc(L.tip)}</div>
     <div class="lq">${esc(L.quiz.q)}</div>
     <div id="choices"></div>
     <div class="lfeedback" id="lfeedback"></div>`;
  const ch = el.querySelector("#choices");
  L.quiz.choices.forEach((c, i) => {
    const b = document.createElement("button");
    b.className = "choice";
    b.textContent = `${i + 1}. ${c}`;
    b.onclick = () => answerLesson(L.id, i, b);
    ch.appendChild(b);
  });
}

async function answerLesson(id, choice, btn) {
  LESSON_LOCK = true;
  const res = await api("/api/learn", { lesson: id, answer: choice });
  const fb = $("lfeedback");
  document.querySelectorAll("#choices .choice").forEach((b) => b.disabled = true);
  if (res.correct) {
    btn.classList.add("right");
    fb.innerHTML = `✅ <b style="color:var(--green)">Correct!</b> ${esc(res.explain)}`;
    toast("✅ +knowledge — " + (res.already ? "reviewed" : "lesson passed"));
    setTimeout(() => { LESSON_LOCK = false; if (res.state) render(res.state); }, 2200);
  } else {
    btn.classList.add("wrong");
    const right = document.querySelectorAll("#choices .choice")[res.answer];
    if (right) right.classList.add("right");
    fb.innerHTML = `❌ ${esc(res.explain)}`;
    setTimeout(() => { LESSON_LOCK = false; }, 2600);
  }
  if (res.state) render(res.state);
}

function renderEvo(curLvl) {
  if (!STAGES.length) return;
  $("evogrid").innerHTML = STAGES.map((st) => {
    const cls = st.lvl === curLvl ? "evo cur" : (st.lvl < curLvl ? "evo done" : "evo locked");
    return `<div class="${cls}"><span class="l">LV${st.lvl}</span>${esc(st.label)}</div>`;
  }).join("");
  const cur = document.querySelector(".evo.cur");
  if (cur) cur.scrollIntoView({ block: "nearest", inline: "nearest" });
}

async function refreshSpellsUnlock() {
  const sres = await api("/api/spells");
  SPELLS = sres.spells; renderSpells();
}

function showModal(r) {
  $("modal-title").textContent = r.spell || "Spell";
  $("modal-summary").textContent = r.summary || "";
  const items = r.items || [];
  $("modal-items").innerHTML = items.length
    ? items.map((it) => `<div class="row"><span class="k">${esc(fmtItem(it))}</span></div>`).join("")
    : `<div class="logline">(no echoes returned)</div>`;
  $("modal").classList.remove("hidden");
}

function fmtItem(it) {
  if (it.ssid) return `📡 ${it.ssid}  —  ${it.signal ?? "?"}%  ${it.security || ""}`;
  if (it.ip && it.port === undefined) return `👤 ${it.ip}  ${it.name || ""}${it.present !== undefined ? (it.present ? "  ✅ present" : "  — away") : ""}`;
  if (it.port !== undefined) return `🚪 ${it.port}/${it.service}${it.risky ? "  ⚠ exposed" : ""}`;
  if (it.hop !== undefined) return `🌌 hop ${it.hop}  ${it.ip}`;
  if (it.address) return `💠 ${it.address}`;
  return JSON.stringify(it);
}

// ---- tabs ------------------------------------------------------------ //
document.querySelectorAll(".tab").forEach((t) => {
  t.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
    document.querySelectorAll(".tabview").forEach((x) => x.classList.add("hidden"));
    t.classList.add("active");
    $("tab-" + t.dataset.tab).classList.remove("hidden");
  });
});

document.querySelectorAll("[data-action]").forEach((b) =>
  b.addEventListener("click", () => doAction(b.dataset.action)));
document.querySelectorAll("[data-deed]").forEach((b) =>
  b.addEventListener("click", () => doDeed(b.dataset.deed)));
document.querySelectorAll("[data-harvest]").forEach((b) =>
  b.addEventListener("click", () => doHarvest()));
$("rename-btn").addEventListener("click", async () => {
  const name = prompt("A new name for the Mantis:", STATE ? STATE.name : "");
  if (name) { const r = await api("/api/rename", { name }); if (r.state) render(r.state); }
});
$("modal-close").addEventListener("click", () => $("modal").classList.add("hidden"));
$("modal").addEventListener("click", (e) => { if (e.target.id === "modal") $("modal").classList.add("hidden"); });

// animated codec frequency flicker
setInterval(() => {
  const f = (140 + Math.random() * 0.9).toFixed(2);
  $("freq").textContent = f;
}, 3000);

// ---- poll loop ------------------------------------------------------- //
async function tick() {
  try {
    const s = await api("/api/state");
    render(s);
    $("status-dot").textContent = "● live"; $("status-dot").style.color = "var(--green)";
  } catch (e) {
    $("status-dot").textContent = "● offline"; $("status-dot").style.color = "var(--red)";
  }
}

// ---- inner mind (adaptive coach) --------------------------------------- //
function renderCoach(c) {
  const st = $("coach-style");
  if (st) st.textContent = `${c.style} — ${c.style_desc || ""}`;
  const g = $("coachsugs");
  if (!g) return;
  const sugs = c.suggestions || [];
  if (!sugs.length) {
    g.innerHTML = `<div class="cwhy">Act, and I'll reveal your next step.</div>`;
    return;
  }
  g.innerHTML = sugs.map((s, i) =>
    `<div class="csug" data-i="${i}">
      <span class="cgo">➤</span>
      <span class="ctext">${esc(s.text)}<div class="cwhy">${esc(s.why || "")}</div></span>
      ${s.teach ? '<span class="cteach">learn</span>' : ""}
    </div>`).join("");
  g.querySelectorAll(".csug").forEach((el) =>
    el.addEventListener("click", () => runSuggestion(sugs[+el.dataset.i])));
}

async function runSuggestion(s) {
  const t = s.cmd.type, id = s.cmd.id;
  let res = null;
  if (t === "action") res = await api("/api/action", { action: id });
  else if (t === "cast") res = await api("/api/cast", { spell: id });
  else if (t === "deed") res = await api("/api/deed", { deed: id });
  else if (t === "harvest") res = await api("/api/harvest", {});
  else if (t === "buy") res = await api("/api/buy", { augment: id });
  else if (t === "learn") {
    const p = document.querySelector(".academy-panel");
    if (p) p.scrollIntoView({ behavior: "smooth", block: "center" });
    toast("📖 Scroll to the Academy to study this");
    return;
  }
  if (res) {
    toast(res.message || (res.result && res.result.summary) || res.summary || "done");
    if (res.state) render(res.state);         // new suggestions appear -> adaptive loop
  }
}

// ---- fleet ------------------------------------------------------------- //
function upfmt(s){ s=s|0; const d=s/86400|0,h=(s%86400)/3600|0,m=(s%3600)/60|0;
  return d?`${d}d${h}h`:(h?`${h}h${m}m`:`${m}m`); }
async function loadFleet(){
  let data; try{ data = await api("/api/fleet"); }catch(e){ return; }
  const g = $("fleetgrid"); if(!g) return;
  const rows = data.fleet || [];
  if(!rows.length){
    g.innerHTML = `<div class="fleet-empty">No devices reporting yet.<br>
      Set a shared key on this hub: <code>mantis fleet key --out &lt;secret&gt;</code><br>
      On each device you own: <code>mantis agent --hub http://THIS-IP:PORT --key &lt;secret&gt;</code></div>`;
    return;
  }
  g.innerHTML = rows.map(d=>{
    const on = d.online ? "on" : "off";
    const batt = d.battery==null ? "—" : d.battery+"%";
    const g2 = d.posture_grade || "?";
    return `<div class="dev ${on}">
      <div class="dname"><span class="dot"></span>${esc(d.name||"?")}</div>
      <div class="dplat">${esc(d.platform||"")} · v${esc(d.version||"?")}</div>
      <div class="drow"><span>level</span><b>${d.level??"?"}</b></div>
      <div class="drow"><span>posture</span><span class="dgrade ${g2}">${g2}${d.posture_score!=null?" ("+d.posture_score+")":""}</span></div>
      <div class="drow"><span>battery</span><span>${batt}</span></div>
      <div class="drow"><span>uptime</span><span>${upfmt(d.uptime_s)}</span></div>
      <div class="drow"><span>${d.online?"online":"last seen"}</span><span>${d.online?"now":upfmt(d.ago)+" ago"}</span></div>
    </div>`;
  }).join("");
}

// ---- theme switcher ---------------------------------------------------- //
function applyTheme(name) {
  document.documentElement.dataset.theme = name;
  try { localStorage.setItem("mantis_theme", name); } catch (e) {}
  const sel = $("theme"); if (sel) sel.value = name;
}
async function initTheme() {
  let name = "red";
  try { name = localStorage.getItem("mantis_theme") || name; } catch (e) {}
  try {
    const meta = await api("/api/persona");
    if (meta && meta.theme) name = meta.theme;    // server config wins on first load
  } catch (e) {}
  applyTheme(name);
  const sel = $("theme");
  if (sel) sel.addEventListener("change", async () => {
    applyTheme(sel.value);
    try { await api("/api/theme", { theme: sel.value }); } catch (e) {}
  });
}

(async function init() {
  await initTheme();
  const sres = await api("/api/spells");
  SPELLS = sres.spells; renderSpells();
  try { STAGES = (await api("/api/stages")).stages || []; } catch (e) { STAGES = []; }
  await buildPersonaControls();
  await loadShop();
  await tick();
  await loadFleet();
  setInterval(tick, 3000);
  setInterval(loadFleet, 6000);
})();
