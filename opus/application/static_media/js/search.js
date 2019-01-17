var o_search = {

    /**
     *
     *  Everything that appears on the search tab
     *
     **/
    searchMsg: "",
    truncatedResults: false,
    truncatedResultsMsg: "&ltMore choices available&gt",
    slugStringSearchChoicesReqno: {},
    slugNormalizeReqno: {},
    slugRangeInputValidValueFromLastSearch: {},
    allNormalizedApiCall: function() {
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
        opus.waitingForAllNormalizedAPI = true;
        opus.lastAllNormalizeRequestNo++;
        let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + opus.lastAllNormalizeRequestNo;
        return $.getJSON(url);
    },
    validateRangeInput: function(normalizedInputData, removeSpinner=false) {
        opus.allInputsValid = true;
        o_search.slugRangeInputValidValueFromLastSearch = {};

        $.each(normalizedInputData, function(eachSlug, value) {
            let currentInput = $(`input[name="${eachSlug}"]`);
            if(value === null) {
                if(currentInput.hasClass("RANGE") && !currentInput.hasClass("input_currently_focused")) {
                    $("#sidebar").addClass("search_overlay");
                    currentInput.addClass("search_input_invalid_no_focus");
                    currentInput.removeClass("search_input_invalid");
                    currentInput.val(opus.selections[eachSlug]);
                    opus.allInputsValid = false;
                }

                if(currentInput.hasClass("input_currently_focused")) {
                    delete opus.selections[eachSlug];
                }
            } else {
                if(currentInput.hasClass("RANGE")) {
                    currentInput.val(value);
                    o_search.slugRangeInputValidValueFromLastSearch[eachSlug] = value;
                    // No color border if the input value is valid
                    currentInput.addClass("search_input_original");
                    currentInput.removeClass("search_input_invalid_no_focus");
                    currentInput.removeClass("search_input_invalid");
                    currentInput.removeClass("search_input_valid");
                }
            }
        });
        if(!opus.allInputsValid) {
            $("#result_count").text("?");
            // set hinting info to ? when any range input has invalid value
            // for range
            $(".range_hints").each(function() {
                if($(this).children().length > 0) {
                    $(this).html("<span>min: ?</span><span>max: ?</span><span> nulls: ?</span>");
                }
            });
            // for mults
            $(".hints").each(function() {
                $(this).html("<span>?</span>");
            });

            if(removeSpinner) {
                $(".spinner").fadeOut("");
            }
        }
    },
    parseFinalNormalizedInputDataAndUpdateHash: function(slug, url) {
        $.getJSON(url, function(normalizedInputData) {
            // Make sure it's the final call before parsing normalizedInputData
            if(normalizedInputData["reqno"] < o_search.slugNormalizeReqno[slug]) {
                return;
            }

            // check each range input, if it's not valid, change its background to red
            o_search.validateRangeInput(normalizedInputData);
            if(!opus.allInputsValid) {
                return;
            }

            o_hash.updateHash();
            if (o_utils.areObjectsEqual(opus.selections, opus.last_selections))  {
                // Put back normal hinting info
                opus.widgets_drawn.forEach(function(eachSlug) {
                    o_search.getHinting(eachSlug);
                });
                $("#result_count").text(o_utils.addCommas(opus.result_count));
            }
            $("input.RANGE").each(function() {
                if(!$(this).hasClass("input_currently_focused")){
                    $(this).removeClass("search_input_valid");
                    $(this).removeClass("search_input_invalid");
                    $(this).addClass("search_input_original");
                }
            });
            // $("input.RANGE").removeClass("search_input_valid");
            // $("input.RANGE").removeClass("search_input_invalid");
            // $("input.RANGE").addClass("search_input_original");
            $("#sidebar").removeClass("search_overlay");
        });
    },
    extractHtmlContent: function(htmlString) {
        let domParser = new DOMParser();
        let content = domParser.parseFromString(htmlString, "text/html").documentElement.textContent;
        return content;
    },
    searchBehaviors: function() {
        /*
        // result count display hover
        $('#result_count').parent().hover(
            function(){ $('#result_count').addClass('result_count_hover'); },
            function(){ $('#result_count').removeClass('result_count_hover'); }
        )
        */

        // the split form buttons - view the search form in 1 or 2 columns
        /*
        $('#split_search_form a').live('click', function() {
            col = $(this).attr("href");
            if (col == '#2col') {
                // clicked '2 columns' so add a 2nd column
                if (opus.search_form_cols==1) o_widgets.resetWidgetScrolls(); // changing shap calls for reset scrolls
                opus.search_form_cols = 2;
                o_search.addSecondFormsCol();
            } else {
                // clicked '1 column' remove the 2nd column
                if (opus.search_form_cols==2) o_widgets.resetWidgetScrolls(); // reset all scroll positions
                // first move the widgets to the first column
                opus.search_form_cols = 1;
                $('#search_widgets1').width('70%');
                $('#search_widgets2 .widget').each(function() {
                    $(this).appendTo('#search_widgets1');
                    slug = $(this).attr('id').split('__')[1];
                    opus.prefs.widgets.push(slug);
                    opus.prefs.widgets2.splice(jQuery.inArray(slug,opus.prefs.widgets2),1);
                    o_hash.updateHash();
                });

                $('#search_widgets1 .widget').each(function() {
                    o_widgets.adjustWidgetWidth(this);
                });
                // remove the 2nd column, widen the first column
                $('#search_widgets2').remove();
            }


            o_widgets.updateWidgetCookies();
            return false;
        });
        */

        // Avoid the orange blinking on border color, and also display proper border when input is in focus
        $("#search").on("focus", "input.RANGE", function(event) {
            let slug = $(this).attr("name");
            let currentValue = $(this).val().trim();
            if(o_search.slugRangeInputValidValueFromLastSearch[slug] || currentValue === "") {
              $(this).addClass("input_currently_focused");
              $(this).addClass("search_input_original");
            } else {
              $(this).addClass("input_currently_focused");
              $(this).addClass("search_input_invalid");
              $(this).removeClass("search_input_invalid_no_focus");
            }
        });

        /*
        This is to properly put back invalid search background
        when user focus out and there is no "change" event
        */
        $("#search").on("focusout", "input.RANGE", function(event) {
            let slug = $(this).attr("name");
            let currentValue = $(this).val().trim();
            $(this).removeClass("input_currently_focused");
            if($(this).hasClass("search_input_invalid")) {
                $(this).addClass("search_input_invalid_no_focus");
                $(this).removeClass("search_input_invalid");
            }
        });

        // Dynamically get input values right after user input a character
        $("#search").on("input", "input.RANGE", function(event) {
            if(!$(this).hasClass("input_currently_focused")) {
                $(this).addClass("input_currently_focused");
            }

            let slug = $(this).attr("name");
            let currentValue = $(this).val().trim();
            let values = []

            opus.lastSlugNormalizeRequestNo++;
            o_search.slugNormalizeReqno[slug] = opus.lastSlugNormalizeRequestNo;

            // values.push(currentValue)
            // opus.selections[slug] = values;
            // Call normalized api with the current focused input slug
            let newHash = `${slug}=${currentValue}`;

            /*
            Do not perform normalized api call if:
            1) Input field is empty OR
            2) Input value didn't change from the last successful search
            */
            if(currentValue === "" || currentValue === o_search.slugRangeInputValidValueFromLastSearch[slug]) {
                $(event.target).removeClass("search_input_valid search_input_invalid");
                $(event.target).addClass("search_input_original");
                return;
            }

            let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + opus.lastSlugNormalizeRequestNo;
            $.getJSON(url, function(data) {
                // Make sure the return json data is from the latest normalized api call
                if(data["reqno"] < o_search.slugNormalizeReqno[slug]) {
                    return;
                }

                let returnData = data[slug];
                /*
                Parse normalized data
                If it's empty string, don't modify anything
                If it's null, add search_input_invalid class
                If it's valid, add search_input_valid class
                */
                if(returnData === "") {
                    $(event.target).removeClass("search_input_valid search_input_invalid");
                    $(event.target).addClass("search_input_original");
                } else if(returnData !== null) {
                    $(event.target).removeClass("search_input_original search_input_invalid");
                    $(event.target).removeClass("search_input_invalid_no_focus");
                    $(event.target).addClass("search_input_valid");
                } else {
                    $(event.target).removeClass("search_input_original search_input_valid");
                    $(event.target).removeClass("search_input_invalid_no_focus");
                    $(event.target).addClass("search_input_invalid");
                }
            }); // end getJSON
        });

        /*
        When user focusout or hit enter on any range input:
        Call final normalized api and validate all inputs
        Update URL (and search) if all inputs are valid
        */
        $("#search").on("change", "input.RANGE", function(event) {
            let slug = $(this).attr("name");
            let currentValue = $(this).val().trim();
            let values = []
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
            opus.lastSlugNormalizeRequestNo++;
            o_search.slugNormalizeReqno[slug] = opus.lastSlugNormalizeRequestNo;
            let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + opus.lastSlugNormalizeRequestNo;

            if($(event.target).hasClass("input_currently_focused")) {
                $(event.target).removeClass("input_currently_focused");
            }
            o_search.parseFinalNormalizedInputDataAndUpdateHash(slug, url);
        });

        // filling in a range or string search field = update the hash
        // range behaviors and string behaviors for search widgets - input box
        $('#search').on('change', 'input.STRING', function(event) {
            let slug = $(this).attr("name");
            let css_class = $(this).attr("class").split(' ')[0]; // class will be STRING, min or max

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

            if(opus.last_selections && opus.last_selections[slug]) {
                if(opus.last_selections[slug][0] === $(this).val().trim()) {
                    return;
                }
            }
            // make a normalized call to avoid changing url whenever there is an invalid range input value
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
            opus.lastSlugNormalizeRequestNo++;
            o_search.slugNormalizeReqno[slug] = opus.lastSlugNormalizeRequestNo;
            let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + opus.lastSlugNormalizeRequestNo;
            o_search.parseFinalNormalizedInputDataAndUpdateHash(slug, url);
        });

        // range behaviors and string behaviors for search widgets - qtype select dropdown
        $('#search').on('change','select', function() {
            var qtypes = [];
            var form_type = $(this).attr("class");

            if (form_type == 'RANGE') {
                slug_no_num = $(this).attr("name").match(/-(.*)/)[1];
                slug = slug_no_num + '1';

                $('#widget__' + slug + ' select').each(function() {
                    qtypes[qtypes.length] = $(this).val();
                });
                opus.extras['qtype-' + slug_no_num] = qtypes;

            } else if (form_type == 'STRING') {
                slug = $(this).attr("name").match(/-(.*)/)[1];
                $('#widget__' + slug + ' select').each(function() {
                    qtypes[qtypes.length] = $(this).val();
                });
                opus.extras['qtype-' + slug] = qtypes;
            }
            o_hash.updateHash();
        });

        // "add range" and "add string" search behaviors -- todo
        $('#search').on("click", 'a.add_input, a.add_input', function() {
            return false;
            slug = $(this).parent().parent().parent().parent().attr("class").split(' ')[0].match(/\__(.*)/)[1]; // shoot me now.
            count = $('#widget__' + slug + ' input').length + 1;

            // no bring in another note form
            // we don't want
            $.ajax({ url: "/opus/__forms/widget/" + slug + '.html?addlink=false',
                success: function(widget_str){
                    // we don't want to insert the entire widget, only the span class = "widget_form" section
                    html = widget_str.match(/<section>([\s\S]*)<\/section>/)[0];
                    $(html).appendTo('#widget__' + slug + ' .widget_inner');
                }});
            return false;

        });

        // add range add string search behaviors - remove string -- todo
        $('#search').on("click", '.STRING a.remove_input, .RANGE a.remove_input', function() {
            return false;

            var slug = $(this).parent().parent().parent().parent().parent().parent().attr("id").match(/\__(.*)/)[1];
            form_type = 'STRING';
            if ($('#widget__' + slug + ' .widget_inner').hasClass('RANGE')) form_type = 'RANGE';
            var qname = 'qtype-' + slug;

            if (form_type == 'RANGE') {
                var min = slug.match(/(.*)[1|2]/)[1] + '1';
                var max = slug.match(/(.*)[1|2]/)[1] + '2';
                var input_val_max = $(this).parent().prev().prev().children('input').val();
                var input_val_min = $(this).parent().prev().prev().prev().children('input').val();


                $(this).parent().parent().remove(); // the section

                // removing a range means removing any values entered from the opus.selections and updating the hash
                if (typeof(opus.selections[min]) != 'undefined' || typeof(opus.selections[min])  != 'undefined') {
                    // this range is contrained, are we removing
                    // loop through the opus.selections to find the pair we are removing
                    lngth = Math.max(opus.selections[min].length, opus.selections[max].length);
                    for (var key=0;key<lngth;key++) {
                        if (opus.selections[min][key] == input_val_min && opus.selections[max][key] == input_val_max) {
                            // this is the pair we need to remove
                            opus.selections[min].splice(key,1);
                            opus.selections[max].splice(key,1);
                            if (jQuery.inArray(qname, opus.extras) > -1 && typeof(opus.extras[qname]) != 'undefined') {
                                opus.extras[qname].splice(key,1);
                            }
                            break;
                        }
                    }
                }
            } else { // this is a STRING field
                var input_val = $(this).parent().prev().prev().children('input').val();

                $(this).parent().prev().prev().remove(); // the section
                $(this).parent().prev().remove(); // the section
                $(this).parent().remove(); // the section
                // $(this).parent().prev().remove(); // the section

                if (typeof(opus.selections[slug]) != 'undefined') {
                    for (key in opus.selections[slug]) {
                         if (opus.selections[slug][key] == input_val) {
                             opus.selections[slug].splice(key,1);
                              if (jQuery.inArray(qname, opus.extras) > -1 && typeof(opus.extras[qname]) != 'undefined') {
                                 opus.extras[qname].splice(key,1);
                             }
                             break;
                         }
                    }
                }
            }
                o_hash.updateHash();
                return false;
            });
    },

    adjustSearchHeight: function() {

        container_height = $(window).height() - 100;
        $(".widget_column").height(container_height);
        $(".sidebar_wrapper").height(container_height);

    },

    getSearchTab: function() {

        if (opus.search_tab_drawn) { return; }
        // widgets1 is the left column of widgets, wigets2 is the optional right col

        // get any prefs from cookies
        if (!opus.prefs.widgets.length && $.cookie("widgets")) {
            opus.prefs.widgets = $.cookie("widgets").split(',');
        }
        if (!opus.prefs.widgets2.length && $.cookie("widgets2")) {
            opus.prefs.widgets2 = $.cookie("widgets2").split(',');
        }

        // get menu
        o_menu.getMenu();

        // find and place the widgets
        if (!opus.prefs.widgets.length && !opus.prefs.widgets2.length) {
            // no widgets defined, get the default widgets
            opus.prefs.widgets = ['planet','target'];
            o_widgets.placeWidgetContainers();
            o_widgets.getWidget('planet','#search_widgets1');
            o_widgets.getWidget('target','#search_widgets1');
        } else {
            if (!opus.widget_elements_drawn.length) {
                o_widgets.placeWidgetContainers();
            }
        }

        o_widgets.updateWidgetCookies();

        for (key in opus.prefs.widgets) {  // fetch each widget
            slug = opus.prefs.widgets[key];
            if (jQuery.inArray(slug, opus.widgets_drawn) < 0) {  // only draw if not already drawn
                o_widgets.getWidget(slug,'#search_widgets1');
            }
        }

        for (key in jQuery.unique(opus.prefs.widgets2)) {  // fetch each widget
            slug = opus.prefs.widgets2[key];
            if (jQuery.inArray(slug, opus.widgets_drawn) < 0) {  // only draw if not already drawn
                o_widgets.getWidget(slug,'#search_widgets2');
            }
        }
        opus.search_tab_drawn = true;

        o_search.adjustSearchHeight();

    },


    addSecondFormsCol: function() {
        var width = '35%';
        if (!$('#search_widgets2').length) {
            $('.formscolumn').width(width);

            $('#search_widgets1').after('<ul  id = "search_widgets2" style = "width:' + width + '" class="formscolumn"></ul>')
                              .animate({width:width},'fast');
            $('#search_widgets1, #search_widgets2').sortable({
                    connectWith: '.formscolumn',
                    handle:'.widget_draghandle',
                    cursor: 'crosshair',
                    stop: function(event,ui) {
                        o_widgets.widgetDrop(ui);
                    }
            });

            $('#search_widgets1 .widget').each(function() {
                o_widgets.adjustWidgetWidth(this);
            });

        }
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

                    min = multdata['min'];
                    max = multdata['max'];
                    nulls = multdata['nulls'];

                    widget = "widget__" + slug;
                    $('#hint__' + slug).html("<span>min: " + min + "</span><span>max: " + max + "</span><span> nulls: " + nulls + '</span>');

                },
                statusCode: {
                    404: function() {
                      $('#widget__' + slug + ' .spinner').removeClass('spinning');
                  }
                },
                error:function (xhr, ajaxOptions, thrownError){
                    $("#widget__" + slug + " .spinner").removeClass("spinning");
                    // range input hints are "?" when wrong values of url is pasted
                    $("#hint__" + slug).html("<span>min: ?</span><span>max: ?</span><span> nulls: ?</span>");
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

                $('#widget__' + slug + ' .spinner').fadeOut('');

                if (multdata['reqno'] < opus.lastRequestNo) {
                    return;
                }
                slug = multdata['field'];
                widget = "widget__" + slug;
                mults = multdata['mults'];
                $('#' + widget + ' input').each( function() {
                    value = $(this).attr('value');
                    id = '#hint__' + slug + "_" + value.replace(/ /g,'-').replace(/[^\w\s]/gi, '');  // id of hinting span, defined in widgets.js getWidget

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
                $("#widget__" + slug + " .spinner").removeClass("spinning");
                // checkbox hints are "?" when wrong values of url is pasted
                $(".hints").each(function() {
                    $(this).html("<span>?</span>");
                });
            }
        }); // end mults ajax

    },



};
