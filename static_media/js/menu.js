var o_menu = {

    /**
     *
     *  the menu on the *search page*
     *
     **/

     menuBehaviors: function() {
         // search menu behaviors
         // why was this here?

         // click param in menu get new widget
         $('.menu_list li a','#search').live("click", function() {
             slug = $(this).data('slug');
             if (jQuery.inArray(slug, opus.widgets_drawn)>-1){
                 // widget is already showing do not fetch another
                 $('#widget__'+slug).effect("highlight", {}, 2000);
             } else {
                 o_widgets.getWidget(slug,'#formscolumn1');
             }
             o_hash.updateHash();
             return false; });


         $(".cat_label").live("click", function(){
                $(this).find('.menu_cat_triangle').toggleClass('closed_triangle');
                $(this).find('.menu_cat_triangle').toggleClass('opened_triangle');
        		if ($(this).find('.menu_cat_triangle').hasClass('opened_triangle')) {
        		    // this is opening, update the menu indicators immediately
        		    o_menu.updateMenuIndicators();
        		    $(this).next().slideToggle("fast");
        		} else {
        		    // this is closing, slide it shut THEN update teh indicators... UX, baby.
        		    $(this).next().slideToggle('fast', function() {
            		    o_menu.updateMenuIndicators();
            		});
        		}
                return false;
          });


         $(".group_label").live("click", function(){
        $(this).find('.menu_group_triangle').toggleClass('closed_triangle');
        $(this).find('.menu_group_triangle').toggleClass('opened_triangle');
        if ($(this).find('.menu_group_triangle').hasClass('opened_triangle')) {
            // this is opening, update the menu indicators immediately
            o_menu.updateMenuIndicators();
            $(this).next().slideToggle("fast");
        } else {
            // this is closing, slide it shut THEN update teh indicators... UX, baby.
            $(this).next().slideToggle('fast', function() {
        	    o_menu.updateMenuIndicators();
        	});
        }
            return false;
        });

     },

     getMenu: function() {
        hash = o_hash.getHash();
        $( "#leftcolumn" ).load( "/opus/menu.html?" + hash, function() {
        });
     },

     updateMenuIndicators: function() {
         if (opus.prefs.view != 'search') return;
         // manage invalid indicators - slug is no longer constrained
         var removed = false;
         for (var i=0;i<opus.menu_list_indicators['slug'].length;i++) {
             slug = opus.menu_list_indicators['slug'][i];
             if (typeof(opus.selections[slug]) == 'undefined' || !opus.selections[slug].length) {
                 // item is not selected
                 cat = opus.menu_list_indicators['cat'][i];
                 group = opus.menu_list_indicators['group'][i];

                 // splice out this slug
                 opus.menu_list_indicators['slug'].splice(i,1);
                 opus.menu_list_indicators['cat'].splice(i,1);
                 opus.menu_list_indicators['group'].splice(i,1);

                 // remove any indicators
                 // $('#menu_select__' + slug).parent().removeClass('menu_list_indicator_on');
                 o_menu.menuIndicatorControl(slug,'remove');
                 $('li.' + group).removeClass('menu_list_indicator_on');
                 $('li.' + cat).removeClass('menu_list_indicator_on');
             }
         }

         if (!opus.selections) return;
         // now for valid indicators
         for (slug in opus.selections) {

             if (opus.selections[slug].length){

                 // this field is constrained
                 // get the cat and group from the slug label's data field
                 slugdata = o_menu.getCatGroupFromSlug(slug);
                 cat = slugdata['cat'];
                 group = slugdata['group'];

                 if (!cat || !group) continue;

                 // add slug,cat,label to menu_list_indicators if not already there
                 if (jQuery.inArray(slug,opus.menu_list_indicators['slug']) < 0) {
                     opus.menu_list_indicators['slug'].push(slug);
                 }

                 if (jQuery.inArray(cat,opus.menu_list_indicators['cat']) < 0) {
                     opus.menu_list_indicators['cat'].push(cat);
                 }
                 if (jQuery.inArray(group,opus.menu_list_indicators['group']) < 0) {
                     opus.menu_list_indicators['group'].push(group);
                 }


                 // check if the parent group of this slug is closed,
                 // if the parent group is closed add indicator to group label
                 if ($('li.' + group + ' .menu_group_triangle', '#search').hasClass('closed_triangle')) {
                     $('li.' + group).addClass('menu_list_indicator_on');
                 } else {
                     $('li.' + group).removeClass('menu_list_indicator_on');
                 }
                 // check if the parent category for this slug is closed,
                 // if the parent category is closed add indicator to cat label
                 if ($('li.' + cat + ' .menu_cat_triangle', '#search').hasClass('closed_triangle')) {
                     $('li.' + cat).addClass('menu_list_indicator_on');
                 } else {
                     $('li.' + cat).removeClass('menu_list_indicator_on');
                 }
                 // add indicator to selection
                 // $('#menu_select__' + slug).parent().addClass('menu_list_indicator_on');
                 o_menu.menuIndicatorControl(slug,'add');


             } // if opus.selections[slug].length
         }  // end for

     },

    // this add/removes the menu indicator on a param name (not a group or category) action = add/remove
     menuIndicatorControl: function(slug, action) {
         action == 'add' ? $('#search__'+slug).parent().parent().addClass('menu_list_indicator_on') : $('#search__'+slug).parent().parent().removeClass('menu_list_indicator_on');
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