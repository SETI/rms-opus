var o_widgets = {

    /**
     *
     *  Getting and manipulating widgets on the search tab
     *
     **/


    addWidgetBehaviors: function() {

        // widgets are draggable
        /*
        $('#formscolumn1, #formscolumn2', '#search').sortable({
                handle:'.widget_draghandle',
                cursor: 'crosshair',
                stop: function(event,ui) {
                    o_widgets.widgetDrop(ui);
                }
        });
        */

        // open/close mult groupings in widgetts
        $('#search').on('click', '.mult_group_label_container', function () {
            $(this).find('.indicator').toggleClass('fa-plus');
            $(this).find('.indicator').toggleClass('fa-minus');
            $(this).next().slideToggle("fast");
        });

        // mult widget behaviors - user clicks a multi-select checkbox

        /***********************************************************/
        /**** what? WHY IS THIS HERE MOVE TO search.js       *******/
        /**** OR move all those behaviors into here because wtf ****/
        /***********************************************************/

        $('#search').on('change', 'input.multichoice', function() {
           opus.user_clicked=true
           id = $(this).attr("id").split('_')[0];
           value = $(this).attr("value");

           if ($(this).is(':checked')) {

               if (opus.selections[id]) {
                   values = opus.selections[id]; // this param already has been constrained
               }else {
                   values = [];                  // first time constraining this param
               }
               values[values.length] = value;    // add the new value to the array of values
               opus.selections[id] = values;     // add the array of values to selections

               // special menu behavior for surface geo, slide in a loading indicator..
               if (id == 'surfacetarget') {
                    var surface_loading = '<li style = "margin-left:50%; display:none" class = "spinner">&nbsp;</li>';
                    $(surface_loading).appendTo($('a.surfacetarget').parent()).slideDown("slow").delay(500);
               }

           } else {
               remove = opus.selections[id].indexOf(value); // find index of value to remove
               opus.selections[id].splice(remove,1);        // remove value from array
           }
           o_hash.updateHash();
        }); // end live
    },

    // removing, pausing, or minimizing widgets
    widgetControlBehaviors: function(slug) {

        var widget = 'widget__' + slug;

        var min = false;
        if (slug.match(/.*(1|2)/)) {
            var min = slug.match(/(.*)[1|2]/)[1] + '1';
            var max = slug.match(/(.*)[1|2]/)[1] + '2';
        }

        // "remove"
        $('#widget_control_' + slug + ' .remove_widget').click(function() {
           if (min) {
               delete opus.selections[min];
               delete opus.selections[max];
           } else {
               delete opus.selections[slug];
           }
           if (jQuery.inArray(slug,opus.prefs.widgets) > -1) {
               opus.prefs.widgets.splice(opus.prefs.widgets.indexOf(slug)); }

           if (jQuery.inArray(slug,opus.prefs.widgets2) > -1) {
               opus.prefs.widgets2.splice(opus.prefs.widgets2.indexOf(slug)); }

           if (jQuery.inArray(slug,opus.widgets_drawn) > -1) {
               opus.widgets_drawn.splice(opus.widgets_drawn.indexOf(slug)); }

           if (jQuery.inArray(slug, opus.widget_elements_drawn) > -1) {
               opus.widget_elements_drawn.splice(opus.widget_elements_drawn.indexOf(slug)); }

           delete opus.extras['qtype-'+slug];
           delete opus.extras['z-'+slug];
           o_hash.updateHash();
           $('#' + widget).fadeOut("slow");
           setTimeout("$('#" + widget + "').remove()",500); // wait for the fade before removing from dom, for some reason couldn't chain a .remove()
           return false;
        });

        // "pause"
        $('input.pause_widget', '#' + widget).change(function() {
            // $(this).text('resume');
            if (!$(this).is(':checked')) {
                $(' .widget_form  li, .mult_group_label', '#' + widget).fadeTo('slow',0.6);
                $('#' + widget).animate({borderColor:"#D8D8D8"},"slow");
                $('#' + widget + ' .widget_form input').attr("disabled","disabled");
                if (min) {
                    opus.widgets_paused[min] = opus.selections[min];
                    opus.widgets_paused[max] = opus.selections[max];
                    delete opus.selections[min];
                    delete opus.selections[max];
                } else {
                    opus.widgets_paused[slug] = opus.selections[slug];
                    delete opus.selections[slug];
                }
                o_hash.updateHash();
            }  else {
                $(' .widget_form  li, .mult_group_label', '#' + widget).fadeTo('slow',1.0);
                $('#' + widget).animate({borderColor:"#C8C8C8"},"slow");
                $('#' + widget + ' .widget_inner input').removeAttr("disabled");
                if (min) {
                    if (opus.widgets_paused[min]) opus.selections[min] = opus.widgets_paused[min];
                    if (opus.widgets_paused[max]) opus.selections[max] = opus.widgets_paused[max];
                    delete opus.widgets_paused[min];
                    delete opus.widgets_paused[max];
                } else {
                    if (opus.widgets_paused[slug]) opus.selections[slug] = opus.widgets_paused[slug]; // if for when the field was unconstrained but they hit pause
                    delete opus.widgets_paused[slug];
                }
                o_hash.updateHash();

        }});

        // "minimize"
        $('.minimize_widget', '#' + widget ).toggle(function() {
            o_widgets.minimizeWidget(slug, widget);
        }, function() {
            o_widgets.maximizeWidget(slug, widget);
        });

        /**
        $('.widget_label', '#' + widget ).click(function() {
            o_widgets.minimizeWidget(slug, widget);
        });
        $('.widget_minimized', '#' + widget ).click(function() {
            o_widgets.maximizeWidget(slug, widget);
        });
        **/
    },

    widgetDrop: function(ui) {
            // if widget as moved to a different formscolumn,
            // redefine the opus.prefs.widgets and opus.prefs.widgets2 (preserves order)
            widgets = $('#formscolumn1').sortable('toArray');
            widgets2 = $('#formscolumn2').sortable('toArray');

            $.each(widgets, function(index,value) {
                widgets[index]=value.split('__')[1];
            });
            $.each(widgets2, function(index,value) {
                widgets2[index]=value.split('__')[1];
            });
            opus.prefs.widgets = widgets;
            opus.prefs.widgets2 = widgets2;


            o_hash.updateHash();

            // for some reason if the widget is scrolled it loses scroll position after sorting, bring it back:
            if (opus.prefs.widget_scroll[slug]) {
                scrolltop = opus.prefs.widget_scroll[slug];
                $('.widget_scroll_wrapper','#widget__'+slug).scrollTop(scrolltop);
            }
            o_widgets.updateWidgetCookies();
    },

    // this is called after a widge is drawn
    customWidgetBehaviors: function(slug) {

        switch(slug) {

            // planet checkboxes open target groupings:
            case 'planet':
                // user checks a planet box - open the corresponding target group
                // adding a behavior: checking a planet box opens the corresponding targets
                $('#search').on('change', '#widget__planet input:checkbox:checked', function() {
                    // a planet is .chosen_columns, and its corresponding target is not already open
                    mult_id = '#mult_group_' + $(this).attr('value');
                    $(mult_id).find('.indicator').addClass('fa-plus');
                    $(mult_id).find('.indicator').removeClass('fa-minus');
                    $(mult_id).next().slideDown("fast");
                });
                break;

           case 'target':
                // when target widget is drawn, look for any checked planets:
                // usually for when a planet checkbox is checked on page load
                $('#widget__planet input:checkbox:checked', '#search').each(function() {
                    if ($(this).attr('id') && $(this).attr('id').split('_')[0] == 'planet') { // confine to param/vals - not other input controls
                        mult_id = '#mult_group_' + $(this).attr('value');
                        mult_id = '#mult_group_' + $(this).attr('value');
                        $(mult_id).find('.indicator').addClass('fa-plus');
                        $(mult_id).find('.indicator').removeClass('fa-minus');
                        $(mult_id).next().slideDown("fast");
                    }
                });
                break;

           //

        }
    },

    // adjusts the widths of the widgets in the main column so they fit users screen size
    adjustWidgetWidth: function(widget) {
            $(widget).animate({width:$('.formscolumn').width() - 2*20 + 'px'},'fast');  // 20px is the side margin of .widget
            $('.widget_scroll_wrapper',widget).width($('.formscolumn').width() - 2*20 + 'px'); // 20px is the side margin of .widget
    },

    resetWidgetScrolls: function() {
        for (slug in opus.prefs.widget_scroll) {
            $('#widget__' + slug).scrollTop(0);
            delete opus.prefs.widget_scroll[slug];
        }
        o_hash.updateHash();
    },

    pauseWidgetControlVisibility: function(selections) {
        for (key in opus.widgets_drawn) {
            slug = opus.widgets_drawn[key];
            if (typeof(selections[slug]) != 'undefined' && selections[slug].length) {
                $('.pause_widget','#widget__'+slug).show();
            } else {
                // this widget is unconstrained
                if (typeof(opus.widgets_paused[slug]) == 'undefined') {
                    // this widget is not merely paused, hide pause control
                    $('.pause_widget','#widget__'+slug).hide();
                }
            }
        }

    },

    maximizeWidget: function(slug, widget) {
        // un-minimize widget ... maximize widget
        $('.minimize_widget', '#' + widget).toggleClass('opened_triangle');
        $('.minimize_widget', '#' + widget).toggleClass('closed_triangle');
        // $('.pause_widget', '#' + widget).show();
        $('#widget_control_' + slug + ' .remove_widget').show();
        $('#widget_control_' + slug + ' .divider').show();
        $('#' + widget + ' .widget_minimized').hide();
        $('#widget_control_' + slug).removeClass('widget_controls_minimized');
        $('#' + widget + ' .widget_inner').show("blind");


        //////////////////// //////////////////// ////////////////////
        // handle the inner widget scroll thing and hide its handle
            // if (opus.prefs.widget_size[slug]) {

                    // look for custom widget size and scrollstop
                    opus.prefs.widget_scroll[slug] ? scrolltop = opus.prefs.widget_scroll[slug] : scrolltop = 0;
                    opus.prefs.widget_size[slug] ? height = Math.ceil(opus.prefs.widget_size[slug]) : height = opus.widget_full_sizes[slug];

                    // widget_full_sizes

                    $('#widget__' + slug).height(height);

                    $('.widget_scroll_wrapper','#widget__' + slug)
                        .height(height)
                        .animate({scrollTop:scrolltop}, 500);


                    o_widgets.widgetScrollAdjust('#widget__' + slug);

            // }
        //////////////////// //////////////////// ////////////////////
        /*
        $('.widget_scroll_wrapper','#'+widget).css({
            'overflow':'auto'
        });
        **/
        $('.ui-resizable-handle').show();
    },


    minimizeWidget: function(slug, widget) {
        // grab the current height of the widget, we'll need it later to restore it
        opus.widget_full_sizes[slug] = $('#' + widget).height();

        // the minimized text version of the contstrained param = like "planet=Saturn"
        $('.minimize_widget', '#' + widget).toggleClass('opened_triangle');
        $('.minimize_widget', '#' + widget).toggleClass('closed_triangle');

        $('#widget_control_' + slug + ' .remove_widget').hide();
        $('#widget_control_' + slug + ' .divider').hide();

        simple = o_widgets.minimizeWidgetLabel(slug);
        function doit() {
            $('#' + widget + ' .widget_inner').hide();

            $('#' + widget).animate({height:'1.2em'}, 'fast');
            $('#' + widget + ' .widget_minimized').html(simple).fadeIn("fast");
            $('#widget_control_' + slug).addClass('widget_controls_minimized');

            // handle the inner widget scroll thing and hide its handle
            $('.widget_scroll_wrapper','#'+widget).css({
                'overflow':'hidden'
            });
            $('.ui-resizable-handle','#'+widget).hide();

        }
        doit();
    },

    // the string that shows when a widget is minimized
    minimizeWidgetLabel: function(slug) {

         try {
             label = $('#widget__' + slug + ' h2.widget_label').html();
         } catch(e) {
             label = slug;
         }

         var min = false;
         if (slug.match(/.*(1|2)/)) {
             var slug_no_num = slug.match(/(.*)[1|2]/)[1];
             var min = slug_no_num + '1';
             var max = slug_no_num + '2';
         }

         if (opus.selections[slug]) {

             form_type = $('#widget__' + slug + ' .widget_inner').attr("class").split(' ')[1];

             if (form_type == 'RANGE') {

                 // this is a range widget
                 try {
                     var qtypes = opus.extras['qtype-' + slug_no_num];
                 } catch(e) {
                     var qtypes = [opus.qtype_default];
                 }

                 (opus.selections[min].length > opus.selections[max].length) ? lngth = opus.selections[min].length : lngth = opus.selections[max].length;

                 simple = [];
                 for (var i=0;i<lngth;i++) {
                     // ouch:
                     try{
                         qtype = qtypes[i];
                     } catch(e) {
                         try {
                             qtype = qtypes[0];
                         } catch(e) {
                             qtype = opus.qtype_default;
                         }
                     }

                     switch(qtype) {
                          case 'only':
                              simple[simple.length] = ' min >= ' + opus.selections[min][i] + ', ' +
                                                      ' max <= ' + opus.selections[max][i];
                              break;

                          case 'all':
                              simple[simple.length] = ' min <= ' + opus.selections[min][i] + ', ' +
                                                      ' max  >= ' + opus.selections[max][i];
                              break;

                          default:
                              simple[simple.length] = ' min  <= ' + opus.selections[max][i] + ', ' +
                                                      ' max  >= ' + opus.selections[min][i];
                      }

                      break;  // we have decided to only show the first range in the minimized display
                  }
                  simple = label + simple.join(' and ');
                  if (lngth > 1) simple = simple + ' and more..';

             } else if (form_type == 'STRING') {
                 s_arr = [];
                 last_qtype = '';
                 for (key in opus.selections[slug]) {
                     value = opus.selections[slug][key];
                     try {
                         qtype = opus.extras['qtype-'+slug][key];
                     } catch(err) {
                         qtype = 'contains';
                     }
                     if (key==0) {
                         s_arr[s_arr.length] = label + " " + qtype + ": " + value;
                     } else {
                         if (last_qtype && qtype == last_qtype) {
                             s_arr[s_arr.length] = value;
                         } else {
                             s_arr[s_arr.length] = qtype + ": " + value;
                         }
                     }
                     last_qtype = qtype
                 }
                 var simple = s_arr.join(' or ');


             } else {
                 // this is not a range widget
                 var simple = label + ' = ' + opus.selections[slug].join(', ');
             }
         } else {
             var simple = label + ' not constrained';
         }
         return simple
     },

     widgetScrollAdjust: function(widget) {
         $('.widget_scroll_wrapper',widget).css({
             'overflow-y':'auto',
             'height':function(){return $(widget).height();},
             'width':  function(){return $(widget).width();},
         });
     },

     updateWidgetCookies: function() {
         $.cookie("widgets", opus.prefs.widgets.join(','), { expires: 21});
         $.cookie("widgets2", opus.prefs.widgets2.join(','), { expires: 21});
     },

     placeWidgetContainers: function() {
         // this is for when you are first drawing the browse tab and there
         // multiple widgets being requested at once and we want to preserve their order
         // and avoid race conditions that will throw them out of order
         if (opus.prefs.widgets2.length) {
 	        o_search.addSecondFormsCol();
 	     }

         for (var k in opus.prefs.widgets) {
             slug = opus.prefs.widgets[k];
             widget = 'widget__' + slug;
             var html = '<li id = "' + widget + '" class = "widget"></li>';
             $(html).appendTo('#search_widgets1 ');
             // $(html).hide().appendTo('#search_widgets1').show("blind",{direction: "vertical" },200);
             opus.widget_elements_drawn.push(slug);
         }

         for (k in opus.prefs.widgets2) {
             slug = opus.prefs.widgets2[k];
             widget = 'widget__' + opus.prefs.widgets2[k];
             html = '<li id = "' + widget + '" class = "widget"></li>';
             $(html).hide().appendTo('#search_widgets2').show("blind",{direction: "vertical" },200);
             opus.widget_elements_drawn.push(slug);
         }
     },

          // adds a widget and its behaviors, adjusts the opus.prefs variable to include this widget, will not update the hash
     getWidget: function(slug, formscolumn){

         if (!slug) return;

         if (jQuery.inArray(slug, opus.widgets_drawn) > -1) {
             return; // widget already drawn
         }
         if (jQuery.inArray(slug, opus.widgets_fetching) > -1) {
             return; // widget being fetched
         }


         var widget = 'widget__' + slug;

         opus.widgets_fetching.push(slug);

         /**
         // add the new slug to the url hash and the opus.prefs vars
         if (formscolumn == '#formscolumn1') {
             if (jQuery.inArray(slug,opus.prefs.widgets) < 0) {
                 opus.prefs.widgets.push(slug);
             }
         } else {
             if (jQuery.inArray(slug,opus.prefs.widgets2) < 0) {
                 opus.prefs.widgets2.push(slug);
            }
         }
         */

        // add the div that will hold the widget
        if (jQuery.inArray(slug,opus.widget_elements_drawn) < 0) {

            opus.prefs.widgets.push(slug);
            o_widgets.updateWidgetCookies();
            // these sometimes get drawn on page load by placeWidgetContainers, but not this time:
            var html = '<li id = "' + widget + '" class = "widget"></li>';
            $(html).hide().appendTo(formscolumn).show("slow");
            opus.widget_elements_drawn.push(slug);
        }

        $.ajax({ url: "/opus/forms/widget/" + slug + '.html?' + o_hash.getHash(),
             success: function(widget_str){

                 // make this widget resizable
                $('#' + widget).html(widget_str)
                     .resizable({
                         handles: 's',
                      });

                o_widgets.scrollToWidget(widget);

                // $('.minimize_widget', '#' + widget).toggleClass('opened_triangle');
                // $('.minimize_widget', '#' + widget).toggleClass('closed_triangle');

                o_widgets.pauseWidgetControlVisibility(opus.selections);

            }}).done(function() {
                if (formscolumn == '#formscolumn1') {
                    // o_widgets.adjustWidgetWidth('#' + widget);
                }

                // adjust the navbar height
                var sidebar_height = $('.main-container-inner').height() > 800 ? $('.main-container-inner').height() : 800;
                $('#sidebar').height(sidebar_height);

                // bind the resize behavior\
                // if you don't bind it this way the 'trigger' won't work later
                $('#' + widget).bind( "resizestop",function(event) {
                         o_widgets.widgetScrollAdjust('#' + widget);   // make the inner content wrapper match the size of the outer widget div
                         $('.widget_scroll_wrapper','#' + widget)
                             .bind('scrollstop',function(e) {
                                 // when they resize we then bind the scroll stop behavior
                                 if (typeof($(this).scrollTop()) == 'undefined') {
                                     opus.prefs.widget_scroll[slug] = $('#' + widget).height();
                                 }
                                 else opus.prefs.widget_scroll[slug] = $(this).scrollTop();
                                 o_hash.updateHash();
                             });
                             // add new widget size to hash
                             opus.prefs.widget_size[slug] = Math.floor($('#' + widget).height());
                             o_hash.updateHash();
               });


                 /** default_resize bug this doesn't properly resize in Safari, chrome, turning off for now
                 if (slug in opus.prefs.widget_size) {

                         // there is a custom widget size, look for a scrollstop
                         opus.prefs.widget_scroll[slug] ? scrolltop = opus.prefs.widget_scroll[slug] : scrolltop = 0;
                         // resize and scroll the widget


                          $('#widget__' + slug).height(opus.prefs.widget_size[slug]);
                          $('#widget__' + slug).trigger("resizestop");

                         $('.widget_scroll_wrapper','#widget__' + slug)
                             .height(opus.prefs.widget_size[slug])
                             .animate({scrollTop:scrolltop}, 500);
                          o_widgets.widgetScrollAdjust('#widget__' + slug);


                 }
                 **/


             // form_type = $('#widget__' + slug + ' .widget_inner').attr("class").split(' ')[1];

             // if we are drawing a range widget we need to check if the qtype dropdown is
             // already defined by the url:
             if (slug.match(/.*(1|2)/)) {    // this is a range widget
                 var id = slug.match(/(.*)[1|2]/)[1];
                 if (jQuery.inArray('qtype-' + id,opus.extras) > -1 && opus.extras['qtype-'+id]) {
                     // this widgets dropdown is defined in the url, update the html select dropdown to match
                     $('#' + widget + ' select').attr("value",opus.extras['qtype-'+id]);
                 }
             }
             o_widgets.widgetControlBehaviors(slug);

             // add the spans that hold the hinting
             $('#' + widget + ' ul label').after( function () {
                 var value = $(this).find('input').attr("value");
                 try {
                     span_id = 'hint__' + value.split(' ').join('_');
                     return '<span class = "hints" id = "' + span_id + '"></span>';
                 } catch(e) {
                     return '<span class = "hints" id = "' + span_id + '"></span>';
                 }
             });


             if (jQuery.inArray(slug,opus.widgets_fetching) > -1) {
                 opus.widgets_fetching.splice(opus.widgets_fetching.indexOf(slug));
             }

             // add the spans for the the range hinting
             $('#' + widget + ' .widget_inner').after( function () {
                 var span_id = 'hint__' + slug;
                 return '<div class = "hints range_hints" id = "' + span_id + '"></div>';
             });
             if (o_hash.getHash()) o_search.getHinting(slug);

             opus.widgets_drawn.push(slug);

             o_widgets.customWidgetBehaviors(slug);


      }); // end function success, end ajax
     }, // end func


     scrollToWidget: function(widget) {
        // scrolls window to a widget and highlights the widge
        // widget is like: "widget__" + slug
        if ($('#' + widget).offset().top > $(window).height() - 50
            |
            $(window).height() > 2 * $(window).height()
            ) {
            $('html, body').animate({
                    scrollTop: $('#' + widget).offset().top + 50
                }, 2000);
        }
        setTimeout(function(){
            $('.' + widget + ' .widget-main').effect("highlight", "slow");
        }, 1000);

     },


     constructWidgetSizeHash: function(slug) {
         widget_sz = opus.prefs.widget_size[slug];
         if (opus.prefs.widget_scroll[slug]) {
             widget_sz += '+' + opus.prefs.widget_scroll[slug]; }
         return 'sz-' + slug + '=' + widget_sz;
     },




};