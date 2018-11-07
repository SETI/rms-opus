var o_search = {

    /**
     *
     *  Everything that appears on the search tab
     *
     **/

    searchBehaviors: function() {
        // filling in a range or string search field = update the hash
        // range behaviors and string behaviors for search widgets - input box
        $('#search').on('change', 'input.STRING, input.RANGE', function() {

            var slug = $(this).attr("name");
            var css_class = $(this).attr("class").split(' ')[0]; // class will be STRING, min or max

            // get values of all inputs
            var values = [];
            if (css_class == 'STRING') {

                $('#widget__' + slug + ' input.STRING').each(function() {
                    values[values.length] = $(this).val();
                });
                opus.selections[slug] = values;

            } else {
                // range query
                var slug_no_num = slug.match(/(.*)[1|2]/)[1];
                // min
                values = [];
                $('#widget__' + slug_no_num + '1 input.min', '#search').each(function() {
                    values[values.length] = $(this).val();
                });
                if (values.length == 0) {
                    $('#widget__' + slug_no_num + ' input.min', '#search').each(function() {
                        values[values.length] = $(this).val();
                    });
                }

                opus.selections[slug_no_num + '1'] = values;
                // max
                values = [];
                $('#widget__' + slug_no_num + '1 input.max', '#search').each(function() {
                    values[values.length] = $(this).val();
                });
                if (values.length == 0) {
                    $('#widget__' + slug_no_num + ' input.max', '#search').each(function() {
                        values[values.length] = $(this).val();
                    });
                }

                opus.selections[slug_no_num + '2'] = values;
            }
            o_hash.updateHash();
        });

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
        });

        // range behaviors and string behaviors for search widgets - qtype select dropdown
        $('#search').on('change','select', function() {
            var qtypes = [];

            switch ($(this).attr("class")) {  // form type
                case "RANGE":
                    var slug_no_num = $(this).attr("name").match(/-(.*)/)[1];
                    var slug = slug_no_num + '1';

                    $('#widget__' + slug + ' select').each(function() {
                        qtypes[qtypes.length] = $(this).val();
                    });
                    opus.extras['qtype-' + slug_no_num] = qtypes;
                    break;

                case "STRING":
                    var slug = $(this).attr("name").match(/-(.*)/)[1];
                    $('#widget__' + slug + ' select').each(function() {
                        qtypes[qtypes.length] = $(this).val();
                    });
                    opus.extras['qtype-' + slug] = qtypes;
                    break;
            }

            o_hash.updateHash();
        });
    },

    adjustSearchHeight: function() {

        var container_height = $(window).height() - 100;
        $(".widget_column").height(container_height);
        $(".sidebar_wrapper").height(container_height);

    },

    getSearchTab: function() {

        if (opus.search_tab_drawn) { return; }

        // get any prefs from cookies
        if (!opus.prefs.widgets.length && $.cookie("widgets")) {
            opus.prefs.widgets = $.cookie("widgets").split(',');
        }
        // get menu
        o_menu.getMenu();

        // find and place the widgets
        if (!opus.prefs.widgets.length) {
            // no widgets defined, get the default widgets
            opus.prefs.widgets = ['planet','target'];
            o_widgets.placeWidgetContainers();
            o_widgets.getWidget('planet','#search_widgets');
            o_widgets.getWidget('target','#search_widgets');
        } else {
            if (!opus.widget_elements_drawn.length) {
                o_widgets.placeWidgetContainers();
            }
        }

        o_widgets.updateWidgetCookies();

        for (key in opus.prefs.widgets) {  // fetch each widget
            slug = opus.prefs.widgets[key];
            if ($.inArray(slug, opus.widgets_drawn) < 0) {  // only draw if not already drawn
                o_widgets.getWidget(slug,'#search_widgets');
            }
        }

        opus.search_tab_drawn = true;

        o_search.adjustSearchHeight();

    },

    getHinting: function(slug) {

        if ($('.widget__' + slug).hasClass('range-widget')) {
            // this is a range field
            o_search.getRangeEndpoints(slug);

        } else if ($('.widget__' + slug).hasClass('mult-widget')) {
            // this is a mult field
            o_search.getValidMults(slug);
        } else {
          $('#widget__' + slug + ' .spinner').fadeOut();
        }
    },

    getRangeEndpoints: function(slug) {

        $('#widget__' + slug + ' .spinner').fadeIn();

        var url = "/opus/__api/meta/range/endpoints/" + slug + ".json?" + o_hash.getHash() +  '&reqno=' + opus.lastRequestNo;
        $.ajax({url: url,
            dataType:"json",
            success: function(multdata){
                $('#widget__' + slug + ' .spinner').fadeOut();

                if (multdata['reqno'] < opus.lastRequestNo) {
                    return;
                }
                $('#hint__' + slug).html("<span>min: " + multdata['min'] +
                                         "</span><span>max: " + multdata['max'] +
                                         "</span><span> nulls: " + multdata['nulls'] + '</span>');
            },
            statusCode: {
                404: function() {
                    $('#widget__' + slug + ' .spinner').removeClass('spinning');
                }
            },
            error:function (xhr, ajaxOptions, thrownError){
                $('#widget__' + slug + ' .spinner').removeClass('spinning');
            }
        }); // end mults ajax
    },

    getValidMults: function (slug) {
        // turn on spinner
        $('#widget__' + slug + ' .spinner').fadeIn();

        var url = "/opus/__api/meta/mults/" + slug + ".json?" + o_hash.getHash() +  '&reqno=' + opus.lastRequestNo;
        $.ajax({url: url,
            dataType:"json",
            success: function(multdata){
                if (multdata['reqno'] < opus.lastRequestNo) {
                    return;
                }

                var dataSlug = multdata['field'];
                $('#widget__' + dataSlug + ' .spinner').fadeOut('');

                var widget = "widget__" + dataSlug;
                var mults = multdata['mults'];
                $('#' + widget + ' input').each( function() {
                    var value = $(this).attr('value');
                    var id = '#hint__' + slug + "_" + value.replace(/ /g,'-').replace(/[^\w\s]/gi, '');  // id of hinting span, defined in widgets.js getWidget

                    if (mults[value]){
                          $(id).html('<span>' + mults[value] + '</span>');
                          if ($(id).parent().hasClass("fadey")) {
                            $(id).parent().removeClass("fadey");
                          }
                    } else {
                        $(id).html('<span>0</span>');
                        $(id).parent().addClass("fadey");
                    }

                });

            },
            statusCode: {
                404: function() {
                  $('#widget__' + slug + ' .spinner').removeClass('spinning');
              }
            },
            error:function (xhr, ajaxOptions, thrownError){
                $('#widget__' + slug + ' .spinner').removeClass('spinning');
            }
        }); // end mults ajax

    },
};
