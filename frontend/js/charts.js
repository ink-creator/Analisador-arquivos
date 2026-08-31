window.ProjectCharts = (() => {
  function renderBars(container, rows, emptyText = "No data available") {
    container.replaceChildren();
    if (!rows.length) {
      const empty = document.createElement("div");
      empty.className = "empty-inline";
      empty.textContent = emptyText;
      container.appendChild(empty);
      return;
    }

    rows.forEach((row) => {
      const wrapper = document.createElement("div");
      wrapper.className = "bar-row";

      const label = document.createElement("span");
      label.className = "bar-label";
      label.textContent = row.label;
      label.title = row.label;

      const track = document.createElement("div");
      track.className = "bar-track";
      const fill = document.createElement("div");
      fill.className = "bar-fill";
      fill.style.width = `${Math.max(0, Math.min(100, row.percent))}%`;
      track.appendChild(fill);

      const value = document.createElement("span");
      value.className = "bar-value";
      value.textContent = row.value;

      wrapper.append(label, track, value);
      container.appendChild(wrapper);
    });
  }

  return { renderBars };
})();
