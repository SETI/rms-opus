/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $, _, PerfectScrollbar */
/* globals o_browse, o_cart, o_detail, o_hash, o_menu, o_selectMetadata, o_sortMetadata, o_mutationObserver, o_search, o_utils, o_widgets, FeedbackMethods */
/* globals DEFAULT_COLUMNS, DEFAULT_WIDGETS, DEFAULT_SORT_ORDER, STATIC_URL, PREVIEW_GUIDES */

// defining the opus namespace first; document ready comes after...
/* jshint varstmt: false */
var opus = {
/* jshint varstmt: true */


    /**
     *
     *  global declarations here
     *
     **/

    // Default vars are found in the apps/ui/templates/header.html template
    // and declared in settings.py

    // Constants
    spinner: '<img border = "0" src = "' + STATIC_URL + 'img/spinner_12px.gif">',
    debug: true,

    // Minimum height of any scrollbar
    minimumPSLength: 30,
    // Fixed scrollbar length for gallery & table view
    galleryAndTablePSLength: 100,

    qtypeRangeDefault: "any",
    qtypeStringDefault: "contains",

    defaultColumns: DEFAULT_COLUMNS.split(","),
    defaultWidgets: DEFAULT_WIDGETS.split(","),

    searchChangeDelay: 1000, // How long to wait after a search changes to do the new search
    spinnerDelay: 250, // The amount of time to wait before showing a spinner in case the API returns quickly

    // avoiding race conditions in ajax calls
    lastAllNormalizeRequestNo: 0,
    lastResultCountRequestNo: 0,

    // An object stores the input (slug) & boolean value to indicate whether the normalize input
    // API (for all fields) is in progress:
    // Key: input slug that triggers the normalize input API call. (Use opus.allSlug for API from getResultCount)
    // Value: true & false to indicate whether the API is in progress.
    normalizeInputForAllFieldsInProgress: {},
    // An object stores the input (slug) & boolean value to indicate whether the normalize input
    // API (for a character) is in progress:
    // Key: input slug that triggers the normalize input API call. (Use opus.allSlug for API
    // from getResultCount)
    // Value: true & false to indicate whether the API is in progress.
    normalizeInputForCharInProgress: {},
    // The key in normalizeInputForAllFieldsInProgress, normalizeInputForCharInProgress, or
    // object. It will store the info of the normalize input API call triggered from
    // o_search.allNormalizeInputApiCall() (not from any specific input).
    allSlug: "all",
    // Record the current unit selections for widgets.
    currentUnitBySlug: {},

    lastLoadDataRequestNo: { "cart": 0, "browse": 0 },

    // client side prefs, changes to these *do not trigger results to refresh*
    // prefs key:value pair order has been re-organized to match up with normalized url
    prefs: {
        "cols": DEFAULT_COLUMNS.split(","),     // default selected metadata by slug
        "widgets": [],                          // search tab open widgets
        "order": DEFAULT_SORT_ORDER.split(","), // results sort order
        "view": "search",                       // selected tab: search, browse, cart, detail
        "browse": "gallery",                    // browsing mode: gallery or data (table)
        "cart_browse": "gallery",               // cart mode: gallery or data (table)
        "startobs": 1,                          // top-left obs for browse tab
        "cart_startobs": 1,                     // top-left obs for cart tab
        "detail": "",                           // opus_id of detail page content
    },

    colLabels: [],  // contains labels that match prefs.cols, which are slugs for each column label
                    // note that this is also not a dictionary because we need to preserve the order.
    colLabelsNoUnits: [], // store labels without units (similar to data in colLabels but no units)

    // searching - making queries
        // NOTE: Any changes to selections or extras will trigger load() to refresh
        // the result count, hints, etc. after a suitable delay
    selections: {},        // the user's search
    extras: {},            // extras to the query: qtypes
    lastSelections: {},    // lastXXX are used to monitor changes
    lastExtras: {},
    searchChangeTimer: null, // The timer used to trigger a new search

    // An object that stores normalizeinput validation result for each input.
    inputFieldsValidation: {},

    // Remember nav clicks during normalize input so we can actually process them
    // later if the inputs are valid.
    navLinkRemembered: null,

    force_load: true, // set this to true to force load() when selections haven't changed

    // searching - ui
    widgetsDrawn: [], // keeps track of what widgets are actually drawn
    widgetsFetching: [], // this widget is currently being fetched
    widgetElementsDrawn: [], // the element is drawn but the widget might not be fetched yet

    // opusID of the current slide show/gallery view observation.
    // Note that both browse and cart use the same dialog for op-metadata-detail-view, so we
    //      only need one variable to represent the last observation in that dialog
    metadataDetailOpusId: "",

    // store the browser version and width supported by OPUS
    browserSupport: {
        "firefox": 64,
        "chrome": 56,
        "chrome (ios)": 56,
        "opera": 42,
        "safari": 10.1,
        "edge": 83,
        "based on applewebkit": 537, // Based on Chrome 56
        "width": 550,
        "height": 270
    },

    // current splash page version for storing in the visited cookie
    splashVersion: 1,

    // Used by checkBrowserSize
    browserSizeActionInProgress: false,

    currentBrowser: "",

    // Max number of input sets per (RANGE or STRING) widget
    maxAllowedInputSets: 10,

    // The browser threshold width & height that font & thumbnail size start to shirnk.
    // NTOE: These two variables have to match the breakpoints in mobile support section in opus.css.
    browserThresholdWidth: 700,
    browserThresholdHeight: 400,

    //------------------------------------------------------------------------------------
    // Debugging support
    //------------------------------------------------------------------------------------
    logError: function(...args) {
        if (opus.debug) {
            console.error("ERROR:", ...args);
        }
    },

    oldSurfacegeoTarget: null,

    //------------------------------------------------------------------------------------
    // Functions to update the result count and hinting numbers on any change to the search
    //------------------------------------------------------------------------------------

    load: function() {
        /**
         * This function is called whenever the search changes and a given time
         * delay is exceeded. It checks to see if the selections or extras have
         * changed since the last call. (Even if a change timer has been
         * triggered, it's possible the user changed those parameters back again
         * before the timer fired, in which case we don't need to do a search.)
         * If either has changed, or opus.force_load is true, then it starts the
         * chain of
         * 1) Check inputs for validity
         * 2) Perform the search and get the result count
         * 3) Update the result count badge(s)
         * 4) Get hinting information and update all hints
         */

        opus.stopSearchChangeTimer();

        let [selections, extras] = o_hash.getSelectionsExtrasFromHash();

        // Align data in opus.selections and opus.extras to make sure empty
        // inputs will also have null in opus.selections
        [opus.selections, opus.extras] = o_hash.alignDataInSelectionsAndExtras(opus.selections,
                                                                               opus.extras);

        // Note: When URL has an empty hash, both selections and extras returned from
        // getSelectionsExtrasFromHash will be undefined. There won't be a case when only
        // one of them is undefined.
        if (selections === undefined) {
            // safety check, the if condition should never be true
            if (extras !== undefined) {
                console.error("Returned extras is not undefined when URL has an empty hash");
            }
            return;
        }

        // Enable or disable the 'Reset Search' and 'Reset Search and Metadata buttons'.
        // There is a potential bug here if the list of default widgets ever includes a widget
        // with a qtype, because then the user could change the qtype value in extras and it
        // wouldn't change the state of the reset buttons. This isn't a problem now, though.
        if (!$.isEmptyObject(selections) || !opus.isDrawnWidgetsListDefault()) {
            $(".op-reset-button button").prop("disabled", false);
        } else if (!opus.isMetadataDefault()) {
            $(".op-reset-button .op-reset-search-metadata").prop("disabled", false);
            $(".op-reset-button .op-reset-search").prop("disabled", true);
        } else {
            $(".op-reset-button button").prop("disabled", true);
        }

        // If we're coming in from a URL, we want to leave startobs and cart_startobs
        // alone so we are using the values in the URL.
        let leaveStartObs = true;

        // Compare selections and last selections, extras and last extras to see if anything
        // has changed that would require an update to the results. We ignore q-types and units for
        // search fields that aren't actually being searched on because when the user changes
        // such a q-type or unit, there's no point in redoing the search since the results will be
        // identical.
        let currentExtrasQ = o_hash.extrasWithoutUnusedQtypesUnits(selections, extras);
        let lastExtrasQ = o_hash.extrasWithoutUnusedQtypesUnits(opus.lastSelections, opus.lastExtras);
        if (o_utils.areObjectsEqual(selections, opus.lastSelections) &&
            o_utils.areObjectsEqual(currentExtrasQ, lastExtrasQ)) {
            if (!opus.force_load) {
                return;
            }
            // Everything is the same but force_load is true; fall through to the reload
            // This happens on OPUS initialization
        } else {
            // If selections != opus.selections or extras != opus.extras,
            // it means the user manually updated the URL in the browser,
            // so we have to reload the page. We can't just continue on normally
            // because we need to re-run the URL normalization process.
            let opusExtrasQ = o_hash.extrasWithoutUnusedQtypesUnits(opus.selections, opus.extras);
            if (!o_utils.areObjectsEqual(selections, opus.selections) ||
                !o_utils.areObjectsEqual(currentExtrasQ, opusExtrasQ)) {
                // Make sure page will not reload in these cases:
                // 1) When it's in the middle of an input removal process. After normalize input API
                // call returns at the end of an input removal, URL and opus.selections will get updated
                // correctly.
                // 2) When normalize input API is in progress. URL and opus.selections will get
                // updated correctly after the return of API call.
                // 3) When there is an invalid input. If there is an invalid values, there will be a
                // mismatch between URL and opus.selections, and the invalid value in opus.selections
                // will be removed when it's removed from UI.
                // 4) When it's in the middle of an input adding process. After updateURL and opus.selections
                // will get updated correctly.
                if (o_widgets.isRemovingInput ||
                    o_widgets.isAddingInput ||
                    opus.isAnyNormalizeInputInProgress() ||
                    !opus.areInputsValid()) {
                    return;
                }

                opus.selections = selections;
                opus.extras = extras;
                location.reload();
                return;
            }

            // The selections or extras have changed in a meaningful way requiring an update
            // In this case we want to reset startobs and cart_startobs to 1
            leaveStartObs = false;
        }

        opus.force_load = false;

        // Start the result count spinner and do the yellow flash
        $("#op-result-count").html(opus.spinner).parent().effect("highlight", {}, 500);

        // Start the observation number slider spinner - no point in doing a flash here
        // and only set the spinner for the #browse tab, as changing search parameters does not affect the cart
        $("#browse .op-observation-number").html(opus.spinner);

        // Start the spinners for the left side menu and each widget for hinting
        $("#sidebar .op-menu-spinner.spinner").addClass("op-show-spinner");
        opus.widgetsDrawn.forEach(function(eachSlug) {
            if ($(`.widget__${eachSlug}`).hasClass("range-widget") ||
                $(`.widget__${eachSlug}`).hasClass("mult-widget")) {
                $(`#widget__${eachSlug} .spinner`).fadeIn();
            }
        });

        // Mark the changes as complete. We have to do this before allNormalizeInputApiCall to
        // avoid a recursive api call
        opus.lastSelections = selections;
        opus.lastExtras = extras;

        // Force the Select Metadata dialog to refresh the next time we go to the browse
        // tab in case the categories are changed by this search.
        o_selectMetadata.rendered = false;

        // Clear the gallery and table views on the browse tab so we start afresh when the data
        // returns. There's no point in clearing the cart tab since the search doesn't
        // affect what appears there.
        o_browse.clearBrowseObservationDataAndEraseDOM(leaveStartObs);

        // Update the UI in the following order:
        // 1) Normalize all the inputs and check for validity (allNormalizeInputApiCall)
        // 2) Perform the search and get the result count (getResultCount)
        // 3a) Update the result count badge(s) (updateSearchTabHinting)
        // 3b) Update all the search hinting (updateSearchTabHinting)
        // The way this is currently implemented, the result count has to finish before
        // any of the search hinting is updated. This is a good thing because of the way
        // the back end is implemented, where the result count needs to finish so the
        // cache table has been created before hinting can be performed. However, at
        // some point we would like to be able to do these in parallel. This will require
        // both backend changes and a change here to remove the sequential dependence.
        o_search.allNormalizeInputApiCall().then(opus.getResultCount).then(opus.updateSearchTabHinting);
    },

    getResultCount: function(normalizedData) {
        /**
         * Given the result of the search parameter normalization, execute the search
         * that will eventually return the result count.
         */
        // If there are more normalized data requests in the queue, don't trigger
        // spurious result counts that we won't use anyway
        if (normalizedData.reqno < o_search.lastAllNormalizeRequestNo) {
            return;
        }

        // Take the results from the normalization, check for errors, and update the
        // UI to show the user if anything is wrong. This updates the
        // opus.inputFieldsValidation and also updates the hash.
        o_search.validateInput(normalizedData, true);

        if (!opus.areInputsValid()) {
            // We don't try to get a result count if any of the inputs are invalid.
            // Remove spinning effect on browse counts and mark as unknown.
            $("#op-result-count").text("?");
            $("#browse .op-observation-number").html("?");
            delete opus.normalizeInputForAllFieldsInProgress[opus.allSlug];
            return;
        } else {
            $("#sidebar").removeClass("search_overlay");
        }

        if (opus.getCurrentTab() === "browse") {
            // The user was really quick, and switched tabs before we had a chance
            // to notice that the search parameters had changed. So they're looking at
            // old data using an old hash :-( The clearObservationDataAndEraseDOM earlier
            // will at least make them look at a blank screen, but we still need to
            // force them to reload the data now that we have updated the hash.
            // Note that things are OK if they switch tabs AFTER this point, even
            // if result_count hasn't returned, because at least the hash has been
            // updated so their call to dataimages.json will have the correct parameters.

            // Prevent loadData to call the same dataimages API twice
            if (!o_browse.loadDataInProgress) {
                o_browse.loadData(opus.getCurrentTab());
            }
        }
        delete opus.normalizeInputForAllFieldsInProgress[opus.allSlug];

        opus.changeTabToRemembered();

        // Execute the query and return the result count
        opus.lastResultCountRequestNo++;
        return $.getJSON(`/opus/__api/meta/result_count.json?${o_hash.getHash()}&reqno=${opus.lastResultCountRequestNo}`);
    },

    updateSearchTabHinting: function(resultCountData) {
        /**
         * Given the result count, update the result count badge(s) and
         * start the process to update the hints.
         */

        // We don't update the search hinting if any of the inputs are invalid.
        // The hints were previously marked as "?" in validateInput so they
        // will just stay that way.
        if (!opus.areInputsValid() || !resultCountData) {
            return;
        }

        // If there are more result counts in the queue, don't trigger
        // spurious hinting queries that we won't use anyway
        if (resultCountData.data[0].reqno < opus.lastResultCountRequestNo) {
            return;
        }

        // We have the new result count, so update the badges and the menu contents
        $("#browse_tab").fadeIn();
        opus.updateResultCount(resultCountData.data[0].result_count);

        // The side menu may have changed by adding or removing search categories,
        // so retrieve a new one.
        o_menu.getNewSearchMenu();

        // Finally, update all the hints
        $.each(opus.prefs.widgets, function(index, slug) {
            if (slug === "surfacegeometrytargetname" && !o_search.areAllSURFACEGEOSelectionsEmpty()) {
                o_search.getValidMults(slug, true);
            } else {
                o_search.getHinting(slug);
            }
        });
    },

    updateResultCount: function(resultCount) {
        /**
         * Given a new result count, update our cache value as well as all
         * badge(s).
         */

        o_browse.totalObsCount = resultCount;
        $("#op-result-count").fadeOut("fast", function() {
            $(this).html(o_utils.addCommas(o_browse.totalObsCount)).fadeIn("fast");
            $(this).removeClass("browse_results_invalid");
        });
    },

    //------------------------------------------------------------------------------------
    // Functions related to nav bar tabs and other menu items
    //------------------------------------------------------------------------------------

    triggerNavbarClick: function() {
        /**
         * Simulate a click on the nav bar tab for the current view. This is a
         * simple way to get the tab to be selected and to execute the associated
         * event code.
         */

        $('.nav-item a[href="#'+opus.prefs.view+'"]').trigger("click");
    },

    updateNotifications: function() {
        /**
         * Retrieve the date of the last blog update and update the tooltip for
         * the 'Recent Announcements' nav bar item.
         */

        $.getJSON("/opus/__notifications.json", function(data) {
            if (data.lastupdate !== null) {
                let lastUpdateDate = new Date(data.lastupdate);
                let today = Date.now();
                let days = (today - lastUpdateDate.valueOf())/1000/60/60/24;
                if (days <= 31) { // Show it for a month for infrequent users
                    $(".blogspot img").show();
                } else {
                    $(".blogspot img").hide();
                }
                let prettyDate = lastUpdateDate.toLocaleDateString('en-GB',
                                        {year: 'numeric', month: 'long', day: 'numeric'});
                $("#op-last-blog-update-date").attr("title", "Blog last updated "+prettyDate);
            } else {
                $("#op-last-blog-update-date").attr("title", "");
            }
            // note: $.cookie compare needs to be != because the cookie is a string number but cdate is a number.
            if (data.notification !== null && data.notification !== "" && $.cookie("notify") != data.notification_mdate) {
                opus.displayNotificationDialog(data.notification, data.notification_mdate);
            }
        });
    },

    changeTabToRemembered: function() {
        // If the user had clicked on a nav tab during the normalizeinput
        // process, go ahead and execute that tab switch now
        if (opus.navLinkRemembered !== null) {
            opus.prefs.view = opus.navLinkRemembered;
            opus.navLinkRemembered = null;
            opus.triggerNavbarClick();
        }
    },

    hideTawkChat: function(action) {
        $("iframe").each(function(index) {
            let elem = $(this).contents().find("div#tawkchat-minified-box");
            if (elem.length > 0) {
                if (elem.find("#minimizeChatMinifiedBtn").hasClass("hide")) {
                    elem.hide();
                }
            }
            elem = $(this).contents().find("[id^=tawkchat-chat-bubble]");
            if (elem.length > 0) {
                elem.hide();
            }
        });
    },

    showTawkChat: function(action) {
        $("iframe").each(function(index) {
            let elem = $(this).contents().find("div#tawkchat-minified-box");
            if (elem.length > 0) {
                elem.show();
            }
            elem = $(this).contents().find("[id^=tawkchat-chat-bubble]");
            if (elem.length > 0) {
                elem.show();
            }
        });
    },

    changeTab: function(tab) {
        /**
         * This is the event handler for the user clicking on one of the main nav
         * bar tabs (views).
         */

        if (opus.isAnyNormalizeInputInProgress()) {
            opus.navLinkRemembered = tab;
            return false;
        }

        opus.navLinkRemembered = null;

        if (!opus.areInputsValid()) {
            return false;
        }

        // First hide everything
        $("#search, #detail, #cart, #browse").hide();
        o_browse.hideMenus();

        // Close any open modals
        $("#op-metadata-detail-view").modal('hide');

        // Update the state with the newly selected view
        opus.prefs.view = tab ? tab : opus.prefs.view;
        o_hash.updateURLFromCurrentHash();

        // Go ahead and check to see if the blog has been updated recently
        opus.updateNotifications();

        // deselect any leftover selected text for clean slate
        document.getSelection().removeAllRanges();

        o_detail.showDetailThumbInNav();
        switch(opus.prefs.view) {
            case "search":
                window.scrollTo(0,0);
                $("#search").fadeIn();
                // Using fadeIn for the feedbackTab looks bad because fadeIn
                // uses opacity, and we're already using opacity for the text
                // and background image, so it flashes bright and then dims
                $(".feedbackTab").show();
                opus.showTawkChat();
                o_search.activateSearchTab();
                break;

            case "browse":
                $("#browse").fadeIn();
                $(".feedbackTab").hide();
                opus.hideTawkChat();
                o_browse.activateBrowseTab();
                break;

            case "detail":
                $("#detail").fadeIn();
                $(".feedbackTab").show();
                opus.showTawkChat();
                o_detail.activateDetailTab(opus.prefs.detail);
                break;

            case "cart":
                $("#cart").fadeIn();
                $(".feedbackTab").hide();
                opus.hideTawkChat();
                o_cart.activateCartTab();
                break;

            default:
                opus.logError(`changeTab got unknown view name ${opus.prefs.view}`);
                o_search.activateSearchTab();
        }

        return true;
    },

    hideHelpPanel: function() {
        /**
         * If the "Help" panel is currently open, close it.
         */
        if ($("#op-help-panel").hasClass("active")) {
            $(".op-cite-opus-btn").removeClass(".op-prevent-pointer-events");
            $("#op-help-panel").toggle("slide", {direction: "right"});
            $("#op-help-panel").removeClass("active");
            $(".op-overlay").removeClass("active");
        }
    },

    hideHelpAndCartPanels: function() {
        /**
         * If the "Help" panel or cart download panel is currently open, close it.
         */
        opus.hideHelpPanel();
        if ($("#op-cart-download-panel").hasClass("active")) {
            $("#op-cart-download-panel").toggle("slide", {direction: "left"});
            $("#op-cart-download-panel").removeClass("active");
            $(".op-overlay").removeClass("active");
        }
    },

    adjustHelpPanelHeight: function() {
        /**
         * Set the height of the "Help" panel based on the browser size.
         */
        let footerHeight = $(".footer").outerHeight();
        let mainNavHeight = $("#op-main-nav").outerHeight();
        let cardHeaderHeight = $("#op-help-panel .card-header").outerHeight();
        let totalNonGalleryHeight = footerHeight + mainNavHeight + cardHeaderHeight;
        let height = $(window).height()-totalNonGalleryHeight;
        $("#op-help-panel .card-body").css("height", height);
        if (opus.helpScrollbar) {
            // Make scrollbar always start from top
            $("#op-help-panel .card-body").scrollTop(0);
            opus.helpScrollbar.update();
        }
    },


    //------------------------------------------------------------------------------------
    // General support functions
    //------------------------------------------------------------------------------------

    handleResetButtons: function(resetMetadata=false) {
        /**
         * Handle the 'Reset Search' and 'Reset Search and Metadata' buttons.
         */

        // Reset the search query
        opus.selections = {};
        opus.extras = {};
        // Update the URL so getWidget below doesn't have old concepts of
        // what mults were selected in the default widgets.
        o_hash.updateURLFromCurrentHash(false);

        o_browse.clearObservationData();

        // Enable or disable the 'Reset Search' and 'Reset Search and Metadata' buttons
        if (!o_utils.areObjectsEqual(opus.prefs.cols, opus.defaultColumns)) {
            if (resetMetadata) {
                opus.prefs.cols = [];
                o_browse.resetMetadata(opus.defaultColumns, true);
                $(".op-reset-button button").prop("disabled", true);
            } else {
                $(".op-reset-button .op-reset-search-metadata").prop("disabled", false);
                $(".op-reset-button .op-reset-search").prop("disabled", true);
            }
        } else {
            $(".op-reset-button button").prop("disabled", true);
        }

        // Remove all previously-opened widgets
        $.each($("#op-search-widgets .widget"), function(idx, widget) {
            widget.remove();
        });

        // Reset widgets drawn back to system default
        opus.prefs.widgets = [];
        opus.widgetsDrawn = [];
        opus.widgetElementsDrawn = [];

        $.each(opus.defaultWidgets.slice().reverse(), function(index, slug) {
            o_widgets.getWidget(slug, "#op-search-widgets");
        });

        // Reload the search menu to get the proper checkmarks and categories
        o_menu.getNewSearchMenu();

        // We changed the selections so do a search, but no delay needed
        o_hash.updateURLFromCurrentHash(true, false);
    },

    isDrawnWidgetsListDefault: function() {
        /**
         * Check if the currently selected widgets are the default ones.
         */
        return o_utils.areObjectsEqual(opus.prefs.widgets, opus.defaultWidgets);
    },

    isMetadataDefault: function() {
        /**
         * Check if the currently selected metadata columns are the default ones.
         */
        return o_utils.areObjectsEqual(opus.prefs.cols, opus.defaultColumns);
    },

    getViewNamespace: function(view) {
        /**
         * Return the namespace object corresponding to the given view, or the
         * current view if none is given.
         * Default to o_browse if the view isn't one of "browse" or "cart".
         */
        view = (view === undefined ? opus.prefs.view : view);
        return (view === "cart" ? o_cart : o_browse);
    },

    getViewTab: function(view) {
        /**
         * Return the DOM ID corresponding to the given view, or the
         * current view if none is given.
         * Default to #browse if the view isn't one of "browse" or "cart".
         */
        view = (view === undefined ? opus.prefs.view : view);
        return (view === "cart" ? "#cart" : "#browse");
    },

    getCurrentTab: function() {
        /**
         * Return the current tab that the user selects
         */
        return opus.prefs.view;
    },

    //------------------------------------------------------------------------------------
    // OPUS initialization
    //------------------------------------------------------------------------------------

    normalizedURLAPICall: function() {
        /**
         * Normalize the URL given by the user and then use it to actually start OPUS.
         */

        let hash = o_hash.getHash();
        // Note: We don't need a reqno here because this API is called at the beginning of
        // document ready (or on reload), and every time this event is triggered, it means
        // everything is reloaded.
        // If we put reqno here, reqno will always be 1 anyway, so there's no point.
        let url = "/opus/__normalizeurl.json?" + hash;
        $.getJSON(url, function(normalizeURLData) {
            // Display returned message, if any, in the "you have a message" modal
            if (normalizeURLData.msg) {
                $("#op-update-url-modal .modal-body").html(normalizeURLData.msg);
                $(".op-user-msg").addClass("op-show-msg");
            }

            // Get the newURLHash array from new_slugs (data returned from api call).
            // The reason we don't use new_url directly is because some slug values might
            // contain "&", and we can't just do .split("&"). This is a more proper way
            // to get newURLHash array.
            let newSlugArr = normalizeURLData.new_slugs;
            let newURLHash = [];
            for (const slugObj of newSlugArr) {
                $.each(slugObj, function(slug, value) {
                    newURLHash.push(`${slug}=${value}`);
                });
            }
            // Encode and update new URL in browser:
            newURLHash = o_hash.encodeHashArray(newURLHash);
            newURLHash = newURLHash.join("&");
            window.location.hash = "/" + newURLHash;

            // Perform rest of initialization process
            opus.opusInitialization();
        });
    },

    addAllBehaviors: function() {
        /**
         * Add the behaviors for all the tabs.
         */

        opus.addOpusBehaviors();
        o_widgets.addWidgetBehaviors();
        o_menu.addMenuBehaviors();
        o_browse.addBrowseBehaviors();
        o_cart.addCartBehaviors();
        o_search.addSearchBehaviors();
        o_sortMetadata.addBehaviours();
        o_selectMetadata.addBehaviors();
    },

    addOpusBehaviors: function() {
        /**
         * Add the top-level behaviors that affect all of OPUS.
         */

        // When the browser is resized, we need to recalculate the scrollbars
        // for all tabs.
        let adjustBrowseHeightDB = function() {o_browse.adjustBrowseHeight(true);};
        let adjustTableSizeDB = _.debounce(o_browse.adjustTableSize, 200);
        let adjustProductInfoHeightDB = _.debounce(o_cart.adjustProductInfoHeight, 200);
        let adjustDetailHeightDB = _.debounce(o_detail.adjustDetailHeight, 200);
        let adjustHelpPanelHeightDB = _.debounce(opus.adjustHelpPanelHeight, 200);
        let adjustMetadataDetailViewSizeDB = _.debounce(o_browse.adjustMetadataDetailViewSize, 200);
        let hideOrShowSelectMetadataMenuPSDB = _.debounce(o_selectMetadata.hideOrShowMenuPS, 200);
        let hideOrShowSelectedMetadataPSDB = _.debounce(o_selectMetadata.hideOrShowPS, 200);
        let adjustMetadataDetailDialogPSDB = function() {o_browse.adjustMetadataDetailDialogPS(true);};
        let displayCartLeftPaneDB = _.debounce(o_cart.displayCartLeftPane, 200);

        $(window).on("resize", function() {
            o_search.searchHeightChanged();
            adjustBrowseHeightDB();
            adjustTableSizeDB();
            adjustProductInfoHeightDB();
            adjustDetailHeightDB();
            adjustHelpPanelHeightDB();
            adjustMetadataDetailViewSizeDB();
            o_selectMetadata.adjustHeight();
            hideOrShowSelectMetadataMenuPSDB();
            hideOrShowSelectedMetadataPSDB();
            adjustMetadataDetailDialogPSDB();
            displayCartLeftPaneDB();
            opus.checkBrowserSize();
            opus.hideOrShowSplashText();
            o_widgets.attachStringDropdownToInput();
        });

        // Support for tooltips on touch screens
        $(window).on("touchstart", function () {
            // The DOM may have changed since the last touch, so remove
            // the click handler on the remaining tooltip elements and then
            // add it to all of them. This way we don't end up with duplicate
            // handlers.
            $("i[title]").off("click", opus.tooltipClickHandler);
            $("i[title]").on("click", opus.tooltipClickHandler);
        });

        // Add the navbar clicking behaviors, selecting which tab to view
        $("#op-main-nav").on("click", ".op-main-site-tabs .nav-item", function() {
            if ($(this).hasClass("external-link") || $(this).children().hasClass("op-show-msg")) {
                // this is a link to an external site or a link to open up a message modal
                return true;
            }

            // find out which tab they clicked
            let tab = $(this).find("a").attr("href").substring(1);
            if (tab == '/') {
                return true;  // they clicked the brand icon, take them to its link
            }

            // little hack in case something calls onclick programmatically
            tab = tab ? tab : "search";
            return opus.changeTab(tab);
        });

        $(".op-help-item").on("click", function(e) {
            // prevent url hash from being changed to # (in a tag href)
            e.preventDefault();
            opus.displayHelpPane($(this).data("action"));
        });

        // Clicking on the "X" in the corner of the help pane
        $("#op-help-panel .close, .op-overlay").on("click", function() {
            opus.hideHelpAndCartPanels();
            return false;
        });

        // Behavior for help submenu
        $("#op-help .dropdown-submenu .dropdown-item").on("click", function(e) {
            $(this).next(".dropdown-menu").toggle("show");
            e.stopPropagation();
        });

        // Click on items inside submenu, we execute something and close the whole dropdown.
        $("#op-help .dropdown-submenu .op-submenu-item").on("click", function(e) {
            let submenuItem = $(this);
            opus.displayHelpPane(submenuItem.data("action"));
            submenuItem.parents(".dropdown-menu").removeClass("show");
            e.stopPropagation();
        });

        // When the parent dropdown is closed, make sure submenu is closed.
        $("#op-help").on("hidden.bs.dropdown", function(e) {
            $(".op-interpret-image").hide();
        });

        // Clicking on either of the Reset buttons
        $(".op-reset-button button").on("click", function() {
            let targetModal = $(this).data("target");

            if (!$.isEmptyObject(opus.selections) || !opus.isDrawnWidgetsListDefault()) {
                $(targetModal).modal("show");
            } else if (targetModal === "#op-reset-search-metadata-modal" && !opus.isMetadataDefault()) {
                $(targetModal).modal("show");
            }
        });

        // Clicking on the OPUS3 logo
        $(".op-reset-opus").on("click", function() {
            $("#op-reset-opus-modal").modal("show");
        });

        $(document).on("keydown click", function(e) {
            if ((e.which || e.keyCode) == 27) {
                // ESC key - close modals and help panel
                // Don't close "#op-browser-version-msg-modal" and "#op-browser-size-msg-modal"
                $.each($(".op-confirm-modal"), function(idx, confirmModal) {
                    if ($(confirmModal).data("action") === "esc") {
                        $(confirmModal).modal("hide");
                    }
                });
                opus.hideHelpAndCartPanels();
                FeedbackMethods.close();
            }
        });

        $(".op-confirm-modal").on("show.bs.modal", function (e) {
            let modal = $(this).attr("id");
            switch (modal) {
                case "op-empty-cart-modal":
                    let emptyCartModalMsg = "";
                    if (o_cart.recycledCount !== undefined && o_cart.recycledCount > 0) {
                        emptyCartModalMsg = "Are you sure you want to remove all observations from the cart" +
                                            "and the recycle bin?";
                    } else {
                        emptyCartModalMsg = "Are you sure you want to remove all observations from the cart?";
                    }
                     $("#op-empty-cart-modal .modal-body").text(emptyCartModalMsg);
                    break;
                case "op-addall-to-cart-modal":
                    // Note: If we use `` for string concatenation in html text, text will split into
                    // multiple lines in html, but stay in one line in UI. Use "+" here can make
                    // sure text stays in one line in both html and UI, just looks cleaner (in html).
                    let addAllmodalMsg = "Are you sure you want to add all" +
                                         ` ${o_utils.addCommas(o_browse.totalObsCount)} ` +
                                         "observations to the cart?";
                    $("#op-addall-to-cart-modal .modal-body").text(addAllmodalMsg);
                    break;
            }
        });

        // Handle the Submit or Cancel buttons for the various confirm modals we can pop up
        $(".op-confirm-modal").on("click", ".btn", function() {
            let target = $(this).data("target");
            switch ($(this).attr("type")) {
                case "submit":
                    switch(target) {
                        case "op-reset-search-metadata-modal":
                            opus.handleResetButtons(true);
                            break;
                        case "op-reset-search-modal":
                            opus.handleResetButtons(false);
                            break;
                        case "op-close-metadata-modal":
                            o_selectMetadata.saveChanges();
                            break;
                        case "op-reset-opus-modal":
                            location.assign("/opus");
                            break;
                        case "op-overwrite-sort-order":
                            // this case handles the replace sort
                            o_sortMetadata.onClickSortOrder($(`#${target}`).data("slug"), false);
                            break;
                        case "op-reset-sort-order":
                            o_sortMetadata.resetSortOrder();
                            break;
                        case "op-empty-cart-modal":
                            o_cart.emptyCartOrRecycleBin("cart");
                            break;
                        case "op-empty-recycle-bin-modal":
                            o_cart.emptyCartOrRecycleBin("recycleBin");
                            break;
                        case "op-restore-recycle-bin-modal":
                            o_cart.restoreRecycleBin();
                            break;
                        case "op-addall-to-cart-modal":
                            o_cart.addAllToCart();
                            break;
                        case "op-close-widgets-modal":
                            let slug = $("#op-close-widgets-modal").data("slug");
                            o_widgets.closeAndRemoveWidgetFromDOM(slug, false);
                            break;
                        case "op-close-surfacegeo-widgets-modal":
                            o_widgets.closeAllSURFACEGEOWidgets();
                            break;
                        case "op-http-response-error-modal":
                            location.reload();
                            break;
                        case "op-notification-modal":
                            $.cookie("notify", $(`#${target}`).data("cookie"), {expires: 1000000});
                            break;
                    }
                    $(`#${target}`).modal("hide");
                    break;

                case "cancel":
                    switch (target) {
                        case "op-update-url-modal":
                            // if user clicks "Dismiss Message" ("No" button), we hide the
                            // link to the message on the nav bar
                            $(".op-user-msg").removeClass("op-show-msg");
                            break;
                        case "op-close-metadata-modal":
                            o_selectMetadata.discardChanges();
                            break;
                        case "op-overwrite-sort-order":
                            // this case handles the append to sort
                            o_sortMetadata.onClickSortOrder($(`#${target}`).data("slug"));
                            break;
                    }
                    $(`#${target}`).modal("hide");
                    break;
            }
        });
    },

    tooltipClickHandler: function () {
        opus.tooltipRemoveHandler();
        let title = $(this).attr("title");
        $(this).append(`<span class="op-tooltip-text">${title}</span>`);
        $(window).on("touchstart", opus.tooltipRemoveHandler);
        return false;
    },

    tooltipRemoveHandler: function() {
        $(".op-tooltip-text").remove();
        $(window).off("touchstart", opus.tooltipRemoveHandler);
    },

    displayNotificationDialog: function(html, cookie) {
        $("#op-notification-modal .modal-body").html(html);
        $("#op-notification-modal").data("cookie", cookie);

        opus.hideOrShowSplashText();
        $("#op-notification-modal").modal("show");
    },

    displayImageInterpretation: function(action) {
        let url = PREVIEW_GUIDES[action];
        window.open(url, "_blank");
        $("#op-help").removeClass("show");
        $(".op-interpret-image").hide();
    },

    displayHelpPane: function(action) {
        /**
         * Given the name of a help menu entry, open the help pane and load the
         * help contents.
         */
        let baseURL = "/opus/__help/";
        let pdfURL = false;
        let url = "";
        let header = "";
        switch (action) {
            case "about":
                url = baseURL + "about.html";
                pdfURL = baseURL + "about.pdf";
                header = "About OPUS";
                break;
            case "volumes":
                url = baseURL + "volumes.html";
                pdfURL = baseURL + "volumes.pdf";
                header = "Volumes Available for Searching with OPUS";
                break;
            case "faq":
                url = baseURL + "faq.html";
                pdfURL = baseURL + "faq.pdf";
                header = "Frequently Asked Questions (FAQ) About OPUS";
                break;
            case "apiguide":
                url = baseURL + "apiguide.html";
                pdfURL = baseURL + "apiguide.pdf";
                header = "OPUS API Guide";
                break;
            case "citing":
                let searchHash = o_hash.getHashStrFromSelections();
                url = baseURL + "citing.html?stateurl=" + encodeURIComponent(window.location);
                url += "&searchurl=" + encodeURIComponent(o_utils.getWindowURLPrefix()+"/#/"+searchHash);
                header = "How to Cite OPUS";
                // Can't allow pdf because wkhtmltopdf doesn't support inline image data
                break;
            case "gettingStarted":
                url = baseURL + "gettingstarted.html";
                pdfURL = baseURL + "gettingstarted.pdf";
                header = "Getting Started with OPUS";
                break;
            case "COCIRS":
            case "COUVIS":
            case "COVIMS":
                opus.displayImageInterpretation(action);
                return;
            case "contact":
                FeedbackMethods.open();
                return;
            case "splash":
                opus.displaySplashDialog();
                return;
            case "announcements":
                window.open("https://ringsnodesearchtool.blogspot.com/", "_blank");
                return;
            case "tutorialVideos":
                window.open("https://www.youtube.com/playlist?list=PLgPYitJagzrYj0iMFiuwQpdGImP6Wdt29", "_blank");
                return;
        }
        let buttons = '<div class="op-open-help">';
        buttons += `&nbsp;&nbsp;<button type="button" class="btn btn-sm btn-secondary op-open-help-new-tab" data-action="${action}" title="Open the contents of this panel in a new browser tab">View in new browser tab</button>`;
        if (pdfURL) {
            buttons += `&nbsp;<button type="button" class="btn btn-sm btn-secondary op-open-help-pdf" data-action="${pdfURL}" title="Download PDF version of this panel">Download PDF</button>`;
        }
        buttons += "</div>";

        $("#op-help-panel").addClass("op-no-select");
        $(".op-cite-opus-btn").addClass(".op-prevent-pointer-events");
        $("#op-help-panel .op-header-text").html(`<h2>${header}</h2>`);
        $("#op-help-panel .op-card-contents").html("Loading... please wait.");
        $("#op-help-panel .loader").show();

        // Enable default scrollbar for Ctrl + F search scroll to work in Chrome and Firefox.
        if (opus.currentBrowser === "chrome" || opus.currentBrowser === "firefox") {
            $("#op-help-panel .card-body").addClass("op-enable-default-scrolling");
        }

        // We only need one perfectScrollbar because the pane is reused
        if (!opus.helpScrollbar) {
            opus.helpScrollbar = new PerfectScrollbar("#op-help-panel .card-body", {
                suppressScrollX: true,
                minScrollbarLength: opus.minimumPSLength
            });
        }
        $("#op-help-panel").toggle("slide", {direction:"right"}, function() {
            $(".op-overlay").addClass("active"); // This shows the panel
            $("#op-help-panel").addClass("active"); // This is for keeping track of what's open
        });
        $.ajax({
            url: url,
            dataType: "html",
            success: function(page) {
                $("#op-help-panel .loader").hide();

                // make sure all text is deselected on init of help panel
                document.getSelection().removeAllRanges();
                $("#op-help-panel").removeClass("op-no-select");

                let contents = `${buttons}<div class="op-help-contents">${page}</div>`;
                $("#op-help-panel .op-card-contents").html(contents);
                $(".op-open-help-new-tab").on("click", function(e) {
                    let contents = $("#op-help-panel .op-help-contents").clone()[0];
                    let contentsHtml = $(contents).html().replace(/class="collapse"/g, 'class="collapse show"');
                    contentsHtml = `<div class="op-help-contents-printable"><h1>${header}</h1>${contentsHtml}</div>`;
                    $(contents).html(contentsHtml);
                    let newTabWindow = window.open("", "_blank");
                    $(newTabWindow.document.head).html($(document.head).html().replace(/\/static_media/g, o_utils.getWindowURLPrefix()+"/static_media"));
                    newTabWindow.document.getElementsByTagName("title")[0].innerHTML = header;
                    $(newTabWindow.document.body).append(contents)
                        .css({
                            overflow: "auto",
                            margin: "1.5em",
                            backgroundColor: "inherit"
                        });
                });
                $(".op-open-help-pdf").on("click", function(e) {
                    let pdfURL = $(".op-open-help-pdf").data("action");
                    window.open(pdfURL, "_blank");
                });
            }
        });
    },

    displaySplashDialog: function() {
        let url = "/opus/__help/splash.html";
        $.ajax({
            url: url,
            dataType: "html",
            success: function(page) {
                $("#op-new-user-msg-modal .modal-body").html(page);
                $(".op-open-getting-started").on("click", function() {
                    $("#op-new-user-msg-modal").modal("hide");
                    opus.displayHelpPane("gettingStarted");
                });

                $(".op-open-faq").on("click", function() {
                    $("#op-new-user-msg-modal").modal("hide");
                    opus.displayHelpPane("faq");
                });
                opus.hideOrShowSplashText();
                $("#op-new-user-msg-modal").modal("show");
            }
        });
    },

    hideOrShowSplashText: function() {
        if ($(window).height() < 540) {
            $(".op-splash-text").hide();
        } else {
            $(".op-splash-text").show();
        }
    },

    opusInitialization: function() {
        /**
         * Initialize OPUS after the normalized URL has been returned.
         */

        opus.updateNotifications();
        opus.addAllBehaviors();

        opus.prefs.widgets = [];

        // probably not needed, just added as a precaution.
        opus.force_load = true;

        // set these to the current hash on opus init
        [opus.lastSelections, opus.lastExtras] = o_hash.getSelectionsExtrasFromHash();

        // Initialize opus.prefs from the URL hash
        o_hash.initFromHash();

        if (!opus.prefs.view) {
            opus.prefs.view = "search";
        }

        o_mutationObserver.observePerfectScrollbar();

        // Create the four infinite scrollbars for the browse&cart gallery&table
        for (const tab of ["browse", "cart"]) {
            o_browse.initInfiniteScroll(tab, `#${tab} .op-gallery-view`);
            o_browse.initInfiniteScroll(tab, `#${tab} .op-data-table-view`);
        }

        o_cart.initCart();
        o_detail.showDetailThumbInNav();

        // This is a general function to discover if an element is in the viewport
        // Used like this: if ($(this).isInViewport()) {}
        $.fn.isInViewport = function() {
            let elementTop = $(this).offset().top;
            let elementBottom = elementTop + $(this).outerHeight();
            let viewportTop = $(window).scrollTop();
            let viewportBottom = viewportTop + $(window).height();
            return elementBottom > viewportTop && elementTop < viewportBottom;
        };

        if (opus.isAnyNormalizeInputInProgress()) {
            opus.navLinkRemembered = opus.prefs.view;
        }
        opus.triggerNavbarClick();
    },

    searchChanged: function(delay) {
        /**
         * Start or restart the timer used to call opus.load() when a search
         * parameter changes.
         */
        opus.stopSearchChangeTimer();
        if (delay) {
            opus.searchChangeTimer = setTimeout(opus.load, opus.searchChangeDelay);
        } else {
            opus.load();
        }
    },

    stopSearchChangeTimer: function() {
        /**
         * Stop the timer used to call opus.load() when a search parameter
         * changes.
         */
        if (opus.searchChangeTimer !== null) {
            clearTimeout(opus.searchChangeTimer);
            opus.searchChangeTimer = null;
        }
    },

    checkBrowserSupported: function() {
        /**
         * Check supported browser versions and display a modal to
         * inform the user if that version is not supprted.
         */
        let browserName, browserVersion, matchObj;
        let userAgent = navigator.userAgent;
        let updateString = "";

        // Good information on how to parse User Agent strings:
        // https://deviceatlas.com/blog/user-agent-parsing-how-it-works-and-how-it-can-be-used
        // https://deviceatlas.com/blog/user-agent-string-analysis
        // NOTE:
        //   Mozilla/5.0 means "Mozilla compatible"
        //   Safari/xxx means "Safari compatible"

        if (userAgent.indexOf("Firefox/") > -1) {
            // ==== FIREFOX ====
            // ** Mac:
            // Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0)
            // Gecko/20100101 Firefox/66.0
            // ** Windows:
            // Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0)
            // Gecko/20100101 Firefox/67.0
            // ** Linux:
            // Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:66.0)
            // Gecko/20100101 Firefox/66.0
            // ** Android:
            // Mozilla/5.0 (Android 7.0; Mobile; rv:54.0)
            // Gecko/54.0 Firefox/54.0
            matchObj = userAgent.match(/Firefox\/(\d+.\d+)/);
            browserName = "Firefox";
            browserVersion = matchObj[1];
        } else if (userAgent.indexOf("OPR") > -1) {
            // ==== OPERA ====
            // ** Mac:
            // Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36
            // (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36 OPR/60.0.3255.95
            // ** Mobile:
            // Mozilla/5.0 (Linux; Android 7.0; SM-A310F Build/NRD90M) AppleWebKit/537.36
            // (KHTML, like Gecko) Chrome/55.0.2883.91 Mobile Safari/537.36 OPR/42.7.2246.114996
            // Opera/9.80 (Android 4.1.2; Linux; Opera Mobi/ADR-1305251841) Presto/2.11.355 Version/12.10
            matchObj = userAgent.match(/OPR\/(\d+.\d+)/);
            browserName = "Opera";
            browserVersion = matchObj[1];
        } else if (userAgent.indexOf("Chrome") > -1 && userAgent.indexOf("Edge") === -1 &&
                   userAgent.indexOf("Edg") === -1) {
            // ==== CHROME ====
            // ** Mac:
            // Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36
            // (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36
            // ** Windows:
            // Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
            // (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36
            // ** Linux:
            // Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36
            // (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36
            // ** Android:
            // Mozilla/5.0 (Linux; Android 8.0.0; SM-G960F Build/R16NW) AppleWebKit/537.36
            // (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36
            // ** Chrome OS:
            // Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36
            // (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36
            matchObj = userAgent.match(/Chrome\/(\d+.\d+)/);
            browserName = "Chrome";
            browserVersion = matchObj[1];
        } else if (userAgent.indexOf("CriOS") > -1) {
            // ==== CHROME (iOS) ====
            // ** iOS:
            // Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15
            // (KHTML, like Gecko) CriOS/69.0.3497.105 Mobile/15E148 Safari/605.1
            matchObj = userAgent.match(/CriOS\/(\d+.\d+)/);
            browserName = "Chrome (iOS)";
            browserVersion = matchObj[1];
        } else if (userAgent.indexOf("Version") > -1) {
            // ==== SAFARI ====
            // ** Mac:
            // Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/605.1.15
            // (KHTML, like Gecko) Version/12.1 Safari/605.1.15
            // ** iOS:
            // Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30
            // (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1
            matchObj = userAgent.match(/Version\/(\d+.\d+)/);
            browserName = "Safari";
            browserVersion = matchObj[1];
        } else if (userAgent.indexOf("Edg") > -1) {
            // ==== Microsoft Edge ====
            // ** Mac:
            // Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36
            // (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36 Edg/83.0.478.37
            // ** Windows:
            // Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
            // (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36 Edg/83.0.478.37
            matchObj = userAgent.match(/Edg\/(\d+.\d+)/);
            browserName = "Edge";
            browserVersion = matchObj[1];
        } else if (userAgent.indexOf("AppleWebKit") > -1 && userAgent.indexOf("Edge") === -1 &&
                   userAgent.indexOf("Edg") === -1) {
            // ==== Other AppleWebKit-based Browser ====
            // I don't know why, but Edge doesn't work even though it claims to have the right version of AWK
            // ** Firefox (iOS)
            // Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_2 like Mac OS X) AppleWebKit/603.2.4
            // (KHTML, like Gecko) FxiOS/7.5b3349 Mobile/14F89 Safari/603.2.4
            // ** Facebook Messenger:
            // Mozilla/5.0 (iPad; CPU OS 9_3_5 like Mac OS X) AppleWebKit/601.1.46
            // (KHTML, like Gecko) Mobile/13G36
            // [FBAN/MessengerForiOS;FBAV/100.1.0.36.68;FBBV/46154306;FBRV/0;FBDV/iPad4,2;
            //  FBMD/iPad;FBSN/iPhone OS;FBSV/9.3.5;FBSS/2;FBCR/Viettel;FBID/tablet;FBLC/en_US;FBOP/5]
            // ** Facebook Mobile App:
            // Mozilla/5.0 (iPhone; CPU iPhone OS 11_4_1 like Mac OS X) AppleWebKit/605.1.15
            // (KHTML, like Gecko) Mobile/15G77
            // [FBAN/FBIOS;FBAV/183.0.0.41.81;FBBV/119182652;FBDV/iPhone8,1;
            //  FBMD/iPhone;FBSN/iOS;FBSV/11.4.1;FBSS/2;FBCR/Oi;FBID/phone;FBLC/pt_BR;FBOP/5;FBRV/0]
            matchObj = userAgent.match(/AppleWebKit\/(\d+.\d+)/);
            browserName = "based on AppleWebKit";
            browserVersion = matchObj[1];
        } else {
            browserName = `unsupported - ${userAgent}`;
            browserVersion = "";
            updateString = "Please use a supported browser for a better experience.";
        }

        let browser = `${browserName} ${browserVersion}</br></br>OPUS may not work properly on your browser.`;
        let modalMsg = (`Your current browser is ${browser}</br>
                        We support
                        Firefox (${opus.browserSupport.firefox}+),
                        Chrome (${opus.browserSupport.chrome}+),
                        Safari (${opus.browserSupport.safari}+),
                        Opera (${opus.browserSupport.opera}+),
                        Edge (${opus.browserSupport.edge}+),
                        and other AppleWebKit-based browsers (${opus.browserSupport["based on applewebkit"]})+.
                        ${updateString}`);
        $("#op-browser-version-msg-modal .modal-body").html(modalMsg);
        browserName = browserName.toLowerCase();
        opus.currentBrowser = browserName;

        if (opus.browserSupport[browserName] === undefined) {
            $("#op-browser-version-msg-modal").modal("show");
            return false;
        } else {
            if (parseFloat(browserVersion) < opus.browserSupport[browserName]) {
                $("#op-browser-version-msg-modal").modal("show");
                return false;
            }
        }
        return true;
    },

    checkBrowserSize: function() {
        /**
         * Check if browser width is less than 1280px or height is less
         * than 275px. If so, display a modal to inform the user to
         * resize the browser size.
         */

         if (opus.browserSizeActionInProgress) {
             return;
         }

         let modal = $("#op-browser-size-msg-modal");

         // This is required to handle problems of rapid hide/show sequencing
         // See: https://github.com/twbs/bootstrap/issues/3902
         function showCompleted() {
             opus.browserSizeActionInProgress = false;
             modal.off("shown.bs.modal", showCompleted);
         }
         function hideCompleted() {
             opus.browserSizeActionInProgress = false;
             modal.off("hidden.bs.modal", hideCompleted);
         }

        if ($(window).width() < opus.browserSupport.width ||
            $(window).height() < opus.browserSupport.height) {
            if (!$("#op-browser-size-msg-modal").hasClass("show")) {
                let modalMsg = (`Please resize your browser or rotate your mobile
                                device to landscape mode. OPUS requires a browser
                                size of at least ${opus.browserSupport.width} pixels
                                by ${opus.browserSupport.height} pixels.`);
                $("#op-browser-size-msg-modal .modal-body").html(modalMsg);
                opus.browserSizeActionInProgress = true;
                modal.on("shown.bs.modal", showCompleted);
                modal.modal("show");
            }
        } else {
            if ($("#op-browser-size-msg-modal").hasClass("show")) {
                opus.browserSizeActionInProgress = true;
                modal.on("hidden.bs.modal", hideCompleted);
                modal.modal("hide");
            }
        }
    },

    checkVisitedCookie: function() {
        /**
         * Check visited cookie to determine if the user is a first time
         * or newer visitor. If so, we display a welcome message.
         */
        if ($.cookie("visited") === undefined ||
            $.cookie("visited") < opus.splashVersion) {
            // set the cookie for the first time user
            $.cookie("visited", opus.splashVersion, {expires: 1000000});
            opus.displaySplashDialog();
        }
    },

    isAnyNormalizeInputInProgress: function() {
        /**
         * Check if any normalize input API call is in progress.
         */
        return (Object.keys(opus.normalizeInputForAllFieldsInProgress).length > 0 ||
                Object.keys(opus.normalizeInputForCharInProgress).length > 0);
    },

    areInputsValid: function() {
        /**
         * Check if all inputs are valid.
         */
        for (const slugWithId in opus.inputFieldsValidation) {
            if (opus.inputFieldsValidation[slugWithId] === false) {
                return false;
            }
        }

        return true;
    },

    updateOPUSLastSelectionsWithOPUSSelections: function() {
        /**
         * Update opus.lastSelections & opus.lastExtras with opus.selections
         * and opus.extras.
         */
        opus.lastSelections = o_utils.deepCloneObj(opus.selections);
        opus.lastExtras = o_utils.deepCloneObj(opus.extras);
    },

}; // end opus namespace

$(document).ajaxError(function(event, jqXHR, ajaxSettings, thrownError) {
    let responseText = jqXHR.responseText;
    let errorMsg = responseText.match(/<div id="info">([\s\S]*?)<\/div>/m)[1];
    let modal = $("#op-http-response-error-modal");
    let modalMsg = (`There was an error on the OPUS server. The following
                     response was received:
                     <br/><br/>
                     ${errorMsg}`);
    $(modal).find(".modal-body").html(modalMsg);
    modal.on("shown.bs.modal");
    modal.modal("show");
});

$(document).ready(function() {
    opus.checkBrowserSupported();
    opus.checkVisitedCookie();
    opus.checkBrowserSize();
    // Call normalized url api first
    // Rest of initialization process will be performed afterwards
    opus.normalizedURLAPICall();
});
