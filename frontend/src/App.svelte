<script>
  let phases = $state([]);
  let seeds = $state([]);
  let page = $state("home");
  let dark = $state(localStorage.getItem("oni-theme") === "dark");

  // New phase form
  let newPhaseName = $state("");
  let newPhaseDesc = $state("");

  // New build form (keyed by phase id)
  let buildForms = $state({});

  function toggleTheme() {
    dark = !dark;
    localStorage.setItem("oni-theme", dark ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  }

  $effect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  });

  async function fetchPhases() {
    const res = await fetch("/api/phases");
    phases = await res.json();
    for (const p of phases) {
      ensureBuildForm(p.id);
    }
  }

  async function fetchSeeds() {
    const res = await fetch("/api/seeds");
    seeds = await res.json();
  }

  async function addPhase() {
    if (!newPhaseName.trim()) return;
    await fetch("/api/phases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newPhaseName, description: newPhaseDesc }),
    });
    newPhaseName = "";
    newPhaseDesc = "";
    await fetchPhases();
  }

  async function deletePhase(id) {
    if (!confirm("Delete this phase and all its builds?")) return;
    await fetch(`/api/phases/${id}`, { method: "DELETE" });
    await fetchPhases();
  }

  async function addBuild(phaseId) {
    const form = buildForms[phaseId] || {};
    if (!form.name?.trim()) return;
    await fetch(`/api/phases/${phaseId}/builds`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: form.name,
        description: form.description || "",
        materials: form.materials || "",
        priority: form.priority || "normal",
      }),
    });
    buildForms[phaseId] = { name: "", description: "", materials: "", priority: "normal" };
    await fetchPhases();
  }

  async function toggleBuildStatus(build) {
    const next = build.status === "planned" ? "in-progress" : build.status === "in-progress" ? "complete" : "planned";
    await fetch(`/api/builds/${build.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...build, status: next }),
    });
    await fetchPhases();
  }

  async function deleteBuild(id) {
    await fetch(`/api/builds/${id}`, { method: "DELETE" });
    await fetchPhases();
  }

  function ensureBuildForm(phaseId) {
    if (!buildForms[phaseId]) {
      buildForms[phaseId] = { name: "", description: "", materials: "", priority: "normal" };
    }
  }

  function phaseProgress(phase) {
    if (!phase.builds.length) return 0;
    return Math.round((phase.builds.filter(b => b.status === "complete").length / phase.builds.length) * 100);
  }

  $effect(() => {
    fetchPhases();
    fetchSeeds();
  });
</script>

<div class="app">
  <header>
    <div class="container header-inner">
      <div class="header-left">
        <button class="logo" onclick={() => page = "home"}>ONI Planner</button>
        <nav class="header-nav">
          <button class:active={page === "home"} onclick={() => page = "home"}>Build Planner</button>
          <button class:active={page === "design"} onclick={() => page = "design"}>Design</button>
          <button class:active={page === "about"} onclick={() => page = "about"}>About</button>
        </nav>
      </div>
      <button class="theme-toggle" onclick={toggleTheme} title="Toggle light/dark mode">
        {#if dark}Light{:else}Dark{/if}
      </button>
    </div>
  </header>

  <div class="content-area">
    <main class="container">
      {#if page === "home"}
        <div class="page-heading">
          <h1>Build Planner</h1>
          <p class="lead">Plan and track your Oxygen Not Included colony builds by phase.</p>
        </div>

        <!-- Seeds -->
      {#if seeds.length > 0}
        <section class="wiki-section seeds-box">
          <h2 class="section-heading">Saved Seeds</h2>
          {#each seeds as seed}
            <div class="seed-item">
              <code class="seed-code">{seed.seed}</code>
              {#if seed.name}<span class="seed-name"> — {seed.name}</span>{/if}
              {#if seed.notes}<span class="seed-notes"> ({seed.notes})</span>{/if}
            </div>
          {/each}
        </section>
      {/if}

      <!-- Add Phase -->
        <section class="wiki-section">
          <h2 class="section-heading">Create New Phase</h2>
          <form onsubmit={(e) => { e.preventDefault(); addPhase(); }}>
            <div class="form-row">
              <div class="form-group">
                <label for="phase-name">Phase Name</label>
                <input type="text" id="phase-name" bind:value={newPhaseName} placeholder="e.g. Early Game, Mid Game, Space..." />
              </div>
              <div class="form-group">
                <label for="phase-desc">Description</label>
                <input type="text" id="phase-desc" bind:value={newPhaseDesc} placeholder="Goals for this phase" />
              </div>
            </div>
            <button class="btn btn-primary" type="submit">Add Phase</button>
          </form>
        </section>

        <!-- Phases -->
        {#if phases.length === 0}
          <p class="empty">No phases yet. Create your first phase above to start planning your colony.</p>
        {/if}

        {#each phases as phase, i}
          <section class="wiki-section phase">
            <div class="phase-header">
              <div class="phase-title-row">
                <h2 class="section-heading">
                  <span class="phase-number">{i + 1}.</span>
                  {phase.name}
                </h2>
                <button class="btn btn-danger btn-sm" onclick={() => deletePhase(phase.id)}>delete</button>
              </div>
              {#if phase.description}
                <p class="phase-desc">{phase.description}</p>
              {/if}
              <div class="progress-bar">
                <div class="progress-fill" style="width: {phaseProgress(phase)}%"></div>
              </div>
              <span class="meta">{phaseProgress(phase)}% complete — {phase.builds.filter(b => b.status === "complete").length}/{phase.builds.length} builds</span>
            </div>

            <!-- Builds list -->
            {#if phase.builds.length > 0}
              <table>
                <thead>
                  <tr>
                    <th class="col-status">Status</th>
                    <th>Build</th>
                    <th>Materials</th>
                    <th class="col-priority">Priority</th>
                    <th class="col-actions"></th>
                  </tr>
                </thead>
                <tbody>
                  {#each phase.builds as build}
                    <tr class="status-{build.status}">
                      <td>
                        <button class="status-btn" onclick={() => toggleBuildStatus(build)} title="Click to cycle status">
                          {#if build.status === "planned"}
                            <span class="status-tag tag-planned">planned</span>
                          {:else if build.status === "in-progress"}
                            <span class="status-tag tag-progress">in progress</span>
                          {:else}
                            <span class="status-tag tag-complete">complete</span>
                          {/if}
                        </button>
                      </td>
                      <td>
                        <span class="build-name">{build.name}</span>
                        {#if build.description}
                          <span class="build-desc"> — {build.description}</span>
                        {/if}
                      </td>
                      <td class="build-materials">{build.materials || "—"}</td>
                      <td><span class="priority-badge priority-{build.priority}">{build.priority}</span></td>
                      <td><button class="btn-link-danger" onclick={() => deleteBuild(build.id)} title="Delete build">delete</button></td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            {/if}

            <!-- Add build form -->
            <div class="add-build">
              <form onsubmit={(e) => { e.preventDefault(); addBuild(phase.id); }}>
                <div class="form-row form-row-4">
                  <input type="text" placeholder="Build name"
                    value={(buildForms[phase.id] || {}).name}
                    oninput={(e) => buildForms[phase.id].name = e.target.value} />
                  <input type="text" placeholder="Description"
                    value={(buildForms[phase.id] || {}).description}
                    oninput={(e) => buildForms[phase.id].description = e.target.value} />
                  <input type="text" placeholder="Materials"
                    value={(buildForms[phase.id] || {}).materials}
                    oninput={(e) => buildForms[phase.id].materials = e.target.value} />
                  <select value={(buildForms[phase.id] || {}).priority}
                    onchange={(e) => buildForms[phase.id].priority = e.target.value}>
                    <option value="low">Low</option>
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <button class="btn btn-sm" type="submit">+ Add Build</button>
              </form>
            </div>
          </section>
        {/each}

      {:else if page === "design"}
        <div class="page-heading">
          <h1>Design System</h1>
          <p class="lead">Visual reference for the ONI Planner interface.</p>
        </div>

        <section class="wiki-section">
          <h2 class="section-heading">Colors</h2>
          <div class="swatches">
            <div class="swatch" style="background: var(--link)"><span>Link</span></div>
            <div class="swatch" style="background: var(--accent)"><span>Accent</span></div>
            <div class="swatch" style="background: var(--danger)"><span>Danger</span></div>
            <div class="swatch" style="background: var(--warning)"><span>Warning</span></div>
            <div class="swatch" style="background: var(--success)"><span>Success</span></div>
          </div>
        </section>

        <section class="wiki-section">
          <h2 class="section-heading">Typography</h2>
          <h1>Heading 1</h1>
          <h2>Heading 2</h2>
          <h3>Heading 3</h3>
          <p>Body text — The quick brown fox jumps over the lazy dog.</p>
          <p class="meta">Meta text for secondary information.</p>
        </section>

        <section class="wiki-section">
          <h2 class="section-heading">Buttons</h2>
          <div class="button-row">
            <button class="btn btn-primary">Primary</button>
            <button class="btn">Default</button>
            <button class="btn btn-danger">Danger</button>
          </div>
        </section>

        <section class="wiki-section">
          <h2 class="section-heading">Status &amp; Priority</h2>
          <div class="button-row" style="margin-bottom: 1rem">
            <span class="status-tag tag-planned">planned</span>
            <span class="status-tag tag-progress">in progress</span>
            <span class="status-tag tag-complete">complete</span>
          </div>
          <div class="button-row">
            <span class="priority-badge priority-low">low</span>
            <span class="priority-badge priority-normal">normal</span>
            <span class="priority-badge priority-high">high</span>
            <span class="priority-badge priority-critical">critical</span>
          </div>
        </section>

      {:else if page === "about"}
        <div class="page-heading">
          <h1>About</h1>
        </div>
        <section class="wiki-section">
          <p><strong>ONI Planner</strong> helps you organize your <em>Oxygen Not Included</em> colony builds into phases.</p>
          <p>Plan your builds from early game survival through to late-game rocketry. Track materials, set priorities, and mark progress as you go.</p>
          <hr />
          <p class="meta">Built with Flask, SQLite, and Svelte.</p>
        </section>
      {/if}
    </main>
  </div>

  <footer>
    <div class="container footer-inner">
      <span class="footer-brand">ONI Planner</span>
      <nav>
        <button class="footer-link" class:active={page === "home"} onclick={() => page = "home"}>Planner</button>
        <button class="footer-link" class:active={page === "design"} onclick={() => page = "design"}>Design</button>
        <button class="footer-link" class:active={page === "about"} onclick={() => page = "about"}>About</button>
      </nav>
    </div>
  </footer>
</div>

<style>
  /* ===== LIGHT THEME (default) ===== */
  :global(:root), :global([data-theme="light"]) {
    --bg: #ffffff;
    --bg-secondary: #f6f6f6;
    --surface: #f6f6f6;
    --surface-border: #a7a7a7;
    --border-light: #c8ccd1;
    --text: #202122;
    --text-muted: #54595d;
    --link: #0645ad;
    --link-hover: #0b0080;
    --accent: #36c;
    --danger: #d33;
    --danger-hover: #b32424;
    --warning: #fc3;
    --success: #14866d;
    --success-bg: #d5fdf4;
    --highlight: #fee7cd;
    --font: Georgia, 'Times New Roman', serif;
    --font-ui: -apple-system, 'Segoe UI', sans-serif;
    --radius: 2px;
    --section-bg: #ffffff;
    --section-border: #a2a9b1;
    --header-bg: #f8f9fa;
    --header-border: #a7d7f9;
    --table-header-bg: #eaecf0;
    --table-border: #a2a9b1;
    --tag-planned-bg: #eaecf0;
    --tag-planned-fg: #54595d;
    --tag-progress-bg: #fef6e7;
    --tag-progress-fg: #ac6600;
    --tag-complete-bg: #d5fdf4;
    --tag-complete-fg: #14866d;
  }

  /* ===== DARK THEME ===== */
  :global([data-theme="dark"]) {
    --bg: #101418;
    --bg-secondary: #1a1e24;
    --surface: #1a1e24;
    --surface-border: #3a3f47;
    --border-light: #3a3f47;
    --text: #c8ccd1;
    --text-muted: #8a9199;
    --link: #6b9eff;
    --link-hover: #8ab4ff;
    --accent: #6b9eff;
    --danger: #ff6b6b;
    --danger-hover: #ff4c4c;
    --warning: #ffcc33;
    --success: #3ddc97;
    --success-bg: rgba(61, 220, 151, 0.15);
    --highlight: rgba(255, 204, 51, 0.15);
    --font: Georgia, 'Times New Roman', serif;
    --font-ui: -apple-system, 'Segoe UI', sans-serif;
    --radius: 2px;
    --section-bg: #1a1e24;
    --section-border: #3a3f47;
    --header-bg: #1a1e24;
    --header-border: #3a5f8a;
    --table-header-bg: #22272e;
    --table-border: #3a3f47;
    --tag-planned-bg: #2a2f36;
    --tag-planned-fg: #8a9199;
    --tag-progress-bg: rgba(255, 204, 51, 0.15);
    --tag-progress-fg: #ffcc33;
    --tag-complete-bg: rgba(61, 220, 151, 0.15);
    --tag-complete-fg: #3ddc97;
  }

  :global(*, *::before, *::after) {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    font-family: var(--font);
    color: var(--text);
    background: var(--bg-secondary);
    -webkit-font-smoothing: antialiased;
    font-size: 14px;
    line-height: 1.6;
  }

  .app {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  .container {
    max-width: 960px;
    margin: 0 auto;
    padding: 0 1.5rem;
    width: 100%;
  }

  /* ===== HEADER — wiki-style tab bar ===== */
  header {
    background: var(--header-bg);
    border-bottom: 1px solid var(--header-border);
  }

  .header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0;
  }

  .header-left {
    display: flex;
    align-items: stretch;
  }

  .logo {
    background: none;
    border: none;
    font-family: var(--font);
    font-size: 1.1rem;
    font-weight: bold;
    color: var(--text);
    cursor: pointer;
    padding: 0.6rem 1rem 0.6rem 0;
    margin-right: 1rem;
    border-right: 1px solid var(--border-light);
  }

  .header-nav {
    display: flex;
  }

  .header-nav button {
    background: none;
    border: none;
    border-bottom: 3px solid transparent;
    font-family: var(--font-ui);
    font-size: 0.85rem;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0.6rem 0.9rem;
    transition: all 0.1s;
  }

  .header-nav button:hover {
    color: var(--text);
    background: var(--surface);
  }

  .header-nav button.active {
    color: var(--text);
    border-bottom-color: var(--link);
    font-weight: 600;
  }

  .theme-toggle {
    background: none;
    border: 1px solid var(--border-light);
    font-family: var(--font-ui);
    font-size: 0.8rem;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0.25rem 0.65rem;
    border-radius: var(--radius);
  }

  .theme-toggle:hover {
    color: var(--text);
    background: var(--surface);
  }

  /* ===== CONTENT AREA ===== */
  .content-area {
    flex: 1;
    background: var(--bg);
    border-left: 1px solid var(--section-border);
    border-right: 1px solid var(--section-border);
    max-width: 960px;
    width: 100%;
    margin: 0 auto;
  }

  main {
    padding-top: 1.25rem;
    padding-bottom: 3rem;
  }

  /* ===== PAGE HEADING ===== */
  .page-heading {
    border-bottom: 1px solid var(--section-border);
    margin-bottom: 1.25rem;
    padding-bottom: 0.25rem;
  }

  .page-heading h1 {
    font-family: var(--font);
    font-size: 1.8rem;
    font-weight: normal;
    margin: 0;
    color: var(--text);
  }

  .lead {
    color: var(--text-muted);
    font-size: 0.9rem;
    margin: 0.35rem 0 0.5rem;
    font-family: var(--font-ui);
  }

  /* ===== WIKI SECTIONS ===== */
  .wiki-section {
    margin-bottom: 1.5rem;
  }

  .section-heading {
    font-family: var(--font);
    font-size: 1.25rem;
    font-weight: normal;
    border-bottom: 1px solid var(--section-border);
    padding-bottom: 0.2rem;
    margin: 0 0 0.75rem;
    color: var(--text);
  }

  h3 {
    font-family: var(--font);
    font-weight: bold;
    font-size: 1rem;
    margin: 1rem 0 0.5rem;
    color: var(--text);
    text-transform: none;
    letter-spacing: normal;
  }

  p {
    margin: 0.5rem 0;
  }

  hr {
    border: none;
    border-top: 1px solid var(--border-light);
    margin: 1rem 0;
  }

  .meta {
    color: var(--text-muted);
    font-size: 0.85rem;
    font-family: var(--font-ui);
  }

  /* ===== SEEDS ===== */
  .seed-item {
    margin: 0.4rem 0;
    font-family: var(--font-ui);
    font-size: 0.9rem;
  }

  .seed-code {
    font-family: ui-monospace, Consolas, monospace;
    font-size: 0.85rem;
    background: var(--table-header-bg);
    padding: 0.15rem 0.5rem;
    border-radius: var(--radius);
    border: 1px solid var(--border-light);
    user-select: all;
  }

  .seed-name {
    font-weight: 600;
  }

  .seed-notes {
    color: var(--text-muted);
    font-size: 0.85rem;
  }

  /* ===== FORMS ===== */
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .form-row-4 {
    grid-template-columns: 2fr 2fr 2fr 1fr;
  }

  .form-group label {
    display: block;
    font-size: 0.8rem;
    font-weight: bold;
    margin-bottom: 0.2rem;
    color: var(--text);
    font-family: var(--font-ui);
  }

  input[type="text"], select {
    width: 100%;
    padding: 0.4rem 0.5rem;
    border: 1px solid var(--surface-border);
    border-radius: var(--radius);
    font-size: 0.85rem;
    font-family: var(--font-ui);
    background: var(--bg);
    color: var(--text);
  }

  input[type="text"]:focus, select:focus {
    outline: none;
    border-color: var(--link);
  }

  /* ===== BUTTONS ===== */
  .btn {
    padding: 0.35rem 0.85rem;
    border: 1px solid var(--surface-border);
    border-radius: var(--radius);
    font-size: 0.85rem;
    font-family: var(--font-ui);
    font-weight: 600;
    cursor: pointer;
    background: var(--header-bg);
    color: var(--text);
    transition: background 0.1s;
  }

  .btn:hover {
    background: var(--surface);
  }

  .btn-primary {
    background: var(--link);
    color: #fff;
    border-color: var(--link);
  }

  .btn-primary:hover {
    background: var(--link-hover);
    border-color: var(--link-hover);
  }

  .btn-danger {
    background: transparent;
    color: var(--danger);
    border-color: var(--danger);
  }

  .btn-danger:hover {
    background: var(--danger);
    color: #fff;
  }

  .btn-sm {
    padding: 0.2rem 0.6rem;
    font-size: 0.8rem;
  }

  .btn-link-danger {
    background: none;
    border: none;
    color: var(--danger);
    cursor: pointer;
    font-size: 0.8rem;
    font-family: var(--font-ui);
    padding: 0;
    text-decoration: underline;
  }

  .btn-link-danger:hover {
    color: var(--danger-hover);
  }

  .button-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
  }

  /* ===== PHASE ===== */
  .phase-header {
    margin-bottom: 0.75rem;
  }

  .phase-title-row {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
  }

  .phase-title-row .section-heading {
    flex: 1;
  }

  .phase-number {
    color: var(--text-muted);
  }

  .phase-desc {
    margin: 0.15rem 0 0.5rem;
    color: var(--text-muted);
    font-size: 0.9rem;
  }

  /* ===== PROGRESS ===== */
  .progress-bar {
    height: 4px;
    background: var(--surface);
    border: 1px solid var(--border-light);
    overflow: hidden;
    margin-bottom: 0.25rem;
  }

  .progress-fill {
    height: 100%;
    background: var(--success);
    transition: width 0.3s;
  }

  /* ===== TABLE ===== */
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    font-family: var(--font-ui);
    margin-bottom: 0.5rem;
  }

  th, td {
    padding: 0.4rem 0.6rem;
    text-align: left;
    border: 1px solid var(--table-border);
  }

  th {
    background: var(--table-header-bg);
    font-size: 0.8rem;
    font-weight: 600;
  }

  .col-status { width: 100px; }
  .col-priority { width: 80px; }
  .col-actions { width: 50px; text-align: center; }

  tr.status-complete .build-name {
    text-decoration: line-through;
    color: var(--text-muted);
  }

  .build-name {
    font-weight: 600;
  }

  .build-desc {
    color: var(--text-muted);
    font-weight: normal;
  }

  .build-materials {
    font-size: 0.8rem;
    color: var(--text-muted);
  }

  /* ===== STATUS TAGS ===== */
  .status-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
  }

  .status-tag {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: var(--font-ui);
    padding: 0.1rem 0.45rem;
    border-radius: var(--radius);
  }

  .tag-planned {
    background: var(--tag-planned-bg);
    color: var(--tag-planned-fg);
  }

  .tag-progress {
    background: var(--tag-progress-bg);
    color: var(--tag-progress-fg);
  }

  .tag-complete {
    background: var(--tag-complete-bg);
    color: var(--tag-complete-fg);
  }

  /* ===== PRIORITY BADGES ===== */
  .priority-badge {
    font-size: 0.7rem;
    font-weight: 600;
    font-family: var(--font-ui);
    text-transform: uppercase;
    letter-spacing: 0.03em;
    padding: 0.1rem 0.4rem;
    border-radius: var(--radius);
  }

  .priority-low { background: var(--tag-planned-bg); color: var(--tag-planned-fg); }
  .priority-normal { background: #d5e5ff; color: #0645ad; }
  .priority-high { background: var(--tag-progress-bg); color: var(--tag-progress-fg); }
  .priority-critical { background: #fdd; color: var(--danger); }

  :global([data-theme="dark"]) .priority-normal { background: rgba(107, 158, 255, 0.15); color: #6b9eff; }
  :global([data-theme="dark"]) .priority-critical { background: rgba(255, 107, 107, 0.15); color: #ff6b6b; }

  /* ===== ADD BUILD ===== */
  .add-build {
    border-top: 1px solid var(--border-light);
    margin-top: 0.5rem;
    padding-top: 0.5rem;
  }

  .empty {
    color: var(--text-muted);
    text-align: center;
    padding: 2rem 0;
    font-style: italic;
  }

  /* ===== DESIGN PAGE ===== */
  .swatches {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .swatch {
    width: 80px;
    height: 60px;
    border-radius: var(--radius);
    display: flex;
    align-items: flex-end;
    padding: 0.3rem;
    border: 1px solid var(--border-light);
  }

  .swatch span {
    font-size: 0.65rem;
    font-weight: 600;
    font-family: var(--font-ui);
    color: white;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
  }

  /* ===== FOOTER ===== */
  footer {
    background: var(--header-bg);
    border-top: 1px solid var(--border-light);
    padding: 0.75rem 0;
    margin-top: auto;
  }

  .footer-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .footer-brand {
    font-weight: bold;
    color: var(--text-muted);
    font-size: 0.8rem;
    font-family: var(--font-ui);
  }

  footer nav {
    display: flex;
    gap: 0.15rem;
  }

  .footer-link {
    background: none;
    border: none;
    padding: 0.3rem 0.6rem;
    font-family: var(--font-ui);
    font-size: 0.8rem;
    color: var(--link);
    cursor: pointer;
    text-decoration: underline;
    transition: color 0.1s;
  }

  .footer-link:hover {
    color: var(--link-hover);
  }

  .footer-link.active {
    font-weight: 600;
    text-decoration: none;
    color: var(--text);
  }

  @media (max-width: 600px) {
    .form-row, .form-row-4 {
      grid-template-columns: 1fr;
    }
    .header-left {
      flex-direction: column;
    }
    .logo {
      border-right: none;
      border-bottom: 1px solid var(--border-light);
      margin-right: 0;
      padding: 0.5rem 0;
    }
    .content-area {
      border: none;
    }
    .swatches {
      flex-wrap: wrap;
    }
    .phase-title-row {
      flex-wrap: wrap;
    }
    .col-status { width: auto; }
    .col-priority { width: auto; }
  }
</style>
