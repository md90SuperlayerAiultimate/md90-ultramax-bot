# md90_superlayerAi — Design Direction

## Three Initial Approaches

### Theme Name: Signal Atelier
Very Brief Intro: A crafted research terminal inspired by editorial data rooms: warm parchment, ink-black panels, and precise electric teal markers. It should feel like an instrument built for people who read markets closely.
Probability: 0.07

### Theme Name: Night Cartography
Very Brief Intro: A dark observatory for mapping market regimes, using graphite surfaces, mineral blue, and restrained amber for decisions. The atmosphere is calm, analytical, and navigational rather than flashy.
Probability: 0.03

### Theme Name: Copper Ledger
Very Brief Intro: A premium risk office with oxblood, bone, and copper accents, combining financial journal craft with modern operational dashboards. It feels serious, tactile, and deliberately human.
Probability: 0.05

## Chosen Approach: Signal Atelier

### Design Movement
Swiss editorial data design fused with contemporary instrument-panel minimalism: asymmetrical composition, sharp typographic hierarchy, and data as the primary visual material.

### Core Principles
1. Every panel must answer one operational question: what is happening, why, what is the risk, and what should happen next.
2. Use quiet surfaces and precise accents rather than decorative gradients or generic dashboard chrome.
3. Make uncertainty visible: confidence, provenance, expiry, and safety mode must be as legible as the signal.
4. Prefer editorial rhythm and offset composition over an evenly tiled admin grid.

### Color Philosophy
The foundation is ink-black and warm graphite for focus. Bone-white typography creates a paper-ledger contrast, while signature teal marks validated data flow and a disciplined amber marks attention without implying profit. Signal green and warning vermilion are reserved for semantic states, never decoration.

### Layout Paradigm
A persistent left rail anchors navigation like a research notebook spine. The main canvas uses a wide lead workspace, offset evidence rail, and lower operational strip. Cards are varied in width and density to create a composed instrument rather than a grid of equal boxes.

### Signature Elements
1. A thin teal “signal trace” line that appears at the edge of key panels.
2. Small uppercase specimen labels with slash-prefixed taxonomy, such as `/ REGIME` and `/ PROVENANCE`.
3. A live “pulse” marker that communicates refresh status without implying live trading is enabled.

### Interaction Philosophy
Interactions should clarify state. Hovering reveals provenance or a micro-explanation; clicking a module shifts the workspace rather than opening generic dialogs. Destructive or live-adjacent controls always expose the current mode and require explicit confirmation. Demo data is visibly labeled.

### Animation
Use 160–220ms ease-out transitions for hover and tab changes. Signal traces may draw in once on entry, while values use a subtle fade-up stagger. No looping glow, no bouncing widgets, and no motion that suggests certainty. Respect reduced-motion preferences.

### Typography System
Use `DM Sans` for body and interface text, paired with `Space Grotesk` for display headings and numeric labels. Headlines are compact and slightly tracked; metadata is 10–11px uppercase with generous letter spacing. Numeric values use tabular figures and a heavier weight.

### Brand Essence
md90_superlayerAi is a transparent market intelligence cockpit for builders and operators who want to test complex signal systems without hiding uncertainty behind polished claims. Personality: exacting, lucid, composed.

### Brand Voice
Headlines sound decisive but never promotional. CTAs describe an observable action, not a promise.
Example lines:
- “Read the stack before you read the signal.”
- “Paper mode is the product, not a disclaimer.”

### Wordmark & Logo
A compact “90” monogram built from two offset signal brackets: the 9 is an open loop for exploration, the 0 is a contained ring for risk control. The mark should be a bold graphic symbol without text, usable as a header badge and favicon.

### Signature Brand Color
Signal Teal: `#22C7B8` — a precise, ownable marker for verified flow and trustworthy instrumentation.

## Style Decisions

- Use a warm off-black canvas with bone text, teal data accents, amber attention states, and vermilion only for risk warnings.
- Treat every data point as demo unless its provenance is shown; no performance claims, reviews, or testimonials.
- Keep the visible product in paper/shadow mode; live is a locked state in the interface.
- The bracket-built 90 monogram is a primary recurring mark in the navigation spine, header utility, and footer rather than a one-time logo treatment.
- The left research-notebook spine has stronger contrast and a persistent teal trace so the shell reads as proprietary navigation, not a generic SaaS sidebar.
- The teal signal trace repeats across panel edges, selected states, chart paths, and provenance markers as one brand system.
