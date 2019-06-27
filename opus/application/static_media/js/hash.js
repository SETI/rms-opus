/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $ */
/* globals opus */

/* jshint varstmt: false */
var o_hash = {
/* jshint varstmt: true */
    /**
     *
     *  changing, reading, and initiating a session from the browser hash
     *
     **/

    // updates the hash according to user selections
    updateHash: function(updateURL=true) {
        let hash = [];
        for (let param in opus.selections) {
            if (opus.selections[param].length) {
                let encodedSelectionValues = o_hash.encodeSlugValue(opus.selections[param]);
                hash.push(param + "=" + encodedSelectionValues.join(","));
            }
        }

        for (let key in opus.extras) {
            let encodedExtraValues = o_hash.encodeSlugValue(opus.extras[key]);
            try {
                hash.push(key + "=" + encodedExtraValues.join(","));
            } catch(e) {
                // oops not an arr
                hash.push(key + "=" + encodedExtraValues);
            }
        }
        $.each(opus.prefs, function(key, value) {
            hash.push(key + "=" + value);
        });

        if (updateURL) {
            window.location.hash = '/' + hash.join('&');
        }

        return hash.join("&");
    },

    encodeSlugValue: function(slugValueArray) {
        /**
         * Take in a slug value array (like opus.selections, each element
         * will be a value for the slug) and encode all values in the
         * array. Return an array that contains encoded values for the
         * slug. This function will be called in updateHash to make sure
         * slug values in the hash are all encoded before updating the URL.
         */
        let slugValue = [];
        $.each(slugValueArray, function(index, val) {
            let value = encodeURIComponent(val);
            value = value.replace(/\%20/g, "+");
            slugValue.push(value);
        });

        return slugValue;
    },

    encodeHashArray: function(hashArray) {
        /**
         * Take in a hash array (each element will be "slug=value") and
         * encode the "value" of each element. Return a hash array that
         * is consist of "slug=encodedValue". This function will be called
         * in opus.normalizedURLAPICall to make sure slug values from
         * new URL are decoded.
         */
        let hash = [];
        $.each(hashArray, function(index, pair) {
            let slug = pair.split('=')[0];
            let value = pair.split('=')[1];
            value = encodeURIComponent(value);
            value = value.replace(/\%20/g, "+");
            hash.push(`${slug}=${value}`);
        });

        return hash;
    },

    decodeHashArray: function(hashArray) {
        /**
         * Take in a hash array (each element will be "slug=value") and
         * decode the "value" of each element. Return a hash array that
         * is consist of "slug=decodedValue". This function will be called
         * in getSelectionsExtrasFromHash to make sure slug values in
         * selections and extras are decoded. And it will also be called
         * in initFromHash to make sure slug values in opus.selections are
         * decoded.
         */
        // console.log(`=== hash from decodeHashArray ===`);
        let hash = [];
        $.each(hashArray, function(index, pair) {
            let slug = pair.split('=')[0];
            let value = pair.split('=')[1];
            value = value.replace(/\+/g, "%20");
            value = decodeURIComponent(value);
            hash.push(`${slug}=${value}`);
        });

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
        let hashArray = [];
        let hashInfo = o_hash.getHash();
        $.each(hashInfo.split('&'), function(index, valuePair) {
            let paramArray = valuePair.split("=");
            hashArray[paramArray[0]] = paramArray[1];
        });
        return hashArray;
    },

    hashArrayToHashString: function(hashArray) {
        let hash = "";
        for (let param in hashArray) {
            hash += "&"+param+"="+hashArray[param];
        }
        return hash;
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
            let slug = pair.split('=')[0];
            let value = pair.split('=')[1];

            if (!(slug in opus.prefs) && value) {
                if (slug.startsWith("qtype-")) {
                    // each qtype will only have one value at a time
                    extras[slug] = [value];
                } else {
                    // If value contains ", ", it's one value from string input.
                    if (value.includes(", ")) {
                        selections[slug] = [value];
                    } else {
                        selections[slug] = value.split(",");
                    }
                }
            }
        });

        return [selections, extras];
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
        // first are any custom widget sizes in the hash?
        // just updating prefs here..
        hash = hash.split('&');
        hash = o_hash.decodeHashArray(hash);
        $.each(hash, function(index, pair) {
            let slug = pair.split('=')[0];
            let value = pair.split('=')[1];
            if (value) {
                if (slug.match(/qtype-.*/)) {
                    // range drop down, add the qtype to the global extras array
                    let id = slug.match(/qtype-(.*)/)[1];
                    opus.extras['qtype-' + id] = value.split(',');
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
                    // these are search params/value!
                    // revisit here !!!
                    // opus.selections[slug] = value.replace(/\+/g, " ").split(',');
                    opus.selections[slug] = value.split(',');
                }
            }
        });

        opus.load();
    },


};
