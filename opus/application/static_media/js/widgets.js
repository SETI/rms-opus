var o_widgets = {

    /**
     *
     *  Getting and manipulating widgets on the search tab
     *
     **/


    addWidgetBehaviors: function() {
		    $("#search_widgets").sortable({
            items: "li:not(.unsortable)",
            cursor: 'move',
            stop: function(event, ui) { o_widgets.widgetDrop(this); }
        });

        $("#search_widgets").on( "sortchange", function( event, ui ) {
            o_widgets.widgetDrop();
        });

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
            let adjustSearchWidgetHeight = _.debounce(o_search.adjustSearchWidgetHeight, 200);
            adjustSearchWidgetHeight();
        });

        // close a card
        $('#search').on('click', '.close_card', function(myevent) {
            var slug = $(this).data('slug');
            o_widgets.closeWidget(slug);
            try {
              var id = "#widget__"+slug;
              $(id).remove();
            } catch (e) {
              console.log("error on close widget, id="+id);
            }
        });

        // close opened surfacegeo widget if user select another surfacegeo target
        $('#search').on('change', 'input.singlechoice', function() {
            $('a[data-slug^="SURFACEGEO"]').each( function (index) {
                let slug = $(this).data('slug');
                o_widgets.closeWidget(slug);
                try {
                  var id = "#widget__"+slug;
                  $(id).remove();
                } catch (e) {
                  console.log("error on close widget, id="+id);
                }
            });
        });
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

        delete opus.extras[`qtype-${slug_no_num}`];
        delete opus.extras[`z-${slug_no_num}`];

        var selector = `li [data-slug='${slug}']`;
        o_menu.markMenuItem(selector, "unselect");

        o_search.allNormalizedApiCall().then(function(normalizedData) {
            if (normalizedData.reqno < opus.lastAllNormalizeRequestNo) {
                return;
            }
            o_search.validateRangeInput(normalizedData);

            if(opus.allInputsValid) {
                $("input.RANGE").removeClass("search_input_valid");
                $("input.RANGE").removeClass("search_input_invalid");
                $("input.RANGE").addClass("search_input_original");
                $("#sidebar").removeClass("search_overlay");
                $("#result_count").text(o_utils.addCommas(opus.result_count));
            }
            let adjustSearchWidgetHeight = _.debounce(o_search.adjustSearchWidgetHeight, 200);
            adjustSearchWidgetHeight();
            o_hash.updateHash(opus.allInputsValid);
            o_widgets.updateWidgetCookies();
        });
    },

    widgetDrop: function(obj) {
            // if widget as moved to a different formscolumn,
            // redefine the opus.prefs.widgets (preserves order)
            let widgets = $('#search_widgets').sortable('toArray');

            $.each(widgets, function(index,value) {
                widgets[index]=value.split('__')[1];
            });
            opus.prefs.widgets = widgets;

            o_hash.updateHash();

            // for some reason if the widget is scrolled it loses scroll position after sorting, bring it back:
            if (opus.prefs.widget_scroll[slug]) {
                let scrolltop = opus.prefs.widget_scroll[slug];
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
            $(widget).animate({width:$('#search_widgets').width() - 2*20 + 'px'},'fast');  // 20px is the side margin of .widget
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

        var simple = o_widgets.minimizeWidgetLabel(slug);
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
        var label;
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

             var form_type = $('#widget__' + slug + ' .widget_inner').attr("class").split(' ')[1];

             if (form_type == 'RANGE') {

                 // this is a range widget
                 var qtypes;
                 try {
                     qtypes = opus.extras['qtype-' + slug_no_num];
                 } catch(e) {
                     qtypes = [opus.qtype_default];
                 }

                 var length = (opus.selections[min].length > opus.selections[max].length) ? opus.selections[min].length : opus.selections[max].length;

                 var simple = [];
                 for (var i=0;i<length;i++) {
                     // ouch:
                     var qtype;
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
                  if (length > 1) simple = simple + ' and more..';

             } else if (form_type == 'STRING') {
                 var s_arr = [];
                 var last_qtype = '';
                 for (var key in opus.selections[slug]) {
                     var value = opus.selections[slug][key];
                     var qtype;
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

     updateWidgetCookies: function() {
         $.cookie("widgets", opus.prefs.widgets.join(','), { expires: 28});  // days
      },

     placeWidgetContainers: function() {
         // this is for when you are first drawing the browse tab and there
         // multiple widgets being requested at once and we want to preserve their order
         // and avoid race conditions that will throw them out of order
         for (var k in opus.prefs.widgets) {
             var slug = opus.prefs.widgets[k];
             var widget = 'widget__' + slug;
             var html = '<li id = "' + widget + '" class = "widget"></li>';
             $(html).appendTo('#search_widgets ');
             // $(html).hide().appendTo('#search_widgets').show("blind",{direction: "vertical" },200);
             opus.widget_elements_drawn.push(slug);
         }
     },

     // adds a widget and its behaviors, adjusts the opus.prefs variable to include this widget, will not update the hash
     getWidget: function(slug, formscolumn, deferredObj=null){

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

                $("#widget__"+slug).html(widget_str);
                o_widgets.pauseWidgetControlVisibility(opus.selections);
            }}).done(function() {

            // o_search.adjustSearchHeight();

             // if we are drawing a range widget we need to check if the qtype dropdown is
             // already defined by the url:
             if (slug.match(/.*(1|2)/)) {
               // this is a range widget
                 var id = slug.match(/(.*)[1|2]/)[1];

                // is the qtype constrained in the url?
                 if ($.inArray('qtype-' + id,opus.extras) > -1 && opus.extras['qtype-'+id]) {
                     // this widgets dropdown is defined in the url, update the html select dropdown to match
                     $('#' + widget + ' select').attr("value",opus.extras['qtype-'+id]);
                 }

                 // add the helper icon to range widgets.
                // add the helper text for range widgets
                if ($('.' + widget).hasClass('range-widget') && $('.' + widget).find('select').length) {
                    // this is a range widget and also the any/all/only dropdown is included
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


             // If we have a string input widget open, initialize autocomplete for string input
             let displayDropDownList = true;
             let stringInputDropDown = $(`input[name="${slug}"].STRING`).autocomplete({
                 minLength: 1,
                 source: function(request, response) {
                     let currentValue = request.term;
                     let values = [];

                     opus.lastRequestNo++;
                     o_search.slugStringSearchChoicesReqno[slug] = opus.lastRequestNo;

                     values.push(currentValue)
                     opus.selections[slug] = values;
                     let newHash = o_hash.updateHash(false);
                     /*
                     We are relying on URL order now to parse and get slugs before "&view" in the URL
                     Opus will rewrite the URL when a URL is pasted, all the search related slugs would be moved ahead of "&view"
                     Refer to hash.js getSelectionsFromHash and updateHash functions
                     */
                     let regexForHashWithSearchParams = /(.*)&view/;
                     if(newHash.match(regexForHashWithSearchParams)) {
                         newHash = newHash.match(regexForHashWithSearchParams)[1];
                     }
                     // Avoid calling api when some inputs are not valid
                     if(!opus.allInputsValid) {
                        return;
                     }
                     let url = `/opus/__api/stringsearchchoices/${slug}.json?` + newHash + "&reqno=" + opus.lastRequestNo;
                     $.getJSON(url, function(stringSearchChoicesData) {
                         if(stringSearchChoicesData.reqno < o_search.slugStringSearchChoicesReqno[slug]) {
                             return;
                         }

                         if(stringSearchChoicesData.full_search) {
                             o_search.searchMsg = "Results from entire database, not current search constraints"
                         } else {
                             o_search.searchMsg = "Results from current search constraints"
                         }

                         if(stringSearchChoicesData.choices.length !== 0) {
                             stringSearchChoicesData.choices.unshift(o_search.searchMsg);
                             o_search.searchResultsNotEmpty = true;
                         } else {
                             o_search.searchResultsNotEmpty = false;
                         }
                         if(stringSearchChoicesData.truncated_results) {
                             stringSearchChoicesData.choices.push(o_search.truncatedResultsMsg);
                         }

                         let hintsOfString = stringSearchChoicesData.choices;
                         o_search.truncatedResults = stringSearchChoicesData.truncated_results;
                         response(displayDropDownList ? hintsOfString : null);
                     });
                 },
                 focus: function(focusEvent, ui) {
                     return false;
                 },
                 select: function(selectEvent, ui) {
                     let displayValue = o_search.extractHtmlContent(ui.item.label);
                     $(`input[name="${slug}"]`).val(displayValue);
                     $(`input[name="${slug}"]`).trigger("change");
                     // If an item in the list is selected, we update the hash with selected value
                     // opus.selections[slug] = [displayValue];
                     // o_hash.updateHash();
                     return false;
                 },
             })
             .keyup(function(keyupEvent) {
                 /*
                 When "enter" key is pressed:
                 (1) autocomplete dropdown list is closed
                 (2) change event is triggered if input is an empty string
                 */
                 if(keyupEvent.which === 13) {
                     displayDropDownList = false;
                     $(`input[name="${slug}"]`).autocomplete("close");
                     let currentStringInputValue = $(`input[name="${slug}"]`).val().trim();
                     if(currentStringInputValue === "") {
                         $(`input[name="${slug}"]`).trigger("change");
                     }
                 } else {
                     displayDropDownList = true;
                 }
             })
             .focusout(function(focusoutEvent) {
                 let currentStringInputValue = $(`input[name="${slug}"]`).val().trim();
                 if(currentStringInputValue === "") {
                     $(`input[name="${slug}"]`).trigger("change");
                 }
             })
             .data( "ui-autocomplete" );

             // element with ui-autocomplete-category class will not be selectable
             let menuWidget = $(`input[name="${slug}"].STRING`).autocomplete("widget");
             menuWidget.menu( "option", "items", "> :not(.ui-autocomplete-not-selectable)" );

             if(stringInputDropDown) {
                 // Add header and footer for dropdown list
                 stringInputDropDown._renderMenu = function(ul, items) {
                   let self = this;
                   $.each(items, function(index, item) {
                       self._renderItem(ul, item );
                   });

                   if(o_search.searchResultsNotEmpty) {
                       ul.find("li:first").addClass("ui-state-disabled ui-autocomplete-not-selectable");
                   }
                   if(o_search.truncatedResults) {
                       ul.find("li:last").addClass("ui-state-disabled ui-autocomplete-not-selectable");
                   }
                 };
                 // Customized dropdown list item
                 stringInputDropDown._renderItem = function(ul, item) {
                     return $( "<li>" )
                     .data( "ui-autocomplete-item", item )
                     .attr( "data-value", item.value )
                     // Need to wrap with <a> tag because of jquery-ui 1.10
                     .append("<a>" + item.label + "</a>")
                     .appendTo(ul);
                 };
             }

             // close autocomplete dropdown menu when y-axis scrolling happens
             $("#widget-container").on("ps-scroll-y", function() {
                 $("input.STRING").autocomplete("close");
             });

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
            }
             opus.widgets_drawn.unshift(slug);
             o_widgets.customWidgetBehaviors(slug);
             o_widgets.scrollToWidget(widget);
             o_search.getHinting(slug);

             if(deferredObj) {
                 deferredObj.resolve();
             }

      }); // end function success, end ajax
     }, // end func


     scrollToWidget: function(widget) {
        // scrolls window to a widget
        // widget is like: "widget__" + slug
        //  scroll the widget panel to top
        $('#search').animate({
            scrollTop: $("#"+ widget).offset().top
        }, 1000);
     },


     constructWidgetSizeHash: function(slug) {
         widget_sz = opus.prefs.widget_size[slug];
         if (opus.prefs.widget_scroll[slug]) {
             widget_sz += '+' + opus.prefs.widget_scroll[slug]; }
         return 'sz-' + slug + '=' + widget_sz;
     },




};
