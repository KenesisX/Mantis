/* MANTIS Command Deck — real-time operator console. Vanilla JS, no deps. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var seenTs = 0, heroSet = false, lessonLock = "", POLL = 1500;
  var loadout = [], ARSENAL = [], duelBusy = false;
  try { loadout = JSON.parse(localStorage.getItem("mantis.loadout") || "[]"); } catch (e) { loadout = []; }

  // ---- theme -------------------------------------------------------- //
  function setTheme(v, persist) {
    document.documentElement.setAttribute("data-t", v);
    [].forEach.call(document.querySelectorAll(".tchip"),
      function (c) { c.classList.toggle("on", c.dataset.v === v); });
    try { if (persist) localStorage.setItem("mantis.theme", v); } catch (e) {}
    if (persist) post("/api/theme", { theme: v });
  }
  $("themes").addEventListener("click", function (e) {
    var c = e.target.closest(".tchip"); if (c) setTheme(c.dataset.v, true);
  });
  try { var th = localStorage.getItem("mantis.theme"); if (th) setTheme(th, false); } catch (e) {}

  // ---- net ---------------------------------------------------------- //
  function post(url, body) {
    return fetch(url, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}) }).then(function (r) { return r.json(); })
      .catch(function () { return {}; });
  }
  function toast(t, i) {
    $("toast-t").textContent = t || ""; $("toast-i").textContent = i || "";
    var el = $("toast"); el.classList.add("show");
    clearTimeout(toast._t); toast._t = setTimeout(function () { el.classList.remove("show"); }, 3200);
  }

  // ---- clock / freq ------------------------------------------------- //
  setInterval(function () {
    $("clock").textContent = new Date().toLocaleTimeString().slice(0, 8);
    $("freq").textContent = (140 + Math.random() * 0.9).toFixed(2);
  }, 1000);

  // ---- actions ------------------------------------------------------ //
  document.querySelector(".care").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-a]"); if (!b) return;
    post("/api/action", { action: b.dataset.a }).then(function (r) {
      if (r.message) toast(b.dataset.a.toUpperCase(), r.message); if (r.state) render(r.state);
    });
  });
  $("deeds").addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    if (b.dataset.harvest) {
      post("/api/harvest", {}).then(function (r) { toast("HARVEST", r.summary || r.error); if (r.state) render(r.state); });
    } else if (b.dataset.d) {
      post("/api/deed", { deed: b.dataset.d }).then(function (r) { toast(b.dataset.d.toUpperCase(), r.summary || r.error); if (r.state) render(r.state); });
    }
  });
  $("rename").addEventListener("click", function () {
    var n = prompt("What shall MANTIS answer to?"); if (!n) return;
    post("/api/rename", { name: n }).then(function (r) { if (r.state) render(r.state); });
  });
  $("modesw").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-m]"); if (!b) return;
    post("/api/mode", { mode: b.dataset.m }).then(function (r) {
      toast("MODE", r.mode === "passive" ? "Passive watch — acts only when asked." : "Active — hunting the ether.");
      if (r.state) render(r.state);
    });
  });
  // run an activity from the deck
  $("agrid").addEventListener("click", function (e) {
    var a = e.target.closest(".act"); if (!a || a.classList.contains("lock")) return;
    a.classList.add("run");
    post("/api/activity", { activity: a.dataset.key }).then(function (r) {
      if (r.ok) toast(r.stage + " ◈", r.summary);
      else toast("blocked", r.error);
      if (r.state) render(r.state);
      setTimeout(function () { a.classList.remove("run"); }, 1200);
    });
  });
  // inner-mind suggestion → run its command if we understand it
  $("sugs").addEventListener("click", function (e) {
    var s = e.target.closest(".sug"); if (!s) return;
    var cmd = (s.dataset.cmd || "").trim().split(/\s+/);
    var verb = cmd[0], arg = cmd[1] || "";
    if (verb === "do") post("/api/activity", { activity: arg }).then(function (r) { toast(r.stage || "activity", r.summary || r.error); if (r.state) render(r.state); });
    else if (verb === "cast") post("/api/cast", { spell: arg }).then(function (r) { if (r.state) render(r.state); toast("spell", (r.result || {}).summary || ""); });
    else if (verb === "mode") post("/api/mode", { mode: arg }).then(function (r) { if (r.state) render(r.state); });
    else if (["feed", "rest", "meditate", "pet"].indexOf(verb) >= 0) post("/api/action", { action: verb }).then(function (r) { if (r.state) render(r.state); });
    else toast("inner mind", s.querySelector(".t").textContent);
  });

  // ---- stream ------------------------------------------------------- //
  var STREAM_KINDS = { activity: 1, teach: 1, levelup: 1, ascend: 1, deed: 1, harvest: 1,
    learn: 1, unlock: 1, mode: 1, cast: 1, achievement: 1, idle_scan: 1, upgrade: 1, rank_up: 1 };
  function pushEvents(log) {
    if (!log) return;
    var box = $("stream"), frag = document.createDocumentFragment(), added = 0;
    log.forEach(function (ev) {
      if (ev.t <= seenTs || !STREAM_KINDS[ev.kind]) return;
      var d = document.createElement("div");
      var kls = ev.kind === "activity" ? "k-" + (ev.act_kind || "sim") :
        (ev.kind === "levelup" || ev.kind === "ascend" || ev.kind === "rank_up") ? "k-levelup" :
          ev.kind === "teach" ? "k-teach" : "";
      d.className = "ev " + kls + (ev.auto ? " k-auto" : "");
      d.innerHTML = '<span class="ts">' + (ev.ts || "") + "</span>" + esc(ev.text);
      frag.appendChild(d); added++;
    });
    if (added) {
      box.insertBefore(frag, box.firstChild);
      while (box.children.length > 60) box.removeChild(box.lastChild);
    }
    var top = log[log.length - 1]; if (top) seenTs = Math.max(seenTs, top.t);
  }
  function esc(s) { return String(s || "").replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); }

  // ---- ladder ------------------------------------------------------- //
  function renderLadder(level) {
    var box = $("ladder"); if (box.children.length !== 50) {
      box.innerHTML = ""; for (var i = 1; i <= 50; i++) { var s = document.createElement("div"); s.className = "seg"; box.appendChild(s); }
    }
    [].forEach.call(box.children, function (seg, i) {
      var lv = i + 1; seg.className = "seg" + (lv < level ? " done" : lv === level ? " now" : "");
    });
  }

  // ---- activity deck ------------------------------------------------ //
  var KIND_LABEL = { passive: "passive", defense: "defense", sim: "sim" };
  function renderDeck(acts, psyche) {
    if (!acts) return;
    var box = $("agrid");
    if (box._n !== acts.length) { box.innerHTML = ""; box._n = acts.length; box._cells = {}; }
    acts.forEach(function (a) {
      var cell = box._cells[a.key];
      if (!cell) {
        cell = document.createElement("button"); cell.className = "act"; cell.dataset.key = a.key;
        cell.innerHTML = '<span class="cost">◈' + a.psy + '</span><div class="lv">LV' + a.lvl + '</div>' +
          '<div class="nm">' + esc(a.label) + '</div><span class="k ' + a.kind + '">' + (KIND_LABEL[a.kind] || a.kind) + '</span>';
        box.appendChild(cell); box._cells[a.key] = cell;
      }
      var locked = !a.unlocked || psyche < a.psy;
      cell.classList.toggle("lock", locked);
      cell.title = a.unlocked ? (a.label + " — ◈" + a.psy + " psyche" + (psyche < a.psy ? " (need more psyche)" : "")) : ("Unlocks at level " + a.lvl);
    });
  }

  // ---- posture ------------------------------------------------------ //
  function renderPosture(p) {
    if (!p) return;
    $("posscore").textContent = p.score == null ? "—" : p.score;
    $("posgrade").textContent = p.grade || "?";
    $("grade").textContent = p.grade || "?";
    var html = (p.components || []).map(function (c) {
      var cls = c.score == null ? "" : (c.score >= 70 ? "b" : "b bad");
      var mark = c.score == null ? "·" : (c.score >= 70 ? "✓" : "!");
      return '<span class="' + cls + '">' + mark + " " + esc(c.label) + "</span>";
    }).join("  ");
    $("poscomp").innerHTML = html || "cast defensive spells to assess";
  }

  // ---- coach -------------------------------------------------------- //
  function renderCoach(c) {
    if (!c) return;
    $("coachstyle").textContent = c.style ? (c.style + " — " + (c.style_desc || "")) : "learning you…";
    var box = $("sugs");
    box.innerHTML = (c.suggestions || []).slice(0, 3).map(function (s) {
      return '<div class="sug" data-cmd="' + esc(s.cmd || "") + '"><span class="go">➤</span>' +
        '<span class="t">' + esc(s.text) + '<div class="w">' + esc(s.why || "") + "</div></span></div>";
    }).join("") || '<div class="muted" style="font-size:11px">Act, and I will learn your style.</div>';
  }

  // ---- academy ------------------------------------------------------ //
  function renderAcademy(a) {
    if (!a) return;
    $("acadrank").textContent = a.tier || "Script Kiddie";
    $("acadfill").style.width = (a.pct || 0) + "%";
    $("acadmeta").textContent = (a.completed || 0) + "/" + (a.total || 0) + " lessons · " + (a.quiz_accuracy || 0) + "% accuracy";
    var les = a.next, box = $("lesson");
    if (!les) { box.innerHTML = '<div class="muted" style="font-size:11px">All lessons complete — you are certified.</div>'; return; }
    if (lessonLock === les.id) return; lessonLock = les.id;
    box.innerHTML = '<div class="sub" style="color:var(--acc2);font-size:10px">' + esc(les.topic) + " · TIER " + les.tier + "</div>" +
      '<div class="lt">' + esc(les.title) + "</div><div class=\"lb\">" + esc(les.body) + "</div>" +
      '<div style="margin-top:7px;font-size:12px;color:#fff">' + esc(les.quiz.q) + "</div>" +
      les.quiz.choices.map(function (ch, i) { return '<button class="choice" data-i="' + i + '">' + (i + 1) + ". " + esc(ch) + "</button>"; }).join("");
    box.querySelectorAll(".choice").forEach(function (btn) {
      btn.onclick = function () {
        post("/api/learn", { lesson: les.id, answer: parseInt(btn.dataset.i, 10) }).then(function (r) {
          if (r.correct) { btn.style.borderColor = "var(--ok)"; btn.style.color = "#fff"; toast("LESSON PASSED", les.title); lessonLock = ""; }
          else { btn.style.borderColor = "var(--acc)"; toast("Not quite", r.explain || ""); }
          if (r.state) render(r.state);
        });
      };
    });
  }

  // ---- fleet -------------------------------------------------------- //
  function loadFleet() {
    fetch("/api/fleet").then(function (r) { return r.json(); }).then(function (d) {
      var box = $("fleet"), rows = (d.devices || d.roster || []);
      if (!rows.length) { box.innerHTML = '<div class="muted" style="font-size:11px">no devices reporting</div>'; return; }
      box.innerHTML = rows.slice(0, 6).map(function (x) {
        var pos = x.posture || {}; var g = (pos.grade || "?") + (pos.score != null ? " (" + pos.score + ")" : "");
        return '<div class="dev"><div class="dn"><span class="dot"></span>' + esc(x.name || x.id || "device") + "</div>" +
          '<div class="r"><span>lv</span><b>' + (x.level || 0) + "</b></div>" +
          '<div class="r"><span>posture</span><span>' + esc(g) + "</span></div></div>";
      }).join("");
    }).catch(function () {});
  }

  // ---- arena -------------------------------------------------------- //
  function buildLoadout() {
    fetch("/api/arsenal").then(function (r) { return r.json(); }).then(function (d) {
      ARSENAL = d.arsenal || [];
      var box = $("loadout");
      box.innerHTML = ARSENAL.map(function (m) {
        var on = loadout.indexOf(m.id) >= 0 ? " on" : "";
        return '<span class="mv ' + m.school + on + '" data-id="' + m.id + '" title="' +
          esc(m.flavour) + '">' + m.glyph + " " + esc(m.name) + "</span>";
      }).join("");
      box.querySelectorAll(".mv").forEach(function (el) {
        el.onclick = function () {
          var id = el.dataset.id, i = loadout.indexOf(id);
          if (i >= 0) loadout.splice(i, 1);
          else if (loadout.length < 5) loadout.push(id);
          else return toast("Loadout full", "5 moves max — deselect one first.");
          el.classList.toggle("on");
          try { localStorage.setItem("mantis.loadout", JSON.stringify(loadout)); } catch (e) {}
        };
      });
    }).catch(function () {});
  }

  function renderArena(s) {
    var du = s.duels || {};
    $("rec").textContent = (du.won || 0) + "W-" + (du.lost || 0) + "L-" + (du.draw || 0) + "D";
    // nearby peers (only rebuild when the set changes, so buttons stay clickable)
    var peers = s.peers || [], box = $("peers");
    $("peercount").textContent = peers.length ? (peers.length + " sensed") : "none sensed";
    var sig = peers.map(function (p) { return p.id + ":" + p.power + ":" + p.verified; }).join("|");
    if (box._sig !== sig) {
      box._sig = sig;
      if (!peers.length) {
        box.innerHTML = '<div class="muted" style="font-size:11px">No other MANTIS nearby. Put two on the same network with discovery on.</div>';
      } else {
        box.innerHTML = peers.map(function (p) {
          var uv = p.verified === false ? '<span class="uv">⚠</span>' : "";
          return '<div class="peer"><div class="pnm"><b>' + esc(p.name || "?") + "</b> " + uv +
            '<div>LV' + (p.level || 0) + " · pow " + (p.power || 0) + " · " + esc(p.ip || "") + "</div></div>" +
            '<span class="via">' + esc(p.via || "wifi") + "</span>" +
            '<button data-peer="' + esc(p.id) + '">Duel</button></div>';
        }).join("");
        box.querySelectorAll("button[data-peer]").forEach(function (b) {
          b.onclick = function () { runDuel(b.dataset.peer); };
        });
      }
    }
    // duel log
    var dl = $("duellog"), log = (du.log || []).slice().reverse();
    dl.innerHTML = log.length ? log.map(function (e) {
      var cls = e.draw ? "draw" : (e.win ? "win" : "loss");
      var r = e.draw ? "DREW" : (e.win ? "WON" : "LOST");
      var uv = e.verified === false ? " ⚠" : "";
      return '<div class="dl ' + cls + '"><span>vs ' + esc(e.foe || "?") + uv + "</span><span>" + r + "</span></div>";
    }).join("") : '<div class="muted" style="font-size:11px">No duels yet.</div>';
  }

  function runDuel(peerId) {
    if (duelBusy) return; duelBusy = true;
    post("/api/duel", { peer: peerId, mode: loadout.length ? "select" : "auto", loadout: loadout })
      .then(function (res) {
        duelBusy = false;
        if (!res.ok) { toast("Duel", res.error || "failed"); return; }
        showFight(res);
        if (res.state) render(res.state);
      }).catch(function () { duelBusy = false; });
  }

  function showFight(res) {
    var me = res.me || {}, foe = res.foe || {};
    $("d-me").innerHTML = '<div class="fn">' + esc(me.name || "Mantis") + '</div>' +
      '<div class="fi">LV' + (me.level || 0) + " · pow " + (me.power || 0) + "</div>";
    $("d-foe").innerHTML = '<div class="fn">' + esc(foe.name || "?") +
      (foe.verified === false ? ' <span class="uv">⚠</span>' : "") + '</div>' +
      '<div class="fi">LV' + (foe.level || 0) + " · pow " + (foe.power || 0) + "<br>" +
      esc(foe.ip || "") + "<br>MAC " + esc(foe.mac || "—") + "</div>";
    var mhp0 = res.my_hp0 || 100, fhp0 = res.foe_hp0 || 100;
    $("d-mehp").style.width = "100%"; $("d-foehp").style.width = "100%";
    var logEl = $("d-log"); logEl.innerHTML = "";
    $("d-result").textContent = ""; $("d-result").className = "duelresult";
    $("duelmodal").hidden = false;
    var turns = res.turns || [], i = 0;
    function step() {
      if (i >= turns.length) {
        var cls = res.draw ? "" : (res.win ? "win" : "loss");
        if (res.upset) cls = "upset";
        $("d-result").className = "duelresult " + cls;
        $("d-result").textContent = (res.draw ? "DRAW" : (res.win ? "VICTORY" : "DEFEAT")) +
          (res.upset ? " — UNDERDOG UPSET!" : "") + "  " + res.summary;
        return;
      }
      var t = turns[i++];
      $("d-mehp").style.width = Math.max(0, 100 * t.my_hp / mhp0) + "%";
      $("d-foehp").style.width = Math.max(0, 100 * t.foe_hp / fhp0) + "%";
      var d = document.createElement("div");
      d.className = "fl " + t.by + " " + t.kind;
      var verb = t.kind === "miss" ? "misses" : t.kind === "defend" ? "" : "hits for <b>" + (t.dmg || 0) + "</b>";
      var extra = t.kind === "crit" ? " ⚡CRIT" : t.kind === "upset" ? " 💥UPSET" : t.kind === "defend" ? ("+shield/heal") : "";
      d.innerHTML = t.glyph + " <b>" + esc(t.actor) + "</b> " + esc(t.move) + " " + verb + extra;
      logEl.appendChild(d); logEl.scrollTop = logEl.scrollHeight;
      setTimeout(step, 420);
    }
    step();
  }
  $("dclose").onclick = function () { $("duelmodal").hidden = true; };
  $("duelmodal").addEventListener("click", function (e) { if (e.target === $("duelmodal")) $("duelmodal").hidden = true; });

  // ---- main render -------------------------------------------------- //
  function setRing(pct) {
    var c = 214, off = c * (1 - Math.max(0, Math.min(100, pct)) / 100);
    $("psyring").setAttribute("stroke-dashoffset", off);
  }
  function bar(id, v) { var e = $(id); if (e) e.style.width = Math.max(0, Math.min(100, v)) + "%"; }

  function render(s) {
    if (!s) return;
    if (!heroSet) { $("hero").style.backgroundImage = "url(/art/mantis_portrait.webp)"; heroSet = true; }
    $("pname").textContent = s.name; $("rank").textContent = s.rank;
    $("lv").textContent = s.level; document.title = "MANTIS LV" + s.level + " — " + s.rank;
    $("stg").textContent = "> " + (s.stage ? s.stage.label : ""); $("say").textContent = s.phrase || "";
    $("agestr").textContent = s.age || "";
    // psyche ring + bars
    $("psynum").textContent = Math.round(s.psyche);
    setRing(s.psyche_pct || 0);
    bar("xp", s.xp_pct || 0); $("xptxt").textContent = s.xp + "/" + s.xp_to_next;
    bar("dk", s.darkness || 0); $("dktxt").textContent = Math.round(s.darkness);
    ["hunger", "energy", "focus", "sanity"].forEach(function (k) {
      bar("n-" + k, s.needs[k]); $("t-" + k).textContent = Math.round(s.needs[k]);
    });
    $("souls").textContent = s.souls; $("infamy").textContent = s.infamy;
    // mode
    var mode = s.idle_mode || "active";
    [].forEach.call($("modesw").children, function (b) { if (b.dataset) b.classList.toggle("on", b.dataset.m === mode); });
    var big = $("modebig"); big.textContent = mode.toUpperCase(); big.className = "big " + mode;
    $("modedesc").textContent = mode === "passive"
      ? "Quiet watch. MANTIS only senses passively and acts when you command it."
      : "MANTIS hunts the ether on its own, performing activities it has grown into.";
    $("runcount").textContent = (s.activity && s.activity.run) || 0;
    $("nowstg").textContent = s.activity && s.activity.last ? ("last: " + s.activity.last) : "idle";
    // evolution
    renderLadder(s.level);
    if (s.stage) { $("evolabel").textContent = "LV" + s.stage.lvl + " " + s.stage.label; $("evocount").textContent = s.stage.lvl; }
    // deck, posture, coach, academy
    renderDeck(s.activities, s.psyche);
    renderPosture(s.posture);
    renderCoach(s.coach);
    renderAcademy(s.academy);
    renderArena(s);
    // verified badge
    var vb = $("vbadge");
    if (s.verified === false) { vb.textContent = "⚠"; vb.className = "vbadge bad"; vb.title = "UNVERIFIED — this save was edited outside the game"; }
    else { vb.textContent = "✓"; vb.className = "vbadge"; vb.title = "verified — earned, un-tampered"; }
    // battery
    if (s.battery) {
      $("batt").hidden = false; $("batt-p").textContent = Math.round(s.battery.percent) + "%";
      $("batt-i").style.width = Math.max(4, Math.min(100, s.battery.percent)) + "%";
    }
    // stream (append new)
    pushEvents(s.log);
  }

  // ---- loop --------------------------------------------------------- //
  function tick() {
    fetch("/api/state").then(function (r) { return r.json(); }).then(render).catch(function () {});
  }
  tick(); setInterval(tick, POLL);
  loadFleet(); setInterval(loadFleet, 8000);
  buildLoadout();
  // version
  fetch("/api/persona").then(function (r) { return r.json(); }).then(function (d) {
    if (d.theme) { try { if (!localStorage.getItem("mantis.theme")) setTheme(d.theme, false); } catch (e) { setTheme(d.theme, false); } }
  }).catch(function () {});
})();
