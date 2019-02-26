var o_search = {

    /**
     *
     *  Everything that appears on the search tab
     *
     **/
    searchScrollbar: new PerfectScrollbar("#sidebar-container", { suppressScrollX: true }),
    widgetScrollbar: new PerfectScrollbar("#widget-container"),

    // for input validation in the search widgets
    searchResultsNotEmpty: false,
    searchMsg: "",
    truncatedResults: false,
    truncatedResultsMsg: "&ltMore choices available&gt",
    lastSlugNormalizeRequestNo: 0,
    lastMultsRequestNo: 0,
    lastEndpointsRequestNo: 0,

    slugStringSearchChoicesReqno: {},
    slugNormalizeReqno: {},
    slugMultsReqno: {},
    slugEndpointsReqno: {},
    slugRangeInputValidValueFromLastSearch: {},

    searchBehaviors: function() {
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

            o_search.lastSlugNormalizeRequestNo++;
            o_search.slugNormalizeReqno[slug] = o_search.lastSlugNormalizeRequestNo;

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

            let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + o_search.lastSlugNormalizeRequestNo;
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
            Opus will rewrite the URL when a URL is pasted, and all the search related slugs will be moved ahead of "&view"
            Refer to hash.js getSelectionsFromHash and updateHash functions
            */
            let regexForHashWithSearchParams = /(.*)&view/;
            if(newHash.match(regexForHashWithSearchParams)) {
                newHash = newHash.match(regexForHashWithSearchParams)[1];
            }
            o_search.lastSlugNormalizeRequestNo++;
            o_search.slugNormalizeReqno[slug] = o_search.lastSlugNormalizeRequestNo;
            let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + o_search.lastSlugNormalizeRequestNo;

            if($(event.target).hasClass("input_currently_focused")) {
                $(event.target).removeClass("input_currently_focused");
            }
            o_search.parseFinalNormalizedInputDataAndUpdateHash(slug, url);
        });

        $('#search').on("change", 'input.STRING', function(event) {

            let slug = $(this).attr("name");
            let css_class = $(this).attr("class").split(' ')[0]; // class will be STRING, min or max

            // get values of all inputs
            var values = [];
            if (css_class == 'STRING') {
                $("#widget__" + slug + ' input.STRING').each(function() {
                    values[values.length] = $(this).val();
                });
                opus.selections[slug] = values;
            } else {
                // range query
                var slug_no_num = slug.match(/(.*)[1|2]/)[1];
                // min
                values = [];
                $("#widget__" + slug_no_num + '1 input.min', '#search').each(function() {
                    values[values.length] = $(this).val();
                });
                if (values.length == 0) {
                    $("#widget__" + slug_no_num + ' input.min', '#search').each(function() {
                        values[values.length] = $(this).val();
                    });
                }

                opus.selections[slug_no_num + '1'] = values;
                // max
                values = [];
                $("#widget__" + slug_no_num + '1 input.max', '#search').each(function() {
                    values[values.length] = $(this).val();
                });
                if (values.length == 0) {
                    $("#widget__" + slug_no_num + ' input.max', '#search').each(function() {
                        values[values.length] = $(this).val();
                    });
                }

                opus.selections[slug_no_num + '2'] = values;
            }

            if (opus.last_selections && opus.last_selections[slug]) {
                if (opus.last_selections[slug][0] === $(this).val().trim()) {
                    return;
                }
            }
            // make a normalized call to avoid changing url whenever there is an invalid range input value
            let newHash = o_hash.updateHash(false);
            /*
            We are relying on URL order now to parse and get slugs before "&view" in the URL
            Opus will rewrite the URL when a URL is pasted, and all the search related slugs will be moved ahead of "&view"
            Refer to hash.js getSelectionsFromHash and updateHash functions
            */
            let regexForHashWithSearchParams = /(.*)&view/;
            if (newHash.match(regexForHashWithSearchParams)) {
                newHash = newHash.match(regexForHashWithSearchParams)[1];
            }
            o_search.lastSlugNormalizeRequestNo++;
            o_search.slugNormalizeReqno[slug] = o_search.lastSlugNormalizeRequestNo;
            let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + o_search.lastSlugNormalizeRequestNo;
            o_search.parseFinalNormalizedInputDataAndUpdateHash(slug, url);
        });

        $('#search').on("change", 'input.multichoice, input.singlechoice', function() {
           // mult widget gets changed
           var id = $(this).attr("id").split('_')[0];
           var value = $(this).attr("value").replace(/\+/g, '%2B');

           if ($(this).is(':checked')) {
               var values = [];
               if (opus.selections[id]) {
                   var values = opus.selections[id]; // this param already has been constrained
               }

               // for surfacegeometry we only want a target selected
               if (id === 'surfacegeometrytargetname') {
                  opus.selections[id] = [value];
               } else {
                  // add the new value to the array of values
                  values[values.length] = value;
                  // add the array of values to selections
                  opus.selections[id] = values;
               }

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
        $('#search').on("change","select", function() {
            var qtypes = [];

            switch ($(this).attr("class")) {  // form type
                case "RANGE":
                    var slug_no_num = $(this).attr("name").match(/-(.*)/)[1];
                    var slug = slug_no_num + '1';

                    $("#widget__" + slug + ' select').each(function() {
                        qtypes[qtypes.length] = $(this).val();
                    });
                    opus.extras['qtype-' + slug_no_num] = qtypes;
                    break;

                case "STRING":
                    var slug = $(this).attr("name").match(/-(.*)/)[1];
                    $("#widget__" + slug + ' select').each(function() {
                        qtypes[qtypes.length] = $(this).val();
                    });
                    opus.extras['qtype-' + slug] = qtypes;
                    break;
            }

            o_hash.updateHash();
        });
    },

    allNormalizedApiCall: function() {
        let newHash = o_hash.updateHash(false);
        /*
        We are relying on URL order now to parse and get slugs before "&view" in the URL
        Opus will rewrite the URL when a URL is pasted, and all the search related slugs will be moved ahead of "&view"
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
                if(currentInput.hasClass("RANGE")) {
                    if(currentInput.hasClass("input_currently_focused")) {
                        $("#sidebar").addClass("search_overlay");
                    } else {
                        $("#sidebar").addClass("search_overlay");
                        currentInput.addClass("search_input_invalid_no_focus");
                        currentInput.removeClass("search_input_invalid");
                        currentInput.val(opus.selections[eachSlug]);
                    }
                }
                opus.allInputsValid = false;
            } else {
                if(currentInput.hasClass("RANGE")) {
                    /*
                    If current focused input value is different from returned normalized data
                    we will not overwrite its displayed value.
                    */
                    if(currentInput.hasClass("input_currently_focused") && currentInput.val() !== value) {
                        o_search.slugRangeInputValidValueFromLastSearch[eachSlug] = value;
                    } else {
                        currentInput.val(value);
                        o_search.slugRangeInputValidValueFromLastSearch[eachSlug] = value;
                        // No color border if the input value is valid
                        currentInput.addClass("search_input_original");
                        currentInput.removeClass("search_input_invalid_no_focus");
                        currentInput.removeClass("search_input_invalid");
                        currentInput.removeClass("search_input_valid");
                    }
                }
            }
        });

        if (!opus.allInputsValid) {
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

    adjustSearchHeight: function() {
        o_search.adjustSearchSideBarHeight();
        o_search.adjustSearchWidgetHeight();
    },

    adjustSearchSideBarHeight: function() {
        let containerHeight = $("#search").height() - 120;
        let searchMenuHeight = $(".searchMenu").height();
        $(".sidebar_wrapper").height(containerHeight);

        if(containerHeight > searchMenuHeight) {
            if(!$("#sidebar-container .ps__rail-y").hasClass("hide_ps__rail-y")) {
                $("#sidebar-container .ps__rail-y").addClass("hide_ps__rail-y");
                o_search.searchScrollbar.settings.suppressScrollY = true;
            }
        } else {
            $("#sidebar-container .ps__rail-y").removeClass("hide_ps__rail-y");
            o_search.searchScrollbar.settings.suppressScrollY = false;
        }

        o_search.searchScrollbar.update();
    },

    adjustSearchWidgetHeight: function() {
        let containerHeight = $("#search").height() - 120;
        let searchWidgetHeight = $("#search_widgets").height();
        $(".widget_column").height(containerHeight);

        if(containerHeight > searchWidgetHeight) {
            if(!$("#widget-container .ps__rail-y").hasClass("hide_ps__rail-y")) {
                $("#widget-container .ps__rail-y").addClass("hide_ps__rail-y");
                o_search.widgetScrollbar.settings.suppressScrollY = true;
            }
        } else {
            $("#widget-container .ps__rail-y").removeClass("hide_ps__rail-y");
            o_search.widgetScrollbar.settings.suppressScrollY = false;
        }

        o_search.widgetScrollbar.update();
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
            opus.prefs.widgets = ["planet","target"];
            o_widgets.placeWidgetContainers();
            o_widgets.getWidget("planet","#search_widgets");
            o_widgets.getWidget("target","#search_widgets");
        } else {
            if (!opus.widget_elements_drawn.length) {
                o_widgets.placeWidgetContainers();
            }
        }

        o_widgets.updateWidgetCookies();

        for (key in opus.prefs.widgets) {  // fetch each widget
            slug = opus.prefs.widgets[key];
            if ($.inArray(slug, opus.widgets_drawn) < 0) {  // only draw if not already drawn
                o_widgets.getWidget(slug,"#search_widgets");
            }
        }

        opus.search_tab_drawn = true;

        o_search.adjustSearchHeight();
    },

    getHinting: function(slug, deferredObj) {

        if ($(".widget__" + slug).hasClass("range-widget")) {
            // this is a range field
            o_search.getRangeEndpoints(slug, deferredObj);

        } else if ($(".widget__" + slug).hasClass("mult-widget")) {
            // this is a mult field
            o_search.getValidMults(slug, deferredObj);
        } else {
          $(`#widget__${slug}.spinner`).fadeOut();
          let adjustSearchWidgetHeight = _.debounce(o_search.adjustSearchWidgetHeight, 200);
          adjustSearchWidgetHeight();
        }
    },

    getRangeEndpoints: function(slug) {

        $(`#widget__${slug}.spinner`).fadeIn();

        o_search.lastEndpointsRequestNo++;
        o_search.slugEndpointsReqno[slug] = o_search.lastEndpointsRequestNo;
        var url = `/opus/__api/meta/range/endpoints/${slug}.json?${o_hash.getHash()}&reqno=${o_search.slugEndpointsReqno[slug]}`;
        $.ajax({url: url,
            dataType:"json",
            success: function(multdata){
                $(`#widget__${slug}.spinner`).fadeOut();

                if (multdata.reqno< o_search.slugEndpointsReqno[slug]) {
                    return;
                }
                $('#hint__' + slug).html(`<span>min: ${multdata.min}</span><span>max: ${multdata.max}</span><span> nulls: ${multdata.nulls}</span>`);
                let adjustSearchWidgetHeight = _.debounce(o_search.adjustSearchWidgetHeight, 200);
                adjustSearchWidgetHeight();
            },
            statusCode: {
                404: function() {
                    $(`#widget__${slug}.spinner`).removeClass("spinning");
                }
            },
            error:function (xhr, ajaxOptions, thrownError){
                $(`#widget__${slug}.spinner`).removeClass("spinning");
                // range input hints are "?" when wrong values of url is pasted
                $(`#hint__${slug}`).html("<span>min: ?</span><span>max: ?</span><span> nulls: ?</span>");
            }
        }); // end mults ajax
    },

    getValidMults: function (slug) {
        // turn on spinner
        $(`#widget__${slug}.spinner`).fadeIn();

        o_search.lastMultsRequestNo++;
        o_search.slugMultsReqno[slug] = o_search.lastMultsRequestNo;
        var url = `/opus/__api/meta/mults/${slug}.json?${o_hash.getHash()}&reqno=${o_search.slugMultsReqno[slug]}`;
        $.ajax({url: url,
            dataType:"json",
            success: function(multdata){
                if (multdata.reqno < o_search.slugMultsReqno[slug]) {
                    return;
                }

                var dataSlug = multdata.field;
                $("#widget__" + dataSlug + " .spinner").fadeOut('');

                var widget = "widget__" + dataSlug;
                var mults = multdata.mults;
                $('#' + widget + ' input').each( function() {
                    var value = $(this).attr("value");
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
                let adjustSearchWidgetHeight = _.debounce(o_search.adjustSearchWidgetHeight, 200);
                adjustSearchWidgetHeight();
            },
            statusCode: {
                404: function() {
                  $(`#widget__${slug}.spinner`).removeClass("spinning");
              }
            },
            error:function (xhr, ajaxOptions, thrownError){
                $(`#widget__${slug}.spinner`).removeClass("spinning");
                // checkbox hints are "?" when wrong values of url is pasted
                $(".hints").each(function() {
                    $(this).html("<span>?</span>");
                });
            }
        }); // end mults ajax

    },
};
