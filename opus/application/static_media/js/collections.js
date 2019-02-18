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
         // nav bar
         $("#collection").on("click", ".download_csv", function(e) {
             window.open(`/opus/__collections/data.csv?${o_hash.getHash()}`, '_blank');
             //$(this).attr("href", "/opus/__collections/data.csv?"+ o_hash.getHash());
         });

         $("#collection").on("click", ".downloadData", function(e) {
             o_collections.downloadZip("create_zip_data_file", "Internal error creating data zip file");
         });

         $("#collection").on("click", ".downloadURL", function(e) {
             o_collections.downloadZip("create_zip_url_file", "Internal error creating URL zip file");
         });
         $("#collection").on("click", ".metadataModal", function(e) {

         });
         $("#collection").on("click", ".emptyCart", function() {
             if (confirm("Are you sure you want to delete all observations in your cart?")) {
                 o_collections.emptyCollection();
             }
         });

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
             let url = "/opus/__collections/view.json?" + add_to_url + "&fmt=json";
             $.getJSON(url, function(info) {
                 $("#total_download_count").fadeOut().html(info.total_download_count).fadeIn();
                 $("#total_download_size").fadeOut().html(info.total_download_size_pretty).fadeIn();
             });
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

     downloadZip: function(type, errorMsg) {
         if (opus.download_in_process) {
             return false;
         }
         $("#download_links").show();
         opus.download_in_process = true;
         $(".spinner", "#download_links").fadeIn().css("display","inline-block");

         let add_to_url = o_collections.getDownloadFiltersChecked();
         let url = "/opus/__collections/download.json?" + add_to_url + "&" + o_hash.getHash();
         url += (type = "create_zip_url_file" ? "&urlonly=1" : "");
         $.ajax({
             url: url,
             dataType: "json",
             success: function(data){
                 if (data.error !== undefined) {
                     $(`<li>${data.error}</li>`).hide().prependTo("ul.zippedFiles", "#collections_summary").slideDown("fast");
                 } else {
                     $(`<li><a href = "${data.filename}">${data.filename}</a></li>`).hide().prependTo("ul.zippedFiles", "#collections_summary").slideDown("slow");
                 }
                 $(".spinner", "#download_links").fadeOut();
             },
             error: function(e) {
                 $(".spinner", "#download_links").fadeOut();
                 $(`<li>${errorMsg}</li>`).hide().prependTo("ul.zippedFiles", "#collections_summary").slideDown("fast");
             },
             complete: function() {
                 opus.download_in_process = false;
             }
         });
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
         $("#collection_count").html(count);
         if (status.total_download_size_pretty !== undefined) {
             $("#total_download_size").html(status.total_download_size_pretty);
             $("#total_download_count").fadeOut().html(status.total_download_count).fadeIn();
             $("#total_download_size").fadeOut().html(status.total_download_size_pretty).fadeIn();
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
        let url = o_hash.getHash() + "&reqno=" + opus.lastRequestNo + view.add_to_url;

        url = o_browse.updatePageInUrl(url, page);

        // metadata; used for both table and gallery
        $.getJSON(base_url + url, function(data) {
            if (opus.col_labels.length === 0) {
                opus.col_labels = data.columns;
            }
            o_browse.renderGalleryAndTable(data, this.url);
            o_browse.updateSortOrder(data);

            if (opus.collection_change) {
                // for infinite scroll
                $("#collection .gallery-contents").infiniteScroll({
                    path: o_browse.updatePageInUrl(this.url, "{{#}}"),
                    responseType: "text",
                    status: "#collection .page-load-status",
                    elementScroll: true,
                    history: false,
                    debug: false,
                });
                $("#collection .gallery-contents").on( "load.infiniteScroll", function( event, response, path ) {
                    let jsonData = JSON.parse( response );
                    o_browse.renderGalleryAndTable(jsonData, path);
                });
                opus.collection_change = false;
            }
        });
    },

    // get Collections tab
    getCollectionsTab: function() {
        o_browse.renderMetadataSelector();   // just do this in background so there's no delay when we want it...
        if (opus.collection_change) {
            var zippedFiles_html = $(".zippedFiles", "#collection").html();

            // don't forget to remove existing stuff before append
            $(".gallery", "#collection").html("");

            $(".collection_details", "#collection").html(opus.spinner);

            // reset page no
            opus.lastPageDrawn.collection = 0;

            // redux: and nix this big thing:
            $.ajax({ url: "/opus/__collections/view.html",
                success: function(html) {
                    // this div lives in the in the nav menu template
                    $(".collection_details", "#collection").hide().html(html).fadeIn();

                    if (opus.download_in_process) {
                        $(".spinner", "#collections_summary").fadeIn();
                    }

                    $("#colls_pages").html(opus.colls_pages);

                    o_collections.loadCollectionData();

                    if (zippedFiles_html) {
                        $(".zippedFiles", "#collection").html(zippedFiles_html);
                    }
                    o_collections.adjustProductInfoHeight();
                }
            });
        }
    },

    isIn: function(opusId) {
        return  $("[data-id='"+opusId+"'].thumbnail-container").hasClass("in");
    },

    emptyCollection: function() {
        // change indicator to zero and let the server know:
        $.getJSON("/opus/__collections/reset.json", function(data) {
            $("#collection_count").html("0");
            opus.colls_pages = 0;
            opus.collection_change = true;
            $("#collection .navbar").hide();
            opus.changeTab("collection");
        });

        let buttonInfo = o_browse.cartButtonInfo("in");
        $(".thumbnail-container.in [data-icon=cart]").html(`<i class="${buttonInfo.icon} fa-xs"></i>`);
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
            return action;
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
                url += "opusid=" + opusId;
                break;

            case "removerange":
            case "addrange":
                url += "range=" + opusId;
                // need to send to server what page this range lands and what limit of that page is
                // limit should include all observations showing on page
                // must adjust limit + page to account for total number of results showing on page

                // server uses offset = (page_no-1)*limit
                // i.e. the offset of the 23rd page at 100 per page starts with the 2200st record:

                let first_page = o_browse.getCurrentPage();
                let last_page = opus.lastPageDrawn[opus.prefs.view];

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
