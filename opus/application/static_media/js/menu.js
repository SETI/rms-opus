var o_menu = {

    /**
     *
     *  the menu on the *search page*
     *
     **/

     menuBehaviors: function() {
         // search menu behaviors

         // click cat header in menu toggles arrow style
        // $('#sidebar').on("click", 'a', function() {
        //    $(this).find('b.arrow').toggleClass('fa-angle-right').toggleClass('fa-angle-down');

         //});
         $('#sidebarCollapse').on('click', function () {
             $('#sidebar, #content').toggleClass('active');
             $('.collapse.in').toggleClass('in');
             $('a[aria-expanded=true]').attr('aria-expanded', 'false');
         });

         // click param in menu get new widget
         $('#sidebar').on("click", '.submenu li a', function() {
             var slug = $(this).data('slug');
             if (!slug) { return; }
             if ($.inArray(slug, opus.widgets_drawn)>-1){
                 // widget is already showing do not fetch another
                 try {
                    // scroll to widget and highlight it
                    o_widgets.scrollToWidget('widget__'+slug);

                } catch(e) {
                    return false;
                }
                return false;

             } else {
                  $(this).css("background", "gainsboro");
                  o_widgets.getWidget(slug,'#search_widgets');
             }
             o_hash.updateHash();
             return false;
         });


        // menu state - keep track of what menu items are open
        $(".sidebar > .nav-list").click( function(e){
            var link_element = $(e.target).closest('a');
            if(!link_element || link_element.length == 0) return;//if not clicked inside a link element

            var sub = link_element.next().get(0);

            // for opus: keeping track of menu state, since menu is constantly refreshed
            // menu cats
            if ($(link_element).data( "cat" )) {
                var cat_name = $(link_element).data( "cat" );
                if ($(sub).parent().hasClass('open')) {
                    if ($.inArray(cat_name, opus.menu_state['cats']) < 0) {
                        opus.menu_state['cats'].push(cat_name);
                    }
                } else {
                    opus.menu_state['cats'].splice(opus.menu_state['cats'].indexOf(cat_name), 1);
                }
            }
            // menu groups
            if ($(link_element).data( "group" )) {
                var group_name = $(link_element).data( "group" );
                if ($(sub).parent().hasClass('open')) {
                    if ($.inArray(group_name, opus.menu_state['groups']) < 0) {
                        opus.menu_state['groups'].push(group_name);
                    }
                } else {
                    opus.menu_state['groups'].splice(opus.menu_state['groups'].indexOf(group_name), 1);
                }
            }
            return false;
        });
     },

     getMenu: function() {
        $('.menu_spinner').fadeIn("fast");
        var hash = o_hash.getHash();

        $( "#sidebar").load( "/opus/__menu.html?" + hash, function() {
            if (opus.menu_state['cats'] == 'all') {

                // first load, open general constraints
                opus.menu_state['cats'] = [];
                var cat_name = 'obs_general';
                opus.menu_state['cats'].push(cat_name);
                var link = $("[data-cat='"+cat_name+"']");
                link.parent().find('b.arrow').toggleClass('fa-angle-right').toggleClass('fa-angle-down');

            } else {

                // open menu items that were open before
                for (var key in opus.menu_state['cats']) {
                    var cat_name = opus.menu_state['cats'][key];
                    var link = $("[data-cat='"+cat_name+"']");
                    link.find('b.arrow').toggleClass('fa-angle-right').toggleClass('fa-angle-down');

                    // $("." + cat_name, ".sidebar").trigger(ace.click_event);
                }
                for (var key in opus.menu_state['groups']) {
                    var group_name = opus.menu_state['groups'][key];
                    var link = $("[data-cat='"+cat_name+"']");
                    link.find('b.arrow').toggleClass('fa-angle-right').toggleClass('fa-angle-down');
                    // $("." + group_name, ".sidebar").trigger(ace.click_event);
                }
            }
            // open any newly arrived surface geo tables
            // todo: this could be problematic if user wants to close it and keep it closed..
            var geo_cat = $('a[data-cat^="obs_surface_geometry__"]', '.sidebar').data('cat');
            if (geo_cat && $.inArray(geo_cat, opus.menu_state['cats']) < 0) {
                // open it
                var link = $("a." + geo_cat, ".sidebar");
                var sub = link.next().get(0);
                $(sub).slideToggle(400).parent().toggleClass('open');
                // and add it to open cats list
                opus.menu_state['cats'].push(geo_cat);
            }
            // highlight open widgets
            $.each(opus.widgets_drawn, function(index, widget) {
                $("li > [data-slug='"+widget+"']").css("background", "gainsboro");
            });

            o_search.adjustSearchHeight();
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
