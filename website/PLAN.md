# Plan: HTML Presentation Pivot — GitHub Pages Experience

## Problem
The current PowerPoint/PDF preserves the talk content, but it does **not** hit the bar for polish, theme, motion, or web readability. It feels like a slide export rather than a designed presentation experience.

The goal is to pivot from a deck-first artifact to a **web-native presentation** that can be hosted on GitHub Pages for Harnessa.

## Proposed Approach
Build a presentation microsite in `website/` and treat the web as the primary medium.

Key recommendation:
- **Do not port all 27 slides 1:1.**
- Reuse the existing narrative, data, and citations from the current plan and generated deck.
- Compress the main story into **8-10 high-impact web scenes** with stronger hierarchy, cleaner composition, and purposeful motion.
- Move dense supporting material into an **appendix route/panel** instead of forcing it into the main flow.

Recommended implementation stack:
- Reuse the repo’s existing frontend pattern from `showcase/client`: **React + Vite + Tailwind**
- Add a React motion layer for scene reveals and chart transitions
- Keep the output static and GitHub Pages-friendly
- Use the installed **frontend-design** skill/plugin as guidance for aesthetic direction, typography, motion, and anti-generic frontend choices
- Use **custom CSS variables and hand-authored presentation layout**, not stock Tailwind card styling; Tailwind is utility support, not the visual identity

## Experience Direction
Confirmed format: **web keynote**

That means:
- full-screen or near-full-screen scenes
- keyboard + click + scroll navigation
- URL hash deep links per scene
- strong transitions between acts
- desktop/projector-first layout, still readable on smaller screens

Why this over another PDF export:
- better theme control
- real animation and progressive reveal
- better visual rhythm than dense slide grids
- hostable and shareable without opening presentation software

## Theme Reference
Primary polish reference: **`ridermw/copilot-app`** (`Azure AI Constellation`)

What to copy from it conceptually:
- **screen-share-first** composition built for live presentation
- **mission-control / operator UI** instead of generic startup glassmorphism
- dark shell, luminous accent lines, mono telemetry, uppercase status language
- one dominant kinetic visual area with supporting metrics and narrative chrome
- static deploy with no server runtime dependence

What **not** to copy literally:
- Azure/HPC branding
- GPU cluster visuals
- cloud-specific terminology

We should borrow the **quality bar and presentation grammar**, then translate it into Harnessa’s content.

## Aesthetic Direction
Use the frontend-design guidance plus the `copilot-app` reference to make the site feel **editorial mission-control**, high-contrast, and memorable — not like a literal slide export.

Working direction:
- **Tone:** operator console for AI evaluation / research-lab keynote
- **Typography:** distinctive display font + restrained body font + **mono telemetry font** for metrics, labels, and run data
- **Composition:** asymmetry, overlap, strong negative space, one dominant scene visual plus secondary telemetry/support panels
- **Motion:** one intentional scene-load choreography per act, chart line-draw/count-up animations, topology/flow morphs, subtle state transitions
- **Visual atmosphere:** dark navy/void base, luminous signal lines, restrained grid texture, warm amber alerts, teal/cyan success accents

Explicitly avoid:
- generic SaaS card mosaics
- default startup gradients
- symmetrical “3 feature cards” layouts
- turning every slide/table into a rounded white card on a pale background
- overusing Tailwind-looking pill/card primitives as the main composition

## Theme Translation For Harnessa
Translate the `copilot-app` presentation grammar into Harnessa-specific scenes:

- **Hero:** animated adversarial loop / orchestration network instead of a static title card
- **Architecture:** planner / generator / evaluator displayed like a live system topology
- **Evidence:** benchmark metrics presented as operator telemetry, not spreadsheet-like tables
- **Headline result:** FAIL → PASS as a dramatic state transition, not just side-by-side boxes
- **Landscape:** converging ecosystem shown as a signal map / timeline rather than a list of logos
- **Appendix:** deep-dive data panels that feel inspectable, not buried in backup slides

## Content Strategy
Use the current presentation materials as source content, not final layout:
- `docs/PRESENTATION_PLAN.md`
- `presentation/generate_the_adversarial_architecture.py`
- `presentation/the-adversarial-architecture.pdf`
- `RESULTS.md`

Preserve the corrected factual caveats:
- N=11 sample-size caveat
- duration as proxy for cost
- Python tags leniency caveat
- conjecture labels on model-tiering / round-robin ideas
- demo fallback / no live-demo dependency

## Information Architecture
Collapse the current 22 + 5 deck into a tighter web flow:

1. **Hero / thesis**
   - title, framing statement, why this matters now
2. **The problem**
   - context degradation + self-evaluation failure
3. **The architecture**
   - planner / generator / evaluator / telemetry
4. **The critic**
   - Karpathy anecdote, evaluator rules, anti-sycophancy
5. **The headline evidence**
   - fullstack FAIL → PASS
6. **The scorecard**
   - what trio actually won, where it tied, where caveats matter
7. **The landscape**
   - Anthropic, Claude Code, Symphony, community patterns
8. **The decision framework**
   - when to use this, when not to, model-tiering as industry practice
9. **Closing**
   - quality ceiling / architecture breaks through it
10. **Appendix**
   - experiment matrix, evaluator reliability, criteria, detailed system diagram

## Visual / Motion System
- Dark editorial mission-control theme with brighter data accents
- Fewer generic cards; use composition-first layouts
- Animated number reveals, line-draw charts, scene transitions, progressive callouts, and state-based view changes
- Persistent operator chrome: top bar / scene rail / compact status indicators
- Reduced-motion support
- Accessibility baseline: strong contrast, keyboard nav, readable type scale
- Desktop/projector-first target with an explicit small-screen fallback state

## Technical Plan
### App structure
- `website/`
  - `package.json`
  - `vite.config.*`
  - `src/main.*`
  - `src/App.*`
  - `src/content/*`
  - `src/components/*`
  - `src/styles/*`

### Core implementation pieces
- structured content/data file instead of hard-coded slide text
- reusable scene shell + navigation
- typography/theme tokens via CSS variables
- presentation chrome inspired by `copilot-app`: top status band, side metrics/facts rail, command/shortcut affordances where appropriate
- custom SVG/HTML data visualizations for:
  - headline result
  - benchmark scorecard
  - iteration chart
  - landscape timeline/network
- appendix route or expandable panel system

### Deployment
- GitHub Pages workflow at `.github/workflows/presentation-pages.yml`
- Vite base path configured for repo hosting
- local preview command documented in the site package

## Key Design Shift From The Current Deck
The new implementation should feel like:
- a **designed web presentation**
- not a literal slide translation
- not a PDF preview in HTML clothing
- closer to a **mission-control keynote demo** than a traditional slide deck

Success means:
- stronger visual hierarchy
- fewer simultaneous boxes/tables
- more purposeful motion
- easier reading at a glance
- better pacing when presented live
- a distinctive visual identity that does **not** read as generic AI-generated frontend work
- polish at the level of `copilot-app`: presentable on a shared screen without apology

## Todos
- `define-web-experience` — Lock the web presentation mode, scene map, and visual direction
- `scaffold-presentation-site` — Create the React/Vite/Tailwind presentation app in `website/`
- `build-core-scenes` — Implement the main 8-10 presentation scenes and reusable layout/navigation components
- `build-data-viz-and-appendix` — Implement charts, appendix content, citations, and supporting deep-dive views
- `add-pages-deploy` — Add GitHub Pages deployment workflow and base-path-safe build configuration
- `qa-web-presentation` — Run browser QA for readability, motion, responsiveness, and presentation flow

## Dependency Notes
- `build-core-scenes` depends on `define-web-experience` and `scaffold-presentation-site`
- `build-data-viz-and-appendix` depends on `scaffold-presentation-site`
- `add-pages-deploy` depends on `scaffold-presentation-site`
- `qa-web-presentation` depends on `build-core-scenes`, `build-data-viz-and-appendix`, and `add-pages-deploy`

## Notes
- The existing PPTX/PDF remain useful as **content reference and archival artifacts**, but they are no longer the target deliverable.
- The current `presentation/preview/` assets can be used for content cross-checking during implementation.
- If the preferred format changes from “web keynote” to “scrollytelling article,” the scene architecture and motion plan should be updated before implementation starts.
