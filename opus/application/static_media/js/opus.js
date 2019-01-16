// generic globals, hmm..
var default_pages = {"gallery":1, "dataTable":1, "colls_gallery":1, "colls_data":1 };
var reset_footer_clicks = {"gallery":0, "dataTable":0, "colls_gallery":0, "colls_data":0 };
var reset_last_page_drawn = {"gallery":0, "dataTable":0, "colls_gallery":0, "colls_data":0 };
var reset_browse_view_scrolls = {"gallery":0, "dataTable":0, "colls_gallery":0, "colls_data":0 };

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
    lastCartRequestNo: 0,

    download_in_process: false,

    // client side prefs, changes to these *do not trigger results to refresh*
    // prefs gets added verbatim to the url, so don't add anything weird into here!
    prefs:{ 'view':'search', // search, browse, collection, detail
            'browse':'gallery', //either 'gallery' or 'data'
            'colls_browse':'gallery',  // which view is showing on the collections page, gallery or data
            'page':default_pages,  // what page are we on, per view, default defined in header.html
                                   // like {"gallery":1, "data":1, "colls_gallery":1, "colls_data":1 };
            'gallery_data_viewer': true, // true if you want to view data in the box rather than img
            'limit': 100, // results per page
            'order':'time1',  // result table ordering
            'cols': default_columns.split(','),  // default result table columns by slug
            'widgets':[], // search tab widget columns
            'widget_size':{}, // search tab resized widgets
            'widget_scroll':{}, // search tab widget internal scroll saved
            'detail':'', // opus_id of detail page content


     }, // pref changes do not trigger load()

    col_labels: [],  // contains labels that match prefs.cols, which are slugs for each column label
                      // it's outside of prefs because those are things loaded into urls
                      // this is not
					  // note that this is also not a dictionary because we need to preserve the order.

    gallery_data: {},  // holds gallery column data

    pages_drawn: {"colls_gallery": [], "gallery": []},  // keeping track of currently rendered gallery pages
                                                          // so underlying data can be refreshed after 'choose columns'

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
    widgets_paused:[],
    search_form_cols:1, // the number of search form cols, 1 or 2
    widget_full_sizes:{}, // when a widget is minimized and doesn't have a custom size defined we keep track of what the full size was so we can restore it when they unminimize/maximize widget
    menu_list_indicators: {'slug':[], 'cat':[], 'group':[] },
    // menu_state: {'cats':['obs_general'], 'groups':[]},  // keep track of menu items that are open
    menu_state: {'cats':'all', 'groups':[]},
    default_widgets: ['target','planet'],
    widget_click_timeout:0,

    // browse tab
    last_page_drawn: reset_last_page_drawn, // defined in header.html,
    pages:0, // total number of pages this result
    colls_pages:1, // total number of collections pages
    browse_auto:'.chosen_columns', // we are turning this on as default
    column_chooser_drawn:false,
    gallery_begun:false, // have we started the gallery view
    browse_view_scrolls: reset_browse_view_scrolls, // same defaults as footer clicks (definied in header.html)
                                                      // {"gallery":0, "data":0, "colls_gallery":0, "colls_data":0 };

    // collections
    collection_queue:[],
    collection_change:true, // collection has changed since last load of collection_tab
    collection_q_intrvl: false,
    colls_options_viz:false,

    // these are for the process that detects there was a change in the selection criteria and updates things
    main_timer:false,
    main_timer_interval:1000,

    //------------------------------------------------------------------------------------//

    load: function () {
        /* When user makes any change to the interface, such as changing a query,
        the load() will send an ajax request to the server to get information it
        needs to update any hinting (green numbers), result counts, browse results
        tab etc. Load watches for changes to the hash to know
        whether to fire an ajax call.
        */

        selections = o_hash.getSelectionsFromHash();

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
              opus.prefs.page = {"gallery":1, "data":1, "colls_gallery":1, "colls_data":1 };

              // and reset the query:
              o_browse.resetQuery();
        }


        // start the result count spinner and do the yellow flash
        $('#result_count').html(opus.spinner).parent().effect("highlight", {}, 500);

          // query string has changed
        opus.last_selections = selections;
        opus.lastRequestNo++;

        $.getJSON("/opus/__api/meta/result_count.json?" + o_hash.getHash() + '&reqno=' + opus.lastRequestNo, function(results) {
            var data = results.data[0];
            if (data['reqno'] < opus.lastRequestNo) {
                return;
            }
            $('#browse_tab').fadeIn();

            opus.updateResultCount(data['result_count']);
            o_menu.getMenu();

            // if all we wanted was a new gallery page we can stop here
            opus.pages = Math.ceil(opus.result_count/opus.prefs.limit);
            if (opus.prefs.view == "browse") {
                $('#pages','#browse').html(opus.pages);
                return;
            }

            // result count is back, now send for widget hinting
            $.each(opus.prefs.widgets, function(index, slug) {
                o_search.getHinting(slug);
            });
        });
    },

    updateResultCount: function(result_count) {
        opus.result_count = result_count;
        $('#result_count').fadeOut('fast', function() {
            $(this).html(o_utils.addCommas(opus.result_count)).fadeIn('fast') ;
        });
    },

    triggerNavbarClick: function() {
        $('.nav-item a[href="#'+opus.prefs.view+'"]').trigger("click");
    },

    changeTab: function(tab) {
        // first hide everything and stop any interval timers
        $('#search, #detail, #collection, #browse').hide();

        // close any open modals
        $("#galleryView").modal('hide');

        opus.prefs.view = tab ? tab : opus.prefs.view;
        o_hash.updateHash();

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

            case 'collection':
                if (opus.prefs.colls_browse == 'data') {
                    $('.data_table','#collection').show();
                    $('.gallery','#collection').hide();
                }
                $('#collection').fadeIn();
                o_collections.getCollectionsTab();
                break;

            default:
                o_search.getSearchTab();

        } // end switch

    },

    startOver: function() {
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
        $.each(opus.default_widgets, function(index, slug) {
            o_widgets.getWidget(slug,"#search_widgets");
        });

        // start the main timer again
        opus.main_timer = setInterval(opus.load, opus.main_timer_interval);

        return false;

    },

    addAllBehaviors: function() {
        o_widgets.addWidgetBehaviors();
        o_menu.menuBehaviors();
        o_browse.browseBehaviors();
        o_collections.collectionBehaviors();
        o_search.searchBehaviors();
        return;
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

    o_hash.initFromHash(); // just returns null if no hash

    if (!opus.prefs.view) {
        opus.prefs.view = 'search';
    }

    var adjustSearchHeight = _.debounce(o_search.adjustSearchHeight, 200);
    var adjustBrowseHeight = _.debounce(o_browse.adjustBrowseHeight, 200);
    $( window ).on("resize", function() {
        adjustSearchHeight();
        adjustBrowseHeight();
    });

    // add the navbar clicking behaviors, selecting which tab to view:
    // see triggerNavbarClick
    $('#navbar').on("click", '.main_site_tabs .nav-item', function() {
        if ($(this).hasClass('external-link')) {
            // this is a link to an external site, so just go there...
            return true;
        }

        // find out which tab they clicked
        var tab = $(this).find('a').attr('href').substring(1);
        if (tab == '/') {
            return true;  // they clicked the brand icon, take them to its link
        }

        // little hack in case something calls onclick programmatically....
        tab = tab ? tab : opus.prefs.search;
        opus.changeTab(tab);

        //$(this).find('a').blur(); // or else it holds the hover style which is stoo pid.

        //return false;

    });


    // restart button behavior - start over button
    $('#sidebar').on("click", ".restart", function() {
        // 'start over' button
        // resets query completely, resets widgets completely
        if (!$.isEmptyObject(opus.selections)) {

            if (confirm("Are you sure you want to restart? Your current search will be lost.")) {
                opus.startOver();
            }
        } else {
            opus.startOver();
        }

    }),

    // doesn't work yet
    $("footer a").on("click", function() {
        opus.search_tab_drawn = false;
        window.open(this.href);
        return false;
    }),

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

    o_collections.initCollection();
    opus.triggerNavbarClick();

    // watch the url for changes, this runs continuously
    opus.main_timer = setInterval(opus.load, opus.main_timer_interval);

    return;

});
