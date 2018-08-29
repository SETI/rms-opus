var o_widgets = {

    /**
     *
     *  Getting and manipulating widgets on the search tab
     *
     **/


    addWidgetBehaviors: function() {

        // widgets are draggable
        /*
        $('#search_widgets1, '#search').sortable({
                handle:'.widget_draghandle',
                cursor: 'crosshair',
                stop: function(event,ui) {
                    o_widgets.widgetDrop(ui);
                }
        });
        */

        $(".widget_column").mCustomScrollbar({
            theme:"rounded-dark",
            scrollInertia:300,
        });
        $(".sidebar_wrapper").mCustomScrollbar({
            theme:"rounded-dark",
            scrollInertia:300,
        });

        // first set sidebar height dynamically

        // click the dictionary icon, the definition slides open
        $('#search').on('click', 'a.dict_link', function() {
            var temp = $(this).parent().parent().find('.dictionary');
            $(this).parent().parent().find('.dictionary').slideToggle();
            return false;
        });

        // open/close mult groupings in widgets
        $('#search').on('click', '.mult_group_label_container', function () {
            $(this).find('.indicator').toggleClass('fa-plus');
            $(this).find('.indicator').toggleClass('fa-minus');
            $(this).next().slideToggle("fast");
        });

        // close a widget
        $('#search').on('click', '.close_widget', function(myevent) {
            var slug = $(this).data('slug');
            o_widgets.closeWidget(slug);
            try {
              var id = "#widget__"+slug;
              $(id).remove();
            } catch (e) {
              console.log("error on close widget, id="+id);
            }
        });


        // mult widget behaviors - user clicks a multi-select checkbox

        /***********************************************************/
        /**** what? WHY IS THIS HERE MOVE TO search.js       *******/
        /**** OR move all those behaviors into here because wtf ****/
        /***********************************************************/

        $('#search').on('change', 'input.multichoice', function() {
           // mult widget gets changed
           var id = $(this).attr("id").split('_')[0];
           var value = $(this).attr("value").replace(/\+/g, '%2B');

           if ($(this).is(':checked')) {
               var values = [];
               if (opus.selections[id]) {
                   var values = opus.selections[id]; // this param already has been constrained
               }

               values[values.length] = value;    // add the new value to the array of values
               opus.selections[id] = values;     // add the array of values to selections

               // special menu behavior for surface geo, slide in a loading indicator..
               if (id == 'surfacetarget') {
                    var surface_loading = '<li style = "margin-left:50%; display:none" class = "spinner">&nbsp;</li>';
                    $(surface_loading).appendTo($('a.surfacetarget').parent()).slideDown("slow").delay(500);
               }

           } else {
               var remove = opus.selections[id].indexOf(value); // find index of value to remove
               opus.selections[id].splice(remove,1);        // remove value from array
           }
           o_hash.updateHash();
        }); // end live
    },


    closeWidget: function(slug) {

        var slug_no_num;
        try {
            slug_no_num = slug.match(/(.*)[1|2]/)[1];

        } catch (e) {
            slug_no_num = slug;
        }

        if ($.inArray(slug,opus.prefs.widgets) > -1) {
            opus.prefs.widgets.splice(opus.prefs.widgets.indexOf(slug), 1);
        }

        if ($.inArray(slug,opus.widgets_drawn) > -1) {
            opus.widgets_drawn.splice(opus.widgets_drawn.indexOf(slug), 1);
        }

        if ($.inArray(slug, opus.widget_elements_drawn) > -1) {
            opus.widget_elements_drawn.splice(opus.widget_elements_drawn.indexOf(slug), 1);
        }

        if (slug in opus.selections) {
            delete opus.selections[slug];
        }
        // handle for range queries
        if (slug_no_num + '1' in opus.selections) {
            delete opus.selections[slug_no_num + '1'];
        }
        if (slug_no_num + '2' in opus.selections) {
            delete opus.selections[slug_no_num + '2'];
        }

        delete opus.extras['qtype-'+slug_no_num];
        delete opus.extras['z-'+slug_no_num];

        o_hash.updateHash();
        o_widgets.updateWidgetCookies();

    },

    widgetDrop: function(ui) {
            // if widget as moved to a different formscolumn,
            // redefine the opus.prefs.widgets (preserves order)
            var widgets = $('#search_widgets1').sortable('toArray');

            $.each(widgets, function(index,value) {
                widgets[index]=value.split('__')[1];
            });
            opus.prefs.widgets = widgets;

            o_hash.updateHash();

            // for some reason if the widget is scrolled it loses scroll position after sorting, bring it back:
            if (opus.prefs.widget_scroll[slug]) {
                var scrolltop = opus.prefs.widget_scroll[slug];
                $('.widget_scroll_wrapper','#widget__'+slug).scrollTop(scrolltop);
            }
            o_widgets.updateWidgetCookies();
    },

    // this is called after a widget is drawn
    customWidgetBehaviors: function(slug) {
        switch(slug) {

            // planet checkboxes open target groupings:
            case 'planet':
                // user checks a planet box - open the corresponding target group
                // adding a behavior: checking a planet box opens the corresponding targets
                $('#search').on('change', '#widget__planet input:checkbox:checked', function() {
                    // a planet is .chosen_columns, and its corresponding target is not already open
                    var mult_id = '.mult_group_' + $(this).attr('value');
                    $(mult_id).find('.indicator').addClass('fa-minus');
                    $(mult_id).find('.indicator').removeClass('fa-plus');
                    $(mult_id).next().slideDown("fast");
                });
                break;

           case 'target':
                // when target widget is drawn, look for any checked planets:
                // usually for when a planet checkbox is checked on page load
                $('#widget__planet input:checkbox:checked', '#search').each(function() {
                    if ($(this).attr('id') && $(this).attr('id').split('_')[0] == 'planet') { // confine to param/vals - not other input controls
                        var mult_id = '.mult_group_' + $(this).attr('value');
                        $(mult_id).find('.indicator').addClass('fa-minus');
                        $(mult_id).find('.indicator').removeClass('fa-plus');
                        $(mult_id).next().slideDown("fast");
                    }
                });
                break;

          case 'surfacegeometrytargetname':
               // when target widget is drawn, look for any checked planets:
               // usually for when a planet checkbox is checked on page load
               $('#widget__planet input:checkbox:checked', '#search').each(function() {
                   if ($(this).attr('id') && $(this).attr('id').split('_')[0] == 'planet') { // confine to param/vals - not other input controls
                       var mult_id = '.mult_group_' + $(this).attr('value');
                       $(mult_id).find('.indicator').addClass('fa-minus');
                       $(mult_id).find('.indicator').removeClass('fa-plus');
                       $(mult_id).next().slideDown("fast");
                   }
               });
               break;
           //

        }
    },

    // adjusts the widths of the widgets in the main column so they fit users screen size
    adjustWidgetWidth: function(widget) {
            $(widget).animate({width:$('#search_widgets1').width() - 2*20 + 'px'},'fast');  // 20px is the side margin of .widget
            // $('.widget_scroll_wrapper',widget).width($('.formscolumn').width() - 2*20 + 'px'); // 20px is the side margin of .widget
    },

    resetWidgetScrolls: function() {
        for (var slug in opus.prefs.widget_scroll) {
            $('#widget__' + slug).scrollTop(0);
            delete opus.prefs.widget_scroll[slug];
        }
        o_hash.updateHash();
    },

    pauseWidgetControlVisibility: function(selections) {
        for (var key in opus.widgets_drawn) {
            var slug = opus.widgets_drawn[key];
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

     updateWidgetCookies: function() {
         $.cookie("widgets", opus.prefs.widgets.join(','), { expires: 28});  // days
     },

     placeWidgetContainers: function() {
         // this is for when you are first drawing the browse tab and there
         // multiple widgets being requested at once and we want to preserve their order
         // and avoid race conditions that will throw them out of order
         $.each( opus.prefs.widgets, function( index, slug ){
             var widget = 'widget__' + slug;
             var html = '<li id = "' + widget + '" class = "widget"></li>';
             $(html).appendTo('#search_widgets1 ');
             // $(html).hide().appendTo('#search_widgets1').show("blind",{direction: "vertical" },200);
             opus.widget_elements_drawn.push(slug);
         });
     },

     // adds a widget and its behaviors, adjusts the opus.prefs variable to include this widget, will not update the hash
     getWidget: function(slug, formscolumn){

         if (!slug) return;

         if ($.inArray(slug, opus.widgets_drawn) > -1) {
             return; // widget already drawn
         }
         if ($.inArray(slug, opus.widgets_fetching) > -1) {
             return; // widget being fetched
         }

         var widget = 'widget__' + slug;

         opus.widgets_fetching.push(slug);

        // add the div that will hold the widget
        if ($.inArray(slug,opus.widget_elements_drawn) < 0) {

            opus.prefs.widgets.unshift(slug);

            o_widgets.updateWidgetCookies();
            // these sometimes get drawn on page load by placeWidgetContainers, but not this time:
            var html = '<li id = "' + widget + '" class = "widget"></li>';
            $(html).hide().prependTo(formscolumn).show("slow");
            opus.widget_elements_drawn.unshift(slug);

        }
        $.ajax({ url: "/opus/__forms/widget/" + slug + '.html?' + o_hash.getHash(),
             success: function(widget_str){

                 // make this widget resizable
                $('#' + widget).html(widget_str)
                     .resizable({
                         handles: 's',
                      });

                o_widgets.pauseWidgetControlVisibility(opus.selections);

            }}).done(function() {

                o_search.adjustSearchHeight();

                // bind the resize behavior\
                // if you don't bind it this way the 'trigger' won't work later
                $('#' + widget).bind( "resizestop",function(event) {
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

             // if we are drawing a range widget we need to check if the qtype dropdown is
             // already defined by the url:
             if (slug.match(/.*(1|2)/)) {
               // this is a range widget
                 var id = slug.match(/(.*)[1|2]/)[1];
                 o_search.updateQtypes('#' + widget + ' select');

                // is the qtype constrained in the url?
                 if ($.inArray('qtype-' + id,opus.extras) > -1 && opus.extras['qtype-'+id]) {
                     // this widgets dropdown is defined in the url, update the html select dropdown to match
                     $('#' + widget + ' select').attr("value",opus.extras['qtype-'+id]);
                 }

                 // add the helper icon to range widgets.
                // add the helper text for range widgets
                if ($('.' + widget).hasClass('range-widget') && $('.' + widget).find('select').length) {
                    // this is a range widget and also the any/all/only dropdown is included
                    // (the server knows not to include it when this is a longitude type query)
                    var help_icon = '<a href = "#" data-toggle="popover" data-placement="left">\
                                    <i class="fa fa-info-circle"></i></a>';

                    $('.' + widget + ' .widget-main>ul>ul').append('<li class = "range-qtype-helper">' + help_icon + '</li>');

                    $('.' + widget + ' .widget-main .range-qtype-helper a').popover({
                      html:true,
                      trigger:"focus",
                      content: function() {
                        return $('#range_query_widget_helper_html').html();
                      }
                    });
                }

             }

             // add the spans that hold the hinting
             try {
                 $('#' + widget + ' ul label').after( function () {
                    var value = $(this).find('input').attr("value");
                    var span_id = 'hint__' + slug + '_' + value.replace(/ /g,'-').replace(/[^\w\s]/gi, '')  // special chars not allowed in id element
                    return '<span class = "hints" id = "' + span_id + '"></span>';
                 });
             } catch(e) { } // these only apply to mult widgets


             if ($.inArray(slug,opus.widgets_fetching) > -1) {
                 opus.widgets_fetching.splice(opus.widgets_fetching.indexOf(slug), 1);
             }

            if ($.isEmptyObject(opus.selections)) {
                $('#widget__' + slug + ' .spinner').fadeOut('');
            } else {
                o_search.getHinting(slug);
            }

             opus.widgets_drawn.unshift(slug);

             o_widgets.customWidgetBehaviors(slug);
             o_widgets.scrollToWidget(widget);

             o_hash.updateHash();
             o_search.getHinting(slug);

      }); // end function success, end ajax
     }, // end func


     scrollToWidget: function(widget) {
        // scrolls window to a widget and highlights the widge
        // widget is like: "widget__" + slug
        /*
        if ($('#' + widget).offset().top > $(window).height() - 50
            |
            $(window).height() > 2 * $(window).height()
            ) {
            $('html, body').animate({
                    scrollTop: $('#' + widget).offset().top + 50
                }, 2000);
        }
        */
        //  scroll the widget panel to top

            $(".widget_column").mCustomScrollbar("scrollTo","top",
                {
                    timeout:1000,
                });

            setTimeout(function() {
                $('.' + widget + ' .widget-main').effect("highlight", "slow");
            }, 1800)

     },


     constructWidgetSizeHash: function(slug) {
         widget_sz = opus.prefs.widget_size[slug];
         if (opus.prefs.widget_scroll[slug]) {
             widget_sz += '+' + opus.prefs.widget_scroll[slug]; }
         return 'sz-' + slug + '=' + widget_sz;
     },




};
