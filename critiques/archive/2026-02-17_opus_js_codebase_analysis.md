# Codebase Analysis: opus/application/static_media/js

## Summary

The OPUS JavaScript front end is a single-page application written in vanilla ES6 JavaScript with heavy jQuery dependency. It consists of 14 source files (~9,500 lines total) organized around UI areas (Search, Browse, Cart, Detail) using a namespace-object pattern with global variables. The codebase has **no tests, no module system, no build toolchain, and no type checking**. The most critical priorities are: (1) introducing a test framework, (2) breaking apart the oversized files (`browse.js` at 3,216 lines, `widgets.js` at 1,825 lines), and (3) migrating from global-variable namespaces toward ES modules.

## 1. Structure and Layout

- **Finding**: Files are organized by UI area, which is a reasonable separation of concerns. Each file defines a single namespace object (`opus`, `o_browse`, `o_cart`, `o_hash`, `o_search`, `o_widgets`, `o_menu`, `o_detail`, `o_selectMetadata`, `o_sortMetadata`, `o_utils`, `o_mutationObserver`) plus two utility files (`dictionary.js`, `stringUtils.js`). **Evidence**: Directory listing and `README.md`. **Suggestion**: The organization is sound at a high level; maintain the domain-area separation when modularizing.

- **Finding** (High): Several files vastly exceed the recommended ~500-1,000 line limit. `browse.js` is **3,216 lines**, `widgets.js` is **1,825 lines**, `opus.js` is **1,515 lines**, `search.js` is **1,302 lines**, `hash.js` is **827 lines**, `cart.js` is **972 lines**, `selectMetadata.js` is **557 lines**. **Evidence**: Line counts of each file. **Suggestion**: Split the largest files. For example, `browse.js` mixes gallery rendering, table rendering, infinite scroll management, metadata detail modal management, slider handling, and context menu handling — each could be its own module.

- **Finding** (Medium): `stringUtils.js` modifies `String.prototype` globally by adding a `toTitleCase` method. This is a risky pattern that could conflict with other libraries or future native additions. **Evidence**: `stringUtils.js:1-35`. **Suggestion**: Convert to a standalone utility function (e.g., `toTitleCase(str)`) rather than augmenting the native prototype.

- **Finding** (Medium): `dictionary.js` also modifies `String.prototype` by adding `replacei` via `Object.defineProperty`. Additionally, `dictionary.js` uses standalone functions (`removeSpecialChars`, `postContents`, `buildDefinitionListHTML`, `searchDictionary`) rather than a namespace object, which is inconsistent with the rest of the codebase. **Evidence**: `dictionary.js:9-14` and `dictionary.js:16-74`. **Suggestion**: Wrap dictionary functions in a namespace object or module for consistency; replace the prototype extension with a utility function.

- **Finding** (Low): Duplicated variables and structures between `o_browse` and `o_cart`. Both define `tableScrollbar`, `galleryScrollbar`, `reloadObservationData`, `metadataDetailEdit`, `observationData`, `totalObsCount`, `cachedObservationFactor`, `maxCachedObservations`, `galleryBoundingRect`, `gallerySliderStep`, `lastMetadataDetailOpusId`, `loadDataInProgress`, and `infiniteScrollLoadInProgress`. Code comments acknowledge this: `"these vars are common w/o_cart"` and `"these vars are common w/o_browse"`. **Evidence**: `browse.js:16-61`, `cart.js:47-91`. **Suggestion**: Extract shared state into a common module or base object to eliminate duplication.

## 2. Best Practices Alignment

- **Finding** (High): All namespace objects are declared as global `var` variables with `jshint varstmt: false` / `jshint varstmt: true` workarounds to suppress the linter warning. There is no ES module system (`import`/`export`) in use. All inter-file dependencies rely on script load order and global scope. **Evidence**: Every file uses the pattern `/* jshint varstmt: false */ var o_xxx = { /* jshint varstmt: true */`. **Suggestion**: Migrate to ES modules with a bundler (e.g., Vite, Webpack, or esbuild). This would eliminate globals, enable tree-shaking, and allow proper dependency management.

- **Finding** (High): Heavy use of magic numbers and strings scattered throughout the code. Examples: `opus.spinnerDelay: 250`, `opus.searchChangeDelay: 1000`, `opus.minimumPSLength: 30`, `opus.galleryAndTablePSLength: 100`, `opus.tooltipsMaxWidth: 680`, `opus.browserThresholdWidth: 700`, `cartLeftPaneThreshold: 1100`, `cartLeftPaneMinHeight: 460`, `downloadLinksPBMaxHeight: 200`, `infiniteScrollUpThreshold: 100`, `galleryAndTableTooltipsDelay: 1000`, `metadataModalHeightBreakPoint: 400`, `gapBetweenBottomEdgeAndMetadataModal: 55`, and pixel values like `40`, `25`, `500`, `200` in calculations. **Evidence**: Various files; e.g., `opus.js:31-44`, `cart.js:11-17`, `browse.js:10-11`. **Suggestion**: Consolidate all configuration constants into a dedicated config object or module.

- **Finding** (Medium): `==` (loose equality) is used in several places instead of `===`. **Evidence**: `dictionary.js:26,50,80,86,99`, `menu.js:99`, `detail.js:78`, `browse.js:1856,1858`, `widgets.js:1074`, `sortMetadata.js:96`. **Suggestion**: Use strict equality (`===`) consistently; enable an ESLint rule to enforce this.

- **Finding** (Medium): Many functions accept boolean parameters (`resetMetadata=false`, `hideHintsForNonSelectedRadioButtons=false`, `useFieldUniqueIDs=false`, `removeSpinner=false`, `leaveStartObs`, etc.) which hurts readability at call sites. **Evidence**: `opus.js:595`, `search.js:893,1002`, `hash.js:18`, and many others. **Suggestion**: Prefer options objects for boolean parameters per the JS best practices rule, especially when there are multiple boolean flags.

- **Finding** (Medium): HTML is constructed via string concatenation throughout the codebase, creating XSS risk and making the code hard to maintain. **Evidence**: `browse.js:1906-1953` (gallery HTML), `cart.js:26-42` (popover templates), `widgets.js:1336-1351` (input icons), `detail.js:63-68,79-84`, `search.js:983-994`. **Suggestion**: Use template literals with proper escaping, or adopt a lightweight templating approach. Consider sanitizing any user-derived values inserted into HTML.

- **Finding** (Low): `console.error` is used directly in the global AJAX error handler (`opus.js:1487-1498`) and in `opus.logError`. The `opus.logError` function is gated behind `opus.debug` but `console.error` in the AJAX handler is not. **Evidence**: `opus.js:146-150,1487-1498`. **Suggestion**: Route all error output through `opus.logError` or a structured logging utility.

## 3. Types and Static Checks

- **Finding** (High): There are **no TypeScript annotations, JSDoc type annotations, or type-checking tools** configured. The codebase uses JSHint directives (ES6 mode) for basic linting, but no ESLint, Prettier, or TypeScript. **Evidence**: Every file starts with `/* jshint esversion: 6 */` directives; no `tsconfig.json`, `.eslintrc`, or `prettier` config found. **Suggestion**: Introduce ESLint with a standard config (e.g., `eslint:recommended` + `plugin:jquery/recommended`). Consider adding JSDoc annotations incrementally, starting with the public API functions.

- **Finding** (Medium): Functions frequently accept and return values with implicit, undocumented types. For example, `o_hash.getSelectionsExtrasFromHash()` returns `[undefined, undefined]` or `[selections, extras]` — the caller must know this is a 2-element array. `o_utils.areObjectsEqual` claims to compare "objects whose values are all arrays" but this contract is only in a comment. **Evidence**: `hash.js:413-481`, `utils.js:20-41`. **Suggestion**: Add JSDoc type annotations to all public functions.

- **Finding** (Low): Some JSHint `/* globals */` declarations are inconsistent. For instance, `opus.js` declares `o_mutationObserver` as a global, but `mutationObserver.js` uses `/* exported o_mutationObserver */` rather than being consumed via import. `bootstrap` is declared as a global in `search.js` and `widgets.js` but not in a centralized way. **Evidence**: Top of each file. **Suggestion**: Centralize global declarations or, better, migrate to ES modules.

## 4. Testing

- **Finding** (Critical): There are **zero tests** for any of the JavaScript code. The `README.md` itself acknowledges this: `"#Todo This needs tests!"`. **Evidence**: `README.md:7`, no test files in the directory. **Suggestion**: Introduce a test framework (e.g., Vitest or Jest with jsdom). Start with unit tests for pure logic functions (`o_utils.areObjectsEqual`, `o_utils.addCommas`, `o_hash.encodeSlugValue`, `o_hash.decodeSlugValues`, `o_hash.convertSlugForSorting`, `o_utils.getSlugOrDataWithoutCounter`, `o_utils.getSurfacegeoTargetSlug`, `stringUtils.toTitleCase`). Then add integration tests for key workflows (hash parsing, search change flow, cart operations).

## 5. Performance and Resource Use

- **Finding** (Medium): Excessive jQuery selector re-evaluation. The same selectors are queried repeatedly within functions without caching. For example, in `o_search.compareInputWithRangesInfo` (search.js:736-835), selectors like `$(\`#${collapsibleContainerId}\`)` and `$(\`a.dropdown-item[href*="${collapsibleContainerId}"]\`)` are called multiple times per iteration of a loop. **Evidence**: `search.js:761-812`, `browse.js` (throughout `renderGalleryAndTable`). **Suggestion**: Cache jQuery selector results in local variables when used more than once within a function or loop.

- **Finding** (Medium): HTML string building via concatenation in `renderGalleryAndTable` (`browse.js:1841-2056`) builds the entire gallery and table HTML in memory as strings, then inserts via `.append()`. For large result sets, this can be slow and cause layout thrashing. **Evidence**: `browse.js:1853-1963`. **Suggestion**: Consider using `DocumentFragment` or batched DOM insertion. For very large datasets, consider virtual scrolling.

- **Finding** (Medium): Every search change triggers multiple sequential AJAX calls (`allNormalizeInputApiCall` → `getResultCount` → `updateSearchTabHinting` → individual `getHinting` calls per widget). These are chained via jQuery promises but could benefit from batching or parallelization where the backend supports it. **Evidence**: `opus.js:320` (`o_search.allNormalizeInputApiCall().then(opus.getResultCount).then(opus.updateSearchTabHinting)`). **Suggestion**: Investigate whether the backend can batch hinting requests; at minimum, the individual `getHinting` calls per widget (search.js:402-408) already run in parallel via `$.each`.

- **Finding** (Low): `o_utils.deepCloneObj` uses `JSON.parse(JSON.stringify(obj))` for deep cloning. This is functional but fails on `undefined` values, `Date` objects, `RegExp`, functions, and circular references. The comment acknowledges the limitation. **Evidence**: `utils.js:115-117`. **Suggestion**: Use `structuredClone()` (available in modern browsers) for safer deep cloning.

- **Finding** (Low): Multiple `MutationObserver` instances are created in `o_mutationObserver.observePerfectScrollbar()` — approximately 15 observers watching various DOM nodes. Each fires debounced callbacks. While necessary for the PerfectScrollbar integration, this is a significant source of overhead. **Evidence**: `mutationObserver.js:15-346`. **Suggestion**: Consider consolidating observers where possible, or evaluate whether PerfectScrollbar can be replaced with native CSS `overflow: auto` with modern scrollbar styling.

## 6. Maintainability and Extensibility

- **Finding** (High): Tight coupling between all modules via global state. Nearly every module reads and writes `opus.selections`, `opus.extras`, `opus.prefs`, `opus.widgetsDrawn`, `opus.inputFieldsValidation`, and other properties on the global `opus` object. There is no encapsulation or interface boundary. **Evidence**: All files reference `opus.*` extensively. **Suggestion**: Introduce a centralized state management approach. Even a simple pub/sub event system would reduce direct coupling. The `README.md` itself suggests `"a redux that incorporates a framework (such as REACT) would provide easier testing"`.

- **Finding** (High): The `browse.js` file contains an extremely complex `addBrowseBehaviors` function (lines 67-687, ~620 lines) that registers dozens of event handlers in a single method. This makes it very difficult to understand, test, or modify individual behaviors. **Evidence**: `browse.js:67-687`. **Suggestion**: Break `addBrowseBehaviors` into smaller, focused functions, each registering handlers for a specific feature (e.g., `addGalleryClickBehaviors`, `addTableClickBehaviors`, `addSliderBehaviors`, `addKeyboardBehaviors`, `addMetadataModalBehaviors`).

- **Finding** (Medium): No separation between data/state management and DOM manipulation. Functions like `o_search.addSearchBehaviors` (search.js:63-524) mix event handler registration, AJAX calls, DOM queries, state updates, and UI rendering in a single monolithic method. **Evidence**: `search.js:63-524`. **Suggestion**: Separate concerns: have data functions that manage state, and rendering functions that update the DOM based on state changes.

- **Finding** (Medium): The SURFACEGEO target-switching logic in `widgets.js` (lines 125-209) is extremely complex, performing in-place DOM attribute updates, selections/extras mutations, metadata column updates, and widget array rewriting all in one event handler. **Evidence**: `widgets.js:125-209`. **Suggestion**: Extract SURFACEGEO handling into its own module with clearly defined steps.

- **Finding** (Low): Comments are generally helpful and explain intent well. The `README.md` provides a good architectural overview. However, some comments are stale or informal (e.g., `"// ouch:"` in `widgets.js:1088`, `"// DEBBY"` in `browse.js:1907`, `"// XXX WHY IS THIS A FUNCTION?"` in `widgets.js:1037`, `"// XXX This entire function needs review and help"` in `widgets.js:1052`). **Evidence**: Various files. **Suggestion**: Remove or resolve informal/stale comments; convert `XXX` and `DEBBY` markers to tracked issues.

## 7. Security and Robustness

- **Finding** (High): HTML is built from data values without escaping, creating potential XSS vectors. User-controlled values (like `opusId`, tooltip content, notification HTML, search results) are interpolated directly into HTML strings. **Evidence**: `browse.js:1900-1945` (gallery HTML with `opusId`, `alt_text`, image URLs), `opus.js:999` (`$("#op-notification-modal .modal-body").html(html)`), `opus.js:1113` (help panel content from AJAX), `cart.js:422` (download link filename inserted into HTML). **Suggestion**: Sanitize all server-returned HTML before inserting via `.html()`. Use `.text()` instead of `.html()` where HTML rendering is not needed. For HTML construction, use DOM APIs or a templating library that auto-escapes.

- **Finding** (Medium): The global AJAX error handler (`opus.js:1487-1498`) extracts error content from the server response using a regex match on HTML (`responseText.match(/<div id="info">([\s\S]*?)<\/div>/m)[1]`). If the server returns unexpected HTML, this will throw an uncaught error (accessing `[1]` of `null`). **Evidence**: `opus.js:1489`. **Suggestion**: Add a null check on the regex match result; wrap in try/catch.

- **Finding** (Medium): Cookie values are set with very long expiry (`{expires: 1000000}` — approximately 2,740 years). **Evidence**: `opus.js:1450` (`$.cookie("visited", opus.splashVersion, {expires: 1000000})`), `opus.js:951`. **Suggestion**: Use reasonable expiry values; consider whether cookies are the right mechanism (localStorage might be more appropriate for preferences).

- **Finding** (Low): `document.execCommand('copy')` is used as a fallback in `o_detail.copyToClipboard` (detail.js:165-191). This API is deprecated. **Evidence**: `detail.js:183`. **Suggestion**: The `navigator.clipboard.writeText` path is already implemented as the primary; consider removing the deprecated fallback or adding a user notification that copy is not supported.

## 8. Dependencies and Tooling

- **Finding** (High): There is **no build system, bundler, or package manager** for the JavaScript code. Scripts are loaded via `<script>` tags in a specific order (implied by the `/* globals */` declarations). Dependencies include jQuery, jQuery UI, Bootstrap 5, PerfectScrollbar, Lodash (underscore), Tooltipster, jQuery Cookie, Colorbox, Flexslider, and infinite-scroll — all presumably loaded as separate `<script>` tags. **Evidence**: `/* globals $, _, PerfectScrollbar, bootstrap */` across all files; no `package.json`, `webpack.config.js`, or similar. **Suggestion**: Introduce a package manager (`npm`) and a bundler (Vite recommended for simplicity). This enables dependency version management, tree-shaking, minification, and source maps.

- **Finding** (Medium): JSHint is used for linting but is largely superseded by ESLint in the modern ecosystem. JSHint lacks many useful rules (no-unused-vars, consistent-return, etc.) and doesn't support plugins for jQuery or framework-specific patterns. **Evidence**: `/* jshint ... */` directives at the top of every file. **Suggestion**: Replace JSHint with ESLint; configure rules matching the project's JS best practices.

- **Finding** (Low): No minification or source mapping is in place. The JavaScript files are served as-is, which increases page load time and exposes source code. **Evidence**: Files are plain `.js` without `.min.js` counterparts. **Suggestion**: Add a build step that produces minified, source-mapped bundles for production.

## 9. Technical Debt and Risk

- **Finding** (Critical): The `README.md` explicitly calls out the need for tests and a framework migration: `"#Todo This needs tests! Also a redux that incorporates a framework (such as REACT) would provide easier testing and for a lot of this custom re-rendering code to be thrown away."` This is a long-standing acknowledged debt item. **Evidence**: `README.md:7`. **Suggestion**: Create a phased migration plan. Phase 1: Add tests for pure functions and critical paths. Phase 2: Introduce ES modules and a bundler. Phase 3: Incrementally adopt a component framework for new UI features.

- **Finding** (High): Complexity hotspots that are difficult to maintain or debug:
  - `o_hash.getHashStrFromSelections()` (hash.js:18-214, ~196 lines) — single function handling all selection/extras serialization with deeply nested conditionals.
  - `o_hash.alignDataInSelectionsAndExtras()` (hash.js:686-782, ~96 lines) — complex array alignment logic.
  - `o_widgets.getWidget()` (widgets.js:1172-1484, ~312 lines) — a single function that fetches, renders, configures, and initializes a widget.
  - `o_browse.addBrowseBehaviors()` (browse.js:67-687, ~620 lines) — a single function registering all browse tab behaviors.
  - `o_browse.renderGalleryAndTable()` (browse.js:1841-2056, ~215 lines) — HTML string building and DOM insertion.
  - `o_browse.realignDOMAndGetStartObsAndScrollbarObsNum()` (browse.js:958-1076, ~118 lines) — complex scrollbar/DOM alignment math.
  **Suggestion**: Refactor each into smaller, well-named functions with clear single responsibilities.

- **Finding** (Medium): Several TODO/FIXME markers and informal notes remain in the code:
  - `"// XXX WHY IS THIS A FUNCTION?"` — `widgets.js:1037`
  - `"// XXX This entire function needs review and help"` — `widgets.js:1052`
  - `"// DEBBY"` — `browse.js:1907`
  - `"/* NOT YET IMPLEMENTED */"` — `browse.js:342`
  - `"// Leave comments here, need to revisit this later"` — `hash.js:450,647`
  - `"// NOTE: We need support both RANGE & STRING inputs, for now we implement RANGE first."` — `widgets.js:219`, `search.js:252`
  **Suggestion**: Convert each to a tracked GitHub issue; remove or resolve informal markers.

- **Finding** (Medium): Browser compatibility checking (`opus.checkBrowserSupported`, opus.js:1249-1395) uses manual User Agent string parsing with hardcoded version numbers. This is fragile and requires ongoing maintenance. **Evidence**: `opus.js:1249-1395`. **Suggestion**: Consider feature detection instead of UA sniffing; or use a library like `bowser` if UA detection is truly needed. Update the minimum supported versions to reflect current browser landscape.

- **Finding** (Low): The `toTitleCase` function in `stringUtils.js` contains a very large hardcoded array of science-domain-specific acronym capitalization rules (~200 entries). **Evidence**: `stringUtils.js:18-29`. **Suggestion**: Move this lookup table to a configuration file or data source that can be updated without code changes.

## Recommended Priorities

1. **Introduce testing** (Critical) — Set up Vitest or Jest with jsdom; write unit tests for all pure utility functions (`o_utils`, `o_hash` encoding/decoding, `stringUtils`). This is the single highest-impact improvement for long-term maintainability.

2. **Adopt ES modules and a bundler** (High) — Introduce `npm` + Vite (or similar). Migrate one file at a time from global `var` to `export`/`import`. This eliminates global coupling, enables proper dependency management, and unblocks all other modernization.

3. **Split oversized files** (High) — Break `browse.js`, `widgets.js`, and `opus.js` into focused modules of 300-500 lines each. Extract `addBrowseBehaviors` sub-handlers, split `getWidget` into fetch/render/configure steps, separate gallery from table rendering.

4. **Replace JSHint with ESLint** (Medium) — Configure ESLint with `eslint:recommended` plus jQuery and strict-equality rules. Add Prettier for formatting. This catches bugs that JSHint misses and enforces consistent style.

5. **Sanitize HTML construction** (High) — Audit all `.html()` calls and string-built HTML for XSS vectors. Introduce an escaping utility or templating approach for dynamically constructed HTML.

6. **Add JSDoc type annotations** (Medium) — Start with public API functions in `o_hash`, `o_utils`, and `opus`. This improves IDE support and serves as living documentation.

7. **Extract shared state** (Medium) — Create a shared state/config module for variables duplicated between `o_browse` and `o_cart`, and for the many configuration constants scattered across files.

8. **Resolve TODOs and stale comments** (Low) — Convert `XXX`, `DEBBY`, `NOT YET IMPLEMENTED`, and similar markers to tracked issues; clean up stale comments.
