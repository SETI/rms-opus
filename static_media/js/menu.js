var o_menu = {

    /**
     *
     *  the menu on the *search page*
     *
     **/

     menuBehaviors: function() {
         // search menu behaviors

         // click param in menu get new widget
         $('#search').on("click", '.submenu li a', function() {
             slug = $(this).data('slug');
             if (!slug) { return; }
             if (jQuery.inArray(slug, opus.widgets_drawn)>-1){
                 // widget is already showing do not fetch another
                 try {
                    $('#widget__'+slug + ' .widget-main').effect("highlight", "slow");
                } catch(e) {
                    return false;
                }
                 return false;
             } else {
                 o_widgets.getWidget(slug,'#search_widgets1');
             }
             o_hash.updateHash();
             return false;
         });


        // need to keep track of what menu groups are open, something like:
        /*
        if (jQuery.inArray(cat, opus.menu_cats_open) < 0) {
            opus.menu_cats_open.push(cat);
        }
        */

        // check if this menu group only has one option, if so just open that widget
        // I'm commenting this out because I do not agree that it is desirable
        // with the new menu behavior
        /*
        if ($(this).next().children().size() == 1) {
            $(this).next().find('li a').trigger("click");
        }
        */


     },

     getMenu: function() {
        // $('.menu_spinner').fadeIn("fast");
        hash = o_hash.getHash();
        $( "#sidebar").load( "/opus/menu.html?" + hash, function() {

            // open menu items that were open before
            for (var key in opus.menu_state['cats']) {
                cat_name = opus.menu_state['cats'][key];
                $("." + cat_name, ".sidebar").trigger(ace.click_event);
            }
            for (var key in opus.menu_state['groups']) {
                group_name = opus.menu_state['groups'][key];
                $("." + group_name, ".sidebar").trigger(ace.click_event);
            }

            /*
            // open any newly arrived surface geo tables
            geo_cat = $('a[title^="obs_surface_geometry__"]', '#search #leftcolumn').attr("title");
            if (geo_cat && jQuery.inArray(geo_cat, opus.menu_cats_open) < 0) {
                $('a[title="' + geo_cat + '"]', '#search #sidebar').trigger("click");
            }

            $('.menu_spinner').fadeOut("fast");
            */
        });
     },


     // type = cat/group
     getCatGroupFromSlug: function(slug) {
         cat = '';
         group = '';
         $('ul.menu_list>li a', '#search').each(function() {
             if (slug == $(this).data('slug')) {
                   cat = $(this).data('cat');
                   group = $(this).data('group');
                   return false; // this is how you break in an each!
             }
         });
         return {"cat":cat, "group":group}

     },



};