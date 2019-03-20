// generic globals, hmm..
var default_pages = {"gallery":1, "dataTable":1, "cart_gallery":1, "cart_data":1 };
var reset_footer_clicks = {"gallery":0, "dataTable":0, "cart_gallery":0, "cart_data":0 };
var reset_browse_view_scrolls = {"gallery":0, "dataTable":0, "cart_gallery":0, "cart_data":0 };

// defining the opus namespace first; document ready comes after...
var opus = {


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

    download_in_process: false,

    // client side prefs, changes to these *do not trigger results to refresh*
    // prefs gets added verbatim to the url, so don't add anything weird into here!
    prefs:{ 'view':'search', // search, browse, cart, detail
            'browse':'gallery', //either 'gallery' or 'data'
            'cart_browse':'gallery',  // which view is showing on the cart page, gallery or data
            'page':default_pages,  // what page are we on, per view, default defined in header.html
                                   // like {"gallery":1, "data":1, "cart_gallery":1, "cart_data":1 };
            'limit': 100, // results per page
            'order': default_sort_order.split(','),  // result table ordering
            'cols': default_columns.split(','),  // default result table columns by slug
            'widgets':[], // search tab widget columns
            'detail':'', // opus_id of detail page content


     }, // pref changes do not trigger load()

    col_labels: [],  // contains labels that match prefs.cols, which are slugs for each column label
                      // it's outside of prefs because those are things loaded into urls
                      // this is not
					  // note that this is also not a dictionary because we need to preserve the order.

    gallery_data: {},  // holds gallery column data

    lastPageDrawn: {"browse":0, "cart":0},
    pages_drawn: {"browse": [], "cart": []},  // keeping track of currently rendered gallery pages
                                                          // so underlying data can be refreshed after 'choose metadata'

    // additional defaults are in base.html

    // searching - making queries
    selections:{},        // the user's search
    extras:{},            // extras to the query, carries units, string_selects, qtypes, size, refreshes result count!!
    last_selections:{},   // last_ are used to moniter changes
    last_hash:'',
    result_count:0,
    qtype_default: 'any',
    force_load: false, // set this to true to force load() when selections haven't chnaged

    // searching - ui
    search_tab_drawn: false,
    widgets_drawn:[], // keeps track of what widgets are actually drawn
    widgets_fetching:[], // this widget is currently being fetched
    widget_elements_drawn:[], // the element is drawn but the widget might not be fetched yet
    search_form_cols:1, // the number of search form cols, 1 or 2
    widget_full_sizes:{}, // when a widget is minimized and doesn't have a custom size defined we keep track of what the full size was so we can restore it when they unminimize/maximize widget
    menu_list_indicators: {'slug':[], 'cat':[], 'group':[] },
    // menu_state: {'cats':['obs_general'], 'groups':[]},  // keep track of menu items that are open
    menu_state: {'cats':['obs_general']},
    default_widgets: default_widgets.split(','),
    widget_click_timeout:0,

    // browse tab
    pages:0, // total number of pages this result
    browse_auto:'.chosen_columns', // we are turning this on as default
    metadata_selector_drawn:false,
    gallery_begun:false, // have we started the gallery view
    browse_view_scrolls: reset_browse_view_scrolls, // same defaults as footer clicks (definied in header.html)
                                                      // {"gallery":0, "data":0, "cart_gallery":0, "cart_data":0 };

    // cart
    cart_change:true, // cart has changed since last load of cart_tab
    cart_q_intrvl: false,
    cart_options_viz:false,

    // these are for the process that detects there was a change in the selection criteria and updates things
    main_timer:false,
    main_timer_interval:1000,

    allInputsValid: true,

    helpPanelOpen: false,
    //------------------------------------------------------------------------------------//

    load: function () {
        /* When user makes any change to the interface, such as changing a query,
        the load() will send an ajax request to the server to get information it
        needs to update any hinting (green numbers), result counts, browse results
        tab etc. Load watches for changes to the hash to know
        whether to fire an ajax call.
        */

        selections = o_hash.getSelectionsFromHash();

        // if (!$.isEmptyObject(opus.selections) || !opus.checkIfDrawnWidgetsAreDefault() || !opus.checkIfMetadataAreDefault()) {
        if (selections || !opus.checkIfDrawnWidgetsAreDefault()) {
            $(".op-reset-button button").prop("disabled", false);
        } else  if (!opus.checkIfMetadataAreDefault()) {
            $(".op-reset-button .op-reset-search-metadata").prop("disabled", false);
            $(".op-reset-button .op-reset-search").prop("disabled", true);
        } else {
            $(".op-reset-button button").prop("disabled", true);
        }

        if (!selections) {
            // there are no selections found in the url hash
            if (!jQuery.isEmptyObject(opus.last_selections)) {
                // last selections is also empty
                opus.last_selections = {};
                o_browse.resetQuery();
            }
        }

        if (o_utils.areObjectsEqual(selections, opus.last_selections))  {
            // selections have not changed from opus.last_selections
            if (!opus.force_load) { // so we do only non-reloading pref changes
                return;
            }
            opus.force_load = false;

        } else {
            // selections in the url hash is different from opus.last_selections
              // reset the pages:
              opus.prefs.page = {"gallery":1, "data":1, "cart_gallery":1, "cart_data":1 };

              // and reset the query:
              o_browse.resetQuery();
        }

        // start the result count spinner and do the yellow flash
        $("#result_count").html(opus.spinner).parent().effect("highlight", {}, 500);
        // move this above allNormalizedApiCall to avoid recursive api call
        opus.last_selections = selections;

        // chain ajax calls, validate range inputs before result count api call
        o_search.allNormalizedApiCall().then(opus.getResultCount).then(opus.updatePageAfterResultCountAPI);
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

        if(!opus.allInputsValid) {
            // remove spinning effect on browse count
            $("#result_count").text("?");
            return;
        }

        return $.getJSON("/opus/__api/meta/result_count.json?" + resultCountHash + "&reqno=" + opus.lastResultCountRequestNo);
    },

    updatePageAfterResultCountAPI: function(resultCountData) {
        if(!opus.allInputsValid || !resultCountData) {
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
            $("#pages","#browse").html(opus.pages);
            return;
        }

        // result count is back, now send for widget hinting
        for (k in opus.prefs.widgets) {
            slug = opus.prefs.widgets[k];
            o_search.getHinting(slug);
        } // endfor
    },

    updateResultCount: function(result_count) {
        opus.result_count = result_count;
        $("#result_count").fadeOut("fast", function() {
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

        if(resetMetadata && !opus.checkIfMetadataAreDefault()) {
            opus.prefs.cols = [];
            o_browse.resetMetadata(default_columns.split(','), true);
            $(".op-reset-button button").prop("disabled", true);
        } else if(!opus.checkIfMetadataAreDefault()) {
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
        // wait until all widgets are get
        $.when.apply(null, deferredArr).then(function(){
            let adjustSearchWidgetHeight = _.debounce(o_search.adjustSearchHeight, 800);
            adjustSearchWidgetHeight();
        });

        // if(resetMetadata) {
        //     $(".op-reset-button button").prop("disabled", false);
        // } else if(!opus.checkIfMetadataAreDefault()) {
        //     $(".op-reset-button .op-reset-search-metadata").prop("disabled", false);
        //     $(".op-reset-button .op-reset-search").prop("disabled", true);
        // } else {
        //     $(".op-reset-button button").prop("disabled", true);
        // }

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
        if(opus.prefs.widgets.length !== opus.default_widgets.length) {
            return false;
        }
        let reversedDefaultWidgets = new Array(...opus.default_widgets)
        reversedDefaultWidgets.reverse();
        let defaultWidgetsString = JSON.stringify(reversedDefaultWidgets);
        let drawnWidgetsString = JSON.stringify(opus.prefs.widgets);
        if(defaultWidgetsString !== drawnWidgetsString) {
            return false;
        }
        return true;
    },

    // check if current cols (metadata) are default ones
    checkIfMetadataAreDefault: function() {
        if(opus.prefs.cols.length !== default_columns.split(',').length) {
            return false;
        }
        let defaultColsString = JSON.stringify(default_columns.split(','));
        let selectedColsString = JSON.stringify(opus.prefs.cols);
        if(defaultColsString !== selectedColsString) {
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
        if(opus.helpScrollbar) {
            // Make ps always start from top
            $("#op-help-panel .card-body").scrollTop(0);
            opus.helpScrollbar.update();
        }
    }
}; // end opus namespace

/*
 * there are 3 main content sections can use for jquery contexts: search, browse, detail
 *
 */

$(document).ready(function() {

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

    o_hash.initFromHash(); // just returns null if no hash

    if (!opus.prefs.view) {
        opus.prefs.view = 'search';
    }

    var adjustSearchHeight = _.debounce(o_search.adjustSearchHeight, 200);
    var adjustBrowseHeight = _.debounce(o_browse.adjustBrowseHeight, 200);
    var adjustTableSize = _.debounce(o_browse.adjustTableSize, 200);
    var adjustProductInfoHeight = _.debounce(o_cart.adjustProductInfoHeight, 200);
    var adjustDetailHeight = _.debounce(o_detail.adjustDetailHeight, 200);
    var adjustHelpPanelHeight = _.debounce(opus.adjustHelpPanelHeight, 200);

    $( window ).on("resize", function() {
        adjustSearchHeight();
        adjustBrowseHeight();
        adjustTableSize();
        adjustProductInfoHeight();
        adjustDetailHeight();
        adjustHelpPanelHeight();
    });

    // add the navbar clicking behaviors, selecting which tab to view:
    // see triggerNavbarClick
    $("#op-main-nav").on("click", ".main_site_tabs .nav-item", function() {
        if ($(this).hasClass("external-link")) {
            // this is a link to an external site, so just go there...
            return true;
        }

        // find out which tab they clicked
        var tab = $(this).find("a").attr("href").substring(1);
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
        var header = "";
        switch ($(this).data("action")) {
            case "about":
                url += "about.html";
                header = "About OPUS";
                break;
            case "datasets":
                url += "datasets.html";
                header = "Datasets Available for Searching with OPUS";
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
        }

        $("#op-help-panel .op-header-text").html(`<h2>${header}</h2`);
        $("#op-help-panel .op-card-contents").html("Loading... please wait.");
        $("#op-help-panel .loader").show();
        // We only need one perfectScrollbar
        if(!opus.helpScrollbar) {
            opus.helpScrollbar = new PerfectScrollbar("#op-help-panel .card-body", { suppressScrollX: true });
        }
        adjustHelpPanelHeight();
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
                adjustHelpPanelHeight()
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
            $(targetModal).modal("show")
        } else if(targetModal === "#op-reset-search-metadata-modal" && !opus.checkIfMetadataAreDefault()){
            $(targetModal).modal("show")
        }
    });

    $(".confirm-modal").on("click", ".btn", function() {
        let target = $(this).data("target");
        switch($(this).attr("type")) {
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
            case "cancel":
                $(".modal").modal("hide")
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

    opus.addAllBehaviors();

    o_cart.initCart();
    opus.triggerNavbarClick();

    // watch the url for changes, this runs continuously
    opus.main_timer = setInterval(opus.load, opus.main_timer_interval);

    return;

});
