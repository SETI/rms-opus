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
                hash.push(param + "=" + opus.selections[param].join(",").replace(/ /g,"+"));
            }
        }

        for (let key in opus.extras) {
            try {
                hash.push(key + "=" + opus.extras[key].join(","));
            } catch(e) {
                // oops not an arr
                hash.push(key + "=" + opus.extras[key]);
            }
        }
        $.each(opus.prefs, function(key, value) {
                switch (key) {
                    case "browse":
                        value = (value == "dataTable" ? "data" : value);
                        hash.push(key + "=" + value);
                        break;

                    default:
                        hash.push(key + "=" + opus.prefs[key]);
                }
            }
        );

        if (updateURL) {
            window.location.hash = '/' + hash.join('&');
        }

        return hash.join("&");
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
                    selections[slug] = value.replace("+", " ").split(",");
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
                        case "browse":
                            opus.prefs[slug] = (value == "data" ? "dataTable" : value);
                            break;
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
                        default:
                            opus.prefs[slug] = value;
                    }
                } else {
                    // these are search params/value!
                    opus.selections[slug] = value.replace(/\+/g, " ").split(',');
                }
            }
        });

        opus.load();
    },


};
