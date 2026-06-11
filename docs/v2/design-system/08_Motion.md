# 08 · Motion
Motion behaves like good machinery: short, precise, damped — nothing bouncy, nothing decorative-only.

## 1. Tokens
| Token | Value | Use |
|---|---|---|
| `dur-micro` | 120ms | press feedback, chip toggle, checkbox |
| `dur-quick` | 200ms | hover fills, badge pulse, toast in |
| `dur-standard` | 280ms | sheets, accordions, modals, tab slides |
| `dur-deliberate` | 400ms | map camera, stamp, page transitions (app) |
| `ease-out` | cubic-bezier(0.2, 0, 0, 1) | entrances (default) |
| `ease-in-out` | cubic-bezier(0.4, 0, 0.2, 1) | moves/resizes |
| `ease-exit` | cubic-bezier(0.4, 0, 1, 1) | exits (faster than entrances) |
No spring/bounce curves anywhere; overshoot maximum 1.02 scale on pin selection only.

## 2. Choreography Rules
- Enter from the direction of cause (sheet from bottom, drawer from rail side, toast from edge).
- Exits are ~30% faster than entrances; dismissed things leave promptly.
- Stagger lists by 30ms capped at 5 items (rest appear instantly) — dashboards and search results only.
- Never animate: money figures (no count-up — amounts appear set, like print), layout shifts under reading content, map pins en masse (pins fade-in 120ms individually as tiles resolve).
- Status changes: badge crossfades + **one** amber ring-pulse (600ms) — the system's heartbeat; no confetti ever.

## 3. Component Specs
Buttons: A scale 0.98 `dur-micro` · Sheets: translate+fade `dur-standard`, scrim fades in parallel; drag-release snaps with `ease-in-out` 200ms · Modal: fade+scale 0.97→1 · Skeleton shimmer 1.2s linear loop · CountdownPill: tick has **no** animation (mono digits change dry); <30min state change = single pulse · Tabs: 2px indicator slides `dur-quick` · Map camera: `flyTo` ≤400ms, no spin/pitch theatrics; locate-me eases, never teleports.

## 4. Signature Moments (the only 3 "designed" animations)
1. **The Stamp** — receipt/PAID stamp drops in: scale 1.15→1.0 + rotate −2°→−6°, `dur-deliberate`, with a 1px settle; haptic `impactMedium` (app).
2. **Terms lock** — on acceptance, LockedTerms' lock icon closes (2-frame) and the 2px total rule draws left→right 280ms: the contract visibly "sets".
3. **On-Hire pulse** — when a hire goes live, its green badge ring-pulses once and the tab badge increments with a 120ms pop.

## 5. Haptics (app) & Sound
Haptics: selection tick on chip/date select · impactMedium on stamp + payment success · notificationError on failures. No custom sounds (system defaults only); haptics respect system settings.

## 6. Reduced Motion
`prefers-reduced-motion` / RN setting: all transitions become 80ms opacity fades; shimmer → static ink-100; pulses/stamps render final state instantly; map `flyTo` → `jumpTo`. Feature-parity is mandatory — motion is never the only signifier.
