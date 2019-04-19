/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $, _, PerfectScrollbar */
/* globals o_browse, o_cart, o_detail, o_hash, o_menu, o_mutationObserver, o_search, o_utils, o_widgets */
/* globals default_columns, default_widgets, default_sort_order, static_url */

// generic globals, hmm..
/* jshint varstmt: false */
var default_pages = {"gallery":1, "dataTable":1, "cart_gallery":1, "cart_data":1 };
/* jshint varstmt: true */

// defining the opus namespace first; document ready comes after...
/* jshint varstmt: false */
var opus = {
/* jshint varstmt: true */


    /**
     *
     *  global var declarations here
     *
     *  the main load() method = sending a new query to the server, gets a result count
     *  and makes any subsequent hinting calls
     *
     **/

    // Vars
    // default vars are found in the menu.html template
    // and declared in ui.views.defaults
    spinner: '<img border = "0" src = "' + static_url + 'img/spinner_12px.gif">',

    // avoiding race conditions in ajax calls
    lastRequestNo: 0,          // holds request numbers for main result count loop,
    lastAllNormalizeRequestNo: 0,
    lastResultCountRequestNo: 0,
    waitingForAllNormalizedAPI: false,

    // client side prefs, changes to these *do not trigger results to refresh*
    // prefs gets added verbatim to the url, so don't add anything weird into here!
    // prefs key:value pair order has been re-organized to match up with normalized url
    prefs: {
        "cols": default_columns.split(","),  // default result table columns by slug
        "widgets": [], // search tab widget columns
        "order": default_sort_order.split(","),  // result table ordering
        "view": "search", // search, browse, cart, detail
        "browse": "gallery", // either 'gallery' or 'data'
        "cart_browse": "gallery",  // which view is showing on the cart page, gallery or data
        "startobs": 1, // for this branch it will not get updated
        "cart_startobs": 1, // for this branch it will not get updated
        "detail": "", // opus_id of detail page content
        "page": default_pages,  // what page are we on, per view, default defined in header.html
                               // like {"gallery":1, "data":1, "cart_gallery":1, "cart_data":1 };
        "limit": 100, // results per page
     }, // pref changes do not trigger load()

    col_labels: [],  // contains labels that match prefs.cols, which are slugs for each column label
                      // it's outside of prefs because those are things loaded into urls
                      // this is not
                      // note that this is also not a dictionary because we need to preserve the order.


    lastPageDrawn: {"browse":0, "cart":0},

    // additional defaults are in base.html

    // searching - making queries
    selections:{},        // the user's search
    extras:{},            // extras to the query, carries units, string_selects, qtypes, size, refreshes result count!!
    last_selections:{},   // last_ are used to moniter changes
    last_hash:'',
    result_count:0,
    qtype_default: 'any',
    force_load: true, // set this to true to force load() when selections haven't changed

    // searching - ui
    widgets_drawn:[], // keeps track of what widgets are actually drawn
    widgets_fetching:[], // this widget is currently being fetched
    widget_elements_drawn:[], // the element is drawn but the widget might not be fetched yet
    widget_full_sizes:{}, // when a widget is minimized and doesn't have a custom size defined we keep track of what the full size was so we can restore it when they unminimize/maximize widget
    menu_state: {'cats':['obs_general']},
    default_widgets: default_widgets.split(','),
    widget_click_timeout:0,

    // browse tab
    pages:0, // total number of pages this result

    // cart
    cart_change:true, // cart has changed since last load of cart_tab
    cart_q_intrvl: false,
    cart_options_viz:false,

    // these are for the process that detects there was a change in the selection criteria and updates things
    main_timer:false,
    main_timer_interval:1000,

    allInputsValid: true,

    helpPanelOpen: false,

    minimumPSLength: 30,
    //------------------------------------------------------------------------------------//
    load: function() {
        /* When user makes any change to the interface, such as changing a query,
        the load() will send an ajax request to the server to get information it
        needs to update any hinting (green numbers), result counts, browse results
        tab etc. Load watches for changes to the hash to know
        whether to fire an ajax call.
        */

        let selections = o_hash.getSelectionsFromHash();

        if (selections === undefined) {
            return;
        }

        // if (!$.isEmptyObject(opus.selections) || !opus.checkIfDrawnWidgetsAreDefault() || !opus.checkIfMetadataAreDefault()) {
        if ($.isEmptyObject(selections) || !opus.checkIfDrawnWidgetsAreDefault()) {
            $(".op-reset-button button").prop("disabled", false);
        } else  if (!opus.checkIfMetadataAreDefault()) {
            $(".op-reset-button .op-reset-search-metadata").prop("disabled", false);
            $(".op-reset-button .op-reset-search").prop("disabled", true);
        } else {
            $(".op-reset-button button").prop("disabled", true);
        }

        // compare selections and last selections
        if (o_utils.areObjectsEqual(selections, opus.last_selections)) {
            // selections have not changed from opus.last_selections
            if (!opus.force_load) { // so we do only non-reloading pref changes
                return;
            }
        } else {
            // selections in the url hash is different from opus.last_selections
            // reset the pages:
            opus.prefs.page = default_pages;

            // create an object from selections to compare with opus.selections
            let modifiedSelections = {};
            $.each(Object.keys(selections), function(idx, slug) {
                // Note: when we select qtype, it is not updated in opus.selections
                // Therefore, we will not put qtype in modifiedSelections to compare with opus.selection
                if (!slug.match(/qtype/)) {
                    modifiedSelections[slug] = selections[slug][0].replace("+", " ").split(",");
                }
            });

            // if data in selections !== data in opus.selections, it means selections are modified manually in url, reload the page (modified url in url bar and hit enter)
            if (!o_utils.areObjectsEqual(modifiedSelections, opus.selections)) {
                opus.selections = modifiedSelections;
                location.reload();
                return;
            } else {
                // and reset the query:
                o_browse.resetQuery();
            }
        }
        opus.force_load = false;

        // start the result count spinner and do the yellow flash
        $("#op-result-count").html(opus.spinner).parent().effect("highlight", {}, 500);
        $("#op-observation-number").html(opus.spinner).effect("highlight", {}, 500);

        // start op-menu-text and op-search-widgets spinner
        // this is to trigger these two spinners right away when result count spinner is running
        $(".op-menu-text.spinner").addClass("op-show-spinner");
        $("#op-search-widgets .spinner").fadeIn();

        // update last selections after the comparison of selections and last selections
        // move this above allNormalizedApiCall to avoid recursive api call
        opus.last_selections = selections;

        // chain ajax calls, validate range inputs before result count api call
        o_search.allNormalizedApiCall().then(opus.getResultCount).then(opus.updatePageAfterResultCountAPI);
    },

    // Normalized URL API call
    normalizedURLAPICall: function() {
        let hash = o_hash.getHash();
        // Note: We don't need a reqno here.
        // Because in our implementation, this api is call at the beginning of document ready (or when reload), and every time this event is triggered, it means everything is reloaded. If we put reqno here, reqno will always be 1, so we don't need reqno.
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

    getResultCount: function(normalizedData) {
        // // we need this to avoid unecessary result count api call
        if (normalizedData.reqno < opus.lastAllNormalizeRequestNo) {
            return;
        }
        o_search.validateRangeInput(normalizedData, true);

        // query string has changed
        // opus.last_selections = selections;
        opus.lastResultCountRequestNo++;
        let resultCountHash = o_hash.getHash();

        if (!opus.allInputsValid) {
            // remove spinning effect on browse count
            $("#op-result-count").text("?");
            $("#op-observation-number").html("?");
            return;
        }

        return $.getJSON("/opus/__api/meta/result_count.json?" + resultCountHash + "&reqno=" + opus.lastResultCountRequestNo);
    },

    updatePageAfterResultCountAPI: function(resultCountData) {
        if (!opus.allInputsValid || !resultCountData) {
            return;
        }
        if (resultCountData.data[0].reqno < opus.lastResultCountRequestNo) {
            return;
        }
        $("#browse_tab").fadeIn();
        opus.updateResultCount(resultCountData.data[0].result_count);

        o_menu.getMenu();

        // if all we wanted was a new gallery page we can stop here
        opus.pages = Math.ceil(opus.result_count/opus.prefs.limit);
        if (opus.prefs.view == "browse") {
            return;
        }

        // result count is back, now send for widget hinting
        $.each(opus.prefs.widgets, function(index, slug) {
            o_search.getHinting(slug);
        });
    },

    updateResultCount: function(result_count) {
        opus.result_count = result_count;
        $("#op-result-count").fadeOut("fast", function() {
            $(this).html(o_utils.addCommas(opus.result_count)).fadeIn("fast");
            $(this).removeClass("browse_results_invalid");
        });
    },

    triggerNavbarClick: function() {
        $('.nav-item a[href="#'+opus.prefs.view+'"]').trigger("click");
    },

    lastBlogUpdate: function() {
        $.getJSON("/opus/__lastblogupdate.json", function(data) {
            if (data.lastupdate !== null) {
                let last_update_date = new Date(data.lastupdate);
                let today = Date.now();
                let days = (today - last_update_date.valueOf())/1000/60/60/24;
                if (days <= 7) {
                    $(".blogspot img").show();
                } else {
                    $(".blogspot img").hide();
                }
                let pretty_date = last_update_date.toLocaleDateString('en-GB', options={year: 'numeric', month: 'long', day: 'numeric'});
                $("#last_blog_update_date").attr("title", "Blog last updated "+pretty_date);
            } else {
                $("#last_blog_update_date").attr("title", "");
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
        opus.lastBlogUpdate();

        switch(opus.prefs.view) {

            case 'search':
                window.scrollTo(0,0);
                $('#search').fadeIn();
                o_search.getSearchTab();
                break;

            case 'browse':
                if (opus.prefs.browse == 'dataTable') {
                    $('.gallery','#browse').hide();
                    $('.data','#browse').show();
                }
                $('#browse').fadeIn();
                o_browse.getBrowseTab();

                break;

            case 'detail':
                $('#detail').fadeIn();

                o_detail.getDetail(opus.prefs.detail);
                break;

            case 'cart':
                if (opus.prefs.cart_browse == 'data') {
                    $('.data_table','#cart').show();
                    $('.gallery','#cart').hide();
                }
                $('#cart').fadeIn();
                o_cart.getCartTab();
                break;

            default:
                o_search.getSearchTab();

        } // end switch

    },

    startOver: function(resetMetadata=false) {
        // handles the 'start over' buttons which has 2 selections
        // if keep_set_widgets is true it will leave the current selected widgets alone
        // and just redraw them with no selections in them
        // if keep_set_widgets is false it will remove all widgets and restore
        // the application default widgets

        clearInterval(opus.main_timer);  // stop polling for UI changes for a moment
        $("#search_widgets").empty(); // remove all widgets on the screen

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

        if (resetMetadata && !opus.checkIfMetadataAreDefault()) {
            opus.prefs.cols = [];
            o_browse.resetMetadata(default_columns.split(','), true);
            $(".op-reset-button button").prop("disabled", true);
        } else if (!opus.checkIfMetadataAreDefault()) {
            $(".op-reset-button .op-reset-search-metadata").prop("disabled", false);
            $(".op-reset-button .op-reset-search").prop("disabled", true);
        } else {
            $(".op-reset-button button").prop("disabled", true);
        }

        o_menu.markDefaultMenuItem();

        let deferredArr = [];
        $.each(opus.default_widgets, function(index, slug) {
            deferredArr.push($.Deferred());
            o_widgets.getWidget(slug,"#search_widgets",deferredArr[index]);
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
    checkIfDrawnWidgetsAreDefault: function() {
        if (opus.prefs.widgets.length !== opus.default_widgets.length) {
            return false;
        }
        let reversedDefaultWidgets = new Array(...opus.default_widgets);
        reversedDefaultWidgets.reverse();
        let defaultWidgetsString = JSON.stringify(reversedDefaultWidgets);
        let drawnWidgetsString = JSON.stringify(opus.prefs.widgets);
        if (defaultWidgetsString !== drawnWidgetsString) {
            return false;
        }
        return true;
    },

    // check if current cols (metadata) are default ones
    checkIfMetadataAreDefault: function() {
        if (opus.prefs.cols.length !== default_columns.split(',').length) {
            return false;
        }
        let defaultColsString = JSON.stringify(default_columns.split(','));
        let selectedColsString = JSON.stringify(opus.prefs.cols);
        if (defaultColsString !== selectedColsString) {
            return false;
        }
        return true;
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

            if (!$.isEmptyObject(opus.selections) || !opus.checkIfDrawnWidgetsAreDefault()) {
                $(targetModal).modal("show");
            } else if (targetModal === "#op-reset-search-metadata-modal" && !opus.checkIfMetadataAreDefault()) {
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
                            opus.startOver(resetMetadata=true);
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
