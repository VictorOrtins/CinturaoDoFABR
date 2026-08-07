# Design Reference

Why this exists: the original frontend (sidebar nav, white cards, a native
`<select>` for switching charts, plain sans body copy) was functionally solid but
read as a generic admin/data-tool UI — "a Streamlit app without Streamlit." The
user has pointed at two real sites as the design target: [fabrnetwork.com.br](https://fabrnetwork.com.br/)
(a Brazilian American-football league site — closest in *subject matter*) and
[coparadiso.com](https://www.coparadiso.com/) (a Melbourne coworking space — closest
in *personality and craft*). Neither should be copied outright; both are studied here
for the underlying moves, which get adapted to this app's own subject (a single running
joke: American football in Brazil, presented like a boxing "belt lineage") and its
own brand tokens (Anton/Manrope/IBM Plex Mono type system, the "Arena" palette in
`frontend/src/index.css` — see CLAUDE.MD's Color Scheme section for the current
hex values and how it was chosen). Nav moved from a sidebar to a topbar in the
palette-decision session; treat mentions of "sidebar" below as describing the
*prior* state that motivated a change, not the current layout.

**When to read this**: before touching frontend layout, typography, or adding a new
page/section. It's a reference for direction, not a locked spec — if a recommendation
here conflicts with something the user says in a session, the session wins; update this
file to match afterward.

---

## What defines fabrnetwork.com.br

1. **Every team gets a full-bleed hero banner colored with that team's own brand
   color**, not a neutral card. The team's identity *is* the page background for that
   view, not a small logo chip in the corner. (This app already has `team.primary_color`
   in the data model — it's currently only used to color a bar in a chart, never to
   theme a section.)
2. **Heavy, condensed, italic display type for every headline** ("ESCOLHA SEU TIME",
   "CUIABÁ ARSENAL", "TEMPORADA REGULAR") — all-caps, slanted, sports-broadcast energy.
   Body/label text stays small and upright by contrast, so the display type reads as
   loud on purpose, not just "big."
3. **Data presented as bio cards, not tables**, for anything narrative (foundation
   date, city, stadium, Instagram handle): a label row (small caps, muted) directly
   above a bold value row, separated by hairline dividers — closer to a spec sheet than
   a spreadsheet. Tables are reserved for genuinely tabular data (standings), and even
   there, team badges sit inline in the row, not in a separate icon column.
4. **Segmented tab controls in two different visual weights depending on hierarchy**:
   top-level tabs (BIO / JOGADORES) are solid pill buttons; sub-tabs within a tab
   (ATAQUE / DEFESA / SPECIAL) are plain text with an underline on the active item.
   The nav sidebar itself is an accordion (RANKINGS expands to reveal JOGADORES/TIMES)
   rather than every route being a flat top-level link.
5. **Status and category chips**: colored pill badges for match status ("Finalizado" in
   green), conference/region tags ("Conferência Sudeste" as a red chip), rounded
   black CTA pills ("SAIBA COMO FOI"). Chips carry meaning through shape + color, not
   just text.
6. **A branded loading state** — the spinner is the club/brand logo inside a rotating
   colored ring, not a generic spinner. Small detail, but it's one of the few moments
   users spend >1s looking at nothing else.
7. **Split-panel layouts for schedule + standings**: the standings table and the
   round-by-round results feed sit side by side as two independent scrollable panels,
   not stacked full-width sections — more like a sports-desk dashboard than a single
   linear document.

## What defines coparadiso.com

1. **One illustrated motif repeated everywhere as the site's signature**: a hand-drawn
   line-art building icon (with palm trees) appears in the nav, the hero, and the
   footer. It's simple enough to render small (nav icon) and large (hero), and it's the
   thing a visitor remembers, more than any photo.
2. **Deliberately mismatched type pairing carries the personality**: a hand-lettered
   script for the wordmark and section sub-headers, a serif display face for big
   headline statements, and a monospace face for ordinary body copy. Three registers,
   used consistently by role (never randomly) — the contrast between "formal serif
   headline" and "typewriter body copy" is doing a lot of the "we don't take ourselves
   too seriously" work.
3. **A warm, saturated, retro-specific palette** (mustard yellow, burnt orange, deep
   green, cream, near-black) applied as one consistent system across photo overlays,
   buttons, and badges — not the generic "brand blue + white card" look most sites
   default to.
4. **Full-bleed photography/video as section backgrounds**, with display type
   overlaid directly on top (not confined to a text column beside the image). The hero
   is a looping video with its own mute toggle, which signals "real place, real
   texture" instead of a stock photo.
5. **Novelty chrome that isn't load-bearing**: a horizontally scrolling marquee ticker
   band right under the nav, and rotated circular "sticker" badges (like
   "Procrastinate in style — guaranteed") dropped on top of photo grids at a slight
   angle. Neither carries critical information; both add texture and make the page feel
   handmade rather than templated.
6. **Real, candid photography of the actual space and actual people**, not stock
   imagery or icons, used generously — pool table, hot desks, people mid-conversation.
7. **Every section pairs a short, voice-y headline with a longer plainspoken
   explanation directly under it** ("Your cheeky inner-north coworking oasis" / "A
   coworking space with real personality, real community..."). The copywriting voice is
   as much a design decision as the visuals.

## Why the current app still reads as "Streamlit"

- Every page is the same shape: a heading, a paragraph, a plain white/dark `--surface`
  card, done. Streamlit's whole layout model *is* "stack of default widgets in a
  column" — the app currently matches that shape even though it's hand-built.
- The stats page picker is a native `<select>`, functionally identical to
  `st.selectbox`. Functionally fine; visually it's the single most recognizable
  "generic data tool" widget there is.
- No page treats a **team** as a themed subject the way fabrnetwork does — team pages
  don't exist yet at all, and nothing on Games/Stats picks up a team's own color as
  anything but a chart-bar fill.
- Body copy, headings, labels, and chart text all use the same two fonts
  (Anton/Manrope) at the same few weights — there's no second "voice" (a script,
  serif, or mono) doing contrast work the way CoParadiso's three-typeface system does.
- No illustration, motif, texture, or motion exists anywhere. Every visual element is
  either plain text or a recharts SVG. Nothing is memorable independent of the data.
- Loading and empty states are plain "Carregando..." text — functional, but exactly
  the generic default a data-tool framework would render for free.

## Directions worth trying here

Ordered roughly by leverage (biggest visual shift for the effort), not by priority —
pick based on what a session is actually working on. Items marked ✅ were implemented
in the first redesign pass; see the file/component pointers for where to extend them
rather than re-inventing.

1. ✅ **Give teams a themed page** — `frontend/src/pages/TeamsPage.tsx` (grid, `/times`)
   and `TeamDetailPage.tsx` (`/times/:id`): hero background is the team's own
   `primary_color`, logo sits on a white "plate" behind it (needed — several team
   logos are themselves the same hue as their brand color and vanish without one; see
   `getContrastingTextColor` in `frontend/src/utils/color.ts` for the text-color pick),
   bio-card `<dl>` rows below with mono labels. `GamesTable` and `ChampionCard` now
   link team names into these pages.
2. **Add one more typeface register** for contrast — *done differently than proposed*:
   rather than a script/serif face, `IBM Plex Mono` (already loaded in `index.html`,
   previously unused — see `--font-mono` in `frontend/src/index.css`) was pressed into
   service as the "spec sheet" voice: bio-card labels, chip text, loading-state
   captions. A script/serif face for the wordmark itself is still open if a stronger
   personality hit is wanted later — the discipline (assign by role, don't add a 4th)
   still applies.
3. ✅ **Replace the Stats page's native `<select>`** — `StatsPage.css`'s
   `.stats-page__select`: `appearance: none` + a custom SVG chevron + pill shape, and
   the 12 stats are now grouped into `<optgroup>`s (Linha do tempo / Rankings de times
   / Tendências) instead of one flat list. Still a native `<select>` under the hood
   (deliberate — 12 options in a custom listbox risks a11y regressions for a cosmetic
   win); a true custom combobox is still open if wanted.
4. ✅ **Introduce a repeatable illustrated motif** — `frontend/src/components/BeltIcon.tsx`,
   a line-art championship belt (strap + plate + star), used in the topbar wordmark
   and inside `LoadingBelt.tsx`. Not yet used in empty states — a natural next step.
5. ✅ **Chips/badges for status and category** — `.chip` utility class in `index.css`,
   currently applied to `GamesTable`'s tournament column. Match status and "current
   champion" badges are still open (there's no per-game status field yet — every seeded
   game is already `Finalizado`, so this matters more once/if future games get added
   before they're played).
6. ✅ **A branded loading state** — `frontend/src/components/LoadingBelt.tsx`
   (`BeltIcon` inside a rotating ring, counter-rotated so the icon itself stays upright,
   respects `prefers-reduced-motion`). Wired into Home/Stats/Teams/TeamDetail. `GamesPage`
   still has no loading state at all (games start as `[]` and fill in silently) — worth
   fixing together if that page gets touched again.
7. **Real photography or texture, if/when available** — still open; depends on having
   usable source images.
8. **Split-panel dashboard layouts** — still open.
9. ✅ **Sidebar → topbar, and a repalette** — `frontend/src/components/Topbar.tsx`/
   `.css` replaced the vertical sidebar with a full-width sticky top bar (brand left,
   pill-style nav, theme toggle right); three candidate palettes were screenshotted
   live and compared (a refined version of the original navy/blue/purple set, a
   turf-green "Campo" direction, and "Arena" — near-black fight-night-poster mood),
   and Arena was picked. See CLAUDE.MD's Color Scheme section for the resulting hex
   values and the note on chart components needing hardcoded hex duplicates instead
   of `var(...)`.

None of these require a new dependency or framework change — they're CSS, layout, and
a small amount of new illustration/type, on top of the existing React + CSS-custom-
property setup already in place.
