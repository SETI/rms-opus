/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $, PerfectScrollbar */
/* globals o_browse, o_hash, o_menu, o_utils, o_widgets, opus */

/* jshint varstmt: false */
var o_search = {
/* jshint varstmt: true */

    /**
     *
     *  Everything that appears on the search tab
     *
     **/
    searchScrollbar: new PerfectScrollbar("#sidebar-container", {
        suppressScrollX: true,
        minScrollbarLength: opus.minimumPSLength
    }),
    widgetScrollbar: new PerfectScrollbar("#widget-container" , {
        suppressScrollX: true,
        minScrollbarLength: opus.minimumPSLength
    }),

    // for input validation in the search widgets
    searchTabDrawn: false,
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

    // Based on user's input, store the number of matched info by category, for example:
    // In ring radius, when user types "ha":
    // { "jupiter-inner-satellites": 0, "jupiter-rings": 1, "neptune-inner-satellites": 1, "neptune-rings": 0,
    //   "saturn-regular-satellites": 0, "saturn-rings": 0, "uranus-inner-satellites": 0, "uranus-rings": 3 }
    rangesNameMatchedCounterByCategory: {},
    // Store the total number of matched info of an input in a widget's ranges dropdown,
    // in above example, it's 5. We use slug as the key to tell which input set the user
    // is currently focusing in.
    rangesNameTotalMatchedCounter: {},
    // Store rangesNameMatchedCounterByCategory for each input field. Use slug + id as the key.
    inputsRangesNameMatchedInfo:{},
    // Use to determine if we should automatically expand/collapse ranges info. If it's set
    // to true, we will automatically expand/collapse ranges info depending on the matched letters.
    isTriggeredFromInput: false,
    // Use to determine if user's input should proceed with validation and search when user types in
    // ranges names. We use slug with uniqueid as the key.
    performInputValidation: {},

    addSearchBehaviors: function() {
        // Avoid the orange blinking on border color, and also display proper border when input is in focus
        $("#search").on("focus", "input.RANGE", function(e) {
            let inputName = $(this).attr("name");
            let currentValue = $(this).val().trim();
            let slug = o_utils.getSlugOrDataWithoutCounter(inputName);
            let uniqueid = $(this).attr("data-uniqueid");
            let slugWithId = `${slug}_${uniqueid}`;

            o_search.performInputValidation[slugWithId] = (o_search.performInputValidation[slugWithId] ||
                                                           true);
            if (o_search.slugRangeInputValidValueFromLastSearch[slugWithId] ||
                currentValue === "" || !o_search.performInputValidation[slugWithId] || !$(this).hasClass("search_input_invalid_no_focus")) {
                $(this).addClass("search_input_original");
            } else {
                $(this).addClass("search_input_invalid");
            }
            $(this).addClass("input_currently_focused");
            $(this).removeClass("search_input_invalid_no_focus");

            // Open the dropdown properly when user tabs to focus in.
            let preprogrammedRangesDropdown = ($(this)
                                               .next(".op-preprogrammed-ranges")
                                               .find(".op-scrollable-menu"));

            o_search.rangesNameTotalMatchedCounter[slugWithId] =
            (o_search.rangesNameTotalMatchedCounter[slugWithId] || 0);

            if ((preprogrammedRangesDropdown.length !== 0 && $(e.target).hasClass("op-range-input-min")) &&
                (!currentValue || o_search.rangesNameTotalMatchedCounter[slugWithId] > 0) &&
                !preprogrammedRangesDropdown.hasClass("show")) {
                o_widgets.isKeepingRangesDropdownOpen = true;
                $(this).dropdown("toggle");
            }
        });

        /*
        This is to properly put back invalid search background
        when user focus out and there is no "change" event
        */
        $("#search").on("focusout", "input.RANGE", function(e) {
            let currentValue = $(this).val().trim();
            let inputName = $(this).attr("name");
            let slug = o_utils.getSlugOrDataWithoutCounter(inputName);
            let uniqueid = $(this).attr("data-uniqueid");
            let slugWithId = `${slug}_${uniqueid}`;
            // Disable browse tab nav link when user focuses out and there is a change of value
            // in range input. The button will be enabled or keep disabled based on the
            // result of input validation in parseFinalNormalizedInputDataAndUpdateURL.
            if ((currentValue && currentValue !== o_search.slugRangeInputValidValueFromLastSearch[slugWithId]) ||
                (!currentValue && o_search.slugRangeInputValidValueFromLastSearch[slugWithId])) {
                $(".op-browse-tab").addClass("op-disabled-nav-link");
            }

            $(this).removeClass("input_currently_focused");
            if ($(this).hasClass("search_input_invalid")) {
                $(this).addClass("search_input_invalid_no_focus");
                $(this).removeClass("search_input_invalid");
            } else {
                $(this).removeClass("search_input_valid");
                $(this).removeClass("search_input_invalid");
                $(this).addClass("search_input_original");
            }

            // Close the dropdown properly when user focuses out.
            let preprogrammedRangesDropdown = ($(this)
                                               .next(".op-preprogrammed-ranges")
                                               .find(".op-scrollable-menu"));
            if (preprogrammedRangesDropdown.length !== 0 &&
                preprogrammedRangesDropdown.hasClass("show")) {
                $(this).dropdown("toggle");
            }

            o_widgets.isKeepingRangesDropdownOpen = false;
        });

        o_search.addPreprogrammedRangesSearchBehaviors();

        // Dynamically get input values right after user input a character
        $("#search").on("input", "input.RANGE", function(e) {
            if (!$(this).hasClass("input_currently_focused")) {
                $(this).addClass("input_currently_focused");
            }

            let inputName = $(this).attr("name");
            let slugWithoutCounter = o_utils.getSlugOrDataWithoutCounter(inputName);
            let uniqueId = $(this).attr("data-uniqueid");
            let slugWithId = `${slugWithoutCounter}_${uniqueId}`;

            let currentValue = $(this).val().trim();
            // Check if there is any match between input values and ranges names
            o_search.compareInputWithRangesInfo(currentValue, e.target);

            o_search.lastSlugNormalizeRequestNo++;
            o_search.slugNormalizeReqno[slugWithId] = o_search.lastSlugNormalizeRequestNo;

            // Call normalized api with the current focused input slug
            let newHash = `${slugWithId}=${currentValue}`;

            /*
            Do not perform normalized api call if:
            1) Input field is empty OR
            2) Input value didn't change from the last successful search
            3) Input value didn't match any ranges names
            */
            if (currentValue === "" || currentValue === o_search.slugRangeInputValidValueFromLastSearch[slugWithId] ||
                !o_search.performInputValidation[slugWithId]) {
                $(e.target).removeClass("search_input_valid search_input_invalid");
                $(e.target).removeClass("search_input_invalid_no_focus");
                $(e.target).addClass("search_input_original");
                return;
            }

            opus.normalizeInputForCharInProgress[slugWithId] = true;
            let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + o_search.lastSlugNormalizeRequestNo;
            $.getJSON(url, function(data) {
                // Make sure the return json data is from the latest normalized api call
                if (data.reqno < o_search.slugNormalizeReqno[slugWithId]) {
                    delete opus.normalizeInputForCharInProgress[slugWithId];
                    return;
                }

                let returnData = data[slugWithId];
                /*
                Parse normalized data
                If it's empty string, don't modify anything
                If it's null, add search_input_invalid class
                If it's valid, add search_input_valid class
                */
                if (returnData === "") {
                    $(e.target).removeClass("search_input_valid search_input_invalid");
                    $(e.target).addClass("search_input_original");
                } else if (returnData !== null) {
                    $(e.target).removeClass("search_input_original search_input_invalid");
                    $(e.target).removeClass("search_input_invalid_no_focus");
                    $(e.target).addClass("search_input_valid");
                } else {
                    $(e.target).removeClass("search_input_original search_input_valid");
                    $(e.target).removeClass("search_input_invalid_no_focus");
                    $(e.target).addClass("search_input_invalid");
                }

                delete opus.normalizeInputForCharInProgress[slugWithId];
            }); // end getJSON
        });

        /*
        When user focusout or hit enter on any range input:
        Call final normalized api and validate all inputs
        Update URL (and search) if all inputs are valid
        */
        $("#search").on("change", "input.RANGE", function(e) {
            let inputName = $(this).attr("name");
            let slugName = $(this).data("slugname");
            let slug = o_utils.getSlugOrDataWithoutCounter(inputName);
            let uniqueid = $(this).attr("data-uniqueid");
            let slugWithId = `${slug}_${uniqueid}`;

            let currentValue = $(this).val().trim();
            o_search.rangesNameTotalMatchedCounter[slugWithId] = (o_search.rangesNameTotalMatchedCounter[slugWithId] ||
                                                                 0);
            if (o_search.rangesNameTotalMatchedCounter[slugWithId] === 1) {
                let matchedCatId = "";
                let currentinputsRangesNameMatchedInfo = o_search.inputsRangesNameMatchedInfo[slugWithId] || {};
                for (const eachCat in currentinputsRangesNameMatchedInfo) {
                    if (currentinputsRangesNameMatchedInfo[eachCat] === 1) {
                        matchedCatId = `#${eachCat}`;
                        break;
                    }
                }
                let allItemsInMatchedCat = $(`${matchedCatId} .op-preprogrammed-ranges-data-item`);
                for (const singleRangeData of allItemsInMatchedCat) {
                    if (!$(singleRangeData).hasClass("op-hide-element")) {
                        let minVal = $(singleRangeData).data("min");
                        let maxVal = $(singleRangeData).data("max");
                        let widgetId = $(singleRangeData).data("widget");
                        let minInputSlug = $(singleRangeData).parent(".container").attr("data-mininput");

                        // NOTE: We need support both RANGE & STRING inputs, for now we implement RANGE first.
                        if ($(`#${widgetId} input.RANGE`).length !== 0) {
                            o_widgets.fillRangesInputs(widgetId, minInputSlug, maxVal, minVal);
                            o_search.rangesNameTotalMatchedCounter[slugWithId] = 0;
                            // close dropdown and trigger the search
                            $(`#widget__${slugName} input.op-range-input-min[name="${inputName}"]`).dropdown("toggle");
                            $(`#${widgetId} input.RANGE[name="${inputName}"]`).trigger("change");
                            let oppositeSuffixSlug = (slug.match(/(.*)1$/) ? `${slugName}2` : `${slugName}1`);
                            $(`#${widgetId} input.RANGE[name*="${oppositeSuffixSlug}"][data-uniqueid="${uniqueid}"]`).trigger("change");
                            return;
                        }
                        break;
                    }
                }
            } else {
                // close the dropdown
                let inputToTriggerDropdown = $(`#widget__${slugName} input.op-range-input-min[name="${inputName}"]`);
                let preprogrammedRangesDropdown = (inputToTriggerDropdown
                                                   .next(".op-preprogrammed-ranges")
                                                   .find(".op-scrollable-menu"));

                if (preprogrammedRangesDropdown.hasClass("show")) {
                    inputToTriggerDropdown.dropdown("toggle");
                }
            }

            // Call normalize input api with only the slug and value from current input.
            let newHash = `${slugWithId}=${currentValue}`;

            o_search.lastSlugNormalizeRequestNo++;
            o_search.slugNormalizeReqno[slugWithId] = o_search.lastSlugNormalizeRequestNo;

            opus.normalizeInputForAllFieldsInProgress[slugWithId] = true;
            let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + o_search.lastSlugNormalizeRequestNo;

            if ($(e.target).hasClass("input_currently_focused")) {
                $(e.target).removeClass("input_currently_focused");
            }

            o_search.parseFinalNormalizedInputDataAndUpdateURL(slugWithId, url);
        });

        $('#search').on("change", 'input.STRING', function(event) {
            let inputName = $(this).attr("name");
            let slug = o_utils.getSlugOrDataWithoutCounter(inputName);

            let inputCounter = o_utils.getSlugOrDataTrailingCounterStr(inputName);
            let idx = inputCounter ? parseInt(inputCounter)-1 : 0;
            let currentValue = $(this).val().trim();
            if (currentValue) {
                if (opus.selections[slug]) {
                    opus.selections[slug][idx] = currentValue;
                } else {
                    opus.selections[slug] = [currentValue];
                }
            } else {
                if (opus.selections[slug]) {
                    opus.selections[slug][idx] = null;
                } else {
                    opus.selections[slug] = [null];
                }
            }

            if (opus.lastSelections && opus.lastSelections[slug]) {
                if (opus.lastSelections[slug][idx] === $(this).val().trim()) {
                    return;
                }
            }

            // If there is an invalid value, and user still updates string input,
            // update the last selections to prevent allNormalizeInputApiCall.
            if (!opus.areRangeInputsValid()) {
                opus.updateOPUSLastSelectionsWithOPUSSelections();
            }
            o_hash.updateURLFromCurrentHash();
        });

        $("#search").on("change", "input.multichoice, input.singlechoice", function() {
            // mult widget gets changed
            let id = $(this).attr("id").split("_")[0];
            let value = $(this).attr("value");

            if ($(this).is(":checked")) {
                let values = [];
                if (opus.selections[id]) {
                    values = opus.selections[id]; // this param already has been constrained
                }

                // for surfacegeometry we only want a target selected
                if (id === "surfacegeometrytargetname") {
                    opus.selections[id] = [value];
                } else {
                    // add the new value to the array of values
                    values.push(value);
                    // add the array of values to selections
                    opus.selections[id] = values;
                }

                // special menu behavior for surface geo, slide in a loading indicator..
                if (id == "surfacetarget") {
                    let surface_loading = '<li style="margin-left:50%; display:none" class="spinner">&nbsp;</li>';
                    $(surface_loading).appendTo($("a.surfacetarget").parent()).slideDown("slow").delay(500);
                }

            } else {
                let remove = opus.selections[id].indexOf(value); // find index of value to remove
                opus.selections[id].splice(remove,1);        // remove value from array

                if (opus.selections[id].length === 0) {
                    delete opus.selections[id];
                }
            }

            // If there is an invalid value, and user still updates mult input,
            // update the last selections to prevent allNormalizeInputApiCall.
            if (!opus.areRangeInputsValid()) {
                opus.updateOPUSLastSelectionsWithOPUSSelections();
            }
            o_hash.updateURLFromCurrentHash();
        });

        // range behaviors and string behaviors for search widgets - qtype select dropdown
        $('#search').on("change", "select", function() {
            if ($(this).attr("name").startsWith("qtype-")) {
                console.log(`change event happend on qtype`);
                let qtypes = [];
                switch ($(this).attr("class")) {  // form type
                    case "RANGE":
                    let slugNoNum = ($(this).attr("name").match(/-(.*)_[0-9]{2}$/) ?
                    $(this).attr("name").match(/-(.*)_[0-9]{2}$/)[1] :
                    $(this).attr("name").match(/-(.*)$/)[1]);
                    $(`#widget__${slugNoNum} .widget-main select`).each(function() {
                        qtypes.push($(this).val());
                    });
                    opus.extras[`qtype-${slugNoNum}`] = qtypes;
                    break;

                    case "STRING":
                    let slug = ($(this).attr("name").match(/-(.*)_[0-9]{2}$/) ?
                    $(this).attr("name").match(/-(.*)_[0-9]{2}$/)[1] :
                    $(this).attr("name").match(/-(.*)$/)[1]);
                    $(`#widget__${slug} .widget-main select`).each(function() {
                        qtypes.push($(this).val());
                    });
                    opus.extras[`qtype-${slug}`] = qtypes;
                    break;
                }
            } else if ($(this).attr("name").startsWith("unit-")) {
                console.log(`change event happend on unit: ${$(this).val()}`);
                let units = [];
                let slugNoNum = $(this).attr("name").match(/unit-(.*)$/)[1];
                let numberOfInputSets = $(`#widget__${slugNoNum} .op-search-inputs-set`).length;
                while(units.length < numberOfInputSets) {
                    units.push($(this).val());
                }
                opus.extras[`unit-${slugNoNum}`] = units;
                console.log(JSON.stringify(opus.extras));
            }
            // If there is an invalid value, and user still updates qtype input,
            // update the last selections to prevent allNormalizeInputApiCall.
            if (!opus.areRangeInputsValid()) {
                opus.updateOPUSLastSelectionsWithOPUSSelections();
            }
            o_hash.updateURLFromCurrentHash();
        });
    },

    addPreprogrammedRangesSearchBehaviors: function() {
        /**
         * Add customized event handlers for preprogrammed ranges dropdown and expandable
         * list when user types/focus in & out of the input. This function will be called
         * in addSearchBehaviors.
         */

        // Make sure ranges info shows up automatically when the count of matched characters
        // is not 0. We do this in the event handler when the collapsing is done. This is to avoid
        // the race condition of the collapsing animation when user types fast in the input.
        $(`#search`).on("hidden.bs.collapse", ".op-scrollable-menu .container", function(e) {
            if (o_search.isTriggeredFromInput) {
                let collapsibleContainerId = $(e.target).attr("id");
                let inputName = $(e.target).attr("data-mininput");
                let slug = o_utils.getSlugOrDataWithoutCounter(inputName);
                let uniqueid = $(`input.op-range-input-min[name="${inputName}"]`).attr("data-uniqueid");
                let slugWithId = `${slug}_${uniqueid}`;
                let currentinputsRangesNameMatchedInfo = o_search.inputsRangesNameMatchedInfo[slugWithId] || {};
                if (currentinputsRangesNameMatchedInfo[collapsibleContainerId]) {
                    $(e.target).collapse("show");
                }
            }
        });

        // Make sure ranges info hides automatically when the count of matched characters
        // is 0. We do this in the event handler when the expanding is done. This is to avoid
        // the race condition of the expanding animation when user types fast in the input.
        $(`#search`).on("shown.bs.collapse", ".op-scrollable-menu .container", function(e) {
            if (o_search.isTriggeredFromInput) {
                let collapsibleContainerId = $(e.target).attr("id");
                let inputName = $(e.target).attr("data-mininput");
                let slug = o_utils.getSlugOrDataWithoutCounter(inputName);
                let uniqueid = $(`input.op-range-input-min[name="${inputName}"]`).attr("data-uniqueid");
                let slugWithId = `${slug}_${uniqueid}`;
                let currentinputsRangesNameMatchedInfo = o_search.inputsRangesNameMatchedInfo[slugWithId] || {};
                if (currentinputsRangesNameMatchedInfo[collapsibleContainerId] === 0) {
                    $(e.target).collapse("hide");
                }
            }
        });

        // When there is no matched characters of ranges names and the category is collapsed,
        // the empty category will not be expanded when user clicks it.
        $(`#search`).on("show.bs.collapse", ".op-scrollable-menu .container", function(e) {
            let collapsibleContainerId = $(e.target).attr("id");
            let inputName = $(e.target).attr("data-mininput");
            let widgetId = $(e.target).data("widget");
            let slug = o_utils.getSlugOrDataWithoutCounter(inputName);
            let uniqueid = $(`input.op-range-input-min[name="${inputName}"]`).attr("data-uniqueid");
            let slugWithId = `${slug}_${uniqueid}`;
            let currentinputsRangesNameMatchedInfo = o_search.inputsRangesNameMatchedInfo[slugWithId] || {};
            let currentIuputValue = $(`#${widgetId} input.op-range-input-min[name="${inputName}"]`).val().trim();
            if (currentinputsRangesNameMatchedInfo[collapsibleContainerId] === 0 && currentIuputValue) {
                e.preventDefault();
            }
        });

        // Set isTriggeredFromInput to false, this will make sure we can still expand/collapse
        // ranges info by mouse clicking.
        $(`#search`).on("click", ".op-scrollable-menu", function(e) {
            o_search.isTriggeredFromInput = false;
        });

        // Reset scrollbar to top if there is no matched ranges info when dropdown is open.
        $("#search").on("shown.bs.dropdown", function(e) {
            $(".op-scrollable-menu").scrollTop(0);
        });

        // Make sure dropdown is not shown if user focus into an input with numerical value or
        // string value with no match.
        $("#search").on("show.bs.dropdown", function(e) {
            let minInput = $(e.target).find("input.op-ranges-dropdown-menu");
            if (minInput.length === 0) {
                return;
            }
            let inputName = minInput.attr("name");
            let slug = o_utils.getSlugOrDataWithoutCounter(inputName);
            let uniqueid = minInput.attr("data-uniqueid");
            let slugWithId = `${slug}_${uniqueid}`;

            let currentValue = minInput.val().trim();
            o_search.rangesNameTotalMatchedCounter[slugWithId] = (o_search.rangesNameTotalMatchedCounter[slugWithId] ||
                                                                 0);
            if (o_search.rangesNameTotalMatchedCounter[slugWithId] === 0 && currentValue) {
                e.preventDefault();
            }
        });
    },

    compareInputWithRangesInfo: function(currentValue, targetInput) {
        /**
         * When user is typing, iterate through all preprogrammed ranges info.
         * 1. If input field is empty, display the whole list with all categories collapsed.
         * 2. If input matches any of list items, expand those categories. Highlight and display
         * matched items, and hide all unmatched items. Collpase and hide the empty categories.
         */
        o_search.isTriggeredFromInput = true;
        let slugName = $(targetInput).data("slugname");
        let inputName = $(targetInput).attr("name");
        let slug = o_utils.getSlugOrDataWithoutCounter(inputName);
        let uniqueid = $(targetInput).attr("data-uniqueid");
        let slugWithId = `${slug}_${uniqueid}`;
        // Need to be more specific to select the corresponding one
        let inputToTriggerDropdown = $(`#widget__${slugName} input.op-range-input-min[name="${inputName}"]`);
        let preprogrammedRangesDropdown = (inputToTriggerDropdown
                                           .next(".op-preprogrammed-ranges")
                                           .find(".op-scrollable-menu"));
        let preprogrammedRangesInfo = preprogrammedRangesDropdown.find("li");

        // If ranges info is not available, return from the function.
        if (preprogrammedRangesDropdown.length === 0 || !$(targetInput).hasClass("op-range-input-min")) {
            o_search.performInputValidation[slugWithId] = true;
            return;
        }
        // Reset matched info
        o_search.rangesNameMatchedCounterByCategory = {};
        for (const category of preprogrammedRangesInfo) {
            let collapsibleContainerId = $(category).attr("data-category");
            let rangesInfoInOneCategory = $(`#${collapsibleContainerId} .op-preprogrammed-ranges-data-item`);

            o_search.rangesNameMatchedCounterByCategory[collapsibleContainerId] = 0;

            for (const singleRangeData of rangesInfoInOneCategory) {
                let dataName = $(singleRangeData).data("name").toLowerCase();
                let currentInputValue = currentValue.toLowerCase();

                if (!currentValue) {
                    // $(`.op-scrollable-menu a.dropdown-item`).removeClass("op-hide-element");
                    preprogrammedRangesDropdown.find("a.dropdown-item").removeClass("op-hide-element");
                    $(singleRangeData).removeClass("op-hide-element");
                    o_search.removeHighlightedRangesName(singleRangeData);
                    for (const eachCat in o_search.rangesNameMatchedCounterByCategory) {
                        o_search.rangesNameMatchedCounterByCategory[eachCat] = 0;
                    }
                } else if (dataName.includes(currentInputValue)) {
                    // Expand the category, display the item and highlight the matched keyword.
                    $(`a.dropdown-item[href*="${collapsibleContainerId}"]`).removeClass("op-hide-element");
                    $(singleRangeData).removeClass("op-hide-element");
                    o_search.highlightMatchedRangesName(singleRangeData, currentInputValue);
                    o_search.rangesNameMatchedCounterByCategory[collapsibleContainerId] += 1;
                    if (!$(`#${collapsibleContainerId}`).hasClass("show")) {
                        $(`#${collapsibleContainerId}`).collapse("show");
                    }
                } else {
                    o_search.removeHighlightedRangesName(singleRangeData);
                    // Hide the item if it doesn't match the input keyword
                    $(singleRangeData).addClass("op-hide-element");
                }
            }

            if (o_search.rangesNameMatchedCounterByCategory[collapsibleContainerId] === 0) {
                $(`#${collapsibleContainerId}`).collapse("hide");
                if (currentValue) {
                    $(`a.dropdown-item[href*="${collapsibleContainerId}"]`).addClass("op-hide-element");
                }
            }
            o_search.setRangesDropdownScrollbarPos(preprogrammedRangesDropdown);
        }

        // If there is one or more matched ranges names, don't perform input validation.
        o_search.performInputValidation[slugWithId] = true;
        o_search.rangesNameTotalMatchedCounter[slugWithId] = 0;
        for (const eachCat in o_search.rangesNameMatchedCounterByCategory) {
            if (o_search.rangesNameMatchedCounterByCategory[eachCat] !== 0) {
                o_search.performInputValidation[slugWithId] = false;
                o_search.rangesNameTotalMatchedCounter[slugWithId] += o_search.rangesNameMatchedCounterByCategory[eachCat];
            }
        }
        o_search.inputsRangesNameMatchedInfo[slugWithId] = o_utils.deepCloneObj(o_search.rangesNameMatchedCounterByCategory);

        if (o_search.rangesNameTotalMatchedCounter[slugWithId] === 0 && currentValue) {
            if (preprogrammedRangesDropdown.hasClass("show")) {
                inputToTriggerDropdown.dropdown("toggle");
            }
        } else {
            if (!preprogrammedRangesDropdown.hasClass("show")) {
                inputToTriggerDropdown.dropdown("toggle");
            }
        }
    },

    highlightMatchedRangesName: function(singleRangeData, currentInputValue) {
        /**
         * Highlight characters of ranges names that match user's input.
         */
        let originalText = $(singleRangeData).data("name");
        let matchedIdx = originalText.toLowerCase().indexOf(currentInputValue);
        let matchedLength = currentInputValue.length;

        // We use "+" to concatenate strings instead of `` string interpolation because
        // we are going to put the highlightedText in html, and white spaces (or new line)
        // will break the format and give the highlighted letters extra spaces at both ends.
        let highlightedText = (originalText.slice(0, matchedIdx) + "<b>" +
                               originalText.slice(matchedIdx, matchedIdx + matchedLength) +
                               "</b>" + originalText.slice(matchedIdx + matchedLength));

        $(singleRangeData).find(".op-preprogrammed-ranges-data-name").html(highlightedText);
    },

    removeHighlightedRangesName: function(singleRangeData) {
        /**
         * Remove highlighted characters of ranges names that match user's input.
         */
        let originalText = $(singleRangeData).data("name");
        $(singleRangeData).find(".op-preprogrammed-ranges-data-name").html(originalText);
    },

    setRangesDropdownScrollbarPos: function(rangesDropdownElement) {
        /**
         * Set ranges info dropdown scrollbar position to make sure scrollbar scrolls
         * to the first matched category when there is a matched character.
         */
        for (let category in o_search.rangesNameMatchedCounterByCategory) {
            if (o_search.rangesNameMatchedCounterByCategory[category]) {
                let targetTopPosition = $(`li[data-category="${category}"]`).offset().top;
                let containerTopPosition = rangesDropdownElement.offset().top;
                let containerScrollbarPosition = rangesDropdownElement.scrollTop();
                let finalScrollbarPosition = targetTopPosition - containerTopPosition + containerScrollbarPosition;
                rangesDropdownElement.scrollTop(finalScrollbarPosition);
                return;
            }
        }
        // Set to top if there is no match.
        $(".op-scrollable-menu").scrollTop(0);
    },

    allNormalizeInputApiCall: function() {
        let newHash = o_hash.getHashStrFromSelections(opus.selections, true);

        opus.normalizeInputForAllFieldsInProgress[opus.allSlug] = true;
        o_search.lastSlugNormalizeRequestNo++;

        let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + o_search.lastSlugNormalizeRequestNo;
        return $.getJSON(url);
    },

    validateRangeInput: function(normalizedInputData, removeSpinner=false, slug=opus.allSlug) {
        /**
         * Validate the return data from a normalize input API call, and update hash & URL
         * based on the selections for the same normalize input API.
         */
        o_search.slugRangeInputValidValueFromLastSearch = {};

        $.each(normalizedInputData, function(eachSlug, value) {
            if (eachSlug === "reqno") {
                return;
            }
            opus.rangeInputFieldsValidation[eachSlug] = opus.rangeInputFieldsValidation[eachSlug] || true;
            // Beacsue normalize input api call is based on hash with unique id (for RANGE & STRING
            // inputs), so we have to parse the return data based on unique id.
            let slugNoCounter = o_utils.getSlugOrDataWithoutCounter(eachSlug);
            let uniqueid = o_utils.getSlugOrDataTrailingCounterStr(eachSlug);
            let currentInput = $(`input[name*="${slugNoCounter}"][data-uniqueid="${uniqueid}"]`);

            let inputName = currentInput.attr("name") || "";
            let inputCounter = o_utils.getSlugOrDataTrailingCounterStr(inputName);
            let idx = inputCounter ? parseInt(inputCounter)-1 : 0;

            if (currentInput.length === 0) {
                return; // continue to the next iteration;
            }

            if (value === null) {
                if (currentInput.hasClass("RANGE")) {
                    if (currentInput.hasClass("input_currently_focused")) {
                        $("#sidebar").addClass("search_overlay");
                    } else {
                        $("#sidebar").addClass("search_overlay");
                        currentInput.addClass("search_input_invalid_no_focus");
                        currentInput.removeClass("search_input_invalid");

                        opus.selections[slugNoCounter][idx] = currentInput.val();
                    }

                    opus.rangeInputFieldsValidation[eachSlug] = false;
                }
            } else {
                if (currentInput.hasClass("RANGE")) {
                    /*
                    If current focused input value is different from returned normalized data
                    we will not overwrite its displayed value.
                    */
                    if (currentInput.hasClass("input_currently_focused") && currentInput.val() !== value) {
                        o_search.slugRangeInputValidValueFromLastSearch[eachSlug] = value;
                    } else {
                        currentInput.val(value);
                        o_search.slugRangeInputValidValueFromLastSearch[eachSlug] = value;
                        if (value === "") {
                            value = null;
                        }
                        if (opus.selections[slugNoCounter]) {
                            opus.selections[slugNoCounter][idx] = value;
                        } else {
                            opus.selections[slugNoCounter] = [value];
                        }

                        // No color border if the input value is valid
                        o_search.clearInputBorder(currentInput);
                    }
                    opus.rangeInputFieldsValidation[eachSlug] = true;
                }
            }
        });

        if (opus.rangeInputFieldsValidation[slug] ||
            (slug === opus.allSlug && opus.areRangeInputsValid())) {

            // If there is an invalid value, and user still updates range input,
            // update the last selections to prevent allNormalizeInputApiCall.
            if (!opus.areRangeInputsValid()) {
                opus.updateOPUSLastSelectionsWithOPUSSelections();
            }
            o_hash.updateURLFromCurrentHash();
        } else {
            $("#op-result-count").text("?");
            // set hinting info to ? when any range input has invalid value
            // for range
            $(".op-range-hints").each(function() {
                if ($(this).children().length > 0) {
                    $(this).html(`<span>Min:&nbsp;<span class="op-hints-info">?</span></span>
                                  <span>Max:&nbsp;<span class="op-hints-info">?</span></span>
                                  <span>Nulls:&nbsp;<span class="op-hints-info">?</span></span>`);
                }
            });
            // for mults
            $(".hints").each(function() {
                $(this).html("<span>?</span>");
            });

            if (removeSpinner) {
                $(".spinner").fadeOut("");
            }
        }
    },

    parseFinalNormalizedInputDataAndUpdateURL: function(slug, url) {
        /**
         * Parse the return data from a normalize input API call. validateRangeInput
         * is called here.
         */
        $.getJSON(url, function(normalizedInputData) {
            // Make sure data is from the final normalize input call before parsing
            // normalizedInputData
            if (normalizedInputData.reqno < o_search.slugNormalizeReqno[slug]) {
                delete opus.normalizeInputForAllFieldsInProgress[slug];
                return;
            }
            // check each range input, if it's not valid, change its background to red
            // and also remove spinner.
            o_search.validateRangeInput(normalizedInputData, true, slug);

            // When search is invalid, we disabled browse tab in nav link.
            if (!opus.areRangeInputsValid()) {
                $(".op-browse-tab").addClass("op-disabled-nav-link");
                delete opus.normalizeInputForAllFieldsInProgress[slug];
                return;
            }

            o_search.rangesNameTotalMatchedCounter[slug] = 0;
            if (o_utils.areObjectsEqual(opus.selections, opus.lastSelections))  {
                // Put back normal hinting info
                opus.widgetsDrawn.forEach(function(eachSlug) {
                    o_search.getHinting(eachSlug);
                });
                $("#op-result-count").text(o_utils.addCommas(o_browse.totalObsCount));
            }
            $("input.RANGE").each(function() {
                if (!$(this).hasClass("input_currently_focused")) {
                    $(this).removeClass("search_input_valid");
                    $(this).removeClass("search_input_invalid");
                    $(this).addClass("search_input_original");
                }
            });

            $(".op-browse-tab").removeClass("op-disabled-nav-link");
            $("#sidebar").removeClass("search_overlay");
            delete opus.normalizeInputForAllFieldsInProgress[slug];
        });
    },

    extractHtmlContent: function(htmlString) {
        let domParser = new DOMParser();
        let content = domParser.parseFromString(htmlString, "text/html").documentElement.textContent;
        return content;
    },

    searchBarContainerHeight: function() {
        let mainNavHeight = $("#op-main-nav").outerHeight();
        let footerHeight = $(".app-footer").outerHeight();
        let resetButtonHeight = $(".op-reset-button").outerHeight();
        let dividerHeight = $(".shadow-divider").outerHeight();
        let offset = mainNavHeight + footerHeight + resetButtonHeight + dividerHeight;
        return $("#search").height() - offset;
    },

    searchHeightChanged: function() {
        o_search.searchSideBarHeightChanged();
        o_search.searchWidgetHeightChanged();
    },

    searchSideBarHeightChanged: function() {
        let containerHeight = o_search.searchBarContainerHeight();
        let searchMenuHeight = $(".op-search-menu").height();
        $("#search .sidebar_wrapper").height(containerHeight);

        if (containerHeight > searchMenuHeight) {
            $("#sidebar-container .ps__rail-y").addClass("hide_ps__rail-y");
            o_search.searchScrollbar.settings.suppressScrollY = true;
        } else {
            $("#sidebar-container .ps__rail-y").removeClass("hide_ps__rail-y");
            o_search.searchScrollbar.settings.suppressScrollY = false;
        }

        o_search.searchScrollbar.update();
    },

    searchWidgetHeightChanged: function() {
        let footerHeight = $(".app-footer").outerHeight();
        let mainNavHeight = $("#op-main-nav").outerHeight();
        let totalNonSearchAreaHeight = footerHeight + mainNavHeight;
        let containerHeight = $("#search").height() - totalNonSearchAreaHeight;
        let searchWidgetHeight = $("#op-search-widgets").height();
        $(".op-widget-column").height(containerHeight);

        if (containerHeight > searchWidgetHeight) {
            $("#widget-container .ps__rail-y").addClass("hide_ps__rail-y");
            o_search.widgetScrollbar.settings.suppressScrollY = true;
        } else {
            $("#widget-container .ps__rail-y").removeClass("hide_ps__rail-y");
            o_search.widgetScrollbar.settings.suppressScrollY = false;
        }

        o_search.widgetScrollbar.update();
    },

    activateSearchTab: function() {

        if (o_search.searchTabDrawn) {
            return;
        }

        // get any prefs from cookies
        if (!opus.prefs.widgets.length && $.cookie("widgets")) {
            opus.prefs.widgets = $.cookie("widgets").split(',');
        }
        // get menu
        o_menu.getNewSearchMenu();

        // find and place the widgets
        if (!opus.prefs.widgets.length) {
            // no widgets defined, get the default widgets
            opus.prefs.widgets = ["planet","target"];
            o_widgets.placeWidgetContainers();
            o_widgets.getWidget("planet","#op-search-widgets");
            o_widgets.getWidget("target","#op-search-widgets");
        } else {
            if (!opus.widgetElementsDrawn.length) {
                o_widgets.placeWidgetContainers();
            }
        }

        o_widgets.updateWidgetCookies();

        $.each(opus.prefs.widgets, function(key, slug) {
            if ($.inArray(slug, opus.widgetsDrawn) < 0) {  // only draw if not already drawn
                o_widgets.getWidget(slug,"#op-search-widgets");
            }
        });

        o_search.searchTabDrawn = true;
    },

    getHinting: function(slug) {

        if ($(".widget__" + slug).hasClass("range-widget")) {
            // this is a range field
            o_search.getRangeEndpoints(slug);

        } else if ($(".widget__" + slug).hasClass("mult-widget")) {
            // this is a mult field
            o_search.getValidMults(slug);
        } else {
          $(`#widget__${slug} .spinner`).fadeOut();
        }
    },

    getRangeEndpoints: function(slug) {

        $(`#widget__${slug} .spinner`).fadeIn();

        let units = "";
        if ($(`#widget__${slug} .unit-${slug}`).length) {
            let unitsVal = $(`#widget__${slug} .unit-${slug}`).val();
            units = `&units=${unitsVal}`;
        }
        o_search.lastEndpointsRequestNo++;
        o_search.slugEndpointsReqno[slug] = o_search.lastEndpointsRequestNo;
        let url = `/opus/__api/meta/range/endpoints/${slug}.json?${o_hash.getHash()}${units}` +
                  `&reqno=${o_search.slugEndpointsReqno[slug]}`;
        console.log(url);
        $.ajax({url: url,
            dataType:"json",
            success: function(multdata) {
                console.log(`successfully update hints`);
                $(`#widget__${slug} .spinner`).fadeOut();

                if (multdata.reqno< o_search.slugEndpointsReqno[slug]) {
                    return;
                }
                $('#hint__' + slug).html(`<span>Min:&nbsp;<span class="op-hints-info">${multdata.min}</span></span>
                                          <span>Max:&nbsp;<span class="op-hints-info">${multdata.max}</span></span>
                                          <span>Nulls:&nbsp;<span class="op-hints-info">${multdata.nulls}</span></span>`);
            },
            statusCode: {
                404: function() {
                    $(`#widget__${slug} .spinner`).fadeOut();
                }
            },
            error:function(xhr, ajaxOptions, thrownError) {
                $(`#widget__${slug} .spinner`).fadeOut();
                // range input hints are "?" when wrong values of url is pasted
                $(`#hint__${slug}`).html(`<span>Min:&nbsp;<span class="op-hints-info">?</span></span>
                                          <span>Max:&nbsp;<span class="op-hints-info">?</span></span>
                                          <span>Nulls:&nbsp;<span class="op-hints-info">?</span></span>`);
            }
        }); // end mults ajax
    },

    getValidMults: function(slug) {
        // turn on spinner
        $(`#widget__${slug} .spinner`).fadeIn();

        o_search.lastMultsRequestNo++;
        o_search.slugMultsReqno[slug] = o_search.lastMultsRequestNo;
        let url = `/opus/__api/meta/mults/${slug}.json?${o_hash.getHash()}&reqno=${o_search.slugMultsReqno[slug]}`;
        $.ajax({url: url,
            dataType:"json",
            success: function(multdata) {
                if (multdata.reqno < o_search.slugMultsReqno[slug]) {
                    return;
                }

                let dataSlug = multdata.field;
                $("#widget__" + dataSlug + " .spinner").fadeOut('');

                let widget = "widget__" + dataSlug;
                let mults = multdata.mults;
                $('#' + widget + ' input').each( function() {
                    let value = $(this).attr("value");
                    let id = '#hint__' + slug + "_" + value.replace(/ /g,'-').replace(/[^\w\s]/gi, '');  // id of hinting span, defined in widgets.js getWidget

                    if (mults[value]) {
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
                  $(`#widget__${slug} .spinner`).fadeOut();
              }
            },
            error:function(xhr, ajaxOptions, thrownError) {
                $(`#widget__${slug} .spinner`).fadeOut();
                // checkbox hints are "?" when wrong values of url is pasted
                $(".hints").each(function() {
                    $(this).html("<span>?</span>");
                });
            }
        }); // end mults ajax

    },

    clearInputBorder: function(inputSet) {
        /**
         * clear the border of an input, remove any invalid border of an input.
         */
        let input = inputSet.find("input");
        input.addClass("search_input_original");
        input.removeClass("search_input_invalid_no_focus");
        input.removeClass("search_input_invalid");
        input.removeClass("search_input_valid");
    },
};
