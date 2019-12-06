/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $ */
/* globals o_browse, o_hash, o_menu, o_search, o_utils, opus */

// font awesome icon class
const trashIcon = "far fa-trash-alt";
const plusIcon = "fas fa-plus";

/* jshint varstmt: false */
var o_widgets = {
/* jshint varstmt: true */

    /**
     *
     *  Getting and manipulating widgets on the search tab
     *
     **/

    lastStringSearchRequestNo: 0,
    // Use to make sure ranges dropdown is not closed by default or manually when it's set to true.
    isKeepingRangesDropdownOpen: false,

    // These two variables will used to prevent page reload when an input is closed and waiting
    // for the return of normalized input api. When an input is closed, there will be a
    // mismatched between selections (from URL) and opus.selections, they will be matched
    // after updateURL is called in the callback function when normalized input api is
    // returned. So in the middle of this process, we have to make sure page won't reload
    // in opus.load. Similar for adding input, after updateURL is called, selections and
    // opus.selections will be matched.
    isRemovingInput: false,
    isAddingInput: false,

    uniqueIdForInputs: 100,
    centerOrLabelDone: false,
    // This flag is used to let opus.load know that a widget just opened and we don't
    // want to perform a search when a widget has just opened.
    isGetWidgetDone: false,

    addWidgetBehaviors: function() {
        $("#op-search-widgets").sortable({
            items: "> li",
            cursor: "move",
            // we need the clone so that widgets in url gets changed only when sorting is stopped
            helper: "clone",
            scrollSensitivity: 100,
            axis: "y",
            opacity: 0.8,
            cursorAt: {top: 10, left: 10},
            stop: function(event, ui) {
                o_widgets.widgetDrop(this);
            },
        });

        $("#op-search-widgets").on( "sortchange", function(event, ui) {
            o_widgets.widgetDrop();
        });

        // click the dictionary icon, the definition slides open
        $('#search').on('click', 'a.dict_link', function() {
            $(this).parent().parent().find('.dictionary').slideToggle();
            return false;
        });

        // open/close mult groupings in widgets
        $('#search').on('click', '.mult_group_label_container', function() {
            $(this).find('.indicator').toggleClass('fa-plus');
            $(this).find('.indicator').toggleClass('fa-minus');
            $(this).next().slideToggle("fast");
        });

        // close a card
        $('#search').on('click', '.close_card', function(e) {
            e.preventDefault();

            let slug = $(this).data('slug');
            o_widgets.closeWidget(slug);
            let id = "#widget__"+slug;
            try {
                $(id).remove();
            } catch (error) {
                console.log("error on close widget, id="+id);
            }
        });

        // close opened surfacegeo widget if user select another surfacegeo target
        $('#search').on('change', 'input.singlechoice', function() {
            $('a[data-slug^="SURFACEGEO"]').each( function(index) {
                let slug = $(this).data('slug');
                o_widgets.closeWidget(slug);
                let id = "#widget__"+slug;
                try {
                    $(id).remove();
                } catch (e) {
                    console.log("error on close widget, id="+id);
                }
            });
        });

        // When user selects a ranges info item, update input fields and opus.selections
        // before triggering the search.
        $("#search").on("click", ".op-preprogrammed-ranges-data-item", function(e) {
            let minVal = $(e.currentTarget).data("min");
            let maxVal = $(e.currentTarget).data("max");
            let widgetId = $(e.currentTarget).data("widget");
            let minInputSlug = $(e.currentTarget).parent(".container").attr("data-mininput");

            // NOTE: We need support both RANGE & STRING inputs, for now we implement RANGE first.
            if ($(`#${widgetId} input.RANGE`).length !== 0) {
                o_widgets.fillRangesInputs(widgetId, minInputSlug, maxVal, minVal);
                // close dropdown and trigger the search
                $(`#${widgetId} input.op-range-input-min[name="${minInputSlug}"]`).dropdown("toggle");
                $(`#${widgetId} input.RANGE[name="${minInputSlug}"]`).trigger("change");

                let minInput = $(`#${widgetId} input.RANGE[name="${minInputSlug}"]`);
                let slug = o_utils.getSlugOrDataWithoutCounter(minInputSlug);
                let slugName = minInput.attr("data-slugname");
                let uniqueid = minInput.attr("data-uniqueid");
                let oppositeSuffixSlug = (slug.match(/(.*)1$/) ? `${slugName}2` : `${slugName}1`);
                $(`#${widgetId} input.RANGE[name*="${oppositeSuffixSlug}"][data-uniqueid="${uniqueid}"]`).trigger("change");
            }
        });

        o_widgets.addPreprogrammedRangesBehaviors();
        o_widgets.addAttachOrRemoveInputsBehaviors();
    },

    attachAddInputIcon: function(slug, addInputIcon) {
        /**
         * Make sure "+ (OR)" is attached to the right of last input set.
         * Display or hide the icon based on the number of input sets.
         */
        $(`#widget__${slug} .op-search-inputs-set`).last().append(addInputIcon);
        let numberOfInputSets = $(`#widget__${slug} .op-search-inputs-set`).length;
        if (numberOfInputSets === opus.maxAllowedInputSets) {
            $(`#widget__${slug} .op-add-inputs`).addClass("op-hide-element");
        } else {
            $(`#widget__${slug} .op-add-inputs`).removeClass("op-hide-element");
        }
    },

    addAttachOrRemoveInputsBehaviors: function() {
        /**
         * Add event handlers for click events on "+ (OR)" and trash icons.
         * These are behaviors of adding/removing inputs in a single widget.
         */

        // Create a new set of inputs when clicking the "+ (OR)" button in a widget.
        $("#search").on("click", ".op-add-inputs-btn", function(e) {
            e.preventDefault();
            o_widgets.isAddingInput = true;

            let widgetId = $(this).data("widget");
            let slug = $(this).data("slug");
            let addInputIcon = $(`#widget__${slug} .op-add-inputs`).detach();
            let firstExistingSetOfInputs = $(`#${widgetId} .op-search-inputs-set`).first();
            let lastExistingSetOfInputs = $(`#${widgetId} .op-search-inputs-set`).last();
            // Do not pass in true to clone(), otherwise event handlers will be attached
            // for multiple times and cause some weird behaviors.
            let cloneInputs = firstExistingSetOfInputs.clone();
            cloneInputs.addClass("op-extra-search-inputs");
            o_search.clearInputBorder(cloneInputs);
            // Clear .op-hide-element in dropdown
            cloneInputs.find(".op-hide-element").removeClass("op-hide-element");
            let defaultQtypeVal = (cloneInputs.find("select") ?
                                   cloneInputs.find("option").first().val() :
                                   "");
            if (defaultQtypeVal) {
                cloneInputs.find("select").val(defaultQtypeVal);
            }

            // Assign unique id to new inputs. Inputs in the same set will have the same id.
            o_widgets.uniqueIdForInputs += 1;
            cloneInputs.find("input").attr("data-uniqueid", o_widgets.uniqueIdForInputs);
            cloneInputs.find("input").val("");

            let orLabel = ('<ul class="op-or-labels text-secondary">' +
                           '<hr class="op-or-label-divider">' +
                           '&nbsp;OR&nbsp;' +
                           '<hr class="op-or-label-divider"></ul>');

            let removeInputIcon = ('<li class="op-remove-inputs">' +
                                   '<button type="button" title="Delete this set of search inputs" \
                                   class="p-0 btn btn-small btn-link op-remove-inputs-btn"' +
                                   `data-widget="widget__${slug}" data-slug="${slug}">` +
                                   `<i class="${trashIcon}"></i></button></li>`);

            // Before attaching a new (cloned from the first input set) input set:
            // If the first input set doesn't have remove icon, we add remove icon & "OR" label
            // to the first input set, and add remove icon to cloned input set, else we add "OR"
            // label to the last input set and remove "OR" label from cloned input set.
            if (firstExistingSetOfInputs.find(".op-remove-inputs").length === 0) {
                firstExistingSetOfInputs.append(removeInputIcon);
                firstExistingSetOfInputs.append(orLabel);
                cloneInputs.append(removeInputIcon);
            } else {
                lastExistingSetOfInputs.append(orLabel);
                cloneInputs.find(".op-or-labels").remove();
            }

            // Add dummy qtype to center "-- OR --".
            let numberOfQtypeInputs = $(`#widget__${slug} .op-qtype-input`).length;
            if (numberOfQtypeInputs !== 0) {
                let qtypeItem = $(`#widget__${slug} .op-qtype-input:first`);
                let qtypeHelperItem = $(`#widget__${slug} .op-range-qtype-helper:first`);
                let [dummyItem1, dummyItem2] = o_widgets.createInvisibleDummyItems(slug);
                if (dummyItem1) {
                    $(`#widget__${slug} .op-or-labels:last`).append(dummyItem1);
                    $(`#widget__${slug} .op-dummy-item1`).width(qtypeItem.width());
                }
                if (dummyItem2) {
                    $(`#widget__${slug} .op-or-labels:last`).append(dummyItem2);
                    $(`#widget__${slug} .op-dummy-item2`).width(qtypeHelperItem.width());
                }
            }

            $(`#${widgetId} .op-input`).append(cloneInputs);
            // Prevent overscrolling for newly added dropdown.
            let newlyAddedDropdown = $(`#${widgetId} .op-search-inputs-set:last .op-scrollable-menu`);
            newlyAddedDropdown.on("scroll wheel", function(scrollingEvent) {
                scrollingEvent.stopPropagation();
            });

            o_widgets.renumberInputsAttributes(slug);

            let numberOfInputSets = $(`#widget__${slug} .op-search-inputs-set`).length;
            o_widgets.attachAddInputIcon(slug, addInputIcon);

            // Restore the dropdown status, including removing all highlighted texts
            // and collapse all ranges categories.
            let inputToTriggerDropdown = ($(`#widget__${slug} .op-search-inputs-set:last`)
                                          .find("input:first"));
            o_widgets.restoreRangesInfoDropdownStatus(inputToTriggerDropdown);

            // Update opus.selections & opus.extras
            let newlyAddedInput = $(`#widget__${slug} .op-search-inputs-set input`).last();
            let newlyAddedQtype = $(`#widget__${slug} .op-search-inputs-set select`).last();

            // Check if there is any selections change. This flag will be used to determine
            // if normalize input should be run when removing an empty input set.
            let noSelectionsChange = (o_utils.areObjectsEqual(opus.selections, opus.lastSelections) &&
                                      o_utils.areObjectsEqual(opus.extras, opus.lastExtras));

            if (newlyAddedInput.hasClass("RANGE")) {
                opus.selections[`${slug}1`] = opus.selections[`${slug}1`] || [];
                opus.selections[`${slug}2`] = opus.selections[`${slug}2`] || [];
                while (opus.selections[`${slug}1`] .length < numberOfInputSets) {
                    opus.selections[`${slug}1`].push(null);
                }
                while (opus.selections[`${slug}2`] .length < numberOfInputSets) {
                    opus.selections[`${slug}2`].push(null);
                }

                if (newlyAddedQtype.length > 0) {
                    opus.extras[`qtype-${slug}`].push(defaultQtypeVal);
                }
                if (opus.extras[`unit-${slug}`]) {
                    let defaultUnitVal = $(`#widget__${slug} .unit-${slug}`).val();
                    opus.extras[`unit-${slug}`].push(defaultUnitVal);
                }
            } else if (newlyAddedInput.hasClass("STRING")) {
                opus.selections[slug] = opus.selections[slug] || [];
                while (opus.selections[slug].length < numberOfInputSets) {
                    opus.selections[slug].push(null);
                }

                if (newlyAddedQtype.length > 0) {
                    opus.extras[`qtype-${slug}`].push(defaultQtypeVal);
                }
                if (opus.extras[`unit-${slug}`]) {
                    let defaultUnitVal = $(`#widget__${slug} .unit-${slug}`).val();
                    opus.extras[`unit-${slug}`].push(defaultUnitVal);
                }

                // Init autocomplete
                let widgetInputs = $(`#widget__${slug} input`);
                // Since inputs are renumber, we have to update the corresponding autocomplete.
                // We will destory all old autocomplete and re-init for each input.
                o_widgets.destroyAutocomplete(slug);
                // loop through each input set and re-init autocomplete for each of them
                for (const singleInput of widgetInputs) {
                    let slugWithCounter = $(singleInput).attr("name");
                    o_widgets.initAutocomplete(slug, slugWithCounter);
                }
            }

            if (!opus.isAnyNormalizeInputInProgress()) {
                if (noSelectionsChange || !opus.areRangeInputsValid()) {
                    // This will make sure normalize input api from opus.load is not called.
                    opus.updateOPUSLastSelectionsWithOPUSSelections();
                }
            }
            o_hash.updateURLFromCurrentHash();
            o_widgets.isAddingInput = false;
        });

        $("#search").on("click", ".op-remove-inputs", function(e) {
            e.preventDefault();
            o_widgets.isRemovingInput = true;

            let slug = $(this).find(".op-remove-inputs-btn").data("slug");
            let addInputIcon = $(`#widget__${slug} .op-add-inputs`).detach();
            let inputSetToBeDeleted = $(this).parent(".op-search-inputs-set");

            let inputElement = $(this).parent(".op-search-inputs-set").find("input");
            let qtypeElement = $(this).parent(".op-search-inputs-set").find("select");
            let slugNameFromInput = inputElement.attr("name");
            let trailingCounterString = o_utils.getSlugOrDataTrailingCounterStr(slugNameFromInput);
            let idx = trailingCounterString ? parseInt(trailingCounterString)-1 : 0;

            let isRemovingEmptySet = true;

            // Check if there is any selections change. This flag will be used to determine
            // if normalize input should be run when removing an empty input set.
            let noSelectionsChange = (o_utils.areObjectsEqual(opus.selections, opus.lastSelections) &&
                                      o_utils.areObjectsEqual(opus.extras, opus.lastExtras));

            if (inputElement.hasClass("RANGE")) {
                let previousMinSelections = opus.selections[`${slug}1`];
                let previousMaxSelections = opus.selections[`${slug}2`];
                if (previousMaxSelections[idx] || previousMinSelections[idx]) {
                    isRemovingEmptySet = false;
                }

                opus.selections[`${slug}1`] = (previousMinSelections.slice(0, idx)
                                               .concat(previousMinSelections.slice(idx+1)));
                opus.selections[`${slug}2`] = (previousMaxSelections.slice(0, idx)
                                               .concat(previousMaxSelections.slice(idx+1)));
                if (qtypeElement.length > 0) {
                    opus.extras[`qtype-${slug}`].splice(idx, 1);
                    // let previousExtras = opus.extras[`qtype-${slug}`];
                    // opus.extras[`qtype-${slug}`] = (previousExtras.slice(0, idx)
                    //                                 .concat(previousExtras.slice(idx+1)));
                }
                if (opus.extras[`unit-${slug}`]) {
                    opus.extras[`unit-${slug}`].splice(idx, 1);
                    // let previousUnits = opus.extras[`unit-${slug}`];
                    // opus.extras[`unit-${slug}`] = (previousUnits.slice(0, idx)
                    //                                .concat(previousUnits.slice(idx+1)));
                }
            } else if (inputElement.hasClass("STRING")) {
                let previousSelections = opus.selections[`${slug}`];
                if (previousSelections[idx]) {
                    isRemovingEmptySet = false;
                }

                opus.selections[`${slug}`] = (previousSelections.slice(0, idx)
                                              .concat(previousSelections.slice(idx+1)));
                if (qtypeElement.length > 0) {
                    opus.extras[`qtype-${slug}`].splice(idx, 1);
                    // let previousExtras = opus.extras[`qtype-${slug}`];
                    // opus.extras[`qtype-${slug}`] = (previousExtras.slice(0, idx)
                    //                                 .concat(previousExtras.slice(idx+1)));
                }
                if (opus.extras[`unit-${slug}`]) {
                    opus.extras[`unit-${slug}`].splice(idx, 1);
                    // let previousUnits = opus.extras[`unit-${slug}`];
                    // opus.extras[`unit-${slug}`] = (previousUnits.slice(0, idx)
                    //                                .concat(previousUnits.slice(idx+1)));
                }
            }

            o_widgets.removeInputsValidationInfo(inputElement);

            inputSetToBeDeleted.remove();

            // Remove OR label and .op-extra-search-inputs if they exist in the first input set
            let firstExistingSetOfInputs = $(`#widget__${slug} .op-search-inputs-set`).first();
            let lastExistingSetOfInputs = $(`#widget__${slug} .op-search-inputs-set`).last();
            firstExistingSetOfInputs.removeClass("op-extra-search-inputs");

            if (lastExistingSetOfInputs.find(".op-or-labels").length !== 0) {
                lastExistingSetOfInputs.find(".op-or-labels").remove();
            }

            // Remove the remove icon if we only have one input set left.
            let numberOfInputSets = $(`#widget__${slug} .op-search-inputs-set`).length;
            if (numberOfInputSets === 1) {
                $(`#widget__${slug} .op-search-inputs-set .op-or-labels`).remove();
                $(`#widget__${slug} .op-search-inputs-set .op-remove-inputs`).remove();
            }

            o_widgets.renumberInputsAttributes(slug);
            o_widgets.attachAddInputIcon(slug, addInputIcon);

            let widgetInputs = $(`#widget__${slug} input`);
            if (widgetInputs.hasClass("STRING")) {
                // Since inputs are renumber, we have to update the corresponding autocomplete.
                // We will destory all old autocomplete and re-init for each input.
                o_widgets.destroyAutocomplete(slug);
                // loop through each input set and re-init autocomplete for each of them
                for (const singleInput of widgetInputs) {
                    let slugWithCounter = $(singleInput).attr("name");
                    o_widgets.initAutocomplete(slug, slugWithCounter);
                }
            }

            // When we delete a set of inputs while there is a normalize input running,
            // we will trigger another normalize input call to make sure the latest
            // opus.selections get synced up properly. Because when parsing the return
            // data from a normalize input call (in validateRangeInput), there is no way
            // for us to tell if any idx changes (elements got removed) happened in
            // opus.selections, and this will mess up opus.selections. By calling one final
            // normalize input, the latest opus.selections will be used for this api call,
            // and opus.selections will get updated properly at the end.
            if (!opus.isAnyNormalizeInputInProgress()) {
                if ((noSelectionsChange && isRemovingEmptySet) ||
                    !opus.areRangeInputsValid()) {
                    // Make sure normalize input api from opus.load is not called when an
                    // empty set is removed.
                    opus.updateOPUSLastSelectionsWithOPUSSelections();
                }
                o_hash.updateURLFromCurrentHash();
                o_widgets.isRemovingInput = false;
            } else {
                o_search.allNormalizeInputApiCall().then(function(normalizedData) {

                    if (normalizedData.reqno < o_search.lastSlugNormalizeRequestNo) {
                        delete opus.normalizeInputForAllFieldsInProgress[opus.allSlug];
                        o_widgets.isRemovingInput = false;
                        return;
                    }
                    o_search.validateRangeInput(normalizedData, false);

                    if (opus.areRangeInputsValid()) {
                        $("input.RANGE").removeClass("search_input_valid");
                        $("input.RANGE").removeClass("search_input_invalid");
                        $("input.RANGE").addClass("search_input_original");
                        $("#sidebar").removeClass("search_overlay");
                        $("#op-result-count").text(o_utils.addCommas(o_browse.totalObsCount));
                        if (o_utils.areObjectsEqual(opus.selections, opus.lastSelections))  {
                            // Put back normal hinting info
                            opus.widgetsDrawn.forEach(function(eachSlug) {
                                o_search.getHinting(eachSlug);
                            });
                        }
                        $(".op-browse-tab").removeClass("op-disabled-nav-link");
                    } else {
                        $(".op-browse-tab").addClass("op-disabled-nav-link");
                    }

                    if (opus.areRangeInputsValid()) {
                        o_hash.updateURLFromCurrentHash();
                    }

                    delete opus.normalizeInputForAllFieldsInProgress[opus.allSlug];
                    o_widgets.isRemovingInput = false;
                });

            }
        });
    },

    addPreprogrammedRangesBehaviors: function() {
        /**
         * Add customized event handlers for the general behaviors of preprogrammed ranges
         * dropdown and expandable list. This function will be called in getWidget.
         */

        // Expand/collapse info when clicking a dropdown submenu
        $("#search").on("click", ".op-scrollable-menu .dropdown-item", function(e) {
            // prevent URL being messed up with href in <a>
            e.preventDefault();
            let collapsibleID = $(e.target).attr("href");
            $(`${collapsibleID}`).collapse("toggle");
        });

        // Avoid closing dropdown menu when clicking any dropdown item
        $("#search").on("click", ".op-scrollable-menu", function(e) {
            e.stopPropagation();
        });

        // Make sure expanded contents are collapsed when ranges dropdown list is closed.
        $("#search").on("hidden.bs.dropdown", function(e) {
            $(".op-preprogrammed-ranges .container").collapse("hide");
        });

        // Prevent dropdown from closing when clicking on the focused input again
        $("#search").on("mousedown", "input.op-range-input-min", function(e) {
            if ($(".op-scrollable-menu").hasClass("show") && $(e.target).is(":focus")) {
                o_widgets.isKeepingRangesDropdownOpen = true;
            }
        });

        $("#search").on("hide.bs.dropdown", function(e) {
            if (o_widgets.isKeepingRangesDropdownOpen) {
                e.preventDefault();
                o_widgets.isKeepingRangesDropdownOpen = false;
            }
        });
    },

    fillRangesInputs: function(widgetId, minInputSlug, maxVal, minVal) {
        /**
         * Fill both ranges inputs with values passed in to the function.
         */
        let minInput = $(`#${widgetId} input.op-range-input-min[name="${minInputSlug}"]`);
        let uniqueid = minInput.attr("data-uniqueid");
        let minInputName = minInput.attr("name");
        let slugName = minInput.data("slugname");
        opus.rangeInputFieldsValidation[`${slugName}1_${uniqueid}`] = true;
        opus.rangeInputFieldsValidation[`${slugName}2_${uniqueid}`] = true;

        let slug = "";
        let slugOrderNum = "";
        if (minInputName.match(/(.*)_[0-9]{2}$/)) {
            slug = minInputName.match(/(.*)_[0-9]{2}$/)[1];
            slugOrderNum = minInputName.match(/.*(_[0-9]{2})$/)[1];
        } else {
            slug = minInputName;
        }

        if (minVal) {
            minInput.val(minVal);
        } else {
            minInput.val("");
        }

        slug = slugName + "2" + slugOrderNum;
        let maxInput = $(`#${widgetId} input.op-range-input-max[name="${slug}"]`);
        slug = slugName + "2";
        if (maxVal) {
            maxInput.val(maxVal);
        } else {
            maxInput.val("");
        }

        // clear validation border & background
        for (const input of [minInput, maxInput]) {
            input.addClass("search_input_original");
            input.removeClass("search_input_invalid_no_focus");
            input.removeClass("search_input_invalid");
            input.removeClass("search_input_valid");
        }
    },

    removeInputsValidationInfo: function(inputs) {
        /**
         * Remove input validation info in opus.rangeInputFieldsValidation when an input
         * or a widget is removed.
         */
        for (const inputField of inputs) {
            let inputName = $(inputField).attr("name");
            let slugWithoutCounter = o_utils.getSlugOrDataWithoutCounter(inputName);
            let uniqueid = $(inputField).attr("data-uniqueid");
            let slugWithId = `${slugWithoutCounter}_${uniqueid}`;
            delete opus.rangeInputFieldsValidation[slugWithId];
        }
    },

    restoreRangesInfoDropdownStatus: function(targetInput) {
        /**
         * Remove all highlighted text and make sure all category are collpased
         */
        let preprogrammedRangesDropdown = (targetInput
                                           .next(".op-preprogrammed-ranges")
                                           .find(".op-scrollable-menu"));
        let preprogrammedRangesInfo = preprogrammedRangesDropdown.find("li");

        // If ranges info is not available, return from the function.
        if (preprogrammedRangesDropdown.length === 0 || !$(targetInput).hasClass("op-range-input-min")) {
            return;
        }

        for (const category of preprogrammedRangesInfo) {
            let collapsibleContainerId = $(category).attr("data-category");
            let rangesInfoInOneCategory = $(`#${collapsibleContainerId} .op-preprogrammed-ranges-data-item`);

            for (const singleRangeData of rangesInfoInOneCategory) {
                o_search.removeHighlightedRangesName(singleRangeData);
                $(`a.dropdown-item[href*="${collapsibleContainerId}"]`).removeClass("op-hide-element");
                $(singleRangeData).removeClass("op-hide-element");
                $(`#${collapsibleContainerId}`).collapse("hide");
            }
        }
    },

    closeWidget: function(slug) {
        let isRemovingEmptyWidget = true;
        let slugNoNum;
        try {
            slugNoNum = slug.match(/(.*)[1|2]$/)[1];
        } catch (e) {
            slugNoNum = slug;
        }

        if ($.inArray(slug,opus.prefs.widgets) > -1) {
            opus.prefs.widgets.splice(opus.prefs.widgets.indexOf(slug), 1);
        }

        if ($.inArray(slug,opus.widgetsDrawn) > -1) {
            opus.widgetsDrawn.splice(opus.widgetsDrawn.indexOf(slug), 1);
        }

        if ($.inArray(slug, opus.widgetElementsDrawn) > -1) {
            opus.widgetElementsDrawn.splice(opus.widgetElementsDrawn.indexOf(slug), 1);
        }

        if (slug in opus.selections) {
            delete opus.selections[slug];
        }
        // handle for range queries
        if (slugNoNum + '1' in opus.selections) {
            delete opus.selections[slugNoNum + '1'];
        }
        if (slugNoNum + '2' in opus.selections) {
            delete opus.selections[slugNoNum + '2'];
        }

        delete opus.extras[`qtype-${slugNoNum}`];
        delete opus.extras[`z-${slugNoNum}`];
        delete opus.extras[`unit-${slugNoNum}`];

        let selector = `.op-search-menu li [data-slug='${slug}']`;
        o_menu.markMenuItem(selector, "unselect");

        let inputs = $(`#widget__${slugNoNum} input`);
        // Check if the widget to be removed has empty values on all inputs.
        for (const input of inputs) {
            if ($(input).val() && $(input).val().trim()) {
                isRemovingEmptyWidget = false;
            }
        }

        o_widgets.removeInputsValidationInfo(inputs);

        o_search.allNormalizeInputApiCall().then(function(normalizedData) {
            if (normalizedData.reqno < o_search.lastSlugNormalizeRequestNo) {
                delete opus.normalizeInputForAllFieldsInProgress[opus.allSlug];
                return;
            }
            o_search.validateRangeInput(normalizedData, false);

            if (opus.areRangeInputsValid()) {
                $("input.RANGE").removeClass("search_input_valid");
                $("input.RANGE").removeClass("search_input_invalid");
                $("input.RANGE").addClass("search_input_original");
                $("#sidebar").removeClass("search_overlay");
                $("#op-result-count").text(o_utils.addCommas(o_browse.totalObsCount));
                if (o_utils.areObjectsEqual(opus.selections, opus.lastSelections))  {
                    // Put back normal hinting info
                    opus.widgetsDrawn.forEach(function(eachSlug) {
                        o_search.getHinting(eachSlug);
                    });
                }
                $(".op-browse-tab").removeClass("op-disabled-nav-link");
            } else {
                $(".op-browse-tab").addClass("op-disabled-nav-link");
            }

            // If the closing widget has empty values, don't perform a search.
            if (isRemovingEmptyWidget) {
                opus.updateOPUSLastSelectionsWithOPUSSelections();
            }

            if (opus.areRangeInputsValid()) {
                o_hash.updateURLFromCurrentHash();
            }

            o_widgets.updateWidgetCookies();
            delete opus.normalizeInputForAllFieldsInProgress[opus.allSlug];
        });
    },

    widgetDrop: function(obj) {
            // if widget is moved to a different formscolumn,
            // redefine the opus.prefs.widgets (preserves order)
            let widgets = $('#op-search-widgets').sortable('toArray');
            $.each(widgets, function(index,value) {
                widgets[index]=value.split('__')[1];
            });
            opus.prefs.widgets = widgets;

            o_hash.updateURLFromCurrentHash();

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
                    let mult_id = '.mult_group_' + $(this).attr('value');
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
                        let mult_id = '.mult_group_' + $(this).attr('value');
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
                       let mult_id = '.mult_group_' + $(this).attr('value');
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
        $(widget).animate({width:$('#op-search-widgets').width() - 2*20 + 'px'},'fast');  // 20px is the side margin of .widget
    },

    maximizeWidget: function(slug, widget) {
        // un-minimize widget ... maximize widget
        $('.minimize_widget', '#' + widget).toggleClass('opened_triangle');
        $('.minimize_widget', '#' + widget).toggleClass('closed_triangle');
        $('#widget_control_' + slug + ' .remove_widget').show();
        $('#widget_control_' + slug + ' .divider').show();
        $('#' + widget + ' .widget_minimized').hide();
        $('#widget_control_' + slug).removeClass('widget_controls_minimized');
        $('#' + widget + ' .widget_inner').show("blind");
        $('.ui-resizable-handle').show();
    },


    minimizeWidget: function(slug, widget) {
        // the minimized text version of the contstrained param = like "planet=Saturn"
        $('.minimize_widget', '#' + widget).toggleClass('opened_triangle');
        $('.minimize_widget', '#' + widget).toggleClass('closed_triangle');

        $('#widget_control_' + slug + ' .remove_widget').hide();
        $('#widget_control_' + slug + ' .divider').hide();

        let simple = o_widgets.minimizeWidgetLabel(slug);
        function doit() { // XXX WHY IS THIS A FUNCTION?
            $('#' + widget + ' .widget_inner').hide();

            $('#' + widget).animate({height:'1.2em'}, 'fast');
            $('#' + widget + ' .widget_minimized').html(simple).fadeIn("fast");
            $('#widget_control_' + slug).addClass('widget_controls_minimized');

            $('.ui-resizable-handle','#'+widget).hide();

        }
        doit();
    },

    // the string that shows when a widget is minimized
    minimizeWidgetLabel: function(slug) {
        // XXX This entire function needs review and help
        let label;
        let simple;
         try {
             label = $('#widget__' + slug + ' h2.widget_label').html();
         } catch(e) {
             label = slug;
         }

         let slugMin = false;
         let slugMax = false;
         let slugNoNum = false;
         if (slug.match(/.*(1|2)$/)) {
             slugNoNum = slug.match(/(.*)[1|2]$/)[1];
             slugMin = slugNoNum + '1';
             slugMax = slugNoNum + '2';
         }

         if (opus.selections[slug]) {

             let form_type = $('#widget__' + slug + ' .widget_inner').attr("class").split(' ')[1];

             if (form_type == 'RANGE') {

                 // this is a range widget
                 let qtypes;
                 try {
                     qtypes = opus.extras['qtype-' + slugNoNum];
                 } catch(e) {
                     qtypes = [opus.qtypeRangeDefault];
                 }

                 let length = (opus.selections[slugMin].length > opus.selections[slugMax].length) ? opus.selections[slugMin].length : opus.selections[slugMax].length;

                 simple = [];
                 for (let i=0;i<length;i++) {
                     // ouch:
                     let qtype;
                     try{
                         qtype = qtypes[i];
                     } catch(e) {
                         try {
                             qtype = qtypes[0];
                         } catch(e) {
                             qtype = opus.qtypeRangeDefault;
                         }
                     }

                     switch(qtype) {
                          case 'only':
                              simple[simple.length] = ' min >= ' + opus.selections[slugMin][i] + ', ' +
                                                      ' max <= ' + opus.selections[slugMax][i];
                              break;

                          case 'all':
                              simple[simple.length] = ' min <= ' + opus.selections[slugMin][i] + ', ' +
                                                      ' max  >= ' + opus.selections[slugMax][i];
                              break;

                          default:
                              simple[simple.length] = ' min  <= ' + opus.selections[slugMax][i] + ', ' +
                                                      ' max  >= ' + opus.selections[slugMin][i];
                      }

                      break;  // we have decided to only show the first range in the minimized display
                  }
                  simple = label + simple.join(' and ');
                  if (length > 1) {
                      simple = simple + ' and more..';
                  }

             } else if (form_type == 'STRING') {
                 let s_arr = [];
                 let last_qtype = '';
                 for (let key in opus.selections[slug]) {
                     let value = opus.selections[slug][key];
                     let qtype;
                     try {
                         qtype = opus.extras['qtype-'+slug][key];
                     } catch(err) {
                         qtype = opus.qtypeStringDefault;
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
                     last_qtype = qtype;
                 }
                 simple = s_arr.join(' or ');


             } else {
                 // this is not a range widget
                 simple = label + ' = ' + opus.selections[slug].join(', ');
             }
         } else {
             simple = label + ' not constrained';
         }
         return simple;
     },

     updateWidgetCookies: function() {
         $.cookie("widgets", opus.prefs.widgets.join(','), { expires: 28});  // days
      },

     placeWidgetContainers: function() {
         // this is for when you are first drawing the browse tab and there
         // multiple widgets being requested at once and we want to preserve their order
         // and avoid race conditions that will throw them out of order
         for (let k in opus.prefs.widgets) {
             let slug = opus.prefs.widgets[k];
             let widget = 'widget__' + slug;
             let html = '<li id="' + widget + '" class="widget"></li>';
             $(html).appendTo('#op-search-widgets ');
             // $(html).hide().appendTo('#op-search-widgets').show("blind",{direction: "vertical" },200);
             opus.widgetElementsDrawn.push(slug);
         }
     },

     // adds a widget and its behaviors, adjusts the opus.prefs variable to include this widget, will not update the hash
    getWidget: function(slug, formscolumn) {
        if (!slug) {
            return;
        }

        if ($.inArray(slug, opus.widgetsDrawn) > -1) {
            return; // widget already drawn
        }
        if ($.inArray(slug, opus.widgetsFetching) > -1) {
            return; // widget being fetched
        }

        let widget = 'widget__' + slug;

        opus.widgetsFetching.push(slug);

        // add the div that will hold the widget
        if ($.inArray(slug, opus.widgetElementsDrawn) < 0) {
            opus.prefs.widgets.unshift(slug);

            o_widgets.updateWidgetCookies();
            // these sometimes get drawn on page load by placeWidgetContainers, but not this time:
            let html = '<li id="' + widget + '" class="widget"></li>';
            $(html).hide().prependTo(formscolumn).show("slow");
            opus.widgetElementsDrawn.unshift(slug);

        }

        $.ajax({
            url: "/opus/__forms/widget/" + slug + '.html?' + o_hash.getHash(),
            success: function(widget_str) {
                $("#widget__"+slug).html(widget_str);
            }
        }).done(function() {
            // If there is no specified qtype in the url, we want default qtype to be in the url
            // This will also put qtype in the url when a widget with qtype is open.
            // Need to wait until api return to determine if the widget has qtype selections
            let hash = o_hash.getHashArray();
            // NOTE: inputs & qtypes are not renumbered yet at this stage.
            let qtype = `qtype-${slug}`;
            let qtypeInputs = $(`#widget__${slug} .widget-main select[name="${qtype}"]`);
            let numberOfQtypeInputs = qtypeInputs.length;

            let unit = `unit-${slug}`;
            let unitInput = $(`#widget__${slug} .${unit}`);

            if (unitInput.length) {
                if (!opus.extras[unit]) {
                    opus.extras[unit] = [unitInput.val()];
                } else {
                    unitInput.val(opus.extras[unit][0]);
                }
                // For widgets with unit but without qtype:
                if (numberOfQtypeInputs === 0) {
                    o_hash.updateURLFromCurrentHash();
                }
            }

            if (numberOfQtypeInputs !== 0) {
                qtypeInputs.parent("li").addClass("op-qtype-input");
                let qtypeValue = $(`#widget__${slug} .widget-main select[name="${qtype}"] option:selected`).val();
                if (qtypeValue === "any" || qtypeValue === "all" || qtypeValue === "only") {
                    let helpIcon = '<li class="op-range-qtype-helper">\
                                    <a class="text-dark" tabindex="0" data-toggle="popover" data-placement="left">\
                                    <i class="fas fa-info-circle"></i></a></li>';

                    // Make sure help icon is attached to the end of each set of inputs
                    $(`#widget__${slug} .widget-main .op-input ul`).append(helpIcon);
                }

                if (numberOfQtypeInputs === 1 && !hash[qtype]) {
                    // When a widget with qtype is open, the value of the first option tag is the
                    // default value for qtype
                    let defaultOption = $(`#widget__${slug} .widget-main select[name="${qtype}"]`).first("option").val();
                    opus.extras[qtype] = [defaultOption];
                    o_hash.updateURLFromCurrentHash();
                } else if (numberOfQtypeInputs > 1) {
                    // When there are multiple qtype inputs, update qtype options for each
                    // set of inputs by values from opus.extras.
                    let qtypeDataIdx = 0;
                    for (const eachQtype of qtypeInputs) {
                        $(eachQtype).val(opus.extras[qtype][qtypeDataIdx]);
                        qtypeDataIdx++;
                    }
                    o_hash.updateURLFromCurrentHash();
                }
            }
            // Initialize popover, this for the (i) icon next to qtype
            $(".widget-main .op-range-qtype-helper a").popover({
                html: true,
                container: "body",
                trigger: "hover",
                content: function() {
                    return $("#op-qtype-tooltip").html();
                }
            });

            // Prevent overscrolling on ps in widget container when scrolling inside dropdown
            // list has reached to both ends
            $(".op-scrollable-menu").on("scroll wheel", function(e) {
                e.stopPropagation();
            });

            // If ".op-preprogrammed-ranges" is available in the widget, we move the whole
            // element into the input.op-range-input-min li and use it as the customized dropdown expandable
            // list for input.op-range-input-min. This will also make sure dropdown list always stays below
            // input.op-range-input-min.
            let rangesInfoDropdown = $(`#${widget} .op-preprogrammed-ranges`).detach();
            if (rangesInfoDropdown.length > 0) {
                $(`#${widget} input.op-range-input-min`).after(rangesInfoDropdown);
                $(`#${widget} .op-input`).addClass("dropdown");
                o_widgets.alignRangesDataByDecimalPoint(widget);
            }

            // add the spans that hold the hinting
            try {
                $('#' + widget + ' ul label').after(function() {
                    let value = $(this).find('input').attr("value");
                    let span_id = 'hint__' + slug + '_' + value.replace(/ /g,'-').replace(/[^\w\s]/gi, '');  // special chars not allowed in id element
                    return '<span class="hints" id="' + span_id + '"></span>';
                });
            } catch(e) { } // these only apply to mult widgets


            if ($.inArray(slug,opus.widgetsFetching) > -1) {
                opus.widgetsFetching.splice(opus.widgetsFetching.indexOf(slug), 1);
            }

            if ($.isEmptyObject(opus.selections)) {
                $('#widget__' + slug + ' .spinner').fadeOut('');
            }

            let widgetInputs = $(`#widget__${slug} input`);
            o_widgets.renumberInputsAttributes(slug);

            if (widgetInputs.hasClass("STRING")) {
                // loop through each input set and init autocomplete for each of them
                for (const singleInput of widgetInputs) {
                    let slugWithCounter = $(singleInput).attr("name");
                    o_widgets.initAutocomplete(slug, slugWithCounter);
                }
            }

            // close autocomplete dropdown menu when y-axis scrolling happens
            $("#widget-container").on("ps-scroll-y", function() {
                $(`#widget__${slug} input.STRING`).autocomplete("close");

                // Close dropdown list when ps scrolling is happening in widget container
                if ($(`#${widget} .op-scrollable-menu`).hasClass("show")) {
                    // Note: the selector to toggle dropdown should be the one with data-toggle="dropdown"
                    // or "dropdown-toggle" class, and in this case it's the li (.op-ranges-dropdown-menu).
                    $(`#${widget} input.op-range-input-min`).dropdown("toggle");
                }
            });

            if (widgetInputs.hasClass("RANGE") || widgetInputs.hasClass("STRING")) {
                let addInputIcon = ('<li class="op-add-inputs">' +
                                    '<button type="button" class="ml-2 p-0 btn btn-small btn-link op-add-inputs-btn" \
                                    title="Add a new set of search inputs"' +
                                    `data-widget="widget__${slug}" data-slug="${slug}">` +
                                    `<i class="${plusIcon}">&nbsp;(OR)</i></button></li>`);

                let orLabel = ('<ul class="op-or-labels text-secondary">' +
                               '<hr class="op-or-label-divider">' +
                               '&nbsp;OR&nbsp;' +
                               '<hr class="op-or-label-divider"></ul>');

                let removeInputIcon = ('<li class="op-remove-inputs">' +
                                       '<button type="button" title="Delete this set of search inputs" \
                                       class="p-0 btn btn-small btn-link op-remove-inputs-btn"' +
                                       `data-widget="widget__${slug}" data-slug="${slug}">` +
                                       `<i class="${trashIcon}"></i></button></li>`);

                let numberOfInputSets = $(`#widget__${slug} .op-search-inputs-set`).length;
                if (numberOfInputSets > 1) {
                    $(`#widget__${slug} .op-search-inputs-set`).first().append(removeInputIcon);
                }

                $(`#widget__${slug} .op-extra-search-inputs`).append(removeInputIcon);
                $(`#widget__${slug} .op-search-inputs-set:not(:last)`).append(orLabel);

                // Add dummy items to the right of "-- OR --" to make it center.
                if (numberOfQtypeInputs !== 0) {
                    let qtypeItem = $(`#widget__${slug} .op-qtype-input:first`);
                    let qtypeHelperItem = $(`#widget__${slug} .op-range-qtype-helper:first`);
                    let [dummyItem1, dummyItem2] = o_widgets.createInvisibleDummyItems(slug);
                    if (dummyItem1) {
                        $(`#widget__${slug} .op-or-labels`).append(dummyItem1);
                        $(`#widget__${slug} .op-dummy-item1`).width(qtypeItem.width());
                    }
                    if (dummyItem2) {
                        $(`#widget__${slug} .op-or-labels`).append(dummyItem2);
                        $(`#widget__${slug} .op-dummy-item2`).width(qtypeHelperItem.width());
                    }
                }

                if ($(`#widget__${slug} .op-add-inputs`).length > 0) {
                    addInputIcon = $(`#widget__${slug} .op-add-inputs`).detach();
                }

                o_widgets.attachAddInputIcon(slug, addInputIcon);

                let widgetInputSets = $(`#widget__${slug} .op-search-inputs-set`);
                // Assign unique id for each input set. Inputs in the same set will have the same id.
                for (const eachInputSet of widgetInputSets) {
                    o_widgets.uniqueIdForInputs += 1;
                    $(eachInputSet).find("input").attr("data-uniqueid", o_widgets.uniqueIdForInputs);
                }
            }

            opus.widgetsDrawn.unshift(slug);
            o_widgets.customWidgetBehaviors(slug);
            o_widgets.scrollToWidget(widget);
            o_search.getHinting(slug);
            o_widgets.isGetWidgetDone = true;
        }); // end callback for .done()
    }, // end getWidget function

    renumberInputsAttributes: function(slug) {
        /**
         * Reorder all inputs attributes in numerical order when there
         * are multiple sets of search inputs in one single widget.
         */
        let widgetInputs = $(`#widget__${slug} input`);
        if (widgetInputs.hasClass("RANGE")) {
            let extraSearchInputs = $(`#widget__${slug} .op-extra-search-inputs`);
            let minRangeInputs = $(`#widget__${slug} input.op-range-input-min`);
            let maxRangeInputs = $(`#widget__${slug} input.op-range-input-max`);
            let qtypes = $(`#widget__${slug} .widget-main select`);

            let trailingCounter = 0;
            let trailingCounterString = "";
            let minInputNamesArray = [];

            let originalMinName = `${$(minRangeInputs).data("slugname")}1`;
            let originalMaxName = `${$(maxRangeInputs).data("slugname")}2`;
            let preprogrammedRangesInfo = $(`#widget__${slug} .op-preprogrammed-ranges`);
            // If there are extra sets of RANGE inputs, we reorder the following:
            // 1. name attribute for min & max inputs.
            // 2. attributes & id for customized ranges dropdown lists (this is required for them
            // to work properly).
            // 3. attributes for qtypes
            if (extraSearchInputs.length > 0) {
                // Renumber min inputs.
                // The data will be used to set as data-mininput for corresponding ranges collapsible
                // (categories) containers. That way each specific min input will be linked to its own
                // ranges info dropdown.
                minInputNamesArray = o_widgets.renumberAttributesOfSearchElements(minRangeInputs, true);

                // Renumber max inputs.
                o_widgets.renumberAttributesOfSearchElements(maxRangeInputs);

                // Renumber preprogrammed ranges dropdown.
                trailingCounter = 0;
                if (preprogrammedRangesInfo.length > 1) {
                    for (const eachRangeDropdown of preprogrammedRangesInfo) {
                        let rangesDropdownCategories = $(eachRangeDropdown).find("li");
                        trailingCounter++;
                        trailingCounterString = o_utils.convertToTrailingCounterStr(trailingCounter);
                        let correspondingMinInputName = minInputNamesArray.shift();

                        for (const category of rangesDropdownCategories) {
                            let originalDataCategory = $(category).attr("data-category");
                            originalDataCategory = o_utils.getSlugOrDataWithoutCounter(originalDataCategory);
                            let updatedDataCategory = `${originalDataCategory}_${trailingCounterString}`;

                            o_widgets.updateRangesCollapseAttributes(category, updatedDataCategory,
                                                                     correspondingMinInputName);
                        }
                    }
                }

                // Renumber qtypes
                o_widgets.renumberAttributesOfSearchElements(qtypes);
            } else {
                // When there is only one set of range input, remove the "_counter" trailing part.
                minRangeInputs.attr("name", originalMinName);
                maxRangeInputs.attr("name", originalMaxName);
                qtypes.attr("name", `qtype-${slug}`);
                if (preprogrammedRangesInfo.length > 0) {
                    let rangesDropdownCategories = preprogrammedRangesInfo.find("li");

                    for (const category of rangesDropdownCategories) {
                        let originalDataCategory = $(category).attr("data-category");
                        let updatedDataCategory = o_utils.getSlugOrDataWithoutCounter(originalDataCategory);

                        o_widgets.updateRangesCollapseAttributes(category, updatedDataCategory,
                                                                 originalMinName);
                    }
                }
            }
        } else if (widgetInputs.hasClass("STRING")) {
            let extraSearchInputs = $(`#widget__${slug} .op-extra-search-inputs`);
            let stringInputs = $(`#widget__${slug} input.STRING`);
            let qtypes = $(`#widget__${slug} .widget-main select`);

            let originalStringName = stringInputs.attr("name");
            originalStringName = o_utils.getSlugOrDataWithoutCounter(originalStringName);

            // If there are extra sets of STRING inputs, we reorder the following:
            // 1. name attribute inputs.
            // 2. attributes for qtypes
            if (extraSearchInputs.length > 0) {
                // Renumber string inputs.
                o_widgets.renumberAttributesOfSearchElements(stringInputs);

                // Renumber qtypes
                o_widgets.renumberAttributesOfSearchElements(qtypes);
            } else {
                // When there is only one set of string input, remove the "_counter" trailing part.
                stringInputs.attr("name", originalStringName);
                qtypes.attr("name", `qtype-${slug}`);
            }
        }
    },

    renumberAttributesOfSearchElements: function(targetSearchElements, returnRenumberedData=false) {
        /**
         * Renumber name attributes of inputs/qtypes (either RANGE or STRING inputs/qtypes),
         * and return the array renumbered data if returnRenumberedData.
         */
        let trailingCounter = 0;
        let trailingCounterString = "";
        let renumberedData = [];

        for (const eachSearchElement of targetSearchElements) {
            trailingCounter++;
            trailingCounterString = o_utils.convertToTrailingCounterStr(trailingCounter);
            let originalName = $(eachSearchElement).attr("name");
            originalName = o_utils.getSlugOrDataWithoutCounter(originalName);
            let updatedName = `${originalName}_${trailingCounterString}`;
            $(eachSearchElement).attr("name", updatedName);
            renumberedData.push(updatedName);
        }

        if (returnRenumberedData) {
            return renumberedData;
        } else {
            return;
        }
    },

    updateRangesCollapseAttributes: function(rangesCategory, updatedDataCategory, correspondingMinInput) {
        /**
         * Update related attributes for ranges info categories. These attributes
         * will make sure the collapsible can work properly and is correctly
         * connected to corresponding input.
         */
         $(rangesCategory).attr("data-category", updatedDataCategory);
        // This is used to connected each customized ranges dropdown to its
        // corresponding .op-range-input-min
        $(rangesCategory).attr("data-mininput", correspondingMinInput);

        let categoryBtn = $(rangesCategory).find("a");
        let itemsInOneCategory = $(rangesCategory).find(".container");
        categoryBtn.attr("href", `#${updatedDataCategory}`);
        categoryBtn.attr("aria-controls", updatedDataCategory);
        itemsInOneCategory.attr("id", updatedDataCategory);
        itemsInOneCategory.attr("data-mininput", correspondingMinInput);
    },

    scrollToWidget: function(widget) {
        // scrolls window to a widget
        // widget is like: "widget__" + slug
        //  scroll the widget panel to top
        $('#search').animate({
            scrollTop: $("#"+ widget).offset().top
        }, 1000);
    },

    alignRangesDataByDecimalPoint: function(widget) {
        /**
         * Align the data of ranges info by decimal point.
         */
        let preprogrammedRangesInfo = $(`#${widget} .op-scrollable-menu li`);
        for (const category of preprogrammedRangesInfo) {
            let collapsibleContainerId = $(category).attr("data-category");
            let rangesInfoInOneCategory = $(`#${collapsibleContainerId} .op-preprogrammed-ranges-data-item`);

            let maxNumOfDigitInMinDataFraction = 0;
            let maxNumOfDigitInMaxDataFraction = 0;

            for (const singleRangeData of rangesInfoInOneCategory) {

                // Special case: (maybe put this somewhere else if there are more and more long names)
                // Deal with long name, in our case, it's "Janus/Epimetheus Ring".
                // We set it the word-break to break-all.
                let rangesName = $(singleRangeData).data("name").toString();
                if (rangesName === "Janus/Epimetheus Ring") {
                    $(singleRangeData).find(".op-preprogrammed-ranges-data-name").addClass("op-word-break-all");
                }

                let minStr = $(singleRangeData).data("min").toString();
                let maxStr = $(singleRangeData).data("max").toString();
                let minIntegerPart = minStr.split(".")[0];
                let minFractionalPart = minStr.split(".")[1];
                let maxIntegerPart = maxStr.split(".")[0];
                let maxFractionalPart = maxStr.split(".")[1];

                minFractionalPart = minFractionalPart ? `.${minFractionalPart}` : "";
                maxFractionalPart = maxFractionalPart ? `.${maxFractionalPart}` : "";
                if (minFractionalPart) {
                    maxNumOfDigitInMinDataFraction = (Math.max(maxNumOfDigitInMinDataFraction,
                                                      minFractionalPart.length-1));
                }
                if (maxFractionalPart) {
                    maxNumOfDigitInMaxDataFraction = (Math.max(maxNumOfDigitInMaxDataFraction,
                                                      maxFractionalPart.length-1));
                }

                let minValReorg = `<span class="op-integer">${minIntegerPart}</span>` +
                                  `<span>${minFractionalPart}</span>`;
                let maxValReorg = `<span class="op-integer">${maxIntegerPart}</span>` +
                                  `<span>${maxFractionalPart}</span>`;

                $(singleRangeData).find(".op-preprogrammed-ranges-min-data").html(minValReorg);
                $(singleRangeData).find(".op-preprogrammed-ranges-max-data").html(maxValReorg);
            }

            // The following steps are to make sure ranges data are aligned properly with headers
            let minData = $(`#${collapsibleContainerId} .op-preprogrammed-ranges-min-data`);
            let rangesDataItem = $(`#${collapsibleContainerId} .op-preprogrammed-ranges-data-item`);
            let minDataPaddingVal = o_widgets.getPaddingValFromDigitsInFraction(maxNumOfDigitInMinDataFraction);
            let rangesDataItemPaddingVal = o_widgets.getPaddingValFromDigitsInFraction(maxNumOfDigitInMaxDataFraction);
            if (minDataPaddingVal) {
                minData.css("padding-right",`${minDataPaddingVal}em`);
            }
            if (rangesDataItemPaddingVal) {
                rangesDataItem.css("padding-right",`${rangesDataItemPaddingVal}em`);
            }
        }
    },

    getPaddingValFromDigitsInFraction: function(numOfDigits) {
        /**
         * Get padding-right values for ranges dropdown data from number of digits
         * in data fractions. Here is the mappings:
         * Num of digits in fraction    padding-right
         *          1                   1em
         *          2                   1.5em
         *          3                   2em
         * Note: currently we have at most 3 digits in data fractions.
         */
        switch(numOfDigits) {
            case 1:
                return 1;
            case 2:
                return 1.5;
            case 3:
                return 2;
            default:
                return 0;
        }
    },

    attachStringDropdownToInput: function() {
        /**
         * Make sure jquery ui autocomplete dropdown is attached right below
         * the corresponding input when browser is resized.
         */
        let autocompleteDropdown = $("ul.ui-autocomplete");
        for (const singleDropdown of autocompleteDropdown) {
            if ($(singleDropdown).find("li").length > 0 && $(singleDropdown).is(":visible")) {
                let slugWithCounter = $(singleDropdown).attr("data-input");

                let inputPosition = $(`input[name="${slugWithCounter}"]`).offset();
                let inputHeight = $(`input[name="${slugWithCounter}"]`).outerHeight();

                let autocompletePos = {left: inputPosition.left, top: inputPosition.top + inputHeight};
                $(singleDropdown).offset(autocompletePos);
                $(singleDropdown).width($(`input[name="${slugWithCounter}"]`).width());
            }
        }
    },

    destroyAutocomplete: function(slug) {
        if ($(`#widget__${slug} input.STRING`).autocomplete().length !== 0) {
            $(`#widget__${slug} input.STRING`).autocomplete("destroy");
        }
    },

    initAutocomplete: function(slug, slugWithCounter) {
        /**
         * If we have a string input widget open, initialize autocomplete
         * for string input
         */

        let displayDropDownList = true;

        let stringInputDropDown = $(`#widget__${slug} input[name="${slugWithCounter}"].STRING`).autocomplete({
            minLength: 1,
            source: function(request, response) {
                let currentValue = request.term;
                let inputCounter = o_utils.getSlugOrDataTrailingCounterStr(slugWithCounter);
                let idx = inputCounter ? parseInt(inputCounter)-1 : 0;

                o_widgets.lastStringSearchRequestNo++;
                o_search.slugStringSearchChoicesReqno[slugWithCounter] = o_widgets.lastStringSearchRequestNo;

                if (opus.selections[slug]) {
                    opus.selections[slug][idx] = currentValue;
                } else {
                    opus.selections[slug] = [currentValue];
                }

                let newHash = o_hash.getHashStrFromSelections();
                // // Make sure the existing STRING input value is not passed to stringsearchchoices
                // // API call. This will make sure each autocomplete dropdown results for individual
                // // input will not be affected by others.
                let hashArray = newHash.split("&");
                let newHashArray = [];
                for (const slugValuePair of hashArray) {
                    let slugParam = slugValuePair.split("=")[0];
                    if (slugParam === slugWithCounter || !slugParam.match(slug) ||
                        slugParam === `qtype-${slugWithCounter}`) {
                        newHashArray.push(slugValuePair);
                    }
                }
                newHash = newHashArray.join("&");

                // Avoid calling api when some inputs are not valid
                if (!opus.areRangeInputsValid()) {
                    return;
                }
                let url = `/opus/__api/stringsearchchoices/${slug}.json?` + newHash + "&reqno=" + o_widgets.lastStringSearchRequestNo;
                $.getJSON(url, function(stringSearchChoicesData) {
                    if (stringSearchChoicesData.reqno < o_search.slugStringSearchChoicesReqno[slugWithCounter]) {
                        return;
                    }

                    if (stringSearchChoicesData.full_search) {
                        o_search.searchMsg = "Results from entire database, not current search constraints";
                    } else {
                        o_search.searchMsg = "Results from current search constraints";
                    }

                    if (stringSearchChoicesData.choices.length !== 0) {
                        stringSearchChoicesData.choices.unshift(o_search.searchMsg);
                        o_search.searchResultsNotEmpty = true;
                    } else {
                        o_search.searchResultsNotEmpty = false;
                    }
                    if (stringSearchChoicesData.truncated_results) {
                        stringSearchChoicesData.choices.push(o_search.truncatedResultsMsg);
                    }

                    let hintsOfString = stringSearchChoicesData.choices;
                    o_search.truncatedResults = stringSearchChoicesData.truncated_results;
                    response(displayDropDownList ? hintsOfString : null);
                });
            },
            focus: function(e, ui) {
                return false;
            },
            select: function(e, ui) {
                slugWithCounter = $(e.target).attr("name");
                let displayValue = o_search.extractHtmlContent(ui.item.label);
                $(`input[name="${slugWithCounter}"]`).val(displayValue);
                $(`input[name="${slugWithCounter}"]`).trigger("change");
                return false;
            }
        })
        .keyup(function(e) {
            /*
            When "enter" key is pressed:
            (1) autocomplete dropdown list is closed
            (2) change event is triggered if input is an empty string
            */
            if (e.which === 13) {
                displayDropDownList = false;
                slugWithCounter = $(e.target).attr("name");
                $(`input[name="${slugWithCounter}"]`).autocomplete("close");
                let currentStringInputValue = $(`input[name="${slugWithCounter}"]`).val().trim();
                if (currentStringInputValue === "") {
                    $(`input[name="${slugWithCounter}"]`).trigger("change");
                }
            } else {
                displayDropDownList = true;
            }
        })
        .focusout(function(e) {
            slugWithCounter = $(e.target).attr("name");
            let currentStringInputValue = $(`input[name="${slugWithCounter}"]`).val().trim();
            if (currentStringInputValue === "") {
                $(`input[name="${slugWithCounter}"]`).trigger("change");
            }
        })
        .data("ui-autocomplete");

        // element with ui-autocomplete-category class will not be selectable
        let menuWidget = $(`input[name="${slugWithCounter}"].STRING`).autocomplete("widget");
        menuWidget.menu( "option", "items", "> :not(.ui-autocomplete-not-selectable)" );

        if (stringInputDropDown) {
            // Add header and footer for dropdown list
            stringInputDropDown._renderMenu = function(ul, items) {
                ul.attr("data-slug", slug);
                ul.attr("data-input", slugWithCounter);
                let self = this;
                $.each(items, function(index, item) {
                   self._renderItem(ul, item );
                });

                if (o_search.searchResultsNotEmpty) {
                    ul.find("li:first").addClass("ui-state-disabled ui-autocomplete-not-selectable");
                }
                if (o_search.truncatedResults) {
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
    },

    createInvisibleDummyItems: function(slug) {
        /**
         * Create invisible dummy items based on the existence of qtype and
         * qtype helper in a widget.
         */
        let qtypeItem = $(`#widget__${slug} .op-qtype-input:first`);
        let qtypeHelperItem = $(`#widget__${slug} .op-range-qtype-helper:first`);
        let dummyItem1 = (qtypeItem.length ?
                          '<li class="op-dummy-item1 op-visibility-hidden">&nbsp;</li>' : '');
        let dummyItem2 = (qtypeHelperItem.length ?
                          '<li class="op-dummy-item2 op-visibility-hidden">&nbsp;</li>' : '');
        return [dummyItem1, dummyItem2];
    }
};
