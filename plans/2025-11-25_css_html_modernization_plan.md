# CSS and HTML Modernization Implementation Plan

## Overview

This plan implements the modernization changes identified in CSS_HTML_MODERNIZATION_REPORT.md. Work is organized into phases by risk level, starting with safe high-impact changes and progressing to more complex modifications requiring careful testing.

## Phase 1: Safe High-Impact Changes (Low Risk)

### Task 1.1: Remove Vendor Prefixes from opus.css

**Files:** `opus/application/static_media/css/opus.css`

Remove vendor prefixes for universally supported properties:

- **Transform/Transition** (lines 452-472, 538-539, 546-547, 724-725, 740-741, 746-747, 778-779, 985-986, 3147, 3496-3497): Remove `-webkit-`, `-moz-`, `-o-`, `-ms-` prefixes
- **Box-sizing** (lines 516-518, 2237-2239): Remove `-webkit-` and `-moz-` prefixes
- **User-select** (lines 2911-2921, 2928-2932): Remove all vendor prefixes, keep only `user-select`
- **Border-radius** (lines 955-956): Remove `-moz-` and `-webkit-` prefixes
- **Sticky position** (line 820): Remove `-webkit-sticky`, keep `sticky`
- **Align-items** (line 1438): Remove `-webkit-align-items`, keep `align-items`
- **Text-align vendor values** (lines 2521-2522, 2542-2543): Replace `-webkit-center` and `-moz-center` with `center`
- **Placeholder pseudo-elements** (lines 3172-3178): Replace `::-moz-placeholder` and `input:-moz-placeholder` with `input::placeholder`
- **Any-link pseudo-class** (line 1457): Replace `a:-webkit-any-link, a::any-link` with standard `:any-link` or remove if not critical

**Testing:** Visual regression in Chrome, Firefox, Safari, Edge. Verify animations and transitions work.

### Task 1.2: Remove Vendor Prefixes from loader.css

**Files:** `opus/application/static_media/css/loader.css`

- Remove `-webkit-animation` prefixes (lines 19, 34, 47)
- Remove `@-webkit-keyframes` and `@-moz-keyframes`, keep only `@keyframes` (lines 50-72)
- Remove transform prefixes in keyframes (lines 52-54, 57-59, 64-66, 69-71)

**Testing:** Verify spinner animation works correctly.

### Task 1.3: Remove Vendor Prefixes from slidingPanel.css

**Files:** `opus/application/static_media/css/slidingPanel.css`

**Note:** Verify this file is still in use before modifying (may be related to dictionary feature).

Remove all vendor prefixes (60+ instances) following same patterns as opus.css:

- Transform, transition, box-sizing, animation, keyframes prefixes

**Testing:** If file is in use, test sliding panel functionality.

### Task 1.4: Remove IE8/IE9 Specific Code

**Files:** `opus/application/static_media/css/opus.css`

- Remove `filter: alpha(opacity=92)` (lines 610, 736) - `opacity` already present
- Remove `-ms-transform` with IE9 comments (lines 570-571, 638, 779, 985-986, 3496-3497)
- Remove `-ms-flexbox` syntax (line 1656), replace with `display: flex`
- Fix cursor property order (line 299): `cursor: grabbing;` should come before `cursor: -webkit-grab;` (or remove webkit version)

**Testing:** Verify opacity effects, transform animations, and flexbox layouts work correctly.

### Task 1.5: Update Deprecated Pseudo-elements

**Files:** `opus/application/static_media/css/opus.css`

- Replace placeholder selectors (lines 3172-3178) with `input::placeholder`
- Replace text-align vendor values (lines 2521-2522, 2542-2543) with `text-align: center`

**Testing:** Verify placeholder text styling and text alignment in detail images.

## Phase 2: Medium-Impact Changes (Require Testing)

### Task 2.1: Convert Float Layouts to Flexbox

**Files:** `opus/application/static_media/css/opus.css`

Convert 10+ float-based layouts to Flexbox:

1. **Gallery thumbnails** (line 579): Update `.gallery` parent to use `display: flex; flex-wrap: wrap;`, remove `float: left` from `.op-thumbnail-container`
2. **Download CSV button** (line 1065): Update parent to flex, use `margin-left: auto` instead of `float: right`
3. **Selected metadata unselect** (line 1178): Update parent `.op-selected-metadata-column ul li` to flex, use `margin-left: auto`
4. **Docking tools** (line 1314): Remove redundant `float: right` (already uses `position: absolute`)
5. **Metadata details tools** (line 1407): Update parent to flex layout
6. **Cart plus icon** (line 1444): Update parent `.bottom` to flex
7. **Cite image** (line 1616): Parent already uses flex, remove `float: left`
8. **Download links button** (line 1622): Update footer to flex, use `margin-left: auto`
9. **Close download links history** (line 1643): Parent already uses flex, use `margin-left: auto`
10. **Open help button** (line 2645): Parent already uses flex, remove `float: right`

**Testing:** Visual regression testing, responsive breakpoint testing, cross-browser layout verification.

### Task 2.2: Review and Reduce !important Usage

**Files:** `opus/application/static_media/css/opus.css`

**Systematic approach:**

1. Categorize 151 instances:

- Bootstrap/CoreUI overrides (keep - lines 9, 13, 21, 39, 505, etc.)
- Third-party library overrides (keep - Perfect Scrollbar, Flexslider, Tooltipster)
- Responsive design (evaluate - lines 3377-3750)
- Custom CSS conflicts (test removal candidates - lines 191, 207, 429, 801, 969, etc.)

2. Test removal of non-essential !important one at a time
3. Improve CSS specificity where possible instead of using !important

**Testing:** Test each removal in isolation. Verify Bootstrap overrides, third-party integrations, and responsive design still work.

## Phase 3: HTML Modernization

### Task 3.1: Add Semantic HTML5 Elements

**Files:**

- `opus/application/apps/ui/templates/ui/base.html`
- `opus/application/apps/ui/templates/ui/detail.html`

**base.html changes:**

- Wrap tab content (line 79) in `<main>` instead of `<div class="tab-content">`
- Change tab panes (lines 80, 104, 176, 285) from `<div id="search">` to `<section id="search" class="tab-pane" aria-label="Search">`
- Add aria-label attributes to all sections

**detail.html changes:**

- Fix invalid HTML nesting (lines 26-50): Move `<h4>Version: {{ version }}</h4>` outside `<ul>` or wrap in `<li>`
- Add CSS class `.op-version-header` if using Option 1 (heading outside list)

**Testing:** Verify CSS selectors still work (update if using `div#search`), check JavaScript selectors, accessibility testing.

### Task 3.2: Remove Deprecated HTML Attributes

**Files:**

- `opus/application/apps/help/templates/help/about.html`
- `opus/application/apps/help/templates/help/splash.html`

**about.html:**

- Replace `valign="top"` (lines 69, 104, 121, 128, 134, 140, 146, 152, 190, 199) with class `op-valign-top`
- Add CSS rule: `.op-valign-top { vertical-align: top; }`

**splash.html:**

- Replace inline styles (lines 3-6) with CSS classes:
- `op-splash-cell`, `op-splash-image-cell`, `op-splash-content-cell`
- `op-splash-title`, `op-splash-subtitle`
- Add missing `alt` attribute to image
- Fix `width=250` to `width="250"` (add quotes)

**Testing:** Visual verification of table layouts and splash page appearance.

### Task 3.3: Fix Invalid HTML Structure

**Files:** `opus/application/apps/ui/templates/ui/detail.html`

- Fix invalid nesting: `<h4>` inside `<ul>` (lines 26-50)
- Choose Option 1 (heading outside) or Option 2 (heading in `<li>`)
- Add CSS class if needed: `.op-version-header { margin-top: 1.5em; margin-bottom: 0.5em; }`

**Testing:** HTML validation, visual verification, CSS selector testing.

### Task 3.4: Improve Accessibility

**Files:** All HTML templates

- Add ARIA labels to sections (already partially done, complete missing ones)
- Verify heading hierarchy (h1 → h2 → h3, no skipped levels)
- Audit all `<img>` tags for `alt` attributes
- Verify form inputs have associated labels
- Test keyboard navigation and focus management

**Testing:** Screen reader testing, keyboard navigation, WCAG 2.1 AA compliance check.

## Phase 4: Testing and Validation

### Task 4.1: Pre-Implementation Baseline

- Screenshot all major pages/views
- Document current appearance
- Test in Chrome, Firefox, Safari, Edge

### Task 4.2: Incremental Testing

- Test each phase separately
- Visual regression after each change category
- Functional testing (modals, dropdowns, tooltips, widgets)
- Responsive breakpoint testing (700px, 992px, 1200px, mobile)

### Task 4.3: Cross-Browser Testing

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

### Task 4.4: Accessibility Testing

- Screen reader (NVDA/JAWS)
- Keyboard-only navigation
- WCAG 2.1 AA compliance

### Task 4.5: JavaScript Integration Testing

- Verify all JavaScript class manipulations still work
- Test widget functionality
- Test cart operations
- Test search/browse/detail views
- Document any CSS class dependencies

## Phase 5: Documentation

### Task 5.1: Update Documentation

- Document any CSS class changes
- Update any references to modified selectors
- Note browser compatibility changes (removed IE8/IE9 support)

## Implementation Notes

- **Order of execution:** Complete Phase 1 entirely before moving to Phase 2. Phase 3 can be done in parallel with Phase 2 testing.
- **Testing strategy:** Test after each task completion, not just at phase end.
- **JavaScript coordination:** Before removing any CSS classes, verify they're not used by JavaScript (check opus.js, cart.js, widgets.js, browse.js, search.js, detail.js).
- **Risk mitigation:** Keep backups, use version control, test incrementally.
- **slidingPanel.css:** Verify file is still in use before modifying (may be dictionary-related and unused).

## Success Criteria

- All vendor prefixes removed from universally supported properties
- IE8/IE9 code removed
- Float layouts converted to Flexbox
- !important usage reduced where possible (Bootstrap/third-party overrides kept)
- Semantic HTML5 elements added
- Deprecated attributes removed
- Invalid HTML fixed
- Accessibility improved
- All tests pass
- No visual regressions
- JavaScript functionality preserved