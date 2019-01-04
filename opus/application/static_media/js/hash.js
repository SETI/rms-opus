var o_hash = {
    /**
     *
     *  changing, reading, and initiating a session from the browser hash
     *
     **/

    // updates the hash according to user selections
    updateHash: function(updateURL=true){

        hash = [];
        for (var param in opus.selections) {
            if (opus.selections[param].length){
                hash[hash.length] = param + '=' + opus.selections[param].join(',').replace(/ /g,'+');
            }
        }

        o_widgets.pauseWidgetControlVisibility(opus.selections);

        for (var key in opus.extras) {

            try {
                hash[hash.length] = key + '=' + opus.extras[key].join(',');
            } catch(e) {
                // oops not an arr
                hash[hash.length] = key + '=' + opus.extras[key];
            }
        }
        for (key in opus.prefs) {

            switch (key) {
                case 'page':
                    // page is stored like {"gallery":1, "data":1, "colls_gallery":1, "colls_data":1 }
                    // so the curent page depends on the view being shown
                    // opus.prefs.view = search, browse, collection, or detail
                    // opus.prefs.browse =  'gallery' or 'data',
                    page = o_browse.getCurrentPage();

                    hash[hash.length] = 'page=' + page;
                    break;

                case 'widget_size':
                    for (slug in opus.prefs[key]) {
                        hash[hash.length] = o_widgets.constructWidgetSizeHash(slug);
                    }
                    break;

                case 'widget_scroll':
                    // these are prefs having to do with widget resize and scrolled
                    break; // there's no scroll without size, so we handle scroll when size comes thru


                default:
                    hash[hash.length] = key + '=' + opus.prefs[key];
            }
        }
        if(updateURL) {
            window.location.hash = '/' + hash.join('&');
        }

        return hash.join('&');
    },

    // returns the hash part of the url minus the #/ symbol
    getHash: function(){
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
        var hashArray = [];
        $.each(this.getHash().split('&'), function(index, valuePair) {
            var paramArray = valuePair.split("=");
            hashArray[paramArray[0]] = paramArray[1];
        });
        return hashArray;
    },

    hashArrayToHashString: function(hashArray) {
        var hash = "";
        for (var param in hashArray) {
            hash += "&"+param+"="+hashArray[param];
        }
        return hash;
    },

    // part is part of the hash, selections or prefs
    getSelectionsFromHash: function() {
        var hash = o_hash.getHash();
        var pairs;
        if (!hash) return;

        if (hash.search('&') > -1) {
            pairs = hash.split('&');
        }
        else pairs = [hash];
        var selections = {};  // the new set of pairs that will not include the result_table specific session vars

        for (var i=0;i< pairs.length;i++) {
            var param = pairs[i].split('=')[0];
            var value = pairs[i].split('=')[1];
            if (!param) continue;
            if (!(param in opus.prefs) && !param.match(/sz-.*/)) {

            if (param in selections) {
                selections[param].push(value);
            } else {
                selections[param] = [value];
                }
            } else {
                if (param  == 'qtype-phase') {}
            }
        }
        if (!jQuery.isEmptyObject(selections)) {
            return selections;
        }

    },


    initFromHash: function(){
        var hash = o_hash.getHash();
        if (!hash) { return; }
        // first are any custom widget sizes in the hash?
        // just updating prefs here..
        hash = hash.split('&');

        for (var q in hash) {

            slug = hash[q].split('=')[0];
            value = hash[q].split('=')[1];

            if (slug.match(/sz-.*/)) {
                var id = slug.match(/sz-(.*)/)[1];
                // opus.extras['sz-' + id] = value;
                opus.prefs.widget_size[id] = value.split('+')[0];

                if (value.split('+')[1])
                    opus.prefs.widget_scroll[id] = value.split('+')[1];
            }
            else if (slug.match(/qtype-.*/)) {
                // range drop down, add the qtype to the global extras array
                var id = slug.match(/qtype-(.*)/)[1];
                opus.extras['qtype-' + id] = value.split(',');
            }
            // look for prefs
            else if (slug in opus.prefs) {

                if (slug == 'widgets' || slug == 'widgets2') {
                    if (value) {
                        opus.prefs[slug] = value.replace(/\s+/g, '').split(',');
                    }
                } else if (slug == 'page') {
                    if (value) {
                        opus.prefs.page['gallery'] = parseInt(value, 10);
                        opus.prefs.page['data'] = parseInt(value, 10);
                    }
                } else if (slug == 'limit') {
                    if (value) {
                        opus.prefs[slug] = parseInt(value, 10);
                    }
                } else if (slug=='cols') {
                    if (value) {
                        opus.prefs[slug] = value.split(',');
                    }
                }
                else if (value) {
                        opus.prefs[slug] = value;
                }

            } else {
                // these are search params/value!
                if (value) {
                    opus.selections[slug] = value.replace(/\+/g, " ").split(',');
                }
            }
        }

        // despite what the url says, make sure every widget that is constrained is actually visible
        for (slug in opus.selections) {
          if ($.inArray(slug, opus.prefs['widgets']) < 0) {
            // this slug is constrained in selections but is not
            // found in widgets, but do some extra checking for
            // range widgets:

            if (slug.indexOf('2') !== -1) {
              // range widges are represented by a single param and that's
              // the first param in the range, but this is the 2nd
              // let's see if the first half of this range is constrained
              slug_no_num = slug.slice(0, -1)
              if ($.inArray(slug_no_num, opus.prefs['widgets']) >= 0
                  ||
                 $.inArray(slug_no_num + '1', opus.prefs['widgets']) >= 0) {
                   // the first half of this range is found in widgets
                   // so nothing to do
                   continue;
                 } else {
                   // the first half of this range is constrained by selections
                   // but NOT found in widgets, so we add it, but don't
                   // add the param with the '2' index, only add the first
                   // '1' indexed param
                   slug = slug_no_num + '1'
                 }
            }

            opus.prefs['widgets'].push(slug);
          }
        }

        if (!jQuery.isEmptyObject(opus.last_selections)) {
            opus.load();
        }
    },


};
