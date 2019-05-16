/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $ */
/* globals o_hash, o_widgets, opus */

/* jshint varstmt: false */
var o_menu = {
/* jshint varstmt: true */

    /**
     *
     *  the menu on the *search page*
     *
     **/

     addMenuBehaviors: function() {
         // click param in menu get new widget
         $("#sidebar").on("click", ".submenu li a", function() {

             let slug = $(this).data("slug");
             if (!slug) { return; }
             if ($.inArray(slug, opus.widgetsDrawn) > -1) {
                 // widget is already showing do not fetch another
                 try {
                    // scroll to widget and highlight it
                    o_widgets.scrollToWidget(`widget__#{slug}`);

                } catch(e) {
                    return false;
                }
                return false;

             } else {
                  o_menu.markMenuItem(this);
                  o_widgets.getWidget(slug,'#op-search-widgets');
             }

             o_hash.updateHash();
             return false;
         });


        // menu state - keep track of what menu items are open
        $("#sidebar").on("click", ".dropdown-toggle", function(e) {
            // for opus: keeping track of menu state, since menu is constantly refreshed
            // menu cats
            let category = $(this).data( "cat" );
            let groupElem = $(`#sidebar #submenu-${category}`);
            if ($(groupElem).hasClass("show")) {
                opus.menuState.cats.splice(opus.menuState.cats.indexOf(category), 1);
            } else {
                if ($.inArray(category, opus.menuState.cats) >= 0 ) {
                    console.log(`submenu ${category } state already in array`);
                } else {
                    opus.menuState.cats.push(category);
                }
            }
        });
     },

     getNewSearchMenu: function() {
        $('.op-menu-text.spinner').addClass("op-show-spinner");

        let hash = o_hash.getHash();

        $("#sidebar").load("/opus/__menu.html?" + hash, function() {
            // open menu items that were open before
            $("#sidebar").toggleClass("op-redraw-menu");
            $.each(opus.menuState.cats, function(key, category) {
                if ($(`#submenu-${category}`).length != 0) {
                    $(`#submenu-${category}`).collapse("show");
                } else {
                    // this is if the surface geometry target is no longer applicable so it's not
                    // on the menu, remove from the menuState
                    opus.menuState.cats.splice(opus.menuState.cats.indexOf(category), 1);
                }
            });
            $("#sidebar").toggleClass("op-redraw-menu");
            $(".menu_spinner").fadeOut("fast");

            o_menu.markCurrentMenuItems();

            $('.op-menu-text.spinner').removeClass("op-show-spinner");
        });
     },

     markMenuItem: function(selector, selected) {
        if (selected == undefined || selected == "select") {
            $(selector).css("background", "gainsboro");
            $(selector).find("i.fa-check").fadeIn().css("display", "inline-block");
        } else {
            $(selector).css("background", "initial");
            $(selector).find("i.fa-check").hide();
      }
     },

    markCurrentMenuItems: function() {
        $.each(opus.prefs.widgets, function(index, slug) {
            o_menu.markMenuItem(`li > [data-slug="${slug}"]`);
        });
    },

     // type = cat/group
     getCatGroupFromSlug: function(slug) {
         let cat = "";
         let group = "";
         $("ul.menu_list>li a", "#search").each(function() {
             if (slug == $(this).data("slug")) {
                 cat = $(this).data("cat");
                 group = $(this).data("group");
                 return false; // this is how you break in an each!
             }
         });
         return {"cat":cat, "group":group};
     },
};
