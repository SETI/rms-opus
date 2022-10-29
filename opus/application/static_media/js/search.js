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
    lastAllNormalizeRequestNo: 0,
    lastMultsRequestNo: 0,
    lastEndpointsRequestNo: 0,

    slugStringSearchChoicesReqno: {},
    slugNormalizeReqno: {},
    slugMultsReqno: {},
    slugEndpointsReqno: {},
    slugInputValidValueFromLastSearch: {},

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
        // Manually focus in the input field if it's not focused after the 1st click.
        // This is to fix the issue that the input field will not be focused after
        // the 1st click in iOS.
        $("#search").on("click", "input[type='text']", function(e) {
            if (!$(this).is(":focus")) {
                $(this).focus();
            }
        });

        // Avoid the orange blinking on border color, and also display proper border when input is in focus
        $("#search").on("focus", "input.RANGE, input.STRING", function(e) {
            let inputName = $(this).attr("name");
            let currentValue = $(this).val().trim();
            let slug = o_utils.getSlugOrDataWithoutCounter(inputName);
            let uniqueid = $(this).attr("data-uniqueid");
            let slugWithId = `${slug}_${uniqueid}`;

            o_search.performInputValidation[slugWithId] = (o_search.performInputValidation[slugWithId] ||
                                                           true);
            if (o_search.slugInputValidValueFromLastSearch[slugWithId] ||
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
                !preprogrammedRangesDropdown.hasClass("show") && !o_widgets.isReFocusingBackToInput) {
                o_widgets.isKeepingRangesDropdownOpen = true;
                $(this).dropdown("toggle");
            }
        });

        // When clicking inside a widget body, if the clicked element is not input,
        // select, hints, text nodes, add input "+" icon, and remove input trash icon,
        // we will disable the default behavior of mousedown event. This will prevent
        // input from focusing out when clicking on preprogrammed ranges dropdown, and
        // also keep the ability to copy text & hints in mults and hints in ranges
        // widgets. This will also make sure input focus out to trigger a change event
        // when clicking any add/remove input icon.
        $("#search").on("mousedown", ".widget .card-body", function(e) {
            if (!$(e.target).is("input") && !$(e.target).is("select") &&
                !$(e.target).is("label") && !$(e.target).hasClass("hints") &&
                !$(e.target).hasClass("op-hints-info") &&
                !$(e.target).hasClass("op-hints-description") &&
                !$(e.target).hasClass("op-choice-label-name") &&
                !$(e.target).hasClass("op-remove-inputs-btn") &&
                !$(e.target).hasClass("op-add-inputs-btn") &&
                !$(e.target).parent(".op-remove-inputs-btn").length &&
                !$(e.target).parent(".op-add-inputs-btn").length) {
                e.preventDefault();
            }
        });

        /*
        This is to properly put back invalid search background
        when user focus out and there is no "change" event
        */
        $("#search").on("focusout", "input.RANGE, input.STRING", function(e) {
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
        $("#search").on("input", "input.RANGE, input.STRING", function(e) {
            if (!$(this).hasClass("input_currently_focused")) {
                $(this).addClass("input_currently_focused");
            }

            let inputName = $(this).attr("name");
            let slugName = $(this).data("slugname");
            let slugWithoutCounter = o_utils.getSlugOrDataWithoutCounter(inputName);
            let uniqueid = $(this).attr("data-uniqueid");
            let slugWithId = `${slugWithoutCounter}_${uniqueid}`;
            let qtypeSlugWithId = `qtype-${slugName}_${uniqueid}`;
            let unitSlugWithId = `unit-${slugName}_${uniqueid}`;

            let currentValue = $(this).val().trim();
            // Check if there is any match between input values and ranges names
            o_search.compareInputWithRangesInfo(currentValue, e.target);
            o_search.lastSlugNormalizeRequestNo++;
            o_search.slugNormalizeReqno[slugWithId] = o_search.lastSlugNormalizeRequestNo;

            // Call normalized api with the current focused input slug
            let encodedValue = o_hash.encodeSlugValue(currentValue);
            let newHash = `${slugWithId}=${encodedValue}`;
            // If qtype input exists, we pass in qtype with id to normalize input api
            // so that we can properly validate string regex.
            if ($(`#widget__${slugName} [name="qtype-${inputName}"]`).length > 0) {
                let currentQtypeVal = $(`#widget__${slugName} [name="qtype-${inputName}"]`).val();
                newHash += `&${qtypeSlugWithId}=${currentQtypeVal}`;
            }
            // If unit input exists, we pass in unit with id to normalize input api
            // to get the pretty value based on current value and unit.
            if ($(`#widget__${slugName} .op-unit-${slugName}`).length > 0) {
                let currentUnitVal = $(`#widget__${slugName} .op-unit-${slugName}`).val();
                newHash += `&${unitSlugWithId}=${currentUnitVal}`;
            }

            opus.normalizeInputForCharInProgress[slugWithId] = true;
            let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + o_search.slugNormalizeReqno[slugWithId];
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
                    $(e.target).removeClass("search_input_invalid_no_focus");
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
            Handle any preprogrammed range dropdown
            Call final normalizeinput and validate all inputs
            Update URL (and search) if all inputs are valid
        */
        $("#search").on("change", "input.RANGE", function(e) {
            let inputName = $(this).attr("name");
            let slugName = $(this).data("slugname");
            let slug = o_utils.getSlugOrDataWithoutCounter(inputName);
            let uniqueid = $(this).attr("data-uniqueid");
            let slugWithId = `${slug}_${uniqueid}`;

            // Handle preprogrammed ranges
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
                let allItemsInMatchedCat = ($(`${matchedCatId} .op-preprogrammed-ranges-data-item`)
                                            .not(".op-hide-different-units-info"));
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

            o_search.stringOrRangeChanged(e.target);
        });

        /*
        When user focusout or hit enter on any string input:
            Call final normalizeinput and validate all inputs
            Update URL (and search) if all inputs are valid
        */
        $("#search").on("change", "input.STRING", function(e) {
            o_search.stringOrRangeChanged(e.target);
        });

        /*
        When user changes any STRING qtype:
            Handle any preprogrammed range dropdown
            Call final normalizeinput and validate all inputs
            Update URL (and search) if all inputs are valid
        We do this because the validity of a regex is different from that of
        any other qtype.
        */
        $("#search").on("change", ".op-qtype-input .STRING", function(e) {
            let inputName = $(this).attr("name").replace("qtype-", "");
            let target = $(`#search input.STRING[name="${inputName}"]`);

            o_search.stringOrRangeChanged(target);
        });

        $("#search").on("change", "input.multichoice, input.singlechoice", function() {
            // mult widget gets changed
            let id = $(this).attr("id").split("_")[0];
            let value = $(this).attr("value");
            let newTargetSlug = $(this).attr("data-slug");
            opus.oldSurfacegeoTarget = opus.oldSurfacegeoTarget || newTargetSlug;

            if ($(this).hasClass("multichoice")) {
                o_search.addCheckMarkForCategories(id);
            }

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
                    opus.selections[id] = [values.join(",")];
                }

                // special menu behavior for surface geo, slide in a loading indicator..
                if (id == "surfacetarget") {
                    let surface_loading = '<li style="margin-left:50%; display:none" class="spinner">&nbsp;</li>';
                    $(surface_loading).appendTo($("a.surfacetarget").parent()).slideDown("slow").delay(500);
                }

            } else {
                let currentVals = opus.selections[id] ? opus.selections[id][0] : "";
                currentVals = currentVals ? currentVals.split(",") : [];

                let remove = currentVals.indexOf(value); // find index of value to remove
                currentVals.splice(remove,1);
                opus.selections[id] = [currentVals.join(",")];

                if (currentVals.length === 0) {
                    delete opus.selections[id];
                }
            }

            // If there is an invalid value, and user still updates mult input,
            // update the last selections to prevent allNormalizeInputApiCall.
            if (!opus.areInputsValid()) {
                opus.updateOPUSLastSelectionsWithOPUSSelections();
            }

            // User may have changed input, so trigger search with delay
            o_hash.updateURLFromCurrentHash(true, true);
        });

        // range behaviors and string behaviors for search widgets - qtype and unit
        // select dropdowns
        $('#search').on("change", "select", function() {
            let areInputSetsEmpty = true;
            // Use this flag to determine if a normalize input api with sourceunit is called.
            // If so, we don't need to perform an extra updateURLFromCurrentHash.
            let performNormalizeInput = false;
            if ($(this).attr("name").startsWith("qtype-")) {
                let qtypes = [];
                let counterStr = o_utils.getSlugOrDataTrailingCounterStr($(this).attr("name"));
                let idx = counterStr ? counterStr - 1 : 0;
                switch ($(this).attr("class")) {  // form type
                    case "RANGE":
                        let slugNoNum = ($(this).attr("name").match(/-(.*)_[0-9]{2}$/) ?
                                         $(this).attr("name").match(/-(.*)_[0-9]{2}$/)[1] :
                                         $(this).attr("name").match(/-(.*)$/)[1]);
                        $(`#widget__${slugNoNum} .op-widget-main select`).each(function() {
                            qtypes.push($(this).val());
                        });
                        opus.extras[`qtype-${slugNoNum}`] = qtypes;

                        // Check if corresponding selections are empty to determine if we
                        // should perform a search.
                        if (opus.selections[`${slugNoNum}1`][idx] ||
                            opus.selections[`${slugNoNum}2`][idx]) {
                            areInputSetsEmpty = false;
                        }
                        break;

                    case "STRING":
                        let slug = ($(this).attr("name").match(/-(.*)_[0-9]{2}$/) ?
                                    $(this).attr("name").match(/-(.*)_[0-9]{2}$/)[1] :
                                    $(this).attr("name").match(/-(.*)$/)[1]);
                        $(`#widget__${slug} .op-widget-main select`).each(function() {
                            qtypes.push($(this).val());
                        });
                        opus.extras[`qtype-${slug}`] = qtypes;

                        // Check if corresponding selections are empty to determine if we
                        // should perform a search.
                        if (opus.selections[`${slug}`][idx]) {
                            areInputSetsEmpty = false;
                        }
                        break;
                }
            } else if ($(this).attr("name").startsWith("unit-")) {
                let units = [];
                let slugNoNum = $(this).attr("name").match(/unit-(.*)$/)[1];
                let numberOfInputSets = $(`#widget__${slugNoNum} .op-search-inputs-set`).length;
                while (units.length < numberOfInputSets) {
                    units.push($(this).val());
                }
                opus.extras[`unit-${slugNoNum}`] = units;

                let inputs = $(`#widget__${slugNoNum} .op-search-inputs-set input`);
                // Check if all selections and actual input values are empty to determine
                // if we should perform a search.
                if (inputs.hasClass("RANGE")) {
                    areInputSetsEmpty = o_search.areSlugSelectionsEmpty(opus.selections[`${slugNoNum}1`],
                                                                        areInputSetsEmpty);
                    areInputSetsEmpty = o_search.areSlugSelectionsEmpty(opus.selections[`${slugNoNum}2`],
                                                                        areInputSetsEmpty);
                    areInputSetsEmpty = o_search.areAllInputsValInAWidgetEmpty(inputs, areInputSetsEmpty);
                } else if (inputs.hasClass("STRING")) {
                    areInputSetsEmpty = o_search.areSlugSelectionsEmpty(opus.selections[`${slugNoNum}`],
                                                                        areInputSetsEmpty);
                    areInputSetsEmpty = o_search.areAllInputsValInAWidgetEmpty(inputs, areInputSetsEmpty);
                }

                // Update values in preprogrammed ranges
                let newUnitVal = $(this).val();
                ($(`#widget__${slugNoNum} .op-preprogrammed-ranges-data-item`)
                 .not(`[data-unit="${newUnitVal}"]`).addClass("op-hide-different-units-info"));
                ($(`#widget__${slugNoNum} .op-preprogrammed-ranges-data-item[data-unit="${newUnitVal}"]`)
                 .removeClass("op-hide-different-units-info"));

                // When input is not empty and there is a unit change, run normalize input api with
                // sourceunit-slug (value: previous selected unit) on all inputs in the same widget.
                // The api return values will be properly converted based on newly selected unit,
                // and we will update all inputs with converted return values.
                let previousUnit = opus.currentUnitBySlug[slugNoNum];

                if (!areInputSetsEmpty) {
                    let slug1 = `${slugNoNum}1`;
                    let slug2 = `${slugNoNum}2`;
                    let qtypeSlug = `qtype-${slugNoNum}`;
                    let unitSlug = `unit-${slugNoNum}`;
                    let sourceunitSlug = `sourceunit-${slugNoNum}`;
                    let inputSets = $(`#widget__${slugNoNum} .op-search-inputs-set`);
                    let hash = [];

                    $.each(inputSets, function(idx, eachInputSet) {
                        let uniqueid = $(eachInputSet).find("input").attr("data-uniqueid");
                        let slug1WithId = `${slug1}_${uniqueid}`;
                        let slug2WithId = `${slug2}_${uniqueid}`;
                        let qtypeWithId =`${qtypeSlug}_${uniqueid}`;
                        let unitWithId = `${unitSlug}_${uniqueid}`;
                        let sourceunitWithId = `${sourceunitSlug}_${uniqueid}`;

                        // Always reevaluate these values even if they're currently marked as
                        // invalid. It's possible with the new units they will no longer be invalid.
                        let minInputVal = $(eachInputSet).find(".op-range-input-min").val();
                        if (minInputVal) {
                            let slug1EncodedSelections = o_hash.encodeSlugValues([minInputVal]);
                            hash.push(slug1WithId + "=" + slug1EncodedSelections[0]);
                        }
                        let maxInputVal = $(eachInputSet).find(".op-range-input-max").val();
                        if (maxInputVal) {
                            let slug2EncodedSelections = o_hash.encodeSlugValues([maxInputVal]);
                            hash.push(slug2WithId + "=" + slug2EncodedSelections[0]);
                        }

                        if (qtypeSlug in opus.extras) {
                            let encodedQtypeValues = o_hash.encodeSlugValues(opus.extras[qtypeSlug]);
                            if (opus.extras[qtypeSlug][idx] !== null) {
                                hash.push(qtypeWithId + "=" + encodedQtypeValues[idx]);
                            }
                        }
                        if (unitSlug in opus.extras) {
                            let encodedUnitValues = o_hash.encodeSlugValues(opus.extras[unitSlug]);
                            if (opus.extras[unitSlug][idx] !== null) {
                                hash.push(unitWithId + "=" + encodedUnitValues[idx]);
                                hash.push(sourceunitWithId + "=" + previousUnit);
                            }
                        }
                    });
                    let newHash = hash.join("&");

                    o_search.lastSlugNormalizeRequestNo++;
                    o_search.lastAllNormalizeRequestNo = o_search.lastSlugNormalizeRequestNo;
                    o_search.slugNormalizeReqno[unitSlug] = o_search.lastSlugNormalizeRequestNo;

                    opus.normalizeInputForAllFieldsInProgress[unitSlug] = true;
                    let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + o_search.slugNormalizeReqno[unitSlug];
                    performNormalizeInput = true;
                    o_search.parseFinalNormalizedInputDataAndUpdateURL(unitSlug, url, newUnitVal);
                } else {
                    // if normalize input api is not run, we update the record here.
                    opus.currentUnitBySlug[slugNoNum] = newUnitVal;
                }
            }

            // If there is an invalid value or all input sets are empty, and user still
            // updates qtype/unit input, update the last selections to prevent allNormalizeInputApiCall.
            // Note: this block will not be executed if performNormalizeInput is true, because all the
            // steps in the block will be performed in parseFinalNormalizedInputDataAndUpdateURL when
            // normalize input is run.
            if (!performNormalizeInput) {
                if (!opus.areInputsValid() || areInputSetsEmpty) {
                    opus.updateOPUSLastSelectionsWithOPUSSelections();
                }
                // User may have changed input, so trigger search with delay
                o_hash.updateURLFromCurrentHash(true, true);
            }

            // If no search is performed, we still update the hints for a unit change.
            if (areInputSetsEmpty) {
                if ($(this).attr("name").startsWith("unit-")) {
                    let slugNoNum = $(this).attr("name").match(/unit-(.*)$/)[1];
                    o_search.getHinting(slugNoNum);
                }
            }
        });
    },

    addCheckMarkForCategories: function(slug) {
        let categories = $(`#widget__${slug} .mult_group`);
        // Check each checkboxes under each category. If a category
        // has any checked checkbox, add a check mark next to the
        // category name
        for (let cat of categories) {
            let isChecked = false;
            let checkboxes = $(cat).find("input.multichoice");
            for (let checkbox of checkboxes) {
                isChecked = $(checkbox).is(":checked");
                if (isChecked) break;
            }

            let groupName = $(cat).data("group");
            let parentCatClassName = `mult_group_${groupName}`;
            let checkMarkClassName = `${parentCatClassName}_checked`;

            // Add the check mark right next to the category if any checkbox inside the
            // category is checked && check mark doesn't exist
            if (isChecked && $(`.mult_group_${groupName} .${checkMarkClassName}`).length === 0) {
                let checkMark = `<span class="${checkMarkClassName} op-checked-indication">` +
                                "<i class='fa fa-check'></i></span>";
                $(`.${parentCatClassName}`).append(checkMark);
            } else if (!isChecked) {
                // Remove the check mark if none of checkboxes under that category is checked.
                $(`.${checkMarkClassName}`).remove();
            }
        }
    },

    stringOrRangeChanged: function(target) {
        let inputName = $(target).attr("name").replace("qtype-", "");
        let slugName = $(target).data("slugname");
        let slug = o_utils.getSlugOrDataWithoutCounter(inputName);
        let uniqueid = $(target).attr("data-uniqueid");
        let slugWithId = `${slug}_${uniqueid}`;
        let currentValue = $(target).val().trim();
        let qtypeSlugWithId = `qtype-${slugName}_${uniqueid}`;
        let unitSlugWithId = `unit-${slugName}_${uniqueid}`;
        // Call normalize input api with only the slug and value from current input.
        let encodedValue = o_hash.encodeSlugValue(currentValue);
        let newHash = `${slugWithId}=${encodedValue}`;
        // If qtype input exists, we pass in qtype with id to normalize input api
        // so that we can properly validate string regex.
        if ($(`#widget__${slugName} [name="qtype-${inputName}"]`).length > 0) {
            let currentQtypeVal = $(`#widget__${slugName} [name="qtype-${inputName}"]`).val();
            newHash += `&${qtypeSlugWithId}=${currentQtypeVal}`;
        }
        // If unit input exists, we pass in unit with id to normalize input api
        // to get the pretty value based on current value and unit.
        if ($(`#widget__${slugName} .op-unit-${slugName}`).length > 0) {
            let currentUnitVal = $(`#widget__${slugName} .op-unit-${slugName}`).val();
            newHash += `&${unitSlugWithId}=${currentUnitVal}`;
        }

        o_search.lastSlugNormalizeRequestNo++;
        o_search.lastAllNormalizeRequestNo = o_search.lastSlugNormalizeRequestNo;
        o_search.slugNormalizeReqno[slugWithId] = o_search.lastSlugNormalizeRequestNo;

        opus.normalizeInputForAllFieldsInProgress[slugWithId] = true;
        let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + o_search.slugNormalizeReqno[slugWithId];

        if ($(target).hasClass("input_currently_focused")) {
            $(target).removeClass("input_currently_focused");
        }

        o_search.parseFinalNormalizedInputDataAndUpdateURL(slugWithId, url);
    },

    areSlugSelectionsEmpty: function(slugSelections, areInputSetsEmpty) {
        /**
         * Check if slugSelections is an array of null to determine if all
         * input sets are empty. Update & return areInputSetsEmpty.
         */
        if (slugSelections && areInputSetsEmpty) {
            for (const val of slugSelections) {
                if (val) {
                    areInputSetsEmpty = false;
                    break;
                }
            }
        }
        return areInputSetsEmpty;
    },

    areAllSURFACEGEOSelectionsEmpty: function() {
        let areInputSetsEmpty = true;
        for (const slug in opus.selections) {
            if (slug.startsWith("SURFACEGEO")) {
                areInputSetsEmpty = o_search.areSlugSelectionsEmpty(opus.selections[slug], areInputSetsEmpty);
                if (!areInputSetsEmpty) {
                    break;
                }
            }
        }

        return areInputSetsEmpty;
    },

    areAllInputsValInAWidgetEmpty: function(inputs, areInputSetsEmpty) {
        /**
         * Check if all inputs value are empty. Iterate through all inputs
         * in a widget and check value of each input. Update & return
         * areInputSetsEmpty.
         */
        if (inputs.length === 0) {
            return areInputSetsEmpty;
        }
        if (areInputSetsEmpty) {
            for (const eachInput of inputs) {
                if ($(eachInput).val()) {
                    areInputSetsEmpty = false;
                    break;
                }
            }
        }
        return areInputSetsEmpty;
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
            let rangesInfoInOneCategory = ($(`#${collapsibleContainerId} .op-preprogrammed-ranges-data-item`)
                                           .not(".op-hide-different-units-info"));

            o_search.rangesNameMatchedCounterByCategory[collapsibleContainerId] = 0;

            for (const singleRangeData of rangesInfoInOneCategory) {
                let dataName = $(singleRangeData).data("name").toLowerCase();
                let currentInputValue = currentValue.toLowerCase();

                if (!currentValue) {
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
                        // Normally inputsRangesNameMatchedInfo gets updated later in this function,
                        // but since we are opening the collapsible item here, to make sure all behaviors
                        // in addPreprogrammedRangesSearchBehaviors are correct, we have to update
                        // inputsRangesNameMatchedInfo here.
                        o_search.inputsRangesNameMatchedInfo[slugWithId] = o_utils.deepCloneObj(o_search.rangesNameMatchedCounterByCategory);
                        $(`#${collapsibleContainerId}`).collapse("show");
                    }
                } else {
                    o_search.removeHighlightedRangesName(singleRangeData);
                    // Hide the item if it doesn't match the input keyword
                    $(singleRangeData).addClass("op-hide-element");
                }
            }

            if (o_search.rangesNameMatchedCounterByCategory[collapsibleContainerId] === 0) {
                // Normally inputsRangesNameMatchedInfo gets updated later in this function,
                // but since we are hiding the collapsible item here, to make sure all behaviors
                // in addPreprogrammedRangesSearchBehaviors are correct, we have to update
                // inputsRangesNameMatchedInfo here.
                o_search.inputsRangesNameMatchedInfo[slugWithId] = o_utils.deepCloneObj(o_search.rangesNameMatchedCounterByCategory);
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
        let newHash = o_hash.getHashStrFromSelections(true);

        opus.normalizeInputForAllFieldsInProgress[opus.allSlug] = true;
        o_search.lastSlugNormalizeRequestNo++;
        o_search.lastAllNormalizeRequestNo = o_search.lastSlugNormalizeRequestNo;

        let url = "/opus/__api/normalizeinput.json?" + newHash + "&reqno=" + o_search.lastSlugNormalizeRequestNo;
        return $.getJSON(url);
    },

    validateInput: function(normalizedInputData, removeSpinner=false, slug=opus.allSlug, unit=null) {
        /**
         * Validate the return data from a normalize input API call, and update hash & URL
         * based on the selections for the same normalize input API.
         */
        o_search.slugInputValidValueFromLastSearch = {};
        $.each(normalizedInputData, function(eachSlug, value) {
            if (eachSlug === "reqno") {
                return;
            }
            opus.inputFieldsValidation[eachSlug] = opus.inputFieldsValidation[eachSlug] || true;
            // Because normalize input api call is based on hash with unique id (for RANGE & STRING
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
                if (currentInput.hasClass("RANGE") || currentInput.hasClass("STRING")) {
                    if (currentInput.hasClass("input_currently_focused")) {
                        $("#sidebar").addClass("search_overlay");
                    } else {
                        $("#sidebar").addClass("search_overlay");
                        currentInput.addClass("search_input_invalid_no_focus");
                        currentInput.removeClass("search_input_invalid");

                        opus.selections[slugNoCounter][idx] = currentInput.val();
                    }

                    opus.inputFieldsValidation[eachSlug] = false;
                }
            } else {
                if (currentInput.hasClass("RANGE") || currentInput.hasClass("STRING")) {
                    /*
                    If current focused input value is different from returned normalized data
                    we will not overwrite its displayed value.
                    */
                    if (currentInput.hasClass("input_currently_focused") && currentInput.val() !== value) {
                        o_search.slugInputValidValueFromLastSearch[eachSlug] = value;
                    } else {
                        currentInput.val(value);
                        o_search.slugInputValidValueFromLastSearch[eachSlug] = value;
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
                    opus.inputFieldsValidation[eachSlug] = true;
                }
            }
        });

        // Update newly selected unit to currentUnitBySlug
        if (slug.startsWith("unit-") && unit) {
            let slugNoNum = slug.match(/unit-(.*)$/)[1];
            opus.currentUnitBySlug[slugNoNum] = unit;
        }

        if (opus.inputFieldsValidation[slug] ||
            (slug === opus.allSlug && opus.areInputsValid()) || slug.startsWith("unit-")) {
            // If there is an invalid value, and user still updates input,
            // update the last selections to prevent allNormalizeInputApiCall.
            if (!opus.areInputsValid()) {
                opus.updateOPUSLastSelectionsWithOPUSSelections();
            }
            // User may have changed input, so trigger search with delay
            o_hash.updateURLFromCurrentHash(true, true);
        } else {
            $("#op-result-count").text("?");
            // set hinting info to ? when any range input has invalid value
            // for range
            let rangeHintsDescription = "op-hints-description";
            let rangeHintsTextClass = "op-hints-info";
            $(".op-range-hints").each(function() {
                if ($(this).children().length > 0) {
                    $(this).html(`<span><span class="${rangeHintsDescription}">Min:&nbsp;</span>
                                  <span class="${rangeHintsTextClass}">?</span></span>
                                  <span><span class="${rangeHintsDescription}">Max:&nbsp;</span>
                                  <span class="${rangeHintsTextClass}">?</span></span>
                                  <span><span class="${rangeHintsDescription}">N/A:&nbsp;</span>
                                  <span class="${rangeHintsTextClass}">?</span></span>`);
                }
            });
            // for mults
            $(".hints").each(function() {
                $(this).html(`<span class="${rangeHintsTextClass}">?</span>`);
            });

            if (removeSpinner) {
                $(".spinner").fadeOut("");
            }
        }
    },

    parseFinalNormalizedInputDataAndUpdateURL: function(slug, url, unit=null) {
        /**
         * Parse the return data from a normalize input API call. validateInput
         * is called here.
         */
        $.getJSON(url, function(normalizedInputData) {
            // Make sure data is from the final normalize input call before parsing
            // normalizedInputData
            if (normalizedInputData.reqno < o_search.slugNormalizeReqno[slug]) {
                delete opus.normalizeInputForAllFieldsInProgress[slug];
                return;
            }

            // Save the old state which indicates if there are ? in the result count and hints
            let inputsWereValid = opus.areInputsValid();

            // check each input, if it's not valid, change its background to red
            // and also remove spinner.
            o_search.validateInput(normalizedInputData, true, slug, unit);

            // When search is invalid, we disabled browse tab in nav link.
            if (!opus.areInputsValid()) {
                delete opus.normalizeInputForAllFieldsInProgress[slug];
                opus.navLinkRemembered = null;
                // This is for the case when we change a valid search (result1) to an invalid
                // search (result2), and later on change back to result1, there will be a search
                // triggered again to put back the valid green hints instead of keeping "?".
                opus.force_load = true;
                return;
            }

            o_search.rangesNameTotalMatchedCounter[slug] = 0;
            if (!inputsWereValid &&
                o_utils.areObjectsEqual(opus.selections, opus.lastSelections))  {
                // Put back normal hinting info
                opus.widgetsDrawn.forEach(function(eachSlug) {
                    o_search.getHinting(eachSlug);
                });
                $("#op-result-count").text(o_utils.addCommas(o_browse.totalObsCount));
            }
            $("input.RANGE, input.STRING").each(function() {
                if (!$(this).hasClass("input_currently_focused")) {
                    $(this).removeClass("search_input_valid");
                    $(this).removeClass("search_input_invalid");
                    $(this).addClass("search_input_original");
                }
            });

            $("#sidebar").removeClass("search_overlay");
            delete opus.normalizeInputForAllFieldsInProgress[slug];
            opus.changeTabToRemembered();

            let slugNoCounter = o_utils.getSlugOrDataWithoutCounter(slug);
            let uniqueid = o_utils.getSlugOrDataTrailingCounterStr(slug);
            let targetInput = $(`input.RANGE[name^="${slugNoCounter}"][data-uniqueid="${uniqueid}"]`);
            // Re-focus into the min input so that it will remember the current value (minVal) as
            // the old value. That way, when user changes the input value (new value), this old value
            // will be used for comparison to determine if a change event should fire. Note: if we
            // don't re-focus into the min input, the old value will be the value when we first focused
            // the input before selecting the preprogrammed item (not minVal).
            if (o_widgets.isReFocusingBackToInput && targetInput.hasClass("op-range-input-min") &&
                targetInput.hasClass("op-ranges-dropdown-menu")) {
                targetInput.blur();
                targetInput.focus();
                o_widgets.isReFocusingBackToInput = false;
            }
        });
    },

    extractHtmlContent: function(htmlString) {
        let domParser = new DOMParser();
        let content = domParser.parseFromString(htmlString, "text/html").documentElement.textContent;
        return content;
    },

    searchBarContainerHeight: function() {
        let mainNavHeight = $(".op-reset-opus").outerHeight() +
                            $("#op-main-nav").innerHeight() - $("#op-main-nav").height();
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

    searchWidgetHeightChanged: function(offset=0) {
        let footerHeight = $(".app-footer").outerHeight();
        let mainNavHeight = $(".op-reset-opus").outerHeight() +
                            $("#op-main-nav").innerHeight() - $("#op-main-nav").height();
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
        // If offset is not 0, properly scroll the scrollbar so that all the expanded mult
        // group contents can be displayed on the screen.
        if (offset) {
            let currentScrollbarPosition = $("#search #widget-container").scrollTop();
            let newScrollbarPosition = currentScrollbarPosition + offset;
            $("#search #widget-container").scrollTop(newScrollbarPosition);
        }
    },

    activateSearchTab: function() {

        if (o_search.searchTabDrawn) {
            return;
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
        if ($(`#widget__${slug} .op-unit-${slug}`).length) {
            let unitsVal = $(`#widget__${slug} .op-unit-${slug}`).val();
            units = `&units=${unitsVal}`;
        }
        o_search.lastEndpointsRequestNo++;
        o_search.slugEndpointsReqno[slug] = o_search.lastEndpointsRequestNo;
        let url = `/opus/__api/meta/range/endpoints/${slug}.json?${o_hash.getHash()}${units}` +
                  `&reqno=${o_search.slugEndpointsReqno[slug]}`;

        $.ajax({url: url,
            dataType:"json",
            success: function(multdata) {
                let rangeHintsDescription = "op-hints-description";
                let rangeHintsTextClass = "op-hints-info";
                $(`#widget__${slug} .spinner`).fadeOut();

                if (multdata.reqno < o_search.slugEndpointsReqno[slug]) {
                    return;
                }
                $("#hint__" + slug).html(`<span><span class="${rangeHintsDescription}">Min:&nbsp;</span>
                                          <span class="${rangeHintsTextClass}">${multdata.min}</span></span>
                                          <span><span class="${rangeHintsDescription}">Max:&nbsp;</span>
                                          <span class="${rangeHintsTextClass}">${multdata.max}</span></span>
                                          <span><span class="${rangeHintsDescription}">N/A:&nbsp;</span>
                                          <span class="${rangeHintsTextClass}">${multdata.nulls}</span></span>`);
            }
        }); // end mults ajax
    },

    getValidMults: function(slug, hideHintsForNonSelectedRadioButtons=false) {
        // turn on spinner
        $(`#widget__${slug} .spinner`).fadeIn();

        o_search.lastMultsRequestNo++;
        o_search.slugMultsReqno[slug] = o_search.lastMultsRequestNo;
        let url = `/opus/__api/meta/mults/${slug}.json?${o_hash.getHash()}&reqno=${o_search.slugMultsReqno[slug]}`;
        $.ajax({url: url,
            dataType:"json",
            success: function(multdata) {
                $(`#widget__${slug} .spinner`).fadeOut();

                if (multdata.reqno < o_search.slugMultsReqno[slug]) {
                    return;
                }

                let dataSlug = multdata.field_id;
                $("#widget__" + dataSlug + " .spinner").fadeOut();

                let widget = "widget__" + dataSlug;
                let mults = multdata.mults;
                let hintsTextClass = "op-hints-info";
                $("#" + widget + " input").each( function() {
                    let value = $(this).attr("value");
                    let id = "#hint__" + slug + "_" + value.replace(/ /g, "-").replace(/[^\w\s]/gi, "");  // id of hinting span, defined in widgets.js getWidget

                    if (!hideHintsForNonSelectedRadioButtons) {
                        if (mults[value]) {
                            $(id).html(`<span class="${hintsTextClass}" data-value=${mults[value]}>` + mults[value] + "</span>");
                            if ($(id).parent().hasClass("fadey")) {
                                $(id).parent().removeClass("fadey");
                            }
                        } else {
                            $(id).html(`<span class="${hintsTextClass}" data-value=0>0</span>`);
                            $(id).parent().addClass("fadey");
                        }
                    } else {
                        // Display "--" next to surfacegeometrytargetname inputs if the input is not selected.
                        $(id).parent().removeClass("fadey");
                        if (mults[value]) {
                            if ($(this).is(":checked")) {
                                $(id).html(`<span class="${hintsTextClass}" data-value=${mults[value]}>` + mults[value] + "</span>");
                            } else {
                                $(id).html(`<span class="${hintsTextClass}" data-value="--">--</span>`);
                            }
                        } else {
                            if ($(this).is(":checked")) {
                                $(id).html(`<span class="${hintsTextClass}" data-value=0>0</span>`);
                            } else {
                                $(id).html(`<span class="${hintsTextClass}" data-value="--">--</span>`);
                            }
                        }
                    }
                });

                // Count the total hints under each group name and display them in the ui
                // If the hints are all "--" under a group, we will display "--" next to
                // the group name.
                $("#" + widget + " .mult_group").each( function() {
                    let sum = 0;
                    // The flag used to determine if we will display the total hints or "--"
                    let displaySum = false;
                    let group = $(this).data("group");
                    let groupClass = `.mult_group_${group}`;

                    $(`#${widget} .mult_group[data-group="${group}"] .${hintsTextClass}`).each(function() {
                        let multVal = $(this).data("value");
                        let multValInt = parseInt(multVal);
                        if (!isNaN(multValInt)) {
                            sum += multValInt;
                            displaySum = true;
                        }
                    });
                    if (!displaySum) { sum = "--"; }
                    let hintHtml = `<span class="${hintsTextClass}">${sum}</span>`;
                    $(`#${widget} ${groupClass} .hints`).html(hintHtml);
                });
            }
        }); // end mults ajax

    },

    clearInputBorder: function(input) {
        /**
         * clear the border of an input, remove any invalid border of an input.
         */
        input.addClass("search_input_original");
        input.removeClass("search_input_invalid_no_focus");
        input.removeClass("search_input_invalid");
        input.removeClass("search_input_valid");
    },
};
