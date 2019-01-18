var o_collections = {
    /**
     *
     *  managing collections communication between server and client and
     *  all interaction on the collections tab
     *
     *  for the visual interaction on the browse table/gallery view when adding/removing
     *  from cart see browse.js
     *
     **/
     collectionBehaviors: function() {

        // collection details hide/show
         $("#collection").on("click", "#collection_summary_more", function() {
             if (opus.colls_options_viz) {
                 opus.colls_options_viz=false;
                 $("#collection_summary_more","#collection").text("show options");
                 $("#collection_summary","#collection").animate({height:"8em"});
             } else {
                 opus.colls_options_viz=true;
                 $("#collection_summary_more","#collection").text("hide options");
                 $("#collection_summary","#collection").animate({height:"33em"});
             }
             return false;
         });

         // check an input on selected products and images updates file_info
         $("#collection").on("click","#download_options input", function() {
             let add_to_url = o_collections.getDownloadFiltersChecked();
             let url = "/opus/__collections/download/info.json?" + add_to_url + "&fmt=json";
             $.getJSON(url, function(info) {
                 $("#total_files").fadeOut().html(info["download_count"]).fadeIn();
                 $("#total_download_size").fadeOut().html(info["download_size_pretty"]).fadeIn();
             });
         });

         // Download CSV button - create CSV file with currently chosen columns
         $("#collection").on("click", "#download_csv", function() {
             $(this).attr("href", "/opus/__collections/data.csv?"+ o_hash.getHash());
         });

         // Download Zipped Archive button - click create download zip file link on collections page
         $("#collection").on("click", "#collections_summary a#create_zip_file button", function() {
             $(".spinner", "#collections_summary").fadeIn();
             opus.download_in_process = true;
             let add_to_url = o_collections.getDownloadFiltersChecked();
             let url = "/opus/__collections/download.zip?" + add_to_url + "&" + o_hash.getHash();
             $.ajax({ url: url,
                 success: function(filename){
                     opus.download_in_process = false;
                     if (filename) {
                         $('<li><a href = "' + filename + '">' + filename + '</a></li>').hide().prependTo('ul.zipped_files', "#collections_summary").slideDown('slow');
                            $(".spinner", "#collections_summary").fadeOut();
                        } else {
                            $('<li>No Files Found</li>').hide().prependTo('ul.zipped_files', "#collections_summary").slideDown('fast');
                        }
                    },
                    error: function(e) {
                        $(".spinner", "#collections_summary").fadeOut();
                        $('<li>No Files Found</li>').hide().prependTo('ul.zipped_files', "#collections_summary").slideDown('fast');
                        opus.download_in_process = false;
                    }
                });
                return false;
         });

         // click create zip file link on detail page
         $("#detail").on("click", "#create_zip_file", function() {
             $('#zip_file', "#detail").html(opus.spinner + " zipping files");
             $.ajax({
                 url: $(this).attr("href"),
                 success: function(json) {
                     $('#zip_file').html('<a href = "' + json + '">' + json + '</a>');
                 }
             });
             return false;
         });

         // empty collection button
         $("#collection").on("click", "#empty_collection", function() {
             if (confirm("Are you sure you want to delete all observations in your cart?")) {
                 o_collections.emptyCollection();
             }
             return false;
         });
     },

     // download filters
     getDownloadFiltersChecked: function() {
         // returned as url string
         let product_types = [];
         let image_types = [];
         let add_to_url = [];
         $("ul#product_types input:checkbox:checked").each(function(){
             product_types.push($(this).val());
         });
         let checked_filters = {"types":product_types};

         for (let filter_name in checked_filters) {
             if (checked_filters[filter_name].length) {
                 add_to_url.push(filter_name + "=" + checked_filters[filter_name].join(','));
             }
        }
        return add_to_url.join('&');
     },

     adjustProductInfoHeight: function() {
         let container_height = $(window).height()-120;
         $("#collection .sidebar_wrapper").height(container_height);
         $("#collection .gallery-contents").height(container_height);
     },

     updateCartStatus: function(status) {
         if (status.reqno < opus.lastCartRequestNo) {
             return;
         }
         let count = status.count;
         $('#collection_count').html(count);
         if (status.download_size_pretty !== undefined) {
             $('#total_download_size').html(status.download_size_pretty);
         }
         opus.colls_pages = Math.ceil(count/opus.prefs.limit);
         o_collections.adjustProductInfoHeight();
     },


     // init an existing collection on page load
     initCollection: function() {
        // returns any user collection saved in session
        opus.lastCartRequestNo++;
        $.getJSON("/opus/__collections/status.json?reqno=" + opus.lastCartRequestNo, function(statusData) {
            o_collections.updateCartStatus(statusData);
        });
     },

     loadCollectionData: function (page) {
        //window.scrollTo(0,opus.browse_view_scrolls[opus.prefs.browse]);
        page = (page == undefined ? 1 : (opus.collection_change ? 1 : page));

        let view = o_browse.getViewInfo();
        let base_url = "/opus/__api/dataimages.json?";
        let url = o_hash.getHash() + '&reqno=' + opus.lastRequestNo + view.add_to_url;

        url = o_browse.updatePageInUrl(url, page);

        // metadata; used for both table and gallery
        $.getJSON(base_url + url, function(data) {
            if (opus.col_labels.length === 0) {
                opus.col_labels = data.columns;
            }
            o_browse.renderGalleryAndTable(data, this.url);

            if (opus.collection_change) {
                // for infinite scroll
                $('#collection .gallery-contents').infiniteScroll({
                    path: o_browse.updatePageInUrl(this.url, "{{#}}"),
                    responseType: 'text',
                    status: '#collection .page-load-status',
                    elementScroll: true,
                    history: false,
                    debug: false,
                });
                $('#collection .gallery-contents').on( 'load.infiniteScroll', function( event, response, path ) {
                    let jsonData = JSON.parse( response );
                    o_browse.renderGalleryAndTable(jsonData, path);
                });
                opus.collection_change = false;
            }
        });
    },

    // get Collections tab
    getCollectionsTab: function() {
        if (opus.collection_change) {
            var zipped_files_html = $('.zipped_files', "#collection").html();

            // don't forget to remove existing stuff before append
            $('.gallery', "#collection").html("");

            $('.collection_details', "#collection").html(opus.spinner);

            // reset page no
            opus.last_page_drawn['colls_gallery'] = 0;
            opus.last_page_drawn['colls_data'] = 0;

            // redux: and nix this big thing:
            $.ajax({ url: "/opus/__collections/view.html",
                success: function(html) {
                    // this div lives in the in the nav menu template
                    $('.collection_details', "#collection").hide().html(html).fadeIn();

                    if (opus.download_in_process) {
                        $(".spinner", "#collections_summary").fadeIn();
                    }

                    $('#colls_pages').html(opus.colls_pages);

                    o_collections.loadCollectionData();

                    if (zipped_files_html) {
                        $('.zipped_files', "#collection").html(zipped_files_html);
                    }
                    o_collections.adjustProductInfoHeight();
                }
            });
        }
    },

    emptyCollection: function() {
        // change indicator to zero and let the server know:
        // FIX ME - this is becoming a JSON
        $.ajax({ url: "/opus/__collections/reset.html",
            success: function(html){
                $("#collection_count").html("0");
                opus.colls_pages = 0;
                opus.collection_change = true;
                o_collections.getCollectionsTab();
            },
        });

        $(".thumbnail-container.in").removeClass("in");
        $("#dataTable input").prop("checked", false);
    },

    getGalleryElement: function(opusId) {
        return $("#" + opus.prefs.view+" .thumbnail-container[data-id=" + opusId + "]");
    },

    toggleInCollection: function(fromOpusId, toOpusId) {
        let fromElem = o_collections.getGalleryElement(fromOpusId);

        // handle it as range
        if (toOpusId != undefined) {
            let action = (fromElem.hasClass("in") ? "addrange" : "removerange");
            let collectionAction = (action == "addrange");
            let toElem = o_collections.getGalleryElement(toOpusId);
            let fromIndex = $(".thumbnail-container").index(fromElem);
            let toIndex = $(".thumbnail-container").index(toElem);

            // reorder if need be
            if (fromIndex > toIndex) {
                [fromIndex, toIndex] = [toIndex, fromIndex];
            }
            let length = toIndex - fromIndex+1;
            let namespace = o_browse.getViewInfo().namespace;
            let elementArray = $(namespace + " .thumbnail-container");
            let opusIdRange = $(elementArray[fromIndex]).data("id") + ","+ $(elementArray[toIndex]).data("id")
            console.log("end range "+action+" : "+opusIdRange);
            $.each(elementArray.splice(fromIndex, length), function(index, elem) {
                // effect no change if it is already selected/deselected same as first item in array
                if ($(elem).hasClass("in") != collectionAction) {
                    let opusId = $(elem).data("id");
                    $(elem).toggleClass("in");
                    // because this is a range, we need to check the boxes by hand
                    $("input[name="+opusId+"]").prop("checked", !$("input[name="+opusId+"]").is(":checked"));
                    console.log("changed: "+$(elem).data("id"));
                }
            });
            o_collections.editCollection(opusIdRange, action);
            o_browse.undoRangeSelect(namespace);
        } else {
            fromElem.toggleClass("in");
            let action = (fromElem.hasClass("in") ? "add" : "remove");
            o_collections.editCollection(fromOpusId, action);
        }
    },

    // action = add/remove/addrange/removerange/addall
    editCollection: function(opusId, action) {
        opus.collection_change = true;

        var viewInfo = o_browse.getViewInfo();
        var url = "/opus/__collections/" + action + ".json?";
        switch (action) {
            case "add":
            case "remove":
                url += "opus_id=" + opusId;
                break;

            case "removerange":
            case "addrange":
                url += "range=" + opusId;
                // need to send to server what page this range lands and what limit of that page is
                // limit should include all observations showing on page
                // must adjust limit + page to account for total number of results showing on page

                // server uses offset = (page_no-1)*limit
                // i.e. the offset of the 23rd page at 100 per page starts with the 2200st record:

                // first find what does opus.prefs.page say we are looking at:
                let prefix = viewInfo.prefix;       // either 'colls_' or ''
                let view_var = opus.prefs[prefix + 'browse'];  // either 'gallery' or 'data'

                let first_page = o_browse.getCurrentPage();
                let last_page = opus.last_page_drawn[prefix + view_var];

                // now find the number of results showing on the page, different from opus.prefs.limit:
                // number of "pages" showing on screen at any time = limit * (1+footer_clicks)
                // i.e., you've got 100 on screen, you click footer 4 times, now you've got 500 showing
                // multiply that by 2 because our results may span no more than 2 "pages" at our new limit on the server
                let limit = opus.prefs.limit * (last_page - first_page + 1);

                let hashArray = o_hash.getHashArray();
                if (hashArray.page !== undefined)
                    delete hashArray.page;
                if (hashArray.limit !== undefined)
                    delete hashArray.limit;

                url += '&' + o_hash.hashArrayToHashString(hashArray);
                url = url + "&limit=" + limit + "&page=" + first_page;
                break;

          case "addall":
              url += o_hash.getHash();
              break;
        }

        // Minor performance check - if we don't need a total download size, don't bother
        //Only the selection tab is interested in updating that count at this time.
        let add_to_url = "";
        if (opus.prefs.view == "collection") {
            add_to_url = "&download=1&" + o_collections.getDownloadFiltersChecked();
        }

        opus.lastCartRequestNo++;
        $.getJSON(url  + add_to_url + "&reqno=" + opus.lastCartRequestNo, function(statusData) {
            o_collections.updateCartStatus(statusData);
        });
    },
};
