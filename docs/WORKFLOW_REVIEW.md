# User Workflow Review

A walkthrough review of the SNES Studio editor experience, based on driving the
app end to end. Scope: is the workflow intuitive, and is the LLM integration
correct?

## The core loop (works well)

Start → pick a **Template** (gallery) or the default game → edit on a single
screen (scenes left, canvas centre, inspector right) → **Build background**,
paint tiles, place actors/triggers → link **scene jumps** → optionally ask the
**Coding Helper** for a reviewed patch → **Preview ROM** / **Build ROM**.

This mirrors GB Studio's mental model, so anyone who has seen GB Studio is
immediately oriented. The left→centre→right flow is correct.

## Strengths

- **Human-in-the-loop patches.** Every AI/helper change is shown as a reviewable
  patch before it touches the project. This is consistent and trustworthy — the
  best part of the product.
- **Consistent "import from image" pattern.** Sprites and scenes use the *same*
  flow (image/AI art → quantize → preview → apply), with links to GameTorch /
  Pixie / Layer.ai / AI Pixel Kit. Learn it once, use it everywhere.
- **One-click scene jumps.** Selecting a trigger or actor and picking "go to
  scene" builds and links the `change_scene` chain for you; the Scenes panel
  shows outgoing jumps as flow chips. This removes the most tedious part of
  hand-building event chains.
- **Templates** give a professional starting point instead of a blank canvas.

## Friction points & recommendations

1. **Two entry points per asset** ("Add sprite" vs "Import from image"; "Add
   scene" vs "Build background"). Fine, but a single "+" with a menu
   (Blank / From image / Preset) would reduce decisions.
2. **Trigger zones obscure the scene.** Trigger/collision overlays are large
   translucent fills; on a full painted background they tint the scene. Consider
   outline-only rendering with a fill only on hover/select, or a layer toggle.
3. **Scene list vs project list.** The left rail can show entries that read like
   separate projects/demos mixed with the current game's scenes. Label the
   sections clearly ("Scenes in this game") so it's unambiguous what you're
   editing.
4. **First-run orientation.** The Templates button is discoverable but a new user
   lands mid-project. A one-time "Start from a template or keep this demo?"
   nudge would orient first-timers.
5. **Build vs Preview clarity.** "Preview ROM" (built-in / load file) and "Build
   ROM" (needs local PVSnesLib) should be visually distinct so nobody expects a
   full ROM build in the browser.
6. **Inline "what happens".** Showing each trigger/actor's effect inline
   ("→ Go to Dungeon Hall", "says: …") would let users understand a scene
   without opening the event editor.

## LLM integration review

**Before:** the "Coding Helper" was **not an LLM**. In the browser it returned a
single hardcoded patch; the backend `agent.py` did keyword matching on the
prompt ("robot"/"boss"). Calling it "AI" was inaccurate.

**Now (corrected):** the helper calls the **Anthropic Messages API** directly
with the user's own key:

- Key is entered in **AI settings** and stored in `localStorage` (this browser
  only); a status pill shows **AI on / offline**.
- A **cached system prompt** constrains the model to the four patch ops the
  apply pipeline supports (`add_scene`, `add_actor`, `add_event_chain`,
  `add_event_step`) and the valid step/trigger types, with the live project
  summary passed as context.
- Output is parsed as a patch and routed through the **same human-review modal**
  before applying — the safety model is preserved.
- If no key is set, it falls back to a deterministic, clearly-labelled patch.

This is a correct, honest integration. Remaining hardening worth doing:

- **Enforce id uniqueness client-side** before applying an AI patch (today it
  relies on the prompt telling the model to invent new ids). Reject/auto-rename
  collisions so a bad generation can't overwrite existing content.
- **Classroom/hosted mode:** browser-side keys are fine for a single user but
  shouldn't be shared. For multi-user, proxy the call through the FastAPI
  backend so the key lives server-side.
- **Provider choice:** optionally support OpenAI as well; the patch schema is
  provider-neutral.
- **Validate ops:** drop any op/type outside the allow-list before showing the
  patch, so malformed generations fail safe.

## Verdict

The workflow is intuitive and internally consistent, and the LLM integration is
now real and safe. The biggest UX wins left are clarifying the left-rail
scene/project distinction, making zone overlays less visually heavy, and a
first-run template nudge.
