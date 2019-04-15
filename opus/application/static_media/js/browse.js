var o_browse = {
    selectedImageID: "",
    keyPressAction: "",
    tableSorting: false,
    tableScrollbar: new PerfectScrollbar("#browse .dataTable", {
        minScrollbarLength: opus.minimumPSLength
    }),
    galleryScrollbar: new PerfectScrollbar("#browse .gallery-contents", {
        suppressScrollX: true,
        minScrollbarLength: opus.minimumPSLength
    }),
    modalScrollbar: new PerfectScrollbar("#galleryViewContents .metadata", {
        minScrollbarLength: opus.minimumPSLength
    }),

    // if the user entered a number/slider for page/obs number,
    // selector to set scrolltop to after data has been loaded
    galleryBegun: false, // have we started the gallery view
    galleryData: {},  // holds gallery column data

    galleryScrollTo: 0,
    metadataSelectorDrawn: false,

    lastLoadDataRequestNo: 0,

    galleryBoundingRect: {'x': 0, 'y': 0},
    gallerySliderStep: 10,

    infiniteScrollCurrentMaxPageNumber: 0, // the largest drawn page number
    infiniteScrollCurrentMinPageNumber: 1000, // prev page of the smallest drawn page number
    loadPrevPage: false,
    currentPage: 1,
    currentOpusId: "",
    tempHash: "",
    dataNotAvailable: false,
    onRenderData: false,
    /**
    *
    *  all the things that happen on the browse tab
    *
    **/
    browseBehaviors: function() {
        // note: using .on vs .click allows elements to be added dynamically w/out bind/rebind of handler

        $(".gallery-contents, .dataTable").on('scroll', _.debounce(o_browse.checkScroll, 500));

        $(".gallery-contents, .dataTable").on('wheel ps-scroll-up', function(event) {
            if (o_browse.infiniteScrollCurrentMinPageNumber > 0) {
                if (opus.prefs.browse === "dataTable" && $(".dataTable").scrollTop() === 0) {
                    opus.lastPageDrawn[opus.prefs.view] = o_browse.infiniteScrollCurrentMinPageNumber - 1;
                    $(`#${opus.prefs.view} .gallery-contents`).infiniteScroll("loadNextPage");
                } else if (opus.prefs.browse === "gallery" && $(".gallery-contents").scrollTop() === 0) {
                    opus.lastPageDrawn[opus.prefs.view] = o_browse.infiniteScrollCurrentMinPageNumber - 1;
                    $(`#${opus.prefs.view} .gallery-contents`).infiniteScroll("loadNextPage");
                }
            }
        });
        // testing area for scrollbar event, will remove it later
        // $(".gallery-contents, .dataTable").bind('mousewheel DOMMouseScroll', function(event) {
        //     console.log("scroll up when it reaches to the top end")
        // });

        // nav stuff - NOTE - this needs to be a global
        o_browse.onRenderData = _.debounce(o_browse.loadData, 500);

        $("#browse").on("click", ".metadataModal", function() {
            o_browse.hideMenu();
            o_browse.renderMetadataSelector();
        });

        $("#metadataSelector").modal({
            keyboard: false,
            backdrop: 'static',
            show: false,
        });

        // browse nav menu - the gallery/table toggle
        $("#browse").on("click", ".browse_view", function() {
            o_browse.hideMenu();
            opus.prefs.browse = $(this).data("view");

            o_hash.updateHash();
            o_browse.updateBrowseNav();

            // reset scroll position
            window.scrollTo(0, 0); // restore previous scroll position

            return false;
        });

        // browse nav menu - download csv
        $("#browse").on("click", ".download_csv", function() {
            let col_str = opus.prefs.cols.join(',');
            let hash = [];
            for (let param in opus.selections) {
                if (opus.selections[param].length) {
                    hash[hash.length] = param + '=' + opus.selections[param].join(',').replace(/ /g,'+');
                }
            }
            let q_str = hash.join('&');
            let csv_link = "/opus/__api/data.csv?" + q_str + "&cols=" + col_str + "&limit=" + opus.result_count.toString() + "&order=" + opus.prefs.order.join(",");
            $(this).attr("href", csv_link);
        });

        // browse sort order - remove sort slug
        $(".sort-contents").on("click", "li .remove-sort", function() {
            $(".op-page-loading-status > .loader").show();
            let slug = $(this).parent().attr("data-slug");
            let descending = $(this).parent().attr("data-descending");
            o_browse.tableSorting = true;

            if (descending == "true") {
                slug = "-"+slug;
            }
            let slugIndex = $.inArray(slug, opus.prefs.order);
            if (slugIndex >= 0) {
                // The clicked-on slug should always be in the order list; this is just a safety precaution
                opus.prefs.order.splice(slugIndex, 1);
            }
            o_hash.updateHash();
            // o_browse.updatePage();
            o_browse.renderSortedDataFromBeginning();
        });

        // browse sort order - flip sort order of a slug
        $(".sort-contents").on("click", "li .flip-sort", function() {
            $(".op-page-loading-status > .loader").show();
            let slug = $(this).parent().attr("data-slug");
            let descending = $(this).parent().attr("data-descending");
            o_browse.tableSorting = true;

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
            // o_browse.updatePage();
            o_browse.renderSortedDataFromBeginning();
        });

        // 1 - click on thumbnail opens modal window
        // 2-  Shift+click or menu/"Start Add[Remove] Range Here" starts a range
        //          Shfit+click on menu/"End Add[Remove] Range Here" ends a range
        //          Clicking on a cart/trash can anywhere aborts the range selection
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
                o_cart.toggleInCart(opusId);
                o_browse.undoRangeSelect();
            }
            // Detecting shift key
            else if (e.shiftKey) {
                if (startElem.length == 0) {
                    o_browse.startRangeSelect(opusId);
                    //o_cart.toggleInCart(opusId);
                } else {
                    let fromOpusId = $(startElem).data("id");
                    o_cart.toggleInCart(fromOpusId, opusId);
                }
            } else {
                o_browse.showModal(opusId);
            }
        });

        // data_table - clicking a table row adds to cart
        $("#dataTable").on("click", ":checkbox", function(e) {
            if ($(this).val() == "all") {
                // checkbox not currently implemented
                // pop up a warning if selection total is > 100 items,
                // with the total number to be selected...
                // if OK, use 'addall' api and loop tru all checkboxes to set them as selected
                //o_cart.editCart("all",action);
                return false;
            }
            let opusId = $(this).val();
            let startElem = $(`#${opus.prefs.view} .thumb.gallery`).find(".selected");

            if (e.shiftKey) {
                if (startElem.length == 0) {
                    o_browse.startRangeSelect(opusId);
                    //o_cart.toggleInCart(opusId);
                } else {
                    let fromOpusId = $(startElem).data("id");
                    o_cart.toggleInCart(fromOpusId, opusId);
                }
            } else {
                o_cart.toggleInCart(opusId);
                // single click stops range selection; shift click starts range
                o_browse.undoRangeSelect();
            }
        });

        $("#dataTable").on("click", "td:not(:first-child)", function(e) {
            let opusId = $(this).parent().data("id");
            o_browse.showModal(opusId);
            o_browse.undoRangeSelect();
        });

        // thumbnail overlay tools
        $('.gallery, #dataTable').on("click", ".op-tools a", function(e) {
          //snipe the id off of the image..
          let opusId = $(this).parent().data("id");

          switch ($(this).data("icon")) {
              case "info":  // detail page
                  o_browse.hideMenu();
                  o_browse.showDetail(e, opusId);
                  break;

              case "cart":   // add to cart
                  o_browse.hideMenu();
                  // clicking on the cart/trash can aborts range select
                  o_browse.undoRangeSelect();

                  let action = o_cart.toggleInCart(opusId);
                  o_browse.updateCartIcon(opusId, action);
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
            drag: function(event, ui) {
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
                // clicking on the cart/trash can aborts range select
                o_browse.undoRangeSelect();
                o_cart.toggleInCart(opusId);
            }
            return false;
        });

        $('#galleryView').on("click", "a.prev,a.next", function(e) {
            let action = $(this).hasClass("prev") ? "prev" : "next";
            let opusId = $(this).data("id");

            if (action === "next") {
                o_browse.checkIfLoadNextPageIsNeeded(opusId);
            } else if (action === "prev") {
                o_browse.checkIfLoadPrevPageIsNeeded(opusId);
            }

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
            // show this spinner right away when table is clicked
            // we will hide page status loader from infiniteScroll if op-page-loading-status loader is spinning
            $(".op-page-loading-status > .loader").show();
            let orderBy =  $(this).data("slug");

            let orderIndicator = $(this).find("span:last");
            o_browse.tableSorting = true;
            if (orderIndicator.data("sort") === "sort-asc") {
                // currently ascending, change to descending order
                orderIndicator.data("sort", "sort-desc");
                orderBy = '-' + orderBy;
            } else if (orderIndicator.data("sort") === "sort-desc") {
                // currently descending, change to ascending order
                orderIndicator.data("sort", "sort-asc");
                orderBy = orderBy;
            } else {
                // not currently ordered, change to ascending
                orderIndicator.data("sort", "sort-asc");
            }

            opus.prefs.order = orderBy;
            o_hash.updateHash();
            o_browse.renderSortedDataFromBeginning();

            return false;
        });

        $("#op-obs-menu").on("click", '.dropdown-header',  function(e) {
            o_browse.hideMenu();
            return false;
        });

        $("#op-obs-menu").on("click", '.dropdown-item',  function(e) {
            let opusId = $(this).parent().attr("data-id");
            o_browse.hideMenu();

            switch ($(this).data("action")) {
                case "cart":  // add/remove from cart
                    o_cart.toggleInCart(opusId);
                    // clicking on the cart/trash can aborts range select
                    o_browse.undoRangeSelect();
                    break;
                case "range": // begin/end range
                    let startElem = $(`#${opus.prefs.view}`).find(".selected");
                    if (startElem.length == 0) {
                        o_browse.startRangeSelect(opusId);
                        //o_cart.toggleInCart(opusId);
                    } else {
                        let fromOpusId = $(startElem).data("id");
                        o_cart.toggleInCart(fromOpusId, opusId);
                    }
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

        $("#op-observation-slider").slider({
            animate: true,
            value: 1,
            min: 1,
            max: 1000,
            step: o_browse.gallerySliderStep,
            slide: function(event, ui) {
                o_browse.onUpdateSliderHandle(ui.value);
            },
            stop: function(event, ui) {
                o_browse.onUpdateSlider(ui.value);
            }
        });

        $(document).on("keydown click", function(e) {
            o_browse.hideMenu();

            if ((e.which || e.keyCode) == 27) { // esc - close modals
                $("#galleryView").modal('hide');
                $("#metadataSelector").modal('hide');
                opus.hideHelpPanel();
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
                        o_browse.checkIfLoadNextPageIsNeeded(opusId);
                        break;
                    case 37:  // prev
                        opusId = $("#galleryView").find(".prev").data("id");
                        o_browse.checkIfLoadPrevPageIsNeeded(opusId);
                        break;
                }
                if (opusId && !$("#galleryViewContents").hasClass("op-disabled")) {
                    o_browse.updateGalleryView(opusId);
                }
            }
            // don't return false here or it will snatch all the user input!
        });
    }, // end browse behaviors

    renderSortedDataFromBeginning: function() {
        opus.lastPageDrawn.browse = 0;
        opus.prefs.page = default_pages; // reset pages to 1 when col ordering changes

        o_browse.galleryBegun = false;     // so that we redraw from the beginning
        o_browse.galleryData = {};
        o_browse.loadData(1);
    },

    // check if we need infiniteScroll to load next page when there is no more prefected data
    checkIfLoadNextPageIsNeeded: function(opusId) {
        if (!opusId) {
            return;
        }
        let next = $(`#browse tr[data-id=${opusId}]`).next("tr");
        let nextNext = next.next("tr");
        let nextNextId = (nextNext.data("id") ? nextNext.data("id") : "");

        if (opus.lastPageDrawn[opus.prefs.view] < o_browse.infiniteScrollCurrentMaxPageNumber) {
            opus.lastPageDrawn[opus.prefs.view] = o_browse.infiniteScrollCurrentMaxPageNumber;
        }

        // load the next page when the next next item is the dead end (no more prefected data)
        if (!nextNextId && !nextNext.hasClass("table-page")) {
            // If data reaches to the end, we don't need to load next page
            // this will make sure we have correct html elements displayed for next opus id
            if (!o_browse.dataNotAvailable) {
                // disable keydown on modal when it's loading
                $("#galleryViewContents").addClass("op-disabled");
                $(`#${opus.prefs.view} .gallery-contents`).infiniteScroll("loadNextPage");
            }
        }
    },

    checkIfLoadPrevPageIsNeeded: function(opusId) {
        o_browse.currentOpusId = opusId;
        if (!opusId) {
            return;
        }
        let prev = $(`#browse tr[data-id=${opusId}]`).prev("tr");
        while (prev.hasClass("table-page")) {
            prev = prev.prev("tr");
            if (prev.data("page")) {
                // if (o_browse.infiniteScrollCurrentMinPageNumber > (prev.data("page") - 1) && prev.data("page") > 0) {
                // if (o_browse.infiniteScrollCurrentMinPageNumber > prev.data("page")) {
                    o_browse.infiniteScrollCurrentMinPageNumber = prev.data("page") - 1;

            }
        }
        prev = (prev.data("id") ? prev.data("id") : "");

        if (!prev && o_browse.infiniteScrollCurrentMinPageNumber > 0) {
            if (opus.lastPageDrawn[opus.prefs.view] >= o_browse.infiniteScrollCurrentMinPageNumber) {
                opus.lastPageDrawn[opus.prefs.view] = o_browse.infiniteScrollCurrentMinPageNumber - 1;
            }
            // disable keydown on modal when it's loading
            // this will make sure we have correct html elements displayed for prev opus id
            $("#galleryViewContents").addClass("op-disabled");

            $(`#${opus.prefs.view} .gallery-contents`).infiniteScroll("loadNextPage");

        }
    },

    setScrollbarOnSlide: function(obsNum) {
        let namespace = o_browse.getViewInfo().namespace;
        let galleryTargetTopPosition = $(`${namespace} .thumbnail-container[data-obs="${obsNum}"]`).offset().top;
        let galleryContainerTopPosition = $(".gallery-contents").offset().top;
        let galleryScrollbarPosition = $(".gallery-contents").scrollTop();

        let galleryTargetFinalPosition = galleryTargetTopPosition - galleryContainerTopPosition + galleryScrollbarPosition;
        $(".gallery-contents").scrollTop(galleryTargetFinalPosition);

        // Create a new jQuery.Event object with specified event properties.
        //let e = jQuery.Event( "DOMMouseScroll",{delta: -650} );

        // trigger an artificial DOMMouseScroll event with delta -650
        //$( ".gallery-contents" ).trigger( e );

        /* make sure it's scrolled to the correct position in table view
        let tableTargetTopPosition = $(`#dataTable tbody tr[data-obs='${obsNum}']`).offset().top;
        let tableContainerTopPosition = $(".dataTable").offset().top;
        let tableScrollbarPosition = $(".dataTable").scrollTop();
        let tableTargetFinalPosition = tableTargetTopPosition - tableContainerTopPosition + tableScrollbarPosition
        $(`${namespace} .dataTable`).scrollTop(tableTargetFinalPosition);*/
    },

    // called when the slider is moved...
    onUpdateSliderHandle: function(value) {
        value = (value == undefined? 1 : value);
        $("#op-observation-number").html(value);
    },

    onUpdateSlider: function(value) {
        // temp til we get rid of page
        opus.prefs.page[opus.prefs.browse] = Math.ceil(value/opus.prefs.limit);
        let namespace = o_browse.getViewInfo().namespace;
        let elem = $(`${namespace} .thumbnail-container[data-obs="${value}"]`);
        if (elem.length > 0) {
            o_browse.setScrollbarOnSlide(value);
        } else {
            o_browse.onRenderData();
        }
    },

    // find the first displayed observation index & id in the upper left corner
    updateSliderHandle: function() {
        let selector = (opus.prefs.browse === "dataTable") ? `#${opus.prefs.view} #dataTable tbody tr` : `#${opus.prefs.view} .gallery .thumbnail-container`;
        $(selector).each(function(index, elem) {
            if ($(elem).offset().top > $(".gallery-contents").offset().top) {
                let obsNum = $(elem).data("obs");
                $("#op-observation-number").html(obsNum);
                $(".op-slider-pointer").css("width", `${opus.result_count.toString().length*0.7}em`);
                // just make the step size the number of the obserations across the page...
                // if the observations have not yet been rendered, leave the default, it will get changed later
                if (o_browse.galleryBoundingRect.x > 0) {
                    o_browse.gallerySliderStep = o_browse.galleryBoundingRect.x;
                }
                $("#op-observation-slider").slider({
                    "value": obsNum,
                    "step": o_browse.gallerySliderStep,
                    "max": opus.result_count,
                });
                return false;
            }
        });
    },

    checkScroll: function() {
        // infinite scroll is attached to the gallery, so we have to force a loadData when we are in table mode
        if (opus.prefs.browse == "dataTable") {
            let bottom = $("tbody").offset().top + $("tbody").height();
            if (bottom <= $(document).height()) {
                if (opus.lastPageDrawn[opus.prefs.view] < o_browse.infiniteScrollCurrentMaxPageNumber) {
                    opus.lastPageDrawn[opus.prefs.view] = o_browse.infiniteScrollCurrentMaxPageNumber;
                }
                // remove spinner when scrollThreshold is triggered and last data fetching has no data
                // Need to revisit this one
                if (o_browse.dataNotAvailable) {
                    $(".infinite-scroll-request").hide();
                }
                $(`#${opus.prefs.view} .gallery-contents`).infiniteScroll("loadNextPage");
            }
        } else {
            $(".gallery .thumb-page").each(function(index, elem) {
                let position = $(elem).children().offset();
                if (position) {
                    if (position.top > 0 && (position.top < $(".gallery-contents").height()-100)) {
                        // Update page number
                        let page = $(elem).data("page");
                        opus.prefs.page[opus.prefs.browse] = page;
                        console.log("page: "+page);
                        o_browse.currentPage = page;
                        return false;
                    }
                }
            });
            opus.lastPageDrawn[opus.prefs.view] = Math.max(o_browse.currentPage, opus.lastPageDrawn[opus.prefs.view], o_browse.infiniteScrollCurrentMaxPageNumber);
        }
        o_browse.updateSliderHandle();
        return false;
    },

    showModal: function(opusId) {
        o_browse.checkIfLoadPrevPageIsNeeded(opusId);
        o_browse.updateGalleryView(opusId);
        $("#galleryView").modal("show");
    },

    hideMenu: function() {
        $("#op-obs-menu").removeClass("show").hide();
    },

    showMenu: function(e, opusId) {
        // make this like a default right click menu
        if ($("#op-obs-menu").hasClass("show")) {
            o_browse.hideMenu();
        }
        let inCart = (o_cart.isIn(opusId) ? "" : "in");
        let buttonInfo = o_browse.cartButtonInfo(inCart);
        $("#op-obs-menu .dropdown-header").html(opusId);
        $("#op-obs-menu .cart-item").html(`<i class="${buttonInfo.icon}"></i>${buttonInfo.title}`);
        $("#op-obs-menu [data-action='cart']").attr("data-id", opusId);
        $("#op-obs-menu [data-action='info']").attr("data-id", opusId);
        $("#op-obs-menu [data-action='downloadCSV']").attr("href",`/opus/__api/metadata_v2/${opusId}.csv?cols=${opus.prefs.cols.join()}`);
        $("#op-obs-menu [data-action='downloadCSVAll']").attr("href",`/opus/__api/metadata_v2/${opusId}.csv`);
        $("#op-obs-menu [data-action='downloadData']").attr("href",`/opus/__api/download/${opusId}.zip?cols=${opus.prefs.cols.join()}`);
        $("#op-obs-menu [data-action='downloadURL']").attr("href",`/opus/__api/download/${opusId}.zip?urlonly=1&cols=${opus.prefs.cols.join()}`);

        // use the state of the current selected observation to set the icons if one has been selected,
        // otherwise use the state of the current observation - this will identify what will happen to the range
        let selectedElem = $(`#${opus.prefs.view}`).find(".selected");
        if (selectedElem.length != 0) {
            inCart = (o_cart.isIn($(selectedElem).data("id")) ? "" : "in");
        }
        let addRemoveText = (inCart != "in" ? "remove range from" : "add range to");

        let rangeText = (selectedElem.length === 0 ?
                            `<i class='fas fa-sign-out-alt'></i>Start ${addRemoveText} cart here` :
                            `<i class='fas fa-sign-out-alt fa-rotate-180'></i>End ${addRemoveText} cart here`);
        $("#op-obs-menu .dropdown-item[data-action='range']").html(rangeText);

        let namespace = `#${opus.prefs.view}`;
        let menu = {"height":$("#op-obs-menu").innerHeight(), "width":$("#op-obs-menu").innerWidth()};

        let top = ($(namespace).innerHeight() - e.pageY > menu.height) ? e.pageY-5 : e.pageY-menu.height;
        let left = ($(namespace).innerWidth() - e.pageX > menu.width)  ? e.pageX-5 : e.pageX-menu.width;

        $("#op-obs-menu").css({
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

    getGalleryElement: function(opusId) {
        return $(`#${opus.prefs.view} .thumbnail-container[data-id=${opusId}]`);
    },

    getDataTableInputElement: function(opusId) {
        return $(`#dataTable div[data-id=${opusId}]`).parent();
    },

    startRangeSelect: function(opusId) {
        o_browse.undoRangeSelect(); // probably not necessary...
        o_browse.getGalleryElement(opusId).addClass("selected hvr-ripple-in b-a-2");
        o_browse.getDataTableInputElement(opusId).addClass("hvr-ripple-in b-a-2");
    },

    undoRangeSelect: function() {
        let startElem = $(`#${opus.prefs.view}`).find(".selected");
        if (startElem.length) {
            $(startElem).removeClass("selected hvr-ripple-in b-a-2");
            let opusId = $(startElem).data("id");
            o_browse.getDataTableInputElement(opusId).removeClass("hvr-ripple-in b-a-2");
        }
    },

    openDetailTab: function() {
        $("#galleryView").modal("hide");
        opus.changeTab("detail");
    },

    // columns can be reordered wrt each other in 'metadata selector' by dragging them
    metadataDragged: function(element) {
        let cols = $.map($(element).sortable("toArray"), function(item) {
            return item.split("__")[1];
        });
        opus.prefs.cols = cols;
    },

    addColumn: function(slug) {
        let elem = $(`#metadataSelector .allMetadata a[data-slug=${slug}]`);
        elem.find("i.fa-check").fadeIn().css("display", "inline-block");

        let label = elem.data("qualifiedlabel");
        let info = '<i class = "fas fa-info-circle" title = "' + elem.find('*[title]').attr("title") + '"></i>';
        let html = `<li id = "cchoose__${slug}">${label}${info}<span class="unselect"><i class="far fa-trash-alt"></span></li>`;
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
            } else {
                // remove spinner if nothing is re-draw when we click save changes
                if ($(".op-page-loading-status > .loader").is(":visible")) {
                    $(".op-page-loading-status > .loader").hide();
                }
            }
        });

        $("#metadataSelector").on("show.bs.modal", function(e) {
            // save current column state so we can look for changes
            currentSelectedMetadata = opus.prefs.cols.slice();
        });

        $('#metadataSelector .allMetadata').on("click", '.submenu li a', function() {
            let slug = $(this).data('slug');
            if (!slug) { return; }

            let chosenSlugSelector = `#cchoose__${slug}`;
            let label = $(this).data('qualifiedlabel');

            //CHANGE THESE TO USE DATA-ICON=
            let def = $(this).find('i.fa-info-circle').attr("title");
            let selectedMetadata = $(this).find("i.fa-check");

            if ($(chosenSlugSelector).length === 0) {
                selectedMetadata.fadeIn();
                // this slug was previously unselected, add to cols
                $(`<li id = "${chosenSlugSelector.substr(1)}">${label}<span class="info">&nbsp;<i class = "fas fa-info-circle" title = "${def}"></i>&nbsp;&nbsp;&nbsp;</span><span class="unselect"><i class="far fa-trash-alt"></span></li>`).hide().appendTo(".selectedMetadata > ul").fadeIn();
                opus.prefs.cols.push(slug);
            } else {
                selectedMetadata.hide();
                // slug had been checked, remove from the chosen
                opus.prefs.cols.splice($.inArray(slug,opus.prefs.cols),1);
                $(chosenSlugSelector).remove();
            }
            return false;
        });


        // removes chosen column
        $("#metadataSelector .selectedMetadata").on("click", "li .unselect", function() {
            if (opus.prefs.cols.length <= 1) {
                return;     // prevent user from removing all the columns
            }
            let slug = $(this).parent().attr("id").split('__')[1];

            if ($.inArray(slug, opus.prefs.cols) >= 0) {
                // slug had been checked, removed from the chosen
                opus.prefs.cols.splice($.inArray(slug, opus.prefs.cols), 1);
                $(`#cchoose__${slug}`).fadeOut(200, function() {
                    $(this).remove();
                });
                $(`#metadataSelector .allMetadata [data-slug=${slug}]`).find("i.fa-check").hide();
            }
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
                    $(".op-page-loading-status > .loader").show();
                    break;
                case "cancel":
                    $('#myModal').modal('hide');
                    opus.prefs.cols = [];
                    o_browse.resetMetadata(currentSelectedMetadata, true);
                    break;
            }
        });
    },  // /addMetadataSelectorBehaviors

    // there are interactions that are applied to different code snippets,
    // this returns the namespace, view_var, prefix, and add_to_url
    // that distinguishes cart vs result tab views
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
        // you are in #cart or #browse views
        let namespace = "#browse";
        let prefix = "";
        let addToURL = "";
        if (opus.prefs.view == "cart") {
            namespace = "#cart";
            prefix = "cart_";
            addToURL = "&colls=true";
        }
        return {"namespace":namespace, "prefix":prefix, "add_to_url":addToURL};

    },

    getCurrentPage: function() {
        // sometimes other functions need to know current page for whatever view we
        // are currently looking at..
        let view_info = o_browse.getViewInfo();
        let prefix = view_info.prefix;       // either 'cart_' or ''
        let view_var = opus.prefs[prefix + "browse"];  // either "gallery" or "data"
        let page = 1;

        if (view_var == "data") {
            page = opus.prefs.page[prefix + "dataTable"];
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

            // $(".justify-content-center").show();

            o_browse.galleryScrollbar.settings.suppressScrollY = false;

            $(".gallery-contents > .ps__rail-y").removeClass("hide_ps__rail-y");
            if (!$(".dataTable > .ps__rail-y").hasClass("hide_ps__rail-y")) {
                $(".dataTable > .ps__rail-y").addClass("hide_ps__rail-y");
            }
        } else {
            $("." + "gallery", "#browse").hide();
            $("." + opus.prefs.browse, "#browse").fadeIn();

            $(".browse_view", "#browse").html("<i class='far fa-images'></i>&nbsp;View Gallery");
            $(".browse_view", "#browse").attr("title", "View sortable thumbnail gallery");
            $(".browse_view", "#browse").data("view", "gallery");

            // remove that extra space on top when loading table page
            // $(".justify-content-center").hide();

            o_browse.galleryScrollbar.settings.suppressScrollY = true;

            if (!$(".gallery-contents > .ps__rail-y").hasClass("hide_ps__rail-y")) {
                $(".gallery-contents > .ps__rail-y").addClass("hide_ps__rail-y");
            }
            $(".dataTable > .ps__rail-y").removeClass("hide_ps__rail-y");
        }
    },

    updatePageInUrl: function(url, page) {
        let urlPage = 0;
        // remove any existing page= slug before adding in the current page= slug w/new page number
        url = $.grep(url.split('&'), function(pair, index) {
            if (pair.startsWith("page")) {
                urlPage = pair.split("=")[1]; // XXX WARNING NOT USED BELOW
            }
            return !pair.startsWith("page");
        }).join('&');

        page = (page === undefined ? ++urlPage : page);
        url += `&page=${page}`;
        return url;
    },

    updateStartobsInUrl: function(url, startobs) {
        let urlStartobs = 0;
        // remove any existing page= slug or startobs= slug
        url = $.grep(url.split('&'), function(pair, index) {
            if (pair.startsWith("page") || pair.startsWith("startobs")) {
                urlPage = pair.split("=")[1];
            }
        }).join('&');

        startobs = (startobs === undefined ? ++urlStartobs : startobs);

        url += `&startobs=${startobs}`;
        $("#op-observation-slider").slider("value", startobs);
        $("#op-observation-number").html(startobs);
        return url;
    },

    renderMetadataSelector: function() {
        if (!o_browse.metadataSelectorDrawn) {
            let url = "/opus/__forms/metadata_selector.html?" + o_hash.getHash();
            $(".modal-body.metadata").load( url, function(response, status, xhr)  {

                o_browse.metadataSelectorDrawn = true;  // bc this gets saved not redrawn
                $("#metadataSelector .op-reset-button").hide(); // we are not using this

                // since we are rendering the left side of metadata selector w/the same code that builds the select menu, we need to unhighlight the selected widgets
                o_menu.markMenuItem(".modal-body.metadata li", "unselect");

                // we keep these all open in the metadata selector, they are all closed by default
                // disply check next to any default columns
                $.each(opus.prefs.cols, function(index, col) { //CHANGE BELOW TO USE DATA-ICON=
                    $(`.modal-body.metadata li > [data-slug="${col}"]`).find("i.fa-check").fadeIn().css('display', 'inline-block');
                });

                o_browse.addMetadataSelectorBehaviors();

                o_browse.allMetadataScrollbar = new PerfectScrollbar("#metadataSelectorContents .allMetadata", {
                    minScrollbarLength: opus.minimumPSLength
                });
                o_browse.selectedMetadataScrollbar = new PerfectScrollbar("#metadataSelectorContents .selectedMetadata", {
                    minScrollbarLength: opus.minimumPSLength
                });

                // dragging to reorder the chosen
                $( ".selectedMetadata > ul").sortable({
                    items: "li",
                    cursor: "grab",
                    stop: function(event, ui) { o_browse.metadataDragged(this); }
                });
            });
        }
    },

    renderGalleryAndTable: function(data, url, prev=false) {
        // render the gallery and table at the same time.
        // gallery is var html; table is row/tr/td.
        let namespace = o_browse.getViewInfo().namespace;

        // this is the list of all observations requested from dataimages.json
        let page = data.page;
        let html = "";

        if (data.count == 0) {
            // either there are no selections OR this is signaling the end of the infinite scroll
            // for now, just post same message to both #browse & #cart tabs
            if (data.page_no == 1) {
                if (opus.prefs.view == "browse") {
                    html += '<div class="thumbnail-message">';
                    html += '<h2>Your search produced no results</h2>';
                    html += '<p>Remove or edit one or more of the search criteria selected on the Search tab ';
                    html += 'or click on the Reset Search button to reset the search criteria to default.</p>';
                    html += '</div>';
                } else {
                    $("#cart .navbar").hide();
                    $("#cart .sort-order-container").hide();
                    html += '<div class="thumbnail-message">';
                    html += '<h2>Your cart is empty</h2>';
                    html += '<p>To add observations to the cart, click on the Browse Results tab ';
                    html += 'at the top of the page, mouse over the thumbnail gallery images to reveal the tools, ';
                    html += 'then click on the cart icon.  </p>';
                    html += '</div>';
                }
            } else {
                // we've hit the end of the infinite scroll.
                return;
            }
        } else {
            $("#cart .navbar").show();
            $("#cart .sort-order-container").show();
            html += '<div class="thumb-page" data-page="'+data.page_no+'">';
            opus.lastPageDrawn[opus.prefs.view] = data.page_no;
            if (o_browse.infiniteScrollCurrentMaxPageNumber < opus.lastPageDrawn[opus.prefs.view]) {
                o_browse.infiniteScrollCurrentMaxPageNumber = opus.lastPageDrawn[opus.prefs.view];
            }

            // add an indicator row that says this is the start of page/observation X - needs to be two hidden rows so as not to mess with the stripes
            if (!prev) {
                $(".dataTable tbody").append(`<tr class="table-page" data-page="${data.page_no}"><td colspan="${data.columns.length}"></td></tr>`);
            }
            // $(".dataTable tbody").append(`<tr class="table-page" data-page="${data.page_no}"><td colspan="${data.columns.length}"></td></tr><tr class="table-page"><td colspan="${data.columns.length}"></td></tr>`);

            $.each(page, function(index, item) {
                let opusId = item.opusid;
                // we have to store the relative observation number because we may not have pages in succession, this is for the slider position
                let observationNumber = ((data.page_no-1)*data.count)+index+1;  // needs to be 1-based, not 0-based...
                o_browse.galleryData[opusId] = item.metadata;	// for galleryView, store in global array

                // gallery
                let images = item.images;
                html += `<div class="thumbnail-container ${(item.in_cart ? ' in' : '')}" data-id="${opusId}" data-obs="${observationNumber}">`;
                html += `<a href="#" class="thumbnail" data-image="${images.full.url}">`;
                html += `<img class="img-thumbnail img-fluid" src="${images.thumb.url}" alt="${images.thumb.alt_text}" title="${observationNumber} - ${opusId}\r\nClick to enlarge">`;
                // whenever the user clicks an image to show the modal, we need to highlight the selected image w/an icon
                html += '<div class="modal-overlay">';
                html += '<p class="content-text"><i class="fas fa-binoculars fa-4x text-info" aria-hidden="true"></i></p>';
                html += '</div></a>';

                html += '<div class="thumb-overlay">';
                html += `<div class="op-tools dropdown" data-id="${opusId}">`;
                html +=     '<a href="#" data-icon="info" title="View observation detail"><i class="fas fa-info-circle fa-xs"></i></a>';

                let buttonInfo = o_browse.cartButtonInfo((item.in_cart ? 'add' : 'remove'));
                html +=     `<a href="#" data-icon="cart" title="Add to cart"><i class="${buttonInfo.icon} fa-xs"></i></a>`;
                html +=     '<a href="#" data-icon="menu"><i class="fas fa-bars fa-xs"></i></a>';
                html += '</div>';
                html += '</div></div>';

                // table row
                let checked = item.in_cart ? " checked" : "";
                let checkbox = `<input type="checkbox" name="${opusId}" value="${opusId}" class="multichoice"${checked}/>`;
                let minimenu = `<a href="#" data-icon="menu"><i class="fas fa-bars fa-xs"></i></a>`;
                let row = `<td><div class="op-tools mx-0" data-id="${opusId}">${checkbox} ${minimenu}</div></td>`;
                let tr = `<tr data-id="${opusId}" data-target="#galleryView" data-obs="${observationNumber}">`;
                $.each(item.metadata, function(index, cell) {
                    row += `<td>${cell}</td>`;
                });
                //$(".dataTable tbody").append("<tr data-toggle='modal' data-id='"+galleryData[0]+"' data-target='#galleryView'>"+row+"</tr>");
                if (prev) {
                    if (index === 0) {
                        $(".dataTable tbody").prepend(tr+row+"</tr>");
                    } else {
                        let prevIdx = index-1;
                        let selector = `.dataTable tbody tr:eq(${prevIdx})`;
                        let currentEl = tr+row+"</tr>";
                        $(currentEl).insertAfter($(selector));
                    }
                } else {
                    $(".dataTable tbody").append(tr+row+"</tr>");
                }
                // $(".dataTable tbody").append(tr+row+"</tr>");
            });

            if (prev) {
                $(".dataTable tbody").prepend(`<tr class="table-page" data-page="${data.page_no}"><td colspan="${data.columns.length}"></td></tr>`);
            }

            html += "</div>";
        }

        if (prev) {
            $(".gallery", namespace).prepend(html);
        } else {
            $(".gallery", namespace).append(html);
        }
        // $(".gallery", namespace).append(html);
        // $(".op-page-loading-status").hide();

        $(".op-page-loading-status > .loader").hide();
        o_browse.updateSliderHandle();
        o_hash.updateHash(true);
    },

    initTable: function(columns) {
        // prepare table and headers...
        $(".dataTable thead > tr > th").detach();
        $(".dataTable tbody > tr").detach();

        // NOTE:  At some point, ORDER needs to be identified in the table, as to which column we are ordering on

        // because i need the slugs for the columns
        let hashArray = o_hash.getHashArray();
        let slugs = hashArray.cols.split(",");
        let order = hashArray.order.split(",");

        opus.col_labels = columns;

        // check all box
        //let checkbox = "<input type='checkbox' name='all' value='all' class='multichoice'>";
        $(".dataTable thead tr").append("<th scope='col' class='sticky-header'></th>");
        $.each(columns, function(index, header) {
            let slug = slugs[index];
            // Assigning data attribute for table column sorting
            let icon = ($.inArray(slug, order) >= 0 ? "-down" : ($.inArray("-"+slug, order) >= 0 ? "-up" : ""));
            let columnSorting = icon === "-down" ? "sort-asc" : icon === "-up" ? "sort-desc" : "none";
            let columnOrdering = `<a href='' data-slug='${slug}'><span>${header}</span><span data-sort='${columnSorting}' class='column_ordering fas fa-sort${icon}'></span></a>`;

            $(".dataTable thead tr").append(`<th id='${slug} 'scope='col' class='sticky-header'><div>${columnOrdering}</div></th>`);
        });

        o_browse.initResizableColumn();
    },

    initResizableColumn: function() {
        $("#dataTable th div").resizable({
            handles: "e",
            minWidth: 40,
            resize: function(event, ui) {
                let resizableContainerWidth = $(event.target).parent().width();
                let columnTextWidth = $(event.target).find("a span:first").width();
                let sortLabelWidth = $(event.target).find("a span:last").width();
                let columnContentWidth = columnTextWidth + sortLabelWidth;
                let beginningSpace = (resizableContainerWidth - columnContentWidth)/2;
                let columnWidthUptoEndContent = columnContentWidth + beginningSpace;

                if (ui.size.width > columnWidthUptoEndContent) {
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
        opus.prefs.order = [];
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

    // set the scrollbar position in gallery / table view
    setScrollbarPosition: function(selector, page) {
        if (!$(`.table-page[data-page='${page}']`).prev().offset()) {
            $(`${selector}`).scrollTop(0);
            // make sure it's scrolled to the correct position in table view
            $(`${selector} .dataTable`).scrollTop(0);
        } else {
            let galleryTargetTopPosition = $(`#browse .gallery-contents .thumb-page[data-page='${page}'] .thumbnail-container:eq(0) a img`).offset().top;
            // console.log($(`#browse .gallery-contents .thumb-page[data-page='${newPage}'] .thumbnail-container:eq(0)`).data("id"))
            let galleryContainerTopPosition = $(".gallery-contents").offset().top;
            let galleryScrollbarPosition = $(".gallery-contents").scrollTop();

            let galleryTargetFinalPosition = galleryTargetTopPosition - galleryContainerTopPosition + galleryScrollbarPosition;
            $(`#browse .gallery-contents`).scrollTop(galleryTargetFinalPosition);
            // make sure it's scrolled to the correct position in table view
            let tableTargetTopPosition = $(`.table-page[data-page='${page}']`).prev().offset().top;
            let tableContainerTopPosition = $(".dataTable").offset().top;
            let tableScrollbarPosition = $(".dataTable").scrollTop();
            let tableTargetFinalPosition = tableTargetTopPosition - tableContainerTopPosition + tableScrollbarPosition;
            $(`${selector} .dataTable`).scrollTop(tableTargetFinalPosition);
        }
    },

    getDataURL: function(page) {
        let view = o_browse.getViewInfo();
        let base_url = "/opus/__api/dataimages.json?";
        if (page == undefined) {
            page = opus.lastPageDrawn[opus.prefs.view]+1;
        }
        // this is a workaround for firefox
        let hashString = (o_hash.getHash() ? o_hash.getHash() : o_browse.tempHash);

        o_browse.lastLoadDataRequestNo++;
        let url = hashString + '&reqno=' + o_browse.lastLoadDataRequestNo + view.add_to_url;
        let startobs = page * opus.prefs.limit; // XXX WARNING NOT USED BELOW
        url = base_url + o_browse.updatePageInUrl(url, page);

        return url;
    },

    loadData: function(page) {
        page = (page === undefined ? opus.prefs.page[opus.prefs.browse] : page);

        // if the request is a block far away from current page cache, flush the cache and start over
        var pagesDrawn = [];
        let namespace = o_browse.getViewInfo().namespace;
        $(`${namespace} [data-page]`).each(function(index, elem) {
            pagesDrawn.push($(elem).data("page"));
        });
        if (page > opus.lastPageDrawn[opus.prefs.view] + 1 ||
            (page < opus.lastPageDrawn[opus.prefs.view] && !$.inArray(page, pagesDrawn))) {
            o_browse.galleryBegun = false;
        }

        let selector = `#${opus.prefs.view} .gallery-contents`;

        // wait! is this page already drawn?
        if ($(`${selector} .thumb-page[data-page='${page}']`).length > 0 && !o_browse.tableSorting) {
            o_browse.setScrollbarPosition(selector, page);
            $(".op-page-loading-status > .loader").hide();
            return;
        } else {
            // reset counter
            o_browse.infiniteScrollCurrentMinPageNumber = parseInt(page) - 1;
            o_browse.infiniteScrollCurrentMaxPageNumber = parseInt(page) + 1;
        }

        let url = o_browse.getDataURL(page);

        // metadata; used for both table and gallery
        $.getJSON(url, function(data) {
            if (data.reqno < o_browse.lastLoadDataRequestNo) {
                // make sure to remove spinner before return
                if ($(".op-page-loading-status > .loader").is(":visible")) {
                    $(".op-page-loading-status > .loader").hide();
                }
                return;
            }
            // data.start_obs, data.count
            opus.lastPageDrawn[opus.prefs.view] = data.page_no;
            if (o_browse.infiniteScrollCurrentMaxPageNumber < opus.lastPageDrawn[opus.prefs.view]) {
                o_browse.infiniteScrollCurrentMaxPageNumber = opus.lastPageDrawn[opus.prefs.view];
            }

            if (!o_browse.galleryBegun) {
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

                    $(selector).on("request.infiniteScroll", function(event, path) {
                        // hide default page status loader if op-page-loading-status loader is spinning
                        // && o_browse.tableSorting
                        if ($(".op-page-loading-status > .loader").is(":visible")) {
                            $(".infinite-scroll-request").hide();
                        }
                    });
                    $(selector).on("scrollThreshold.infiniteScroll", function(event) {
                        if (opus.lastPageDrawn[opus.prefs.view] < o_browse.infiniteScrollCurrentMaxPageNumber) {
                            opus.lastPageDrawn[opus.prefs.view] = o_browse.infiniteScrollCurrentMaxPageNumber;
                        }

                        // remove spinner when scrollThreshold is triggered and last data fetching has no data
                        // Need to revisit this one
                        // console.log(`page about to be drawn: ${opus.lastPageDrawn[opus.prefs.view] + 1}`);
                        if (o_browse.dataNotAvailable) {
                            $(".infinite-scroll-request").hide();
                        }
                        $(selector).infiniteScroll("loadNextPage");


                    });
                    $(selector).on("load.infiniteScroll", o_browse.infiniteScrollLoadEventListener);
                }
            }

            // Because we redraw from the beginning or user inputted page, we need to remove previous drawn thumb-pages
            $(".gallery > .thumb-page").detach();
            o_browse.renderGalleryAndTable(data, this.url);
            if (o_browse.currentOpusId != "") {
                o_browse.metadataboxHtml(o_browse.currentOpusId);
            }
            o_browse.updateSortOrder(data);

            // prefill next page
            if (!o_browse.galleryBegun) {
                $(selector).infiniteScroll('loadNextPage');
                o_browse.updateSliderHandle();
                o_browse.galleryBegun = true;
            }
            // if ($(".op-page-loading-status > .loader").is(":visible")) {
            //     $(".op-page-loading-status > .loader").hide();
            // }
            o_browse.tableSorting = false;
        });
    },

    infiniteScrollLoadEventListener: function(event, response, path) {
        let data = JSON.parse( response );
        // this variable is used let us know there is no data to load
        // we will use it as the flag to hide the spinner triggered by scrollThreshold
        o_browse.dataNotAvailable = (data.page_no > opus.pages);

        if ($(`.thumb-page[data-page='${data.page_no}']`).length !== 0 || data.page_no > opus.pages) {
            console.log(`data.reqno: ${data.reqno}, last reqno: ${o_browse.lastLoadDataRequestNo}`);
            if ($(".op-page-loading-status > .loader").is(":visible")) {
                $(".op-page-loading-status > .loader").hide();
            }
            return;
        }

        if (o_browse.infiniteScrollCurrentMaxPageNumber > data.page_no) {
            // prepend data from new page
            o_browse.renderGalleryAndTable(data, path, true);

            // Update to make prev button appear when prefetching previous page is done
            if (!$("#galleryViewContents .prev").data("id") && $("#galleryViewContents .prev").hasClass("op-button-disabled")) {
                let prev = $(`#browse tr[data-id=${o_browse.currentOpusId}]`).prev("tr");
                while (prev.hasClass("table-page")) {
                    prev = prev.prev("tr");
                }
                prev = (prev.data("id") ? prev.data("id") : "");

                $("#galleryViewContents .prev").data("id", prev);
                $("#galleryViewContents .prev").removeClass("op-button-disabled");
            }

            o_browse.loadPrevPage = true;
        } else {
            // append data from new page
            o_browse.renderGalleryAndTable(data, path);

            // Update to make next button appear when prefetching next page is done
            if (!$("#galleryViewContents .next").data("id") && $("#galleryViewContents .next").hasClass("op-button-disabled")) {
                let next = $(`#browse tr[data-id=${o_browse.currentOpusId}]`).next("tr");
                while (next.hasClass("table-page")) {
                    next = next.next("tr");
                }
                next = (next.data("id") ? next.data("id") : "");

                $("#galleryViewContents .prev").data("id", next);
                $("#galleryViewContents .prev").removeClass("op-button-disabled");
            }
        }

        // update the scroll position in the 'other' bit
        if (opus.prefs.browse == "dataTable") {
            $(`.thumb-page[data-page='${data.page_no}']`).scrollTop(0);
        }
        //console.log('Loaded page: ' + $('#browse .gallery-contents').data('infiniteScroll').pageIndex );

        if (o_browse.loadPrevPage) {
            o_browse.infiniteScrollCurrentMinPageNumber -= 1;
            o_browse.loadPrevPage = false;
        }

        // if left/right arrow are disabled, make them clickable again
        $("#galleryViewContents").removeClass("op-disabled");
    },

    getBrowseTab: function() {
        // only draw the navbar if we are in gallery mode... doesn't make sense in cart mode
        let hide = opus.prefs.browse == "gallery" ? "dataTable" : "gallery";
        $(`${hide}#browse`).hide();

        // reset range select
        o_browse.undoRangeSelect();

        $(`.${opus.prefs.browse}#browse`).fadeIn();
        $(".op-page-loading-status > .loader").show();
        o_browse.updateBrowseNav();
        o_browse.renderMetadataSelector();   // just do this in background so there's no delay when we want it...

        // figure out the page
        let page = opus.prefs.page[opus.prefs.browse]; // default: {"gallery":1, "dataTable":1, 'cart_gallery':1, 'cart_data':1 };

        // some outlier things that can go wrong with page (when user entered page #)
        page = (!page || page < 1) ? 1 : page;

        if (opus.pages && page > opus.pages) {
            // page is higher than the total number of pages, reset it to the last page
            page = opus.pages;
        }

        o_browse.loadData(page);
    },

    countGalleryImages: function() {
        let xDir = 0;
        let xCount = 0;
        // we need to know how many images fit across; we can approx the y dir differently
        $(".thumbnail-container").each(function(index, thumb) {
            let offset = $(thumb).offset();
            if (offset.left >= xDir) {
                xDir = offset.left;
                ++xCount;
            } else {
                // done; no need to continue
                return false;
            }
        });
        let yCount = Math.round($(".gallery-contents").height()/100);   // images are 100px
        return {"x": xCount, "y": yCount};
    },

    adjustBrowseHeight: function() {
        let container_height = $(window).height()-120;
        $(".gallery-contents").height(container_height);
        o_browse.galleryScrollbar.update();
        o_browse.galleryBoundingRect = o_browse.countGalleryImages();
        $("#op-observation-slider").slider("option", "step", o_browse.galleryBoundingRect.x);
        //opus.limit =  (floor($(window).width()/thumbnailSize) * floor(container_height/thumbnailSize));
    },

    adjustTableSize: function() {
        let containerWidth = $(".gallery-contents").width();
        let containerHeight = $(".gallery-contents").height() - $(".app-footer").height() + 8;
        $(".dataTable").width(containerWidth);
        $(".dataTable").height(containerHeight);
        o_browse.tableScrollbar.update();
    },

    adjustMetadataSelectorMenuPS: function() {
        let containerHeight = $(".allMetadata").height();
        let menuHeight = $(".allMetadata .searchMenu").height();

        if (containerHeight > menuHeight) {
            if (!$(".allMetadata .ps__rail-y").hasClass("hide_ps__rail-y")) {
                $(".allMetadata .ps__rail-y").addClass("hide_ps__rail-y");
                o_browse.allMetadataScrollbar.settings.suppressScrollY = true;
            }
        } else {
            $(".allMetadata .ps__rail-y").removeClass("hide_ps__rail-y");
            o_browse.allMetadataScrollbar.settings.suppressScrollY = false;
        }
        o_browse.allMetadataScrollbar.update();
    },

    adjustSelectedMetadataPS: function() {
        let containerHeight = $(".selectedMetadata").height();
        let selectedMetadataHeight = $(".selectedMetadata .ui-sortable").height();

        if (containerHeight > selectedMetadataHeight) {
            if (!$(".selectedMetadata .ps__rail-y").hasClass("hide_ps__rail-y")) {
                $(".selectedMetadata .ps__rail-y").addClass("hide_ps__rail-y");
                o_browse.selectedMetadataScrollbar.settings.suppressScrollY = true;
            }
        } else {
            $(".selectedMetadata .ps__rail-y").removeClass("hide_ps__rail-y");
            o_browse.selectedMetadataScrollbar.settings.suppressScrollY = false;
        }
        o_browse.selectedMetadataScrollbar.update();
    },

    adjustBrowseDialogPS: function() {
        let containerHeight = $("#galleryViewContents .metadata").height();
        let browseDialogHeight = $(".metadata .contents").height();

        if (containerHeight > browseDialogHeight) {
            if (!$("#galleryViewContents .metadata .ps__rail-y").hasClass("hide_ps__rail-y")) {
                $("#galleryViewContents .metadata .ps__rail-y").addClass("hide_ps__rail-y");
                o_browse.modalScrollbar.settings.suppressScrollY = true;
            }
        } else {
            $("#galleryViewContents .metadata .ps__rail-y").removeClass("hide_ps__rail-y");
            o_browse.modalScrollbar.settings.suppressScrollY = false;
        }
        o_browse.modalScrollbar.update();
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

    updateCartIcon: function(opusId, action) {
        let buttonInfo = o_browse.cartButtonInfo(action);
        let selector = `.thumb-overlay [data-id=${opusId}] [data-icon="cart"]`;
        $(selector).html(`<i class="${buttonInfo.icon} fa-xs"></i>`);
        $(selector).prop("title", buttonInfo.title);

        let modalCartSelector = `#galleryViewContents .bottom .select[data-id=${opusId}]`;
        if ($("#galleryView").is(":visible") && $(modalCartSelector).length > 0) {
            $(modalCartSelector).html(`<i class="${buttonInfo.icon} fa-2x"></i>`);
            $(modalCartSelector).prop("title", buttonInfo.title);
        }
    },

    getNextPrevHandles: function(opusId) {
        let namespace = `#${opus.prefs.view}`;
        let idArray = $(`${namespace} .thumbnail-container[data-id]`).map(function() {
            return $(this).data("id");
        });
        let next = $.inArray(opusId, idArray) + 1;
        next = (next < idArray.length ? idArray[next] : "");

        let prev = $.inArray(opusId, idArray) - 1;
        prev = (prev < 0 ? "" : idArray[prev]);

        return {"next": next, "prev": prev};
    },

    metadataboxHtml: function(opusId) {
        o_browse.currentOpusId = opusId;

        // list columns + values
        let html = "<dl>";
        $.each(opus.col_labels, function(index, columnLabel) {
            let value = o_browse.galleryData[opusId][index];
            html += `<dt>${columnLabel}:</dt><dd>${value}</dd>`;
        });
        html += "</dl>";
        $("#galleryViewContents .contents").html(html);

        let nextPrevHandles = o_browse.getNextPrevHandles(opusId);
        let status = o_cart.isIn(opusId) ? "" : "in";
        let buttonInfo = o_browse.cartButtonInfo(status);

        // prev/next buttons - put this in galleryView html...
        html = `<div class="col"><a href="#" class="select" data-id="${opusId}" title="${buttonInfo.title}"><i class="${buttonInfo.icon} fa-2x float-left"></i></a></div>`;
        html += `<div class="col text-center">`;
        let opPrevDisabled = (nextPrevHandles.prev == "" ? "op-button-disabled" : "");
        let opNextDisabled = (nextPrevHandles.next == "" ? "op-button-disabled" : "");
        html += `<a href="#" class="prev text-center ${opPrevDisabled}" data-id="${nextPrevHandles.prev}" title="Previous image"><i class="far fa-hand-point-left fa-2x"></i></a>`;
        html += `<a href="#" class="next ${opNextDisabled}" data-id="${nextPrevHandles.next}" title="Next image"><i class="far fa-hand-point-right fa-2x"></i></a>`;
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
    },


    resetData: function() {
        $("#dataTable > tbody").empty();  // yes all namespaces
        $(".gallery").empty();
        o_browse.galleryData = [];
        opus.lastPageDrawn = {"browse":0, "cart":0};
        opus.cart_change = true;  // forces redraw of cart tab because reset_lastPageDrawn
        o_browse.galleryBegun = false;
        o_hash.updateHash();
    },

    resetQuery: function() {
        /*
        when the user changes the query and all this stuff is already drawn
        need to reset all of it (todo: replace with framework!)
        */
        o_browse.metadataSelectorDrawn = false;
        o_browse.resetData();
    },
};
