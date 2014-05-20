/*
 * there are 3 main content sections can use for jquery contexts: search, browse, detail
 *
 */



$(document).ready(function() {

    o_hash.initFromHash(); // just returns null if no hash

    // main navbar behaviors
    $('#navbar').on("click", '.navbar-nav li', function() {

        // handle showing what menu tab is active
        $('.navbar-nav li').each(function(index) {
            if ($(this).hasClass("active")) {
                $(this).toggleClass("active");
                return false; // aka break from each
            }
        });

        tab = $(this).find('a').attr('href').substring(1);
        if (tab == '/') {
            return true;
        }
        if (!tab) { tab = "search"; }
        $(this).addClass("active");
        opus.prefs.view = tab;

        opus.changeTab();

        return false;

    });

    // figure out which tab is up now
    opus.changeTab();


    $('.navbar-nav li a[href="#search"]', '#navbar').trigger("click");

    // initiate the correct view behavior - which tab is on top on page load

    opus.addAllBehaviors();

    // watching the url for changes
    setInterval(opus.load, 1000);
    return;

    $('#search').css('display','inline-block');

    o_collections.initCollection();

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

    // client side prefs, changes to these do not trigger page/query load
    prefs:{ 'view':'search',
            'page':1,
            'colls_page':1,
            'limit': 100,
            'widgets':[],
            'widgets2':[],
            'widget_size':{},
            'widget_scroll':{},
            'browse':'gallery',        // which view is showing on the browse tab, gallery or table
            'colls_browse':'gallery',  // which view is showing on the collections page, gallery or table
            'detail':'',
            'order':'',
            'cols': default_columns.split(','),
     }, // pref changes do not trigger load()

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
    activeWidgetRequest: [],   // prevents repeat calling to server to get widgets
    user_clicked:true, // if false form updates when hash changes
    page_monitor:[],       // holds page number in results during polling
    input_timer:false,     // triggers start of polling an input field when true
    widgets_drawn:[], // keeps track of what widgets are actually drawn
    widgets_fetching:[], // this widget is currently being fetched
    widget_elements_drawn:[], // the element is drawn but the widget might not be fetched yet
    widgets_paused:[],
    search_form_cols:1, // the number of search form cols, 1 or 2
    widget_full_sizes:{}, // when a widget is minimized and doesn't have a custom size defined we keep track of what the full size was so we can restore it when they unminimize/maximize widget
    menu_list_indicators: {'slug':[], 'cat':[], 'group':[] },
    menu_state: {'cats':['obs_general'], 'groups':[]},  // keep track of menu items that are open

    // browse tab
    pages:0, // total number of pages
    colls_pages:0, // total number of collections pages
    text_field_monitor:[], // holds text-field-entries during polling
    browse_footer_clicks:{'gallery':0, 'data':0, 'colls_gallery':0, 'colls_data':0 },
    browse_footer_clicked:false,
    browse_auto:'.chosen_columns', // we are turning this on as default
    browse_footer_style_disabled: false,  // keeps track of whether we have
    scroll_watch_interval:'',
    browse_empty:true, // zero results on browse tab AND no ajax calls to get data have been sent
    footer_clicks_trigger: 0, // number of results footer clicks *after first* to trigger form that lets user set auto, -1 to turn off (not tested)
    page_bar_offsets:{},  // list of bars that indicate page in infinite scrolling
    browse_controls_fixed:false, // indicates whether browse controle bar is fixed at top of screen
    current_page_msg:"",
    column_chooser_drawn:false,
    last_page:{ 'browse':{ 'data':0, 'gallery':0 }, 'colls_browse':{ 'data':0, 'gallery':0 }},
    browse_tab_click:false,

    // collections
    collection_queue:[],
    collection_change:false, // collection has changed wince last load of collection_tab
    addrange_clicked:false,
    addrange_min:false,
    page_colls_monitor:[],  // cart view has it's own page count
    collection_q_intrvl: false,
    colls_options_viz:false,

    //------------------------------------------------------------------------------------//

    load: function () {
      	  selections = o_hash.getSelectionsFromHash();
      	  if (!selections) {
              if (opus.result_count!='0') {
                  $('.hints').html("");  // remove all hints
                  opus.updateResultCount('0');
              }
              if (opus.last_selections) {
      	          opus.last_selections = {};
      	      }
      	      return;
      	  }
          if (o_utils.areObjectsEqual(selections, opus.last_selections))  {
              // selections haven't changed
              if (!opus.force_load) { // only non-loading pref changes
                  return;
              }
          } else {
              // selections changed, reset page
              if (!opus.browse_empty) {
                  // there was a last selections, clear results containers
                  opus.prefs.page = 1;
                  $('.gallery', '#browse').empty();
                  $('.data_container', '#browse').empty();
                  opus.browse_footer_clicks['gallery']=0;
                  opus.browse_footer_clicks['data']=0;
                  opus.browse_empty = true;
              }
          }
          opus.force_load = false;
          if (!Object.keys(selections).length) {
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

          if (!opus.user_clicked) {
              opus.user_clicked=true;
             //  window.location.reload(true);
          }


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
                  }

              } // end result count success
          }); // end result count ajax

        if (Object.keys(selections).length) opus.user_clicked=false
    }, // endfunc jeezumcrow! #shootmenow

    updateResultCount: function(result_count) {
      opus.result_count = result_count;
      $('#result_count').fadeOut('fast', function() {
          $(this).html('<span>' + o_utils.addCommas(opus.result_count) + '</span>').fadeIn('fast');
      });
    },

    addAllBehaviors: function() {
        o_search.searchBehaviors();
        o_browse.browseBehaviors();
        o_collections.collectionBehaviors();
        o_widgets.addWidgetBehaviors();
        o_menu.menuBehaviors();


        // these are the default open groups/cats
        $(".cat_label", "li.target-body", "#search").trigger("click");

    }

}; // end opus namespace

