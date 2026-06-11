# 05 · Core Components
Every component lists: anatomy → variants/sizes → state matrix → platform notes. States abbreviated: D default · H hover · F focus · A active/pressed · L loading · X disabled · E error.

## 1. Buttons
**Anatomy:** container r-sm · label Inter 500 · optional leading icon 18px · min-width 88px.
**Sizes:** `lg` 48px (app primary, portal heroes) · `md` 40px (portal default) · `sm` 32px (table inline).
**Variants × states:**
- **Primary** (amber-500/ink-900): H amber-400 · F focus ring · A amber-600 + scale 0.98 · L spinner replaces label, width locked, `aria-busy` · X ink-100/ink-400.
- **Secondary** (outline ink-300): H ink-50 fill · A ink-100.
- **Destructive** (red-600/paper-0): requires confirm pattern (07 §6) for irreversible actions.
- **Ghost** (ink-700): toolbar/table actions.
**Rules:** one primary per view region · labels are verbs · icon-only buttons need `aria-label` + 40px min target · full-width permitted only in app bottom action zone.

## 2. Inputs & Forms
**Text field:** 48px (app)/40px (portal), r-sm, 1px `border/default`; label always above (Inter 500 caption, ink-700); helper/error text 13px below; placeholder = example never instruction.
States: F amber focus ring · E `border/error` + red-700 message + icon · X ink-50 fill.
**Specializations:** money input (₦ prefix slot, Plex Mono, right-aligned, auto-grouping) · phone (+234 prefix, Nigerian format mask) · OTP (6 mono cells 48×56, auto-advance, paste-aware) · search (pill r-full on map, rect elsewhere) · textarea (min 3 rows, char counter when limit) · password (visibility toggle, strength meter = 3-segment bar amber/amber/green).
**Select/Combobox:** portal = shadcn popover style; app = bottom-sheet picker (never native wheel for >6 options). Class picker always shows class dot + glyph.
**Date range picker:** dual-month portal / single-month sheet app; unavailable dates ink-300 strikethrough; held dates amber-100 fill (legend included); selected range amber-500 endpoints + amber-100 span; today = ink-900 ring.
**Form pattern:** sections separated s-8 with h3; validation on blur + on submit (scroll-to-first-error, focus it, announce via live region); multi-step forms use Stepper (§7) with per-step save (drafts).

## 3. Selection Controls
Checkbox 20px r-2 (amber-500 checked, indeterminate dash) · radio 20px · switch 36×20 (amber-500 on; used for binary settings only, never bulk actions) · **Chips**: filter chips (r-full, ink outline → amber-100/amber-900 selected, count suffix), class chips (class dot + label, wash colors per 02 §3), input chips (removable ×).

## 4. Feedback
- **Toast** (app top / portal bottom-right): 4s auto-dismiss, max 2 stacked; success ink-900 surface + green icon · error stays until dismissed.
- **Banner** (inline, full-width wash): info blue-50 · warning amber-50 · danger red-50; with action link. Used for: payment countdown, verification prompts, offline notice.
- **Skeleton**: ink-100 blocks, 1.2s shimmer (ink-100→paper-50); shapes mirror real layout (card, table-row, map-callout variants). No spinners for content loads — spinners only inside buttons and map tile corner.
- **Progress**: linear 4px amber on ink-100 (uploads); circular only in button-loading.
- **Badge/Count**: r-full min 18px, amber-500/ink-900 (unread), red-600/paper-0 (urgent: payment expiring).

## 5. Navigation
- **Portal nav rail:** ink-900; items Inter 500 14px ink-300 → paper-0 active with 3px amber left indicator; sections: Dashboard, Assets, Hires, Calendar, Messages (badge), Storefront, Settings; collapse toggle bottom; wordmark plate top.
- **App tab bar:** 5 tabs (Map, Search, Hires, Messages, Profile), 56pt, icons 24px + 11px labels — exception to 14px floor, mitigated by icons + AA contrast; active = amber-600 icon + ink-900 label; unread dot on Messages.
- **Breadcrumbs (portal):** caption ink-500, chevron separators, current page ink-900.
- **Tabs (in-page):** underline style, 2px ink-900 active indicator (not amber — reserves amber for actions); badge counts allowed.
- **Pagination:** portal cursor-based "Load more" button + count caption; app infinite scroll + end-of-list marker (hazard stripe 24px, 40% opacity).

## 6. Overlays
- **Modal (portal):** max-w 560px, r-lg, e-2; header h3 + close; footer right-aligned buttons (primary rightmost); never nested.
- **Bottom sheet (app):** r-lg top corners, drag handle 32×4 ink-300, snap points per 04 §3; sheet header optional; content scrolls within sheet at full snap.
- **Popover/Dropdown:** e-1, r-md, min-width trigger; menu rows 40px with icons.
- **Tooltip (portal only):** ink-900/paper-0, caption, 400ms delay; never holds essential info.

## 7. Structure
- **Card:** paper-0, 1px border, r-md; clickable cards get H border-strong + cursor; entire card is the tap target (app).
- **DataTable (portal):** sticky header (paper-50, overline labels), 0.5px row rules, zebra off by default (on for >20 rows), sort arrows, bulk-select column, row hover ink-50, right-aligned mono numerics, sticky first column on overflow, density-aware (04 §4). Empty/loading/error states per 07.
- **Stepper:** portal horizontal (numbered 24px circles, amber done/current, ink-200 upcoming, labels caption) · app vertical-compressed ("Step 2 of 6" + progress bar 4px amber).
- **Accordion:** chevron right-rotates; h3 trigger; one-open-at-a-time only in forms.
- **Avatar:** r-full people, **r-md (squircle) businesses** — shape = entity type; initials fallback ink-900/amber-500 text; sizes 24/32/40/56.
- **Divider:** per 04 §6. **SectionHeader:** h2/h3 + optional action link right.
