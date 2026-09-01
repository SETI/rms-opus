# CSS and HTML Modernization Report
## OPUS Application Code Review

**Date:** Generated Report
**Scope:** `opus/application/apps`, `opus/application/static_media/css`, `opus/application/static_media/js`
**Exclusions:** Third-party code (Bootstrap, jQuery UI, Font Awesome, etc.), Python formatting/type issues, `dictionary.css` (not used)

---

## Executive Summary

This report identifies modernization opportunities in the OPUS application's CSS and HTML codebase. The analysis reveals:

- **151 instances** of `!important` declarations requiring careful review
- **191+ vendor prefix instances** that can be removed (modern browsers support standard properties)
- **Deprecated CSS properties** including IE8-specific filters and old flexbox syntax
- **HTML templates** with opportunities for semantic HTML5 elements and accessibility improvements
- **Inline styles** that should be moved to CSS classes

The codebase is generally well-structured but contains legacy patterns from earlier browser support requirements. Most issues are straightforward to modernize without breaking functionality.

---

## Table of Contents

1. [High-Level Issues Overview](#high-level-issues-overview)
2. [CSS Modernization Issues](#css-modernization-issues)
3. [HTML Modernization Issues](#html-modernization-issues)
4. [File-by-File Analysis](#file-by-file-analysis)
5. [Specific Change Recommendations](#specific-change-recommendations)
6. [JavaScript Integration Considerations](#javascript-integration-considerations)
7. [Testing Recommendations](#testing-recommendations)

---

## High-Level Issues Overview

### CSS Issues Summary

| Category | Count | Priority | Impact |
|----------|-------|----------|--------|
| Vendor Prefixes | 191+ | High | Code simplification, maintenance |
| Deprecated Properties | 15+ | High | Browser compatibility, standards |
| !important Overuse | 151 | Medium | CSS specificity, maintainability |
| Float-based Layouts | 10+ | Medium | Modern layout techniques |
| Inline Styles | 5+ | Low | Separation of concerns |

### HTML Issues Summary

| Category | Count | Priority | Impact |
|----------|-------|----------|--------|
| Missing Semantic Elements | 50+ | Medium | Accessibility, SEO, maintainability |
| Deprecated Attributes | 15+ | High | Standards compliance |
| Inline Styles | 5+ | Low | Separation of concerns |
| Accessibility Issues | 10+ | High | WCAG compliance |

---

## CSS Modernization Issues

### 1. Vendor Prefixes

**Issue:** Extensive use of vendor prefixes (`-webkit-`, `-moz-`, `-ms-`, `-o-`) for properties that are now universally supported.

**Impact:** Unnecessary code bloat, maintenance burden. Modern browsers (Chrome 56+, Firefox 64+, Safari 10.1+, Edge 83+) support standard properties.

**Files Affected:**
- `opus.css` (primary - 150+ instances)
- `loader.css` (15+ instances)
- `slidingPanel.css` (60+ instances)

**Properties with Unnecessary Prefixes:**

1. **Transform** - Standard since 2012
   - `-webkit-transform`, `-moz-transform`, `-ms-transform`, `-o-transform` → `transform`
   - Found in: Lines 459, 470, 571-573, 638, 724-725, 740-741, 746-747, 778-779, 985-986, 3147, 3496-3497

2. **Transition** - Standard since 2012
   - `-webkit-transition`, `-moz-transition`, `-o-transition` → `transition`
   - Found in: Lines 454, 466, 538-539, 546-547, 855-857, 2550-2553, 3142

3. **Box-sizing** - Standard since 2011
   - `-webkit-box-sizing`, `-moz-box-sizing` → `box-sizing`
   - Found in: Lines 516-518, 2237-2239

4. **User-select** - Standard since 2013
   - `-moz-user-select`, `-khtml-user-select`, `-webkit-user-select`, `-ms-user-select` → `user-select`
   - Found in: Lines 2911-2921, 2928-2932

5. **Border-radius** - Standard since 2011
   - `-moz-border-radius`, `-webkit-border-radius` → `border-radius`
   - Found in: Lines 955-956

6. **Animation/Keyframes** - Standard since 2012
   - `@-webkit-keyframes`, `@-moz-keyframes` → `@keyframes`
   - Found in: Lines 2946-2964, loader.css lines 50-72

7. **Flexbox Properties** - Standard since 2012
   - `-ms-flexbox`, `-ms-flex-align`, `-ms-flex-pack` → Standard flexbox
   - Found in: Lines 1656-1660

8. **Sticky Position** - Standard since 2017
   - `position: -webkit-sticky` → `position: sticky`
   - Found in: Line 820

9. **Align-items** - Standard since 2012
   - `-webkit-align-items` → `align-items`
   - Found in: Line 1438

10. **Text-align** - Vendor-specific values
    - `text-align: -webkit-center`, `text-align: -moz-center` → `text-align: center`
    - Found in: Lines 2521-2522, 2542-2543

11. **Placeholder Pseudo-elements** - Deprecated syntax
    - `::-moz-placeholder`, `input:-moz-placeholder` → `::placeholder`
    - Found in: Lines 3172-3178

12. **Any-link Pseudo-class** - Non-standard
    - `a:-webkit-any-link`, `a::any-link` → Standard `:any-link` (limited support, may need alternative)
    - Found in: Line 1457

### 2. Deprecated CSS Properties

**Issue:** Properties that are deprecated or no longer needed for modern browsers.

**Specific Issues:**

1. **IE8 Filter Alpha Opacity**
   - `filter: alpha(opacity=92)` → Remove (use `opacity: 0.92` instead)
   - Found in: Lines 610, 736
   - **Note:** The `opacity: 0.92` is already present, so `filter: alpha()` can be safely removed

2. **IE9 Transform Prefixes**
   - `-ms-transform` with IE9 comments → Remove (IE9 is no longer supported)
   - Found in: Lines 570-571, 638, 779, 985-986, 3496-3497

3. **Old Flexbox Syntax**
   - `display: -ms-flexbox` → `display: flex`
   - Found in: Line 1656

4. **Cursor Vendor Prefix**
   - `cursor: -webkit-grab` → Should include standard `cursor: grab` (line 299 already has it, but order matters)
   - Found in: Line 299

### 3. !important Declarations

**Issue:** 151 instances of `!important` found. Many may be necessary for overriding Bootstrap/third-party styles, but some can be eliminated through better CSS specificity.

**Analysis Approach Required:**
- For each `!important`, determine if it's overriding:
  1. Bootstrap/CoreUI styles (likely necessary)
  2. Other custom CSS (may be fixable with specificity)
  3. Inline styles (should move to classes)
  4. JavaScript-added styles (may need JS changes)

**High-Priority !important to Review:**

1. **Bootstrap Overrides** (Likely Necessary):
   - Line 9: `body.modal-open { padding-right: 0 !important; }` - Bootstrap modal fix
   - Line 13: `body.modal-open .navbar { padding-right: 16px !important; }` - Bootstrap modal fix
   - Line 21: `.app-body { margin-top: 3.8em !important; }` - Layout override
   - Line 39: `.navbar-brand { width: 3em !important; }` - Bootstrap override
   - Line 505: `.op-search-menu .dropdown-toggle::after { display: none !important; }` - Bootstrap override

2. **Third-Party Library Overrides** (Likely Necessary):
   - Lines 270, 929, 935, 1453, 1542: Perfect Scrollbar overrides
   - Lines 2446, 2462, 2474: Flexslider overrides (with comments indicating necessity)
   - Lines 3776-3834: Tooltipster theme overrides

3. **Responsive Design** (May Be Optimizable):
   - Lines 384, 398, 429: Media query responsive overrides
   - Lines 1234-1239, 1246-1248: Modal sizing in media queries
   - Lines 3379-3511: Mobile support section (many !important)

4. **Potential Candidates for Removal** (Require Testing):
   - Line 191: `#op-help-menu.show:hover { color: var(--cui-dark) !important; }`
   - Line 207: `#op-interpret-image-menu { padding-left: 0.2em !important; }`
   - Line 429: `.shadow-divider { margin-left: 1em !important; }`
   - Line 801: `td.op-table-tools { min-width: auto !important; }`
   - Line 969: `.op-mini-thumbnail { min-width: auto !important; }`

**Recommendation:** Create a systematic review process:
1. Test each `!important` removal in isolation
2. Document which ones are required for Bootstrap/third-party overrides
3. Refactor CSS specificity where possible to eliminate unnecessary `!important`

### 4. Float-Based Layouts

**Issue:** Use of `float` for layout purposes instead of Flexbox or CSS Grid.

**Specific Instances:**

1. **Navigation Layouts:**
   - Lines 133-141: `float: none` in media queries (could use flexbox)
   - Line 579: `.op-thumbnail-container { float: left; }` - Gallery thumbnails
   - Line 1065: `#op-select-metadata .op-download-csv { float: right; }` - Button positioning
   - Line 1178: `.op-selected-metadata-unselect { float: right; }` - Button positioning
   - Line 1314: `#op-metadata-detail-view-content .op-docking-tools { float: right; }` - Tool positioning
   - Line 1407: `.op-metadata-details-tools { float: left; }` - Tool positioning
   - Line 1444: `.op-metadata-detail-view-body .fa-cart-plus { float: left; }` - Icon positioning
   - Line 1616: `.op-cite-image { float: left; }` - Image positioning
   - Line 1622: `.op-download-links-btn { float: right; }` - Button positioning
   - Line 1643: `.op-close-download-links-history { float: right; }` - Button positioning
   - Line 2645: `.op-open-help { float: right; }` - Button positioning

**Modernization Approach:**
- Replace `float: left/right` with Flexbox (`display: flex` with `justify-content` or `align-items`)
- Use CSS Grid for complex two-dimensional layouts
- Maintain visual appearance while improving maintainability

### 5. Deprecated Pseudo-elements and Selectors

**Issue:** Use of deprecated or non-standard pseudo-elements.

1. **Mozilla Placeholder (Deprecated):**
   - Lines 3172-3178: `::-moz-placeholder` and `input:-moz-placeholder`
   - **Modern replacement:** `::placeholder` (universally supported)
   - **Action:** Replace with `input::placeholder { text-overflow: ellipsis; }`

2. **Webkit Any-link (Non-standard):**
   - Line 1457: `a:-webkit-any-link, a::any-link`
   - **Issue:** `::any-link` is not widely supported, `:-webkit-any-link` is non-standard
   - **Action:** Use standard `:any-link` or remove if not critical

3. **Text-align Vendor Values:**
   - Lines 2521-2522, 2542-2543: `text-align: -webkit-center`, `text-align: -moz-center`
   - **Modern replacement:** `text-align: center` (universally supported)

### 6. CSS Organization and Structure

**Issue:** `opus.css` is 3836 lines - very large and could benefit from organization.

**Current Structure:**
- Mixed concerns (layout, components, utilities, responsive)
- Some duplicate rules
- Inconsistent commenting

**Recommendations:**
- Add section comments for major components
- Group related rules together
- Consider future modularization (not immediate priority)

---

## HTML Modernization Issues

### 1. Semantic HTML5 Elements

**Issue:** Overuse of generic `<div>` elements where semantic HTML5 elements would be more appropriate.

**Current State:**
- Navigation uses `<div>` and `<ul>` but could use `<nav>`
- Main content areas use `<div>` instead of `<main>`, `<section>`, `<article>`
- Footer exists but could be more semantic

**Specific Opportunities:**

#### base.html

1. **Main Navigation** (Lines 8-77):
   - Current: `<nav>` element exists but contains mostly divs
   - **Status:** Already uses `<nav>` - Good!
   - **Improvement:** Ensure all navigation items are properly structured

2. **Tab Content** (Lines 79-293):
   - Current: `<div class="tab-content">` containing multiple `<div id="search">`, `<div id="browse">`, etc.
   - **Recommendation:**
     - Wrap in `<main>` element
     - Use `<section>` for each major tab (search, browse, cart, detail)
     - Example: `<main><section id="search" class="tab-pane">...</section></main>`

3. **Footer** (Line 624):
   - Current: `{% include "ui/footer.html" %}`
   - **Status:** Need to check footer.html structure

#### detail.html

1. **Main Content** (Line 1):
   - Current: `<section class="container-fluid">` - Good use of semantic element!
   - **Status:** Already semantic

2. **Product Lists** (Lines 26-50):
   - Current: `<ul>` with `<h4>` inside (invalid HTML - h4 cannot be child of ul)
   - **Issue:** `<h4>Version: {{ version }}</h4>` is inside `<ul class="op-detail-list">`
   - **Fix:** Move heading outside list or use `<li><h4>...</h4></li>`

#### Other Templates

- Most templates use appropriate Bootstrap classes but could benefit from semantic wrappers
- Help templates appear to use semantic structure appropriately

### 2. Deprecated HTML Attributes

**Issue:** Use of deprecated HTML attributes that should be replaced with CSS.

**Specific Instances:**

1. **help/templates/help/about.html:**
   - Lines 69, 104, 121, 128, 134, 140, 146, 152, 190, 199: `valign="top"` attribute
   - **Modern replacement:** CSS `vertical-align: top` or Flexbox `align-items: flex-start`
   - **Action:** Move to CSS class

2. **help/templates/help/about.html:**
   - Lines 69, 104, 121, 152: `rowspan` attribute
   - **Status:** `rowspan` is still valid HTML5 for tables - no change needed

3. **help/templates/help/splash.html:**
   - Lines 3-6: Inline `style` attributes
   - **Action:** Move to CSS classes

### 3. Inline Styles

**Issue:** Inline `style` attributes that should be moved to CSS classes.

**Specific Instances:**

1. **help/templates/help/splash.html:**
   - Line 3: `<td style="border:0;">`
   - Line 4: `<td style="border:0;width:100%;">`
   - Line 5: `<div style="font-size:30px;line-height:35px;text-align:center;">`
   - Line 6: `<div style="font-size:10px;text-align:center;">`
   - **Action:** Create CSS classes in appropriate stylesheet

2. **ui/templates/ui/widget.html:**
   - Line 25: `style="display: none"` (likely set by JavaScript)
   - Line 41: `style=""` (empty, likely set by JavaScript)
   - **Action:** Use CSS classes, manipulate with JS `addClass/removeClass`

3. **ui/templates/ui/footer.html:**
   - Line 8: Inline `style` in SVG element
   - **Status:** SVG inline styles are sometimes necessary for dynamic sizing
   - **Action:** Review if this can be moved to CSS

### 4. Accessibility Issues

**Issue:** Missing or improper accessibility attributes and structure.

**Specific Issues:**

1. **Missing Alt Attributes:**
   - Need to audit all `<img>` tags for `alt` attributes
   - Found in detail.html: Lines 74, 83 have proper `alt` attributes - Good!

2. **ARIA Labels:**
   - Navigation has some ARIA attributes but could be more comprehensive
   - Modal dialogs have proper ARIA - Good!

3. **Heading Hierarchy:**
   - Need to verify proper h1 → h2 → h3 hierarchy
   - detail.html has proper structure

4. **Form Labels:**
   - Need to verify all form inputs have associated labels
   - Widget templates should be checked

5. **Keyboard Navigation:**
   - Focus management in modals
   - Tab order verification needed

### 5. HTML Structure Issues

**Issue:** Invalid or suboptimal HTML structure.

1. **Invalid Nesting (detail.html):**
   - Lines 27-49: `<h4>` directly inside `<ul>` (invalid HTML)
   - **Current:**
     ```html
     <ul class="op-detail-list">
         <h4>Version: {{ version }}</h4>
         <li>...</li>
     </ul>
     ```
   - **Fix:**
     ```html
     <h4>Version: {{ version }}</h4>
     <ul class="op-detail-list">
         <li>...</li>
     </ul>
     ```
     OR
     ```html
     <ul class="op-detail-list">
         <li><h4>Version: {{ version }}</h4></li>
         <li>...</li>
     </ul>
     ```

2. **Empty/Redundant Attributes:**
   - Line 41 in widget.html: `style=""` (empty attribute)
   - **Action:** Remove or populate appropriately

---

## File-by-File Analysis

### opus.css (3836 lines)

**Priority: High** - Main stylesheet with most issues

#### Vendor Prefixes to Remove:

1. **Lines 454-472:** Transition and transform prefixes
   ```css
   /* Current */
   transition: all .3s;
   -webkit-transition: all .3s;
   transform: rotate(-90deg);
   -webkit-transform: rotate(-90deg);
   -o-transform: rotate(-90deg);

   /* Modern */
   transition: all .3s;
   transform: rotate(-90deg);
   ```

2. **Lines 516-518:** Box-sizing prefixes
   ```css
   /* Current */
   -webkit-box-sizing: border-box;
   -moz-box-sizing: border-box;
   box-sizing: border-box;

   /* Modern */
   box-sizing: border-box;
   ```

3. **Lines 570-576:** IE9 transform prefixes (remove entirely)
   ```css
   /* Current */
   -ms-transform: rotate(-90deg); /* IE 9 */
   -ms-transform-origin: 80% 43%; /* IE 9 */
   -webkit-transform: rotate(-90deg); /* Safari 3-8 */
   -webkit-transform-origin: 80% 43%; /* Safari 3-8 */
   transform: rotate(-90deg);
   transform-origin: 80% 43%;

   /* Modern */
   transform: rotate(-90deg);
   transform-origin: 80% 43%;
   ```

4. **Lines 610, 736:** Remove filter alpha
   ```css
   /* Current */
   opacity: 0.92;
   filter: alpha(opacity=92);

   /* Modern */
   opacity: 0.92;
   ```

5. **Lines 2911-2921:** User-select prefixes
   ```css
   /* Current */
   -moz-user-select: none;
   -khtml-user-select: none;
   -webkit-user-select: none;
   -ms-user-select: none;
   user-select: none;

   /* Modern */
   user-select: none;
   ```

6. **Lines 3172-3178:** Placeholder pseudo-elements
   ```css
   /* Current */
   ::-moz-placeholder {
       text-overflow: ellipsis;
   }
   input:-moz-placeholder {
       text-overflow: ellipsis;
   }

   /* Modern */
   input::placeholder {
       text-overflow: ellipsis;
   }
   ```

#### Float to Flexbox Conversions:

1. **Line 579:** Thumbnail container
   ```css
   /* Current */
   .op-thumbnail-container {
       float: left;
       position: relative;
       margin: 1px;
   }

   /* Modern */
   .op-thumbnail-container {
       position: relative;
       margin: 1px;
       /* Parent should use display: flex or grid */
   }
   ```

2. **Line 1065:** Download CSV button
   ```css
   /* Current */
   #op-select-metadata .op-download-csv {
       position: relative;
       float: right;
       margin-top: 1rem;
   }

   /* Modern */
   #op-select-metadata .op-download-csv {
       position: relative;
       margin-top: 1rem;
       margin-left: auto; /* If parent is flex */
   }
   ```

#### !important Review Needed:

**High Priority for Testing:**
- Lines 9, 13, 21, 39: Bootstrap overrides (likely necessary)
- Lines 270, 929, 935: Perfect Scrollbar overrides (likely necessary)
- Lines 2446, 2462, 2474: Flexslider overrides (comments indicate necessity)
- Lines 191, 207, 429: May be removable with better specificity

### loader.css (74 lines)

**Priority: Medium** - Smaller file, straightforward fixes

#### Issues:

1. **Lines 19, 34, 47:** Remove `-webkit-animation` prefixes
2. **Lines 50-72:** Remove `@-webkit-keyframes` and `@-moz-keyframes`, keep only `@keyframes`
3. **Lines 52-54, 57-59, 64-66, 69-71:** Remove transform prefixes in keyframes

**All vendor prefixes can be safely removed** - animations are universally supported.

### slidingPanel.css (340 lines)

**Priority: Low** - Appears to be for dictionary feature (may not be actively used)

**Note:** User specified to ignore dictionary.css, but slidingPanel.css may be related. Verify usage before modifying.

#### Issues Found:
- Extensive vendor prefixes (60+ instances)
- All can be removed if this file is still in use
- Same patterns as other files

### api_guide.css (67 lines)

**Priority: Low** - Simple stylesheet, minimal issues

#### Issues:
- No vendor prefixes found
- Some hardcoded pixel values (acceptable for print styles)
- Generally clean code

### offline-mode.css

**Status:** File is empty - no issues

---

## Specific Change Recommendations

### Phase 1: Safe, High-Impact Changes

#### 1. Remove Vendor Prefixes for Universally Supported Properties

**Files:** `opus.css`, `loader.css`, `slidingPanel.css`

**Properties to Update:**
- `transform` and `transform-origin` (remove all prefixes)
- `transition` (remove all prefixes)
- `box-sizing` (remove all prefixes)
- `user-select` (remove all prefixes)
- `border-radius` (remove all prefixes)
- `animation` and `@keyframes` (remove all prefixes)
- `flexbox` properties (remove `-ms-` prefixes)

**Risk Level:** Low - These properties have been standard for 10+ years

**Testing Required:**
- Visual regression testing in Chrome, Firefox, Safari, Edge
- Verify animations still work
- Check transform/transition effects

#### 2. Remove IE8/IE9 Specific Code

**Files:** `opus.css`

**Changes:**
- Remove `filter: alpha(opacity=X)` (lines 610, 736)
- Remove `-ms-transform` with IE9 comments (lines 570-571, 638, 779, 985-986, 3496-3497)
- Remove `-ms-flexbox` syntax (line 1656)

**Risk Level:** Low - IE8/IE9 are no longer supported

**Testing Required:**
- Verify opacity effects work correctly
- Check transform animations
- Verify flexbox layouts

#### 3. Update Deprecated Pseudo-elements

**Files:** `opus.css`

**Changes:**
- Replace `::-moz-placeholder` and `input:-moz-placeholder` with `::placeholder` (lines 3172-3178)
- Replace `text-align: -webkit-center` and `text-align: -moz-center` with `text-align: center` (lines 2521-2522, 2542-2543)

**Risk Level:** Low

**Testing Required:**
- Verify placeholder text styling
- Check text alignment in detail images

### Phase 2: Medium-Impact Changes (Require Careful Testing)

#### 4. Convert Float Layouts to Flexbox

**Files:** `opus.css`

**Approach:**
1. Identify parent containers of floated elements
2. Add `display: flex` to parents
3. Replace `float: left/right` with appropriate flex properties
4. Test thoroughly for layout regressions

**Specific Conversions:**

**Gallery Thumbnails (Line 579):**
```css
/* Current parent context needed - likely .gallery */
/* Add to parent: */
.gallery {
    display: flex;
    flex-wrap: wrap;
}

/* Update child: */
.op-thumbnail-container {
    /* Remove: float: left; */
    position: relative;
    margin: 1px;
}
```

**Download CSV Button (Line 1065):**
```css
/* Update parent to use flex: */
#op-select-metadata .modal-footer {
    display: flex;
    justify-content: space-between;
}

/* Update child: */
#op-select-metadata .op-download-csv {
    position: relative;
    margin-top: 1rem;
    margin-left: auto; /* Pushes to right in flex container */
}
```

**Risk Level:** Medium - Layout changes require visual testing

**Testing Required:**
- Visual regression testing
- Responsive breakpoint testing
- Cross-browser layout verification

#### 5. Review and Reduce !important Usage

**Files:** `opus.css`

**Systematic Approach:**

1. **Categorize each !important:**
   - Bootstrap/CoreUI overrides (keep)
   - Third-party library overrides (keep)
   - Responsive design (evaluate)
   - Custom CSS conflicts (candidates for removal)

2. **Test removal of non-essential !important:**
   - Start with responsive design section (lines 3377-3750)
   - Test each removal individually
   - Document which ones are required

3. **Improve CSS specificity where possible:**
   - Use more specific selectors instead of !important
   - Example: Instead of `.class { color: red !important; }`
   - Use: `.parent .class { color: red; }`

**Risk Level:** Medium-High - Requires extensive testing

**Testing Required:**
- Test each !important removal in isolation
- Verify Bootstrap overrides still work
- Check third-party library integrations
- Responsive design testing

### Phase 3: HTML Modernization

#### 6. Add Semantic HTML5 Elements

**Files:** `base.html`, `detail.html`, other templates

**Changes:**

**base.html:**
```html
<!-- Current -->
<div class="tab-content border-0 container-fluid tab-full-width">
    <div id="search" class="tab-pane">...</div>
    <div id="browse" class="tab-pane">...</div>
</div>

<!-- Modern -->
<main class="tab-content border-0 container-fluid tab-full-width">
    <section id="search" class="tab-pane" aria-label="Search">...</section>
    <section id="browse" class="tab-pane" aria-label="Browse Results">...</section>
    <section id="cart" class="tab-pane" aria-label="Cart">...</section>
    <section id="detail" class="tab-pane" aria-label="Observation Detail">...</section>
</main>
```

**detail.html:**
```html
<!-- Fix invalid nesting -->
<!-- Current (INVALID) -->
<ul class="op-detail-list">
    <h4>Version: {{ version }}</h4>
    <li>...</li>
</ul>

<!-- Modern Option 1 -->
<h4>Version: {{ version }}</h4>
<ul class="op-detail-list">
    <li>...</li>
</ul>

<!-- Modern Option 2 -->
<ul class="op-detail-list">
    <li class="op-version-header"><h4>Version: {{ version }}</h4></li>
    <li>...</li>
</ul>
```

**Risk Level:** Low-Medium - Semantic changes shouldn't break functionality

**Testing Required:**
- Verify CSS selectors still work (may need to update if using `div#search`)
- Check JavaScript selectors (jQuery uses `#search` which works with sections)
- Accessibility testing with screen readers

#### 7. Remove Deprecated HTML Attributes

**Files:** `help/templates/help/about.html`, `help/templates/help/splash.html`

**Changes:**

**about.html - Replace valign:**
```html
<!-- Current -->
<td rowspan="5" valign="top">

<!-- Modern -->
<td rowspan="5" class="op-valign-top">
```
```css
/* Add to CSS */
.op-valign-top {
    vertical-align: top;
}
```

**splash.html - Move inline styles:**
```html
<!-- Current -->
<td style="border:0;"><img src="..."></td>
<td style="border:0;width:100%;">
    <div style="font-size:30px;line-height:35px;text-align:center;">Welcome<br>to<br>OPUS3</div>
    <div style="font-size:10px;text-align:center;">Outer Planets Unified Search<br>10th Anniversary Edition</div>
</td>

<!-- Modern -->
<td class="op-splash-cell op-splash-image-cell"><img src="..."></td>
<td class="op-splash-cell op-splash-content-cell">
    <div class="op-splash-title">Welcome<br>to<br>OPUS3</div>
    <div class="op-splash-subtitle">Outer Planets Unified Search<br>10th Anniversary Edition</div>
</td>
```
```css
/* Add to appropriate CSS file */
.op-splash-cell {
    border: 0;
}
.op-splash-content-cell {
    width: 100%;
}
.op-splash-title {
    font-size: 30px;
    line-height: 35px;
    text-align: center;
}
.op-splash-subtitle {
    font-size: 10px;
    text-align: center;
}
```

**Risk Level:** Low

**Testing Required:**
- Visual verification of table layouts
- Check splash page appearance

#### 8. Improve Accessibility

**Files:** All HTML templates

**Changes:**

1. **Add ARIA labels where missing:**
   ```html
   <!-- Add aria-label to sections -->
   <section id="search" class="tab-pane" aria-label="Search for observations">
   ```

2. **Ensure proper heading hierarchy:**
   - Verify h1 → h2 → h3 structure
   - No skipped heading levels

3. **Add alt text to images:**
   - Audit all `<img>` tags
   - Add descriptive alt text (many already have this)

4. **Form accessibility:**
   - Verify all inputs have associated labels
   - Check widget templates for proper label/input relationships

**Risk Level:** Low - Improvements only

**Testing Required:**
- Screen reader testing
- Keyboard navigation testing
- WCAG compliance audit

---

## JavaScript Integration Considerations

### CSS Class Dependencies

**Critical:** JavaScript extensively uses `addClass()` and `removeClass()` to manipulate styling. Any CSS class name changes must be coordinated with JavaScript updates.

**Key JavaScript Files to Review:**

1. **opus.js:**
   - Line 280: `$("#op-result-count").html(opus.spinner).parent().effect("highlight", {}, 500);`
   - Uses jQuery effects that may depend on CSS

2. **cart.js:**
   - Lines 881-893: Adds/removes classes like `op-in-cart`, `op-hide-element`, `text-success`, `op-recycled`
   - **Action:** Verify these classes exist in CSS and aren't being removed

3. **widgets.js:**
   - Extensive class manipulation for widget states
   - **Action:** Document all classes used by JavaScript

4. **browse.js, search.js, detail.js:**
   - All manipulate CSS classes for UI state
   - **Action:** Create inventory of JS-manipulated classes

**Recommendation:**
- Before removing any CSS, create a mapping of JavaScript class dependencies
- Test JavaScript functionality after CSS changes
- Consider creating a CSS class registry/documentation

### Inline Style Manipulation

**Found Instances:**
- Some JavaScript may set inline styles directly
- **Action:** Identify and move to CSS classes where possible

**Example Pattern to Look For:**
```javascript
// Bad (if found)
$(element).css('display', 'none');

// Good
$(element).addClass('op-hide-element');
```

---

## Testing Recommendations

### Pre-Implementation Testing

1. **Create Visual Baseline:**
   - Screenshot all major pages/views
   - Document current appearance
   - Test in Chrome, Firefox, Safari, Edge

2. **Functional Testing:**
   - Test all interactive elements
   - Verify modals, dropdowns, tooltips
   - Test responsive breakpoints
   - Verify JavaScript functionality

### During Implementation Testing

1. **Incremental Testing:**
   - Test each change category separately
   - Vendor prefix removal → test
   - Float to flexbox → test
   - HTML semantic changes → test

2. **Regression Testing:**
   - After each change, verify:
     - Visual appearance unchanged
     - Functionality preserved
     - JavaScript still works
     - Responsive design intact

### Post-Implementation Testing

1. **Cross-Browser Testing:**
   - Chrome (latest)
   - Firefox (latest)
   - Safari (latest)
   - Edge (latest)

2. **Accessibility Testing:**
   - Screen reader testing
   - Keyboard navigation
   - WCAG 2.1 AA compliance check

3. **Performance Testing:**
   - CSS file size reduction
   - Page load times
   - Render performance

---

## Detailed Line-by-Line Changes

### opus.css - Vendor Prefix Removal

#### Section: Transitions and Transforms (Lines 450-472)

**Lines 452-455:**
```css
/* CURRENT */
.op-search-menu .dropdown-toggle::after {
    transition: all .3s;
    -webkit-transition: all .3s;
}

/* CHANGE TO */
.op-search-menu .dropdown-toggle::after {
    transition: all .3s;
}
```

**Lines 457-461:**
```css
/* CURRENT */
.op-search-menu .dropdown-toggle.collapsed::after {
    transform: rotate(-90deg);
    -webkit-transform: rotate(-90deg);
    -o-transform: rotate(-90deg);
}

/* CHANGE TO */
.op-search-menu .dropdown-toggle.collapsed::after {
    transform: rotate(-90deg);
}
```

**Lines 464-472:**
```css
/* CURRENT */
.op-search-menu .dropdown-toggle .op-menu-arrow {
    transition: all .3s;
    -webkit-transition: all .3s;
}
.op-search-menu .dropdown-toggle.collapsed .op-menu-arrow {
    transform: rotate(-90deg);
    -webkit-transform: rotate(-90deg);
    -o-transform: rotate(-90deg);
}

/* CHANGE TO */
.op-search-menu .dropdown-toggle .op-menu-arrow {
    transition: all .3s;
}
.op-search-menu .dropdown-toggle.collapsed .op-menu-arrow {
    transform: rotate(-90deg);
}
```

#### Section: Box-sizing (Lines 516-518)

```css
/* CURRENT */
.sidebar_wrapper {
    display: flex;
    margin: 0;
    padding: 0;
    overflow: auto;
    margin-top: 5px;
    position: relative;
    height: 500px;
    -webkit-box-sizing: border-box;
    -moz-box-sizing: border-box;
    box-sizing: border-box;
}

/* CHANGE TO */
.sidebar_wrapper {
    display: flex;
    margin: 0;
    padding: 0;
    overflow: auto;
    margin-top: 5px;
    position: relative;
    height: 500px;
    box-sizing: border-box;
}
```

#### Section: Widget Header Transforms (Lines 569-576)

```css
/* CURRENT */
.widget .card-header .collapsed .icon-action {
    -ms-transform: rotate(-90deg); /* IE 9 */
    -ms-transform-origin: 80% 43%; /* IE 9 */
    -webkit-transform: rotate(-90deg); /* Safari 3-8 */
    -webkit-transform-origin: 80% 43%; /* Safari 3-8 */
    transform: rotate(-90deg);
    transform-origin: 80% 43%;
}

/* CHANGE TO */
.widget .card-header .collapsed .icon-action {
    transform: rotate(-90deg);
    transform-origin: 80% 43%;
}
```

#### Section: Thumbnail Overlay (Lines 604-616)

```css
/* CURRENT */
.op-thumb-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    opacity: 0.92;
    filter: alpha(opacity=92);
    background: rgba(76, 75, 80, 0.3);
    overflow: hidden;
    width: 100%;
    height: 0;
    transition: .5s ease;
}

/* CHANGE TO */
.op-thumb-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    opacity: 0.92;
    background: rgba(76, 75, 80, 0.3);
    overflow: hidden;
    width: 100%;
    height: 0;
    transition: .5s ease;
}
```

#### Section: User Select (Lines 2911-2933)

```css
/* CURRENT */
.op-no-select, .feedbackTab, .fas, .far {
    -moz-user-select: none;
    -khtml-user-select: none;
    -webkit-user-select: none;
    -ms-user-select: none;
    user-select: none;
}

/* Allow users to mouse over and select texts & hints in widgets */
.op-input ul label, .op-input ul span,
.op-hints-info, .op-hints-description,
.op-detail-list {
    -ms-user-select: text;
    user-select: text;
    -moz-user-select: text;
    -khtml-user-select: text;
    -webkit-user-select: text;
}

/* CHANGE TO */
.op-no-select, .feedbackTab, .fas, .far {
    user-select: none;
}

/* Allow users to mouse over and select texts & hints in widgets */
.op-input ul label, .op-input ul span,
.op-hints-info, .op-hints-description,
.op-detail-list {
    user-select: text;
}
```

#### Section: Placeholder Styling (Lines 3168-3178)

```css
/* CURRENT */
input[placeholder] {
    text-overflow: ellipsis;
}

::-moz-placeholder {
    text-overflow: ellipsis;
}

input:-moz-placeholder {
    text-overflow: ellipsis;
}

/* CHANGE TO */
input[placeholder] {
    text-overflow: ellipsis;
}

input::placeholder {
    text-overflow: ellipsis;
}
```

#### Section: Text Alignment (Lines 2521-2523, 2542-2544)

```css
/* CURRENT */
.op-detail-img li {
    text-align: -webkit-center;
    text-align: -moz-center;
}

.op-detail-img .op-preview-guide-center {
    text-align: -webkit-center;
    text-align: -moz-center;
    margin-top: 2rem;
}

/* CHANGE TO */
.op-detail-img li {
    text-align: center;
}

.op-detail-img .op-preview-guide-center {
    text-align: center;
    margin-top: 2rem;
}
```

#### Section: Cursor Property (Line 299)

```css
/* CURRENT */
.op-metadata-details-edit-enabled ul:hover {
    cursor: -webkit-grab;
    cursor: grabbing;
}

/* CHANGE TO (reorder for better fallback) */
.op-metadata-details-edit-enabled ul:hover {
    cursor: grabbing;
    cursor: -webkit-grab; /* Fallback for older Safari if needed, but can likely remove */
}
```

**Note:** Modern browsers support `cursor: grabbing`, so `-webkit-grab` can likely be removed entirely. Test in Safari to confirm.

### loader.css - Complete Modernization

**Lines 19-20:**
```css
/* CURRENT */
-webkit-animation: spin 2s linear infinite;
animation: spin 2s linear infinite;

/* CHANGE TO */
animation: spin 2s linear infinite;
```

**Lines 34-35, 47-48:** Same pattern - remove `-webkit-animation`

**Lines 50-72:** Remove all `@-webkit-keyframes` and `@-moz-keyframes`, keep only `@keyframes`:

```css
/* CURRENT */
@-webkit-keyframes spin {
    0%   {
        -webkit-transform: rotate(0deg);
        -ms-transform: rotate(0deg);
        transform: rotate(0deg);
    }
    100% {
        -webkit-transform: rotate(360deg);
        -ms-transform: rotate(360deg);
        transform: rotate(360deg);
    }
}
@keyframes spin {
    0%   {
        -webkit-transform: rotate(0deg);
        -ms-transform: rotate(0deg);
        transform: rotate(0deg);
    }
    100% {
        -webkit-transform: rotate(360deg);
        -ms-transform: rotate(360deg);
        transform: rotate(360deg);
    }
}

/* CHANGE TO */
@keyframes spin {
    0% {
        transform: rotate(0deg);
    }
    100% {
        transform: rotate(360deg);
    }
}
```

### HTML Template Changes

#### base.html - Semantic Improvements

**Lines 79-293:** Wrap tab content in semantic elements

```html
<!-- CURRENT -->
<div class="tab-content border-0 container-fluid tab-full-width">
    <div id="search" class="tab-pane op-no-select" role="tabpanel" aria-labelledby="search-tab">
        <!-- content -->
    </div>
    <div id="browse" class="tab-pane op-no-select" role="tabpanel" aria-labelledby="browse-tab">
        <!-- content -->
    </div>
    <!-- etc -->
</div>

<!-- MODERN -->
<main class="tab-content border-0 container-fluid tab-full-width">
    <section id="search" class="tab-pane op-no-select" role="tabpanel" aria-labelledby="search-tab" aria-label="Search for observations">
        <!-- content -->
    </section>
    <section id="browse" class="tab-pane op-no-select" role="tabpanel" aria-labelledby="browse-tab" aria-label="Browse observation results">
        <!-- content -->
    </section>
    <section id="cart" class="tab-pane op-no-select" role="tabpanel" aria-labelledby="cart-tab" aria-label="Observation cart">
        <!-- content -->
    </section>
    <section id="detail" class="tab-pane" role="tabpanel" aria-labelledby="detail-tab" aria-label="Observation detail">
        <!-- content -->
    </section>
</main>
```

**Note:** CSS selectors using `#search`, `#browse`, etc. will continue to work. JavaScript using `$("#search")` will also work. Only change needed is updating any CSS that specifically targets `div#search` to `section#search` or just `#search`.

#### detail.html - Fix Invalid HTML

**Lines 26-50:** Fix heading inside list

```html
<!-- CURRENT (INVALID) -->
{% for version, version_items in products.items %}
    <ul class="op-detail-list">
        <h4>Version: {{ version }}</h4>
        {% for product_type, product_type_info in version_items.items %}
            <li class="op-detail-entry">
                <!-- content -->
            </li>
        {% endfor %}
    </ul>
{% endfor %}

<!-- MODERN OPTION 1 (Recommended) -->
{% for version, version_items in products.items %}
    <h4 class="op-version-header">Version: {{ version }}</h4>
    <ul class="op-detail-list">
        {% for product_type, product_type_info in version_items.items %}
            <li class="op-detail-entry">
                <!-- content -->
            </li>
        {% endfor %}
    </ul>
{% endfor %}
```

**CSS Addition Needed:**
```css
.op-version-header {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}
```

#### help/templates/help/splash.html - Remove Inline Styles

**Lines 3-6:**
```html
<!-- CURRENT -->
<td style="border:0;"><img src="{{ STATIC_URL }}img/splash-outer-planets.jpg" width=250></td>
<td style="border:0;width:100%;">
    <div style="font-size:30px;line-height:35px;text-align:center;">Welcome<br>to<br>OPUS3</div>
    <div style="font-size:10px;text-align:center;">Outer Planets Unified Search<br>10th Anniversary Edition</div>
</td>

<!-- MODERN -->
<td class="op-splash-image-cell"><img src="{{ STATIC_URL }}img/splash-outer-planets.jpg" width="250" alt="Outer planets visualization"></td>
<td class="op-splash-content-cell">
    <div class="op-splash-title">Welcome<br>to<br>OPUS3</div>
    <div class="op-splash-subtitle">Outer Planets Unified Search<br>10th Anniversary Edition</div>
</td>
```

**CSS to Add (in appropriate stylesheet, possibly new `help.css` or add to existing):**
```css
.op-splash-image-cell {
    border: 0;
}
.op-splash-content-cell {
    border: 0;
    width: 100%;
}
.op-splash-title {
    font-size: 30px;
    line-height: 35px;
    text-align: center;
}
.op-splash-subtitle {
    font-size: 10px;
    text-align: center;
}
```

#### help/templates/help/about.html - Remove Deprecated Attributes

**Multiple lines with `valign="top"`:**
```html
<!-- CURRENT -->
<td rowspan="5" valign="top">

<!-- MODERN -->
<td rowspan="5" class="op-valign-top">
```

**CSS to Add:**
```css
.op-valign-top {
    vertical-align: top;
}
```

---

## !important Declaration Analysis

### Categorization of !important Usage

#### Category 1: Bootstrap/CoreUI Overrides (Keep - Likely Necessary)

**Count:** ~30 instances

**Examples:**
- Line 9: `body.modal-open { padding-right: 0 !important; }` - Bootstrap modal fix
- Line 13: `body.modal-open .navbar { padding-right: 16px !important; }` - Bootstrap modal fix
- Line 21: `.app-body { margin-top: 3.8em !important; }` - Layout override
- Line 39: `.navbar-brand { width: 3em !important; }` - Bootstrap override
- Line 505: `.op-search-menu .dropdown-toggle::after { display: none !important; }` - Bootstrap override
- Line 3616: `.modal-header { align-items: center !important; }` - Bootstrap override

**Recommendation:** Keep these - they're overriding third-party framework styles.

#### Category 2: Third-Party Library Overrides (Keep - Likely Necessary)

**Count:** ~25 instances

**Examples:**
- Lines 270, 929, 935, 1453, 1542: Perfect Scrollbar overrides
  ```css
  .op-gallery-view > .ps__rail-y {
      background-color: transparent !important;
  }
  ```
- Lines 2446, 2462, 2474: Flexslider overrides (with comments indicating necessity)
  ```css
  /* use !important to override the styling from flexslider */
  .op-detail-img img {
      height: 150px !important;
  }
  ```
- Lines 3776-3834: Tooltipster theme overrides (entire section)

**Recommendation:** Keep these - they're overriding third-party library styles that may use !important themselves.

#### Category 3: Responsive Design (Evaluate Case-by-Case)

**Count:** ~60 instances in mobile support section (lines 3377-3750)

**Examples:**
- Line 3379: `body { font-size: 75% !important; }` - Mobile font scaling
- Line 3391: `.app-footer { display: none !important; }` - Hide footer on mobile
- Line 3420: `.op-tab { flex-direction: row !important; }` - Mobile nav layout
- Line 3530: `.modal-header, .modal-body, .modal-footer { padding: 0.25em 0.5em !important; }` - Mobile modal sizing

**Analysis:**
- Many of these are in media queries that override default styles
- Some may be removable by increasing selector specificity
- Comments indicate some are necessary (e.g., line 3388: "Need to use !important here so that the footer (inside a flex container) will not take up the space when hidden")

**Recommendation:**
- Test removal of each individually
- Keep those with comments explaining necessity
- Try improving specificity for others

#### Category 4: Custom CSS Conflicts (Candidates for Removal)

**Count:** ~36 instances

**Examples to Test Removal:**
- Line 191: `#op-help-menu.show:hover { color: var(--cui-dark) !important; }`
- Line 207: `#op-interpret-image-menu { padding-left: 0.2em !important; }`
- Line 429: `.shadow-divider { margin-left: 1em !important; }`
- Line 801: `td.op-table-tools { min-width: auto !important; }`
- Line 969: `.op-mini-thumbnail { min-width: auto !important; }`
- Line 1097: `.op-menu-first-category .op-submenu-category { padding-top: 0 !important; }`
- Line 1109-1110: `.op-submenu-category { margin-top: 0 !important; margin-bottom: 0 !important; }`
- Line 1138: `.op-all-metadata-column .op-search-menu-category { padding-top: 0px !important; }`
- Line 1723: `.op-observation-text { margin-left: 0px !important; }`
- Line 1989: `.op-sort-order-add-icon { margin-bottom: 0.1em !important; }`
- Line 2344: `.mult-group { padding-left: 1.2em !important; }`
- Line 2605: `.op-range-select-info-box { margin-left: 0px !important; }`
- Line 2625: `footer { min-height: 1rem !important; }`

**Testing Strategy:**
1. Remove one !important at a time
2. Test the specific component/feature
3. If it breaks, investigate why (specificity issue? cascade issue?)
4. Document findings

**Potential Fixes:**
- Increase selector specificity instead of using !important
- Reorganize CSS order (later rules override earlier ones)
- Use more specific class names

---

## Float to Flexbox Conversion Details

### Conversion Strategy

For each float-based layout:

1. **Identify the parent container**
2. **Add flexbox to parent:** `display: flex;`
3. **Remove float from child:** Remove `float: left/right`
4. **Use flex properties for positioning:**
   - `justify-content: flex-end` for right alignment
   - `justify-content: space-between` for spacing
   - `margin-left: auto` to push item right
   - `margin-right: auto` to push item left

### Specific Conversions

#### 1. Gallery Thumbnails (Line 579)

**Current:**
```css
.op-thumbnail-container {
    float: left;
    position: relative;
    margin: 1px;
    min-width: 98px;
    min-height: 98px;
    border: medium solid transparent;
}
```

**Parent Context:** `.gallery` (line 256-261)

**Conversion:**
```css
/* Update parent */
.gallery {
    margin: 0;
    padding: 0;
    background-color: #303030;
    padding-left: 1.5em;
    display: flex;
    flex-wrap: wrap;
    gap: 2px; /* Replaces margin: 1px on children */
}

/* Update child */
.op-thumbnail-container {
    /* Remove: float: left; */
    position: relative;
    /* margin: 1px; - replaced by parent gap */
    min-width: 98px;
    min-height: 98px;
    border: medium solid transparent;
}
```

**Testing:** Verify thumbnail grid layout, spacing, and wrapping behavior.

#### 2. Download CSV Button (Line 1065)

**Current:**
```css
#op-select-metadata .op-download-csv {
    position: relative;
    float: right;
    margin-top: 1rem;
}
```

**Parent Context:** Modal footer (line 381-389 in base.html)

**Conversion:**
```css
/* Parent already has display: flex from Bootstrap, verify */
#op-select-metadata .modal-footer {
    display: flex;
    justify-content: space-between; /* Already present */
}

/* Update child */
#op-select-metadata .op-download-csv {
    position: relative;
    margin-top: 1rem;
    margin-left: auto; /* Pushes to right */
}
```

**Testing:** Verify button positioning in modal footer.

#### 3. Selected Metadata Unselect Button (Line 1178)

**Current:**
```css
.op-selected-metadata-unselect {
    float: right;
}
```

**Parent Context:** `.op-selected-metadata-column ul li` (line 1190-1194)

**Conversion:**
```css
.op-selected-metadata-column ul li {
    padding: 5px 10px 5px 5px;
    border: 1px dotted gray;
    list-style-type: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.op-selected-metadata-unselect {
    /* Remove: float: right; */
    margin-left: auto; /* Pushes to right */
}
```

**Testing:** Verify button alignment in metadata list items.

#### 4. Docking Tools (Line 1314)

**Current:**
```css
#op-metadata-detail-view-content .op-docking-tools {
    position: absolute;
    float: right;
    top: 1em;
    right: 4em;
    z-index: 999;
}
```

**Note:** This already uses `position: absolute` with `right: 4em`, so `float: right` is redundant.

**Conversion:**
```css
#op-metadata-detail-view-content .op-docking-tools {
    position: absolute;
    /* Remove: float: right; - redundant with position: absolute */
    top: 1em;
    right: 4em;
    z-index: 999;
}
```

**Testing:** Verify tool positioning in metadata detail view.

#### 5. Metadata Details Tools (Line 1407)

**Current:**
```css
.op-metadata-detail-view-body .op-metadata-details .op-metadata-details-tools {
    float: left;
}
```

**Parent Context:** `.op-metadata-details` (line 1391-1404)

**Conversion:**
```css
.op-metadata-detail-view-body .op-metadata-details {
    /* ... existing styles ... */
    display: flex;
    flex-direction: column; /* Or row, depending on layout */
}

.op-metadata-detail-view-body .op-metadata-details .op-metadata-details-tools {
    /* Remove: float: left; */
    /* Use flex order or justify-content instead */
}
```

**Testing:** Requires understanding of the layout - test carefully.

#### 6. Cart Plus Icon (Line 1444)

**Current:**
```css
.op-metadata-detail-view-body .fa-cart-plus {
    float: left;
}
```

**Parent Context:** `.op-metadata-detail-view-body .bottom` (line 1424-1442)

**Conversion:**
```css
.op-metadata-detail-view-body .bottom {
    /* ... existing styles ... */
    display: flex;
    align-items: center;
}

.op-metadata-detail-view-body .fa-cart-plus {
    /* Remove: float: left; */
    /* Flex will handle positioning */
}
```

**Testing:** Verify icon alignment in bottom toolbar.

#### 7. Cite Image (Line 1616)

**Current:**
```css
.op-cite-image {
    float: left;
    margin-right: 1rem;
}
```

**Parent Context:** `.op-cite-container` (line 1603-1606) - already uses flex!

**Conversion:**
```css
.op-cite-container {
    display: flex;
    align-items: center;
}

.op-cite-image {
    /* Remove: float: left; - parent is already flex */
    margin-right: 1rem;
}
```

**Testing:** Verify image alignment in cite container.

#### 8. Download Links Button (Line 1622)

**Current:**
```css
.op-download-links-btn {
    float: right;
    cursor: pointer;
}
```

**Parent Context:** Footer (needs investigation)

**Conversion:**
```css
/* Update parent to use flex */
footer {
    /* ... existing styles ... */
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.op-download-links-btn {
    /* Remove: float: right; */
    cursor: pointer;
    margin-left: auto; /* Pushes to right */
}
```

**Testing:** Verify button positioning in footer.

#### 9. Close Download Links History (Line 1643)

**Current:**
```css
.op-close-download-links-history {
    float: right;
    --cui-link-color: var(--cui-popover-header-color);
    --cui-link-hover-color: var(--cui-popover-header-color);
}
```

**Parent Context:** Popover footer (line 1655-1664) - already uses flex!

**Conversion:**
```css
.popover-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    /* ... */
}

.op-close-download-links-history {
    /* Remove: float: right; - parent is already flex */
    --cui-link-color: var(--cui-popover-header-color);
    --cui-link-hover-color: var(--cui-popover-header-color);
    margin-left: auto; /* Pushes to right */
}
```

**Testing:** Verify close button positioning.

#### 10. Open Help Button (Line 2645)

**Current:**
```css
.op-open-help {
    float: right;
}
```

**Parent Context:** Help panel header (needs investigation)

**Conversion:**
```css
/* Update parent */
#op-help-panel .card-header {
    display: flex;
    justify-content: space-between;
    /* Already has this at line 2779-2782 */
}

.op-open-help {
    /* Remove: float: right; - parent is already flex */
    /* Will be positioned by justify-content: space-between */
}
```

**Testing:** Verify button positioning in help panel.

---

## Additional CSS Issues

### 1. Redundant Properties

**Issue:** Some properties are set multiple times or have redundant values.

**Examples:**

1. **Line 820:** Duplicate `position` property
   ```css
   /* CURRENT */
   th.sticky-header {
       position: sticky;
       position: -webkit-sticky;
       top: 0;
   }

   /* MODERN */
   th.sticky-header {
       position: sticky;
       top: 0;
   }
   ```

2. **Lines 2521-2522, 2542-2543:** Multiple `text-align` declarations
   ```css
   /* CURRENT */
   text-align: -webkit-center;
   text-align: -moz-center;

   /* MODERN */
   text-align: center;
   ```

### 2. Inconsistent Units

**Issue:** Mix of pixels, ems, rems, and percentages. While not necessarily wrong, consistency improves maintainability.

**Recommendation:** Document unit usage patterns, but not a high priority for modernization.

### 3. Magic Numbers

**Issue:** Some hardcoded values without clear explanation.

**Examples:**
- Line 335: `width: 400em;` - Very large width, likely intentional for layout
- Line 1759: `width: calc(80% - 2rem) !important;` - Specific calculation
- Line 2605: `margin-left: 0px !important;` - Redundant `px` with `0`

**Recommendation:** Add comments explaining non-obvious values, but not critical for modernization.

### 4. Commented-Out Code

**Issue:** Some commented code that should be removed if no longer needed.

**Examples:**
- Lines 727-729: Commented transition code
- Line 1223: Commented `display:absolute;`
- Line 2092: Commented color value

**Recommendation:** Clean up commented code during modernization.

---

## HTML Template Detailed Issues

### base.html Analysis

**File:** `opus/application/apps/ui/templates/ui/base.html` (702 lines)

#### Semantic HTML Opportunities:

1. **Main Content Wrapper (Line 79):**
   - Current: `<div class="tab-content">`
   - Recommendation: `<main class="tab-content">`
   - Impact: Low - CSS selector `.tab-content` will still work

2. **Tab Panes (Lines 80, 104, 176, 285):**
   - Current: `<div id="search" class="tab-pane">`
   - Recommendation: `<section id="search" class="tab-pane" aria-label="Search">`
   - Impact: Low - ID selectors still work, improves semantics

3. **Navigation (Lines 8-77):**
   - Status: Already uses `<nav>` - Good!
   - Improvement: Ensure all nav items have proper ARIA

4. **Footer (Line 624):**
   - Status: Uses `{% include "ui/footer.html" %}`
   - Need to check footer.html for semantic structure

#### Inline Style Issues:

- Line 41: Empty `style=""` in widget.html include (line 41 in widget.html)
- No inline styles found in base.html itself - Good!

#### Accessibility:

- Good use of ARIA attributes (`role="tabpanel"`, `aria-labelledby`)
- Navigation has proper structure
- Modals have proper ARIA

### detail.html Analysis

**File:** `opus/application/apps/ui/templates/ui/detail.html` (98 lines)

#### Critical Issue - Invalid HTML:

**Lines 26-50:** Heading inside list (INVALID HTML5)

```html
<!-- CURRENT (INVALID) -->
{% for version, version_items in products.items %}
    <ul class="op-detail-list">
        <h4>Version: {{ version }}</h4>  <!-- INVALID: h4 cannot be child of ul -->
        {% for product_type, product_type_info in version_items.items %}
            <li class="op-detail-entry">
                <!-- content -->
            </li>
        {% endfor %}
    </ul>
{% endfor %}
```

**Fix Required:**
```html
<!-- OPTION 1 (Recommended) -->
{% for version, version_items in products.items %}
    <h4 class="op-version-header">Version: {{ version }}</h4>
    <ul class="op-detail-list">
        {% for product_type, product_type_info in version_items.items %}
            <li class="op-detail-entry">
                <!-- content -->
            </li>
        {% endfor %}
    </ul>
{% endfor %}

<!-- OPTION 2 (Alternative) -->
{% for version, version_items in products.items %}
    <ul class="op-detail-list">
        <li class="op-version-header-item">
            <h4>Version: {{ version }}</h4>
        </li>
        {% for product_type, product_type_info in version_items.items %}
            <li class="op-detail-entry">
                <!-- content -->
            </li>
        {% endfor %}
    </ul>
{% endfor %}
```

**CSS Addition for Option 1:**
```css
.op-version-header {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-size: 1.25rem;
    font-weight: 600;
}
```

#### Semantic HTML:

- Line 1: Already uses `<section>` - Good!
- Good use of semantic structure overall
- Proper heading hierarchy (h1 → h2 → h4, though h3 is skipped)

#### Accessibility:

- Line 74, 83: Images have proper `alt` attributes - Good!
- Proper use of ARIA where needed
- Good semantic structure

### help/templates/help/splash.html Analysis

**File:** `help/templates/help/splash.html` (minimal content)

#### Inline Styles (Lines 3-6):

```html
<!-- CURRENT -->
<td style="border:0;"><img src="{{ STATIC_URL }}img/splash-outer-planets.jpg" width=250></td>
<td style="border:0;width:100%;">
    <div style="font-size:30px;line-height:35px;text-align:center;">Welcome<br>to<br>OPUS3</div>
    <div style="font-size:10px;text-align:center;">Outer Planets Unified Search<br>10th Anniversary Edition</div>
</td>
```

**Issues:**
1. Inline styles should be in CSS
2. Missing `alt` attribute on image
3. `width=250` should be `width="250"` (quotes)

**Fix:**
```html
<td class="op-splash-image-cell">
    <img src="{{ STATIC_URL }}img/splash-outer-planets.jpg" width="250" alt="Outer planets visualization">
</td>
<td class="op-splash-content-cell">
    <div class="op-splash-title">Welcome<br>to<br>OPUS3</div>
    <div class="op-splash-subtitle">Outer Planets Unified Search<br>10th Anniversary Edition</div>
</td>
```

### help/templates/help/about.html Analysis

**File:** `help/templates/help/about.html`

#### Deprecated Attributes:

**Multiple instances of `valign="top"`:**
- Lines 69, 104, 121, 128, 134, 140, 146, 152, 190, 199

**Fix:**
```html
<!-- CURRENT -->
<td rowspan="5" valign="top">

<!-- MODERN -->
<td rowspan="5" class="op-valign-top">
```

**CSS:**
```css
.op-valign-top {
    vertical-align: top;
}
```

**Note:** `rowspan` is still valid HTML5 - no change needed.

### ui/templates/ui/widget.html Analysis

**File:** `ui/templates/ui/widget.html`

#### Inline Styles:

**Line 25:**
```html
<!-- CURRENT -->
<div class="collapse" id="card__{{ slug }}" style="display: none">
```

**Issue:** Inline style likely set by JavaScript. Should use class instead.

**Fix:**
```html
<div class="collapse op-widget-hidden" id="card__{{ slug }}">
```

**CSS:**
```css
.op-widget-hidden {
    display: none;
}
```

**JavaScript Update Needed:**
- Find where JavaScript sets `style="display: none"`
- Replace with `addClass('op-widget-hidden')` / `removeClass('op-widget-hidden')`

**Line 41:**
```html
<!-- CURRENT -->
<div class="collapse show" id="card__{{ slug }}" style="">
```

**Issue:** Empty style attribute - remove it.

**Fix:**
```html
<div class="collapse show" id="card__{{ slug }}">
```

---

## JavaScript Integration Deep Dive

### CSS Classes Used by JavaScript

**Critical Classes (Do Not Remove Without JS Updates):**

1. **State Classes:**
   - `op-in-cart` - Added/removed by cart.js (line 881, 888)
   - `op-hide-element` - Toggle visibility (cart.js line 883, 890)
   - `op-recycled` - Cart recycle bin state (cart.js line 882, 889)
   - `text-success` - Success state (cart.js line 882, 889)
   - `op-modal-show` - Modal display state
   - `op-show-msg` - Message display (opus.js line 704)
   - `op-show-spinner` - Spinner display (opus.js line 2294)
   - `op-disabled` - Disabled state (line 1476-1479)
   - `op-button-disabled` - Button disabled (line 1482-1486)
   - `op-sort-add-disabled` - Sort disabled (line 1488-1491)
   - `op-prevent-pointer-events` - Pointer events (utils.js line 60)

2. **Layout Classes:**
   - `op-gallery-view` - Gallery display mode
   - `op-data-table-view` - Table display mode
   - `op-browse-view[data-view]` - Browse view type

3. **Widget Classes:**
   - `widget__${slug}` - Widget identification
   - `range-widget`, `mult-widget` - Widget types
   - `collapsed` - Collapse state

4. **Menu Classes:**
   - `op-mark` - Selected menu item
   - `op-search-param` - Search parameter item
   - `show`, `collapsed` - Menu expansion state

**Action Required:**
- Before removing any CSS class, verify it's not used by JavaScript
- Create a comprehensive list of JS-manipulated classes
- Test JavaScript functionality after CSS changes

### Inline Style Manipulation

**Pattern to Find and Fix:**
```javascript
// BAD (if found)
$(element).css('display', 'none');
$(element).css('opacity', '0.5');

// GOOD
$(element).addClass('op-hide-element');
$(element).addClass('op-disabled');
```

**Search Strategy:**
- Search JavaScript files for `.css(` method calls
- Identify which can be moved to CSS classes
- Update JavaScript to use classes instead

---

## Implementation Priority Matrix

### High Priority (Safe, High Impact)

1. ✅ Remove vendor prefixes for universally supported properties
   - Risk: Low
   - Impact: High (code simplification)
   - Effort: Low

2. ✅ Remove IE8/IE9 specific code
   - Risk: Low
   - Impact: Medium (code cleanup)
   - Effort: Low

3. ✅ Fix invalid HTML (detail.html heading in list)
   - Risk: Low
   - Impact: High (standards compliance)
   - Effort: Low

4. ✅ Update deprecated pseudo-elements
   - Risk: Low
   - Impact: Medium (standards compliance)
   - Effort: Low

### Medium Priority (Require Testing)

5. ⚠️ Convert float layouts to flexbox
   - Risk: Medium
   - Impact: Medium (modernization)
   - Effort: Medium

6. ⚠️ Review and reduce !important usage
   - Risk: Medium-High
   - Impact: High (maintainability)
   - Effort: High (requires systematic testing)

7. ⚠️ Add semantic HTML5 elements
   - Risk: Low-Medium
   - Impact: Medium (accessibility, SEO)
   - Effort: Medium

### Low Priority (Nice to Have)

8. Remove deprecated HTML attributes
   - Risk: Low
   - Impact: Low (standards compliance)
   - Effort: Low

9. Move inline styles to CSS
   - Risk: Low
   - Impact: Low (separation of concerns)
   - Effort: Low

10. Improve accessibility attributes
    - Risk: Low
    - Impact: Medium (accessibility)
    - Effort: Medium

---

## Risk Assessment

### Low Risk Changes

- Vendor prefix removal (universally supported properties)
- IE8/IE9 code removal
- Deprecated pseudo-element updates
- HTML semantic improvements (with proper testing)
- Removing deprecated HTML attributes

### Medium Risk Changes

- Float to flexbox conversion (layout changes)
- !important removal (requires careful testing)
- CSS class name changes (must coordinate with JavaScript)

### High Risk Changes

- Major CSS restructuring
- Changing CSS that JavaScript depends on
- Modifying third-party library overrides

---

## Testing Checklist

### Visual Regression Testing

- [ ] Home/Search page
- [ ] Browse Results (gallery view)
- [ ] Browse Results (table view)
- [ ] Cart page
- [ ] Detail page
- [ ] Help panels
- [ ] Modals and dialogs
- [ ] Metadata selector
- [ ] Widgets
- [ ] Navigation menus
- [ ] Footer
- [ ] Responsive breakpoints (700px, 992px, 1200px)
- [ ] Mobile view (550px width, 270px height)

### Functional Testing

- [ ] Search functionality
- [ ] Widget interactions
- [ ] Cart add/remove
- [ ] Browse navigation
- [ ] Detail page loading
- [ ] Modal dialogs
- [ ] Dropdown menus
- [ ] Tooltips
- [ ] Form submissions
- [ ] Keyboard navigation
- [ ] Tab switching

### Cross-Browser Testing

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Accessibility Testing

- [ ] Screen reader (NVDA/JAWS)
- [ ] Keyboard-only navigation
- [ ] Focus indicators
- [ ] ARIA labels
- [ ] Color contrast
- [ ] Heading hierarchy

### Performance Testing

- [ ] CSS file size (before/after)
- [ ] Page load time
- [ ] Render performance
- [ ] Animation smoothness

---

## Estimated Impact

### Code Reduction

- **Vendor Prefixes:** ~191 lines can be simplified
- **Deprecated Properties:** ~15 lines can be removed
- **Commented Code:** ~5-10 lines can be cleaned up
- **Total:** ~200+ lines of code simplification

### Maintainability Improvements

- Cleaner, more standard CSS
- Easier to understand code
- Better browser compatibility (removing old hacks)
- Improved accessibility
- Better semantic HTML structure

### Potential Issues

- JavaScript dependencies on CSS classes (mitigated by testing)
- Third-party library compatibility (test thoroughly)
- Responsive design breakpoints (test all breakpoints)

---

## Conclusion

The OPUS codebase contains significant opportunities for CSS and HTML modernization. The majority of issues are straightforward to fix (vendor prefix removal, deprecated properties) with low risk. Some changes (float to flexbox, !important reduction) require more careful testing but offer substantial maintainability benefits.

**Recommended Approach:**
1. Start with low-risk, high-impact changes (vendor prefixes, IE code removal)
2. Progress to medium-risk changes with thorough testing
3. Document all changes and test incrementally
4. Maintain backward compatibility throughout

**Key Success Factors:**
- Comprehensive testing at each step
- Coordination between CSS and JavaScript changes
- Documentation of dependencies
- Incremental implementation

This modernization will result in cleaner, more maintainable code that follows current web standards while preserving all existing functionality.
