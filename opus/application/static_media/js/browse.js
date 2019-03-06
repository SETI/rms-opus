var o_browse = {
    selectedImageID: "",
    keyPressAction: "",
    tableSorting: false,
    tableScrollbar: new PerfectScrollbar(".dataTable", { minScrollbarLength: 30 }),
    galleryScrollbar: new PerfectScrollbar(".gallery-contents", { suppressScrollX: true }),
    modalScrollbar: new PerfectScrollbar("#galleryViewContents .metadata"),

    // if the user entered a number/slider for page/obs number,
    // selector to set scrolltop to after data has been loaded
    galleryScrollTo: 0,

    lastLoadDataRequestNo: 0,

    allowKeydownOnMetaDataModal: true,
    /**
    *
    *  all the things that happen on the browse tab
    *
    **/
    browseBehaviors: function() {
        // note: using .on vs .click allows elements to be added dynamically w/out bind/rebind of handler

        $(".gallery-contents, .dataTable").on('scroll', _.debounce(o_browse.checkScroll, 200));

        // nav stuff
        var onRenderData = _.debounce(o_browse.loadData, 500);

        $("#browse").on('click', 'input#page', function() {
            let newPage = parseInt($("input#page").val());
            return false;
        });

        $("#browse").on('change', 'input#page', function() {
            let newPage = parseInt($("input#page").val());
            if (newPage > 0 && newPage <= opus.pages ) {
                opus.gallery_begun = false;     // so that we redraw from the beginning
                $("input#page").addClass("text-warning");
                onRenderData();
            } else {
                // put back
                $("input#page").val(opus.lastPageDrawn[opus.prefs.view]);
            }
            return false;
        });

        $("#browse").on("click", ".metadataModal", function() {
            o_browse.hideMenu();
            o_browse.renderMetadataSelector();
        });

        $("#metadataSelector").modal({
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
        $("#browse").on("click", ".download_csv", function() {
            let col_str = opus.prefs.cols.join(',');
            let hash = [];
            for (let param in opus.selections) {
                if (opus.selections[param].length){
                    hash[hash.length] = param + '=' + opus.selections[param].join(',').replace(/ /g,'+');
                }
            }
            let q_str = hash.join('&');
            let csv_link = "/opus/__api/data.csv?" + q_str + "&cols=" + col_str + "&limit=" + opus.result_count.toString() + "&order=" + opus.prefs.order.join(",");
            $(this).attr("href", csv_link);
        });

        // browse sort order - remove sort slug
        $(".sort-contents").on("click", "li .remove-sort", function() {
            let slug = $(this).parent().attr("data-slug");
            let descending = $(this).parent().attr("data-descending");
            if (descending == "true") {
                slug = "-"+slug;
            }
            let slugIndex = $.inArray(slug, opus.prefs.order);
            if (slugIndex >= 0) {
                // The clicked-on slug should always be in the order list; this is just a safety precaution
                opus.prefs.order.splice(slugIndex, 1);
            }
            o_hash.updateHash();
            o_browse.updatePage();
        });

        // browse sort order - flip sort order of a slug
        $(".sort-contents").on("click", "li .flip-sort", function() {
            let slug = $(this).parent().attr("data-slug");
            let descending = $(this).parent().attr("data-descending");

            let new_slug = slug;
            if (descending == "true") {
                slug = "-"+slug; // Old descending, new ascending
            } else {
                new_slug = "-"+slug; // Old ascending, new descending
            }
            let slugIndex = $.inArray(slug, opus.prefs.order);
            if (slugIndex >= 0) {
                // The clicked-on slug should always be in the order list; this is just a safety precaution
                opus.prefs.order[slugIndex] = new_slug;
            }
            o_hash.updateHash();
            o_browse.updatePage();
        });

        // 1 - click on thumbnail opens modal window
        // 2 - shift click - takes range from whatever the last thing you shift+clicked on and if the
        //     thing you previously shift+clicked is IN the cart, do an 'add range', otherwise
        //     do a 'remove range'. If there was nothing you previously shift+clicked on, then
        //     toggle the selection and set up for the next shift+click.
        // 3 - ctrl click - alternate way to add to cart
        // NOTE: range can go forward or backwards

        // images...
        $(".gallery").on("click", ".thumbnail", function(e) {
            // make sure selected modal thumb is unhighlighted, as clicking on this closes the modal
            // but is not caught in time before hidden.bs to get correct opusId
            e.preventDefault();
            o_browse.hideMenu();

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
          let opusId = $(this).parent().data("id");

          switch ($(this).data("icon")) {
              case "info":  // detail page
                  o_browse.hideMenu();
                  o_browse.showDetail(e, opusId);
                  break;

              case "cart":   // add to collection
                  o_browse.hideMenu();
                  let action = o_collections.toggleInCollection(opusId);
                  let buttonInfo = o_browse.cartButtonInfo(action);
                  $(this).html(`<i class="${buttonInfo.icon} fa-xs"></i>`);
                  $(this).prop("title", buttonInfo.title);
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

        // do we need an on.resize for when the user makes the screen tiny?

        $(".modal-dialog").draggable({
            handle: ".modal-content",
            cancel: ".metadata",
            drag: function( event, ui ) {
                o_browse.hideMenu();
            }
        });

        $(".app-body").on("hide.bs.modal", "#galleryView", function(e) {
            let namespace = o_browse.getViewInfo().namespace;
            $(namespace).find(".modal-show").removeClass("modal-show");
        });

        $('#galleryView').on("click", "a.select", function(e) {
            let opusId = $(this).data("id");
            if (opusId) {
                let status = o_collections.toggleInCollection(opusId) == "add" ? "" : "in";
                let buttonInfo = o_browse.cartButtonInfo(status);
                $(this).attr("title", buttonInfo.title);
                $(this).html(`<i class="${buttonInfo.icon} fa-2x float-left"></i>`);
            }
            return false;
        });

        $('#galleryView').on("click", "a.prev,a.next", function(e) {
            let action = $(this).hasClass("prev") ? "prev" : "next";
            let opusId = $(this).data("id");
            o_browse.checkIfLoadingNextPageIsNeeded(opusId);

            if (opusId) {
                o_browse.updateGalleryView(opusId);
            }
            return false;
        });

        $("#galleryView").on("click", "a.menu", function(e) {
            let opusId = $(this).data("id");
            o_browse.showMenu(e, opusId);
            return false;
        });

        // click table column header to reorder by that column
        $("#browse").on("click", ".dataTable th a",  function() {
            $(".table-page-load-status > .loader").show();
            let orderBy =  $(this).data("slug");

            let orderIndicator = $(this).find("span:last")

            if (orderIndicator.data("sort") === "sort-asc") {
                // currently ascending, change to descending order
                orderIndicator.data("sort", "sort-desc")
                orderBy = '-' + orderBy;
            } else if (orderIndicator.data("sort") === "sort-desc") {
                // currently descending, change to ascending order
                orderIndicator.data("sort", "sort-asc")
                orderBy = orderBy;
            } else {
                // not currently ordered, change to ascending
                orderIndicator.data("sort", "sort-asc")
            }
            opus.prefs['order'] = orderBy;

            o_hash.updateHash();
            opus.lastPageDrawn.browse = 0;
            opus.gallery_begun = false;     // so that we redraw from the beginning
            opus.gallery_data = {};
            opus.prefs.page = default_pages; // reset pages to 1 when col ordering changes
            o_browse.loadData(1);
            return false;
        });

        $("#obs-menu").on("click", '.dropdown-header',  function(e) {
            o_browse.hideMenu();
            return false;
        });

        $("#obs-menu").on("click", '.dropdown-item',  function(e) {
            let opusId = $(this).parent().attr("data-id");
            o_browse.hideMenu();

            switch ($(this).data("action")) {
                case "cart":  // add/remove from cart
                    o_collections.toggleInCollection(opusId);
                    break;
                case "range": // begin/end range
                    break;
                case "info":  // detail page
                    o_browse.showDetail(e, opusId);
                    break;
                case "downloadCSV":
                case "downloadCSVAll":
                case "downloadData":
                case "downloadURL":
                    document.location.href = $(this).attr("href");
                case "help":
                    break;
            }
            return false;
        });

        $("#page-slider").on("change", ".slider", function(e) {
            let page = e.target.value;
        });

        $(document).on("keydown click", function(e) {
            o_browse.hideMenu();
            // only close the help panel if the user clicked outside of the panel element
            if ($(e.target).parents("#op-help-panel").length == 0) {
                opus.hideHelpPanel();
            }
            if ((e.which || e.keyCode) == 27) { // esc - close modals
                $("#galleryView").modal('hide');
                $("#metadataSelector").modal('hide');
            }
            if ($("#galleryView").hasClass("show")) {
                /*  Catch the right/left arrow while in the modal
                    Up: 38
                    Down: 40
                    Right: 39
                    Left: 37 */
                let opusId;

                // the || is for cross-browser support; firefox does not support keyCode
                switch (e.which || e.keyCode) {
                    case 39:  // next
                        opusId = $("#galleryView").find(".next").data("id");
                        o_browse.checkIfLoadingNextPageIsNeeded(opusId);
                        break;
                    case 37:  // prev
                        opusId = $("#galleryView").find(".prev").data("id");
                        break;
                }
                if (opusId && o_browse.allowKeydownOnMetaDataModal) {
                    o_browse.updateGalleryView(opusId);
                }
            }
            // don't return false here or it will snatch all the user input!
        });
    }, // end browse behaviors

    // check if we need infiniteScroll to load next page when there is no more prefected data
    checkIfLoadingNextPageIsNeeded: function(opusId) {
        let next = $(`#browse tr[data-id=${opusId}]`).next("tr");
        let nextNext = next.next("tr");
        let nextNextId = (nextNext.data("id") ? nextNext.data("id") : "");

        // load the next page when the next next item is the dead end (no more prefected data)
        if(!nextNextId && !nextNext.hasClass("table-page")) {
            // disable keydown on modal when it's loading
            // this will make sure we have correct html elements displayed for next opus id
            if(!$("#galleryViewContents").hasClass("op-disabled")) {
                $("#galleryViewContents").addClass("op-disabled");
            }
            o_browse.allowKeydownOnMetaDataModal = false;
            $(`#${opus.prefs.view} .gallery-contents`).infiniteScroll("loadNextPage");
        }
    },

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
        // infinite scroll is attached to the gallery, so we have to force a loadData when we are in table mode
        if (opus.prefs.browse == "dataTable") {
            let bottom = $("tbody").offset().top + $("tbody").height();
            if (bottom <= $(document).height()) {
                $(`#${opus.prefs.view} .gallery-contents`).infiniteScroll("loadNextPage");
            }
        }
        return false;
    },

    showModal: function(opusId) {
        o_browse.updateGalleryView(opusId);
        $("#galleryView").modal("show");
        o_browse.modalScrollbar.update();
    },

    hideMenu: function() {
        $("#obs-menu").removeClass("show").hide();
    },

    showMenu: function(e, opusId) {
        // make this like a default right click menu
        if ($("#obs-menu").hasClass("show")) {
            o_browse.hideMenu();
        }
        let inCart = o_collections.isIn(opusId) ? "" : "in";
        let buttonInfo = o_browse.cartButtonInfo(inCart);
        $("#obs-menu .dropdown-header").html(opusId);
        $("#obs-menu .cart-item").html(`<i class="${buttonInfo.icon}"></i>${buttonInfo.title}`);
        $("#obs-menu [data-action='cart']").attr("data-id", opusId);
        $("#obs-menu [data-action='info']").attr("data-id", opusId);
        $("#obs-menu [data-action='downloadCSV']").attr("href",`/opus/__api/metadata_v2/${opusId}.csv?cols=${opus.prefs.cols.join()}`);
        $("#obs-menu [data-action='downloadCSVAll']").attr("href",`/opus/__api/metadata_v2/${opusId}.csv`);
        $("#obs-menu [data-action='downloadData']").attr("href",`/opus/__api/download/${opusId}.zip?cols=${opus.prefs.cols.join()}`);
        $("#obs-menu [data-action='downloadURL']").attr("href",`/opus/__api/download/${opusId}.zip?urlonly=1&cols=${opus.prefs.cols.join()}`);

        $("#obs-menu .dropdown-item[data-action='range']").hide();

        let namespace = `#${opus.prefs.view}`;
        let menu = {"height":$("#obs-menu").innerHeight(), "width":$("#obs-menu").innerWidth()};

        let top = ($(namespace).innerHeight() - e.pageY > menu.height) ? e.pageY-5 : e.pageY-menu.height;
        let left = ($(namespace).innerWidth() - e.pageX > menu.width)  ? e.pageX-5 : e.pageX-menu.width;

        $("#obs-menu").css({
            display: "block",
            top: top,
            left: left
        }).addClass("show")
            .attr("data-id", opusId);
    },

    showDetail: function(e, opusId) {
        opus.prefs.detail = opusId;
        if (e.shiftKey || e.ctrlKey || e.metaKey) {
            // handles command click to open in new tab
            let link = "/opus/#/" + o_hash.getHash();
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

    // columns can be reordered wrt each other in 'metadata selector' by dragging them
    metadataDragged: function(element) {
        let cols = $(element).sortable('toArray');
        cols.unshift('cchoose__opusid');  // manually add opusid to this list
        $.each(cols, function(key, value)  {
            cols[key] = value.split('__')[1];
        });
        opus.prefs.cols = cols;
    },

    addColumn: function(slug) {
        let elem = $(`#metadataSelector .allMetadata a[data-slug=${slug}]`);
        elem.find("i.fa-check").fadeIn().css('display', 'inline-block');

        let label = elem.data("qualifiedlabel");
        let info = '<i class = "fas fa-info-circle" title = "' + elem.find('*[title]').attr("title") + '"></i>';
        let html = `<li id = "cchoose__${slug}">${label}${info}<span class="unselect"><i class="far fa-trash-alt"></span></li>`
        $(".selectedMetadata > ul").append(html);
    },

    resetMetadata: function(cols, closeModal) {
        opus.prefs.cols = cols.slice();
        if (closeModal == true)
            $("#metadataSelector").modal('hide');

        // uncheck all on left; we will check them as we go
        $("#metadataSelector .allMetadata .fa-check").hide();

        // remove all from selected column
        $("#metadataSelector .selectedMetadata li").remove();

        // add them back and set the check
        $.each(cols, function(index, slug) {
            o_browse.addColumn(slug);
        });
    },

    // metadata selector behaviors
    addMetadataSelectorBehaviors: function() {
        // this is a global
        var currentSelectedMetadata = opus.prefs.cols.slice();

        $("#metadataSelector").on("hide.bs.modal", function(e) {
            // update the data table w/the new columns
            if (!o_utils.areObjectsEqual(opus.prefs.cols, currentSelectedMetadata)) {
                o_browse.resetData();
                o_browse.initTable(opus.col_labels);
                opus.prefs.page.gallery = 1;
                o_browse.loadData(1);
            }
        });

        $("#metadataSelector").on("show.bs.modal", function(e) {
            // save current column state so we can look for changes
            currentSelectedMetadata = opus.prefs.cols.slice();
        });

        $("#metadataSelector").on("shown.bs.modal", function () {
            o_browse.allMetadataScrollbar.update();
            o_browse.selectedMetadataScrollbar.update();
        });

        $('#metadataSelector .allMetadata').on("click", '.submenu li', function() {

            let elem = this;
            let slug = $(elem).data('slug');
            if (!slug) {
                if ($(this).children().length > 0) {
                     elem = $(this).children()[0];
                     slug = $(elem).data('slug');
                     if (!slug) {
                         return false;
                     }
                } else {
                    return false;
                }
            }

            let label = $(elem).data('qualifiedlabel');

            //CHANGE THESE TO USE DATA-ICON=
            let def = $(elem).find('i.fa-info-circle').attr("title");
            let selectedMetadata = $(elem).find("i.fa-check");

            if (!selectedMetadata.is(":visible")) {
                selectedMetadata.fadeIn().css("display", "inline-block");
                if ($.inArray(slug, opus.prefs.cols ) < 0) {
                    // this slug was previously unselected, add to cols
                    $(`<li id = "cchoose__${slug}">${label}<span class="info">&nbsp;<i class = "fas fa-info-circle" title = "${def}"></i>&nbsp;&nbsp;&nbsp;</span><span class="unselect"><i class="far fa-trash-alt"></span></li>`).hide().appendTo(".selectedMetadata > ul").fadeIn();
                    opus.prefs.cols.push(slug);
                }

            } else {
                selectedMetadata.hide();
                if ($.inArray(slug,opus.prefs.cols) > -1) {
                    // slug had been checked, remove from the chosen
                    opus.prefs.cols.splice($.inArray(slug,opus.prefs.cols),1);
                    $(`#cchoose__${slug}`).fadeOut(function() {
                        $(`#cchoose__${slug}`).remove();
                    });
                }
            }
            o_browse.selectedMetadataScrollbar.update();
            return false;
        });


        // removes chosen column
        $("#metadataSelector .selectedMetadata").on("click", "li .unselect", function() {
            let slug = $(this).parent().attr("id").split('__')[1];

            if ($.inArray(slug, opus.prefs.cols) >= 0) {
                // slug had been checked, removed from the chosen
                opus.prefs.cols.splice($.inArray(slug, opus.prefs.cols), 1);
                $(`#cchoose__${slug}`).fadeOut(200, function() {
                    $(this).remove();
                });
                $(`#metadataSelector .allMetadata [data-slug=${slug}]`).find("i.fa-check").hide();
            }
            o_browse.selectedMetadataScrollbar.update();
            return false;
        });
        // buttons
        $("#metadataSelector").on("click", ".btn", function() {
            switch($(this).attr("type")) {
                case "reset":
                    opus.prefs.cols = [];
                    o_browse.resetMetadata(default_columns.split(','));
                    break;
                case "submit":
                    break;
                case "cancel":
                    $('#myModal').modal('hide')
                    opus.prefs.cols = [];
                    o_browse.resetMetadata(currentSelectedMetadata, true);
                    break;
            }
        });
    },  // /addMetadataSelectorBehaviors

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
        if (opus.prefs.view == "collection") {
            namespace = "#collection";
            prefix = "colls_";
            add_to_url = "&colls=true";
        } else {
            namespace = "#browse";
            prefix = "";
            add_to_url = "";
        }
        return {"namespace":namespace, "prefix":prefix, "add_to_url":add_to_url};

    },

    getCurrentPage: function() {
        // sometimes other functions need to know current page for whatever view we
        // are currently looking at..
        let view_info = o_browse.getViewInfo();
        let namespace = view_info.namespace; // either '#collection' or '#browse'
        let prefix = view_info.prefix;       // either 'colls_' or ''
        let view_var = opus.prefs[prefix + "browse"];  // either "gallery" or "data"
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
            $(".browse_view", "#browse").attr("title", "View sortable metadata table");
            $(".browse_view", "#browse").data("view", "dataTable");

            $(".justify-content-center").show();

            o_browse.galleryScrollbar.settings.suppressScrollY = false;

            $(".gallery-contents > .ps__rail-y").removeClass("hide_ps__rail-y");
            if(!$(".dataTable > .ps__rail-y").hasClass("hide_ps__rail-y")) {
                $(".dataTable > .ps__rail-y").addClass("hide_ps__rail-y");
            }

            o_browse.galleryScrollbar.update();
        } else {
            $("." + "gallery", "#browse").hide();
            $("." + opus.prefs.browse, "#browse").fadeIn();

            $(".browse_view", "#browse").html("<i class='far fa-images'></i>&nbsp;View Gallery");
            $(".browse_view", "#browse").attr("title", "View sortable thumbnail gallery");
            $(".browse_view", "#browse").data("view", "gallery");

            // remove that extra space on top when loading table page
            $(".justify-content-center").hide();

            o_browse.galleryScrollbar.settings.suppressScrollY = true;

            if(!$(".gallery-contents > .ps__rail-y").hasClass("hide_ps__rail-y")) {
                $(".gallery-contents > .ps__rail-y").addClass("hide_ps__rail-y");
            }
            $(".dataTable > .ps__rail-y").removeClass("hide_ps__rail-y");

            o_browse.tableScrollbar.update();
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

    renderMetadataSelector: function() {
        if (!opus.metadata_selector_drawn) {
            let url = "/opus/__forms/metadata_selector.html?" + o_hash.getHash();
            $(".modal-body.metadata").load( url, function(response, status, xhr)  {

                opus.metadata_selector_drawn=true;  // bc this gets saved not redrawn
                $("#metadataSelector .op-reset-button").hide(); // we are not using this

                // since we are rendering the left side of metadata selector w/the same code that builds the select menu, we need to unhighlight the selected widgets
                o_menu.markMenuItem(".modal-body.metadata li", "unselect");

                // we keep these all open in the metadata selector, they are all closed by default
                // disply check next to any default columns
                $.each(opus.prefs.cols, function(index, col) { //CHANGE BELOW TO USE DATA-ICON=
                    $(`.modal-body.metadata li > [data-slug="${col}"]`).find("i.fa-check").fadeIn().css('display', 'inline-block');
                });

                o_browse.addMetadataSelectorBehaviors();

                o_browse.allMetadataScrollbar = new PerfectScrollbar("#metadataSelectorContents .allMetadata");
                o_browse.selectedMetadataScrollbar = new PerfectScrollbar("#metadataSelectorContents .selectedMetadata");

                // dragging to reorder the chosen
                $( ".selectedMetadata > ul").sortable({
                    items: "li",
                    cursor: "grab",
                    stop: function(event, ui) { o_browse.metadataDragged(this); }
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
                $("#collection .navbar").hide();
                $("#collection .sort-order-container").hide();
                html += '<div class="thumbnail-message">';
                html += '<h2>Your Cart is empty</h2>';
                html += '<p>To add observations to the cart, click on the Browse Results tab ';
                html += 'at the top of the page, mouse over the thumbnail gallery images to reveal the tools, ';
                html += 'then click on the cart icon.  </p>';
                html += '</div>';
            } else {
                // we've hit the end of the infinite scroll.
            }
        } else {
            $("#collection .navbar").show();
            $("#collection .sort-order-container").show();
            html += '<div class="thumb-page" data-page="'+data.page_no+'">';
            opus.lastPageDrawn[opus.prefs.view] = data.page_no;

            // add an indicator row that says this is the start of page/observation X - needs to be two hidden rows so as not to mess with the stripes
            $(".dataTable tbody").append(`<tr class="table-page" data-page="${data.page_no}"><td colspan="${data.columns.length}"></td></tr><tr class="table-page"><td colspan="${data.columns.length}"></td></tr>`);

            if(!$(".dataTable tbody").hasClass("tableBody")) {
                $(".dataTable tbody").addClass("tableBody")
            }

            $.each(page, function( index, item ) {
                let opusId = item.opusid;
                opus.gallery_data[opusId] = item.metadata;	// for galleryView, store in global array

                // gallery
                let images = item.images;
                html += `<div class="thumbnail-container ${(item.in_collection ? ' in' : '')}" data-id="${opusId}">`;
                html += `<a href="#" class="thumbnail" data-image="${images.full.url}">`;
                html += `<img class="img-thumbnail img-fluid" src="${images.thumb.url}" alt="${images.thumb.alt_text}" title="${opusId}">`;
                // whenever the user clicks an image to show the modal, we need to highlight the selected image w/an icon
                html += '<div class="modal-overlay">';
                html += '<p class="content-text"><i class="fas fa-binoculars fa-4x text-info" aria-hidden="true"></i></p>';
                html += '</div></a>';

                html += '<div class="thumb-overlay">';
                html += `<div class="tools dropdown" data-id="${opusId}">`;
                html +=     '<a href="#" data-icon="info" title="View observation detail"><i class="fas fa-info-circle fa-xs"></i></a>';

                let buttonInfo = o_browse.cartButtonInfo((item.in_collection ? 'add' : 'remove'));
                html +=     `<a href="#" data-icon="cart" title="Add to cart"><i class="${buttonInfo.icon} fa-xs"></i></a>`;
                html +=     '<a href="#" data-icon="menu"><i class="fas fa-bars fa-xs"></i></a>';
                html += '</div>';
                html += '</div></div>';

                // table row
                let checked = item.in_collection ? " checked" : "";
                let checkbox = `<input type="checkbox" name="${opusId}" value="${opusId}" class="multichoice"${checked}/>`;
                let row = `<td>${checkbox}</td>`;
                let tr = `<tr data-id="${opusId}" data-target="#galleryView">`;
                $.each(item.metadata, function(index, cell) {
                    row += `<td>${cell}</td>`;
                });
                //$(".dataTable tbody").append("<tr data-toggle='modal' data-id='"+galleryData[0]+"' data-target='#galleryView'>"+row+"</tr>");
                $(".dataTable tbody").append(tr+row+"</tr>");
            });
            html += "</div>";
        }

        $(".gallery", namespace).append(html);
        $(".table-page-load-status").hide();

        o_browse.adjustTableSize();
        o_browse.galleryScrollbar.update();

        o_hash.updateHash(true);
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

            // Assigning data attribute for table column sorting
            let icon = ($.inArray(slug, order) >= 0 ? "-down" : ($.inArray("-"+slug, order) >= 0 ? "-up" : ""));
            let columnSorting = icon === "-down" ? "sort-asc" : icon === "-up" ? "sort-desc" : "none";
            let columnOrdering = `<a href='' data-slug='${slug}'><span>${header}</span><span data-sort='${columnSorting}' class='column_ordering fas fa-sort${icon}'></span></a>`;

            $(".dataTable thead tr").append(`<th id='${slug} 'scope='col' class='sticky-header'><div>${columnOrdering}</div></th>`);
        });

        o_browse.initResizableColumn();
        o_browse.adjustTableSize();
    },

    initResizableColumn: function() {
        $("#dataTable th div").resizable({
            handles: "e",
            minWidth: 40,
            resize: function (event, ui) {
                let resizableContainerWidth = $(event.target).parent().width();
                let columnTextWidth = $(event.target).find("a span:first").width();
                let sortLabelWidth = $(event.target).find("a span:last").width();
                let columnContentWidth = columnTextWidth + sortLabelWidth;
                let beginningSpace = (resizableContainerWidth - columnContentWidth)/2;
                let columnWidthUptoEndContent = columnContentWidth + beginningSpace;

                if(ui.size.width > columnWidthUptoEndContent) {
                    $(event.target).width(ui.size.width);
                    $(event.target).parent().width(ui.size.width);
                    $(event.target).parent().height(ui.size.height);
                    $(event.target).find("div").height($(event.target).parent().height());
                } else {
                    let tableCellWidth = $(event.target).parent().width();
                    let resizableElementWidth = tableCellWidth > columnContentWidth ? tableCellWidth : columnContentWidth;
                    $(event.target).width(resizableElementWidth);
                    $(event.target).find("div").height($(event.target).parent().height());
                    // Make sure resizable handle is always at the right border of th
                    $(event.target).attr("style", "width: 100%");
                }
            },
        });
    },

    updateSortOrder: function(data) {
        let listHtml = "";
        opus.prefs.order = []
        $.each(data.order_list, function(index, order_entry) {
            let slug = order_entry.slug;
            let label = order_entry.label;
            let descending = order_entry.descending;
            let removeable = order_entry.removeable;
            listHtml += "<li class='list-inline-item'>";
            listHtml += `<span class='badge badge-pill badge-light' data-slug="${slug}" data-descending="${descending}">`;
            if (removeable) {
                listHtml += "<span class='remove-sort' title='Remove metadata field from sort'><i class='fas fa-times-circle'></i></span> ";
            }
            if (descending) {
                listHtml += "<span class='flip-sort' title='Change to ascending sort'>";
                listHtml += label;
                listHtml += " <i class='fas fa-arrow-circle-up'></i>";
            } else {
                listHtml += "<span class='flip-sort' title='Change to descending sort'>";
                listHtml += label;
                listHtml += " <i class='fas fa-arrow-circle-down'></i>";
            }
            listHtml += "</span></span></li>";
            let fullSlug = slug;
            if (descending) {
                fullSlug = "-"+slug;
            }
            opus.prefs.order.push(fullSlug);
        });
        $(".sort-contents").html(listHtml);
        o_hash.updateHash();
},

    getDataURL: function(page) {
        let view = o_browse.getViewInfo();
        let base_url = "/opus/__api/dataimages.json?";
        if (page == undefined) {
            page = opus.lastPageDrawn[opus.prefs.view]+1;
        }
        o_browse.lastLoadDataRequestNo++;
        let url = o_hash.getHash() + '&reqno=' + o_browse.lastLoadDataRequestNo + view.add_to_url;
        url = base_url + o_browse.updatePageInUrl(url, page);
        return url;
    },

    loadData: function(page) {
        //window.scrollTo(0,opus.browse_view_scrolls[opus.prefs.browse]);
        page = (page == undefined ? $("input#page").val() : page);
        $("input#page").val(page).removeClass("text-warning");

        // wait! is this page already drawn?
        if (opus.lastPageDrawn[opus.prefs.view] == page) {
            return;
        }

        let selector = `#${opus.prefs.view} .gallery-contents`;

        let url = o_browse.getDataURL(page);

        // metadata; used for both table and gallery
        start_time = new Date().getTime();
        $.getJSON(url, function(data) {
            let request_time = new Date().getTime() - start_time;
            if (data.reqno < o_browse.lastLoadDataRequestNo) {
                return;
            }
            opus.lastPageDrawn[opus.prefs.view] = data.page_no;

            if (!opus.gallery_begun) {
                o_browse.initTable(data.columns);

                if (!$(selector).data("infiniteScroll")) {
                    $(selector).infiniteScroll({
                        path: function() {
                            let path = o_browse.getDataURL();
                            return path;
                        },
                        responseType: "text",
                        status: `#${opus.prefs.view} .page-load-status`,
                        elementScroll: true,
                        history: false,
                        scrollThreshold: 500,
                        debug: false,
                    });

                    $(selector).on("request.infiniteScroll", function( event, path ) {
                        $(".table-page-load-status").show();
                    });
                    $(selector).on("scrollThreshold.infiniteScroll", function( event ) {
                        $(selector).infiniteScroll("loadNextPage");
                    });
                    $(selector).on("load.infiniteScroll", o_browse.infiniteScrollLoadEventListener);
                }
            }

            o_browse.renderGalleryAndTable(data, this.url);
            o_browse.updateSortOrder(data);

            // prefill next page
            if (!opus.gallery_begun) {
                $(selector).infiniteScroll('loadNextPage');
                opus.gallery_begun = true;
            }
            $(".table-page-load-status > .loader").hide();
        });
    },

    infiniteScrollLoadEventListener: function( event, response, path ) {
        let data = JSON.parse( response );
        if ($(`.thumb-page[data-page='${data.page_no}']`).length != 0) {
            console.log(`data.reqno: ${data.reqno}, last reqno: ${o_browse.lastLoadDataRequestNo}`);
            return;
        }
        o_browse.renderGalleryAndTable(data, path);
        // update the scroll position in the 'other' bit
        if (opus.prefs.browse == "dataTable") {
            //$(`.thumb-page[data-page='${data.page_no}']`).scrollTop(0);
        }
        //console.log('Loaded page: ' + $('#browse .gallery-contents').data('infiniteScroll').pageIndex );

        // if left/right arrow are disabled, make them clickable again
        $("#galleryViewContents").removeClass("op-disabled");
        o_browse.allowKeydownOnMetaDataModal = true;
        // $(`#${opus.prefs.view} .page-load-status .loader`).hide();
    },

    getBrowseTab: function() {
        // only draw the navbar if we are in gallery mode... doesn't make sense in collection mode
        let hide = opus.prefs.browse == "gallery" ? "dataTable" : "gallery";
        $(`${hide}#browse`).hide();

        $(`.${opus.prefs.browse}#browse`).fadeIn();

        o_browse.updateBrowseNav();
        o_browse.renderMetadataSelector();   // just do this in background so there's no delay when we want it...

        // total pages indicator
        $("#pages", "#browse").html(opus.pages);

        // figure out the page
        let page = opus.prefs.page[opus.prefs.browse]; // default: {"gallery":1, "dataTable":1, 'colls_gallery':1, 'colls_data':1 };

        // some outlier things that can go wrong with page (when user entered page #)
        page = (!page || page < 1) ? 1 : page;

        if (opus.pages && page > opus.pages) {
            // page is higher than the total number of pages, reset it to the last page
            page = opus.pages;
        }

        o_browse.loadData(page);
        o_browse.adjustBrowseHeight();
        o_browse.adjustTableSize();

        o_hash.updateHash();
    },

    adjustBrowseHeight: function() {
        let container_height = $(window).height()-120;
        $(".gallery-contents").height(container_height);
        o_browse.galleryScrollbar.update();
        //opus.limit =  (floor($(window).width()/thumbnailSize) * floor(container_height/thumbnailSize));
    },

    adjustTableSize: function() {
        let containerWidth = $(".gallery-contents").width();
        let containerHeight = $(".gallery-contents").height() - $(".app-footer").height();
        $(".dataTable").width(containerWidth);
        $(".dataTable").height(containerHeight);
        o_browse.tableScrollbar.update();
    },

    cartButtonInfo: function(status) {
        let icon = "fas fa-cart-plus";
        let title = "Add to cart";
        if (status != "in" && status != "remove") {
            icon = "far fa-trash-alt";
            title = "Remove from cart";
        }
        return  {"icon":icon, "title":title};
    },

    metadataboxHtml: function(opusId) {
        // list columns + values
        let html = "<dl>";
        $.each(opus.col_labels, function(index, columnLabel) {
            let value = opus.gallery_data[opusId][index];
            html += `<dt>${columnLabel}:</dt><dd>${value}</dd>`;
        });
        html += "</dl>";
        $("#galleryViewContents .contents").html(html);
        let next = $(`#browse tr[data-id=${opusId}]`).next("tr");
        while(next.hasClass("table-page")) {
            next = next.next("tr");
        }
        next = (next.data("id") ? next.data("id") : "");

        let prev = $(`#browse tr[data-id=${opusId}]`).prev("tr");
        while(prev.hasClass("table-page")) {
            prev = prev.prev("tr");
        }
        prev = (prev.data("id") ? prev.data("id") : "");
        // console.log(`current id: ${opusId}`);
        // console.log(`next id: ${next}`);
        // console.log(`prev id: ${prev}`);
        let status = o_collections.isIn(opusId) ? "" : "in";
        let buttonInfo = o_browse.cartButtonInfo(status);

        // prev/next buttons - put this in galleryView html...
        html = `<div class="col"><a href="#" class="select" data-id="${opusId}" title="${buttonInfo.title}"><i class="${buttonInfo.icon} fa-2x float-left"></i></a></div>`;
        html += `<div class="col text-center">`;
        if (prev != "")
            html += `<a href="#" class="prev text-center" data-id="${prev}" title="Previous image"><i class="far fa-hand-point-left fa-2x"></i></a>`;
        if (next != "")
            html += `<a href="#" class="next" data-id="${next}" title="Next image"><i class="far fa-hand-point-right fa-2x"></i></a>`;
        html += `</div>`;

        // mini-menu like the hamburger on the observation/gallery page
        html += `<div class="col"><a href="#" class="menu pr-3 float-right" data-toggle="dropdown" role="button" data-id="${opusId}"><i class="fas fa-bars fa-2x"></i></a></div>`;
        $("#galleryViewContents .bottom").html(html);
    },

    updateGalleryView: function(opusId) {
        // while modal is up, highlight the image/table row shown
        // right here need to add a CSS bit!!
        //////o_browse.toggleGalleryViewHighlight(opusId);
        let namespace = o_browse.getViewInfo().namespace;
        $(namespace).find(".modal-show").removeClass("modal-show");
        $(namespace).find(`[data-id='${opusId}'] div.modal-overlay`).addClass("modal-show");
        $(namespace).find(`tr[data-id='${opusId}']`).addClass("modal-show");
        let imageURL = $(namespace).find(`[data-id='${opusId}'] > a.thumbnail`).data("image");
        o_browse.updateMetaGalleryView(opusId, imageURL);
    },


    updateMetaGalleryView: function(opusId, imageURL) {
        $("#galleryViewContents .left").html(`<a href='${imageURL}' target='_blank'><img src='${imageURL}' title='${opusId}' class='preview'/></a>`);
        o_browse.metadataboxHtml(opusId);
        o_browse.modalScrollbar.update();
    },

    resetData: function() {
        $("#dataTable > tbody").empty();  // yes all namespaces
        $(".gallery").empty();
        opus.gallery_data = [];
        opus.lastPageDrawn = {"browse":0, "collection":0};
        opus.collection_change = true;  // forces redraw of collections tab because reset_lastPageDrawn
        opus.browse_view_scrolls = reset_browse_view_scrolls;
        opus.gallery_begun = false;
        o_hash.updateHash();
    },

    resetQuery: function() {
        /*
        when the user changes the query and all this stuff is already drawn
        need to reset all of it (todo: replace with framework!)
        */
        opus.metadata_selector_drawn = false;
        o_browse.resetData();
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
