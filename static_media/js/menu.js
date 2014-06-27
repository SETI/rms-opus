var o_menu = {

    /**
     *
     *  the menu on the *search page*
     *
     **/

     menuBehaviors: function() {
         // search menu behaviors

         // click param in menu get new widget
         $('.sidebar').on("click", '.submenu li a', function() {
             slug = $(this).data('slug');
             if (!slug) { return; }
             if (jQuery.inArray(slug, opus.widgets_drawn)>-1){
                 // widget is already showing do not fetch another
                 try {
                    $('#widget__'+slug + ' .widget-main').effect("highlight", "slow");
                    if ($('#widget__' + slug).offset().top > $(window).height() - 50
                        ) {
                        $('html, body').animate({
                                scrollTop: $('#widget__' + slug).offset().top + 50
                            }
                            , 2000);
                    }
                    setTimeout(function(){
                        $('.widget__' + slug + ' .widget-main').effect("highlight", "slow");
                    }, 1000);


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


        // menu state - keep track of what menu items are open
        $('.sidebar').on(ace.click_event, '.nav-list', function(e){
            var link_element = $(e.target).closest('a');
            if(!link_element || link_element.length == 0) return;//if not clicked inside a link element

            var sub = link_element.next().get(0);

            // for opus: keeping track of menu state, since menu is constantly refreshed
            // menu cats
            if ($(link_element).data( "cat" )) {
                cat_name = $(link_element).data( "cat" );
                if ($(sub).parent().hasClass('open')) {
                    if (jQuery.inArray(cat_name, opus.menu_state['cats']) < 0) {
                        opus.menu_state['cats'].push(cat_name);
                    }
                } else {
                    opus.menu_state['cats'].splice(opus.menu_state['cats'].indexOf(cat_name));
                }
            }
            // menu groups
            if ($(link_element).data( "group" )) {
                group_name = $(link_element).data( "group" );
                if ($(sub).parent().hasClass('open')) {
                    if (jQuery.inArray(group_name, opus.menu_state['groups']) < 0) {
                        opus.menu_state['groups'].push(group_name);
                    }
                } else {
                    opus.menu_state['groups'].splice(opus.menu_state['groups'].indexOf(group_name));
                }
            }


            // check if this menu group only has one option, if so just open that widget
            // I'm commenting this out because I do not agree that it is desirable
            // with the new menu
            /*
            if ($(this).next().children().size() == 1) {
                $(this).next().find('li a').trigger("click");
            }
            */

            return false;
        });




     },

     getMenu: function() {
        $('.menu_spinner').fadeIn("fast");
        hash = o_hash.getHash();
        $( "#sidebar").load( "/opus/menu.html?" + hash, function() {

            // open menu items that were open before
            for (var key in opus.menu_state['cats']) {
                cat_name = opus.menu_state['cats'][key];
                link = $("a." + cat_name, ".sidebar");
                sub = link.next().get(0);
                $(sub).toggle().parent().toggleClass('open');

                // $("." + cat_name, ".sidebar").trigger(ace.click_event);
            }
            for (var key in opus.menu_state['groups']) {
                group_name = opus.menu_state['groups'][key];
                link = $("a." + group_name, ".sidebar");
                sub = link.next().get(0);
                $(sub).toggle().parent().toggleClass('open');
                // $("." + group_name, ".sidebar").trigger(ace.click_event);
            }

            // open any newly arrived surface geo tables
            // todo: this could be problematic if user wants to close it and keep it closed..
            geo_cat = $('a[title^="obs_surface_geometry__"]', '.sidebar').attr("title");
            if (geo_cat && jQuery.inArray(geo_cat, opus.menu_state['cats']) < 0) {
                // open it
                link = $("a." + geo_cat, ".sidebar");
                sub = link.next().get(0);
                $(sub).slideToggle(400).parent().toggleClass('open');
                // and add it to open cats list
                opus.menu_state['cats'].push(geo_cat);
            }

            $('.menu_spinner').fadeOut("fast");

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