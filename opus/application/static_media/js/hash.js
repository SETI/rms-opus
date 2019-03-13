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
                hash.push(param + "=" + opus.selections[param].join(",").replace(/ /g,"+"));
            }
        }

        o_widgets.pauseWidgetControlVisibility(opus.selections);

		for (var key in opus.extras) {
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

				case "page":
					// page is stored like {"gallery":1, "data":1, "colls_gallery":1, "colls_data":1 }
					// so the curent page depends on the view being shown
					// opus.prefs.view = search, browse, cart, or detail
					// opus.prefs.browse =  'gallery' or 'dataTable',
					page = o_browse.getCurrentPage();
					hash.push("page=" + page);
					break;

                case 'widget_size':
                    for (slug in opus.prefs[key]) {
                        hash.push(o_widgets.constructWidgetSizeHash(slug));
                    }
                    break;

                case 'widget_scroll':
                    // these are prefs having to do with widget resize and scrolled
                    break; // there's no scroll without size, so we handle scroll when size comes thru

                default:
                    hash.push(key + "=" + opus.prefs[key]);
            }
        }
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
        var hashArray = [];
        // this is a workaround for firefox
        // when user hit enter in input#page, the url hash will be "", we will remove input#page eventually
        let hashInfo = this.getHash() ? this.getHash() : o_browse.tempHash;
        $.each(hashInfo.split('&'), function(index, valuePair) {
            var paramArray = valuePair.split("=");
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
        if (!hash) return;

        hash = (hash.search('&') > -1 ? hash.split('&') : [hash]);
        var selections = {};  // the new set of pairs that will not include the result_table specific session vars

        $.each(hash, function(index, pair) {
            let slug = pair.split('=')[0];
            let value = pair.split('=')[1];

            if (!(slug in opus.prefs) && !slug.match(/sz-.*/) && value) {
                if (slug in selections) {
                    selections[slug].push(value);
                } else {
                    selections[slug] = [value];
                }
            }
        });

        if (!$.isEmptyObject(selections)) {
            return selections;
        }
    },


    initFromHash: function() {
        let hash = o_hash.getHash();
        if (!hash) return;
        // first are any custom widget sizes in the hash?
        // just updating prefs here..
        hash = hash.split('&');

        $.each(hash, function(index, pair) {
            let slug = pair.split('=')[0];
            let value = pair.split('=')[1];
            if (value) {
                if (slug.match(/sz-.*/)) {
                    let id = slug.match(/sz-(.*)/)[1];
                    // opus.extras['sz-' + id] = value;
                    opus.prefs.widget_size[id] = value.split('+')[0];

                    if (value.split('+')[1])
                        opus.prefs.widget_scroll[id] = value.split('+')[1];
                }
                else if (slug.match(/qtype-.*/)) {
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
                            opus.prefs.page['gallery'] = parseInt(value, 10);
                            opus.prefs.page['data'] = parseInt(value, 10);
                            break;
                        case "limit":
                            opus.prefs[slug] = parseInt(value, 10);
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

        // despite what the url says, make sure every widget that is constrained is actually visible
        //$.each(opus.selections, function(index, slug) { })
        for (slug in opus.selections) {
          if ($.inArray(slug, opus.prefs.widgets) < 0) {
            // this slug is constrained in selections but is not
            // found in widgets, but do some extra checking for
            // range widgets:

            if (slug.indexOf('2') !== -1) {
              // range widges are represented by a single param and that's
              // the first param in the range, but this is the 2nd
              // let's see if the first half of this range is constrained
              slug_no_num = slug.slice(0, -1)
              if ($.inArray(slug_no_num, opus.prefs.widgets) >= 0
                  ||
                 $.inArray(slug_no_num + '1', opus.prefs.widgets) >= 0) {
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

            opus.prefs.widgets.push(slug);
          }
        }
        opus.load();
    },


};
