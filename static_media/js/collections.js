var o_collections = {
    /**
     *
     *  managing collections and
     *  all interaction on the collections tab
     *
     **/
     collectionBehaviors: function() {


         $('#collections_summary_more','#collections').live("click", function() {
             if (opus.colls_options_viz) {
                 opus.colls_options_viz=false;
                 $('#collections_summary_more','#collections').text('show options');
                 $('#collections_summary','#collections').animate({height:'8em'});
             } else {
                 opus.colls_options_viz=true;
                 $('#collections_summary_more','#collections').text('hide options');
                 $('#collections_summary','#collections').animate({height:'33em'});
             }
             return false;
         });


         $('#download_options_link','#collections').live("click", function() {
             $('#download_options','#collections').slideToggle();
         });



         // check an input on selected products and images updates file_info
         $('#collections_summary input','#collections').live("click",function() {
             add_to_url = o_collections.getDownloadFiltersChecked();
             url = "/opus/collections/download/info?" + add_to_url;
             $.ajax({ url: url + '&fmt=json',
                      success: function(json){
                          $('#total_files').html(json['size']);
                          $('#download_size').html(json['count']);
                  }});


         });

         // click
         $('a#create_zip_file','#collections').live("click", function() {
                $('#zip_file', "#detail").html(opus.spinner + " zipping files");
                add_to_url = [];
                add_to_url = o_collections.getDownloadFiltersChecked();
                url = 'collections/download/default.zip?' + add_to_url;
                $.ajax({ url: url,
                     success: function(json){
                         $('#zip_files').append('<p><a href = "' + json + '">' + json + '</a></p>').show();
                     }});
                return false;
         });


         $('#create_zip_file', "#detail").live("click",function() {
             $('#zip_file', "#detail").html(opus.spinner + " zipping files");
              $.ajax({ url: $(this).attr("href"),
                     success: function(json){
                         $('#zip_file').html('<a href = "' + json + '">' + json + '</a>');
                     }});
              return false;
         });

         $('#empty_collection').live("click", function() {
             if (confirm("are you sure?")) {
                 o_collections.emptyCollection();
               }
             return false;
         });
     },
     getDownloadFiltersChecked: function() {
         // returned as url string
         product_types = [];
         image_types = [];
         add_to_url = [];
         $('ul#product_types input[@type=checkbox]:checked').each(function(){
               product_types.push($(this).val());
             });
         if (product_types.length) {}
         $('ul#image_types input[@type=checkbox]:checked').each(function(){
               image_types.push($(this).val());
             });

        checked_filters = {"types":product_types, "previews":image_types };

        for (filter_name in checked_filters) {
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
                   if (parseInt(count)) {
                       opus.collection_change = true;
                       opus.last_page.colls_browse = { 'data':0, 'gallery':0 }; // reset the last_page drawn tracker
                       $('#collections_tab').fadeIn();
                       opus.colls_pages = Math.ceil(count/opus.prefs.limit);
                       $('.collections_extra').html('(' + count + ')');

                   }
                   opus.lastCartRequestNo = parseInt(json['expected_request_no']) - 1
            }});
    },

    getCollectionsTab: function() {
        if (opus.collection_change) {
            // collection has changed wince tab was last drwan, fetch anew
            $('#collections').html(opus.spinner)
            $.ajax({ url: "/opus/collections/default/view.html",
                   success: function(html){
                       $('#collections').html(html);
                       opus.collection_change = false;
                       o_browse.getBrowseTab();
                       $('#colls_pages').html(opus.colls_pages);
                   }});
        }
    },

    processCollectionQueue: function() {
        // start processing at the lowest item in queue
        found = false;
        for (request_no in opus.collection_queue) {
            if (!opus.collection_queue[request_no]['sent']) {
                found = true;
                // this request is waiting to be sent
                action = opus.collection_queue[request_no]['action'];
                ringobsid = opus.collection_queue[request_no]['ringobsid'];
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
        if (!opus.collection_q_intrvl) {
            opus.collection_q_intrvl = setInterval("o_collections.processCollectionQueue()", 3000); // resends any stray requests not recvd back from server
        }

        url = "/opus/collections/default/" + action + ".json?request=" + request_no;
        if (action == 'addrange' || action == 'removerange') {
            url += "&addrange=" + ringobsid
            url += '&' + o_hash.getHash();
            opus.prefs.browse == 'gallery' ? footer_clicks = opus.browse_footer_clicks['gallery'] : footer_clicks = opus.browse_footer_clicks['data'];
            if (footer_clicks) {
                // user is using infinite scroll
                // must adjust limit + page to account for total number of results showing on page

                // server uses offset = (page_no-1)*limit
                // i.e. the offset of the 23rd page at 100 per page starts with the 2200st record:
                offset = (opus.prefs.page-1) * opus.prefs.limit;

                // now find the number of results showing on the page, different from opus.prefs.limit:
                // number of "pages" showing on screen at any time = limit * (1+footer_clicks)
                // i.e., you've got 100 on screen, you click footer 4 times, now you've got 500 showing
                // multiply that by 2 because our results may span no more than 2 "pages" at our new limit on the server
                limit = 2 * opus.prefs.limit * (1 + parseInt(footer_clicks));

                // server says offset = (page_no-1)*limit
                // solve that equation for page:
                page = Math.floor(offset/limit + 1);
                url += '&limit=' + limit + '&page=' + page;
            }
        } else {
            url += "&ringobsid=" + ringobsid;
        }
        $.ajax({ url: url,
                  dataType:"json",
               success: function(json){
                   if (!json) {
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
                        opus.colls_pages = Math.ceil(count/opus.prefs.limit);
                        $('.collections_extra').html('(' + count + ')');
                        o_collections.resetCollectionQueue();
                   } else {
                       alert('server last ' + server_latest_processed + ' client: ' + opus.lastCartRequestNo)
                   }
               }});
    },

    emptyCollection: function() {
        o_collections.resetCollectionQueue();
        opus.lastCartRequestNo = 0;
        $('.collections_extra').html('(0)');
        $.ajax({ url: "/opus/collections/reset.html"});
        function collTransition() {
            $('.gallery, .data_table','#collections').fadeOut(function() {
                $('.gallery, .data_table','#collections').empty();
            });
            $('.gallery, .data_table','#collections').fadeIn();
        }
        collTransition();
        // uncheck any range boxes
        $('.gallery input', '#browse').attr('checked',false);
        $('.data_container input, .gallery input', '#collections').attr('checked',false);
    },

    resetCollectionQueue: function() {
        clearInterval(opus.collection_q_intrvl);
        opus.collection_q_intrvl = false;
        opus.collection_queue = [];
    },

    editCollection: function(ring_obs_id, action) {
        opus.collection_change = true;
        opus.last_page.colls_browse = { 'data':0, 'gallery':0 };
        opus.lastCartRequestNo++
        $('.collections_extra').html(opus.spinner);
        $('#collections_tab').fadeIn();
        opus.collection_queue[opus.lastCartRequestNo] = {"action":action, "ringobsid":ring_obs_id, "sent":false}
        o_collections.processCollectionQueue();
    },


};