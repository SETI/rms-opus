var o_browse = {
    selectedImageID: "",
    keyPressAction: "",
    sortIcon: "fa-sort",
    sortAscIcon: "fa-sort-up",
    sortDescIcon: "fa-sort-down",

    //scrollbar: new PerfectScrollbar("#browse .gallery-contents"),

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
            o_browse.hideMenu();
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

       $("#browse").on("click", ".get_column_chooser", function() {
           o_browse.hideMenu();
           o_browse.renderColumnChooser();
       });

       $("#columnChooser").modal({
           keyboard: false,
           backdrop: 'static',
           show: false,
       })

       // browse nav menu - the gallery/table toggle
       $("#browse").on("click", ".browse_view", function() {
           o_browse.hideMenu();
           opus.prefs.browse = $(this).data("view");

           o_hash.updateHash();
           o_browse.updateBrowseNav();

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

       // 1 - click on thumbnail opens modal window
        // 2 - shift click - takes range from whatever the last thing you clicked on and if the
        //     thing you previously clicked is IN the card, do an 'add range', otherwise
        //     do a 'remove range'.  Don't toggle the items inside the range
        // 3 - ctrl click - alternate way to add to shopping cart
        //    NOTE: range can go forward or backwards
        //

        // images...
        $(".gallery").on("click", ".thumbnail", function(e) {
            // make sure selected modal thumb is unhighlighted, as clicking on this closes the modal
            // but is not caught in time before hidden.bs to get correct opusId
            e.preventDefault();
            o_browse.hideMenu();

            let action = "add";     // just a default var decl
            let opusId = $(this).parent().data("id");
            let startElem = $(e.delegateTarget).find(".selected");

            // Detecting ctrl (windows) / meta (mac) key.
            if (e.ctrlKey || e.metaKey) {
                o_collections.toggleInCollection(opusId);
                o_browse.undoRangeSelect(e.delegateTarget);
            }
            // Detecting shift key
            else if (e.shiftKey) {
                if (startElem.length == 0) {
                    $(this).addClass("selected");
                    o_collections.toggleInCollection(opusId);
                    console.log("start range, action="+action);
                } else {
                    let fromOpusId = $(startElem).parent().data("id");
                    o_collections.toggleInCollection(fromOpusId, opusId);
                }
            } else {
                o_browse.showModal(opusId);
                o_browse.undoRangeSelect(e.delegateTarget);
            }
        });

        // data_table - clicking a table row adds to collection
        $("#dataTable").on("click", ":checkbox", function(e) {
            if ($(this).val() == "all") {
                // checkbox not currently implemented
                // pop up a warning if selection total is > 100 items,
                // with the total number to be selected...
                // if OK, use 'addall' api and loop tru all checkboxes to set them as selected
                //o_collections.editCollection("all",action);
                return false;
            }
            let opusId = $(this).val();
            let startElem = $(e.delegateTarget).find(".selected");

            if (e.shiftKey) {
                if (startElem.length == 0) {
                    $(this).closest("tr").addClass("selected");
                    o_collections.toggleInCollection(opusId);
                } else {
                    let fromOpusId = $(startElem).data("id");
                    o_collections.toggleInCollection(fromOpusId, opusId);
                }
            } else {
                o_collections.toggleInCollection(opusId);
                // single click stops range selection; shift click starts range
                o_browse.undoRangeSelect(e.delegateTarget);
            }
        });

        $("#dataTable").on("click", "td:not(:first-child)", function(e) {
            let opusId = $(this).parent().data("id");
            o_browse.showModal(opusId);
            o_browse.undoRangeSelect(e.delegateTarget);
        });

        // thumbnail overlay tools
        $('.gallery').on("click", ".tools a", function(e) {
          //snipe the id off of the image..
          var opusId = $(this).parent().data("id");

          switch ($(this).data("icon")) {
              case "info":  // detail page
                  o_browse.hideMenu();
                  o_browse.showDetail(e, opusId);
                  break;

              case "cart":   // add to collection
                  o_browse.hideMenu();
                  o_collections.toggleInCollection(opusId);
                  break;

              case "menu":  // expand, same as click on image
                  o_browse.showMenu(e, opusId);
                  break;
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
            let namespace = o_browse.getViewInfo().namespace;
            $(namespace).find(".modal-show").removeClass("modal-show");
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
                o_collections.toggleInCollection(opusId)
            }
            return false;
        });

        $('#galleryView').on("click", "a.prev,a.next", function(e) {
            let action = $(this).hasClass("prev") ? "prev" : "next";
            let opusId = $(this).data("id");
            if (opusId) {
                o_browse.updateGalleryView(opusId);
            }
            return false;
        });

        $("#browse").on("click", '.dataTable th a',  function() {
            let orderBy =  $(this).data('slug');
            let classList = $(this).find("i").attr('class').split(" ");
            let desc = $("#dataTable thead").find("."+o_browse.sortDescIcon);
            let asc = $("#dataTable thead").find("."+o_browse.sortAscIcon);
            if (asc.length > 0) {
                asc.removeClass(o_browse.sortAscIcon);
                asc.addClass(o_browse.sortIcon);
            } else if (desc.length > 0) {
                desc.removeClass(o_browse.sortDescIcon);
                desc.addClass(o_browse.sortIcon);
            }

            let orderElem = $(this).find("i");
            if ($.inArray(o_browse.sortAscIcon, classList) >= 0) {
                orderElem.addClass(o_browse.sortDescIcon);
            } else {
                orderElem.addClass(o_browse.sortAscIcon);
                orderBy = "-" + orderBy;
            }
            opus.prefs['order'] = orderBy;

            o_hash.updateHash();
            opus.last_page_drawn = $.extend(true, {}, reset_last_page_drawn)
            opus.gallery_begun = false;     // so that we redraw from the beginning
            opus.gallery_data = {};
            opus.prefs.page = default_pages; // reset pages to 1 when col ordering changes

            o_browse.loadBrowseData(1);
            return false;
        });

        // Dave: table column sorting event handler
        // click table column header to reorder by that column
        // $("#browse").on("click", ".dataTable th a",  function() {
        //     let orderBy =  $(this).data("slug");
        //     if (orderBy == "collection") {
        //         // Don't do anything if clicked on the "Selected" column
        //         return false;
        //     }
        //
        //     let order_indicator = $(this).children()
        //
        //     if (order_indicator.data("sort") === "sort-asc") {
        //         // currently ascending, change to descending order
        //         order_indicator.data("sort", "sort-desc")
        //         orderBy = '-' + orderBy;
        //     } else if (order_indicator.data("sort") === "sort-desc") {
        //         // currently descending, change to ascending order
        //         order_indicator.data("sort", "sort-asc")
        //         orderBy = orderBy;
        //     } else {
        //         // not currently ordered, change to ascending
        //         order_indicator.data("sort", "sort-asc")
        //     }
        //     opus.prefs['order'] = orderBy;
        //     opus.prefs.page = default_pages; // reset pages to 1 when col ordering changes
        //
        //     o_browse.updatePage();
        //     return false;
        // });

        $("#obs-menu").on("click", '.dropdown-item',  function(e) {
            o_browse.hideMenu();
            var opusId = $(this).parent().data("id");

            switch ($(this).data("action")) {
                case "cart":  // add/remove from cart
                    o_collections.toggleInCollection(opusId);
                    break;
                case "range": // begin/end range
                    break;
                case "info":  // detail page
                    o_browse.showDetail(e, opusId);
                    break;
                case "downloadAll":
                    break;
                case "downloadCSV":
                    break;
                case "help":
                    break;
            }
            return false;
        });

        $(document).on("keydown",function(e) {
            if ($("#galleryView").hasClass("show")) {
                /*  Catch the right/left arrow while in the modal
                    Up: 38
                    Down: 40
                    Right: 39
                    Left: 37 */
                let opusId;
                // the || is for cross-browser support; firefox does not support keyCode
                switch (e.which || e.keyCode) {
                    case 27:  // esc - close modal
                        $("#galleryView").modal('hide')
                        return;
                        break;
                    case 39:  // next
                        opusId = $("#galleryView").find(".next").data("id");
                        break;
                    case 37:  // prev
                        opusId = $("#galleryView").find(".prev").data("id");
                        break;
                }
                if (opusId) {
                    o_browse.updateGalleryView(opusId);
                }
            } else if ($("#columnChooser").hasClass("show") && e.keyCode === 27) {
                $("#columnChooser").modal('hide')
            }
            // don't return false here or it will snatch all the user input!
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

    showModal: function(opusId) {
        o_browse.updateGalleryView(opusId);
        $("#galleryView").modal("show");
    },

    hideMenu: function() {
        $("#obs-menu").removeClass("show").hide();
    },

    showMenu: function(e, opusId) {
        // make this like a default right click menu
        if ($("#obs-menu").hasClass("show")) {
            o_browse.hideMenu();
        } else {
            let top = e.pageY;
            let left = e.pageX;
            $("#obs-menu").css({
                display: "block",
                top: top,
                left: left
            }).addClass("show")
            .attr("data-id", opusId);
        }
    },

    showDetail: function(e, opusId) {
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
    },

    undoRangeSelect: function(selector) {
        let startElem = $(selector).find(".selected");
        if (startElem.length) {
            $(startElem).removeClass("selected");
        }
    },

    openDetailTab: function() {
        $("#galleryView").modal('hide');
        opus.changeTab('detail');
    },

    // columns can be reordered wrt each other in 'column chooser' by dragging them
    columnsDragged: function(element) {
        let cols = $(element).sortable('toArray');
        cols.unshift('cchoose__opusid');  // manually add opusid to this list
        $.each(cols, function(key, value)  {
            cols[key] = value.split('__')[1];
        });
        opus.prefs['cols'] = cols;
    },

    // column chooser behaviors
    addColumnChooserBehaviors: function() {
        // this is a global
        currentSelectedColumns = opus.prefs.cols.slice();

        $(".app-body").on("hide.bs.modal", "#columnChooser", function(e) {
            // update the data table w/the new columns
            if (!o_utils.areObjectsEqual(opus.prefs.cols, currentSelectedColumns)) {
                o_hash.updateHash();
                opus.last_page_drawn = $.extend(true, {}, reset_last_page_drawn)
                opus.gallery_begun = false;     // so that we redraw from the beginning
                opus.gallery_data = {};
                o_browse.loadBrowseData(1);
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

            //CHANGE THESE TO USE DATA-ICON=
            let def = $(this).find('i.fa-info-circle').attr("title");
            let addToCart = $(this).find("i.fa-shopping-cart");

            if (!addToCart.is(":visible")) {
                addToCart.fadeIn().css('display', 'inline-block');
                if ($.inArray(slug, opus.prefs.cols ) < 0) {
                    // this slug was previously unselected, add to cols
                    $('<li id = "cchoose__' + slug + '">' + label + ' <i class = "fa fa-info-circle" title = "' + def + '"></i><span class = "unselect">X</span></li>').hide().appendTo('.selectedColumns > ul').fadeIn();
                    opus.prefs.cols.push(slug);
                }

            } else {
                addToCart.hide();
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
        $('#columnChooser .selectedColumns').on("click", 'li .unselect', function() {
            let slug = $(this).parent().attr("id").split('__')[1];

            if ($.inArray(slug,opus.prefs['cols']) > -1) {
                // slug had been checked, removed from the chosen
                opus.prefs['cols'].splice($.inArray(slug,opus.prefs['cols']),1);
                $('#cchoose__' + slug).fadeOut(function() {
                    $(this).remove();
                });
            }
            return false;
        });
    },  // /addColumnChooserBehaviors

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
            $("." + "dataTable", "#browse").hide();
            $("." + opus.prefs.browse, "#browse").fadeIn();

            $(".browse_view", "#browse").html("<i class='far fa-list-alt'></i>&nbsp;View Table");
            $(".browse_view", "#browse").attr("title", "Click to view sortable table");
            $(".browse_view", "#browse").data("view", "dataTable");
        } else {
            $("." + "gallery", "#browse").hide();
            $("." + opus.prefs.browse, "#browse").fadeIn();

            $(".browse_view", "#browse").html("<i class='far fa-images'></i>&nbsp;View Gallery");
            $(".browse_view", "#browse").attr("title", "Click to view sortable gallery");
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
                $.each(opus.prefs['cols'], function(index, col) { //CHANGE BELOW TO USE DATA-ICON=
                    $('.column_chooser li > [data-slug="'+col+'"]').find("i.fa-shopping-cart").fadeIn().css('display', 'inline-block');
                });

                o_browse.addColumnChooserBehaviors();

                // dragging to reorder the chosen
                $( ".selectedColumns > ul").sortable({
                    items: "li:not(.unsortable)",
                    cursor: 'move',
                    stop: function(event, ui) { o_browse.columnsDragged(this); }
                });
            });
        }
    },

    renderGalleryAndTable: function(data, url) {
        // render the gallery and table at the same time.
        // gallery is var html; table is row/tr/td.

        let namespace = o_browse.getViewInfo().namespace;
        let page = data.page;
        var html = "";

        if (data.count == 0) {
            // either there are no selections OR this is signaling the end of the infinite scroll
            // for now, just post same message to both #browse & #collections tabs
            if (data.page_no == 1) {
                html += '<div class="thumbnail-message">';
                html += '<h2>You Have No Selections</h2>';
                html += '<p>To select observations, click on the Browse Results tab ';
                html += 'at the top of the page,<br> mouse over the thumbnail gallery images to reveal the tools,';
                html += 'then click the <br>checkbox below a thumbnail.  </p>';
                html += '</div>';
            } else {
                // we've hit the end of the infinite scroll.
            }
        } else {
            html += '<div class="thumb-page" data-page="'+data.page_no+'">';
            $.each(page, function( index, item ) {
                let opusId = item.opusid;
                opus.gallery_data[opusId] = item.metadata;	// for galleryView, store in global array

                // gallery
                let images = item.images;
                html += '<div class="thumbnail-container'+(item.in_collection ? ' in' : '')+'" data-id="'+opusId+'">';
                html += '<a href="#" class="thumbnail" data-image="'+images.full.url+'">';
                html += '<img class="img-thumbnail img-fluid" src="'+images.thumb.url+'" alt="'+images.thumb.alt_text+'" title="'+opusId+'">';
                // whenever the user clicks an image to show the modal, we need to highlight the selected image w/an icon
                html += '<div class="modal-overlay">';
                html += '<p class="content-text"><i class="fa fa-street-view fa-4x text-info" aria-hidden="true"></i></p>';
                html += '</div></a>';

                html += '<div class="thumb-overlay">';
                if (opus.prefs.view == "browse") {
                    html += '<div class="tools dropdown" data-id="'+opusId+'">';
                    html +=     '<a href="#" data-icon="info"><i class="fas fa-info-circle fa-xs"></i></a>';
                    html +=     '<a href="#" data-icon="cart"><i class="fas fa-shopping-cart fa-xs"></i></a>';
                    html +=     '<a href="#" data-icon="menu"><i class="fas fa-ellipsis-v fa-xs"></i></a>';
                    html += '</div>';
                } else {
                    // this will only display if the user has shift-click to remove the image from the cart
                    html += '<a href="#" class="remove"><i class="fas fa-times fa-7x"></i></a>';
                }
                html += '</div></div>';

                // table row
                let checked = item.in_collection ? " checked" : "";
                let checkbox = "<input type='checkbox' name='"+opusId+"' value='"+opusId+"' class='multichoice'"+checked+"/>";
                let row = "<td>"+checkbox+"</td>";
                let tr = "<tr data-id='"+opusId+"' data-target='#galleryView'>";
                $.each(item.metadata, function(index, cell) {
                    row += "<td>"+cell+"</td>";
                });
                //$(".dataTable tbody").append("<tr data-toggle='modal' data-id='"+galleryData[0]+"' data-target='#galleryView'>"+row+"</tr>");
                $(".dataTable tbody").append(tr+row+"</tr>");
            });
            html += '</div>';
        }
        $('.gallery', namespace).append(html);
    },

    initTable: function(columns) {
        // prepare table and headers...
        $(".dataTable thead > tr > th").detach();
        $(".dataTable tbody > tr").detach();

        // NOTE:  At some point, ORDER needs to be identified in the table, as to which column we are ordering on

        // because i need the slugs for the columns
        let hashArray = o_hash.getHashArray();
        let slugs = hashArray["cols"].split(",");
        let order = hashArray["order"].split(",");

        opus.col_labels = columns;

        // check all box
        //let checkbox = "<input type='checkbox' name='all' value='all' class='multichoice'>";
        $(".dataTable thead tr").append("<th scope='col' class='sticky-header'></th>");
        $.each(columns, function( index, header) {
            let slug = slugs[index];

            // Dave: assigning data attribute for table column sorting
            // let icon = ($.inArray(slug, order) >= 0 ? o_browse.sortDescIcon : ($.inArray("-"+slug, order) >= 0 ? o_browse.sortAscIcon : o_browse.sortIcon));
            // let columnSorting = icon === o_browse.sortDescIcon ? "sort-asc" : icon === o_browse.sortAscIcon ? "sort-desc" : "none";
            // let columnOrdering = `<div class='column_ordering'><a href='' data-slug='${slug}'><i data-sort='${columnSorting}' class='fas `+icon+"'></i></a></div>";

            let icon = ($.inArray(slug, order) >= 0 ? o_browse.sortDescIcon : ($.inArray("-"+slug, order) >= 0 ? o_browse.sortAscIcon : o_browse.sortIcon));
            let columnOrdering = "<div class='column_ordering'><a href='' data-slug='"+slug+"'><i class='fas "+icon+"'></i></a></div>";

            $(".dataTable thead tr").append("<th id='"+slug+" 'scope='col' class='sticky-header'>"+header+columnOrdering+"</th>");
        });
        $(".dataTable th").resizable({
            handles: "e",
            minWidth: 40,
            resize: function (event, ui) {
              $(event.target).width(ui.size.width);
            }
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
        let base_url = "/opus/__api/dataimages.json?";
        let url = o_hash.getHash() + '&reqno=' + opus.lastRequestNo + view.add_to_url;

        url = o_browse.updatePageInUrl(url, page);

        // metadata; used for both table and gallery
        start_time = new Date().getTime();
        $.getJSON(base_url + url, function(data) {
            let request_time = new Date().getTime() - start_time;
            console.log(request_time);

            if (!opus.gallery_begun) {
                o_browse.initTable(data.columns);
                // for infinite scroll
                $('#browse .gallery-contents').infiniteScroll({
                    path: o_browse.updatePageInUrl(this.url, "{{#}}"),
                    responseType: 'text',
                    status: '#browse .page-load-status',
                    elementScroll: true,
                    history: false,
                    scrollThreshold: 500,
                    debug: true,
                });
                $('#browse .gallery-contents').on( 'request.infiniteScroll', function( event, response, path ) {
                    reqStart = new Date().getTime();
                });
                $('#browse .gallery-contents').on( 'load.infiniteScroll', function( event, response, path ) {
                    let request_time = new Date().getTime() - reqStart;
                    console.log("load: "+request_time);

                    let jsonData = JSON.parse( response );
                    o_browse.renderGalleryAndTable(jsonData, path);

                    console.log('Loaded page: ' + $('#browse .gallery-contents').data('infiniteScroll').pageIndex );
                });
            }

            o_browse.renderGalleryAndTable(data, this.url);

            if (!opus.gallery_begun) {
                $('#browse .gallery-contents').infiniteScroll('loadNextPage');
                opus.gallery_begun = true;
            }
        });

        // ew.  this needs to be dealt with, as table/gallery are always drawn at same time
        opus.last_page_drawn["dataTable"] = page;
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
        o_browse.adjustBrowseHeight();

        $("input#page").val(page).css("color","initial");
        o_hash.updateHash();
    },

    adjustBrowseHeight: function() {
        let container_height = $(window).height()-120;
        $(".gallery-contents").height(container_height);
        //o_browse.scrollbar.update();
        //opus.limit =  (floor($(window).width()/thumbnailSize) * floor(container_height/thumbnailSize));
    },

    metadataboxHtml: function(opusId) {
        // list columns + values
        let html = "<dl>";
        $.each(opus.col_labels, function(index, columnLabel) {
            let value = opus.gallery_data[opusId][index];
            html += "<dt>" + columnLabel + ":</dt><dd>" + value + "</dd>";
        });

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
        html += "<a href='#' class='select' data-id='"+opusId+"' title='Add to selections'><i class='fas fa-shopping-cart fa-2x float-left'></i></a>";
        html += "<a href='#' class='next pr-5' data-id='"+next+"' title='Next image'><i class='far fa-hand-point-right fa-2x float-right'></i></a>";
        html += "<a href='#' class='prev pr-5' data-id='"+prev+"' title='Previous image'><i class='far fa-hand-point-left fa-2x float-right'></i></a></div>";
        return html;
    },

    updateGalleryView: function(opusId) {
        // while modal is up, highlight the image/table row shown
        // right here need to add a CSS bit!!
        //////o_browse.toggleGalleryViewHighlight(opusId);
        let namespace = o_browse.getViewInfo().namespace;
        $(namespace).find(".modal-show").removeClass("modal-show");
        $(namespace).find("[data-id='"+opusId+"'] div.modal-overlay").addClass("modal-show");
        $(namespace).find("tr[data-id='"+opusId+"']").addClass("modal-show");
        let imageURL = $(namespace).find("[data-id='"+opusId+"'] > a.thumbnail").data("image");
        if (imageURL === undefined) {
            // put a temp spinner while retrieving the image; this only happens if the data table is loaded first
            $("#galleryViewContents").html(o_browse.loader + o_browse.metadataboxHtml(opusId));
            $("#galleryViewContents").data("id", opusId);

            let url = "/opus/__api/image/full/" + opusId + ".json";
            $.getJSON(url, function(imageData) {
                var imageURL = imageData['data'][0]['url'];
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
        opus.last_page_drawn = {"gallery":0, "dataTable":0, "colls_gallery":0, "colls_data":0 };
        opus.collection_change = true;  // forces redraw of collections tab because reset_last_page_drawn
        opus.browse_view_scrolls = reset_browse_view_scrolls;
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
};
