/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $, _, PerfectScrollbar */
/* globals o_browse, o_cart, o_detail, o_hash, o_menu, o_mutationObserver, o_search, o_utils, o_widgets */
/* globals DEFAULT_COLUMNS, DEFAULT_WIDGETS, DEFAULT_SORT_ORDER, STATIC_URL */

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

    mainTimerInterval: 1000,


    // avoiding race conditions in ajax calls
    lastAllNormalizeRequestNo: 0,
    lastResultCountRequestNo: 0,
    waitingForAllNormalizedAPI: false,
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
        // the result count, hints, etc. at the next timer interval
    selections: {},        // the user's search
    extras: {},            // extras to the query: qtypes
    lastSelections: {},    // lastXXX are used to monitor changes
    lastExtras: {},

    allInputsValid: true,

    force_load: true, // set this to true to force load() when selections haven't changed

    // searching - ui
    widgetsDrawn: [], // keeps track of what widgets are actually drawn
    widgetsFetching: [], // this widget is currently being fetched
    widgetElementsDrawn: [], // the element is drawn but the widget might not be fetched yet
    menuState: {"cats": ["obs_general"]},

    // Help panel
    helpPanelOpen: false,

    // these are for the process that detects there was a change in the selection criteria and
    // updates things
    mainTimer: false,

    // store the browser version and width supported by OPUS
    browserSupport: {
        "firefox": 59,
        "chrome": 56,
        "opera": 42,
        "safari": 10.1,
        "width": 600,
        "height": 200
    },

    //------------------------------------------------------------------------------------
    // Debugging support
    //------------------------------------------------------------------------------------
    logError: function(...args) {
        if (opus.debug) {
            console.error("ERROR:", ...args);
        }
    },


    //------------------------------------------------------------------------------------
    // Functions to update the result count and hinting numbers on any change to the search
    //------------------------------------------------------------------------------------

    load: function() {
        /**
         * This function is called periodically by a timer. Each time it checks to see
         * if the selections or extras have changed since the last call. If either
         * has changed, or opus.force_load is true, then it starts the chain of
         * 1) Check inputs for validity
         * 2) Perform the search and get the result count
         * 3) Update the result count badge(s)
         * 4) Get hinting information and update all hints
         */

        let [selections, extras] = o_hash.getSelectionsExtrasFromHash();

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

        // Compare selections and last selections, extras and last extras to see if anything
        // has changed that would require an update to the results. We ignore q-types for
        // search fields that aren't actually being searched on because when the user changes
        // such a q-type, there's no point in redoing the search since the results will be
        // identical.
        let currentExtrasQ = o_hash.extrasWithoutUnusedQtypes(selections, extras);
        let lastExtrasQ = o_hash.extrasWithoutUnusedQtypes(opus.lastSelections, opus.lastExtras);
        if (o_utils.areObjectsEqual(selections, opus.lastSelections) &&
                                    o_utils.areObjectsEqual(currentExtrasQ, lastExtrasQ)) {
            if (!opus.force_load) {
                return;
            }
        } else {
            // The selections or extras have changed in a meaningful way requiring an update
            opus.prefs.startobs = 1;
            opus.prefs.cart_startobs = 1;

            // If selections != opus.selections or extras != opus.extras,
            // it means the user manually updated the URL in the browser,
            // so we have to reload the page. We can't just continue on normally
            // because we need to re-run the URL normalization process.
            let opusExtrasQ = o_hash.extrasWithoutUnusedQtypes(opus.selections, opus.extras);
            if (!o_utils.areObjectsEqual(selections, opus.selections) ||
                !o_utils.areObjectsEqual(currentExtrasQ, opusExtrasQ)) {
                opus.selections = selections;
                opus.extras = extras;
                location.reload();
                return;
            } else {
                // Otherwise, this was just a user change to one of the search criteria inside
                // the UI, so erase the previous data and reload the results.
                o_browse.clearObservationData();
            }
        }

        opus.force_load = false;

        // Start the result count spinner and do the yellow flash
        $("#op-result-count").html(opus.spinner).parent().effect("highlight", {}, 500);

        // Start the observation number slider spinner - no point in doing a flash here
        $("#op-observation-number").html(opus.spinner);

        // Start the spinners for the left side menu and each widget for hinting
        $(".op-menu-text.spinner").addClass("op-show-spinner");
        $("#op-search-widgets .spinner").fadeIn();

        // Mark the changes as complete. We have to do this before allNormalizedApiCall to
        // avoid a recursive api call
        opus.lastSelections = selections;
        opus.lastExtras = extras;

        // Update the UI in the following order:
        // 1) Normalize all the inputs and check for validity (allNormalizedApiCall)
        // 2) Perform the search and get the result count (getResultCount)
        // 3a) Update the result count badge(s) (updateSearchTabHinting)
        // 3b) Update all the search hinting (updateSearchTabHinting)
        // The way this is currently implemented, the result count has to finish before
        // any of the search hinting is updated. This is a good thing because of the way
        // the back end is implemented, where the result count needs to finish so the
        // cache table has been created before hinting can be performed. However, at
        // some point we would like to be able to do these in parallel. This will require
        // both backend changes and a change here to remove the sequential dependence.
        o_search.allNormalizedApiCall().then(opus.getResultCount).then(opus.updateSearchTabHinting);
    },

    getResultCount: function(normalizedData) {
        /**
         * Given the result of the search parameter normalization, execute the search
         * that will eventually return the result count.
         */

        // If there are more normalized data requests in the queue, don't trigger
        // spurious result counts that we won't use anyway
        if (normalizedData.reqno < opus.lastAllNormalizeRequestNo) {
            return;
        }

        // Take the results from the normalization, check for errors, and update the
        // UI to show the user if anything is wrong. This sets the opus.allInputsValid
        // flag used below.
        o_search.validateRangeInput(normalizedData, true);

        if (!opus.allInputsValid) {
            // We don't try to get a result count if any of the inputs are invalid.
            // Remove spinning effect on browse counts and mark as unknown.
            $("#op-result-count").text("?");
            $("#op-observation-number").html("?");
            return;
        }

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
        // The hints were previously marked as "?" in validateRangeInput so they
        // will just stay that way.
        if (!opus.allInputsValid || !resultCountData) {
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
            o_search.getHinting(slug);
        });
    },

    updateResultCount: function(resultCount) {
        /**
         * Given a new result count, update our cache value as well as all
         * badge(s).
         */

        o_browse.totalObsCount = resultCount;
        $("#op-result-count").fadeOut("fast", function() {
            $(this).html(o_utils.addCommas(o_browse.totalObsCount )).fadeIn("fast");
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

    updateLastBlogDate: function() {
        /**
         * Retrieve the date of the last blog update and update the tooltip for
         * the 'Recent Announcements' nav bar item.
         */

        $.getJSON("/opus/__lastblogupdate.json", function(data) {
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
        });
    },

    changeTab: function(tab) {
        /**
         * This is the event handler for the user clicking on one of the main nav
         * bar tabs (views).
         */

        // First hide everything and stop any interval timers
        $("#search, #detail, #cart, #browse").hide();
        o_browse.hideMenu();

        // Close any open modals
        $("#galleryView").modal('hide');

        // Update the state with the newly selected view
        opus.prefs.view = tab ? tab : opus.prefs.view;
        o_hash.updateHash();

        // Go ahead and check to see if the blog has been updated recently
        opus.updateLastBlogDate();

        switch(opus.prefs.view) {
            case "search":
                window.scrollTo(0,0);
                $("#search").fadeIn();
                o_search.activateSearchTab();
                break;

            case "browse":
                $("#browse").fadeIn();
                o_browse.activateBrowseTab();
                break;

            case "detail":
                $("#detail").fadeIn();
                o_detail.activateDetailTab(opus.prefs.detail);
                break;

            case "cart":
                $("#cart").fadeIn();
                o_cart.activateCartTab();
                break;

            default:
                opus.logError(`changeTab got unknown view name ${opus.prefs.view}`);
                o_search.activateSearchTab();
        }

    },

    hideHelpPanel: function() {
        /**
         * If the "Help" panel is currently open, close it.
         */
        if (opus.helpPanelOpen) {
            $("#op-help-panel").toggle("slide", {direction: "right"});
            $(".op-overlay").removeClass("active");
        }
        opus.helpPanelOpen = false;
    },

    adjustHelpPanelHeight: function() {
        /**
         * Set the height of the "Help" panel based on the browser size.
         */
        let height = $(window).height()-120;
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

        // Stop polling for UI changes for a moment
        clearInterval(opus.mainTimer);

        // Reset the search query and return to the Search tab
        opus.selections = {};
        opus.extras = {};
        o_browse.clearObservationData();
        opus.changeTab('search');

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

        o_hash.updateHash();

        // Start the main timer again
        opus.mainTimer = setInterval(opus.load, opus.mainTimerInterval);
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
                $("#op-update-url .modal-body").html(normalizeURLData.msg);
                $(".op-user-msg").addClass("op-show-msg");
            }

            // Update URL in browser
            window.location.hash = "/" + normalizeURLData.new_url.replace(" ", "+");
            // Perform rest of initialization process
            opus.opusInitialization();
            // Watch the hash and URL for changes; this runs continuously
            opus.mainTimer = setInterval(opus.load, opus.mainTimerInterval);
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
    },

    addOpusBehaviors: function() {
        /**
         * Add the top-level behaviors that affect all of OPUS.
         */

        // When the browser is resized, we need to recalculate the scrollbars
        // for all tabs.
        let adjustSearchHeightDB = _.debounce(o_search.adjustSearchHeight, 200);
        let adjustBrowseHeightDB = _.debounce(function() {o_browse.adjustBrowseHeight(true);}, 200);
        let adjustTableSizeDB = _.debounce(o_browse.adjustTableSize, 200);
        let adjustProductInfoHeightDB = _.debounce(o_cart.adjustProductInfoHeight, 200);
        let adjustDetailHeightDB = _.debounce(o_detail.adjustDetailHeight, 200);
        let adjustHelpPanelHeightDB = _.debounce(opus.adjustHelpPanelHeight, 200);

        $(window).on("resize", function() {
            adjustSearchHeightDB();
            adjustBrowseHeightDB();
            adjustTableSizeDB();
            adjustProductInfoHeightDB();
            adjustDetailHeightDB();
            adjustHelpPanelHeightDB();
            opus.checkBrowserSize();
        });

        // Add the navbar clicking behaviors, selecting which tab to view
        $("#op-main-nav").on("click", ".main_site_tabs .nav-item", function() {
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
            opus.changeTab(tab);
        });

        $(".op-help-item").on("click", function() {
            let url = "/opus/__help/";
            let header = "";
            switch ($(this).data("action")) {
                case "about":
                    url += "about.html";
                    header = "About OPUS";
                    break;
                case "volumes":
                    url += "volumes.html";
                    header = "Volumes Available for Searching with OPUS";
                    break;
                case "faq":
                    url += "faq.html";
                    header = "Frequently Asked Questions (FAQ)";
                    break;
                case "guide":
                    url += "guide.html";
                    header = "OPUS API Guide";
                    break;
                case "tutorial":
                    url += "tutorial.html";
                    header = "A Brief Tutorial";
                    break;
                case "feedback":
                    url = "https://pds-rings.seti.org/cgi-bin/comments/form.pl";
                    header = "Questions/Feedback";
                    break;
            }

            $("#op-help-panel .op-header-text").html(`<h2>${header}</h2`);
            $("#op-help-panel .op-card-contents").html("Loading... please wait.");
            $("#op-help-panel .loader").show();
            // We only need one perfectScrollbar because the pane is reused
            if (!opus.helpScrollbar) {
                opus.helpScrollbar = new PerfectScrollbar("#op-help-panel .card-body", {
                    suppressScrollX: true,
                    minScrollbarLength: opus.minimumPSLength
                });
            }
            $("#op-help-panel").toggle("slide", {direction:"right"}, function() {
                $(".op-overlay").addClass("active");
            });
            $.ajax({
                url: url,
                dataType: "html",
                success: function(page) {
                    $("#op-help-panel .loader").hide();
                    $("#op-help-panel .op-card-contents").html(page);
                    opus.helpPanelOpen = true;
                }
            });
        });

        // Clicking on the "X" in the corner of the help pane
        $("#op-help-panel .close, .op-overlay").on("click", function() {
            opus.hideHelpPanel();
            return false;
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

        $(document).on("keydown click", function(e) {
            if ((e.which || e.keyCode) == 27) {
                // ESC key - close modals and help panel
                // Don't close "#op-browser-version-msg" and "#op-browser-size-msg"
                $.each($(".op-confirm-modal"), function(idx, confirmModal) {
                    if ($(confirmModal).data("action") === "esc") {
                        $(confirmModal).modal("hide");
                    }
                });

                opus.hideHelpPanel();
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
                        case "op-empty-cart":
                            o_cart.emptyCart();
                            break;
                    }
                    $(`#${target}`).modal("hide");
                    break;

                case "cancel":
                    switch (target) {
                        case "op-update-url":
                            // if user clicks "Dismiss Message" ("No" button), we hide the
                            // link to the message on the nav bar
                            $(".op-user-msg").removeClass("op-show-msg");
                            break;
                    }
                    $(`#${target}`).modal("hide");
                    break;
            }
        });
    },

    opusInitialization: function() {
        /**
         * Initialize OPUS after the normalized URL has been returned.
         */

        opus.updateLastBlogDate();
        opus.addAllBehaviors();

        opus.prefs.widgets = [];
        o_widgets.updateWidgetCookies();

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
        for (let tab of ["browse", "cart"]) {
            o_browse.initInfiniteScroll(tab, `#${tab} .op-gallery-view`);
            o_browse.initInfiniteScroll(tab, `#${tab} .op-data-table-view`);
        }

        o_cart.initCart();

        // This is a general function to discover if an element is in the viewport
        // Used like this: if ($(this).isInViewport()) {}
        $.fn.isInViewport = function() {
            let elementTop = $(this).offset().top;
            let elementBottom = elementTop + $(this).outerHeight();
            let viewportTop = $(window).scrollTop();
            let viewportBottom = viewportTop + $(window).height();
            return elementBottom > viewportTop && elementTop < viewportBottom;
        };

        opus.triggerNavbarClick();
    },

    isBrowserSupported: function() {
        /**
         * Check supported browser versions and display a modal to
         * inform the user if that version is not supprted.
         */
        let browserName, browserVersion, matchObj;
        let userAgent = navigator.userAgent;

        if (userAgent.indexOf("Firefox") > -1) {
            // Example output:
            // Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0)
            // Gecko/20100101 Firefox/66.0
            matchObj = userAgent.match(/Firefox\/(\d+.\d+)/);
            browserName = "Firefox";
            browserVersion = matchObj[1];
        } else if (userAgent.indexOf("OPR") > -1) {
            // userAgent example output:
            // Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36
            // (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36 OPR/60.0.3255.95
            matchObj = userAgent.match(/OPR\/(\d+.\d+)/);
            browserName = "Opera";
            browserVersion = matchObj[1];
        } else if (userAgent.indexOf("Chrome") > -1 && userAgent.indexOf("Edge") === -1 &&
                   userAgent.indexOf("Edg") === -1) {
            // userAgent example output:
            // Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36
            // (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36
            matchObj = userAgent.match(/Chrome\/(\d+.\d+)/);
            browserName = "Chrome";
            browserVersion = matchObj[1];
        } else if (userAgent.indexOf("Version") > -1) {
            // userAgent example output:
            // Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/605.1.15
            // (KHTML, like Gecko) Version/12.1 Safari/605.1.15
            matchObj = userAgent.match(/Version\/(\d+.\d+)/);
            browserName = "Safari";
            browserVersion = matchObj[1];
        } else {
            browserName = "unsupported";
            browserVersion = "0.0";
        }

        let browser = `${browserName} ${browserVersion}. Please update your browser`;
        if (browserName === "unsupported") {
            browser = browserName;
        }
        let modalMsg = (`Your current browser is ${browser}. OPUS supports
                        Firefox (${opus.browserSupport.firefox}+),
                        Chrome (${opus.browserSupport.chrome}+),
                        Safari (${opus.browserSupport.safari}+),
                        and Opera (${opus.browserSupport.opera}+).`);
        $("#op-browser-version-msg .modal-body").html(modalMsg);
        browserName = browserName.toLowerCase();

        if (opus.browserSupport[browserName] === undefined) {
            $("#op-browser-version-msg").modal("show");
            return false;
        } else {
            if (parseFloat(browserVersion) < opus.browserSupport[browserName]) {
                $("#op-browser-version-msg").modal("show");
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
        let modalMsg = (`Please resize your browser. OPUS works best with a browser
                        size of at least ${opus.browserSupport.width} pixels by
                        ${opus.browserSupport.height} pixels.`);
        $("#op-browser-size-msg .modal-body").html(modalMsg);
        if ($(window).width() < opus.browserSupport.width ||
            $(window).height() < opus.browserSupport.height) {
            $("#op-browser-size-msg").modal("show");
        } else {
            $("#op-browser-size-msg").modal("hide");
        }
    },

    checkCookies: function() {
        /**
         * Check widgets cookie to determine if the user is a first time
         * visitor. If so, we display a guide page.
         * Note: we will call __help/splash.html api in the future to
         * display the guide page. For now, we just show a modal.
         */
        if ($.cookie("visited") === undefined) {
            // set the cookie for the first time user
            $.cookie("visited", true);
            $("#op-guide").modal("show");
        }
    }
}; // end opus namespace

$(document).ready(function() {
    if (opus.isBrowserSupported()) {
        opus.checkCookies();
        opus.checkBrowserSize();
        // Call normalized url api first
        // Rest of initialization prcoess will be performed afterwards
        opus.normalizedURLAPICall();
    }
});
