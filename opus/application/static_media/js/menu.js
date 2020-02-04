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
     *  The category/field list on the search tab or Select Metadata dialog
     *
     **/

    lastSearchMenuRequestNo: 0,

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

            o_hash.updateURLFromCurrentHash();
            return false;
        });
    },

    getNewSearchMenu: function() {
        let spinnerTimer = setTimeout(function() {
            $("#sidebar .op-menu-spinner.spinner").addClass("op-show-spinner"); }, opus.spinnerDelay);
        let hash = o_hash.getHash();

        // Figure out which categories are already expanded
        let expandedCategoryLinks = $("#sidebar .op-submenu-category").not(".collapsed");
        let expandedCategories = [];
        $.each(expandedCategoryLinks, function(index, linkObj) {
            expandedCategories.push($(linkObj).data("cat"));
        });
        let expandedCats = "";
        if (hash !== "") {
            expandedCats = "&";
        }
        expandedCats += "expanded_cats=" + expandedCategories.join();
        o_menu.lastSearchMenuRequestNo++;
        let url = `/opus/__menu.json?${hash}${expandedCats}&reqno=${o_menu.lastSearchMenuRequestNo}`;

        $.getJSON(url, function(data) {
            if (data.reqno < o_menu.lastSearchMenuRequestNo) {
                return;
            }
            $("#sidebar").html(data.html);
            o_menu.markCurrentMenuItems();
            clearTimeout(spinnerTimer);
        });
    },

    markMenuItem: function(selector, selected) {
        if (selected == undefined || selected == "select") {
            $(selector).children().css({"background": "gainsboro"});
            // We use find() here instead of just adding to the selector because
            // selector might be a string or it might be an actual DOM object
            $(selector).find(".op-search-param-checkmark").css({'opacity': 1});
        } else {
            $(selector).children().css({"background": "initial"});
            $(selector).find(".op-search-param-checkmark").css({'opacity': 0});
        }
    },

    markCurrentMenuItems: function() {
        $.each(opus.prefs.widgets, function(index, slug) {
            o_menu.markMenuItem(`.op-search-menu li > [data-slug="${slug}"]`);
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
