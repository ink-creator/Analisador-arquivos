(() => {
  const state = { project: null, currentView: "overview", fileSearch: "" };

  const byId = (id) => document.getElementById(id);
  const openButtons = [byId("open-project"), byId("empty-open-project")];

  function formatNumber(value) {
    return new Intl.NumberFormat().format(value ?? 0);
  }

  function formatBytes(bytes) {
    const value = Number(bytes || 0);
    if (value < 1024) return `${value} B`;
    const units = ["KB", "MB", "GB", "TB"];
    let size = value;
    let unit = -1;
    do { size /= 1024; unit += 1; } while (size >= 1024 && unit < units.length - 1);
    return `${size >= 10 ? size.toFixed(1) : size.toFixed(2)} ${units[unit]}`;
  }

  function setScreen(screen) {
    ["empty-state", "loading-state", "error-state", "dashboard"].forEach((id) => byId(id).classList.add("hidden"));
    byId(screen).classList.remove("hidden");
  }

  function setButtonsDisabled(disabled) {
    openButtons.forEach((button) => { button.disabled = disabled; });
  }

  async function openProject() {
    setButtonsDisabled(true);
    setScreen("loading-state");
    try {
      if (!window.pywebview?.api?.select_project) {
        throw new Error("The Python bridge is unavailable. Start the app with 'python main.py'.");
      }
      const response = await window.pywebview.api.select_project();
      if (response.cancelled) {
        setScreen(state.project ? "dashboard" : "empty-state");
        return;
      }
      if (!response.ok) throw new Error(response.error || "Unknown analysis error.");
      state.project = response.data;
      state.fileSearch = "";
      byId("file-search").value = "";
      renderProject(response.data);
      setScreen("dashboard");
      showView("overview");
    } catch (error) {
      byId("error-message").textContent = error?.message || String(error);
      setScreen("error-state");
    } finally {
      setButtonsDisabled(false);
    }
  }

  function languageRows(data, metric, limit = 10) {
    return Object.entries(data.languages || {})
      .map(([label, stats]) => ({
        label,
        raw: metric === "lines" ? stats.lines : stats.files,
        percent: metric === "lines" ? stats.percent_by_lines : stats.percent_by_files,
      }))
      .sort((a, b) => b.raw - a.raw)
      .slice(0, limit)
      .map((row) => ({ ...row, value: `${row.percent.toFixed(1)}%` }));
  }

  function renderProject(data) {
    const summary = data.summary;
    const markers = data.markers || { counts: {}, total: 0, files: 0, items: [] };
    const insights = data.insights || {};

    byId("project-name").textContent = data.project.name;
    byId("project-path").textContent = data.project.path;
    byId("stat-files").textContent = formatNumber(summary.files);
    byId("stat-folders").textContent = formatNumber(summary.directories);
    byId("stat-lines").textContent = formatNumber(summary.lines);
    byId("stat-size").textContent = formatBytes(summary.size);

    ProjectCharts.renderBars(byId("overview-languages"), languageRows(data, "lines", 6));
    ProjectCharts.renderBars(byId("languages-by-lines"), languageRows(data, "lines"));
    ProjectCharts.renderBars(byId("languages-by-files"), languageRows(data, "files"));

    const largest = data.largest_files?.[0];
    byId("largest-file").textContent = largest ? `${largest.path} · ${formatBytes(largest.size)}` : "—";
    const firstExtension = Object.entries(data.extensions || {})[0];
    byId("common-extension").textContent = firstExtension ? `${firstExtension[0]} · ${formatNumber(firstExtension[1])} files` : "—";
    byId("max-depth").textContent = formatNumber(data.structure.maximum_depth);
    byId("average-file-size").textContent = formatBytes(summary.average_file_size);
    byId("overview-markers").textContent = `${formatNumber(markers.total)} across ${formatNumber(markers.files)} files`;

    byId("structure-directories").textContent = formatNumber(summary.directories);
    byId("structure-depth").textContent = formatNumber(data.structure.maximum_depth);
    byId("structure-empty").textContent = formatNumber(data.structure.empty_directories);
    byId("structure-average").textContent = formatBytes(summary.average_file_size);

    renderRankList(
      byId("extensions-list"),
      Object.entries(data.extensions || {})
        .map(([name, count]) => ({ name, value: `${formatNumber(count)} files` }))
        .slice(0, 15),
    );
    renderRankList(
      byId("directories-list"),
      (data.structure.largest_directories || []).map((item) => ({ name: item.path, value: formatBytes(item.size) })),
    );

    renderTree(data.tree || [], "");
    clearFileInspector();
    renderInsights(markers, insights);
  }

  function renderInsights(markers, insights) {
    byId("marker-todo").textContent = formatNumber(markers.counts?.TODO || 0);
    byId("marker-fixme").textContent = formatNumber(markers.counts?.FIXME || 0);
    byId("marker-hack").textContent = formatNumber(markers.counts?.HACK || 0);
    byId("marker-summary").textContent = `${formatNumber(markers.total || 0)} occurrences in ${formatNumber(markers.files || 0)} files`;

    const emptyFiles = insights.empty_files || { count: 0, paths: [] };
    const largeFiles = insights.large_files || { count: 0, threshold: 0, items: [] };
    const unclassified = insights.unclassified_files || { count: 0, paths: [] };

    byId("insight-empty-files").textContent = formatNumber(emptyFiles.count);
    byId("insight-large-files").textContent = formatNumber(largeFiles.count);
    byId("insight-large-threshold").textContent = formatBytes(largeFiles.threshold);
    byId("insight-unclassified").textContent = formatNumber(unclassified.count);
    byId("insight-extension-variety").textContent = formatNumber(insights.extension_variety || 0);
    byId("insight-warnings").textContent = formatNumber(insights.warnings || 0);

    renderMarkers(markers.items || [], markers.truncated);
    renderRankList(
      byId("large-files-list"),
      (largeFiles.items || []).map((item) => ({ name: item.path, value: formatBytes(item.size) })),
    );
    renderRankList(
      byId("empty-files-list"),
      (emptyFiles.paths || []).map((path) => ({ name: path, value: "0 B" })),
    );
  }

  function renderMarkers(items, truncated) {
    const container = byId("markers-list");
    container.replaceChildren();

    if (!items.length) {
      const empty = document.createElement("div");
      empty.className = "empty-inline marker-empty";
      empty.textContent = "No TODO, FIXME or HACK markers found.";
      container.appendChild(empty);
      return;
    }

    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "marker-item";

      const header = document.createElement("div");
      header.className = "marker-item-header";

      const badge = document.createElement("span");
      badge.className = `marker-badge marker-${String(item.type).toLowerCase()}`;
      badge.textContent = item.type;

      const location = document.createElement("span");
      location.className = "marker-location";
      location.textContent = `${item.path}:${item.line}`;
      location.title = `${item.path}:${item.line}`;

      const snippet = document.createElement("code");
      snippet.className = "marker-snippet";
      snippet.textContent = item.snippet || "";

      header.append(badge, location);
      row.append(header, snippet);
      container.appendChild(row);
    });

    if (truncated) {
      const note = document.createElement("div");
      note.className = "marker-truncated";
      note.textContent = "The list is capped for display; totals above still include every detected marker.";
      container.appendChild(note);
    }
  }

  function renderRankList(container, items) {
    container.replaceChildren();
    if (!items.length) {
      const empty = document.createElement("div");
      empty.className = "empty-inline";
      empty.textContent = "No data available";
      container.appendChild(empty);
      return;
    }
    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "rank-item";
      const name = document.createElement("span");
      name.className = "rank-name";
      name.textContent = item.name;
      name.title = item.name;
      const value = document.createElement("span");
      value.className = "rank-value";
      value.textContent = item.value;
      row.append(name, value);
      container.appendChild(row);
    });
  }

  function filterTree(nodes, query) {
    if (!query) return nodes;
    const normalized = query.toLowerCase();

    return nodes.reduce((results, node) => {
      const selfMatches = node.name.toLowerCase().includes(normalized) || node.path.toLowerCase().includes(normalized);
      if (node.type === "file") {
        if (selfMatches) results.push(node);
        return results;
      }

      if (selfMatches) {
        results.push(node);
        return results;
      }

      const children = filterTree(node.children || [], query);
      if (children.length) results.push({ ...node, children });
      return results;
    }, []);
  }

  function countVisibleFiles(nodes) {
    return nodes.reduce((total, node) => {
      if (node.type === "file") return total + 1;
      return total + countVisibleFiles(node.children || []);
    }, 0);
  }

  function renderTree(nodes, query = "") {
    const container = byId("file-tree");
    container.replaceChildren();

    const filtered = filterTree(nodes, query.trim());
    if (!filtered.length) {
      const empty = document.createElement("div");
      empty.className = "tree-empty";
      empty.textContent = `No files or folders match “${query}”.`;
      container.appendChild(empty);
      byId("file-search-meta").textContent = "0 matching files";
      return;
    }

    const fragment = document.createDocumentFragment();
    filtered.forEach((node) => fragment.appendChild(createTreeNode(node, Boolean(query.trim()))));
    container.appendChild(fragment);

    if (query.trim()) {
      byId("file-search-meta").textContent = `${formatNumber(countVisibleFiles(filtered))} matching files · matching folders are expanded automatically`;
    } else {
      byId("file-search-meta").textContent = "Browse the project tree or search by name/path.";
    }
  }

  function createTreeNode(node, expandDirectories = false) {
    const wrapper = document.createElement("div");
    wrapper.className = "tree-node";
    const row = document.createElement("button");
    row.className = "tree-row";
    row.type = "button";

    const icon = document.createElement("span");
    icon.className = "tree-icon";
    icon.textContent = node.type === "directory" ? (expandDirectories ? "▾" : "▸") : "·";
    const name = document.createElement("span");
    name.textContent = node.name;
    row.append(icon, name);
    wrapper.appendChild(row);

    if (node.type === "directory") {
      const children = document.createElement("div");
      children.className = `tree-children${expandDirectories ? "" : " hidden"}`;
      (node.children || []).forEach((child) => children.appendChild(createTreeNode(child, expandDirectories)));
      row.addEventListener("click", () => {
        const collapsed = children.classList.toggle("hidden");
        icon.textContent = collapsed ? "▸" : "▾";
      });
      wrapper.appendChild(children);
    } else {
      row.addEventListener("click", () => {
        document.querySelectorAll(".tree-row.selected").forEach((element) => element.classList.remove("selected"));
        row.classList.add("selected");
        inspectFile(node);
      });
    }
    return wrapper;
  }

  function inspectFile(file) {
    byId("file-name").textContent = file.name;
    byId("file-language").textContent = file.language || "Unknown";
    byId("file-size").textContent = formatBytes(file.size);
    byId("file-lines").textContent = file.lines == null ? "Binary / unavailable" : formatNumber(file.lines);
    byId("file-path").textContent = file.path;
  }

  function clearFileInspector() {
    byId("file-name").textContent = "Select a file";
    ["file-language", "file-size", "file-lines", "file-path"].forEach((id) => { byId(id).textContent = "—"; });
  }

  function showView(viewName) {
    state.currentView = viewName;
    document.querySelectorAll("[data-view-panel]").forEach((panel) => panel.classList.toggle("hidden", panel.dataset.viewPanel !== viewName));
    document.querySelectorAll(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === viewName));
    if (viewName === "files") byId("file-search").focus();
  }

  openButtons.forEach((button) => button.addEventListener("click", openProject));
  document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => {
    if (state.project) showView(button.dataset.view);
  }));

  byId("file-search").addEventListener("input", (event) => {
    state.fileSearch = event.target.value;
    if (state.project) renderTree(state.project.tree || [], state.fileSearch);
  });

  byId("file-search").addEventListener("keydown", (event) => {
    if (event.key === "Escape" && event.target.value) {
      event.target.value = "";
      state.fileSearch = "";
      renderTree(state.project?.tree || [], "");
    }
  });
})();
