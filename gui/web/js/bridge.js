/**
 * bridge.js — Comunicación con Python y lógica de todas las pantallas.
 */

const SCREENS_WITH_SIDEBAR = ["main", "config", "summary", "manual", "duplicates", "groups"];

window.app = (() => {
  let _snapshot = null;
  let _currentScreen = null;
  let _selectedDuplicates = new Set();
  let _selectedManualPath = "";
  let _selectedManualCat  = "";

  // ── Utilidades ─────────────────────────────────────────────────────────────
  const el = id => document.getElementById(id);

  async function api(method, ...args) {
    return await window.pywebview.api[method](...args);
  }

  function catPillClass(cat) {
    if (!cat) return "cat-default";
    const c = cat.toLowerCase();
    if (c.includes("inteligencia") || c.includes(" ia")) return "cat-ia";
    if (c.includes("redes") || c.includes("red"))        return "cat-net";
    if (c.includes("datos") || c.includes("bd"))         return "cat-bd";
    if (c.includes("sistema") || c.includes("so"))       return "cat-so";
    return "cat-default";
  }

  function fileRow(name, sub, badge, badgeClass) {
    return `<div class="file-row">
      <div style="flex:1;min-width:0">
        <div class="file-name" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${name}</div>
        ${sub ? `<div style="font-size:10px;color:var(--text-muted);margin-top:2px">${sub}</div>` : ""}
      </div>
      ${badge ? `<span class="cat-pill ${badgeClass}" style="margin-left:8px;flex-shrink:0">${badge}</span>` : ""}
    </div>`;
  }

  // ── Snapshot ───────────────────────────────────────────────────────────────
  async function refreshSnapshot() {
    _snapshot = await api("snapshot");
    return _snapshot;
  }

  function onSnapshotPush(data) {
    _snapshot = data;
    if (_currentScreen) renderCurrentScreen();
  }

  // ── Navegación ─────────────────────────────────────────────────────────────
  async function navigate(screen) {
    _currentScreen = screen;
    const sidebar  = el("sidebar");
    sidebar.style.display = SCREENS_WITH_SIDEBAR.includes(screen) ? "flex" : "none";

    document.querySelectorAll(".nav-item").forEach(b =>
      b.classList.toggle("active", b.dataset.screen === screen));

    document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
    const target = el(`screen-${screen}`);
    if (target) {
      target.classList.add("active", "fade-in");
      setTimeout(() => target.classList.remove("fade-in"), 300);
    }

    await refreshSnapshot();
    renderCurrentScreen();
  }

  function renderCurrentScreen() {
    const renders = {
      welcome:    renderWelcome,
      main:       renderMain,
      config:     renderConfig,
      groups:     renderGroups,
      summary:    renderSummary,
      duplicates: renderDuplicates,
      manual:     renderManual,
    };
    renders[_currentScreen]?.();
  }

  // ── WELCOME ────────────────────────────────────────────────────────────────
  function renderWelcome() {
    const s      = _snapshot || {};
    const stats  = s.stats  || {};
    const agent  = s.agent  || {};
    const config = s.config || {};
    const recent = (s.recent_files || []).slice(0, 3);

    el("w-folder").textContent    = config.watch_folder || "Sin configurar";
    el("w-organized").textContent = stats.total_organized    ?? 0;
    el("w-precision").textContent = `${stats.average_confidence ?? 0}%`;
    el("w-dupes").textContent     = stats.duplicates_detected ?? 0;
    el("w-status-msg").textContent = s.status_message || "Listo para comenzar.";

    const active = agent.active && !agent.paused;
    el("w-agent-dot").style.background = active ? "var(--success)" : "var(--text-muted)";
    el("w-agent-label").textContent    = active ? "Agente activo — monitoreando" : "Agente inactivo";
    el("w-agent-label").style.color    = active ? "var(--success)" : "var(--text-muted)";
    el("btn-open-panel").style.display = config.watch_folder ? "inline-flex" : "none";

    el("w-recent-list").innerHTML = recent.length === 0
      ? `<div class="file-row" style="justify-content:center"><span style="font-size:10px;color:var(--text-secondary)">Tu actividad aparecerá aquí en cuanto FileMaster organice los primeros archivos.</span></div>`
      : recent.map(f => fileRow(f.name, null, f.category, catPillClass(f.category))).join("");
  }

  // ── MAIN PANEL ─────────────────────────────────────────────────────────────
  function renderMain() {
    const s      = _snapshot || {};
    const stats  = s.stats  || {};
    const agent  = s.agent  || {};
    const config = s.config || {};
    const recent = (s.recent_files || []).slice(0, 6);
    const pending = s.pending_groups || [];

    // Header agent badge
    const active = agent.active && !agent.paused;
    el("m-agent-dot").style.background = active ? "var(--success)" : "var(--warning)";
    el("m-agent-label").textContent    = active ? "Activo" : agent.paused ? "En pausa" : "Inactivo";

    // Pending banner
    const banner = el("m-pending-banner");
    if (pending.length > 0) {
      el("m-pending-text").textContent = `Hay ${pending.length} grupos pendientes de confirmación`;
      banner.style.display = "flex";
    } else {
      banner.style.display = "none";
    }

    // Status msg
    const statusEl = el("m-status-msg");
    if (s.status_message) {
      statusEl.textContent = s.status_message;
      statusEl.style.display = "block";
    } else {
      statusEl.style.display = "none";
    }

    // Config rows
    const dupFolder = config.watch_folder ? `${config.watch_folder}/_Duplicados/` : "Sin configurar";
    const configRows = [
      { icon: "📁", label: "Carpeta monitoreada",   value: config.watch_folder || "Sin configurar", accent: "var(--warning-bg)", edit: true },
      { icon: "✦",  label: "Renombrado IA",         value: config.auto_rename ? "Activado" : "Desactivado", accent: "var(--success-bg)" },
      { icon: "🤖", label: "Modo de operación",      value: `${active ? "Observador en segundo plano" : agent.paused ? "En pausa" : "Inactivo"} — desde ${agent.started_at || "--:--:--"}`, accent: "var(--info-bg)" },
      { icon: "⊗",  label: "Carpeta de duplicados", value: dupFolder, accent: "var(--bg-card-soft)" },
    ];
    el("m-config-rows").innerHTML = configRows.map(r => `
      <div class="config-row">
        <div class="config-row-icon" style="background:${r.accent}">${r.icon}</div>
        <div style="flex:1;min-width:0">
          <div style="font-size:9px;color:var(--text-muted)">${r.label}</div>
          <div style="font-size:11px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${r.value}</div>
        </div>
        ${r.edit ? `<button class="btn btn-secondary" style="padding:4px 10px;font-size:10px" onclick="window.app.navigate('config')">Editar</button>` : ""}
      </div>`).join("");

    // Agent box
    el("m-agent-circle").style.background   = active ? "var(--success-bg)" : "var(--warning-bg)";
    el("m-agent-circle").style.borderColor  = active ? "var(--success)" : "var(--warning)";
    el("m-agent-status").textContent        = active ? "Monitoreando activamente" : agent.paused ? "Agente en pausa" : "Agente inactivo";
    el("m-agent-status").style.color        = active ? "var(--success)" : "var(--warning)";
    el("m-agent-last").textContent          = `Última ejecución: ${agent.last_run || "sin ejecuciones"}`;
    el("btn-toggle-agent").textContent      = agent.paused ? "▶ Reanudar" : "⏸ Pausar";

    // Stats
    el("m-organized").textContent = stats.total_organized    ?? 0;
    el("m-precision").textContent = `${stats.average_confidence ?? 0}%`;
    el("m-folders").textContent   = stats.folders_created    ?? 0;
    el("m-dupes").textContent     = stats.duplicates_detected ?? 0;
    el("m-recent-count").textContent = `${recent.length} recientes`;

    el("m-recent-list").innerHTML = recent.length === 0
      ? `<div style="font-size:11px;color:var(--text-secondary)">Todavía no hay archivos organizados.</div>`
      : recent.map(f => fileRow(f.name, `${f.original} · ${f.time}`, f.category, catPillClass(f.category))).join("");
  }

  // ── CONFIG ─────────────────────────────────────────────────────────────────
  function renderConfig() {
    const s      = _snapshot || {};
    const config = s.config  || {};
    const msg    = s.status_message || "";

    // Status banner
    const cfgStatus = el("cfg-status");
    if (msg) {
      el("cfg-status-text").textContent = msg;
      cfgStatus.style.display = "flex";
    } else {
      cfgStatus.style.display = "none";
    }

    // Folder input (no pisar si el usuario está escribiendo)
    const inp = el("cfg-folder-input");
    if (inp && !inp._focused) inp.value = config.watch_folder || "";
    inp.addEventListener("focus", () => inp._focused = true);
    inp.addEventListener("blur",  () => inp._focused = false);

    const renameEl = el("cfg-rename");
    const dupesEl  = el("cfg-dupes");
    if (renameEl) renameEl.checked = config.auto_rename       ?? true;
    if (dupesEl)  dupesEl.checked  = config.detect_duplicates ?? true;

    updateFolderDisplay();

    // Accesos rápidos — solo se renderizan una vez
    const shortcutsEl = el("cfg-shortcuts");
    if (shortcutsEl && shortcutsEl.children.length === 0) {
      const shortcuts = [
        ["Descargas", "Downloads"],
        ["Documentos", "Documents"],
        ["Escritorio", "Desktop"],
        ["Usuario",    ""],
      ];
      shortcutsEl.innerHTML = shortcuts.map(([label, folder]) => {
        const path = folder
          ? `C:/Users/${(config.watch_folder || "").split("/")[2] || "usuario"}/${folder}`
          : `C:/Users/${(config.watch_folder || "").split("/")[2] || "usuario"}`;
        return `<button class="btn btn-secondary" style="font-size:10px;padding:5px 8px;text-align:left;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
          onclick="window.app.setFolder('${path}')">${label}</button>`;
      }).join("");
    }
  }

  function setFolder(path) {
    const inp = el("cfg-folder-input");
    if (inp) { inp.value = path; updateFolderDisplay(); }
  }

  function updateFolderDisplay() {
    const inp   = el("cfg-folder-input");
    const disp  = el("cfg-folder-display");
    const badge = el("cfg-folder-badge");
    if (!inp || !disp || !badge) return;
    const val = inp.value.trim();
    disp.textContent  = val || "Todavía no has elegido ninguna carpeta.";
    badge.textContent = val ? "Lista para monitoreo" : "Sin seleccionar";
    badge.style.color = val ? "var(--success)" : "var(--text-secondary)";
    badge.style.borderColor = val ? "var(--success)" : "var(--border)";
  }

  // ── GROUPS ─────────────────────────────────────────────────────────────────
  function renderGroups() {
    const s      = _snapshot || {};
    const groups = s.pending_groups || [];
    const total  = groups.reduce((acc, g) => acc + (g.file_names || []).length, 0);

    el("grp-total-files").textContent  = total;
    el("grp-total-groups").textContent = groups.length;
    el("grp-banner-text").textContent  = `Análisis completado — se encontraron ${groups.length} grupos temáticos`;

    const cols = Math.max(1, Math.min(4, groups.length));

    if (groups.length === 0) {
      el("grp-list").innerHTML = `<div class="card"><div style="font-size:14px;font-weight:600;color:var(--text);margin-bottom:6px">No hay grupos pendientes</div><div style="font-size:12px;color:var(--text-secondary)">Vuelve a la configuración y analiza una carpeta con documentos.</div></div>`;
      return;
    }

    el("grp-list").style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    el("grp-list").innerHTML = groups.map(g => `
      <div class="group-card">
        <div style="display:flex;align-items:center;justify-content:space-between">
          <span style="font-size:9px;font-weight:700;color:var(--text-muted);letter-spacing:.08em">${(g.group_id || "").toUpperCase()}</span>
          <span class="cat-pill cat-ia">${(g.file_names || []).length} archivos</span>
        </div>
        <div>
          <div style="font-size:9px;font-weight:700;color:var(--text-muted);letter-spacing:.08em;margin-bottom:6px">PALABRAS CLAVE</div>
          <div style="display:flex;flex-wrap:wrap;gap:5px">
            ${(g.keywords || []).map(k => `<span class="tag">${k}</span>`).join("")}
          </div>
        </div>
        <div>
          <div style="font-size:9px;font-weight:700;color:var(--text-muted);letter-spacing:.08em;margin-bottom:6px">MUESTRA DE ARCHIVOS</div>
          <div style="background:var(--bg-card);border:1px solid var(--border-soft);border-radius:8px;padding:8px 10px">
            ${(g.file_names || []).slice(0, 4).map(n => `<div style="font-size:9px;color:var(--text-secondary);margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${n}</div>`).join("")}
          </div>
        </div>
        <div>
          <div style="font-size:9px;font-weight:700;color:var(--text-muted);letter-spacing:.08em;margin-bottom:6px">NOMBRE DE CARPETA</div>
          <input id="grp-name-${g.group_id}" class="group-name-input" value="${g.suggested_name || ""}" />
        </div>
      </div>`).join("");
  }

  // ── SUMMARY ────────────────────────────────────────────────────────────────
  function renderSummary() {
    const s           = _snapshot || {};
    const summary     = s.last_summary  || {};
    const unclassified = s.unclassified || [];
    const folders     = summary.folders || [];
    const config      = s.config        || {};
    const agent       = s.agent         || {};

    el("sum-subtitle").textContent     = `${config.watch_folder || "Sin configurar"} — ${agent.last_run || "--:--:--"}`;
    el("sum-status-msg").textContent   = s.status_message || "Los archivos detectados fueron clasificados.";
    el("sum-speed").textContent        = `${summary.duration_seconds ?? 0}s`;
    el("sum-precision-val").textContent = `${summary.precision ?? 0}%`;
    el("sum-detected").textContent     = summary.detected     ?? 0;
    el("sum-organized").textContent    = summary.organized    ?? 0;
    el("sum-renamed").textContent      = summary.renamed      ?? 0;
    el("sum-unclassified").textContent = summary.unclassified ?? 0;
    el("sum-dupes").textContent        = summary.duplicates   ?? 0;

    el("sum-folders-count").textContent = `${folders.length} resultados`;
    el("sum-folders").innerHTML = folders.length === 0
      ? `<div style="font-size:11px;color:var(--text-secondary)">Sin carpetas generadas aún.</div>`
      : folders.map(f => `
        <div class="file-row" style="margin-bottom:8px">
          <div style="font-size:13px;margin-right:8px;flex-shrink:0">📁</div>
          <div style="flex:1;min-width:0">
            <div style="font-size:12px;font-weight:600;color:var(--text)">${f.name}</div>
            <div style="font-size:10px;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${f.path}</div>
          </div>
          <span class="cat-pill cat-ia" style="flex-shrink:0;margin-left:8px">${f.count} archivos</span>
        </div>`).join("");

    el("sum-unclassified-count").textContent = `${unclassified.length} pendientes`;

    let unclHtml = "";
    if (unclassified.length > 0) {
      unclHtml += `<div style="background:var(--warning-bg);border:1px solid var(--warning);border-radius:8px;padding:10px 12px;margin-bottom:10px;display:flex;align-items:center;gap:10px">
        <span style="font-size:14px">⚠</span>
        <div>
          <div style="font-size:12px;font-weight:600;color:var(--text)">${unclassified.length} archivos requieren clasificación manual</div>
          <div style="font-size:10px;color:var(--text-secondary);margin-top:2px">La IA no encontró suficiente contenido para clasificarlos</div>
        </div>
      </div>`;
      unclHtml += unclassified.map(f => `
        <div class="file-row" style="margin-bottom:6px">
          <span style="font-size:11px;margin-right:6px">📄</span>
          <span style="font-size:11px;color:var(--text-secondary)">${f.name}</span>
        </div>`).join("");
    } else {
      unclHtml = `<div style="font-size:11px;color:var(--text-secondary)">No hay archivos pendientes de clasificación manual.</div>`;
    }
    el("sum-unclassified-list").innerHTML = unclHtml;
  }

  // ── DUPLICATES ─────────────────────────────────────────────────────────────
  function renderDuplicates() {
    const s      = _snapshot || {};
    const groups = s.duplicate_groups || [];
    const dupCount = groups.reduce((acc, g) => acc + (g.items || []).filter(i => i.state === "Duplicado").length, 0);

    el("dup-badge").textContent = `${groups.length} grupos · ${dupCount} duplicados`;
    _selectedDuplicates = new Set();
    updateDupSelectedCount();

    if (groups.length === 0) {
      el("dup-list").innerHTML = `<div class="card" style="text-align:center;padding:40px;color:var(--text-secondary);font-size:13px">✅ No se detectaron duplicados.</div>`;
      return;
    }

    el("dup-list").innerHTML = groups.map((g, gi) => {
      const isSimilar = (g.mode || "").includes("Levenshtein");
      return `<div class="card" style="margin-bottom:12px">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
          <span style="font-size:12px;font-weight:700;color:var(--text)">${g.title || `Grupo ${gi+1}`}</span>
          <span class="cat-pill ${isSimilar ? "cat-bd" : "cat-net"}">${g.mode || ""}</span>
          <span style="margin-left:auto;font-size:10px;color:var(--text-muted)">${(g.items||[]).length} archivos</span>
        </div>
        ${(g.items || []).map(item => {
          const isOrig = item.state === "Original";
          return `<div class="file-row" style="margin-bottom:6px">
            ${!isOrig ? `<input type="checkbox" class="dup-checkbox" data-path="${item.current_path || item.name}" onchange="window.app.toggleDupSelect(this)">` : `<div style="width:16px;flex-shrink:0"></div>`}
            <div style="flex:1;min-width:0;margin:0 10px">
              <div style="font-size:12px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${item.name}</div>
              <div style="font-size:9px;color:var(--text-muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${item.meta || ""}</div>
            </div>
            <span class="cat-pill ${isOrig ? "cat-net" : "cat-default"}" style="flex-shrink:0">${item.state}</span>
            ${item.detail ? `<span class="cat-pill cat-default" style="flex-shrink:0;margin-left:4px">${item.detail}</span>` : ""}
          </div>`;
        }).join("")}
      </div>`;
    }).join("");
  }

  function toggleDupSelect(checkbox) {
    const path = checkbox.dataset.path;
    if (checkbox.checked) _selectedDuplicates.add(path);
    else _selectedDuplicates.delete(path);
    updateDupSelectedCount();
  }

  function updateDupSelectedCount() {
    el("dup-selected-count").textContent = `${_selectedDuplicates.size} archivos seleccionados`;
  }

  // ── MANUAL CLASSIFY ────────────────────────────────────────────────────────
  function renderManual() {
    const s            = _snapshot || {};
    const unclassified = s.unclassified || [];
    const categories   = (s.categories || []).map(c => c.name || c);

    el("man-pending-badge").textContent = `Pendientes: ${unclassified.length}`;

    if (!_selectedManualPath && unclassified.length > 0) {
      _selectedManualPath = unclassified[0].path;
    }
    if (_selectedManualPath && !unclassified.find(f => f.path === _selectedManualPath)) {
      _selectedManualPath = unclassified[0]?.path || "";
    }
    if (!_selectedManualCat && categories.length > 0) {
      _selectedManualCat = categories[0];
    }

    // Lista de archivos
    el("man-file-list").innerHTML = unclassified.length === 0
      ? `<div style="font-size:12px;color:var(--text-secondary);padding:12px">No hay archivos pendientes. 🎉</div>`
      : unclassified.map(f => `
        <div class="man-file-item ${f.path === _selectedManualPath ? "selected" : ""}" onclick="window.app.selectManualFile('${f.path.replace(/'/g,"\\'")}')">
          <span style="font-size:13px;flex-shrink:0">📄</span>
          <div style="flex:1;min-width:0">
            <div style="font-size:11px;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${f.name}</div>
            <div style="font-size:9px;color:var(--text-muted);margin-top:2px">${f.meta || ""}</div>
          </div>
        </div>`).join("");

    // Detalle
    const file = unclassified.find(f => f.path === _selectedManualPath);
    if (!file) {
      el("man-detail").innerHTML = `<div style="font-size:13px;color:var(--text-secondary);text-align:center;padding:40px 0">Selecciona un archivo de la lista</div>`;
      return;
    }

    el("man-detail").innerHTML = `
      <div class="section-label" style="margin-bottom:10px"><span class="section-dot" style="background:var(--warning)"></span>Archivo seleccionado</div>
      <div style="background:var(--bg-card);border:1px solid var(--border-soft);border-radius:9px;padding:10px 14px;display:flex;align-items:center;gap:10px;margin-bottom:12px">
        <span style="font-size:16px">📄</span>
        <div style="flex:1;min-width:0">
          <div style="font-size:12px;font-weight:600;color:var(--text)">${file.name}</div>
          <div style="font-size:9px;color:var(--text-muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${file.path}</div>
        </div>
      </div>

      <div style="background:#2d2318;border:1px solid #7c4a2a;border-radius:8px;padding:10px 12px;margin-bottom:14px">
        <div style="font-size:9px;font-weight:700;color:var(--warning);letter-spacing:.08em;margin-bottom:6px">¿POR QUÉ NO PUDO CLASIFICARSE?</div>
        <div style="font-size:11px;color:var(--text-secondary)">${file.reason || "No se encontró suficiente contenido de texto."}</div>
      </div>

      <div class="section-label" style="margin-bottom:10px"><span class="section-dot" style="background:var(--primary)"></span>Selecciona la carpeta destino</div>

      ${categories.map(name => `
        <div class="man-cat-item ${name === _selectedManualCat ? "selected" : ""}" onclick="window.app.selectManualCat('${name.replace(/'/g,"\\'")}')">
          <span style="font-size:12px">📁</span>
          <div style="flex:1;min-width:0">
            <div style="font-size:12px;color:var(--text)">${name}</div>
            <div style="font-size:9px;color:var(--text-muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${(_snapshot?.config?.watch_folder || "")}/${name}</div>
          </div>
          ${name === _selectedManualCat ? `<span style="color:var(--primary-light);font-size:14px">✓</span>` : ""}
        </div>`).join("")}

      <div style="background:var(--bg-card);border:1px solid var(--border-soft);border-radius:9px;display:flex;align-items:center;margin-bottom:14px">
        <input id="man-new-folder" type="text" placeholder="+ Crear nueva carpeta..."
          style="flex:1;background:transparent;color:var(--text);border:none;padding:9px 12px;font-family:var(--font);font-size:12px;outline:none" />
        <span style="font-size:11px;color:var(--primary-light);padding-right:12px;cursor:pointer" onclick="window.app.doManualNewFolder()">Crear</span>
      </div>

      <div style="display:flex;gap:10px;margin-top:auto">
        <button class="btn btn-secondary" onclick="window.app.navigate('summary')">Omitir archivo</button>
        <button class="btn btn-primary" style="flex:1" onclick="window.app.doManualMove()">Mover a carpeta seleccionada →</button>
      </div>`;
  }

  function selectManualFile(path) {
    _selectedManualPath = path;
    renderManual();
  }

  function selectManualCat(name) {
    _selectedManualCat = name;
    renderManual();
  }

  // ── Acciones ───────────────────────────────────────────────────────────────
  async function doOrganizeNow() {
    const btn = el("btn-organize");
    if (btn) { btn.disabled = true; btn.textContent = "Organizando..."; }
    await api("organize_now");
    if (btn) { btn.disabled = false; btn.textContent = "⚡ Organizar"; }
    const snap = await refreshSnapshot();
    if (snap.pending_groups?.length > 0) navigate("groups");
    else navigate("summary");
  }

  async function doToggleAgent() {
    await api("toggle_agent");
    await refreshSnapshot();
    renderMain();
  }

  async function doPickFolder() {
    const folder = await api("open_folder_dialog");
    if (folder) setFolder(folder);
  }

  async function doSaveAndAnalyze() {
    const folder = el("cfg-folder-input")?.value?.trim() || "";
    if (!folder) {
      alert("Selecciona una carpeta antes de continuar.");
      return;
    }
    const rename = el("cfg-rename")?.checked ?? true;
    const dupes  = el("cfg-dupes")?.checked  ?? true;
    await api("update_config", folder, rename, dupes);
    const btn = document.querySelector("#screen-config .btn-primary");
    if (btn) { btn.disabled = true; btn.textContent = "Analizando..."; }
    await api("analyze_initial");
    if (btn) { btn.disabled = false; btn.textContent = "Analizar carpeta y continuar →"; }
    const snap = await refreshSnapshot();
    if (snap.pending_groups?.length > 0) navigate("groups");
    else navigate("main");
  }

  async function doConfirmGroups() {
    const groups = (_snapshot?.pending_groups || []);
    const mapping = {};
    groups.forEach(g => {
      const inp = el(`grp-name-${g.group_id}`);
      if (inp) mapping[g.group_id] = inp.value.trim();
    });
    await api("confirm_groups", mapping);
    navigate("summary");
  }

  async function doRestoreDuplicates() {
    if (_selectedDuplicates.size === 0) return;
    await api("restore_duplicates", [..._selectedDuplicates]);
    await refreshSnapshot();
    renderDuplicates();
  }

  async function doDeleteDuplicates() {
    if (_selectedDuplicates.size === 0) return;
    if (!confirm(`¿Seguro que deseas eliminar ${_selectedDuplicates.size} archivo(s) duplicado(s)?`)) return;
    await api("delete_duplicates", [..._selectedDuplicates]);
    await refreshSnapshot();
    renderDuplicates();
  }

  async function doManualMove() {
    if (!_selectedManualPath || !_selectedManualCat) return;
    await api("manual_classify", _selectedManualPath, _selectedManualCat, "");
    _selectedManualPath = "";
    await refreshSnapshot();
    navigate("summary");
  }

  async function doManualNewFolder() {
    const inp  = el("man-new-folder");
    const name = inp?.value?.trim() || "";
    if (!name) return;
    _selectedManualCat = name;
    renderManual();
  }

  // ── Init ───────────────────────────────────────────────────────────────────
  function init() {
    window.addEventListener("pywebviewready", () => {
      // La pantalla inicial la decide Python vía on_loaded → navigate()
    });
  }

  return {
    navigate, onSnapshotPush, renderCurrentScreen,
    doOrganizeNow, doToggleAgent, doPickFolder,
    doSaveAndAnalyze, doConfirmGroups,
    doRestoreDuplicates, doDeleteDuplicates,
    doManualMove, doManualNewFolder,
    toggleDupSelect,
    selectManualFile, selectManualCat,
    setFolder, updateFolderDisplay,
    init,
  };
})();

document.addEventListener("DOMContentLoaded", () => window.app.init());