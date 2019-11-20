/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $ */
/* globals opus, o_utils*/

/* jshint varstmt: false */
var o_hash = {
/* jshint varstmt: true */
    /**
     *
     *  changing, reading, and initiating a session from the browser hash
     *
     **/
    getHashStrFromSelections: function(useFieldUniqueIDs=false) {
        /**
         * Get the hash string from selections only. Hash string will be in alphabetical
         * & slug counter order. When useFieldUniqueIDs is set to true, it will create
         * the hash string with slugs + inputs' uniqueid, and it's used for normalize
         * input API call.
         */
        console.log(`getHashStrFromSelections`);
        let hash = [];
        let visited = {};

        let selectionsSlugArr = Object.keys(opus.selections).concat(Object.keys(opus.extras));
        //  sort in alphabetical order with case insensitive
        let sortedSlugs = selectionsSlugArr.sort(function(a, b) {
            let trailingCounterStr = "";
            a = o_hash.convertSlugForSorting(a);
            b = o_hash.convertSlugForSorting(b);
            if (a > b) {
                return 1;
            } else if (a < b) {
                return -1;
            } else {
                return 0;
            }
        });
        // let sortedSlugs = Object.keys(opus.selections).sort(function(a, b) {
        //     return a.localeCompare(b, 'en', {'sensitivity': 'base'});
        // });

        console.log(sortedSlugs);
        for (const slug of sortedSlugs) {
            if (visited[slug]) {
                continue;
            }
            let value = opus.selections[slug];
            if (value && value.length) {
                let encodedSelectionValues = o_hash.encodeSlugValues(value);
                let numberOfInputSets = encodedSelectionValues.length;
                let slugNoNum = slug.match(/.*(1|2)$/) ? slug.match(/(.*)[1|2]$/)[1] : slug;
                let qtypeSlug = `qtype-${slugNoNum}`;

                // If the slug has an array of more than 1 value, and it's either a STRING or RANGE input slug,
                // we attach the trailing counter string to the slug and assign the corresponding selection value
                // before pushing it into hash array.
                if (slug.match(/.*(1|2)$/)) { // RANGE inputs
                    let oppositeSuffixSlug = slug.match(/.*1$/) ? `${slugNoNum}2` : `${slugNoNum}1`;
                    let oppositeSuffixEncodedSelectionValues = (o_hash.encodeSlugValues(
                                                                opus.selections[oppositeSuffixSlug]));

                    let slug1 = slug;
                    let slug2 = oppositeSuffixSlug;
                    let slug1EncodedSelections = encodedSelectionValues;
                    let slug2EncodedSelections = oppositeSuffixEncodedSelectionValues;
                    if (slug.match(/.*2$/)) {
                        [slug1, slug2] = [slug2, slug1];
                        [slug1EncodedSelections, slug2EncodedSelections] = ([slug2EncodedSelections,
                                                                            slug1EncodedSelections]);
                    }

                    visited[slug1] = true;
                    visited[slug2] = true;

                    for (let trailingCounter = 1; trailingCounter <= numberOfInputSets; trailingCounter++) {
                        let trailingCounterString = o_utils.convertToTrailingCounterStr(trailingCounter);
                        let slug1WithCounter = (numberOfInputSets === 1) ? slug1 : `${slug1}_${trailingCounterString}`;
                        let slug2WithCounter = (numberOfInputSets === 1) ? slug2 : `${slug2}_${trailingCounterString}`;

                        if (useFieldUniqueIDs) {
                            let uniqueid1 = ($(`#widget__${slugNoNum} input[name="${slug1WithCounter}"]`)
                                             .attr("data-uniqueid"));
                            let uniqueid2 = ($(`#widget__${slugNoNum} input[name="${slug2WithCounter}"]`)
                                             .attr("data-uniqueid"));

                            if (uniqueid1) {
                                slug1WithCounter = `${slug1}_${uniqueid1}`;
                            }
                            if (uniqueid2) {
                                slug2WithCounter = `${slug2}_${uniqueid2}`;
                            }
                        }

                        if (opus.selections[slug1][trailingCounter-1] !== null) {
                            hash.push(slug1WithCounter + "=" + slug1EncodedSelections[trailingCounter-1]);
                        }
                        if (opus.selections[slug2][trailingCounter-1] !== null) {
                            hash.push(slug2WithCounter + "=" + slug2EncodedSelections[trailingCounter-1]);
                        }

                        if (qtypeSlug in opus.extras) {
                            visited[qtypeSlug] = true;
                            o_hash.updateHashFromExtras(hash, qtypeSlug, numberOfInputSets,
                                                        trailingCounter);
                        }

                    }
                } else if (`${qtypeSlug}` in opus.extras) { // STRING inputs
                    visited[slug] = true;
                    for (let trailingCounter = 1; trailingCounter <= numberOfInputSets; trailingCounter++) {
                        let trailingCounterString = o_utils.convertToTrailingCounterStr(trailingCounter);
                        let slugWithCounter = (numberOfInputSets === 1) ? slug : `${slug}_${trailingCounterString}`;

                        if (useFieldUniqueIDs) {
                            let uniqueid = ($(`#widget__${slugNoNum} input[name="${slugWithCounter}"]`)
                                            .attr("data-uniqueid"));
                            if (uniqueid) {
                                slugWithCounter = `${slug}_${uniqueid}`;
                            }
                        }

                        if (value[trailingCounter-1] !== null) {
                            hash.push(slugWithCounter + "=" + encodedSelectionValues[trailingCounter-1]);
                        }
                        if (qtypeSlug in opus.extras) {
                            visited[qtypeSlug] = true;
                            o_hash.updateHashFromExtras(hash, qtypeSlug, numberOfInputSets,
                                                        trailingCounter);
                        }
                    }
                } else { // Multi/single choice inputs
                    hash.push(slug + "=" + encodedSelectionValues.join(","));
                }
            } else { // qtypeSlug
                // For slugs only exist in extras, make sure they are updated in the hash.
                // This will make sure multiple empty input sets can show up after page reloads.
                let qtypeSlug = slug;
                if (visited[qtypeSlug]) {
                    continue;
                }
                let qtypeValue = opus.extras[qtypeSlug];
                if (qtypeValue.length) {
                    let encodedExtraValues = o_hash.encodeSlugValues(qtypeValue);

                    if (qtypeValue.length > 1) {
                        let numberOfQtypeInputs = encodedExtraValues.length;

                        for(let trailingCounter = 1; trailingCounter <= numberOfQtypeInputs; trailingCounter++) {
                            let trailingCounterString = o_utils.convertToTrailingCounterStr(trailingCounter);
                            let newKey = `${qtypeSlug}_${trailingCounterString}`;

                            if (qtypeValue[trailingCounter-1] !== null) {
                                hash.push(newKey + "=" + encodedExtraValues[trailingCounter-1]);
                            }
                        }
                    } else {
                        hash.push(qtypeSlug + "=" + encodedExtraValues.join(","));
                    }
                }
            }
        }

        // For slugs only exist in extras, make sure they are updated in the hash.
        // This will make sure multiple empty input sets can show up after page reloads.
        // for (const qtypeSlug in opus.extras) {
        //     if (visited[qtypeSlug]) {
        //         continue;
        //     }
        //     // let slugMatchObj = qtypeSlug.match(/qtype-(.*)$/);
        //     // let slugName = qtypeSlug.match(/qtype-(.*)$/) ? qtypeSlug.match(/qtype-(.*)$/)[1] : "";
        //     // if ((qtypeSlug.match(/qtype-(.*)$/)[1] in opus.selections ||
        //     //      `${qtypeSlug.match(/qtype-(.*)$/)[1]}1` in opus.selections ||
        //     //      `${qtypeSlug.match(/qtype-(.*)$/)[1]}2` in opus.selections)) {
        //     //     continue;
        //     // }
        //     let value = opus.extras[qtypeSlug];
        //     if (value.length) {
        //         let encodedExtraValues = o_hash.encodeSlugValues(value);
        //
        //         if (value.length > 1) {
        //             let numberOfQtypeInputs = encodedExtraValues.length;
        //
        //             for(let trailingCounter = 1; trailingCounter <= numberOfQtypeInputs; trailingCounter++) {
        //                 let trailingCounterString = o_utils.convertToTrailingCounterStr(trailingCounter);
        //                 let newKey = `${qtypeSlug}_${trailingCounterString}`;
        //
        //                 if (value[trailingCounter-1] !== null) {
        //                     hash.push(newKey + "=" + encodedExtraValues[trailingCounter-1]);
        //                 }
        //             }
        //         } else {
        //             hash.push(qtypeSlug + "=" + encodedExtraValues.join(","));
        //         }
        //     }
        // }

        console.log(hash);

        return hash.join("&");
    },

    convertSlugForSorting: function(slug) {
        /**
         * This function converts the slug for comparison in .sort callback function.
         */
        slug = slug.toLowerCase();
        let trailingCounter = "";
        if (slug.includes("_")) {
            let idx = slug.indexOf("_");
            trailingCounter = slug.slice(idx);
            slug = slug.slice(0, idx);
        }
        if (slug.startsWith("qtype-")) {
            slug = slug.slice(6) + "3";
        }
        slug += trailingCounter;
        return slug;
    },

    getHashStrFromOPUSPrefs: function() {
        /**
         * Get the hash string from opus.prefs
         */
        let hash = [];
        $.each(opus.prefs, function(key, value) {
            hash.push(key + "=" + value);
        });
        return hash.join("&");
    },

    getFullHashStr: function() {
        /**
         * Get the full hash string from search params and opus.prefs
         */
        let hashStrFromSelections = o_hash.getHashStrFromSelections();
        let hashStrFromOPUSPrefs =  o_hash.getHashStrFromOPUSPrefs();
        return (hashStrFromSelections ?
                hashStrFromSelections + "&" + hashStrFromOPUSPrefs : hashStrFromOPUSPrefs);
    },

    updateURLFromCurrentHash: function() {
        /**
         * Update URL with full hash string
         */
        console.log(`=== updateURLFromCurrentHash ===`);
        console.log(JSON.stringify(opus.selections));
        console.log(JSON.stringify(opus.extras));
        let fullHashStr = o_hash.getFullHashStr();
        console.log(fullHashStr.split("&"));
        window.location.hash = '/' + fullHashStr;
    },

    updateHashFromExtras: function(hash, qtypeInExtras, numberOfInputSets, counter) {
        /**
         * Update the hash with data from opus.extras. The function will take in
         * numberOfInputSets & counter to determine if trailingCounterString should
         * be added to the final slug in the hash.
         */
        let trailingCounterString = o_utils.convertToTrailingCounterStr(counter);
        let encodedExtraValues = o_hash.encodeSlugValues(opus.extras[qtypeInExtras]);
        let qtypeInURL = ((numberOfInputSets === 1) ?
                          qtypeInExtras : `${qtypeInExtras}_${trailingCounterString}`);
        if (opus.extras[qtypeInExtras][counter-1] !== null) {
            hash.push(qtypeInURL + "=" + encodedExtraValues[counter-1]);
        }
    },

    encodeSlugValues: function(slugValueArray) {
        /**
         * Take in a slug value array (like opus.selections, each element
         * will be a list of values for the slug) and encode all values in the
         * array. Return an array that contains encoded values for the
         * slug. This function will be called in getHashStrFromSelections to
         * make sure slug values in the hash are all encoded before updating
         * the URL.
         */
        let slugValue = [];
        for (const val of slugValueArray) {
            let value = encodeURIComponent(val);
            value = value.replace(/\%20/g, "+");
            // All ":" in the search string will be unencoded.
            value = value.replace(/\%3A/g, ":");

            slugValue.push(value);
        }

        return slugValue;
    },

    encodeHashArray: function(hashArray) {
        /**
         * Take in a hash array (each element will be "slug=value") and
         * encode the "value" of each element. Return a hash array that
         * consists of "slug=encodedValue". This function will be called
         * in opus.normalizedURLAPICall to make sure slug values from
         * new URL are encoded.
         */
        let hash = [];
        for (const pair of hashArray) {
            // Get the first idx of "=" sign and take all of string after the first
            // "=" as the value (or a list of values) for the slug.
            let idxOfFirstEqualSign = pair.indexOf("=");
            let slug = pair.slice(0, idxOfFirstEqualSign);
            let value = pair.slice(idxOfFirstEqualSign + 1);

            let valueArray = value.split(",");
            valueArray = o_hash.encodeSlugValues(valueArray);

            value = valueArray.join(",");

            hash.push(`${slug}=${value}`);
        }

        return hash;
    },

    decodeSlugValues: function(slugValueArray) {
        /**
         * Take in a slug value array (like opus.selections, each element
         * will be a list of values for the slug) and decode all values in the
         * array. Return an array that contains decoded values for the
         * slug. This function will be called in decodeHashArray to make sure
         * slug values in the hash are all decoded.
         */
        let slugValue = [];
        for (const val of slugValueArray) {
            let value = val.replace(/\+/g, "%20");
            value = decodeURIComponent(value);
            slugValue.push(value);
        }

        return slugValue;
    },

    decodeHashArray: function(hashArray) {
        /**
         * Take in a hash array (each element will be "slug=value") and
         * decode the "value" of each element. Return a hash array that
         * consists of "slug=decodedValue". This function will be called
         * in getSelectionsExtrasFromHash to make sure slug values in
         * selections and extras are decoded. And it will also be called
         * in initFromHash to make sure slug values in opus.selections are
         * decoded.
         */
        let hash = [];
        for (const pair of hashArray) {
            let idxOfFirstEqualSign = pair.indexOf("=");
            let slug = pair.slice(0, idxOfFirstEqualSign);
            let value = pair.slice(idxOfFirstEqualSign + 1);

            let valueArray = value.split(",");
            valueArray = o_hash.decodeSlugValues(valueArray);
            value = valueArray.join(",");

            hash.push(`${slug}=${value}`);
        }

        return hash;
    },

    // returns the hash part of the url minus the #/ symbol
    getHash: function() {
        try {
            if (window.location.hash) {
                return window.location.hash.match(/^#\/(.*)$/)[1];
            } else {
                return "";
            }
        } catch (e) {
            return "";
        }
    },

    getHashArray: function() {
        let hashArray = {};
        let hashInfo = o_hash.getHash();
        $.each(hashInfo.split('&'), function(index, valuePair) {
            let paramArray = valuePair.split("=");
            hashArray[paramArray[0]] = paramArray[1];
        });
        return hashArray;
    },

    hashArrayToHashString: function(hashArray) {
        let hash = "";
        $.each(hashArray, function(param, value) {
            hash += `&${param}=${value}`;
        });
        return hash.substring(1);   // don't forget to strip off the first &, it is not needed
    },

    // get both selections and extras (qtype) from hash.
    getSelectionsExtrasFromHash: function() {
        let hash = o_hash.getHash();
        if (!hash) {
            return [undefined, undefined];
        }

        hash = (hash.search('&') > -1 ? hash.split('&') : [hash]);
        hash = o_hash.decodeHashArray(hash);
        let selections = {};  // the new set of pairs that will not include the result_table specific session vars
        let extras = {}; // store qtype from url

        $.each(hash, function(index, pair) {
            let idxOfFirstEqualSign = pair.indexOf("=");
            let slug = pair.slice(0, idxOfFirstEqualSign);
            let value = pair.slice(idxOfFirstEqualSign + 1);

            if (!(slug in opus.prefs) && value) {
                let slugNoCounter = o_utils.getSlugOrDataWithoutCounter(slug);
                let slugCounter = o_utils.getSlugOrDataTrailingCounterStr(slug);
                slug = slugNoCounter;

                if (slugCounter > opus.maxAllowedInputSets) {
                    return; // continue to next iteration
                }

                if (slug.startsWith("qtype-")) {
                    if (slugCounter) {
                        slugCounter = parseInt(slugCounter);
                        extras[slug] = extras[slug] || [];
                        while (extras[slug].length < slugCounter) {
                            extras[slug].push(null);
                        }
                        extras[slug][slugCounter-1] = value;
                    } else {
                        // each qtype will only have one value at a time
                        extras[slug] = [value];
                    }
                } else {
                    // Leave comments here, need to revisit this later. We have find
                    // a better way to tell if the slug value is coming from string input.
                    // if ($(`input[name="${slug}"]`).hasClass("STRING")) {
                    //     selections[slug] = [value];
                    // } else {

                    if (slugCounter) {
                        slugCounter = parseInt(slugCounter);
                        selections[slug] = selections[slug] || [];
                        while (selections[slug].length < slugCounter) {
                            selections[slug].push(null);
                        }
                        selections[slug][slugCounter-1] = value;
                    } else {
                        selections[slug] = value.split(",");
                    }
                    // }
                }
            } else if (slug === "widgets" && value) {
                // Loop through widgets and check if there is any widget with RANGE or STRING input
                // but without qtype, we will put those in selections as well.
                $.each(value.split(","), function(idx, widgetSlug) {
                    o_hash.SyncUpWithOPUSSelectionsForWidgetsWithNoQtype(selections,
                                                                         extras, widgetSlug);
                });
            }
        });

        [selections, extras] = o_hash.alignDataInSelectionsAndExtras(selections, extras);

        return [selections, extras];
    },

    SyncUpWithOPUSSelectionsForWidgetsWithNoQtype: function(selections, extras, widgetSlug) {
        /**
         * Takes in a widgetSlug and check if the widget has STRING or RANGE input
         * without qtype, if so, sync up the opus.selections with selections.
         */
        if (`qtype-${widgetSlug}` in extras) {
            return;
        }

        let inputInAWidget = $(`#widget__${widgetSlug} input`);
        if (inputInAWidget.length === 0) {
            return;
        }

        // Sync up selections and opus.selections when a set of inputs is removed or added
        // so that page will not reload in these two cases.
        if (inputInAWidget.hasClass("RANGE")) {
            if (!(`${widgetSlug}1` in selections) && !(`${widgetSlug}2` in selections) &&
                !(`${widgetSlug}1` in opus.selections) && !(`${widgetSlug}2` in opus.selections)) {
                selections[`${widgetSlug}1`] = [null];
                selections[`${widgetSlug}2`] = [null];
                opus.selections[`${widgetSlug}1`] = [null];
                opus.selections[`${widgetSlug}2`] = [null];
            } else {
                selections[`${widgetSlug}1`] = selections[`${widgetSlug}1`] || [];
                selections[`${widgetSlug}2`] = selections[`${widgetSlug}2`] || [];

                opus.selections[`${widgetSlug}1`] = opus.selections[`${widgetSlug}1`] || [];
                opus.selections[`${widgetSlug}2`] = opus.selections[`${widgetSlug}2`] || [];

                let opusSelectionsLen1 = opus.selections[`${widgetSlug}1`].length;
                let opusSelectionsLen2 = opus.selections[`${widgetSlug}2`].length;
                // Sync up selections and opus.selections when a new set of input is added.
                while (selections[`${widgetSlug}1`].length < opusSelectionsLen1) {
                    selections[`${widgetSlug}1`].push(null);
                }
                while (selections[`${widgetSlug}2`].length < opusSelectionsLen2) {
                    selections[`${widgetSlug}2`].push(null);
                }
                // Sync up selections and opus.selections when a set of input is removed.
                while (selections[`${widgetSlug}1`].length > opusSelectionsLen1) {
                    selections[`${widgetSlug}1`].pop();
                }
                while (selections[`${widgetSlug}2`].length > opusSelectionsLen2) {
                    selections[`${widgetSlug}2`].pop();
                }
            }
        } else if (inputInAWidget.hasClass("STRING")) {
            if (!(widgetSlug in selections) && !(widgetSlug in opus.selections)) {
                selections[widgetSlug] = [null];
                opus.selections[widgetSlug] = [null];
            } else {
                selections[widgetSlug] = selections[widgetSlug] || [];
                opus.selections[widgetSlug] = opus.selections[widgetSlug] || [];


                let opusSelectionsLen = opus.selections[widgetSlug].length;
                // Sync up selections and opus.selections when a new set of input is added.
                while (selections[widgetSlug].length < opusSelectionsLen) {
                    selections[widgetSlug].push(null);
                }
                // Sync up selections and opus.selections when a set of input is removed.
                while (selections[widgetSlug].length > opusSelectionsLen) {
                    selections[widgetSlug].pop();
                }
            }
        }
    },

    extrasWithoutUnusedQtypes: function(selections, extras) {
        // If a qtype is present in extras but is not used in the search
        // selections, then don't include it at all. This is so that when we
        // compare selections and extras over time, a "lonely" qtype won't be
        // taken into account and trigger a new backend search.
        let newExtras = {};
        $.each(extras, function(slug, value) {
            if (slug.startsWith("qtype-")) {
                let qtypeSlug = slug.slice(6);
                if (qtypeSlug in selections ||
                    qtypeSlug+'1' in selections ||
                    qtypeSlug+'2' in selections) {
                    newExtras[slug] = value;
                }
            }
        });
        return newExtras;
    },

    initFromHash: function() {
        let hash = o_hash.getHash();
        if (!hash) {
            return;
        }

        hash = hash.split('&');
        hash = o_hash.decodeHashArray(hash);

        $.each(hash, function(index, pair) {
            let idxOfFirstEqualSign = pair.indexOf("=");
            let slug = pair.slice(0, idxOfFirstEqualSign);
            let value = pair.slice(idxOfFirstEqualSign + 1);

            if (value) {
                if (slug.match(/qtype-.*/)) {
                    let slugNoCounter = o_utils.getSlugOrDataWithoutCounter(slug);
                    let slugCounter = o_utils.getSlugOrDataTrailingCounterStr(slug);
                    slug = slugNoCounter;

                    if (slugCounter > opus.maxAllowedInputSets) {
                        return; // continue to next iteration
                    }

                    if (slugCounter) {
                        slugCounter = parseInt(slugCounter);
                        opus.extras[slug] = opus.extras[slug] || [];
                        while (opus.extras[slug].length < slugCounter) {
                            opus.extras[slug].push(null);
                        }
                        opus.extras[slug][slugCounter-1] = value;
                    } else {
                        // range drop down, add the qtype to the global extras array
                        let id = slug.match(/qtype-(.*)/)[1];
                        opus.extras['qtype-' + id] = value.split(',');
                    }
                }
                // look for prefs
                else if (slug in opus.prefs) {
                    switch (slug) {
                        case "widgets":
                            opus.prefs[slug] = value.replace(/\s+/g, '').split(',');
                            break;
                        case "page":
                            // page is no longer supported and should have been normalized out
                            break;
                        case "limit":
                            // limit is no longer supported and is calculated based on screen size, so ignore this param
                            break;
                        case "cols":
                            opus.prefs[slug] = value.split(',');
                            break;
                        case "order":
                            opus.prefs[slug] = value.split(',');
                            break;
                        case "startobs":
                        case "cart_startobs":
                            // Make sure cart_startobs is stored as integer in opus.prefs
                            opus.prefs[slug] = parseInt(value);
                            break;
                        default:
                            opus.prefs[slug] = value;
                    }
                } else {
                    // Leave comments here, need to revisit this later. We have find
                    // a better way to tell if the slug value is coming from string input.
                    // these are search params/value!
                    // if ($(`input[name="${slug}"]`).hasClass("STRING")) {
                    //     opus.selections[slug] = [value];
                    // } else {
                    let slugNoCounter = o_utils.getSlugOrDataWithoutCounter(slug);
                    let slugCounter = o_utils.getSlugOrDataTrailingCounterStr(slug);
                    slug = slugNoCounter;

                    if (slugCounter > opus.maxAllowedInputSets) {
                        return; // continue to next iteration
                    }

                    if (slugCounter) {
                        slugCounter = parseInt(slugCounter);
                        opus.selections[slug] = opus.selections[slug] || [];
                        while (opus.selections[slug].length < slugCounter) {
                            opus.selections[slug].push(null);
                        }
                        opus.selections[slug][slugCounter-1] = value;
                    } else {
                        opus.selections[slug] = value.split(",");
                    }
                    // }
                }
            }
        });

        [opus.selections, opus.extras] = o_hash.alignDataInSelectionsAndExtras(opus.selections, opus.extras);

        opus.load();
    },

    alignDataInSelectionsAndExtras: function(selectionsData, extrasData) {
        /**
         * Arrange data arrays in selections and extras. Make them the same
         * length if they are related to the same slug. For example:
         * Arrays for slugNameA1, slugNameA2, and qtype-slugNameA will be the
         * same length (RANGE input).
         * Arrays for slugNameB and qtype-slugNameB will be the same length
         * (STRING input).
         */
        let selections = o_utils.deepCloneObj(selectionsData);
        let extras = o_utils.deepCloneObj(extrasData);
        let rangeQtypeDefaultVal = "any";
        let strQtypeDefaultVal = "contains";
        for (const slug in selections) {
            if (slug.match(/.*(1|2)$/)) {
                let slugNoNum = slug.match(/.*(1|2)$/) ? slug.match(/(.*)[1|2]$/)[1] : slug;
                let qtypeSlug = `qtype-${slugNoNum}`;
                selections[`${slugNoNum}1`] = selections[`${slugNoNum}1`] || [];
                selections[`${slugNoNum}2`] = selections[`${slugNoNum}2`] || [];
                let longestLength = (Math.max(selections[`${slugNoNum}1`].length,
                                              selections[`${slugNoNum}2`].length));
                if (qtypeSlug in extras) {
                    longestLength = (Math.max(selections[`${slugNoNum}1`].length,
                                              selections[`${slugNoNum}2`].length,
                                              extras[qtypeSlug].length));
                }

                while (selections[`${slugNoNum}1`].length < longestLength) {
                    selections[`${slugNoNum}1`].push(null);
                }
                while (selections[`${slugNoNum}2`].length < longestLength) {
                    selections[`${slugNoNum}2`].push(null);
                }
                if (qtypeSlug in extras) {
                    while (extras[qtypeSlug] && extras[qtypeSlug] < longestLength) {
                        extras[qtypeSlug].push(rangeQtypeDefaultVal);
                    }
                }
            } else {
                let qtypeSlug = `qtype-${slug}`;
                if (qtypeSlug in extras) {
                    selections[slug] = selections[slug] || [];
                    extras[qtypeSlug] = extras[qtypeSlug] || [];
                    let longestLength = Math.max(selections[slug].length, extras[qtypeSlug].length);

                    while (selections[slug].length < longestLength) {
                        selections[slug].push(null);
                    }
                    while (extras[qtypeSlug] && extras[qtypeSlug] < longestLength) {
                        extras[qtypeSlug].push(strQtypeDefaultVal);
                    }
                }
            }
        }

        // When slug in selections is empty but qtype-slug in extras exists, we will also
        // make sure data in selections and extras are aligned.
        for (const qtypeSlug in extras) {
            if ((qtypeSlug.match(/qtype-(.*)$/)[1] in selections ||
                 `${qtypeSlug.match(/qtype-(.*)$/)[1]}1` in selections ||
                 `${qtypeSlug.match(/qtype-(.*)$/)[1]}2` in selections)) {
                continue;
            }
            let slug = qtypeSlug.match(/qtype-(.*)$/)[1];
            let longestLength = extras[qtypeSlug].length;

            if ($(`#widget__${slug} .op-search-inputs-set input`).hasClass("RANGE")) {
                selections[`${slug}1`] = selections[`${slug}1`] || [];
                selections[`${slug}2`] = selections[`${slug}2`] || [];
                while (selections[`${slug}1`].length < longestLength) {
                    selections[`${slug}1`].push(null);
                }
                while (selections[`${slug}2`].length < longestLength) {
                    selections[`${slug}2`].push(null);
                }
            } else if ($(`#widget__${slug} .op-search-inputs-set input`).hasClass("STRING")) {
                selections[slug] = selections[slug] || [];
                while (selections[slug].length < longestLength) {
                    selections[slug].push(null);
                }
            }
        }

        return [selections, extras];
    }
};
