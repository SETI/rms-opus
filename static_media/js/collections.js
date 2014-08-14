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
         $('#collection').on("click", '#collection_summary_more', function() {
             if (opus.colls_options_viz) {
                 opus.colls_options_viz=false;
                 $('#collection_summary_more','#collection').text('show options');
                 $('#collection_summary','#collection').animate({height:'8em'});
             } else {
                 opus.colls_options_viz=true;
                 $('#collection_summary_more','#collection').text('hide options');
                 $('#collection_summary','#collection').animate({height:'33em'});
             }
             return false;
         });


         // check an input on selected products and images updates file_info
         $('#collection').on("click",'#downlaod_options input', function() {
             add_to_url = o_collections.getDownloadFiltersChecked();
             url = "/opus/collections/download/info?" + add_to_url;
             $.ajax({ url: url + '&fmt=json',
                success: function(json){
                    $('#total_files').fadeOut().html(json['size']).fadeIn();
                    $('#download_size').fadeOut().html(json['count']).fadeIn();
                }});

         });

         // click create download zip file link on collections page
         $('#collection').on("click", '#collections_summary a#create_zip_file button', function() {
                $('#zip_files .spinner', "#collections_summary").fadeIn();
                add_to_url = [];
                add_to_url = o_collections.getDownloadFiltersChecked();
                url = '/opus/collections/download/default.zip?' + add_to_url;
                $.ajax({ url: url,
                     success: function(json){
                        $('#zip_files .spinner', "#collections_summary").fadeOut();
                        $('#zip_files', "#collections_summary").append('<p><a href = "' + json + '">' + json + '</a></p>');
                     }});
                return false;
         });


         // click create zip file link on detail page
         $("#detail").on("click", '#create_zip_file', function() {
             $('#zip_file', "#detail").html(opus.spinner + " zipping files");
              $.ajax({ url: $(this).attr("href"),
                     success: function(json){
                         $('#zip_file').html('<a href = "' + json + '">' + json + '</a>');
                     }});
              return false;
         });

         // empty collection button
         $('#collection').on("click", '#empty_collection', function() {
             if (confirm("are you sure you want to delete all observations in your collection?")) {
                 o_collections.emptyCollection();
               }
             return false;
         });
     },

     // download filters
     getDownloadFiltersChecked: function() {
         // returned as url string
         product_types = [];
         image_types = [];
         add_to_url = [];
         $('ul#product_types input:checkbox:checked').each(function(){
               product_types.push($(this).val());
             });
         if (product_types.length) {}
         $('ul#image_types input:checkbox:checked').each(function(){
               image_types.push($(this).val());
             });
        checked_filters = {"types":product_types, "previews":image_types };

        for (var filter_name in checked_filters) {
          if (checked_filters[filter_name].length) {
              add_to_url.push(filter_name + "=" + checked_filters[filter_name].join(','));
          }
        }
        return add_to_url.join('&');
     },

    // init an existing collection on page load
    initCollection: function() {
        // returns any user collection saved in session
        $.ajax({ url: "/opus/collections/default/status.json",
            dataType:"json",
            success: function(json){
                   count = json['count'];
                   if (parseInt(count, 10)) {
                       opus.collection_change = true;

                        opus.mainTabDisplay('collection');  // make sure the main site tab label is displayed

                       $('#collection_tab').fadeIn();
                       opus.colls_pages = Math.ceil(count/opus.prefs.limit);
                        $('#collection_count').html(count);

                   }
                   opus.lastCartRequestNo = parseInt(json['expected_request_no']) - 1
            }});
    },

    // get Collections tab
    getCollectionsTab: function() {


        clearInterval(opus.scroll_watch_interval); // hold on cowboy only 1 page at a time


        if (opus.collection_change) {
            // collection has changed wince tab was last drwan, fetch anew
            $('.collection_details', '#collection').html(opus.spinner);
            $.ajax({ url: "/opus/collections/default/view.html",
                   success: function(html){

                       $('.collection_details', '#collection').hide().html(html).fadeIn();
                       opus.collection_change = false;
                       o_browse.getBrowseTab();
                       $('#colls_pages').html(opus.colls_pages);
                   }});
        }
    },

    // when you add to a collection you are really adding to a queue, this processes that queue
    processCollectionQueue: function() {
        // start the lowest item in the queue, then trigger sendCollectionRequest again?
        found = false;
        for (request_no in opus.collection_queue) {
            if (!opus.collection_queue[request_no]['sent']) {
                found = true;
                // this request is waiting to be sent
                action = opus.collection_queue[request_no]['action'];
                ringobsid = opus.collection_queue[request_no]['ringobsid'];
                // alert('calling sendCollectionRequest for ' + ring_obs_id);
                o_collections.sendCollectionRequest(action,ringobsid,request_no);
            }
        }
        if (!found) {
            // queue is empty quit lookin' at it
            o_collections.resetCollectionQueue();
        }
    },

    // action = add/remove/addrange/removerange
    sendCollectionRequest: function(action,ringobsid,request_no) {
        // this sends the ajax call to edit the cart on the server
        // but this should really be a private method
        // for adding/removing from cart see edit_collection()


        if (!opus.collection_q_intrvl) {
            opus.collection_q_intrvl = setInterval("o_collections.processCollectionQueue()", 500); // resends any stray requests not recvd back from server
        }

        url = "/opus/collections/default/" + action + ".json?request=" + request_no;
        if (action == 'addrange') {
            url += "&addrange=" + ringobsid;
            // need to send to server what page this range lands and what limit of that page is
            // limit should include all observations showing on page
            // must adjust limit + page to account for total number of results showing on page

            // server uses offset = (page_no-1)*limit
            // i.e. the offset of the 23rd page at 100 per page starts with the 2200st record:

            // first find what does opus.prefs.page say we are looking at:
            current_page = o_browse.getCurrentPage();

            offset = (current_page-1) * opus.prefs.limit;

            // now find the number of results showing on the page, different from opus.prefs.limit:
            // number of "pages" showing on screen at any time = limit * (1+footer_clicks)
            // i.e., you've got 100 on screen, you click footer 4 times, now you've got 500 showing
            // multiply that by 2 because our results may span no more than 2 "pages" at our new limit on the server
            limit = 2 * opus.prefs.limit * current_page;

            // server says offset = (page_no-1)*limit
            // solve that equation for page our new page value:
            page = Math.floor(offset/limit + 1);
            url += '&limit=' + limit + '&page=' + page;
            url += '&' + o_hash.getHash();
        } else {
            url += "&ringobsid=" + ringobsid;
        }

        $.ajax({ url: url,
              dataType:"json", success: function(json){

                   if (!json) {
                        // alert('no json kay bai')
                       return;
                   }
                   try {
                       opus.collection_queue[request_no]['sent'] = true; // server has recvd this request
                   } catch(e) {}
                   if (json['err']) {
                       // server still waiting for earlier request
                       return;
                   }
                   server_latest_processed = json['request_no'];
                   if (server_latest_processed == opus.lastCartRequestNo) {
                        // server has process all collection requests, this count is valid
                        count = json['count'];
                        $('#collection_count').html(count);
                        opus.colls_pages = Math.ceil(count/opus.prefs.limit);
                        o_collections.resetCollectionQueue();
                   } else {
                       // // alert('server last ' + server_latest_processed + ' client: ' + opus.lastCartRequestNo)
                   }
               }});
    },

    emptyCollection: function() {
        // remove all
        o_collections.resetCollectionQueue();
        opus.lastCartRequestNo = 0;
        // change indicator to zero and let the server know:

        $.ajax({ url: "/opus/collections/reset.html",
            success: function(html){
                $('#collection_count').html('0');
            }, error: function(e) {
            }
        });

        // hide the collection data viewing page
        function collTransition() {
            $('.gallery, .data_table','#collection').fadeOut(function() {
                $('.gallery, .data_table','#collection').empty();
            });
            $('.gallery, .data_table','#collection').fadeIn();
        }
        collTransition();

        // remove 'in collection' styles in gallery/data view
        $('.tools-bottom', '.gallery').removeClass("in"); // this class keeps parent visible when mouseout
        $('i.fa-check', '.gallery').removeClass('thumb_selected_icon');
        $('.thumb_overlay', '.gallery').removeClass('thumb_selected');
    },

    resetCollectionQueue: function() {
        clearInterval(opus.collection_q_intrvl);
        opus.collection_queue = [];
    },

    editCollection: function(ring_obs_id, action) {

        opus.mainTabDisplay('collection');  // make sure the main site tab label is displayed

        opus.collection_change = true;
        opus.lastCartRequestNo++;
        // $('.collections_extra').html(opus.spinner);
        // $('#collection_tab').fadeIn();
        opus.collection_queue[opus.lastCartRequestNo] = {"action":action, "ringobsid":ring_obs_id, "sent":false};
        o_collections.processCollectionQueue();
    },


};