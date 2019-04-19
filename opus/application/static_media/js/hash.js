/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $ */
/* globals o_browse, opus */

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
        // console.log("hash from hash.js");
        // console.log(hash);
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
        // this is a workaround for firefox
        // when user hit enter in input#page, the url hash will be "", we will remove input#page eventually
        let hashInfo = this.getHash() ? this.getHash() : o_browse.tempHash;
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

    // part is part of the hash, selections or prefs
    getSelectionsFromHash: function() {
        let hash = o_hash.getHash();
        if (!hash) {
            return;
        }

        hash = (hash.search('&') > -1 ? hash.split('&') : [hash]);
        let selections = {};  // the new set of pairs that will not include the result_table specific session vars
        $.each(hash, function(index, pair) {
            let slug = pair.split('=')[0];
            let value = pair.split('=')[1];

            if (!(slug in opus.prefs) && value) {
                if (slug in selections) {
                    selections[slug].push(value);
                } else {
                    selections[slug] = [value];
                }
            }
        });

        return selections;
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
