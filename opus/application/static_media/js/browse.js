var o_browse = {

    /**
    *
    *  all the things that happen on the browse tab
    *
    **/
    browseBehaviors: function() {
        // note: using .on vs .click allows elements to be added dynamically w/out bind/rebind of handler

        $(".gallery-contents").on('scroll', _.debounce(o_browse.checkScroll, 200));

        // nav stuff
        var onRenderBrowse = _.debounce(o_browse.loadBrowseData, 500);
        $(".browse-nav-container").on("click", "a.next, a.prev", function() {

            // we will set a timer to wait for settle but right now just do it
            var currentPage = parseInt($("input#page").val());

            var page = ($(this).hasClass("next") ? currentPage+1 : currentPage-1);
            if (page > 0 && page <= opus.pages ) {
                $("input#page").val(page).css("color","red");
                onRenderBrowse();
            }
            return false;
        });

        $("#browse").on('change', 'input#page', function() {
            var newPage = parseInt($("input#page").val());
            if (newPage > 0 && newPage <= opus.pages ) {
                $("input#page").css("color","red");
                onRenderBrowse();
            } else {
                // put back
                $("input#page").val(opus.last_page_drawn[opus.prefs.browse]);
            }
            return false;
        });

        $("#browse").on("click", ".cart_control", function() {
          console.log("add range");
          return false;
        });

      // browse nav menu - add range - begins add range interaction
       $('#browse').on("click", '.addrange', function() {
          // if someone clicks 'add range' this method sets the addrange_clicked to true
          // then if they click a thumbnail next it is considered part of the range
          var container =  $('.cart_control', '#browse');
          var link = $('.addrange', '#browse');
          var button_text = link.html();
          var element_name = 'thumbnail';
          if (opus.prefs.browse == 'data') {
              element_name = 'row';
          }
          var start_hint = "click on a " + element_name + " to define a range of selections";

          if (button_text = "add range") {
              // the first click of 'add range' begins the add-range interaction
              opus.addrange_clicked = true;
              link.html("select range start");
              link.popover('destroy');
              container.popover({
                  content: start_hint,
                  trigger:"click",
                  placement: "bottom",
              });
          }
          return false;

       });


       $("#browse").on("click", ".get_column_chooser", function() {
          o_browse.renderColumnChooser();
       });

       $("#columnChooser").modal({
           keyboard: false,
           backdrop: false,
           show: false,
       })

       // browse nav menu - the gallery/table toggle
       $("#browse").on("click", ".browse_view", function() {
          opus.prefs.browse = $(this).data("view");

          o_hash.updateHash();

// do i need to do this...?
          var hide = opus.prefs.browse == "gallery" ? "dataTable" : "gallery";
          $('.' + hide, "#browse").hide();

          $('.' + opus.prefs.browse, "#browse").fadeIn();

          o_browse.updateBrowseNav();

          // do we need to fetch a new browse tab?
          if ((opus.prefs.browse == "gallery" && !opus.gallery_begun) ||
              (opus.prefs.browse == "dataTable" && !opus.table_headers_drawn)) {
              o_browse.getBrowseTab();
          }

          // reset scroll position
          window.scrollTo(0,opus.browse_view_scrolls[opus.prefs.browse]); // restore previous scroll position

          return false;
       });

       // browse nav menu - download csv
       $("#browse").on("click", '.download_csv', function() {
           var col_str = opus.prefs.cols.join(',');
           var hash = [];
           for (var param in opus.selections) {
               if (opus.selections[param].length){
                   hash[hash.length] = param + '=' + opus.selections[param].join(',').replace(/ /g,'+');
               }
           }
           var q_str = hash.join('&');
           var csv_link = "/opus/__api/data.csv?" + q_str + '&cols=' + col_str + '&limit=' + opus.result_count.toString() + '&order=' + opus.prefs['order'];
           $(this).attr("href", csv_link);
       });

       // other behaviours
        // click on thumbnail opens modal window
      $(".gallery, #dataTable ").on("click", ".thumbnail, tbody > tr :not(:input)", function(e) {
            // make sure selected modal thumb is unhighlighted, as clicking on this closes the modal
            // but is not caught in time before hidden.bs to get correct opusId
            o_browse.toggleGalleryViewHighlight("off");

            let opusId = $(this).data("id");
            if (opusId == undefined) {
                opusId = $(this).parent().data("id");
            }

            o_browse.updateGalleryView(opusId);
        });

        // data_table - clicking a table row adds to cart
        $("#browse").on("click", "#data_table :input", function() {

            var opusId = $(this).attr("id").substring(6);
            $(this).find('.data_checkbox').toggleClass('fa-check-square-o').toggleClass('fa-square-o');
            var action = 'remove';
            if ($(this).find('.data_checkbox').hasClass('fa-check-square-o')) {
                // this is checked, we are unchecking it now
                action = 'add';
            }

            // make sure the checkbox for this observation in the other view (either data or gallery)
            // is also checked/unchecked - if that view is drawn
            try {
                o_browse.toggleBrowseInCollectionStyle(opusId);
            } catch(e) { } // view not drawn yet so no worries

            // check if we are clicking as part of an 'add range' interaction
            if (!opus.addrange_clicked) {

                // no add range, just add this obs to collection
                o_collections.editCollection(opusId,action);

            } else {
                o_browse.addRangeHandler(opusId);
            }
            return false;

        });

        // thumbnail overlay tools
        $('.gallery').on("click", ".tools a", function(e) {
          //snipe the id off of the image..
          var opusId = $(this).parent().data("id");

          switch ($(this).data("icon")) {
              case "info":  // detail page
                  opus.prefs.detail = opusId;
                  if (e.shiftKey || e.ctrlKey || e.metaKey) {
                      // handles command click to open in new tab
                      var link = "/opus/#/" + o_hash.getHash();
                      link = link.replace("view=browse", "view=detail");
                      window.open(link, '_blank');
                  } else {
                      opus.prefs.detail = opusId;
                      opus.changeTab("detail");
                      $('a[href="#detail"]').tab("show");
                  }
                  break;

              case "check":   // add to cart
                  var action = o_browse.toggleBrowseInCollectionStyle(opusId);
                  o_browse.cartHandler(opusId, action);
                  break;

              case "resize":  // expand, same as click on image
                  $('a[data-id="'+opusId+'"]').trigger("click");
                  break;

              default:
                alert("Hmm... should not be here. error 710.");
            }
            return false;
        }); // end click a browse tools icon

        $("#gallerylView").modal({
            keyboard: false,
            backdrop: 'static',
            show: false,
        });

        $(".modal-dialog").draggable({
            handle: ".modal-content"
        });

        $(".app-body").on("hide.bs.modal", "#galleryView", function(e) {
            o_browse.toggleGalleryViewHighlight("off");
        });

        // add the 'get detail' behavior
        $('#galleryView').on("click", '.detailViewLink', function(e) {
            if (e.shiftKey || e.ctrlKey || e.metaKey) {
                // handles command click to open in new tab
                let link = "/opus/#/" + o_hash.getHash();
                link = link.replace("view=browse", "view=detail");
                window.open(link, '_blank');
            } else {
                opus.prefs.detail = $(this).data('opusid');
                opus.changeTab("detail");
                $('a[href="#detail"]').tab("show");
            }
            return false;
        });

        $('#galleryView').on("click", "a.select", function(e) {
            let opusId = $(this).data("id");
            if (opusId) {
                let action = o_browse.toggleBrowseInCollectionStyle(opusId);
                o_browse.cartHandler(opusId, action);
            }
            return false;
        });

        $('#galleryView').on("click", "a.prev,a.next", function(e) {
            let action = $(this).hasClass("prev") ? "prev" : "next";
            let opusId = $(this).data("id");
            if (opusId) {
                o_browse.toggleGalleryViewHighlight();  // toggle highlight of current
                o_browse.updateGalleryView(opusId);
            }
            return false;
        });

        $(document).on("keydown",function(e) {
            /*  Catch the right/left arrow while in the modal
                Up: 38
                Down: 40
                Right: 39
                Left: 37 */
            if ($("#galleryView").hasClass("show")) {
                let opusId;
                switch (e.keyCode) {
                    case 39:  // next
                        opusId = $("#galleryView").find(".next").data("id");
                        break;
                    case 37:  // prev
                        opusId = $("#galleryView").find(".prev").data("id");
                        break;
                }
                if (opusId) {
                    o_browse.toggleGalleryViewHighlight();  // toggle highlight of current
                    o_browse.updateGalleryView(opusId);
                }
            }
            return false;
        });

        // click table column header to reorder by that column
        $("#browse").on("click", '.data_table th a',  function() {
            let order_by =  $(this).data('slug');
            if (order_by == 'collection') {
              // Don't do anything if clicked on the "Selected" column
              return false;
            }
            let order_indicator = $(this).find('.column_ordering');
            if (order_indicator.hasClass('fa-sort-asc')) {
                // currently ascending, change to descending order
                order_indicator.removeClass('fa-sort-asc');
                order_indicator.addClass('fa-sort-desc');
                order_by = '-' + order_by;
            } else if (order_indicator.hasClass('fa-sort-desc')) {
                // change to not ordered
                order_indicator.removeClass('fa-sort-desc');
                order_by = "";

            } else {
                // not currently ordered, change to ascending
                order_indicator.addClass('fa-sort-asc');
            }
            opus.prefs['order'] = order_by;
            opus.prefs.page = default_pages; // reset pages to 1 when col ordering changes

            o_browse.updatePage();
            return false;
        });

        // the "back to top" link at bottom of gallery
        $("#browse").on('click', 'a[href="#top"]', function() {
            $('html, body').animate({scrollTop:0}, 'slow');
            return false;
        });

    }, // end browse behaviors

    checkScroll: function() {
        $.each($(".gallery .thumb-page"), function(index, elem) {
            let position = $(elem).children().offset();
            if (position) {
                if (position.top > 0 && (position.top < $(".gallery-contents").height()-100)) {
                    // Update page number
                    let page = $(elem).data("page");
                    opus.prefs.page[opus.prefs.browse] = page;
                    $("input#page").val(page).css("color","initial");
                    console.log("page: "+page);
                    return false;
                }
            }
        })
        return false;
    },

    cartHandler: function(opusId, action) {
        // behaviors for the click to add/remove from cart
        // whether that's from checkbox being clicked
        // or thumbnail clicked while 'add range' is happening

        // make sure the checkbox for this observation in the other view (either data or gallery)
        // is also checked/unchecked - if that view is drawn
        $('#data__' + opusId).find('.data_checkbox').toggleClass('fa-check-square-o').toggleClass('fa-square-o');
        o_collections.editCollection(opusId,action);
    },

    openDetailTab: function() {
        $("#galleryView").modal('hide');
        opus.changeTab('detail');
    },

    getGalleryElement: function(opusId) {
        let elem = $("#" + opus.prefs.view+" .thumbnail-container a[data-id=" + opusId + "]");
        return elem;
    },

    toggleBrowseInCollectionStyle: function(opusId) {
        var elem = o_browse.getGalleryElement(opusId);

        // if this opusId is modal, make sure it stays highlighted
        o_browse.toggleGalleryViewHighlight("on", opusId);

        elem.toggleClass("in"); // this class keeps parent visible when mouseout

        return (elem.hasClass("in") ? "add" : "remove");
    },

    // column chooser behaviors
    addColumnChooserBehaviors: function() {
        // this is a global
        currentSelectedColumns = opus.prefs.cols.slice();

        $(".app-body").on("hide.bs.modal", "#columnChooser", function(e) {
            // update the data table w/the new columns
            if (!o_utils.areObjectsEqual(opus.prefs.cols, currentSelectedColumns)) {
                o_hash.updateHash();
                o_browse.loadBrowseData(last_page_drawn.gallery);
                currentSelectedColumns = opus.prefs.cols.slice();
            }
        });

        $(".app-body").on("show.bs.modal", "#columnChooser", function(e) {
            // save current column state so we can look for changes
            currentSelectedColumns = opus.prefs.cols.slice();
        });

        $('#columnChooser .allColumns').on("click", '.submenu li a', function() {

            let slug = $(this).data('slug');
            if (!slug) {
                return false;  // just a 2nd level menu click, move along
            }

            let label = $(this).data('qualifiedlabel');
            let def = $(this).find('i.fa-info-circle').attr("title");
            let checkmark = $(this).find("i.fa-check");

            if (!checkmark.is(":visible")) {
                checkmark.fadeIn().css('display', 'inline-block');
                if ($.inArray(slug, opus.prefs.cols ) < 0) {
                    // this slug was previously unselected, add to cols
                    $('<li id = "cchoose__' + slug + '">' + label + ' <i class = "fa fa-info-circle" title = "' + def + '"></i><span class = "unselect">X</span></li>').hide().appendTo('.selectedColumns > ul').fadeIn();
                    opus.prefs.cols.push(slug);
                }

            } else {
                checkmark.hide();
                if ($.inArray(slug,opus.prefs.cols) > -1) {
                    // slug had been checked, remove from the chosen
                    opus.prefs.cols.splice($.inArray(slug,opus.prefs.cols),1);
                    $('#cchoose__' + slug).fadeOut(function() {
                        $(this).remove();
                    });
                }
            }
            return false;
        });


        // removes chosen column with X
        $('.column_chooser').on("click",'.chosen_column_close', function() {
            let slug = $(this).parent().attr("id").split('__')[1];
            let checkmark = $('.all_columns .' + slug).find('i').first();

            checkmark.hide();

            if ($.inArray(slug,opus.prefs['cols']) > -1) {
                // slug had been checked, removed from the chosen
                opus.prefs['cols'].splice($.inArray(slug,opus.prefs['cols']),1);
                $('#cchoose__' + slug).fadeOut(function() {
                    $(this).remove();
                });
            }

            // update the data table w/the new columns
            o_hash.updateHash();
            let pages = opus.pages_drawn.gallery;
            for (let i in pages) {
                o_browse.loadBrowseData(pages[i]);
            }
            return false;
        });
    },  // /addColumnChooserBehaviors

    checkAllRenderedElements: function() {
      // returns first and last opusId that is rendered on the page

      // find the id of the first and last element showing on this page
      let first = "";
      let last = "";
      if (opus.prefs.browse == "gallery") {
        el = $('.gallery li');
        first = el.first().attr('id');
        last = el.last().attr('id');
      } else {
        first = $('.data_table tbody tr:first').attr('id');
        last = $('.data_table tbody tr:last').attr('id');
      }

      let opusId1 = first.split('__')[1];
      let opusId2 = last.split('__')[1];

      o_browse.checkRangeBoxes(opusId1, opusId2);
    },

    // handles checking of a range of boxes in each view (table/gallery)
    checkRangeBoxes: function(opusId1, opusId2) {

        // make all list/td elements bt r1 and r2 be added to cart
        let elements = ['#gallery__','#data__'];
        for (let key in elements) {
            let element = elements[key];
            let current_id = opusId1;
            let next_element = $(element + current_id, '#browse');
            while (current_id != opusId2) {

                // thumbnail in the list
                if (next_element.hasClass("infinite_scroll_page")) {
                    // this is the infinite scroll indicator, continue to next
                    next_element = $(element + current_id, '#browse').next().next();
                }

                // check the boxes:
                if (element == '#gallery__') {
                    /* gallery view */
                    if (!next_element.find('.tools').hasClass("in")) {  // if not already checked
                        try {
                            opusId = next_element.attr("id").split('__')[1];
                            o_browse.toggleBrowseInCollectionStyle(opusId);
                        } catch(e) {
                        }
                    }
                } else {
                    /* this is table view */
                    if (!next_element.find('.data_checkbox').hasClass('fa-check-square-o')) {  // if not already checked
                        // box is not checked so checkity check it
                        $(next_element).find(".data_checkbox").addClass('fa-check-square-o').removeClass('fa-square-o');
                    }

                }

                // now move along
                try {
                    current_id = next_element.attr("id").split('__')[1];
                } catch(e) {
                    break;  // no next_id means the view isn't drawn, so we don't need to worry about it
                }

                next_element = $(element + current_id, '#browse').next();

            } // /while
        }
    },

    // there are interactions that are applied to different code snippets,
    // this returns the namespace, view_var, prefix, and add_to_url
    // that distinguishes collections vs result tab views
    // NOTE: get rid of all this with a framework!
    // usage:
    // utility function to figure out what view we are in
    /*
        // usage
        view_info = o_browse.getViewInfo();
        namespace = view_info['namespace'];
        view_var = view_info['view_var'];
        prefix = view_info['prefix'];
        add_to_url = view_info['add_to_url'];
    */
    getViewInfo: function() {
        // this function returns some data you need depending on whether
        // you are in #collection or #browse views
        if (opus.prefs.view == 'collection') {
            namespace = '#collection';
            prefix = 'colls_';
            add_to_url = "&colls=true";
        } else {
            namespace = '#browse';
            prefix = '';
            add_to_url = "";
        }
        return {'namespace':namespace, 'prefix':prefix, 'add_to_url':add_to_url};

    },

    getCurrentPage: function() {
        // sometimes other functions need to know current page for whatever view we
        // are currently looking at..
        let view_info = o_browse.getViewInfo();
        let namespace = view_info['namespace']; // either '#collection' or '#browse'
        let prefix = view_info['prefix'];       // either 'colls_' or ''
        let view_var = opus.prefs[prefix + 'browse'];  // either "gallery" or "data"
        let page = 1;

        if (view_var == "data") {
            page = opus.prefs.page[prefix + "data"];
        } else {
            page = opus.prefs.page[prefix + "gallery"];
        }
        if (!page) { page = 1; }

        return page;
    },

    updateBrowseNav: function() {
        if (opus.prefs.browse == "gallery") {
            $('.' + "dataTable", "#browse").hide();
            $('.' + opus.prefs.browse, "#browse").fadeIn();

            $('.browse_view', "#browse").text('view table');
            $(".browse_view", "#browse").data("view", "dataTable");
        } else {
            $('.' + "gallery", "#browse").hide();
            $('.' + opus.prefs.browse, "#browse").fadeIn();

            $('.browse_view', "#browse").text('view gallery');
            $(".browse_view", "#browse").data("view", "gallery");
        }
    },

    updatePageInUrl: function(url, page) {
        let urlPage = 0;
        // remove any existing page= slug before adding in the current page= slug w/new page number
        url = $.grep(url.split('&'), function(pair, index) {
            if (pair.startsWith("page")) {
                urlPage = pair.split("=")[1];
            }
            return !pair.startsWith("page");
        }).join('&');

        page = (page === undefined ? ++urlPage : page);
        url += '&page=' + page;
        return url;
    },

    renderColumnChooser: function() {
        if (!opus.column_chooser_drawn) {
            let url = '/opus/__forms/column_chooser.html?' + o_hash.getHash() + '&col_chooser=1';
            $('.column_chooser').load( url, function(response, status, xhr)  {

                opus.column_chooser_drawn=true;  // bc this gets saved not redrawn

                // we keep these all open in the column chooser, they are all closed by default
                // disply check next to any default columns
                $.each(opus.prefs['cols'], function(index, col) {
                    $('.column_chooser li > [data-slug="'+col+'"]').find("i.fa-check").fadeIn().css('display', 'inline-block');
                });

                o_browse.addColumnChooserBehaviors();

                // dragging to reorder the chosen
                $( ".chosen_columns>ul").sortable({
                    items: "li:not(.unsortable)",
                    cursor: 'move',
                    stop: function(event, ui) { o_browse.columnsDragged(this); }
                });
            });
        }
    },

    // note that renderTable also updates the gallery_data table, as it contains the same information/columns as the table
    renderTable: function(tableData) {
        // update table
        $.each(tableData.page, function(item, galleryData) {
              // for now, always assume that opusId is first item in list
            let opusId = galleryData[0];
            opus.gallery_data[opusId] = galleryData;

            let checkbox = "<input type='checkbox' name='"+opusId+"' value='"+opusId+"' class='multichoice' id='select_"+opusId+"'>";
            var row = "<td>"+checkbox+"</td>";
            var tr = "<tr data-toggle='modal' data-id='"+opusId+"' data-target='#galleryView'>";
            $.each(galleryData, function(index, cell) {
                row += "<td>"+cell+"</td>";
            });
            //$("<tr data-toggle='modal' data-id='"+galleryData[0]+"' data-target='#galleryView'>"+row+"</tr>").appendTo(".dataTable tbody");
            $(tr+row+"</tr>").appendTo(".dataTable tbody");
        });
    },

    renderGallery: function(data, page, url) {
        let namespace = o_browse.getViewInfo().namespace;
        var html = "";
        if (data.length == 0) {
            html += '<div class="thumbnail-message">';
            html += '<h2>You Have No Selections</h2>';
            html += '<p>To select observations, click on the Browse Results tab';
            html += 'at the top of the page,<br> mouse over the thumbnail gallery images to reveal the tools,';
            html += 'then click the <br>checkbox below a thumbnail.  </p>';
            html += '</div>';
        } else {
            html += '<div class="thumb-page" data-page="'+page+'">';
            $.each(data, function( key, imageData ) {
                html += '<div class="thumbnail-container'+ (imageData.in_collection ? ' thumb_selected' : '') +'">';
                html += '<a href="#" class="thumbnail '+(imageData.in_collection ? ' in' : '')+'" ';
                html += 'data-toggle="modal" data-target="#galleryView" data-id="'+imageData.opus_id+'"	data-image="'+imageData.full_url+'">';
                html += '<img class="img-thumbnail img-fluid" src="'+imageData.thumb_url+'" alt="'+imageData.thumb_alt_text+'" title="'+imageData.opus_id+'"> </a>';
                html += '<div class="thumb_overlay">';
                html +=    '<div class="tools" data-id="'+imageData.opus_id+'">';
                html +=       '<a href="#" data-icon="info"><i class="fa fa-info fa-xs" aria-hidden="true"></i></a>';
                html +=       '<a href="#" data-icon="check"><i class="fa fa-check fa-xs" aria-hidden="true"></i></a>';
                html +=       '<a href="#" data-icon="resize"><i class="fas fa-expand-arrows-alt fa-xs" aria-hidden="true"></i></a>';
                html += '</div></div></div>';
            });
            html += '</div>';
        }
        $('.gallery', namespace).append(html);
    },

    startTable: function(tableData) {
        // prepare table and headers...
        $(".dataTable thead > tr > th").detach();
        $(".dataTable tbody > tr").detach();

        // this endpoint also returns column labels:
        opus.col_labels = [];
        $.each(tableData.labels, function(index, labels) {
            opus.col_labels.push(labels);
        })

        // check all box
        let checkbox = "<input type='checkbox' name='all' value='all' class='multichoice' id='all'>";
        $("<th id='checkAll' scope='col' class='sticky-header'>"+checkbox+"</th>").appendTo(".dataTable thead tr");
        $.each(tableData.labels, function( column, header) {
            $("<th id='"+column+"'scope='col' class='sticky-header'>"+header+"</th>").appendTo(".dataTable thead tr");
        });
    },

    loadBrowseData: function(page) {
        //window.scrollTo(0,opus.browse_view_scrolls[opus.prefs.browse]);
        page = (page == undefined ? $("input#page").val() : page);
        $("input#page").val(page);

        // wait! is this page already drawn?
        if (opus.last_page_drawn[opus.prefs.browse] == page) {
            return;
        }

        let view = o_browse.getViewInfo();
        let base_url = "/opus/__api/images.json?";
        let url = o_hash.getHash() + '&reqno=' + opus.lastRequestNo + view.add_to_url;

        url = o_browse.updatePageInUrl(url, page);

        // metadata; used for both table and gallery
        $.getJSON(base_url + url, function(allData) {
            o_browse.renderGallery(allData.data, allData.page_no, this.url);
            if (!opus.gallery_begun)
                o_browse.startTable(allData.metadata);

            o_browse.renderTable(allData.metadata);

            if (!opus.gallery_begun) {
                // for infinite scroll
                $('#browse .gallery-contents').infiniteScroll({
                    path: o_browse.updatePageInUrl(this.url, "{{#}}"),
                    responseType: 'text',
                    status: '.scroller-status',
                    elementScroll: true,
                    history: false,
                    debug: false,
                });
                $('#browse .gallery-contents').on( 'load.infiniteScroll', function( event, response, path ) {
                    let jsonData = JSON.parse( response );
                    o_browse.renderGallery(jsonData.data, jsonData.page_no, path);
                    o_browse.renderTable(jsonData.metadata);

                    // load another page
                    if (jsonData.page_no % 2 == 0) {
                        $('#browse .gallery-contents').infiniteScroll('loadNextPage')
                    }
                });
                $('#browse .gallery-contents').infiniteScroll('loadNextPage');
                opus.gallery_begun = true;
            }

        });

        opus.last_page_drawn["dataTable"] = page;
        opus.table_headers_drawn = true;

        opus.last_page_drawn[opus.prefs.browse] = page;
    },

    getBrowseTab: function() {
        // only draw the navbar if we are in gallery mode... doesn't make sense in collection mode
        let hide = opus.prefs.browse == "gallery" ? "dataTable" : "gallery";
        $('.' + hide, "#browse").hide();

        $('.' + opus.prefs.browse, "#browse").fadeIn();

        o_browse.updateBrowseNav();
        o_browse.renderColumnChooser();   // just do this in background so there's no delay when we want it...

        // total pages indicator
        $('#' + 'pages', "#browse").html(opus['pages']);

        // figure out the page
        let page = opus.prefs.page[opus.prefs.browse]; // default: {"gallery":1, "dataTable":1, 'colls_gallery':1, 'colls_data':1 };

        // some outlier things that can go wrong with page (when user entered page #)
        page = (!page || page < 1) ? 1 : page;

        if (opus.pages && page > opus.pages) {
            // page is higher than the total number of pages, reset it to the last page
            page = opus.pages;
        }
        o_browse.loadBrowseData(page);
        o_browse.adjustBrowseHeight();  // may need to go in getGallery

        $("input#page").val(page).css("color","initial");
        o_hash.updateHash();
    },

    adjustBrowseHeight: function() {
        let container_height = $(window).height()-120;
        $(".gallery-contents").height(container_height);
        //opus.limit =  (floor($(window).width()/thumbnailSize) * floor(container_height/thumbnailSize));
    },

    metadataboxHtml: function(opusId) {
        // list columns + values
        var html = "<dl>";
        for (let i in opus.prefs["cols"]) {
            let column = opus.col_labels[i];  // use the label not the column title
            let value = opus.gallery_data[opusId][i];
            html += "<dt>" + column + ":</dt><dd>" + value + "</dd>";

        }
        html += "</dl>";
        let next = $("#browse tr[data-id="+opusId+"]").next("tr");
        next = (next.length > 0 ? next.data("id") : "");
        let prev = $("#browse tr[data-id="+opusId+"]").prev("tr");
        prev = (prev.length > 0 ? prev.data("id") : "");

        // add a link to detail page;
        let hashArray = o_hash.getHashArray();
        hashArray["view"] = "detail";
        hashArray["detail"] = opusId;
        html += '<p><a href = "/opus/#/' + o_hash.hashArrayToHashString(hashArray) + '" class="detailViewLink" data-opusid="' + opusId + '">View Detail</a></p>';

        // prev/next buttons - put this in galleryView html...
        html += "<div class='bottom'>";
        html += "<a href='#' class='select' data-id='"+opusId+"' title='Add to selections'><i class='fas fa-cart-plus fa-2x float-left'></i></a>";
        html += "<a href='#' class='next pr-5' data-id='"+next+"' title='Next image'><i class='far fa-hand-point-right fa-2x float-right'></i></a>";
        html += "<a href='#' class='prev pr-5' data-id='"+prev+"' title='Previous image'><i class='far fa-hand-point-left fa-2x float-right'></i></a></div>";
        return html;
    },

    toggleGalleryViewHighlight: function(highlight, opusId) {
        if (opusId == undefined) {
            opusId = $("#galleryView [data-opusid]").data("opusid");
        }
        if (opusId !== undefined) {
            switch (highlight) {
                case "on":
                    $("tr[data-id='"+opusId+"']").addClass("highlight");
                    $("a.thumbnail[data-id='"+opusId+"']").parent().addClass("thumb_selected");
                    break;
                case "off":
                    $("tr[data-id='"+opusId+"']").removeClass("highlight");
                    $("a.thumbnail[data-id='"+opusId+"']").parent().removeClass("thumb_selected");
                    break;
                case undefined:
                default:
                    // don't unhighlight if it is in collection unless specifically asked
                    if (!$("a.thumbnail[data-id='"+opusId+"']").hasClass("in")) {
                        $("tr[data-id='"+opusId+"']").toggleClass("highlight");
                        $("a.thumbnail[data-id='"+opusId+"']").parent().toggleClass("thumb_selected");
                    }
                    break;
            }
        }
    },

    updateGalleryView: function(opusId) {
        // while modal is up, highlight the image/table row shown
        o_browse.toggleGalleryViewHighlight("on", opusId);

        var imageURL = $("#browse").find("a[data-id='"+opusId+"']").data("image");
        if (imageURL === undefined) {
            // put a temp spinner while retrieving the image; this only happens if the data table is loaded first
            $("#galleryViewContents").html(o_browse.loader + o_browse.metadataboxHtml(opusId));
            $("#galleryViewContents").data("id", opusId);

            var url = '/opus/__api/image/full/' + opusId + '.json';
            $.getJSON(url, function(imageData) {
                var imageURL = imageData["data"][0]['url'];
                o_browse.updateMetaGalleryView(opusId, imageURL);
            });
        } else {
            o_browse.updateMetaGalleryView(opusId, imageURL);
        }
    },


    updateMetaGalleryView: function(opusId, imageURL) {
        $("#galleryViewContents .left").html("<a href='"+imageURL+"' target='_blank'><img src='"+imageURL+"' title='"+opusId+"' class='preview'/></a>");
        $("#galleryViewContents .right").html(o_browse.metadataboxHtml(opusId));
    },

    resetQuery: function() {
        /*
        when the user changes the query and all this stuff is already drawn
        need to reset all of it (todo: replace with framework!)
        */
        $("#dataTable > tbody").empty();  // yes all namespaces
        $(".gallery").empty();
        opus.gallery_data = [];
        opus.pages_drawn = {"colls_gallery":[], "gallery":[]};
        opus.browse_footer_clicks = {"gallery":0, "data":0, "colls_gallery":0, "colls_data":0 };
        opus.last_page_drawn = {"gallery":0, "dataTable":0, "colls_gallery":0, "colls_data":0 };
        opus.collection_change = true;  // forces redraw of collections tab because reset_last_page_drawn
        browse_view_scrolls = reset_browse_view_scrolls;
        opus.table_headers_drawn = false;
        opus.gallery_begun = false;
        opus.column_chooser_drawn = false;
        o_hash.updateHash();

    },

    updatePage: function() {

        /*
        reloads the current results view from server and
        sets other views back to undrawn
        gets page/view info from from getViewInfo()
        and opus.prefs[prefix + "browse"]
        */
        o_browse.resetQuery();
        // FIX ME - RENDER BROWSE OR COLLECTION TAB, BUT DON'T CALL SAME FUNC FOR BOTH, YUCK
        o_browse.getBrowseTab();
    },

    // http://stackoverflow.com/questions/487073/jquery-check-if-element-is-visible-after-scroling thanks!
    isAlmostScrolledIntoView: function(elem) {

        var docViewTop = $(window).scrollTop() + $(window).height()/4;
        var docViewBottom = docViewTop + $(window).height();

        var elemTop = $(elem).offset().top;
        var elemBottom = elemTop + $(elem).height();
        var answer = (elemBottom >= docViewTop) && (elemTop <= docViewBottom) && (elemBottom <= docViewBottom) &&  (elemTop >= docViewTop);

        return (answer);
    },

    // columns can be reordered wrt each other in 'column chooser' by dragging them
    columnsDragged: function(element) {
        var cols = $(element).sortable('toArray');
        cols.unshift('cchoose__opusid');  // manually add opusid to this list
        $.each(cols, function(key, value)  {
            cols[key] = value.split('__')[1];
        });
        opus.prefs['cols'] = cols;
        // if we are in gallery - just change the data-struct that gallery draws from
        // if we are in table -
        // $('.gallery', '#browse').html(opus.spinner);

        // we are about to update the same page we just updated, it will replace
        // the one that is showing,

        // we are about to update the same page we just updated, it will replace
        // the one that is showing,
        // set last page to one before first page that is showing in the interface
        // now update the browse table
        if (opus.prefs.browse == "dataTable") {
            o_browse.updatePage();
        } else {
            // update the hash
            o_hash.updateHash();

            // update the underlying column data that goes with
            // thumbnails currently rendered
            var view_info = o_browse.getViewInfo();
            var prefix = view_info['prefix'];       // either 'colls_' or ''
            var pages = opus.pages_drawn[prefix + "gallery"];
            for (var i in pages) {
                o_browse.loadBrowseData(pages[i]);
            }
        }

    },

};
