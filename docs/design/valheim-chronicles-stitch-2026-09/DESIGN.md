---
name: Valheim Chronicler Archive
colors:
  surface: '#0e141c'
  surface-dim: '#0e141c'
  surface-bright: '#343a42'
  surface-container-lowest: '#090f16'
  surface-container-low: '#161c24'
  surface-container: '#1a2028'
  surface-container-high: '#242a33'
  surface-container-highest: '#2f353e'
  on-surface: '#dde3ee'
  on-surface-variant: '#d8c3ad'
  inverse-surface: '#dde3ee'
  inverse-on-surface: '#2b3139'
  outline: '#a08e7a'
  outline-variant: '#534434'
  surface-tint: '#ffb95f'
  primary: '#ffc174'
  on-primary: '#472a00'
  primary-container: '#f59e0b'
  on-primary-container: '#613b00'
  inverse-primary: '#855300'
  secondary: '#ffb77d'
  on-secondary: '#4d2600'
  secondary-container: '#d97707'
  on-secondary-container: '#432100'
  tertiary: '#ffc32d'
  on-tertiary: '#402d00'
  tertiary-container: '#e0a800'
  on-tertiary-container: '#584000'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffddb8'
  primary-fixed-dim: '#ffb95f'
  on-primary-fixed: '#2a1700'
  on-primary-fixed-variant: '#653e00'
  secondary-fixed: '#ffdcc3'
  secondary-fixed-dim: '#ffb77d'
  on-secondary-fixed: '#2f1500'
  on-secondary-fixed-variant: '#6e3900'
  tertiary-fixed: '#ffdf9f'
  tertiary-fixed-dim: '#f9bd22'
  on-tertiary-fixed: '#261a00'
  on-tertiary-fixed-variant: '#5c4300'
  background: '#0e141c'
  on-background: '#dde3ee'
  surface-variant: '#2f353e'
typography:
  display-hero:
    fontFamily: Bodoni Moda
    fontSize: 56px
    fontWeight: '700'
    lineHeight: 64px
    letterSpacing: 0.04em
  display-hero-mobile:
    fontFamily: Bodoni Moda
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: 0.02em
  headline-lg:
    fontFamily: Bodoni Moda
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: 0.02em
  headline-lg-mobile:
    fontFamily: Bodoni Moda
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: 0.01em
  headline-md:
    fontFamily: Bodoni Moda
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: 0.01em
  headline-sm:
    fontFamily: Bodoni Moda
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  label-runic:
    fontFamily: Bodoni Moda
    fontSize: 13px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.14em
  label-mono-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.04em
  label-mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  space-2xs: 0.25rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
  space-3xl: 4rem
  space-4xl: 6rem
  gutter-mobile: 1rem
  gutter-desktop: 2rem
  margin-mobile: 1rem
  margin-desktop: 3rem
---

## Brand & Style

This design system embodies an atmospheric, high-craft Nordic archive curated for legendary architectural feats. It balances ancient monumental heritage with contemporary museum-grade precision. 

The aesthetic is grounded in a hybrid of **Tactile Nordic Brutalism** and **Atmospheric Precision**:
- **Tonal Substrates**: Chiseled slate, weathered charcoal, and forged iron surfaces evoke monumental stone steles and deep Scandinavian longhouses.
- **Luminescent Heat**: Accents derived from forged bronze, crackling hearth embers, and runic amber provide contrast against cold stone backdrops.
- **Curatorial Rigor**: UI chrome remains disciplined, structural, and restrained—elevating high-resolution architectural captures, structural blueprints, era chronologies, and masonry metadata without historic pastiche or illegibility.
- **Emotional Intent**: Quiet reverence, enduring craftsmanship, architectural weight, and legendary legacy.

## Colors

The palette operates in strict dark mode, anchored by deep atmospheric strata that evoke stone slabs, charcoal forges, and twilight fells.

### Palette Mechanics
- **Base Surfaces**:
  - `Surface Void` (`#0B0F14`): Deepest background substrate for canvases and full-screen viewports.
  - `Surface Basalt` (`#121820`): Default container, section framing, and structural surface tier.
  - `Surface Ironstone` (`#1A232E`): Raised modular slabs, interactive cards, and toolbars.
  - `Surface Granite` (`#24303F`): Elevated popovers, flyouts, and modal interiors.
- **Ember & Runic Accents**:
  - `Primary Flame` (`#F59E0B`): Primary CTA fills, active era indicators, and focal runic glyphs.
  - `Burnished Bronze` (`#D97706`): Secondary actions, architectural borders, hover transitions, and badge outlines.
  - `Radiant Amber` (`#FBBF24`): High-intensity data markers, luminous pips, and key stats.
  - `Ember Glow` (`rgba(245, 158, 11, 0.12)`): Ambient volumetric backlight behind key exhibits.
- **Neutral & Text Layers**:
  - `Text Monument` (`#F1F5F9`): Titles, metrics, and monumental headings (Slate 100).
  - `Text Parchment` (`#CBD5E1`): Body copy, archive descriptions, and metadata labels (Slate 300).
  - `Text Muted` (`#64748B`): Timestamps, coordinates, inactive pagination, and sub-labels (Slate 500).
  - `Border Chisel` (`rgba(255, 255, 255, 0.08)`): Subtle structural outlines simulating fine carved stone edges.

## Typography

The typographic hierarchy couples classical architectural stature with technical precision.

- **Monumental Serif (`Bodoni Moda`)**: Serves as the high-drama museum display face. Evoking stone-cut Nordic epigraphs, royal chronicles, and historical monumental inscriptions, it is used for primary exhibit titles, era demarcations, and modal headlines. Display levels must retain slight positive tracking (`0.02em` to `0.04em`) to mirror chisel-carved stonework.
- **Architectural UI (`Plus Jakarta Sans`)**: Delivers geometric clarity and warm legibility across dense curation narratives, chronicle entries, builder commentary, and user-generated transcripts.
- **Curatorial Metrics (`JetBrains Mono`)**: Engineered for tabular density, spatial coordinates (`X: -1420, Z: 8904`), build piece counts, structural integrity ratings, timestamp metadata, and era markers.

## Layout & Spacing

The layout is built upon an architectural 12-column fluid grid system anchored by strict monolithic proportions.

### Grid & Breakpoints
- **Desktop (1280px and above)**: 12-column grid with `3rem` outer margins and `2rem` gutters. Ideal for multi-column chronicle spreads, metadata inspection sidebars, and masonry gallery feeds. Maximum content containment width is `1600px`.
- **Tablet (768px – 1279px)**: 8-column grid with `2rem` outer margins and `1.5rem` gutters. Sidebars fold into collapsible bottom drawers; gallery items transition into a 2-column masonry grid.
- **Mobile (320px – 767px)**: 4-column fluid grid with `1rem` outer margins and `1rem` gutters. Stone cards span full column width, with sticky top action bars for era filtering.

### Vertical Rhythm
A base 8px increment dictates vertical rhythm. Structural separators between historical eras utilize expansive spacing (`space-3xl` or `space-4xl`) to provide a breathing gallery cadence. Micro UI metadata clusters use compact increments (`space-2xs` to `space-sm`) to preserve data density.

## Elevation & Depth

Visual hierarchy does not use soft generic drop shadows; instead, it relies on **Tonal Stratification**, **Carved Inset Edges**, and **Ember Backlighting**.

1. **Layer 0 (Fell Void)**: `#0B0F14`. The baseline deep canvas representing unlit earth.
2. **Layer 1 (Stone Slab)**: `#121820` with a 1px perimeter border of `rgba(255, 255, 255, 0.06)`. Used for base page sections and inactive feed cards.
3. **Layer 2 (Elevated Stele)**: `#1A232E` with a 1px border of `rgba(245, 158, 11, 0.2)` on hover or focus, accompanied by a directional ambient shadow: `0 8px 24px -4px rgba(0, 0, 0, 0.6)`.
4. **Layer 3 (Forged Modal / Focus Drawer)**: `#24303F` bounded by a crisp `1px solid rgba(217, 119, 6, 0.4)` border. Background receives a volumetric glow: `0 0 40px -10px rgba(245, 158, 11, 0.15)`.

Interactive cards simulate carved granite steles: inset top highlights (`inset 0 1px 0 0 rgba(255, 255, 255, 0.08)`) give each panel a tactile, beveled architectural presence.

## Shapes

The design system maintains a **Soft-Chiseled (Level 1)** geometry. 

Elements feature slight, precise corner radiuses (`0.25rem` / `4px`) rather than pill shapes or circular curves, reinforcing the feel of hand-hewn, dressed masonry.
- **Buttons, Badges, and Input Fields**: `0.25rem` (`4px`) corner radius.
- **Structural Slabs & Cards**: `0.375rem` (`6px`) corner radius with crisp 1px borders.
- **Modals & Overlays**: `0.5rem` (`8px`) corner radius.
- **Era Pills & Metrics**: Kept squarish with minimal rounding (`0.25rem`) to maintain runic talismanic proportions. Chamfered or beveled 45-degree edge motifs may be selectively applied via clip-path on featured showcase headers.

## Components

### Buttons
- **Primary Forged Button**: Background filled with `Primary Flame` (`#F59E0B`), text in `#0B0F14` bold weight. On hover: shifts to `#FBBF24` with an outer ember glow (`box-shadow: 0 0 16px rgba(245, 158, 11, 0.4)`).
- **Secondary Stele Button**: Background in `#1A232E`, text in `Text Monument` (`#F1F5F9`), bordered with `1px solid rgba(217, 119, 6, 0.5)`. On hover: border brightens to full ember gold, background darkens to `#121820`.
- **Runic Ghost Button**: Transparent background, text in `Text Parchment` (`#CBD5E1`), adorned with runic chevron indicators (`‹ ›`). On hover: text illuminates in `#F59E0B`.

### Era Pills & Badges
- **Era Indicators (Era 7 – Era 17)**: Constructed as compact stone tablets. Background `#121820`, top-edge highlight `rgba(255, 255, 255, 0.1)`, bordered by `1px solid rgba(245, 158, 11, 0.25)`. The typography uses `JetBrains Mono` bold in all-caps (e.g., `ERA XVII // ASHLANDS`). Active era badges glow with an interior pulse of `rgba(245, 158, 11, 0.15)`.

### Stone-Slab Cards
- Modular cards housing Valheim builder chronicles. Features a 16:10 architectural photograph frame capped with an inset runic badge, followed by a metadata slab. Includes builder title (`Bodoni Moda`), server realm tag, timber/stone piece ratio, and structural integrity rating. 
- Hovering initiates an elevation lift of `2px` and shifts the border from subtle charcoal to burnished bronze.

### Data Tables & Spec Lists
- Strict museum ledger styling. Table rows feature alternating micro-striping (`#121820` and `#0E141B`) bordered by hairline grid dividers (`rgba(255, 255, 255, 0.04)`).
- Coordinates, comfort levels, and builder hashes align to `label-mono-sm` for absolute numerical clarity.

### Photography Request Modals
- High-elevation focus overlays. The modal perimeter features an etched double-border motif (outer `rgba(217, 119, 6, 0.3)`, inner hairline `rgba(255, 255, 255, 0.05)`).
- Incorporates focal length request sliders, time-of-day condition pickers (e.g., *Meadow Dawn*, *Swamp Mist*, *Ashlands Aurora*), and coordinate inputs formatted like runic steles.

### Inputs, Checkboxes & Radio Controls
- **Input Fields**: Recessed background (`#0B0F14`), inset border (`1px solid rgba(255, 255, 255, 0.1)`), glowing amber caret, placeholder text in `Text Muted`. Active focus shifts border to `#F59E0B`.
- **Checkboxes & Radios**: Squared stone markers (`0.125rem` radius). When checked, an amber rune glyph or illuminated diamond pip appears centered against the dark iron basin.