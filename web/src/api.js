export class StudioClient {
  constructor() { this.mode = 'loading'; this.project = null; }
  async fetchJson(url, options = {}) {
    const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
  async boot() {
    try {
      await this.fetchJson('/api/health');
      this.mode = 'backend';
      return this.refresh();
    } catch (_) {
      this.mode = 'online';
      const project = await this.fetchJson(`${import.meta.env.BASE_URL}examples/poachermon.snesproj`);
      this.project = project;
      return { mode: this.mode, project, inventory: this.inventory(project), blocks: await this.blocks() };
    }
  }
  inventory(project = this.project) {
    const scenes = project?.scenes || [];
    const actor_count = scenes.reduce((n, s) => n + (s.actors?.length || 0), 0);
    const collision_count = scenes.reduce((n, s) => n + (s.collision?.length || 0), 0);
    const trigger_count = scenes.reduce((n, s) => n + (s.triggers?.length || 0), 0);
    const event_step_count = (project?.eventChains || []).reduce((n, c) => n + (c.steps?.length || 0), 0);
    return { name: project?.name, scene_count: scenes.length, actor_count, sprite_count: project?.sprites?.length || 0, event_chain_count: project?.eventChains?.length || 0, event_step_count, collision_count, trigger_count };
  }
  async blocks() {
    if (this.mode === 'backend') return this.fetchJson('/api/blocks');
    return {
      Dialogue: [{ type: 'show_text', label: 'Show text', defaults: { text: 'Hello!' } }],
      Actor: [{ type: 'move_actor', label: 'Move actor', defaults: { actor: 'player', dx: 0, dy: 8 } }, { type: 'face_player', label: 'Face player', defaults: { actor: 'robot' } }],
      Scene: [{ type: 'change_scene', label: 'Change scene', defaults: { scene: 'school' } }],
      Logic: [{ type: 'set_flag', label: 'Set flag', defaults: { flag: 'met_robot', value: true } }, { type: 'if_flag', label: 'If flag', defaults: { flag: 'met_robot', then: [], else: [] } }],
      Sound: [{ type: 'play_sound', label: 'Play sound', defaults: { sound: 'blip' } }]
    };
  }
  async refresh() {
    if (this.mode === 'backend') {
      const project = await this.fetchJson('/api/project'); this.project = project;
      return { mode: this.mode, project, inventory: await this.fetchJson('/api/inventory'), blocks: await this.blocks() };
    }
    return { mode: this.mode, project: this.project, inventory: this.inventory(), blocks: await this.blocks() };
  }
  async propose(prompt) {
    if (this.mode === 'backend') return this.fetchJson('/api/propose', { method: 'POST', body: JSON.stringify({ prompt }) });
    return { id: 'patch_browser_robot', title: 'Add friendly robot helper', summary: 'Browser-safe patch. Review before applying.', risk: 'low', changes: [
      { op: 'add_event_chain', chain: { id: 'browser_helper_hint', name: 'Browser Helper Hint', trigger: { type: 'scene_start' } } },
      { op: 'add_event_step', chain: 'browser_helper_hint', step: { id: 'hint_text', type: 'show_text', text: prompt || 'Make a clear player hint.' } }
    ]};
  }
  applyLocalPatch(patch) {
    const p = structuredClone(this.project);
    for (const ch of patch.changes || []) {
      if (ch.op === 'add_event_chain' && !p.eventChains.some(c => c.id === ch.chain.id)) p.eventChains.push({ ...ch.chain, steps: [] });
      if (ch.op === 'add_event_step') { const c = p.eventChains.find(x => x.id === ch.chain); if (c) c.steps.push(ch.step); }
      if (ch.op === 'add_scene' && !p.scenes.some(s => s.id === ch.scene.id)) p.scenes.push({ ...ch.scene, actors: [], collision: [], triggers: [] });
      if (ch.op === 'add_actor') { const s = p.scenes.find(x => x.id === ch.scene); if (s && !s.actors.some(a => a.id === ch.actor.id)) s.actors.push(ch.actor); }
    }
    this.project = p;
    return { applied: true, backup: 'browser-memory', project: p };
  }
  async applyPatch(patch) {
    if (this.mode === 'backend') return this.fetchJson('/api/apply-patch', { method: 'POST', body: JSON.stringify({ patch }) });
    return this.applyLocalPatch(patch);
  }
  // ---- Editing (works in both backend and online demo mode) ----
  _commit(res) { if (res?.project) this.project = res.project; return this.project; }
  _localCommit(mutate) { const p = structuredClone(this.project); mutate(p); this.project = p; return p; }
  _scene(p, id) { const s = (p.scenes || []).find(x => x.id === id); if (!s) throw new Error(`scene not found: ${id}`); return s; }

  async addScene(id, name, background = null) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson('/api/scenes', { method: 'POST', body: JSON.stringify({ id, name, background }) }));
    return this._localCommit(p => {
      if ((p.scenes || []).some(s => s.id === id)) throw new Error(`scene already exists: ${id}`);
      (p.scenes ||= []).push({ id, name, background, actors: [], collision: [], triggers: [] });
    });
  }
  async addActor(sceneId, actor) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/scenes/${sceneId}/actors`, { method: 'POST', body: JSON.stringify(actor) }));
    return this._localCommit(p => {
      const s = this._scene(p, sceneId);
      if ((s.actors ||= []).some(a => a.id === actor.id)) throw new Error(`actor already exists: ${actor.id}`);
      s.actors.push({ direction: 'down', events: {}, ...actor });
    });
  }
  async updateActor(sceneId, actorId, fields) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/scenes/${sceneId}/actors/${actorId}`, { method: 'PATCH', body: JSON.stringify({ id: actorId, ...fields }) }));
    return this._localCommit(p => {
      const a = this._scene(p, sceneId).actors.find(x => x.id === actorId);
      if (!a) throw new Error(`actor not found: ${actorId}`);
      Object.assign(a, fields);
    });
  }
  async deleteActor(sceneId, actorId) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/scenes/${sceneId}/actors/${actorId}`, { method: 'DELETE' }));
    return this._localCommit(p => { const s = this._scene(p, sceneId); s.actors = (s.actors || []).filter(a => a.id !== actorId); });
  }
  async addChain(id, name, trigger = null) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson('/api/event-chains', { method: 'POST', body: JSON.stringify({ id, name, trigger }) }));
    return this._localCommit(p => {
      if ((p.eventChains ||= []).some(c => c.id === id)) throw new Error(`event chain already exists: ${id}`);
      p.eventChains.push({ id, name, trigger, steps: [] });
    });
  }
  async addStep(chainId, step) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/event-chains/${chainId}/steps`, { method: 'POST', body: JSON.stringify({ step }) }));
    return this._localCommit(p => { const c = (p.eventChains || []).find(x => x.id === chainId); if (!c) throw new Error(`chain not found: ${chainId}`); (c.steps ||= []).push(step); });
  }
  async deleteStep(chainId, stepId) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/event-chains/${chainId}/steps/${stepId}`, { method: 'DELETE' }));
    return this._localCommit(p => { const c = (p.eventChains || []).find(x => x.id === chainId); if (c) c.steps = (c.steps || []).filter(s => s.id !== stepId); });
  }
  async updateSprite(spriteId, sprite) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/sprites/${spriteId}`, { method: 'PUT', body: JSON.stringify({ sprite }) }));
    return this._localCommit(p => {
      const i = (p.sprites || []).findIndex(s => s.id === spriteId);
      if (i < 0) throw new Error(`sprite not found: ${spriteId}`);
      p.sprites[i] = { ...sprite, id: spriteId };
    });
  }

  async exportC() { if (this.mode !== 'backend') throw new Error('Local builder required for C export. Download the project and run SNES Studio locally.'); return this.fetchJson('/api/export-c', { method: 'POST' }); }
  async makeRom() { if (this.mode !== 'backend') throw new Error('Local builder required to build ROMs.'); return this.fetchJson('/api/make-rom', { method: 'POST', body: JSON.stringify({ skip_build: true, out_file: 'build/web-preview.sfc' }) }); }
  downloadProject() { const blob = new Blob([JSON.stringify(this.project, null, 2)], { type: 'application/json' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `${(this.project?.name || 'project').toLowerCase().replace(/[^a-z0-9]+/g, '-')}.snesproj`; a.click(); URL.revokeObjectURL(url); }
}
