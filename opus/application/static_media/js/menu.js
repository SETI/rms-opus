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
                // if the widget is already showing, delete it
                // if the widget has config params, ask first...
                o_widgets.closeCard(slug, true);
                return false;
            } else {
                let menuSelector = `.op-search-menu a[data-slug=${slug}]`;
                o_menu.markMenuItem(menuSelector);
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

            o_menu.wrapTriangleArrowAndLastWordOfMenuCategory("#search");
            // Initialize all tooltips using tooltipster in menu.html
            $("#sidebar-container .op-menu-tooltip").tooltipster({
                maxWidth: opus.tooltips_max_width,
                theme: opus.tooltips_theme,
                delay: opus.tooltips_delay,
            });
        });
    },

    wrapTriangleArrowAndLastWordOfMenuCategory: function(tab) {
        /**
         * Wrap the last word of each menu category with triangle arrow. This is
         * used to group the triangle arrow and the last word of category string,
         * and make sure they will stay together when wrapped into a different
         * line.
         */
        $.each($(`${tab} .op-submenu-category .title`), function(idx, category) {
            let textArr = $(category).text().split(" ");
            let lastWord = textArr.pop();
            let spacing = textArr.length ? "&nbsp;" : "";
            let lastWordWrappingGroup = `${spacing}<span class="op-menu-triangle-group">${lastWord}` +
                                        "<span class='op-menu-arrow'></span></span>";
            $(category).html(textArr.join(" ") + lastWordWrappingGroup);
        });
    },

    markMenuItem: function(selector, selected) {
        if (selected == undefined || selected == "select") {
            $(selector).children().css({"background": "gainsboro"});
            // We use find() here instead of just adding to the selector because
            // selector might be a string or it might be an actual DOM object
            $(selector).find(".op-search-param-checkmark").css({'opacity': 1});
            $(selector).addClass("op-mark");
        } else {
            $(selector).children().css({"background": "initial"});
            $(selector).find(".op-search-param-checkmark").css({'opacity': 0});
            $(selector).removeClass("op-mark");
        }
    },

    markCurrentMenuItems: function() {
        $.each(opus.prefs.widgets, function(index, slug) {
            o_menu.markMenuItem(`#search .op-search-menu li > [data-slug="${slug}"]`);
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
