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
     *  global var declarations here
     *
     **/

    // Vars
    // Default vars are found in the apps/ui/templates/header.html template
    // and declared in settings.py

    spinner: '<img border = "0" src = "' + STATIC_URL + 'img/spinner_12px.gif">',

    // Minimum height of any scrollbar
    minimumPSLength: 30,

    // avoiding race conditions in ajax calls
    lastAllNormalizeRequestNo: 0,
    lastResultCountRequestNo: 0,
    waitingForAllNormalizedAPI: false,
    lastLoadDataRequestNo: { "#cart": 0, "#browse": 0 },

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
    resultCount: 0,

    allInputsValid: true,

    qtypeRangeDefault: 'any',
    qtypeStringDefault: 'contains',

    force_load: true, // set this to true to force load() when selections haven't changed

    // searching - ui
    widgets_drawn: [], // keeps track of what widgets are actually drawn
    widgets_fetching: [], // this widget is currently being fetched
    widget_elements_drawn: [], // the element is drawn but the widget might not be fetched yet
    menu_state: {'cats': ['obs_general']},
    default_widgets: DEFAULT_WIDGETS.split(','),

    // Help panel
    helpPanelOpen: false,

    // these are for the process that detects there was a change in the selection criteria and updates things
    main_timer: false,
    main_timer_interval: 1000,


    //------------------------------------------------------------------------------------
    // Functions to update the result count and hinting numbers on any change to the search
    //------------------------------------------------------------------------------------

    load: function() {
        /* When user makes any change to the interface, such as changing a query,
        load() will send an ajax request to the server to get information it
        needs to update any hinting (green numbers), result counts, browse results
        tab etc. Load watches for changes to the hash to know
        whether to fire an ajax call.
        */

        let [selections, extras] = o_hash.getSelectionsExtrasFromHash();

        // Note: When URL has an empty hash, both selections and extras returned from getSelectionsExtrasFromHash will be undefined.
        // There won't be a case when only one of them is undefined.
        if (selections === undefined) {
            // safety check, the if condition should never be true
            if (extras !== undefined) {
                console.error("Returned extras is not undefined when URL has an empty hash");
            }
            return;
        }

        // There is a potential bug here if the list of default widgets ever includes a widget with
        // a qtype, because then the user could change the qtype value in extras and it wouldn't
        // change the state of the reset buttons. This isn't a problem now, though.
        if (!$.isEmptyObject(selections) || !opus.isDrawnWidgetsListDefault()) {
            $(".op-reset-button button").prop("disabled", false);
        } else if (!opus.isMetadataDefault()) {
            $(".op-reset-button .op-reset-search-metadata").prop("disabled", false);
            $(".op-reset-button .op-reset-search").prop("disabled", true);
        } else {
            $(".op-reset-button button").prop("disabled", true);
        }

        // compare selections and last selections, extras and last extras to see if anything has changed
        // that would require an update to the results
        if (o_utils.areObjectsEqual(selections, opus.lastSelections) &&
                                    o_utils.areObjectsEqual(o_hash.extrasWithoutUnusedQtypes(selections, extras),
                                                            o_hash.extrasWithoutUnusedQtypes(opus.lastSelections, opus.lastExtras))) {
            if (!opus.force_load) {
                return;
            }
        } else {
            // The selections or extras have changed in a meaningful way requiring an update
            opus.prefs.startobs = 1;
            opus.prefs.cart_startobs = 1;

            // if selections != opus.selections or extras != opus.extras,
            // it means the user manually updated the URL in the browser,
            // so we have to reload the page
            if (!o_utils.areObjectsEqual(selections, opus.selections) ||
                !o_utils.areObjectsEqual(o_hash.extrasWithoutUnusedQtypes(selections, extras),
                                         o_hash.extrasWithoutUnusedQtypes(opus.selections, opus.extras))) {
                opus.selections = selections;
                opus.extras = extras;
                location.reload();
                return;
            } else {
                // Otherwise, this was just a user change to one of the search criteria inside
                // the UI, so erase the previous data and reload the results.
                o_browse.resetData();
            }
        }

        opus.force_load = false;

        // start the result count spinner and do the yellow flash
        $("#op-result-count").html(opus.spinner).parent().effect("highlight", {}, 500);

        // start the observation number slider spinner - no point in doing a flash here
        $("#op-observation-number").html(opus.spinner);

        // start op-menu-text and op-search-widgets spinners
        $(".op-menu-text.spinner").addClass("op-show-spinner");
        $("#op-search-widgets .spinner").fadeIn();

        // Mark the changes as complete. We have to do this before allNormalizedApiCall to avoid a recursive api call
        opus.lastSelections = selections;
        opus.lastExtras = extras;

        // Update the UI in the following order:
        // 1) Normalize all the inputs and check for validity
        // 2) Perform the search and update the result count
        // 3) Update all the search hinting
        // The way this is currently implement, the result count has to finish before any of the
        // search hinting is updated. This is a good thing because of the way the back end
        // is implemented. However, at some point we would like to be able to do these in parallel.
        o_search.allNormalizedApiCall().then(opus.getResultCount).then(opus.updateSearchTabHinting);
    },

    getResultCount: function(normalizedData) {
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
            // We don't try to get a result count if any of the inputs are invalid
            // Remove spinning effect on browse counts and mark as unknown
            $("#op-result-count").text("?");
            $("#op-observation-number").html("?");
            return;
        }

        opus.lastResultCountRequestNo++;
        return $.getJSON(`/opus/__api/meta/result_count.json?${o_hash.getHash()}&reqno=${opus.lastResultCountRequestNo}`);
    },

    updateSearchTabHinting: function(resultCountData) {
        // We don't update the search hinting if any of the inputs are invalid
        // The hints were previously marked as "?" in validateRangeInput
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

        o_menu.getMenu();

        $.each(opus.prefs.widgets, function(index, slug) {
            o_search.getHinting(slug);
        });
    },

    updateResultCount: function(resultCount) {
        opus.resultCount = resultCount;
        $("#op-result-count").fadeOut("fast", function() {
            $(this).html(o_utils.addCommas(opus.resultCount)).fadeIn("fast");
            $(this).removeClass("browse_results_invalid");
        });
    },

    //--------------------------------------------------------------------------
    // Functions related to nav bar tabs
    //--------------------------------------------------------------------------

    triggerNavbarClick: function() {
        $('.nav-item a[href="#'+opus.prefs.view+'"]').trigger("click");
    },

    updateLastBlogUpdate: function() {
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
                let prettyDate = lastUpdateDate.toLocaleDateString('en-GB', {year: 'numeric', month: 'long', day: 'numeric'});
                $("#op-last-blog-update-date").attr("title", "Blog last updated "+prettyDate);
            } else {
                $("#op-last-blog-update-date").attr("title", "");
            }
        });
    },

    changeTab: function(tab) {
        // first hide everything and stop any interval timers
        $('#search, #detail, #cart, #browse').hide();
        o_browse.hideMenu();

        // close any open modals
        $("#galleryView").modal('hide');
        opus.prefs.view = tab ? tab : opus.prefs.view;
        o_hash.updateHash();
        opus.updateLastBlogUpdate();

        switch(opus.prefs.view) {

            case 'search':
                window.scrollTo(0,0);
                $('#search').fadeIn();
                o_search.getSearchTab();
                break;

            case 'browse':
                $('#browse').fadeIn();
                o_browse.getBrowseTab();

                break;

            case 'detail':
                $('#detail').fadeIn();
                o_detail.getDetail(opus.prefs.detail);
                break;

            case 'cart':
                $('#cart').fadeIn();
                o_cart.getCartTab();
                break;

            default:
                o_search.getSearchTab();

        } // end switch

    },

    // Normalize all input fields and check them for validity
    normalizedURLAPICall: function() {
        let hash = o_hash.getHash();
        // Note: We don't need a reqno here.
        // Because in our implementation, this api is called at the beginning of document ready
        // (or on reload), and every time this event is triggered, it means everything is reloaded.
        // If we put reqno here, reqno will always be 1, so we don't need reqno.
        let url = "/opus/__normalizeurl.json?" + hash;
        $.getJSON(url, function(normalizeurlData) {
            // Comment out action of updating startobs
            // $.each(normalizeurlData.new_slugs, function(idx, slug) {
            //     if (slug.startobs) {
            //         opus.currentObs = slug.startobs;
            //     }
            // });

            // display returned message in the modal
            if (normalizeurlData.msg) {
                $("#op-update-url .modal-body").html(normalizeurlData.msg);
                $(".op-user-msg").addClass("op-show-msg");
            }

            // update URL
            window.location.hash = "/" + normalizeurlData.new_url.replace(" ", "+");
            // perform rest of initialization process
            opus.opusInitialization();
            // watch the url for changes, this runs continuously
            opus.main_timer = setInterval(opus.load, opus.main_timer_interval);
        });
    },

    startOver: function(resetMetadata=false) {
        // handles the 'start over' buttons which has 2 selections
        // if keep_set_widgets is true it will leave the current selected widgets alone
        // and just redraw them with no selections in them
        // if keep_set_widgets is false it will remove all widgets and restore
        // the application default widgets

        clearInterval(opus.main_timer);  // stop polling for UI changes for a moment
        // remove all widgets on the screen
        $.each($("#op-search-widgets .widget"), function(idx, widget) {
            widget.remove();
        });

        // reset the search query
        opus.selections = {};
        opus.extras = {};
        o_browse.resetQuery();
        opus.changeTab('search');

        // resets widgets drawn back to system default
        // in the 2 tier button this was the 'start over and restore defaults' behavior
        // note: this is the current deployed behavior for the single 'start over' button
        opus.prefs.widgets = [];
        opus.widgets_drawn = [];
        opus.widget_elements_drawn = [];

        if (!o_utils.areObjectsEqual(opus.prefs.cols, default_columns.split(','))) {
            if (resetMetadata) {
                opus.prefs.cols = [];
                o_browse.resetMetadata(default_columns.split(','), true);
                $(".op-reset-button button").prop("disabled", true);
            } else {
                $(".op-reset-button .op-reset-search-metadata").prop("disabled", false);
                $(".op-reset-button .op-reset-search").prop("disabled", true);
            }
        } else {
            $(".op-reset-button button").prop("disabled", true);
        }

        o_menu.markDefaultMenuItem();

        let deferredArr = [];
        $.each(opus.default_widgets.slice().reverse(), function(index, slug) {
            deferredArr.push($.Deferred());
            o_widgets.getWidget(slug, "#op-search-widgets", deferredArr[index]);
        });

        // start the main timer again
        opus.main_timer = setInterval(opus.load, opus.main_timer_interval);

        o_hash.updateHash();

        return false;

    },

    addAllBehaviors: function() {
        o_widgets.addWidgetBehaviors();
        o_menu.menuBehaviors();
        o_browse.browseBehaviors();
        o_cart.cartBehaviors();
        o_search.searchBehaviors();
        return;
    },

    // check if current drawn widgets are default ones
    isDrawnWidgetsListDefault: function() {
        return o_utils.areObjectsEqual(opus.prefs.widgets, opus.default_widgets);
    },

    // check if current cols (metadata) are default ones
    isMetadataDefault: function() {
        return o_utils.areObjectsEqual(opus.prefs.cols, default_columns.split(','));
    },

    hideHelpPanel: function() {
        if (opus.helpPanelOpen) {
            $("#op-help-panel").toggle("slide", {direction:'right'});
            $(".op-overlay").removeClass("active");
        }
        opus.helpPanelOpen = false;
    },

    adjustHelpPanelHeight: function() {
        let height = $(window).height()-120;
        $("#op-help-panel .card-body").css("height", height);
        if (opus.helpScrollbar) {
            // Make ps always start from top
            $("#op-help-panel .card-body").scrollTop(0);
            opus.helpScrollbar.update();
        }
    },

    // return either o_browse or o_cart, default to o_browse object
    getViewNamespace: function() {
        return (opus.prefs.view === "cart" ? o_cart : o_browse);
    },

    // return either #browse or #cart, default to #browse
    getViewTab: function() {
        return (opus.prefs.view === "cart" ? "#cart" : "#browse");
    },

    // OPUS initialization process after document.ready and normalized url api call
    opusInitialization: function() {
        /* displays a list of the included css for debug only!
            let temp = "";
            $.each($("link"), function(index, elem) {
                temp += elem.href + "\n"
            });
            alert(temp);
        */

        opus.prefs.widgets = [];
        o_widgets.updateWidgetCookies();
        opus.lastBlogUpdate();
        opus.addAllBehaviors();

        o_hash.initFromHash(); // just returns null if no hash

        if (!opus.prefs.view) {
            opus.prefs.view = 'search';
        }

        let adjustSearchHeightDB = _.debounce(o_search.adjustSearchHeight, 200);
        let adjustBrowseHeightDB = _.debounce(o_browse.adjustBrowseHeight, 200);
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
        });

        o_mutationObserver.observePerfectScrollbar();

        for (let tab of ["browse", "cart"]) {
            o_browse.initInfiniteScroll(tab, `#${tab} .op-gallery-view`);
            o_browse.initInfiniteScroll(tab, `#${tab} .op-data-table-view`);
        }

        // add the navbar clicking behaviors, selecting which tab to view:
        // see triggerNavbarClick
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

            // little hack in case something calls onclick programmatically....
            tab = tab ? tab : opus.prefs.search;
            opus.changeTab(tab);

            //$(this).find('a').blur(); // or else it holds the hover style which is stoo pid.

            //return false;

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
            // We only need one perfectScrollbar
            if (!opus.helpScrollbar) {
                opus.helpScrollbar = new PerfectScrollbar("#op-help-panel .card-body", {
                    suppressScrollX: true,
                    minScrollbarLength: opus.minimumPSLength
                });
            }
            $("#op-help-panel").toggle("slide", {direction:'right'}, function() {
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

        $("#op-help-panel .close, .op-overlay").on("click", function() {
            opus.hideHelpPanel();
            return false;
        });

        $(".op-reset-button button").on("click", function() {
            let targetModal = $(this).data("target");

            if (!$.isEmptyObject(opus.selections) || !opus.isDrawnWidgetsListDefault()) {
                $(targetModal).modal("show");
            } else if (targetModal === "#op-reset-search-metadata-modal" && !opus.isMetadataDefault()) {
                $(targetModal).modal("show");
            }
        });

        $(document).on("keydown click", function(e) {
            if ((e.which || e.keyCode) == 27) { // esc - close modals
                $(".op-confirm-modal").modal('hide');
            }
        });

        $(".op-confirm-modal").on("click", ".btn", function() {
            let target = $(this).data("target");
            switch ($(this).attr("type")) {
                case "submit":
                    switch(target) {
                        case "op-reset-search-metadata-modal":
                            opus.startOver(true);
                            break;
                        case "op-reset-search-modal":
                            opus.startOver();
                            break;
                        case "op-empty-cart":
                            o_cart.emptyCart();
                            break;
                    }
                    $(".modal").modal("hide");
                    break;
                case "cancel":
                    switch (target) {
                        case "op-update-url":
                            // if user clicks "Dismiss Message" ("No" button), we hide the link to url message on navbar
                            $(".op-user-msg").removeClass("op-show-msg");
                            break;
                    }
                    $(".modal").modal("hide");
                    break;
            }
        });

        // general functionality to discover if an element is in the viewport
        // used like this: if ($(this).isInViewport()) {}
        $.fn.isInViewport = function() {
            let elementTop = $(this).offset().top;
            let elementBottom = elementTop + $(this).outerHeight();
            let viewportTop = $(window).scrollTop();
            let viewportBottom = viewportTop + $(window).height();
            return elementBottom > viewportTop && elementTop < viewportBottom;
        };

        o_cart.initCart();
        opus.triggerNavbarClick();
    }

}; // end opus namespace

/*
 * there are 3 main content sections can use for jquery contexts: search, browse, detail
 *
 */
$(document).ready(function() {
    // Call normalized url api first
    // Rest of initialization prcoess will be performed afterwards
    opus.normalizedURLAPICall();
    return;
});
