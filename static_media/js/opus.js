/*
 * there are 3 main content sections can use for jquery contexts: search, browse, detail
 *
 */

$(document).ready(function() {


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
            console.log(left_margin);
            $('#cboxContent').animate({
                left:left_margin
            }, 'fast');
            */
            if ($('#cboxOverlay .gallery_data_viewer').is(':visible')) { // :visible being used here to see if element exists)
                // colorbox is showing, lets reload it so it shows
                // the orientation it will show when they next page
                // first get the ring_obs_id
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
    opus.changeTab();

    // add the navbar clicking behaviors, selecting which tab to view:
    // see triggerNavbarClick
    $('#navbar').on("click", '.navbar-nav li', function() {

        if ($(this).find('a').hasClass('old_opus')) {
            return;
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
    $('#navbar').on("click", ".restart", function() {

        // this removes all from collection on every restart, a stop-gap until we fix issue
        // $.ajax({ url: "/opus/collections/reset.html"});

        // this might be temporary, reset widgets on restart
        opus.prefs.widgets = [];
        opus.prefs.widgets2 = [];
        opus.widgets_drawn = [];
        o_widgets.updateWidgetCookies();
        // end widgets part

        window.location.hash = '';
        window.location.href = "/opus";
        return false;
    }),

    opus.addAllBehaviors();

    // watch the url for changes, this runs continuously
    setInterval(opus.load, 1000);

    o_collections.initCollection();

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
    spinner: '<img border = "0" src = "' + static_url + 'images/spinner_12px.gif">',

    // avoiding race conditions in ajax calls
    lastRequestNo: 0,          // holds request numbers for main result count loop,
    lastCartRequestNo: 0,

    download_in_process: false,

    // client side prefs, changes to these *do not trigger results to refresh*
    prefs:{ 'view':'', // search, browse, collection, detail
            'browse':'gallery', //either 'gallery' or 'data', see all_browse_views below
            'colls_browse':'gallery',  // which view is showing on the collections page, gallery or data
            'page':default_pages,  // what page are we on, per view, default defined in header.html
                                   // like {"gallery":1, "data":1, "colls_gallery":1, "colls_data":1 };
            'gallery_data_viewer': true, // true if you want to view data in the box rather than img
            'limit': 100, // results per page
            'order':'timesec1',  // result table ordering
            'cols': default_columns.split(','),  // default result table columns by slug
            'widgets':[], // search tab widget columns
            'widgets2':[],
            'widget_size':{}, // search tab resized widgets
            'widget_scroll':{}, // search tab widget internal scroll saved
            'detail':'', // ring_obs_id of detail page content

     }, // pref changes do not trigger load()

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
    browse_view_scrolls: reset_browse_view_scrolls, // same defaults as footer clicks (definied in header.html)
                                                    // {"gallery":0, "data":0, "colls_gallery":0, "colls_data":0 };

    // collections
    collection_queue:[],
    collection_change:false, // collection has changed wince last load of collection_tab
    addrange_clicked:false,
    addrange_min:false,
    collection_q_intrvl: false,
    colls_options_viz:false,

    //------------------------------------------------------------------------------------//


    load: function () {
        selections = o_hash.getSelectionsFromHash();

        if (!selections) {

            if (opus.result_count != '0') {
              $('.hints').html("");  // remove all hints
              opus.updateResultCount('0');
            }
            if (opus.last_selections) {
                  opus.last_selections = {};
            }
            o_browse.resetQuery();

            return;
        }

        // if selections different from last_selections
        if (o_utils.areObjectsEqual(selections, opus.last_selections))  {
            // selections have not changed
            if (!opus.force_load) { // so we do only non-reloading pref changes
                return;
            }
            opus.force_load = false;

        } else if (!jQuery.isEmptyObject(opus.last_selections)) {

            // selections have changed (and last_selections is not empty)
            // if there was a last selections, clear results containers
            // and reset any browse tab things
            opus.prefs.page = default_pages;
            o_browse.resetQuery();
        }


        if (!Object.keys(opus.selections).length) {
            opus.last_selections = {};
            if (opus.result_count!='0') {
                $('.hints').html("");  // remove all hinting
                opus.updateResultCount('0');
            }
            return;
        }
        // start the result count spinner and do the yellow flasj
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
                    $('.data_container','#browse').show();
                    $('.gallery','#browse').hide();
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
        // progressive disclosing of main site tabs
        // tab labels at the top of the site are not displayed all at once
        // they appear as they are triggered, for example result tab appears when there
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
            $('ul.main_site_tabs li:nth-child(' + child + ')').fadeIn();
        }

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



