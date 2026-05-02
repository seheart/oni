<script>
  let phases = $state([]);
  let seeds = $state([]);
  let page = $state("home");
  let activePhaseGroup = $state(null);
  let dark = $state(localStorage.getItem("oni-theme") === "dark");

  let newPhaseName = $state("");
  let newPhaseDesc = $state("");
  let buildForms = $state({});
  let lightboxImg = $state(null);

  const chapterLabels = ["a", "b", "c", "d", "e", "f", "g", "h"];

  let grouped = $derived(() => {
    const groups = {};
    for (const phase of phases) {
      const g = phase.phase_group || "?";
      if (!groups[g]) groups[g] = [];
      groups[g].push(phase);
    }
    return groups;
  });

  function handleKeydown(e) {
    if (e.key === "Escape" && lightboxImg) {
      lightboxImg = null;
    }
  }

  $effect(() => {
    window.addEventListener("keydown", handleKeydown);
    return () => window.removeEventListener("keydown", handleKeydown);
  });

  $effect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  });

  function toggleTheme() {
    dark = !dark;
    localStorage.setItem("oni-theme", dark ? "dark" : "light");
  }

  function goHome() {
    page = "home";
    activePhaseGroup = null;
    window.scrollTo(0, 0);
  }

  function goPhase(group) {
    page = "phase";
    activePhaseGroup = group;
    window.scrollTo(0, 0);
  }

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
        <button class="logo" onclick={goHome}>Colony Blueprint</button>
        <nav class="header-nav">
          <button class:active={page === "home"} onclick={goHome}>Home</button>
          {#each Object.keys(grouped()) as group}
            <button class:active={page === "phase" && activePhaseGroup === group} onclick={() => goPhase(group)}>Phase {group}</button>
          {/each}
        </nav>
      </div>
    </div>
  </header>

  <div class="content-area">
    <main class="container">
      {#if page === "home"}
        <div class="page-heading">
          <h1>Colony Blueprint</h1>
        </div>

        <section class="wiki-section intro-section">
          <div class="intro-text">
            <p>Hey, I'm <strong>Seth</strong>. This is my build guide for <em>Oxygen Not Included</em> — my strategies, priorities, and lessons learned from many colonies. This is how I play the game and what works for me. It's just for fun — I hope it helps you get started or gives you some new ideas. Enjoy the game with me!</p>
          </div>
          <div class="intro-image">
            <img src="/oni-hero.png" alt="Oxygen Not Included" />
          </div>
        </section>

        <div class="home-screenshot">
          <img src="/screenshots/cycle35-mess-hall.png" alt="Dupes enjoying a meal in the Great Hall" />
          <span class="meta">Dupes enjoying a meal in the Great Hall</span>
        </div>

        {#if seeds.length > 0}
          <section class="wiki-section">
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

        {#each Object.entries(grouped()) as [group, groupPhases]}
          <section class="wiki-section">
            <button class="phase-overview-card" onclick={() => goPhase(group)}>
              <h2 class="section-heading">Phase {group}</h2>
              <p class="phase-desc">{groupPhases.length} chapter{groupPhases.length > 1 ? "s" : ""}: {groupPhases.map((p, i) => `${group}${chapterLabels[i]}. ${p.name}`).join(" — ")}</p>
              <div class="progress-bar">
                <div class="progress-fill" style="width: {Math.round(groupPhases.reduce((a, p) => a + p.builds.filter(b => b.status === 'complete').length, 0) / Math.max(groupPhases.reduce((a, p) => a + p.builds.length, 0), 1) * 100)}%"></div>
              </div>
              <span class="meta">{groupPhases.reduce((a, p) => a + p.builds.filter(b => b.status === "complete").length, 0)}/{groupPhases.reduce((a, p) => a + p.builds.length, 0)} builds complete</span>
            </button>
          </section>
        {/each}


      {:else if page === "phase" && activePhaseGroup}
        <div class="page-heading">
          <h1>Phase {activePhaseGroup}</h1>
          <p class="lead"><button class="btn-link" onclick={goHome}>← Back to Home</button></p>
        </div>

        {#each (grouped()[activePhaseGroup] || []) as phase, j}
          <section class="wiki-section phase" id="phase-{phase.id}">
            <div class="phase-header">
              <div class="phase-title-row">
                <h2 class="section-heading">
                  <span class="phase-number">{activePhaseGroup}{chapterLabels[j]}.</span>
                  {phase.name}
                </h2>
              </div>
              {#if phase.description}
                <p class="phase-desc">{phase.description}</p>
              {/if}
              <div class="progress-bar">
                <div class="progress-fill" style="width: {phaseProgress(phase)}%"></div>
              </div>
              <span class="meta">{phaseProgress(phase)}% complete — {phase.builds.filter(b => b.status === "complete").length}/{phase.builds.length} builds</span>
            </div>

            {#if phase.builds.length > 0}
              <div class="builds-list">
                {#each phase.builds as build}
                  <div class="build-card status-{build.status}">
                    <div class="build-card-header">
                      <button class="status-btn" onclick={() => toggleBuildStatus(build)} title="Click to cycle status">
                        {#if build.status === "planned"}
                          <span class="status-tag tag-planned">planned</span>
                        {:else if build.status === "in-progress"}
                          <span class="status-tag tag-progress">in progress</span>
                        {:else}
                          <span class="status-tag tag-complete">complete</span>
                        {/if}
                      </button>
                      <span class="build-name">{build.name}</span>
                      <span class="priority-badge priority-{build.priority}">{build.priority}</span>
                    </div>
                    {#if build.description}
                      <p class="build-desc">{build.description}</p>
                    {/if}
                    {#if build.materials}
                      <p class="build-materials">Materials: {build.materials}</p>
                    {/if}
                    {#if build.screenshot}
                      <div class="build-screenshot">
                        <button class="screenshot-btn" onclick={() => lightboxImg = `/screenshots/${build.screenshot}`}>
                          <img src="/screenshots/{build.screenshot}" alt={build.name} loading="lazy" />
                        </button>
                      </div>
                    {/if}
                  </div>
                {/each}
              </div>
            {/if}

          </section>
        {/each}

      {:else if page === "design"}
        <div class="page-heading">
          <h1>Design System</h1>
          <p class="lead">Visual language for Colony Blueprint.</p>
        </div>

        <section class="wiki-section">
          <h2 class="section-heading">Palette</h2>
          <div class="palette-grid">
            <div class="palette-card">
              <div class="palette-swatch" style="background: #2c3e50"></div>
              <div class="palette-info"><span class="palette-name">Deep Space</span><span class="palette-hex">#2c3e50</span></div>
            </div>
            <div class="palette-card">
              <div class="palette-swatch" style="background: #0645ad"></div>
              <div class="palette-info"><span class="palette-name">Blueprint</span><span class="palette-hex">#0645ad</span></div>
            </div>
            <div class="palette-card">
              <div class="palette-swatch" style="background: #14866d"></div>
              <div class="palette-info"><span class="palette-name">Oxygen</span><span class="palette-hex">#14866d</span></div>
            </div>
            <div class="palette-card">
              <div class="palette-swatch" style="background: #c0863a"></div>
              <div class="palette-info"><span class="palette-name">Copper</span><span class="palette-hex">#c0863a</span></div>
            </div>
            <div class="palette-card">
              <div class="palette-swatch" style="background: #8e4a4a"></div>
              <div class="palette-info"><span class="palette-name">Magma</span><span class="palette-hex">#8e4a4a</span></div>
            </div>
            <div class="palette-card">
              <div class="palette-swatch" style="background: #5b7a8a"></div>
              <div class="palette-info"><span class="palette-name">Slate</span><span class="palette-hex">#5b7a8a</span></div>
            </div>
          </div>
        </section>

        <section class="wiki-section">
          <h2 class="section-heading">Typography</h2>
          <div class="type-specimen">
            <div class="type-row">
              <span class="type-label">H1 — Page Title</span>
              <h1 style="margin: 0">Colony Blueprint</h1>
            </div>
            <div class="type-row">
              <span class="type-label">H2 — Section</span>
              <h2 style="margin: 0; border: none; padding: 0">Phase 1: First Cycle</h2>
            </div>
            <div class="type-row">
              <span class="type-label">H3 — Subsection</span>
              <h3 style="margin: 0">Build Details</h3>
            </div>
            <div class="type-row">
              <span class="type-label">Body</span>
              <p style="margin: 0">Dig out space to the right of the pod for bathrooms. This area will later become the permanent plumbed bathrooms.</p>
            </div>
            <div class="type-row">
              <span class="type-label">Meta</span>
              <p class="meta" style="margin: 0">100% complete — 14/14 builds</p>
            </div>
          </div>
        </section>

        <section class="wiki-section">
          <h2 class="section-heading">Controls</h2>
          <div class="design-subsection">
            <h3>Buttons</h3>
            <div class="button-row">
              <button class="btn btn-primary">Primary</button>
              <button class="btn">Default</button>
              <button class="btn btn-danger">Danger</button>
              <button class="btn btn-sm">Small</button>
            </div>
          </div>
          <div class="design-subsection">
            <h3>Status</h3>
            <div class="button-row">
              <span class="status-tag tag-planned">planned</span>
              <span class="status-tag tag-progress">in progress</span>
              <span class="status-tag tag-complete">complete</span>
            </div>
          </div>
          <div class="design-subsection">
            <h3>Priority</h3>
            <div class="button-row">
              <span class="priority-badge priority-low">low</span>
              <span class="priority-badge priority-normal">normal</span>
              <span class="priority-badge priority-high">high</span>
              <span class="priority-badge priority-critical">critical</span>
            </div>
          </div>
          <div class="design-subsection">
            <h3>Progress</h3>
            <div class="progress-bar" style="max-width: 300px"><div class="progress-fill" style="width: 72%"></div></div>
            <span class="meta">72% complete</span>
          </div>
        </section>

        <section class="wiki-section">
          <h2 class="section-heading">Build Card</h2>
          <div class="builds-list" style="max-width: 500px">
            <div class="build-card status-complete">
              <div class="build-card-header">
                <span class="status-tag tag-complete">complete</span>
                <span class="build-name">Build 1 Outhouse</span>
                <span class="priority-badge priority-critical">critical</span>
              </div>
              <p class="build-desc">ASAP — #1 priority. Dupes will soil the base if this is not up immediately.</p>
              <p class="build-materials">Materials: Dirt</p>
            </div>
          </div>
        </section>

      {:else if page === "about"}
        <div class="page-heading">
          <h1>About</h1>
        </div>
        <section class="wiki-section">
          <p>Hey, I'm <strong>Seth</strong>.</p>
          <p>This is my build guide and recommendations for <em>Oxygen Not Included</em>. This is how I play the game — my strategies, my priorities, my mistakes and lessons learned along the way.</p>
          <p>This is just for fun. I hope it helps you get started or gives you some new ideas for your own colony. Please enjoy the game with me!</p>
          <p>Get the game: <a href="https://store.steampowered.com/app/457140/Oxygen_Not_Included/" target="_blank" rel="noreferrer">Oxygen Not Included on Steam</a></p>
          <hr />
          <p class="meta">Built with love, Flask, SQLite, and Svelte.</p>
        </section>
      {/if}
    </main>
  </div>

  {#if lightboxImg}
    <div class="lightbox" onclick={() => lightboxImg = null}>
      <button class="lightbox-close" onclick={() => lightboxImg = null}>×</button>
      <img src={lightboxImg} alt="Screenshot" />
    </div>
  {/if}

  <footer>
    <div class="container footer-inner">
      <span class="footer-brand">Colony Blueprint</span>
      <nav>
        <button class="footer-link" class:active={page === "design"} onclick={() => page = "design"}>Design</button>
        <button class="footer-link" class:active={page === "about"} onclick={() => page = "about"}>About</button>
        <button class="theme-toggle" onclick={toggleTheme} title="Toggle light/dark mode">
          {#if dark}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
          {:else}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
          {/if}
        </button>
      </nav>
    </div>
  </footer>
</div>

<style>
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
    --font: Georgia, "Times New Roman", serif;
    --font-ui: -apple-system, "Segoe UI", sans-serif;
    --radius: 2px;
    --section-border: #a2a9b1;
    --header-bg: #f8f9fa;
    --header-border: #a7d7f9;
    --tag-planned-bg: #eaecf0;
    --tag-planned-fg: #54595d;
    --tag-progress-bg: #fef6e7;
    --tag-progress-fg: #ac6600;
    --tag-complete-bg: #d5fdf4;
    --tag-complete-fg: #14866d;
  }

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
    --font: Georgia, "Times New Roman", serif;
    --font-ui: -apple-system, "Segoe UI", sans-serif;
    --radius: 2px;
    --section-border: #3a3f47;
    --header-bg: #1a1e24;
    --header-border: #3a5f8a;
    --tag-planned-bg: #2a2f36;
    --tag-planned-fg: #8a9199;
    --tag-progress-bg: rgba(255, 204, 51, 0.15);
    --tag-progress-fg: #ffcc33;
    --tag-complete-bg: rgba(61, 220, 151, 0.15);
    --tag-complete-fg: #3ddc97;
  }

  :global(*, *::before, *::after) { box-sizing: border-box; }

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

  /* Header */
  header {
    background: var(--header-bg);
    border-bottom: 1px solid var(--header-border);
  }

  .header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
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

  .header-nav { display: flex; }

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

  /* Content */
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

  /* Page heading */
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

  /* Sections */
  .wiki-section { margin-bottom: 1.5rem; }

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
  }

  p { margin: 0.5rem 0; }

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

  /* Seeds */
  /* Intro & Home */
  .intro-section {
    display: flex;
    gap: 1.5rem;
    align-items: flex-start;
  }

  .intro-text {
    flex: 1;
  }

  .intro-image {
    flex-shrink: 0;
    width: 130px;
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid var(--border-light);
  }

  .intro-image img {
    display: block;
    width: 100%;
    height: auto;
  }

  .home-screenshot {
    margin-bottom: 1.5rem;
    text-align: center;
  }

  .home-screenshot img {
    display: block;
    width: 100%;
    max-width: 600px;
    margin: 0 auto 0.35rem;
    border-radius: 4px;
    border: 1px solid var(--border-light);
  }

  .seed-item {
    margin: 0.4rem 0;
    font-family: var(--font-ui);
    font-size: 0.9rem;
  }

  .seed-code {
    font-family: ui-monospace, Consolas, monospace;
    font-size: 0.85rem;
    background: var(--surface);
    padding: 0.15rem 0.5rem;
    border-radius: var(--radius);
    border: 1px solid var(--border-light);
    user-select: all;
  }

  .seed-name { font-weight: 600; }
  .seed-notes { color: var(--text-muted); font-size: 0.85rem; }

  /* Phase overview cards */
  .phase-overview-card {
    display: block;
    width: 100%;
    cursor: pointer;
    padding: 0.75rem;
    border: 1px solid var(--border-light);
    border-radius: 4px;
    background: var(--bg);
    text-align: left;
    font-family: inherit;
    transition: border-color 0.15s;
  }

  .phase-overview-card:hover {
    border-color: var(--link);
  }

  .phase-overview-card .section-heading {
    margin-bottom: 0.5rem;
  }

  /* Back link */
  .btn-link {
    background: none;
    border: none;
    color: var(--link);
    cursor: pointer;
    font-family: var(--font-ui);
    font-size: 0.9rem;
    padding: 0;
    text-decoration: underline;
  }

  .btn-link:hover { color: var(--link-hover); }

  /* Phase */
  .phase-header { margin-bottom: 0.75rem; }

  .phase-title-row {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
  }

  .phase-title-row .section-heading { flex: 1; }
  .phase-number { color: var(--text-muted); }

  .phase-desc {
    margin: 0.15rem 0 0.5rem;
    color: var(--text-muted);
    font-size: 0.9rem;
  }

  /* Progress */
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

  /* Forms */
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .form-row-4 { grid-template-columns: 2fr 2fr 2fr 1fr; }

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

  /* Buttons */
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

  .btn:hover { background: var(--surface); }

  .btn-primary { background: var(--link); color: #fff; border-color: var(--link); }
  .btn-primary:hover { background: var(--link-hover); border-color: var(--link-hover); }

  .btn-danger { background: transparent; color: var(--danger); border-color: var(--danger); }
  .btn-danger:hover { background: var(--danger); color: #fff; }

  .btn-sm { padding: 0.2rem 0.6rem; font-size: 0.8rem; }

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

  .btn-link-danger:hover { color: var(--danger-hover); }

  .button-row { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }

  /* Build cards */
  .builds-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .build-card {
    border: 1px solid var(--border-light);
    border-radius: 4px;
    padding: 1rem;
    background: var(--bg);
  }

  .build-card-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: var(--font-ui);
  }

  .build-name { font-weight: 600; font-size: 0.9rem; flex: 1; }


  .build-desc {
    color: var(--text-muted);
    font-size: 0.85rem;
    font-family: var(--font-ui);
    margin: 0.4rem 0 0;
    line-height: 1.5;
  }

  .build-materials {
    font-size: 0.8rem;
    color: var(--accent);
    font-family: var(--font-ui);
    margin: 0.25rem 0 0;
  }

  .build-screenshot { margin-top: 0.75rem; }

  .screenshot-btn {
    background: none;
    border: 2px solid var(--border-light);
    border-radius: 4px;
    padding: 0;
    cursor: zoom-in;
    display: block;
    overflow: hidden;
    transition: border-color 0.15s;
  }

  .screenshot-btn:hover { border-color: var(--link); }

  .screenshot-btn img {
    display: block;
    width: 100%;
    max-width: 460px;
    height: auto;
  }

  /* Lightbox */
  .lightbox {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    cursor: zoom-out;
    padding: 2rem;
  }

  .lightbox img {
    max-width: 90vw;
    max-height: 85vh;
    border-radius: 4px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.5);
    object-fit: contain;
  }

  .lightbox-close {
    position: fixed;
    top: 1rem;
    right: 1.5rem;
    background: none;
    border: none;
    color: #fff;
    font-size: 2rem;
    cursor: pointer;
    z-index: 1001;
    line-height: 1;
    opacity: 0.7;
    transition: opacity 0.15s;
  }

  .lightbox-close:hover { opacity: 1; }

  /* Status tags */
  .status-btn { background: none; border: none; cursor: pointer; padding: 0; }

  .status-tag {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: var(--font-ui);
    padding: 0.1rem 0.45rem;
    border-radius: var(--radius);
  }

  .tag-planned { background: var(--tag-planned-bg); color: var(--tag-planned-fg); }
  .tag-progress { background: var(--tag-progress-bg); color: var(--tag-progress-fg); }
  .tag-complete { background: var(--tag-complete-bg); color: var(--tag-complete-fg); }

  /* Priority badges */
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

  /* Add build */
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

  /* Design page */
  .palette-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
  }

  .palette-card {
    border: 1px solid var(--border-light);
    border-radius: 4px;
    overflow: hidden;
  }

  .palette-swatch {
    height: 64px;
  }

  .palette-info {
    padding: 0.5rem 0.6rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: var(--font-ui);
    font-size: 0.8rem;
  }

  .palette-name { font-weight: 600; color: var(--text); }
  .palette-hex { color: var(--text-muted); font-family: ui-monospace, Consolas, monospace; font-size: 0.75rem; }

  .type-specimen {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .type-row {
    display: flex;
    align-items: baseline;
    gap: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-light);
  }

  .type-row:last-child { border-bottom: none; padding-bottom: 0; }

  .type-label {
    flex-shrink: 0;
    width: 120px;
    font-family: var(--font-ui);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
  }

  .design-subsection {
    margin-bottom: 1.25rem;
  }

  .design-subsection:last-child { margin-bottom: 0; }

  /* Footer */
  footer {
    background: var(--header-bg);
    border-top: 1px solid var(--border-light);
    padding: 0.75rem 0;
    position: sticky;
    bottom: 0;
    z-index: 100;
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

  footer nav { display: flex; gap: 0.15rem; }

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

  .footer-link:hover { color: var(--link-hover); }

  .footer-link.active {
    font-weight: 600;
    text-decoration: none;
    color: var(--text);
  }

  .theme-toggle {
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0.3rem 0.6rem;
    display: flex;
    align-items: center;
    border-radius: var(--radius);
    transition: color 0.1s;
  }

  .theme-toggle:hover {
    color: var(--text);
    background: var(--surface);
  }

  @media (max-width: 600px) {
    .form-row, .form-row-4 { grid-template-columns: 1fr; }
    .header-left { flex-direction: column; }
    .logo {
      border-right: none;
      border-bottom: 1px solid var(--border-light);
      margin-right: 0;
      padding: 0.5rem 0;
    }
    .content-area { border: none; }
    .swatches { flex-wrap: wrap; }
    .phase-title-row { flex-wrap: wrap; }
  }
</style>
