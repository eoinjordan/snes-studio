import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { motion } from 'framer-motion';
import { Gamepad2, FolderOpen, Save, Code2, Play, MonitorPlay, Download, Upload, Wifi, WifiOff, Plus, ChevronRight, Palette, Map, GitBranch, Blocks, Image as ImageIcon, MousePointer2, Move, Square, Circle, Link2, Paintbrush, Eraser, Copy, Trash2, Wand2, Eye, ShieldCheck, CheckCircle2, AlertTriangle, Users, MessageSquare, Settings2, Layers, X } from 'lucide-react';
import { StudioClient } from './api.js';
import './styles.css';

const SCENE_W = 256, SCENE_H = 224, SCALE_X = 2, SCALE_Y = 1.6;
const EXAMPLES = [
  { slug: 'mango-island', name: 'Mango Island', desc: 'Pirate point-and-click demake' },
  { slug: 'poachermon', name: 'Poachermon', desc: 'Safari rescue template' },
  { slug: 'hello-human', name: 'Hello Human', desc: 'Small starter project' }
];
const slug = (s) => (s || '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || 'item';
const uniqueId = (base, existing) => { const has = new Set(existing); let id = base, n = 2; while (has.has(id)) id = `${base}_${n++}`; return id; };
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const hexToRgb = (hex) => { const s = (hex || '').replace('#', ''); const f = s.length === 3 ? s.split('').map(c => c + c).join('') : s; const n = parseInt(f || '0', 16); return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 }; };

// Renders a sprite frame to a pixel-perfect canvas. Palette index 0 = transparent.
function SpriteThumb({ sprite, frame = 0, scale = 2, className = '' }) {
  const ref = useRef(null);
  const w = sprite?.width || 16, h = sprite?.height || 16;
  useEffect(() => {
    const cvs = ref.current; if (!cvs || !sprite) return;
    cvs.width = w; cvs.height = h;
    const ctx = cvs.getContext('2d');
    const img = ctx.createImageData(w, h);
    const px = sprite.frames?.[frame]?.pixels || [];
    const pal = sprite.palette || [];
    for (let i = 0; i < w * h; i++) {
      const idx = px[i] || 0;
      if (idx === 0 || !pal[idx]) { img.data[i * 4 + 3] = 0; continue; }
      const { r, g, b } = hexToRgb(pal[idx]);
      img.data[i * 4] = r; img.data[i * 4 + 1] = g; img.data[i * 4 + 2] = b; img.data[i * 4 + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
  }, [sprite, frame, w, h]);
  if (!sprite) return null;
  return <canvas ref={ref} className={className} style={{ width: w * scale, height: h * scale, imageRendering: 'pixelated' }} />;
}

function Pill({ children, tone='neutral' }) { return <span className={`pill ${tone}`}>{children}</span>; }
function Btn({ children, className='', ...props }) { return <button className={`btn ${className}`} {...props}>{children}</button>; }
function Tool({ icon: Icon, label, active, onClick }) { return <button title={label} aria-label={label} onClick={onClick} className={`tool ${active ? 'active' : ''}`}><Icon size={16}/>{label}</button>; }

function SceneStats({ scene, tool, selectedZone, actor }) {
  const selected = selectedZone ? `${selectedZone.kind}: ${selectedZone.id}` : (actor ? `actor: ${actor.name}` : 'none');
  return <div className="scene-stats">
    <span>{scene?.actors?.length || 0} actors</span>
    <span>{scene?.collision?.length || 0} collision</span>
    <span>{scene?.triggers?.length || 0} triggers</span>
    <span>{tool}</span>
    <span>{selected}</span>
  </div>;
}

function PatchModal({ patch, onClose, onApply }) {
  if (!patch) return null;
  return <div className="modal-backdrop"><div className="modal">
    <div className="modal-head"><div><h2>{patch.title}</h2><p>{patch.summary}</p></div><button className="icon" onClick={onClose}><X size={16}/></button></div>
    <div className="review-note"><strong>Human review required.</strong><p>The helper is proposing editor operations. Read them before applying.</p></div>
    <div className="patch-list">{(patch.changes||[]).map((c,i)=><div className="patch-line" key={i}><span>+</span><div><strong>{c.op}</strong><p>{c.actor?.name || c.chain?.name || c.step?.text || c.scene?.name || c.scene || c.chain || 'project change'}</p></div></div>)}</div>
    <div className="modal-actions"><Btn className="secondary" onClick={onClose}>Reject</Btn><Btn className="primary" onClick={onApply}><ShieldCheck size={16}/>Apply reviewed patch</Btn></div>
  </div></div>;
}

// Generic create form modal. fields: [{key,label,type,options?}]
function FieldModal({ title, fields, initial, submitLabel='Create', onClose, onSubmit }) {
  const [v, setV] = useState(initial || {});
  if (!fields) return null;
  const set = (k, val) => setV(s => ({ ...s, [k]: val }));
  const submit = (e) => { e.preventDefault(); onSubmit(v); };
  return <div className="modal-backdrop"><form className="modal" onSubmit={submit}>
    <div className="modal-head"><div><h2>{title}</h2></div><button type="button" className="icon" onClick={onClose}><X size={16}/></button></div>
    <div className="patch-list">{fields.map(f => <label key={f.key} className="field">{f.label}
      {f.type === 'select'
        ? <select value={v[f.key] ?? ''} onChange={e => set(f.key, e.target.value)}>{(f.options||[]).map(o => <option key={o.value} value={o.value}>{o.label}</option>)}</select>
        : <input type={f.type || 'text'} min={f.min} max={f.max} step={f.step} value={v[f.key] ?? ''} onChange={e => set(f.key, f.type === 'number' ? Number(e.target.value) : e.target.value)} autoFocus={f.autoFocus}/>}
    </label>)}</div>
    <div className="modal-actions"><Btn type="button" className="secondary" onClick={onClose}>Cancel</Btn><Btn type="submit" className="primary"><Plus size={16}/>{submitLabel}</Btn></div>
  </form></div>;
}

function SpriteEditor({ sprite, actor, onChange, onAssignToActor }) {
  const s = sprite;
  const [frameIdx, setFrameIdx] = useState(0);
  const [selColor, setSelColor] = useState(2);
  const [tool, setTool] = useState('pencil');
  const [pixels, setPixels] = useState([]);
  const [name, setName] = useState('');
  const painting = useRef(false);
  const dirty = useRef(false);
  const area = (s?.width || 16) * (s?.height || 16);

  useEffect(() => { setFrameIdx(0); }, [s?.id]);
  useEffect(() => { setName(s?.name || ''); }, [s?.id, s?.name]);
  useEffect(() => {
    const frame = s?.frames?.[frameIdx];
    const base = frame?.pixels?.length === area ? frame.pixels.slice() : Array(area).fill(0);
    setPixels(base); dirty.current = false;
  }, [s?.id, frameIdx, area]);

  if (!s) return <section className="card"><h2><Palette size={18}/> Sprite Editor</h2><p className="hint">No sprite selected.</p></section>;

  const commit = (next) => {
    if (!dirty.current) return;
    dirty.current = false;
    const frames = (s.frames || []).map((f, i) => i === frameIdx ? { ...f, pixels: next } : f);
    onChange({ ...s, frames });
  };
  const paint = (i) => setPixels(prev => {
    const val = tool === 'erase' ? 0 : selColor;
    if (prev[i] === val) return prev;
    dirty.current = true;
    const copy = prev.slice(); copy[i] = val; return copy;
  });
  const stop = () => { painting.current = false; commit(pixels); };
  const clearFrame = () => { const next = Array(area).fill(0); dirty.current = true; setPixels(next); const frames = (s.frames||[]).map((f,i)=>i===frameIdx?{...f,pixels:next}:f); onChange({ ...s, frames }); };
  const duplicateFrame = () => {
    const id = uniqueId(`${s.frames?.[frameIdx]?.id || 'frame'}_copy`, (s.frames||[]).map(f=>f.id));
    const frames = [...(s.frames||[]), { id, name: `Frame ${(s.frames?.length||0)+1}`, pixels: pixels.slice() }];
    onChange({ ...s, frames }); setFrameIdx(frames.length - 1);
  };
  const commitName = () => { if (name && name !== s.name) onChange({ ...s, name }); };
  const updatePalette = (i, color) => {
    const palette = (s.palette || []).slice();
    palette[i] = color;
    onChange({ ...s, palette });
  };

  return <section className="card"><div className="section-title"><h2><Palette size={18}/> Sprite Editor</h2><Pill tone="blue">{s.name}</Pill></div>
    <div className="sprite-layout">
      <div>
        <div className="pixel-grid" style={{gridTemplateColumns:`repeat(${s.width},1fr)`}} onPointerUp={stop} onPointerLeave={stop}>
          {pixels.map((p,i)=><div key={i} style={{background:s.palette[p] || '#fff', cursor:'crosshair'}}
            onPointerDown={()=>{painting.current=true; paint(i);}}
            onPointerEnter={()=>{ if(painting.current) paint(i); }} />)}
        </div>
        <div className="toolbar"><Tool icon={Paintbrush} label="Pencil" active={tool==='pencil'} onClick={()=>setTool('pencil')}/><Tool icon={Eraser} label="Erase" active={tool==='erase'} onClick={()=>setTool('erase')}/></div>
      </div>
      <div className="sprite-side">
        <label>Sprite name<input value={name} onChange={e=>setName(e.target.value)} onBlur={commitName}/></label>
        <div className="asset-meta"><span>{s.id}</span><span>{s.width}x{s.height}</span><span>{(s.frames||[]).length} frames</span></div>
        {actor ? <Btn className="secondary full" onClick={()=>onAssignToActor(s.id)}><Users size={16}/>Use for {actor.name}</Btn> : null}
        <strong>Palette</strong>
        <div className="palette-editor">{s.palette.map((c,i)=><label key={i} className={`palette-chip ${i===selColor?'active':''}`}><button type="button" title={c} onClick={()=>setSelColor(i)} style={{background:c}} /> <input type="color" value={c} onChange={e=>updatePalette(i, e.target.value)}/></label>)}</div>
        <strong>Frames</strong>
        <div className="frames">{(s.frames||[]).map((f,i)=><button className={i===frameIdx?'active':''} key={f.id} onClick={()=>setFrameIdx(i)}>Frame {i+1}</button>)}</div>
        <div className="two"><Btn className="secondary" onClick={duplicateFrame}><Copy size={16}/>Duplicate</Btn><Btn className="secondary" onClick={clearFrame}><Trash2 size={16}/>Clear</Btn></div>
      </div>
    </div>
  </section>;
}

function EventEditor({ chains, chainId, setChainId, blocks, onAddChain, onAddStep, onDeleteStep }) {
  const chain = chains?.find(c => c.id === chainId) || chains?.[0];
  return <section className="card"><div className="section-title"><h2><GitBranch size={18}/> Event Chain</h2><div className="two"><Pill tone="good">{chains?.length||0} chains</Pill><button className="icon" title="Add event chain" onClick={onAddChain}><Plus size={16}/></button></div></div>
    {chains?.length ? <div className="chain-tabs">{chains.map(c => <button key={c.id} className={`row ${c.id===chain?.id?'active':''}`} onClick={()=>setChainId(c.id)}><span>{c.name}</span><small>{c.steps?.length||0} steps</small></button>)}</div> : null}
    <div className="event-layout">
      <div className="block-palette"><h3>Block Palette</h3><p className="hint">Click a block to add it to the chain.</p>{Object.entries(blocks||{}).map(([cat,items])=><div key={cat}><strong>{cat}</strong>{items.map(b=><button key={b.type} disabled={!chain} onClick={()=>onAddStep(chain, b)}>{b.label}</button>)}</div>)}</div>
      <div className="chain"><h3>{chain?.name || 'No event chain yet'}</h3>{(chain?.steps||[]).map((step,i)=><div className={`event-step ${step.type}`} key={step.id}><span>{i+1}</span><div className="step-body"><strong>{step.type}</strong><p>{step.text || step.flag || step.scene || step.actor || step.sound || step.music || 'Edit parameters in inspector'}</p></div><button className="icon step-del" title="Remove step" onClick={()=>onDeleteStep(chain.id, step.id)}><Trash2 size={14}/></button></div>)}{chain && !(chain.steps||[]).length ? <p className="hint">No steps yet â€” pick a block on the left.</p> : null}</div>
    </div>
  </section>;
}

function SceneCanvas({ scene, sprites, selectedActor, actor, setSelectedActor, tool, setTool, selectedZone, setSelectedZone, onMoveActor, onAddActor, onAddCollision, onAddTrigger, onPaintScene }) {
  const ref = useRef(null);
  const [drag, setDrag] = useState(null); // {id, x, y}
  const [draw, setDraw] = useState(null); // {x, y, w, h, sx, sy}
  const painting = useRef(false);
  const paintDirty = useRef(false);
  const [paintTile, setPaintTile] = useState(1);
  const [paintCells, setPaintCells] = useState(scene?.paint || Array(32 * 28).fill(0));
  const paintRef = useRef(paintCells);
  const spriteById = useMemo(() => Object.fromEntries((sprites || []).map(s => [s.id, s])), [sprites]);
  const tileColors = ['transparent', '#9ca3af', '#22c55e', '#f59e0b', '#0ea5e9'];
  useEffect(() => { setPaintCells(scene?.paint || Array(32 * 28).fill(0)); paintDirty.current = false; }, [scene?.id, scene?.paint]);
  useEffect(() => { paintRef.current = paintCells; }, [paintCells]);
  useEffect(() => {
    const up = () => {
      if (!painting.current) return;
      painting.current = false;
      if (paintDirty.current) {
        paintDirty.current = false;
        onPaintScene(paintRef.current);
      }
    };
    window.addEventListener('pointerup', up);
    return () => window.removeEventListener('pointerup', up);
  }, [onPaintScene]);

  useEffect(() => {
    if (!drag) return;
    const rect = ref.current?.getBoundingClientRect();
    const move = (e) => {
      if (!rect) return;
      const x = clamp(Math.round((e.clientX - rect.left - drag.ox) / SCALE_X), 0, SCENE_W);
      const y = clamp(Math.round((e.clientY - rect.top - drag.oy) / SCALE_Y), 0, SCENE_H);
      setDrag(d => d && ({ ...d, x, y }));
    };
    const up = () => { setDrag(d => { if (d) onMoveActor(d.id, d.x, d.y); return null; }); };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
    return () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); };
  }, [drag?.id, onMoveActor]);

  const startDrag = (e, a) => {
    if (tool !== 'select' && tool !== 'move') return;
    setSelectedActor(a.id);
    setSelectedZone(null);
    const rect = ref.current.getBoundingClientRect();
    const ox = e.clientX - rect.left - a.x * SCALE_X;
    const oy = e.clientY - rect.top - a.y * SCALE_Y;
    setDrag({ id: a.id, x: a.x, y: a.y, ox, oy });
  };

  const rectFromDrag = (start, end) => {
    const x1 = clamp(Math.round(start.x / SCALE_X), 0, SCENE_W);
    const y1 = clamp(Math.round(start.y / SCALE_Y), 0, SCENE_H);
    const x2 = clamp(Math.round(end.x / SCALE_X), 0, SCENE_W);
    const y2 = clamp(Math.round(end.y / SCALE_Y), 0, SCENE_H);
    const x = Math.min(x1, x2);
    const y = Math.min(y1, y2);
    const w = Math.max(1, Math.abs(x2 - x1));
    const h = Math.max(1, Math.abs(y2 - y1));
    return { x, y, w, h };
  };

  const onCanvasPointerDown = (e) => {
    if (tool !== 'collision' && tool !== 'trigger') return;
    if (e.target.closest('.actor')) return;
    const rect = ref.current.getBoundingClientRect();
    const start = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    const next = rectFromDrag(start, start);
    setDraw({ ...next, sx: start.x, sy: start.y });
  };

  useEffect(() => {
    if (!draw || (tool !== 'collision' && tool !== 'trigger')) return;
    const rect = ref.current?.getBoundingClientRect();
    const move = (e) => {
      if (!rect) return;
      const end = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      const next = rectFromDrag({ x: draw.sx, y: draw.sy }, end);
      setDraw(d => d && ({ ...d, ...next }));
    };
    const up = () => {
      setDraw(d => {
        if (!d) return null;
        if (d.w > 1 && d.h > 1) {
          if (tool === 'collision') onAddCollision({ x: d.x, y: d.y, w: d.w, h: d.h });
          if (tool === 'trigger') onAddTrigger({ x: d.x, y: d.y, w: d.w, h: d.h });
        }
        return null;
      });
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
    return () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); };
  }, [draw?.sx, draw?.sy, tool, onAddCollision, onAddTrigger]);

  const paintCell = (idx) => {
    setPaintCells(prev => {
      const next = prev.slice();
      const v = tool === 'erase' ? 0 : paintTile;
      if (next[idx] === v) return prev;
      next[idx] = v;
      paintDirty.current = true;
      return next;
    });
  };

  return <section className="card grow"><div className="section-title"><div><h2>Scene Canvas: {scene?.name || 'No scene'}</h2></div><div className="two"><Pill tone="blue">SNES 256 x 224</Pill>{scene ? <button className="icon" title="Add actor" onClick={onAddActor}><Plus size={16}/></button> : null}</div></div>
    <SceneStats scene={scene} tool={tool} selectedZone={selectedZone} actor={actor}/>
    <div className="toolbar tool-rack">
      <div className="tool-group"><Tool icon={MousePointer2} label="Select" active={tool==='select'} onClick={()=>setTool('select')}/><Tool icon={Move} label="Move" active={tool==='move'} onClick={()=>setTool('move')}/></div>
      <div className="tool-group"><Tool icon={Paintbrush} label="Paint" active={tool==='paint'} onClick={()=>setTool('paint')}/><Tool icon={Eraser} label="Erase" active={tool==='erase'} onClick={()=>setTool('erase')}/></div>
      <div className="tool-group"><Tool icon={Square} label="Collision" active={tool==='collision'} onClick={()=>setTool('collision')}/><Tool icon={Circle} label="Trigger" active={tool==='trigger'} onClick={()=>setTool('trigger')}/><Tool icon={Link2} label="Link event" onClick={()=>setTool('select')}/></div>
    </div>
    {(tool==='paint'||tool==='erase') ? <div className="swatches">{tileColors.map((c,i)=><button key={i} onClick={()=>setPaintTile(i)} style={{background:c==='transparent'?'#ffffff':c, outline:i===paintTile?'2px solid #111827':'none'}} title={`Tile ${i}`}/>)}</div> : null}
    <div className="canvas" ref={ref} onPointerDown={onCanvasPointerDown}><div className="grid-bg"/><div className="ground"/>
      <div className="tile-layer" style={{gridTemplateColumns:'repeat(32, 1fr)'}}>
        {paintCells.map((v, idx) => <button key={idx} className="tile-cell" style={{background:tileColors[v] || tileColors[0]}} onPointerDown={(e)=>{ if(tool!=='paint'&&tool!=='erase') return; e.preventDefault(); painting.current=true; paintCell(idx); }} onPointerEnter={()=>{ if(painting.current && (tool==='paint'||tool==='erase')) paintCell(idx); }} />)}
      </div>
      {(scene?.collision||[]).map(c=><button key={c.id} className={`collision ${selectedZone?.kind==='collision'&&selectedZone?.id===c.id?'sel':''}`} style={{left:c.x*SCALE_X, top:c.y*SCALE_Y, width:c.w*SCALE_X, height:c.h*SCALE_Y}} onClick={()=>{ setSelectedZone({kind:'collision',id:c.id}); setSelectedActor(null); }}>Collision</button>)}
      {(scene?.triggers||[]).map(t=><button key={t.id} className={`trigger ${selectedZone?.kind==='trigger'&&selectedZone?.id===t.id?'sel':''}`} style={{left:t.x*SCALE_X, top:t.y*SCALE_Y, width:t.w*SCALE_X, height:t.h*SCALE_Y}} onClick={()=>{ setSelectedZone({kind:'trigger',id:t.id}); setSelectedActor(null); }}>Trigger</button>)}
      {draw ? <div className={tool === 'collision' ? 'collision' : 'trigger'} style={{left:draw.x*SCALE_X, top:draw.y*SCALE_Y, width:draw.w*SCALE_X, height:draw.h*SCALE_Y}}>{tool === 'collision' ? 'Collision' : 'Trigger'}</div> : null}
      {(scene?.actors||[]).map(a=>{ const pos = drag?.id===a.id ? drag : a; const spr = spriteById[a.sprite]; return <button key={a.id} onPointerDown={(e)=>startDrag(e,a)} className="actor" style={{left:pos.x*SCALE_X, top:pos.y*SCALE_Y, touchAction:'none'}}><motion.div animate={selectedActor===a.id?{y:[0,-4,0]}:{}} transition={{repeat:Infinity,duration:1.3}} className={`actor-spr ${selectedActor===a.id?'sel':''}`}>{spr ? <SpriteThumb sprite={spr} scale={2}/> : null}</motion.div><span>{a.name}</span></button>; })}
      <div className="hud">A Talk · B Jump · Start Menu</div></div>
  </section>;
}

function SceneTools({ scene, selectedZone, setSelectedZone, onUpdateCollision, onDeleteCollision, onUpdateTrigger, onDeleteTrigger }) {
  const selected = !selectedZone ? null : (selectedZone.kind === 'collision'
    ? (scene?.collision || []).find(c => c.id === selectedZone.id)
    : (scene?.triggers || []).find(t => t.id === selectedZone.id));
  const [form, setForm] = useState({});
  useEffect(() => { setForm(selected ? { ...selected } : {}); }, [selectedZone?.kind, selectedZone?.id]);
  const apply = () => {
    if (!selected) return;
    const fields = { x: Number(form.x)||0, y: Number(form.y)||0, w: Number(form.w)||1, h: Number(form.h)||1 };
    if (selectedZone.kind === 'collision') onUpdateCollision(selected.id, fields);
    if (selectedZone.kind === 'trigger') onUpdateTrigger(selected.id, { ...fields, name: form.name || selected.name, event: form.event || null });
  };
  return <section className="card">
    <div className="section-title"><h2><Map size={18}/> Scene Tools</h2><Pill tone="blue">{(scene?.collision?.length||0)+(scene?.triggers?.length||0)} zones</Pill></div>
    <div className="zone-list">
      {(scene?.collision||[]).map(c=><button key={c.id} className={`row ${selectedZone?.kind==='collision'&&selectedZone?.id===c.id?'active':''}`} onClick={()=>setSelectedZone({kind:'collision',id:c.id})}><span>{c.id}</span><small>Collision {c.w}×{c.h}</small></button>)}
      {(scene?.triggers||[]).map(t=><button key={t.id} className={`row ${selectedZone?.kind==='trigger'&&selectedZone?.id===t.id?'active':''}`} onClick={()=>setSelectedZone({kind:'trigger',id:t.id})}><span>{t.name}</span><small>Trigger {t.w}×{t.h}</small></button>)}
    </div>
    {selected ? <div>
      <label>X<input type="number" value={form.x ?? 0} onChange={e=>setForm(f=>({...f,x:e.target.value}))} onBlur={apply}/></label>
      <label>Y<input type="number" value={form.y ?? 0} onChange={e=>setForm(f=>({...f,y:e.target.value}))} onBlur={apply}/></label>
      <label>W<input type="number" value={form.w ?? 1} onChange={e=>setForm(f=>({...f,w:e.target.value}))} onBlur={apply}/></label>
      <label>H<input type="number" value={form.h ?? 1} onChange={e=>setForm(f=>({...f,h:e.target.value}))} onBlur={apply}/></label>
      {selectedZone.kind==='trigger' ? <><label>Name<input value={form.name ?? ''} onChange={e=>setForm(f=>({...f,name:e.target.value}))} onBlur={apply}/></label><label>Event chain id<input value={form.event ?? ''} onChange={e=>setForm(f=>({...f,event:e.target.value}))} onBlur={apply}/></label></> : null}
      <Btn className="secondary full" onClick={()=> selectedZone.kind==='collision' ? onDeleteCollision(selected.id) : onDeleteTrigger(selected.id)}><Trash2 size={16}/>Delete zone</Btn>
    </div> : <p className="hint">Select a collision or trigger to edit it.</p>}
  </section>;
}

function SceneHierarchy({ scene, selectedActor, setSelectedActor, selectedZone, setSelectedZone }) {
  const [q, setQ] = useState('');
  const term = q.trim().toLowerCase();
  const actorItems = (scene?.actors || []).filter(a => !term || a.name.toLowerCase().includes(term) || a.id.toLowerCase().includes(term));
  const collisionItems = (scene?.collision || []).filter(c => !term || c.id.toLowerCase().includes(term));
  const triggerItems = (scene?.triggers || []).filter(t => !term || t.id.toLowerCase().includes(term) || (t.name || '').toLowerCase().includes(term));
  return <section className="card">
    <div className="section-title"><h2><Layers size={18}/> Hierarchy</h2><Pill tone="blue">{(scene?.actors?.length||0)+(scene?.collision?.length||0)+(scene?.triggers?.length||0)} items</Pill></div>
    <input placeholder="Search scene objects..." value={q} onChange={e=>setQ(e.target.value)} />
    <div className="hier-group"><strong>Actors</strong>{actorItems.map(a => <button key={a.id} className={`row ${selectedActor===a.id?'active':''}`} onClick={()=>{ setSelectedActor(a.id); setSelectedZone(null); }}><span>{a.name}</span><small>{a.id} · ({a.x},{a.y})</small></button>)}{!actorItems.length ? <p className="hint">No matching actors.</p> : null}</div>
    <div className="hier-group"><strong>Collision</strong>{collisionItems.map(c => <button key={c.id} className={`row ${selectedZone?.kind==='collision'&&selectedZone?.id===c.id?'active':''}`} onClick={()=>{ setSelectedZone({kind:'collision',id:c.id}); setSelectedActor(null); }}><span>{c.id}</span><small>{c.w}×{c.h} at {c.x},{c.y}</small></button>)}{!collisionItems.length ? <p className="hint">No matching collision zones.</p> : null}</div>
    <div className="hier-group"><strong>Triggers</strong>{triggerItems.map(t => <button key={t.id} className={`row ${selectedZone?.kind==='trigger'&&selectedZone?.id===t.id?'active':''}`} onClick={()=>{ setSelectedZone({kind:'trigger',id:t.id}); setSelectedActor(null); }}><span>{t.name}</span><small>{t.id} · {t.event || 'no event'}</small></button>)}{!triggerItems.length ? <p className="hint">No matching triggers.</p> : null}</div>
  </section>;
}

function Inspector({ scene, actor, chains, onUpdate, onDelete }) {
  const [form, setForm] = useState({});
  useEffect(() => { setForm({ name: actor?.name ?? '', x: actor?.x ?? 0, y: actor?.y ?? 0, interact: actor?.events?.interact ?? '' }); }, [actor?.id]);
  if (!actor) return <section className="card"><div className="section-title"><h2><Settings2 size={18}/> Inspector</h2></div><p>Select or add an actor to edit its properties.</p></section>;
  const commit = (fields) => onUpdate(scene.id, actor.id, fields);
  const commitInteract = (v) => commit({ events: { ...(actor.events||{}), ...(v ? { interact: v } : {}) } });
  return <section className="card"><div className="section-title"><h2><Settings2 size={18}/> Inspector</h2><Pill tone="blue">{actor.sprite||'none'}</Pill></div>
    <label>Actor name<input value={form.name} onChange={e=>setForm(f=>({...f,name:e.target.value}))} onBlur={()=>form.name!==actor.name && commit({name:form.name})}/></label>
    <div className="two">
      <label>X<input type="number" value={form.x} onChange={e=>setForm(f=>({...f,x:Number(e.target.value)}))} onBlur={()=>form.x!==actor.x && commit({x:Number(form.x)})}/></label>
      <label>Y<input type="number" value={form.y} onChange={e=>setForm(f=>({...f,y:Number(e.target.value)}))} onBlur={()=>form.y!==actor.y && commit({y:Number(form.y)})}/></label>
    </div>
    <label>Interact event<select value={form.interact} onChange={e=>{ setForm(f=>({...f,interact:e.target.value})); commitInteract(e.target.value); }}>
      <option value="">none</option>{(chains||[]).map(c=><option key={c.id} value={c.id}>{c.name}</option>)}
    </select></label>
    <Btn className="secondary full" onClick={()=>onDelete(scene.id, actor.id)}><Trash2 size={16}/>Delete actor</Btn>
  </section>;
}

// In-browser SNES emulator (EmulatorJS, loaded from CDN). Plays a homebrew .sfc
// the user loads from disk â€” no copyrighted ROMs are bundled. EmulatorJS attaches
// to window globals, so each ROM load remounts a fresh host div via React key.
const EJS_DATA = 'https://cdn.emulatorjs.org/stable/data/';
function RomPreview({ romUrl, romName, onPick, onPlayBuiltIn }) {
  const hostRef = useRef(null);
  useEffect(() => {
    if (!romUrl || !hostRef.current) return;
    // Tear down any previous EmulatorJS instance before starting a new one.
    try { window.EJS_emulator?.callEvent?.('exit'); } catch (_) {}
    delete window.EJS_emulator;
    hostRef.current.innerHTML = '<div id="ejs-game" style="width:100%;height:100%"></div>';
    Object.assign(window, {
      EJS_player: '#ejs-game',
      EJS_core: 'snes',
      EJS_gameUrl: romUrl,
      EJS_gameName: romName || 'SNES Studio ROM',
      EJS_pathtodata: EJS_DATA,
      EJS_startOnLoaded: true,
      EJS_DEBUG_XX: false,
    });
    const prev = document.getElementById('ejs-loader');
    if (prev) prev.remove();
    const script = document.createElement('script');
    script.id = 'ejs-loader';
    script.src = `${EJS_DATA}loader.js`;
    script.async = true;
    document.body.appendChild(script);
    return () => {
      try { window.EJS_emulator?.callEvent?.('exit'); } catch (_) {}
      delete window.EJS_emulator;
      document.getElementById('ejs-loader')?.remove();
    };
  }, [romUrl, romName]);

  return <section className="card preview-card">
    <div className="section-title"><h2><MonitorPlay size={18}/> ROM Preview</h2>
      <Btn className="secondary compact" onClick={onPick}><Upload size={16}/>Load .sfc / .smc</Btn></div>
    {romUrl
      ? <div className="emu-host" key={romUrl} ref={hostRef}/>
      : <div className="preview-empty">
          <MonitorPlay size={40}/>
          <h3>Play a homebrew ROM</h3>
          {onPlayBuiltIn ? <Btn className="primary" onClick={onPlayBuiltIn}><Play size={16}/>Play Poachermon (built-in)</Btn> : null}
          <p>â€¦or load a SNES <code>.sfc</code> / <code>.smc</code> file to play it here with EmulatorJS.
             Build your own locally with <code>snes-studio make:rom</code> (PVSnesLib), or drop in any homebrew ROM you own.</p>
          <p className="hint">The built-in Poachermon ROM is generated by SNES Studio. Files stay in your browser.</p>
        </div>}
  </section>;
}

function App(){
  const client = useRef(null);
  const [mode,setMode]=useState('loading'); const [project,setProject]=useState(null); const [inventory,setInventory]=useState({}); const [blocks,setBlocks]=useState({});
  const [sceneId,setSceneId]=useState(null); const [actorId,setActorId]=useState(null); const [chainId,setChainId]=useState(null);
  const [sceneTool,setSceneTool]=useState('select');
  const [selectedZone,setSelectedZone]=useState(null);
  const [spriteId,setSpriteId]=useState(null);
  const [view,setView]=useState('scene'); const [prompt,setPrompt]=useState('Make the robot wave, then explain how to talk to characters.');
  const [patch,setPatch]=useState(null); const [log,setLog]=useState('Starting SNES Studio.'); const [form,setForm]=useState(null);
  const [rom,setRom]=useState(null); // {url, name}
  const fileInput = useRef(null);
  const romInput = useRef(null);
  const releaseRepo = (import.meta.env.VITE_GITHUB_REPO || '').trim();
  const releaseBase = releaseRepo ? `https://github.com/${releaseRepo}/releases/latest/download` : `${import.meta.env.BASE_URL}downloads`;
  const winInstaller = `${releaseBase}/SNES-Studio-Setup.exe`;
  const macInstaller = `${releaseBase}/SNES-Studio-macOS.pkg`;

  function applySnap(s){ setMode(s.mode); setProject(s.project); setInventory(s.inventory); setBlocks(s.blocks); }
  useEffect(()=>{ client.current=new StudioClient(); client.current.boot().then(s=>{ applySnap(s); setSceneId(s.project?.scenes?.[0]?.id); setChainId(s.project?.eventChains?.[0]?.id); setSpriteId(s.project?.sprites?.[0]?.id); setLog(s.mode==='backend'?`Backend connected: ${client.current.backendTarget()}`:'Online demo mode.'); }).catch(e=>setLog(e.message)); },[]);

  const scene = useMemo(()=>project?.scenes?.find(s=>s.id===sceneId)||project?.scenes?.[0], [project,sceneId]);
  const actor = useMemo(()=>scene?.actors?.find(a=>a.id===actorId)||null, [scene,actorId]);
  const sprite = useMemo(()=>project?.sprites?.find(s=>s.id===spriteId)||project?.sprites?.find(s=>s.id===(actor?.sprite))||project?.sprites?.[0], [project,actor,spriteId]);
  useEffect(()=>{ setSelectedZone(null); }, [scene?.id]);

  // run a client editing call, then sync project + inventory
  async function commit(promise, msg){ try{ const proj = await promise; setProject(proj); setInventory(client.current.inventory(proj)); if(msg) setLog(msg); return proj; }catch(e){ setLog(`Error: ${e.message}`); throw e; } }

  const onMoveActor = (id,x,y)=> commit(client.current.updateActor(scene.id, id, {x,y}), `Moved ${id} to (${x}, ${y}).`);
  const onUpdateActor = (sid,id,fields)=> commit(client.current.updateActor(sid, id, fields), `Updated ${id}.`);
  const onDeleteActor = (sid,id)=>{ commit(client.current.deleteActor(sid,id), `Deleted ${id}.`); setActorId(null); };
  const onPaintSprite = (s)=> commit(client.current.updateSprite(s.id, s), `Saved sprite ${s.name}.`);
  const onAddSprite = (sprite) => commit(client.current.addSprite(sprite), `Added sprite ${sprite.name}.`);
  const onAssignSprite = (sid) => {
    if (!actor || !scene) return;
    setSpriteId(sid);
    return commit(client.current.updateActor(scene.id, actor.id, { sprite: sid }), `Assigned ${sid} to ${actor.name}.`);
  };
  const onAddCollision = ({x,y,w,h}) => {
    const ids = (scene?.collision || []).map(c => c.id);
    const id = uniqueId('collision', ids);
    return commit(client.current.addCollision(scene.id, { id, x, y, w, h }), `Added collision zone ${id}.`);
  };
  const onAddTrigger = ({x,y,w,h}) => {
    const ids = (scene?.triggers || []).map(t => t.id);
    const id = uniqueId('trigger', ids);
    return commit(client.current.addTrigger(scene.id, { id, name: id, x, y, w, h }), `Added trigger zone ${id}.`);
  };
  const onUpdateCollision = (id, fields) => commit(client.current.updateCollision(scene.id, id, fields), `Updated collision ${id}.`);
  const onDeleteCollision = (id) => { commit(client.current.deleteCollision(scene.id, id), `Deleted collision ${id}.`); if(selectedZone?.id===id) setSelectedZone(null); };
  const onUpdateTrigger = (id, fields) => commit(client.current.updateTrigger(scene.id, id, fields), `Updated trigger ${id}.`);
  const onDeleteTrigger = (id) => { commit(client.current.deleteTrigger(scene.id, id), `Deleted trigger ${id}.`); if(selectedZone?.id===id) setSelectedZone(null); };
  const onPaintScene = (paint) => commit(client.current.updateScene(scene.id, { paint }), `Updated scene paint.`);
  const onAddStep = (chain, block)=>{ if(!chain) return; const { then, else:_e, ...rest } = block.defaults||{}; const step={ id: uniqueId(slug(block.type), (chain.steps||[]).map(s=>s.id)), type: block.type, ...rest }; if(block.type==='if_flag'){ step.then=[]; step.else=[]; } commit(client.current.addStep(chain.id, step), `Added ${block.label} step.`); };
  const onDeleteStep = (cid, sid)=> commit(client.current.deleteStep(cid, sid), 'Removed step.');

  function openSceneForm(){ setForm({ kind:'scene', title:'Add scene', submitLabel:'Add scene', fields:[{key:'name',label:'Scene name',type:'text',autoFocus:true}] }); }
  function openActorForm(){ if(!scene) return; setForm({ kind:'actor', title:`Add actor to ${scene.name}`, submitLabel:'Add actor', initial:{x:120,y:120,sprite:project?.sprites?.[0]?.id||''}, fields:[
    {key:'name',label:'Actor name',type:'text',autoFocus:true},{key:'x',label:'X (0â€“256)',type:'number'},{key:'y',label:'Y (0â€“224)',type:'number'},
    {key:'sprite',label:'Sprite',type:'select',options:(project?.sprites||[]).map(s=>({value:s.id,label:s.name}))}] }); }
  function openChainForm(){ setForm({ kind:'chain', title:'Add event chain', submitLabel:'Add chain', fields:[{key:'name',label:'Chain name',type:'text',autoFocus:true}] }); }
  function openSpriteForm(){ setForm({ kind:'sprite', title:'Add sprite', submitLabel:'Add sprite', initial:{width:16,height:16,color1:'#64748b',color2:'#67e8f9',color3:'#ffffff'}, fields:[
    {key:'name',label:'Sprite name',type:'text',autoFocus:true},{key:'width',label:'Width',type:'number',min:8,max:32,step:8},{key:'height',label:'Height',type:'number',min:8,max:32,step:8},
    {key:'color1',label:'Color 1',type:'color'},{key:'color2',label:'Color 2',type:'color'},{key:'color3',label:'Color 3',type:'color'}] }); }

  async function submitForm(v){
    const kind = form.kind; setForm(null);
    try {
      if(kind==='scene'){ const id=uniqueId(slug(v.name), (project?.scenes||[]).map(s=>s.id)); await commit(client.current.addScene(id, v.name||'New Scene'), `Added scene ${v.name}.`); setSceneId(id); }
      if(kind==='actor'){ const id=uniqueId(slug(v.name), (scene?.actors||[]).map(a=>a.id)); await commit(client.current.addActor(scene.id, {id, name:v.name||'New Actor', x:clamp(Number(v.x)||0,0,SCENE_W), y:clamp(Number(v.y)||0,0,SCENE_H), sprite:v.sprite||null}), `Added actor ${v.name}.`); setActorId(id); }
      if(kind==='chain'){ const id=uniqueId(slug(v.name), (project?.eventChains||[]).map(c=>c.id)); await commit(client.current.addChain(id, v.name||'New Chain'), `Added chain ${v.name}.`); setChainId(id); }
      if(kind==='sprite'){
        const w = clamp(Number(v.width)||16, 8, 32), h = clamp(Number(v.height)||16, 8, 32);
        const id=uniqueId(slug(v.name), (project?.sprites||[]).map(s=>s.id));
        const pixels = Array(w*h).fill(0);
        await onAddSprite({ id, name:v.name||'New Sprite', width:w, height:h, palette:['#000000', v.color1||'#64748b', v.color2||'#67e8f9', v.color3||'#ffffff'], frames:[{id:'idle_0', name:'Idle', pixels}] });
        setSpriteId(id); setView('sprite');
      }
    } catch(_) {}
  }

  async function propose(){ const p=await client.current.propose(prompt); setPatch(p); setLog('Patch proposed. Review before applying.'); }
  async function apply(){ const proj = await client.current.applyPatch(patch); setPatch(null); const p = proj.project || client.current.project; setProject(p); setInventory(client.current.inventory(p)); setLog('Patch applied after human review.'); }
  async function exportC(){ try{ const r=await client.current.exportC(); setLog(`Generated ${r.files?.length||0} files.`);}catch(e){setLog(e.message);} }
  async function build(){ try{ const r=await client.current.makeRom(); setLog(`ROM artifact: ${r.rom} (${r.bytes} bytes).`);}catch(e){setLog(e.message);} }
  function openProject(){ fileInput.current?.click(); }
  function pickRom(){ romInput.current?.click(); }
  function playBuiltIn(){ setRom(prev=>{ if(prev?.url?.startsWith('blob:')) URL.revokeObjectURL(prev.url); const cacheBust = Date.now(); return { url: `${import.meta.env.BASE_URL}roms/poachermon.sfc?cacheBust=${cacheBust}`, name: 'Poachermon (built-in)' }; }); setView('preview'); setLog('Loaded the built-in Poachermon ROM.'); }
  function onRomFile(e){ const file=e.target.files?.[0]; if(!file) return; setRom(prev=>{ if(prev?.url) URL.revokeObjectURL(prev.url); return { url: URL.createObjectURL(file), name: file.name }; }); setView('preview'); setLog(`Loaded ROM ${file.name}.`); e.target.value=''; }
  async function onFile(e){ const file=e.target.files?.[0]; if(!file) return; try{ const data=JSON.parse(await file.text()); const snap = await client.current.importProject(data); applySnap(snap); setSceneId(snap.project.scenes?.[0]?.id); setChainId(snap.project.eventChains?.[0]?.id); setSpriteId(snap.project.sprites?.[0]?.id); setActorId(null); setSelectedZone(null); setLog(`Loaded ${file.name}. Build ROM now compiles this project.`);}catch(err){ setLog(`Could not load project: ${err.message}`);} e.target.value=''; }
  async function loadExample(slug, name){
    try {
      const snap = await client.current.loadExample(slug);
      applySnap(snap);
      setSceneId(snap.project.scenes?.[0]?.id);
      setChainId(snap.project.eventChains?.[0]?.id);
      setSpriteId(snap.project.sprites?.[0]?.id);
      setActorId(null);
      setSelectedZone(null);
      setView('scene');
      setLog(`Loaded ${name}. Build ROM now compiles this project.`);
    } catch (err) {
      setLog(`Could not load ${name}: ${err.message}`);
    }
  }

  return <div className="page"><div className="shell"><header className="topbar"><div className="brand"><div className="logo"><Gamepad2/></div><div><h1>SNES Studio</h1><p>Scene editor Â· sprite painter Â· event chains Â· human-reviewed coding helper</p></div></div><div className="actions"><Btn className="secondary" onClick={openProject}><FolderOpen size={16}/>Open</Btn><Btn className="secondary" onClick={()=>client.current.downloadProject()}><Save size={16}/>Save</Btn><Btn className="secondary" onClick={exportC}><Code2 size={16}/>Export C</Btn><Btn className="secondary" onClick={pickRom}><MonitorPlay size={16}/>Preview ROM</Btn><Btn className="primary" onClick={build}><Play size={16}/>Build ROM</Btn></div></header>
    <input ref={fileInput} type="file" accept=".snesproj,.json,application/json" style={{display:'none'}} onChange={onFile}/>
    <input ref={romInput} type="file" accept=".sfc,.smc" style={{display:'none'}} onChange={onRomFile}/>
    <div className="modebar">{mode==='backend'?<Wifi size={16}/>:<WifiOff size={16}/>}<strong>{mode==='backend'?'Backend mode':'Online demo mode'}</strong><span>{log}</span><Btn className="secondary compact" onClick={()=>client.current.downloadProject()}><Download size={16}/>Download project</Btn></div>
    <div className="workspace">
      <aside className="left">
        <section className="card"><div className="section-title"><h2>Project</h2><Pill tone={mode==='backend'?'good':'blue'}>{mode}</Pill></div><div className="project-card"><strong>{project?.name||'Loading'}</strong><span>{inventory.scene_count||0} scenes Â· {inventory.actor_count||0} actors Â· {inventory.event_chain_count||0} chains</span></div></section>
        <section className="card"><div className="section-title"><h2>Example Games</h2><Pill tone="warn">load</Pill></div>{EXAMPLES.map(ex=><button className={`row example-row ${project?.name===ex.name?'active':''}`} key={ex.slug} onClick={()=>loadExample(ex.slug, ex.name)}><span>{ex.name}</span><small>{ex.desc}</small><ChevronRight size={16}/></button>)}</section>
        <section className="card"><div className="section-title"><h2>Scenes</h2><button className="icon" title="Add scene" onClick={openSceneForm}><Plus size={16}/></button></div>{(project?.scenes||[]).map(s=><button className={`row ${s.id===scene?.id?'active':''}`} key={s.id} onClick={()=>{setSceneId(s.id); setActorId(null);}}><span>{s.name}</span><small>{s.actors?.length||0} actors Â· {s.triggers?.length||0} triggers</small><ChevronRight size={16}/></button>)}</section>
        <section className="card"><div className="section-title"><h2><ImageIcon size={16}/> Assets</h2><button className="icon" title="Add sprite" onClick={openSpriteForm}><Plus size={16}/></button></div>{(project?.sprites||[]).map(s=><button className={`asset asset-spr ${s.id===sprite?.id?'active':''}`} key={s.id} onClick={()=>{setSpriteId(s.id); setView('sprite');}}><SpriteThumb sprite={s} scale={2}/><span>{s.name}<small>Sprite · {s.width}x{s.height} · {(s.frames||[]).length} frames</small></span></button>)}</section>
      </aside>
      <main className="main">
        <section className="card"><div className="tabs"><Tool icon={Map} label="Scene" active={view==='scene'} onClick={()=>setView('scene')}/><Tool icon={Palette} label="Sprite" active={view==='sprite'} onClick={()=>setView('sprite')}/><Tool icon={GitBranch} label="Events" active={view==='events'} onClick={()=>setView('events')}/><Tool icon={Blocks} label="Blocks" active={view==='blocks'} onClick={()=>setView('blocks')}/><Tool icon={MonitorPlay} label="ROM Preview" active={view==='preview'} onClick={()=>setView('preview')}/></div></section>
        {view==='scene'&&<SceneCanvas scene={scene} sprites={project?.sprites} selectedActor={actor?.id} actor={actor} setSelectedActor={setActorId} tool={sceneTool} setTool={setSceneTool} selectedZone={selectedZone} setSelectedZone={setSelectedZone} onMoveActor={onMoveActor} onAddActor={openActorForm} onAddCollision={onAddCollision} onAddTrigger={onAddTrigger} onPaintScene={onPaintScene}/>}
        {view==='sprite'&&<SpriteEditor sprite={sprite} actor={actor} onChange={onPaintSprite} onAssignToActor={onAssignSprite}/>}
        {(view==='events'||view==='blocks')&&<EventEditor chains={project?.eventChains||[]} chainId={chainId} setChainId={setChainId} blocks={blocks} onAddChain={openChainForm} onAddStep={onAddStep} onDeleteStep={onDeleteStep}/>}
        {view==='preview'&&<RomPreview romUrl={rom?.url} romName={rom?.name} onPick={pickRom} onPlayBuiltIn={playBuiltIn}/>}
      </main>
      <aside className="right">
        {view==='scene'
          ? <><SceneHierarchy scene={scene} selectedActor={actor?.id} setSelectedActor={setActorId} selectedZone={selectedZone} setSelectedZone={setSelectedZone}/>{selectedZone ? <SceneTools scene={scene} selectedZone={selectedZone} setSelectedZone={setSelectedZone} onUpdateCollision={onUpdateCollision} onDeleteCollision={onDeleteCollision} onUpdateTrigger={onUpdateTrigger} onDeleteTrigger={onDeleteTrigger}/> : <Inspector scene={scene} actor={actor} chains={project?.eventChains||[]} onUpdate={onUpdateActor} onDelete={onDeleteActor}/>}</>
          : <Inspector scene={scene} actor={actor} chains={project?.eventChains||[]} onUpdate={onUpdateActor} onDelete={onDeleteActor}/>}
        <section className="card"><div className="section-title"><h2><Download size={18}/> Installers</h2></div><p className="hint">Download desktop installers from the latest release.</p><div className="two"><a className="btn secondary" href={winInstaller}><Download size={16}/>Windows</a><a className="btn secondary" href={macInstaller}><Download size={16}/>macOS</a></div></section>
        <section className="card"><div className="section-title"><h2><Wand2 size={18}/> Coding Helper</h2></div><textarea value={prompt} onChange={e=>setPrompt(e.target.value)}/><Btn className="primary full" onClick={propose}><Wand2 size={16}/>Propose safe patch</Btn></section>
        <section className="card"><div className="section-title"><h2><CheckCircle2 size={18}/> Build Checks</h2></div><p className="check"><CheckCircle2 size={14}/>Project schema valid</p><p className="check"><CheckCircle2 size={14}/>Event chains compile to C</p><p className="warn"><AlertTriangle size={14}/>Real SNES build needs PVSnesLib runtime</p></section>
        <section className="card"><h2><Users size={18}/> Human Review</h2><p><MessageSquare size={14}/> Kid or mentor approval required before helper patches apply.</p></section>
      </aside>
    </div></div>
    <PatchModal patch={patch} onClose={()=>setPatch(null)} onApply={apply}/>
    {form && <FieldModal title={form.title} fields={form.fields} initial={form.initial} submitLabel={form.submitLabel} onClose={()=>setForm(null)} onSubmit={submitForm}/>}
  </div>;
}

createRoot(document.getElementById('root')).render(<App/>);


