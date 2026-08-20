# Design Reference

Why this exists: the original frontend (sidebar nav, white cards, a native
`<select>` for switching charts, plain sans body copy) was functionally solid but
read as a generic admin/data-tool UI — "a Streamlit app without Streamlit." The
user has pointed at real sites as the design target: [fabrnetwork.com.br](https://fabrnetwork.com.br/)
(a Brazilian American-football league site — closest in *subject matter*),
[coparadiso.com](https://www.coparadiso.com/) (a Melbourne coworking space — closest
in *personality and craft*), and — added in a later session, once the first redesign
pass still felt "off" — [eatrocketfuel](https://webflow.com/made-in-webflow/website/eatrocketfuel)
(a Webflow showcase site, closest in *the 8-bit/pixel-art energy the user wants next*).
None should be copied outright; all are studied here for the underlying moves, which get
adapted to this app's own subject (a single running joke: American football in Brazil,
presented like a boxing "belt lineage" — itself already game-ladder shaped) and its own
brand tokens (Anton/Manrope/IBM Plex Mono type system, the "Arena" palette in
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

## What defines eatrocketfuel (Webflow showcase) — the 8-bit reference

First checked 2026-08-19 via a text-only fetch, then **actually browsed live** at
eatrocketfuel.webflow.io the same session once the Chrome extension reconnected — the
live-browse corrected several assumptions the text-only pass got wrong, so treat this
version as authoritative. It is *not* a full pixel-grid site the way NES/SNES game art
is; it's a **comic/pop-art retro system with pixel-art used as an accent**, not the
whole typographic or illustration language:

1. **Bold, rounded, all-caps comic-bubble headline type with a hard (never blurred)
   black offset duplicate behind it** — "REFUEL YOUR SHIP," "CHECK OUT THE ROCKET
   MENU." This is the dominant voice on the page, and it is a chunky rounded sans, not
   a monospace pixel font. The genuinely pixel-grid elements (see #3-4) are accents on
   top of this, not the headline system itself.
2. **A halftone/Ben-Day dot texture as the default fill for solid color panels** — the
   purple hero, the green promo block, and the footer are all one saturated flat hue
   with a faint dot-pattern overlay (not a gradient, not a photo), and the same dot
   texture is reused as *dithered shading* on illustrated spheres (a halftone moon).
   Cheap to reproduce (a repeating SVG/CSS pattern) and needs no photography or new
   illustration — probably the single highest-value/lowest-effort item here.
3. **A jagged, pixel-stepped dashed border, reserved specifically for speech-bubble/
   callout shapes** ("ORDER HERE," "TIME 2 REFUEL?" — copy cycles inside on a timer).
   This is the one element on the page that is unambiguously "8-bit UI": a genuinely
   stepped/pixelated outline instead of a smooth curve, used narrowly as a callout
   device rather than applied to every box.
4. **Small chunky pixel-cross "sparkle" icons** scattered through the space scene as
   stars/twinkles, built on a visible pixel grid — and the small prop icons (burger,
   fries, drink, condiment bottles) read noticeably more pixelated/blocky than the
   hero astronaut character, which is smooth flat vector line art with a black
   outline. **The pixel treatment is reserved for small accessory icons and borders,
   not hero illustrations** — the astronaut is drawn the same clean way coparadiso or
   this app's own `BeltIcon` line art already is.
5. **Real product photography, still present** — burger, onion rings, fries, and
   apparel shots are actual photos, not illustrations. What makes them fit the system
   is the treatment wrapped around them: a thick black outline, a hard offset shadow,
   a comic "starburst" badge ("ORDER NOW," like a comic-book POW shape), and a wavy
   black-outline divider between the photo and the price label below it. Photography
   isn't excluded from an 8-bit/retro system — it just needs the same hard-outline
   treatment as everything else to fit.
6. **Hard, un-blurred black borders and offset shadows on every card, button, and
   pill** — confirms the button/card direction already listed below (item 10):
   square-ish corners, a flat solid-color offset shadow instead of a blurred one, thick
   black stroke.
7. **Saturated, single-hue full-bleed section blocks** (violet, hot pink, mint green)
   rather than gradients — each section changes background color wholesale, high
   contrast against black outlines and white text, no soft blending between sections.
8. **A rotating circular sticker badge** (logo + tagline, "a space cadet is currently
   refueling") in the footer — the same device DESIGN.md already logs from coparadiso's
   circular "sticker" motif; worth doing once regardless of which reference gets credit
   for it.

I did not find a literal scrolling marquee/ticker band on the live page despite it
being one of the site's own tags — likely refers to the swirling background motion or
a state I scrolled past. Don't treat "marquee ticker" as confirmed-present the way the
items above are; the coparadiso reference (still open, item 11 below) is the sturdier
basis for that specific idea.

**A note on workos.com/launch-week/summer-2026**: checked as the user's second link,
but it has drifted since it was first suggested — it now reads as a curated *cinematic
80s/90s nostalgia* piece (CRT television, VHS tapes, Blockbuster branding, a TRON
poster, a DeLorean), not pixel art. Worth knowing this reference exists in case a
future session wants that different flavor of retro, but per the user's own steer,
**eatrocketfuel is the one to actually mine for 8-bit moves** — treat WorkOS as
checked-and-parked, not a current input.

### Translating "8-bit" for this app specifically

The existing "Arena" palette and Anton/Manrope/IBM Plex Mono system don't need to be
replaced to read as 8-bit — most of the genre's punch comes from *how shapes, edges,
and fills are drawn*, not from new hex values or a wholesale pixel-font swap:

- **Hard edges over soft ones**: today's buttons/cards use `border-radius` +
  blurred `box-shadow`. An 8-bit pass means square corners and *stepped, solid-offset*
  shadows (a flat 2-4px hard offset, no blur) — the classic NES button bezel — with the
  shadow removed and the element nudged down on `:active` to read as "pressed." Most
  directly confirmed by the reference (its #6) — the highest-confidence item here.
- **A halftone dot-texture fill utility**, reused as a background on existing
  `--surface`/hero blocks in the current Arena palette (amber/crimson/near-black/
  parchment, not new colors) — a repeating dot pattern rather than a flat fill or a
  gradient. Reachable without new illustration or photography, confirmed by the
  reference's #2 as its actual highest-leverage/lowest-effort move.
- **A pixel-stepped dashed border, scoped to callout/speech-bubble-shaped moments
  only** — a "current champion" banner, an empty-state box, an assistant chat bubble
  in `AssistantPage.tsx` — not applied globally to every card. Mirrors the reference's
  #3 exactly: the one clearly-pixel element on their page is scoped this narrowly too.
- **Pixel treatment belongs on small accessory icons/borders, not hero illustrations**
  — per the reference's #4, `BeltIcon.tsx`'s line art and any astronaut-equivalent
  hero graphic should probably stay clean vector, while small decorative marks (stars,
  chip corner accents, a "sparkle" on the champion badge) are where a visible pixel
  grid actually belongs. This walks back an earlier draft of this section that
  proposed sprite-ifying `BeltIcon` itself — do the small accents first and see if a
  full sprite redraw is even still wanted.
- **One pixel typeface, used as narrowly as coparadiso's script face** — not a
  replacement for Anton or Manrope, and not what carries the "8-bit" read on the
  reference site either (its headlines are a bold rounded sans, not a pixel font). A
  genuine pixel face (e.g. "Press Start 2P") is a secondary accent at most: score
  numerals, a win count, a numeric chip badge. This would be a 4th type register on
  top of the existing three — the DESIGN.md discipline from the coparadiso section
  ("assign by role, don't add a 4th casually") still applies.
- **The belt-lineage concept is already game-shaped** — "who currently holds the belt"
  is structurally a game ladder/leaderboard, which is the underlying reason this
  direction fits the app's actual subject rather than being a generic reskin.
- **A scoreboard/ticker band** under the topbar is still worth trying (carried over
  from the coparadiso marquee idea, item 8) but is no longer treated as confirmed by
  eatrocketfuel specifically — see the caveat above.
- **Real photography, if/when available, doesn't need to be avoided** — wrap it in the
  same hard-outline + offset-shadow + comic-badge system used everywhere else (the
  reference's #5) rather than assuming an illustration-only approach is required.

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
   respects `prefers-reduced-motion`). Wired into Home/Stats/Teams/TeamDetail/Assistente
   (CDF-3's "Pensando..." state while the LLM call is in flight). `GamesPage`
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

10. **Hard-edge, hard-shadow buttons and cards** — swap `button`'s current
    `border-radius: 0.375rem` + soft styling (`index.css`) for square corners and a
    flat, un-blurred offset shadow that collapses on `:active` (press feedback). Same
    idea extends to `.chip` and card surfaces (`--surface` blocks across the pages).
    Highest-confidence item — directly confirmed live on eatrocketfuel (every card/
    button/pill on the site works this way).
11. **A halftone dot-texture fill utility** — a repeating dot pattern (SVG or CSS
    `radial-gradient` tile) applied to existing `--surface`/hero blocks, in the current
    Arena palette, no new colors needed. Confirmed live as eatrocketfuel's actual
    highest-leverage/lowest-effort move (it's their default panel fill, not a special
    case) and it needs no new illustration or photography — probably the single
    cheapest win on this list.
12. **A pixel-stepped dashed border, scoped to callout-shaped moments only** — a
    "current champion" banner, an empty-state box, an `AssistantPage.tsx` chat bubble.
    Confirmed live as the one genuinely pixel-grid element on eatrocketfuel, and it's
    used narrowly there too (speech bubbles only, not every card) — don't apply this
    globally.
13. **Small pixel-grid accent icons** (a sparkle/star mark on a champion badge, a chip
    corner accent) rather than a full sprite redraw of `BeltIcon.tsx`/`LoadingBelt.tsx`
    — confirmed live that eatrocketfuel keeps its hero character (the astronaut) as
    clean vector line art and reserves the visible pixel grid for small decorative
    props/stars instead. Do this before considering a full `BeltIcon` sprite redraw;
    the smooth line art may already be the right call once these small accents exist
    elsewhere on the page.
14. **A scoreboard/ticker band under `Topbar.tsx`** — the coparadiso marquee idea
    (item 8): recent results scrolling in mono/pixel type on a solid dark strip. Still
    worth trying, but note it's carried over from coparadiso, not something actually
    confirmed present on eatrocketfuel's live page despite being one of its tags.
15. **One pixel typeface (e.g. "Press Start 2P"), scoped narrowly** — score numerals,
    win counts, numeric chip badges only. Not for prose, not a replacement for
    Anton/Manrope/IBM Plex Mono, and — confirmed live — not even what carries the
    "8-bit" read on the reference site itself (its headlines are a bold rounded sans
    with a hard offset shadow, not a pixel font; see item 10). Treat as a minor accent
    on top of items 10-12, not the main event.
16. **Wrap real photography (if/when available) in the same hard-outline system**,
    rather than assuming illustration/parallax is the only photo-free path — confirmed
    live that eatrocketfuel uses real product photos for menu items, made to fit by
    adding a thick black outline, a hard offset shadow, and a comic "starburst" badge
    on top, the same treatment as every illustrated element. A restrained parallax
    starfield for hero sections (low-opacity, theme-aware, `prefers-reduced-motion`-
    respecting) is still a reasonable *separate* idea, just not framed as photography's
    substitute.

None of these require a new dependency or framework change — they're CSS, layout, and
a small amount of new illustration/type, on top of the existing React + CSS-custom-
property setup already in place. Items 10-16 are new (2026-08-19; 11-13 and the caveats
on 14-16 added after live-browsing the reference, correcting an earlier text-only-fetch
draft) — pick them up individually rather than attempted as one big pass, same rule the
✅ items above already followed. 10-12 are now implemented (hard-edge/hard-shadow
buttons and cards spread across essentially every card/input surface, halftone applied
to the TeamDetailPage hero and ChampionCard, dashed callout on ChampionCard); 13-16
remain open.

17. ✅ **Saturate the Arena palette's accent/secondary hues for the 8-bit read** —
    the original Arena palette (item 9) was a *muted* fight-poster mood (dusty steel
    blue, brick red); real 8-bit/arcade palettes are flat and highly saturated. Bumped
    `--color-accent-yellow` (#f0a202 → #ffb703), `--color-blue-primary`
    (#5b7a99 → #1a54c4 light / #7fa0c2 → #5f95ff dark), and `--color-purple-secondary`
    (#b3261e → #e2231a light / #e0574c → #f23c2c dark) toward flat, cartridge-vivid
    hues, checked against WCAG contrast on their actual light/dark backgrounds so the
    saturation bump didn't cost readability. Left ink, gray text, and the parchment/
    surface tones untouched — they already read as high-contrast "cabinet" black-on-
    cream and didn't need to move. See CLAUDE.MD's Color Scheme section for the
    current hex values and the note on where they're duplicated for SVG chart props.
