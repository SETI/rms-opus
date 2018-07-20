/*
 * there are 3 main content sections can use for jquery contexts: search, browse, detail
 *
 */

$(document).ready(function() {

    opus.prefs.widgets = [];
    o_widgets.updateWidgetCookies();

    $(window).smartresize(function(){

        o_search.adjustSearchHeight();

        // see if the metadata box is off screen, if so redraw it.
        // find left border of metadata box is > screen width.
        // if so then move it inside
        /*
        $(window).width()
        $('#cboxOverlay .gallery_data_viewer').width();
        $('#cboxOverlay .gallery_data_viewer').offset().left;
        */

        if ($('#cboxOverlay .gallery_data_viewer').is(':visible')) {
            // user is resizing browser with gallery viewer open
            // make sure they don't lose the metadata box off to the right
            // this happens only if they've previously put it there
            // alert('visible');

            /*
            window_width = $(window).width();
            left_margin = '15%';
            if (window_width < 900) {
                left_margin = '2%';
            }
            $('#cboxContent').animate({
                left:left_margin
            }, 'fast');
            */
            if ($('#cboxOverlay .gallery_data_viewer').is(':visible')) { // :visible being used here to see if element exists)
                // colorbox is showing, lets reload it so it shows
                // the orientation it will show when they next page
                // first get the opus_id
                setTimeout(o_browse.reset_colorbox(), 1500);
            }
        }

    });

    $( document ).tooltip({
        show: { delay: 300 }
    });

    o_hash.initFromHash(); // just returns null if no hash

    if (!opus.prefs.view) {
        opus.prefs.view = 'search';
    }
    //opus.changeTab();


    // add the navbar clicking behaviors, selecting which tab to view:
    // see triggerNavbarClick
    $('#navbar').on("click", 'ul.main_site_tabs li', function() {

        if ($(this).find('a').hasClass('restore_widgets')) {
            return;
        }
        if ($(this).find('a').hasClass('old_opus')) {
            return;
        }
        if ($(this).find('a').hasClass('restart')) {
            return;
        }
        if ($(this).hasClass('external-link')) {
            // this is a link to an external site, so just go there...
            return true;
        }
        // remove the active class on whatever other tab it is on
        $('.navbar-nav li', '#navbar').each(function(index, value) {
            if ($(this).hasClass("active")) {
                $(this).toggleClass("active");
                return false; // we found the active one, so break from this each
            }
        });
        $(this).addClass("active");

        // find out which tab they clicked
        tab = $(this).find('a').attr('href').substring(1);
        if (tab == '/') {
            return true;  // they clicked the brand icon, take them to its link
        }

        if (!tab) { tab = opus.prefs.search; }
        opus.prefs.view = tab;
        o_hash.updateHash();
        opus.changeTab();

        $(this).find('a').blur(); // or else it holds the hover style which is stoo pid.

        return false;

    });


    // restart button behavior - start over button
    $('#sidebar').on("click", ".restart", function() {
        // 'start over' button
        // resets query completely, resets widgets completely
        if (!jQuery.isEmptyObject(opus.selections)) {

            if (confirm("Are you sure you want to restart? Your current search will be lost.")) {
                opus.startOver();
            }
        } else {
            opus.startOver();
        }

    }),

    opus.addAllBehaviors();

    // watch the url for changes, this runs continuously
    opus.main_timer = setInterval(opus.load, opus.main_timer_interval);

    o_collections.initCollection();
    opus.triggerNavbarClick();

    return;

});

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
    prefs:{ 'view':'', // search, browse, collection, detail
            'browse':'gallery', //either 'gallery' or 'data', see all_browse_views below
            'colls_browse':'gallery',  // which view is showing on the collections page, gallery or data
            'page':default_pages,  // what page are we on, per view, default defined in header.html
                                   // like {"gallery":1, "data":1, "colls_gallery":1, "colls_data":1 };
            'gallery_data_viewer': true, // true if you want to view data in the box rather than img
            'limit': 100, // results per page
            'order':'time1',  // result table ordering
            'cols': default_columns.split(','),  // default result table columns by slug
            'widgets':[], // search tab widget columns
            'widgets2':[],
            'widget_size':{}, // search tab resized widgets
            'widget_scroll':{}, // search tab widget internal scroll saved
            'detail':'', // opus_id of detail page content

     }, // pref changes do not trigger load()

    col_labels: [],  // may be empty, contains labels that match prefs.cols
                      // it's outside of prefs becuase those are things loaded into urls
                      // this is not

    gallery_data: {},  // holds gallery column data
    all_browse_views: ['gallery','data'],

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
    activeWidgetRequest: [],   // prevents repeat calling to server to get widgets
    page_monitor_data:[],       // holds page number in results during polling
    page_monitor_gallery:[],       // holds page number in results during polling
    input_timer:false,     // triggers start of polling an input field when true
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

    // browse tab
    last_page_drawn: reset_last_page_drawn, // defined in header.html,
    pages:0, // total number of pages this result
    colls_pages:0, // total number of collections pages
    browse_footer_clicks:reset_footer_clicks, // defined in header.html
    browse_auto:'.chosen_columns', // we are turning this on as default
    browse_footer_style_disabled: false,  // keeps track of whether we have
    scroll_watch_interval:'', // holder for setInterval timer
    footer_clicks_trigger: 0, // number of results footer clicks *after first* to trigger form that lets user set auto, -1 to turn off (not tested)
    page_bar_offsets:{},  // list of bars that indicate page in infinite scrolling
    current_page_msg:"",
    column_chooser_drawn:false,
    table_headers_drawn:false,  // have we drawn the table headers
    gallery_begun:false, // have we started the gallery view
    current_metadatabox:false,
    browse_view_scrolls: reset_browse_view_scrolls, // same defaults as footer clicks (definied in header.html)
                                                      // {"gallery":0, "data":0, "colls_gallery":0, "colls_data":0 };

    // collections
    collection_queue:[],
    collection_change:false, // collection has changed wince last load of collection_tab
    addrange_clicked:false,
    addrange_min:false,
    collection_q_intrvl: false,
    colls_options_viz:false,
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

      	  // get result count
          $.ajax({ url: "/opus/api/meta/result_count.json?" + o_hash.getHash() + '&reqno=' + opus.lastRequestNo,
              dataType:"json",
              success: function(json){

                  if (json['reqno'] < opus.lastRequestNo) {
                      return;
                  }
                  $('#browse_tab').fadeIn();
                  opus.updateResultCount(json['data'][0]['result_count']);

                  opus.mainTabDisplay('results');  // make sure the main site tab label is displayed

                  o_menu.getMenu();

                  // if all we wanted was a new gallery page we can stop here
                  opus.pages = Math.ceil(opus.result_count/opus.prefs.limit);
                  if (opus.prefs.view == "browse") {
                      $('#pages','#browse').html(opus.pages);
                      return;
                  }

                  // result count is back, now send for widget hinting
                  var widget_cols = ['widgets','widgets2'];
                  for (key in widget_cols) {
                      col = widget_cols[key];
                      for (k in opus.prefs[col]) {
                          slug = opus.prefs[col][k];
                          o_search.getHinting(slug);
                      } // end for widget in..
                  } // endfor
              } // end result count success
          }); // end result count ajax
    }, // endfunc jeezumcrow! #shootmenow

    updateResultCount: function(result_count) {
      opus.result_count = result_count;
      $('#result_count').fadeOut('fast', function() {
        $(this).html(o_utils.addCommas(opus.result_count)).fadeIn('fast') ;
      });
    },

    triggerNavbarClick: function() {
        $('.navbar-nav li a[href="#' + opus.prefs.view + '"]', '#navbar').trigger("click");
    },

    changeTab: function() {
        // first hide everything and stop any interval timers
        $('#search, #detail, #collection, #browse').hide();
        clearInterval(opus.scroll_watch_interval);
        clearInterval(opus.collection_q_intrvl);

        switch(opus.prefs.view) {

            case 'search':
                window.scroll(0,0);
                $('#search').fadeIn();
                o_search.getSearchTab();
                break;

            case 'browse':
                if (opus.prefs.browse == 'data') {
                    $('.gallery','#browse').hide();
                    $('.data','#browse').show();
                }
                $('#browse').fadeIn();
                o_browse.getBrowseTab();

                break;

            case 'detail':
                $('#detail').fadeIn();

                o_detail.getDetail(opus.prefs.detail);

                opus.collection_q_intrvl = setInterval("o_collections.processCollectionQueue()", 1000); // resends any stray requests not recvd back from server

                break;

            case 'collection':
                opus.collection_change = true;
                if (opus.prefs.colls_browse == 'data') {
                    $('.data_table','#collection').show();
                    $('.gallery','#collection').hide();
                }
                $('#collection').fadeIn();
                o_collections.getCollectionsTab();

                opus.collection_q_intrvl = setInterval("o_collections.processCollectionQueue()", 1000); // resends any stray requests not recvd back from server

                break;

            default:
                o_search.getSearchTab();

        } // end switch

    },

    mainTabDisplay: function(tabname) {
        // disclosing of main site tabs
        // tab labels at the top of the site are not displayed all at once
        // become some results, etc

        switch (tabname) {
            case "results":
                child = 2;  // results is the 2nd tab
                break;

            case "collection":
                child = 3;
                break;

            case "detail":
                child = 4;
                break;
        }

        if (!$('ul.main_site_tabs li:nth-child(' + child + ')').is(":visible")) {
            $('ul.main_site_tabs li:nth-child(' + child + ')').addClass('tab_display');
        }

    },


    startOver: function() {
        // handles the 'start over' buttons which has 2 selections
        // if keep_set_widgets is true it will leave the current selected widgets alone
        // and just redraw them with no selections in them
        // if keep_set_widgets is false it will remove all widgets and restore
        // the application default widgets

        clearInterval(opus.main_timer);  // hold the phone for a sec
        $('.widget-container-span').empty(); // remove all widgets on the screen

        // reset the search query
        opus.selections = {};
        o_browse.resetQuery();
        opus.prefs.view = 'search';
        opus.changeTab();

        keep_set_widgets = false  // use as argument for the 2 tiered start over button, currently disabled
        if (keep_set_widgets) {
            // redraw all widgets that user had open before
            // this is the 'start over' behavior
            opus.widgets_drawn = [];
            for (key in opus.prefs.widgets) {
                slug = opus.prefs.widgets[key];
                o_widgets.getWidget(slug,'#search_widgets1');
            }
            window.location.hash = '/cols=' + opus.prefs.cols.join(',');

        } else {
            // resets widgets drawn back to system default
            // in the 2 tier button this was the 'start over and restore defaults' behavior
            // note: this is the current deployed behavior for the single 'start over' button
            opus.prefs.widgets2 = [];
            opus.prefs.widgets = [];
            opus.widgets_drawn = [];
            opus.widget_elements_drawn = [];
            for (k in opus.default_widgets) {
                slug = opus.default_widgets[k];
                o_widgets.getWidget(slug,'#search_widgets1');
            }
        }

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


        // these are the default open groups/cats in search tab side menu
        $(".cat_label", "li.target-body", "#search").trigger("click");

    }

}; // end opus namespace


// Paul Irish's smartresize: http://www.paulirish.com/2009/throttled-smartresize-jquery-event-handler/
(function($,sr){

  // debouncing function from John Hann
  // http://unscriptable.com/index.php/2009/03/20/debouncing-javascript-methods/
  var debounce = function (func, threshold, execAsap) {
      var timeout;

      return function debounced () {
          var obj = this, args = arguments;
          function delayed () {
              if (!execAsap)
                  func.apply(obj, args);
              timeout = null;
          };

          if (timeout)
              clearTimeout(timeout);
          else if (execAsap)
              func.apply(obj, args);

          timeout = setTimeout(delayed, threshold || 100);
      };
  }
  // smartresize
  jQuery.fn[sr] = function(fn){  return fn ? this.bind('resize', debounce(fn)) : this.trigger(sr); };

})(jQuery,'smartresize');
