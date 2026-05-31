// System prompt for the AI Coding Helper. Constrained to the four patch ops the
// human-reviewed apply pipeline supports, so generated patches always apply safely.
const PATCH_SYSTEM_PROMPT = `You are the Coding Helper for SNES Studio, a kid-friendly SNES game maker.
Given the current project and a request, output a SAFE PATCH as JSON only — no prose, no markdown fences.

Shape: {"title": str, "summary": str, "risk": "low"|"medium", "changes": [ ...ops ]}

Allowed ops (use ONLY these):
- {"op":"add_scene","scene":{"id":str,"name":str}}
- {"op":"add_actor","scene":sceneId,"actor":{"id":str,"name":str,"x":0-256,"y":0-224,"sprite":spriteId}}
- {"op":"update_actor","scene":sceneId,"actor_id":str,"fields":{"x"?:0-256,"y"?:0-224,"name"?:str,"sprite"?:spriteId,"direction"?:"up"|"down"|"left"|"right"}}
- {"op":"add_event_chain","chain":{"id":str,"name":str,"trigger":{"type":"scene_start"|"actor_interact"|"zone_enter","scene"?:id,"actor"?:id,"zone"?:id}}}
- {"op":"add_event_step","chain":chainId,"step":{"id":str,"type":TYPE,...}}
- {"op":"update_event_step","chain":chainId,"step_id":str,"fields":{...same fields as the step TYPE...}}
- {"op":"delete_event_step","chain":chainId,"step_id":str}
- {"op":"add_collision","scene":sceneId,"collision":{"id":str,"x":int,"y":int,"w":int,"h":int}}
- {"op":"add_trigger","scene":sceneId,"trigger":{"id":str,"name":str,"x":int,"y":int,"w":int,"h":int,"event"?:chainId}}

Event step TYPE and fields:
- show_text {"text":str}      // a line of dialogue
- change_scene {"scene":sceneId}
- set_flag {"flag":str,"value":bool}
- set_variable {"variable":str,"value":number|str}
- if_flag {"flag":str,"then":[steps],"else":[steps]}
- move_actor {"actor":id,"dx":int,"dy":int}
- face_player {"actor":id}
- play_sound {"sound":str}

Capabilities: dialogue and game logic ("scripts") are event chains made of steps — add_event_step with type show_text writes a new dialogue line, update_event_step edits an existing line's text. To change which sprite a character uses, update_actor with fields.sprite. To move/rename a character, update_actor with fields.x/fields.y/fields.name. (Drawing new sprite pixels is done in the Sprite editor / image import, not via this helper.)

Rules: reuse existing scene/sprite/actor/chain/step ids from the project; invent NEW unique ids only for things you add; prefer editing existing items (update_*) when the request is about something already in the project; keep it small and reviewable. Output JSON only.`;

export class StudioClient {
  constructor() {
    this.mode = 'loading';
    this.project = null;
    this.apiBase = '';
  }
  _withBase(url) {
    if (!url.startsWith('/api')) return url;
    return this.apiBase ? `${this.apiBase}${url}` : url;
  }
  async fetchJson(url, options = {}) {
    const res = await fetch(this._withBase(url), { headers: { 'Content-Type': 'application/json' }, ...options });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
  async _tryBackend(base) {
    this.apiBase = base;
    await this.fetchJson('/api/health');
  }
  async boot() {
    const configured = (import.meta.env.VITE_API_BASE || '').trim().replace(/\/+$/, '');
    const candidates = [];
    if (configured) candidates.push(configured);
    candidates.push('');
    if (!configured) {
      candidates.push('http://127.0.0.1:8765');
      candidates.push('http://localhost:8765');
    }
    try {
      // The desktop app may open the browser a beat before its local server is
      // ready to accept connections. Retry briefly so a slow start doesn't drop
      // us into online demo mode permanently. Only the desktop app is served from
      // localhost; the hosted demo has no backend, so it shouldn't pay the wait.
      let ok = false;
      const isLocal = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
      const attempts = isLocal ? 12 : 1;
      for (let i = 0; i < attempts && !ok; i++) {
        for (const base of candidates) {
          try {
            await this._tryBackend(base);
            ok = true;
            break;
          } catch (_) {}
        }
        if (!ok) await new Promise(r => setTimeout(r, 300));
      }
      if (!ok) throw new Error('backend unavailable');
      this.mode = 'backend';
      return this.refresh();
    } catch (_) {
      this.apiBase = '';
      this.mode = 'online';
      const project = await this.fetchJson(`${import.meta.env.BASE_URL}examples/pocket-bugs.snesproj`);
      this.project = project;
      return { mode: this.mode, project, inventory: this.inventory(project), blocks: await this.blocks() };
    }
  }
  backendTarget() {
    return this.apiBase || '(vite proxy /api)';
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
  async importProject(project) {
    if (this.mode === 'backend') {
      const res = await this.fetchJson('/api/project', { method: 'POST', body: JSON.stringify({ project }) });
      this.project = res.project;
      return { mode: this.mode, project: res.project, inventory: res.inventory, blocks: await this.blocks() };
    }
    this.project = project;
    return { mode: this.mode, project, inventory: this.inventory(project), blocks: await this.blocks() };
  }
  async loadExample(slug) {
    const project = await this.fetchJson(`${import.meta.env.BASE_URL}examples/${slug}.snesproj`);
    return this.importProject(project);
  }
  // ---- AI "Coding Helper": real LLM (bring-your-own-key) or deterministic fallback ----
  llmConfig() {
    try { return { key: localStorage.getItem('snesstudio_llm_key') || '', model: localStorage.getItem('snesstudio_llm_model') || 'claude-haiku-4-5' }; }
    catch { return { key: '', model: 'claude-haiku-4-5' }; }
  }
  projectSummary() {
    const p = this.project || {};
    const scenes = (p.scenes || []).map(s => `- "${s.id}" (${s.name}); actors: ${(s.actors || []).map(a => a.id).join(', ') || 'none'}`).join('\n');
    return `Scenes:\n${scenes}\nSprite ids: ${(p.sprites || []).map(s => s.id).join(', ') || 'none'}\nExisting event-chain ids: ${(p.eventChains || []).map(c => c.id).join(', ') || 'none'}`;
  }
  async proposeLLM(prompt) {
    const { key, model } = this.llmConfig();
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01', 'anthropic-dangerous-direct-browser-access': 'true' },
      body: JSON.stringify({
        model, max_tokens: 1024,
        system: [{ type: 'text', text: PATCH_SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
        messages: [{ role: 'user', content: `Current project:\n${this.projectSummary()}\n\nUser request: ${prompt}\n\nReturn ONLY the JSON patch.` }],
      }),
    });
    if (!res.ok) throw new Error(`Anthropic API ${res.status}: ${(await res.text()).slice(0, 200)}`);
    const data = await res.json();
    const text = (data.content || []).filter(b => b.type === 'text').map(b => b.text).join('');
    const m = text.match(/\{[\s\S]*\}/);
    if (!m) throw new Error('LLM did not return JSON.');
    const patch = JSON.parse(m[0]);
    return { id: 'patch_llm', title: patch.title || 'AI helper patch', summary: patch.summary || 'Generated by your LLM. Review before applying.', risk: patch.risk || 'low', changes: patch.changes || [] };
  }
  async propose(prompt) {
    if (this.llmConfig().key) return this.proposeLLM(prompt);
    if (this.mode === 'backend') return this.fetchJson('/api/propose', { method: 'POST', body: JSON.stringify({ prompt }) });
    const cid = `helper_hint_${Date.now().toString(36)}`;
    return { id: 'patch_browser_robot', title: 'Add a helper hint (offline)', summary: 'No LLM key set — this is a deterministic safe patch. Add an API key in AI settings for real AI help. Review before applying.', risk: 'low', changes: [
      { op: 'add_event_chain', chain: { id: cid, name: 'Helper Hint', trigger: { type: 'scene_start' } } },
      { op: 'add_event_step', chain: cid, step: { id: `${cid}_text`, type: 'show_text', text: prompt || 'Add a clear hint for the player here.' } },
    ]};
  }
  applyLocalPatch(patch) {
    const p = structuredClone(this.project);
    const sceneOf = id => (p.scenes || []).find(s => s.id === id);
    const chainOf = id => (p.eventChains || []).find(c => c.id === id);
    for (const ch of patch.changes || []) {
      if (ch.op === 'add_event_chain' && !p.eventChains.some(c => c.id === ch.chain.id)) p.eventChains.push({ ...ch.chain, steps: [] });
      if (ch.op === 'add_event_step') { const c = chainOf(ch.chain); if (c) (c.steps ||= []).push(ch.step); }
      if (ch.op === 'update_event_step') { const c = chainOf(ch.chain); const st = c && (c.steps || []).find(s => s.id === ch.step_id); if (st) Object.assign(st, ch.fields || {}); }
      if (ch.op === 'delete_event_step') { const c = chainOf(ch.chain); if (c) c.steps = (c.steps || []).filter(s => s.id !== ch.step_id); }
      if (ch.op === 'add_scene' && !p.scenes.some(s => s.id === ch.scene.id)) p.scenes.push({ ...ch.scene, actors: [], collision: [], triggers: [] });
      if (ch.op === 'add_actor') { const s = sceneOf(ch.scene); if (s && !(s.actors ||= []).some(a => a.id === ch.actor.id)) s.actors.push(ch.actor); }
      if (ch.op === 'update_actor') { const s = sceneOf(ch.scene); const a = s && (s.actors || []).find(x => x.id === ch.actor_id); if (a) Object.assign(a, ch.fields || {}); }
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
      (p.scenes ||= []).push({ id, name, background, actors: [], collision: [], triggers: [], paint: Array(32 * 28).fill(0) });
    });
  }
  async updateScene(sceneId, fields) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/scenes/${sceneId}`, { method: 'PATCH', body: JSON.stringify(fields) }));
    return this._localCommit(p => {
      const s = this._scene(p, sceneId);
      Object.assign(s, fields);
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
  async addSprite(sprite) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson('/api/sprites', { method: 'POST', body: JSON.stringify({ sprite }) }));
    return this._localCommit(p => {
      if ((p.sprites ||= []).some(s => s.id === sprite.id)) throw new Error(`sprite already exists: ${sprite.id}`);
      p.sprites.push({ ...sprite });
    });
  }
  async addCollision(sceneId, rect) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/scenes/${sceneId}/collision`, { method: 'POST', body: JSON.stringify(rect) }));
    return this._localCommit(p => {
      const s = this._scene(p, sceneId);
      if ((s.collision ||= []).some(c => c.id === rect.id)) throw new Error(`collision already exists: ${rect.id}`);
      s.collision.push({ ...rect });
    });
  }
  async updateCollision(sceneId, collisionId, fields) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/scenes/${sceneId}/collision/${collisionId}`, { method: 'PATCH', body: JSON.stringify({ id: collisionId, ...fields }) }));
    return this._localCommit(p => {
      const s = this._scene(p, sceneId);
      const c = (s.collision || []).find(x => x.id === collisionId);
      if (!c) throw new Error(`collision not found: ${collisionId}`);
      Object.assign(c, fields);
    });
  }
  async deleteCollision(sceneId, collisionId) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/scenes/${sceneId}/collision/${collisionId}`, { method: 'DELETE' }));
    return this._localCommit(p => {
      const s = this._scene(p, sceneId);
      s.collision = (s.collision || []).filter(x => x.id !== collisionId);
    });
  }
  async addTrigger(sceneId, trigger) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/scenes/${sceneId}/triggers`, { method: 'POST', body: JSON.stringify(trigger) }));
    return this._localCommit(p => {
      const s = this._scene(p, sceneId);
      if ((s.triggers ||= []).some(t => t.id === trigger.id)) throw new Error(`trigger already exists: ${trigger.id}`);
      s.triggers.push({ ...trigger });
    });
  }
  async updateTrigger(sceneId, triggerId, fields) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/scenes/${sceneId}/triggers/${triggerId}`, { method: 'PATCH', body: JSON.stringify({ id: triggerId, ...fields }) }));
    return this._localCommit(p => {
      const s = this._scene(p, sceneId);
      const t = (s.triggers || []).find(x => x.id === triggerId);
      if (!t) throw new Error(`trigger not found: ${triggerId}`);
      Object.assign(t, fields);
    });
  }
  async deleteTrigger(sceneId, triggerId) {
    if (this.mode === 'backend') return this._commit(await this.fetchJson(`/api/scenes/${sceneId}/triggers/${triggerId}`, { method: 'DELETE' }));
    return this._localCommit(p => {
      const s = this._scene(p, sceneId);
      s.triggers = (s.triggers || []).filter(x => x.id !== triggerId);
    });
  }

  async exportC() { if (this.mode !== 'backend') throw new Error('Local builder required for C export. Download the project and run SNES Studio locally.'); return this.fetchJson('/api/export-c', { method: 'POST' }); }
  async makeRom() {
    if (this.mode !== 'backend') throw new Error('Local builder required to build ROMs.');
    return this.fetchJson('/api/make-rom', { method: 'POST', body: JSON.stringify({ skip_build: false, out_file: 'build/web-preview.sfc' }) });
  }
  async toolchain() {
    if (this.mode !== 'backend') return { ready: false, online: true };
    try { return await this.fetchJson('/api/toolchain'); } catch { return { ready: false }; }
  }
  romUrl(file = 'build/web-preview.sfc') { return `/api/rom?file=${encodeURIComponent(file)}&t=${Date.now()}`; }
  downloadProject() { const blob = new Blob([JSON.stringify(this.project, null, 2)], { type: 'application/json' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `${(this.project?.name || 'project').toLowerCase().replace(/[^a-z0-9]+/g, '-')}.snesproj`; a.click(); URL.revokeObjectURL(url); }
}
