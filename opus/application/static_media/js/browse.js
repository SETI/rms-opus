/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* globals $, PerfectScrollbar */
/* globals o_cart, o_hash, o_menu, o_utils, opus */

// font awesome icon class
const pillSortUpArrow = "fas fa-arrow-circle-up";
const pillSortDownArrow = "fas fa-arrow-circle-down";
const tableSortUpArrow = "fas fa-sort-up";
const tableSortDownArrow = "fas fa-sort-down";
const defaultTableSortArrow = "fas fa-sort";
const infiniteScrollUpThreshold = 100;

/* jshint varstmt: false */
var o_browse = {
/* jshint varstmt: true */
    // tableScrollbar and galleryScrollbar are common vars w/cart.js
    tableScrollbar: new PerfectScrollbar("#browse .op-data-table-view", {
        minScrollbarLength: opus.galleryAndTablePSLength,
        maxScrollbarLength: opus.galleryAndTablePSLength,
    }),
    galleryScrollbar: new PerfectScrollbar("#browse .op-gallery-view", {
        suppressScrollX: true,
        minScrollbarLength: opus.galleryAndTablePSLength,
        maxScrollbarLength: opus.galleryAndTablePSLength,
    }),
    // only in o_browse
    modalScrollbar: new PerfectScrollbar("#galleryViewContents .op-metadata-details", {
        minScrollbarLength: opus.minimumPSLength
    }),

    // these vars are common w/o_cart
    reloadObservationData: true, // start over by reloading all data
    observationData: {},  // holds observation column data
    totalObsCount: undefined,
    cachedObservationFactor: 4,     // this is the factor times the screen size to determine cache size
    maxCachedObservations: 1000,    // max number of observations to store in cache, will be updated based on screen size
    galleryBoundingRect: {'x': 0, 'y': 0, 'tr': 0},
    gallerySliderStep: 10,

    // The viewable fraction of an item's height such that it will be treated as present on the screen
    galleryImageViewableFraction: 0.8,

    // unique to o_browse
    imageSize: 100,     // default

    metadataDetailOpusId: "",
    selectMetadataDrawn: false,

    tempHash: "",
    onRenderData: false,
    fading: false,  // used to prevent additional clicks until the fade animation complete

    pageLoaderSpinnerTimer: null,   // used to apply a small delay to the loader spinner
    loadDataInProgress: false,
    infiniteScrollLoadInProgress: false,
    /**
    *
    *  all the things that happen on the browse tab
    *
    **/
    addBrowseBehaviors: function() {
        // note: using .on vs .click allows elements to be added dynamically w/out bind/rebind of handler

        $(".op-gallery-view, .op-data-table-view").on("scroll", o_browse.checkScroll);

        // Mouse wheel up will also trigger ps-scroll-up.
        // NOTE: We put both wheel and ps-scroll-up here for a corner case like this:
        // 1. Scroll slider to the very end (scrollbar will be at the bottom and is fairly long)
        // 2. When moving scrollbar around scroll threshold point at the bottom end, it will keep triggering
        //    infiniteScroll request and load with 0 returned data (We haven't found a proper way to avoid this yet, so for now we leave it like that).
        // 3. In above step, at the time when infiniteScroll request (we call it request A here) is triggered but before the load, if we move the scrollbar
        //    all the way up to the top in a very fast manner, the loadPrevPage will be triggered with url in request A. This means we will have 0 returned
        //    data prepended. So we do the followings to fix this issue:
        // - Prefetch more data ahead of startObs if the current (middle) page has reached to the bottom end of the data.
        // - Lower the scroll threshold point in infiniteScroll.
        // - Adding wheel event: because wheel event can (ps-scroll-up can't) trigger another loadNextPage with correct url if we reach to the top end
        //   in that corner case.
        $(".op-gallery-view, .op-data-table-view").on("wheel ps-scroll-up", function(event) {
            let startObsLabel = o_browse.getStartObsLabel();
            let view = opus.prefs.view;
            let tab = opus.getViewTab();
            let contentsView = o_browse.getScrollContainerClass();

            if (event.type === "ps-scroll-up" || (event.type === "wheel" && event.originalEvent.deltaY < 0)) {
                if (opus.prefs[startObsLabel] > 1) {
                    let firstObs = $(`${tab} [data-obs]`).first().data("obs");
                    if (firstObs !== undefined && firstObs !== 1 && $(`${tab} ${contentsView}`).scrollTop() < infiniteScrollUpThreshold) {
                        $(`${tab} ${contentsView}`).infiniteScroll({
                            "loadPrevPage": true,
                        });
                        $(`${tab} ${contentsView}`).infiniteScroll("loadNextPage");
                        o_browse.updateSliderHandle(view);
                    }
                }
            }
            o_browse.hideMenu();
        });

        $("#op-select-metadata").modal({
            keyboard: false,
            backdrop: 'static',
            show: false,
        });

        // browse nav menu - the gallery/table toggle
        $("#browse, #cart").on("click", ".op-browse-view", function() {
            if (o_browse.fading) {
                return false;
            }

            o_browse.hideMenu();
            let browse = o_browse.getBrowseView();
            opus.prefs[browse] = $(this).data("view");
            if (!o_browse.isGalleryView()) {
                // update this when we switch to table view
                o_browse.countTableRows();
            }

            o_hash.updateHash();
            o_browse.updateBrowseNav();
            // reset scroll position
            window.scrollTo(0, 0); // restore previous scroll position

            // Do the fake API call to write in the Apache log files that
            // we changed views so log_analyzer has something to go on
            let hashString = o_hash.getHash();
            let fakeUrl = `/opus/__fake/__api/dataimages.json?${hashString}`;
            $.getJSON(fakeUrl, function(data) {
            });

            return false;
        });

        // browse nav menu - download csv
        $("#browse").on("click", ".op-download-csv", function() {
            let colStr = opus.prefs.cols.join(',');
            let selectionsHash = [];
            for (let param in opus.selections) {
                if (opus.selections[param].length) {
                    let valueStr = opus.selections[param].join(',').replace(/ /g,'+');
                    selectionsHash.push(`${param}=${valueStr}`);
                }
            }
            let selectionsHashStr = selectionsHash.join('&');
            if (selectionsHashStr !== "") {
                selectionsHashStr += "&";
            }
            let resultCountStr = o_browse.totalObsCount.toString();
            let orderStr = opus.prefs.order.join(",");
            let csvLink = `/opus/__api/data.csv?${selectionsHashStr}cols=${colStr}&limit=${resultCountStr}&order=${orderStr}`;
            $(this).attr("href", csvLink);
        });

        // 1 - click on thumbnail opens modal window
        // 2-  Shift+click or menu/"Start Add[Remove] Range Here" starts a range
        //          Shfit+click on menu/"End Add[Remove] Range Here" ends a range
        //          Clicking on a cart/trash can anywhere aborts the range selection
        // 3 - ctrl click - alternate way to add to cart
        // NOTE: range can go forward or backwards

        // images...
        $(".gallery").on("click", ".thumbnail, .op-recycle-overlay", function(e) {
            // make sure selected modal thumb is unhighlighted, as clicking on this closes the modal
            // but is not caught in time before hidden.bs to get correct opusId
            e.preventDefault();
            o_browse.hideMenu();

            let opusId = $(this).parent().data("id");

            // Detecting ctrl (windows) / meta (mac) key.
            if (e.ctrlKey || e.metaKey) {
                o_cart.toggleInCart(opusId);
                o_browse.undoRangeSelect();
            }
            // Detecting shift key
            else if (e.shiftKey) {
                o_browse.cartShiftKeyHandler(e, opusId);
            } else {
                o_browse.showMetadataDetailModal(opusId);
            }
        });

        // data_table - clicking a table row adds to cart
        $(".op-data-table").on("click", ":checkbox", function(e) {
            if ($(this).val() == "all") {
                // checkbox not currently implemented
                // pop up a warning if selection total is > 100 items,
                // with the total number to be selected...
                // if OK, use 'addall' api and loop tru all checkboxes to set them as selected
                //o_cart.editCart("all",action);
                return false;
            }
            let tab = opus.getViewTab();
            let opusId = $(this).val();

            if (e.shiftKey) {
                let fromOpusId = $(`${tab} .op-gallery-view`).data("infiniteScroll").options.rangeSelectOpusID;
                if (fromOpusId === undefined) {
                    o_browse.startRangeSelect(opusId);
                } else {
                    o_cart.toggleInCart(fromOpusId, opusId);
                }
            } else {
                o_cart.toggleInCart(opusId);
                // single click stops range selection; shift click starts range
                o_browse.undoRangeSelect();
            }
        });

        $(".op-data-table").on("click", "td:not(:first-child)", function(e) {
            let opusId = $(this).parent().data("id");
            e.preventDefault();
            o_browse.hideMenu();

            // Detecting ctrl (windows) / meta (mac) key.
            if (e.ctrlKey || e.metaKey) {
                o_cart.toggleInCart(opusId);
                o_browse.undoRangeSelect();
            }
            // Detecting shift key
            else if (e.shiftKey) {
                o_browse.cartShiftKeyHandler(e, opusId);
            } else {
                o_browse.showMetadataDetailModal(opusId);
            }
        });

        // this event handler is here because the gallery may not yet be updated after a change to the
        // metadata selection, so refresh the URL attached to the .thumbnail image.  This allows the
        // user to right click and open in new tab w/out stale metadata.  Happens only on the gallery view.
        $(".gallery").on("contextmenu", ".op-thumbnail-container", function(e) {
            let opusId = $(this).data("id");
            let obj = $(this).children("a").eq(0);
            let url = o_browse.getDetailURL(opusId);
            if (obj.length) {
                obj.attr("href", url);
            }
        });

        // thumbnail overlay tools
        $(".gallery, .op-data-table").on("click contextmenu", ".op-tools a", function(e) {
            let retValue = false;   // do not use the default handler
            //snipe the id off of the image..
            let opusId = $(this).parent().data("id");
            let iconAction = $(this).data("icon");
            if (e.which === 3) {    // right mouse click
                // on any right click w/in the op-tools, display context menu and allow 'open in new tab'
                // and as a side effect, the tool in focus has no effect, as the new tab will always be 'detail view'
                iconAction = "info";
                retValue = undefined; // need to use the default handler to allow the context menu to work
            }

            switch (iconAction) {
                case "info":  // detail page
                    o_browse.hideMenu();
                    o_browse.showDetail(e, opusId);
                    break;

                case "cart":   // add to cart
                    o_browse.hideMenu();

                    if (e.shiftKey) {
                        o_browse.cartShiftKeyHandler(e, opusId);
                    } else {
                        // clicking on the cart/trash can aborts range select
                        o_browse.undoRangeSelect();

                        let action = o_cart.toggleInCart(opusId);
                        o_browse.updateCartIcon(opusId, action);
                    }
                    break;

                case "menu":  // expand, same as click on image
                    o_browse.showMenu(e, opusId);
                    break;
            }
            return retValue;
        }); // end click a browse tools icon

        // do we need an on.resize for when the user makes the screen tiny?

        $(".modal-dialog").draggable({
            handle: ".modal-content",
            cancel: ".contents",
            drag: function(event, ui) {
                o_browse.hideMenu();
            }
        });

        // Disable draggable for these infomation modals
        $.each($(".op-confirm-modal"), function(idx, dialog) {
            if ($(dialog).data("draggable") === "False") {
                let id = $(dialog).attr("id");
                $(`#${id} .modal-dialog`).draggable("disable");
            }
        });

        $(".app-body").on("hide.bs.modal", "#galleryView", function(e) {
            let namespace = o_browse.getViewInfo().namespace;
            $(namespace).find(".op-modal-show").removeClass("op-modal-show");
        });

        $('#galleryView').on("click", "a.op-cart-toggle", function(e) {
            let opusId = $(this).data("id");
            if (opusId) {
                // clicking on the cart/trash can aborts range select
                o_browse.undoRangeSelect();
                o_cart.toggleInCart(opusId);
            }
            return false;
        });

        $('#galleryView').on("click", "a.op-prev,a.op-next", function(e) {
            let action = $(this).hasClass("op-prev") ? "prev" : "next";
            let opusId = $(this).data("id");

            if (opusId) {
                o_browse.loadPageIfNeeded(action, opusId);
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
        $("#browse, #cart").on("click", ".op-data-table-view th a",  function() {
            // show this spinner right away when table is clicked
            // we will hide page status loader from infiniteScroll if op-page-loading-status loader is spinning
            o_browse.showPageLoaderSpinner();
            let orderBy =  $(this).data("slug");
            let targetSlug = orderBy;

            // get order of opusid when table header is clicked
            let hash = o_hash.getHashArray();
            let opusidOrder = (hash.order && hash.order.match(/(-?opusid)/)) ? hash.order.match(/(-?opusid)/)[0] : "opusid";
            let isDescending = true;
            let orderIndicator = $(this).find("span:last");
            let pillOrderIndicator = $(`.sort-contents span[data-slug="${orderBy}"] .flip-sort`);

            if (orderIndicator.data("sort") === "sort-asc") {
                // currently ascending, change to descending order
                orderBy = '-' + orderBy;
            } else if (orderIndicator.data("sort") === "sort-desc") {
                // currently descending, change to ascending order
                isDescending = false;
                orderBy = orderBy;
            } else {
                // not currently ordered, change to ascending
                isDescending = false;
            }

            // make sure opusid is always in order slug values
            opus.prefs.order = orderBy.match(/opusid/) ? [orderBy] : [orderBy, opusidOrder];
            o_browse.updateOrderIndicator(orderIndicator, pillOrderIndicator, isDescending, targetSlug);

            o_hash.updateHash();
            o_browse.renderSortedDataFromBeginning();

            return false;
        });

        // browse sort order - remove sort slug
        $(".sort-contents").on("click", "li .remove-sort", function() {
            o_browse.showPageLoaderSpinner();
            let slug = $(this).parent().attr("data-slug");
            let descending = $(this).parent().attr("data-descending");

            if (descending == "true") {
                slug = "-"+slug;
            }
            let slugIndex = $.inArray(slug, opus.prefs.order);
            // The clicked-on slug should always be in the order list;
            // The "if" is a safety precaution and the condition should always be true
            if (slugIndex >= 0) {
                opus.prefs.order.splice(slugIndex, 1);
            }

            // remove the sort pill right away
            // NOTE: we will find a better way to do this using data-xxx in the future.
            $(this).closest(".list-inline-item").remove();

            o_hash.updateHash();
            // o_browse.updatePage();
            o_browse.renderSortedDataFromBeginning();
        });

        // browse sort order - flip sort order of a slug
        $(".sort-contents").on("click", "li .flip-sort", function() {
            o_browse.showPageLoaderSpinner();
            let slug = $(this).parent().attr("data-slug");
            let targetSlug = slug;
            let isDescending = true;
            let descending = $(this).parent().attr("data-descending");
            let headerOrderIndicator = $(`.op-data-table-view th a[data-slug="${slug}"]`).find("span:last");
            let pillOrderIndicator = $(this);

            let new_slug = slug;
            if (descending == "true") {
                slug = "-"+slug; // Old descending, new ascending
                isDescending = false;
            } else {
                new_slug = "-"+slug; // Old ascending, new descending
                isDescending = true;
            }
            let slugIndex = $.inArray(slug, opus.prefs.order);
            // The clicked-on slug should always be in the order list;
            // The "if" is a safety precaution and the condition should always be true
            if (slugIndex >= 0) {
                opus.prefs.order[slugIndex] = new_slug;
            }

            // When clicking on opusid sorting pill AND there is another sort order other an opusid, we don't update the table header arrows
            // Only one arrow will displayed either up or down at a time, rest of arrows will be up + down in table header
            if (targetSlug === "opusid" && opus.prefs.order.length > 1) {
                o_browse.updateOrderIndicator(null, pillOrderIndicator, isDescending, targetSlug);
            } else {
                o_browse.updateOrderIndicator(headerOrderIndicator, pillOrderIndicator, isDescending, targetSlug);
            }

            // order in the url will get updated right away
            o_hash.updateHash();

            // o_browse.updatePage();
            o_browse.renderSortedDataFromBeginning();
        });

        $("#op-obs-menu").on("click", '.dropdown-header',  function(e) {
            o_browse.hideMenu();
            return false;
        });

        $("#op-obs-menu").on("click", '.dropdown-item',  function(e) {
            let retValue = false;
            let opusId = $(this).parent().attr("data-id");
            o_browse.hideMenu();

            switch ($(this).data("action")) {
                case "cart":  // add/remove from cart
                    o_cart.toggleInCart(opusId);
                    // clicking on the cart/trash can aborts range select
                    o_browse.undoRangeSelect();
                    break;

                case "range": // begin/end range
                    let tab = opus.getViewTab();
                    let fromOpusId = $(`${tab} .op-gallery-view`).data("infiniteScroll").options.rangeSelectOpusID;
                    if (fromOpusId === undefined) {
                        o_browse.startRangeSelect(opusId);
                    } else {
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
                    break;

                case "help":
                    break;
            }
            return retValue;
        });

        $(".op-observation-slider").slider({
            animate: true,
            value: 1,
            min: 1,
            max: 1000,
            step: o_browse.gallerySliderStep,
            slide: function(event, ui) {
                let tab = ui.handle.dataset.target;
                o_browse.onSliderHandleMoving(tab, ui.value);
                o_browse.hideMenu();
            },
            stop: function(event, ui) {
                let tab = ui.handle.dataset.target;
                o_browse.onSliderHandleStop(tab, ui.value);
            }
        });

        $(document).on("keydown click", function(e) {
            // don't close the mini-menu on the ctrl key in case the user
            // is trying to open a new window for detail
           if (!(e.ctrlKey || e.metaKey)) {
                o_browse.hideMenu();
            }

            if ((e.which || e.keyCode) == 27) { // esc - close modals
                o_browse.hideGalleryViewModal();
                $("#op-select-metadata").modal('hide');
                // reset range select
                o_browse.undoRangeSelect();
            }
            if ($("#galleryView").hasClass("show")) {
                /*  Catch the right/left arrow and spacebar while in the modal
                    Up: 38
                    Down: 40
                    Right: 39
                    Left: 37
                    Space: 32 */

                let detailOpusId;
                // the || is for cross-browser support; firefox does not support keyCode
                switch (e.which || e.keyCode) {
                    case 32:  // spacebar
                        if (o_browse.metadataDetailOpusId !== "") {
                            o_browse.undoRangeSelect();
                            o_cart.toggleInCart(o_browse.metadataDetailOpusId);
                        }
                        break;
                    case 39:  // next
                        detailOpusId = $("#galleryView").find(".op-next").data("id");
                        o_browse.loadPageIfNeeded("next", detailOpusId);
                        break;
                    case 37:  // prev
                        detailOpusId = $("#galleryView").find(".op-prev").data("id");
                        o_browse.loadPageIfNeeded("prev", detailOpusId);
                        break;
                }
                if (detailOpusId && !$("#galleryViewContents").hasClass("op-disabled")) {
                    o_browse.updateGalleryView(detailOpusId);
                }
            }
            // don't return false here or it will snatch all the user input!
        });
    }, // end browse behaviors

    cartShiftKeyHandler: function(e, opusId) {
        let tab = opus.getViewTab();
        let fromOpusId = $(`${tab} .op-gallery-view`).data("infiniteScroll").options.rangeSelectOpusID;
        if (fromOpusId === undefined) {
            o_browse.startRangeSelect(opusId);
        } else {
            o_cart.toggleInCart(fromOpusId, opusId);
        }
    },

    // update order arrows right away when user clicks on sorting arrows in pill or table header
    // sync up arrows in both sorting pill and table header
    updateOrderIndicator: function(headerOrderIndicator, pillOrderIndicator, isDescending, slug) {
        let headerOrder = isDescending ? "sort-desc" : "sort-asc";
        let headerOrderArrow = isDescending ? tableSortUpArrow : tableSortDownArrow;
        let pillOrderTooltip = isDescending ? "Change to ascending sort" : "Change to descending sort";

        // If header already exists, we update the header arrow, else we do nothing
        if (headerOrderIndicator && headerOrderIndicator.length !== 0) {
            headerOrderIndicator.data("sort", `${headerOrder}`);
            headerOrderIndicator.attr("class", `column_ordering ${headerOrderArrow}`);

            // Reset arrows on rest of table headers
            // let headers = $(`.op-data-table-view th a:not([data-slug="opusid"], [data-slug=${slug}])`).find("span:last");
            let headers = $(`.op-data-table-view th a:not([data-slug=${slug}])`).find("span:last");
            headers.data("sort", "none");
            headers.attr("class", `column_ordering ${defaultTableSortArrow}`);
        }

        // Re-render each pill
        let listHtml = "";
        $.each(opus.prefs.order, function(index, orderEntry) {
            let isPillOrderDesc = orderEntry[0] === "-" ? "true" : "false";
            let pillOrderArrow = orderEntry[0] === "-" ? pillSortUpArrow : pillSortDownArrow;
            let orderEntrySlug = orderEntry[0] === "-" ? orderEntry.slice(1) : orderEntry;

            // Retrieve label from either displayed header's data-label attribute or displayed pill's text
            // The browse and cart sort pills will always be identical so we just get the one from browse
            // here. If we don't specify one, we end up getting two elements.
            let label = ($(`.op-data-table-view th a[data-slug="${orderEntrySlug}"]`).data("label") ||
                         $(`#browse .sort-contents span[data-slug="${orderEntrySlug}"] .flip-sort`).text());
            listHtml += "<li class='list-inline-item'>";
            listHtml += `<span class='badge badge-pill badge-light' data-slug="${orderEntrySlug}" data-descending="${isPillOrderDesc}">`;
            if (orderEntrySlug !== "opusid") {
                listHtml += "<span class='remove-sort' title='Remove metadata field from sort'><i class='fas fa-times-circle'></i></span> ";
            }
            listHtml += `<span class='flip-sort' title="${pillOrderTooltip}">`;
            listHtml += label;
            listHtml += ` <i class="${pillOrderArrow}"></i>`;
            listHtml += "</span></span></li>";
        });
        $(".sort-contents").html(listHtml);
    },

    renderSortedDataFromBeginning: function() {
        o_browse.clearObservationData();
        o_browse.loadData(opus.prefs.view);
    },

    loadPageIfNeeded: function(direction, opusId) {
        // opusId will be empty at the end of the observations, so just return out.
        if (opusId === "") {
            return;
        }
        let tab = opus.getViewTab();
        let contentsView = o_browse.getScrollContainerClass();
        let viewNamespace = opus.getViewNamespace();
        o_browse.metadataDetailOpusId = opusId;

        let maxObs = viewNamespace.totalObsCount;
        let element = (o_browse.isGalleryView() ? $(`${tab} .op-thumbnail-container[data-id=${opusId}]`) : $(`${tab} tr[data-id=${opusId}]`));
        let obsNum = $(element).data("obs");

        let checkView = (direction === "next" ? obsNum <= maxObs : obsNum > 0);

        if (checkView) {
            // make sure the current element that the modal is displaying is viewable
            if (!element.isOnScreen($(`${tab} .gallery-contents`), 0.5)) {
                let galleryBoundingRect = opus.getViewNamespace().galleryBoundingRect;

                let startObs = $(`${tab} ${contentsView}`).data("infiniteScroll").options.sliderObsNum;

                // if the binoculars have scrolled up, then reset the screen to the top;
                // if the binoculars have scrolled down off the screen, then scroll up just until the they are visible in bottom row
                if (obsNum > startObs) {    // the binoculars have scrolled off bottom
                    if (o_browse.isGalleryView()) {
                        obsNum = Math.max(obsNum - (galleryBoundingRect.x * (galleryBoundingRect.yPartial - 1)), 1);
                    } else {
                        obsNum = Math.max(obsNum - galleryBoundingRect.trFloor + 1, 1);
                    }
                }
                o_browse.onSliderHandleStop(tab, obsNum);
            }
        }
    },

    setScrollbarPosition: function(galleryObsNum, tableObsNum, view, offset=0) {
        let tab = opus.getViewTab(view);
        let galleryTarget = $(`${tab} .op-thumbnail-container[data-obs="${galleryObsNum}"]`);
        let tableTarget = $(`${tab} .op-data-table tbody tr[data-obs='${tableObsNum}']`);

        // Make sure obsNum is rendered before setting scrollbar position
        if (galleryTarget.length && tableTarget.length) {
            let galleryTargetTopPosition = galleryTarget.offset().top;
            let galleryContainerTopPosition = $(`${tab} .gallery-contents .op-gallery-view`).offset().top;
            let galleryScrollbarPosition = $(`${tab} .gallery-contents .op-gallery-view`).scrollTop();

            let galleryTargetFinalPosition = (galleryTargetTopPosition - galleryContainerTopPosition +
                                              galleryScrollbarPosition - offset);
            $(`${tab} .gallery-contents .op-gallery-view`).scrollTop(galleryTargetFinalPosition);

            // make sure it's scrolled to the correct position in table view
            let tableTargetTopPosition = tableTarget.offset().top;
            let tableContainerTopPosition = $(`${tab} .op-data-table-view`).offset().top;
            let tableScrollbarPosition = $(`${tab} .op-data-table-view`).scrollTop();
            let tableHeaderHeight = $(`${tab} .op-data-table thead th`).outerHeight();

            let tableTargetFinalPosition = (tableTargetTopPosition - tableContainerTopPosition +
                                            tableScrollbarPosition - tableHeaderHeight - offset);
            $(`${tab} .op-data-table-view`).scrollTop(tableTargetFinalPosition);
        }
    },

    // called when the slider is moved...
    onSliderHandleMoving: function(tab, value) {
        value = (value === undefined) ? 1 : Math.max(value, 1);
        $(`${tab} .op-observation-number`).html(o_utils.addCommas(value));
    },

    // This function will be called when we scroll the slide to a target value
    onSliderHandleStop: function(tab, value) {
        value = Math.max(value, 1);
        let view = opus.prefs.view;
        let elem = $(`${tab} .op-thumbnail-container[data-obs="${value}"]`);
        let startObsLabel = o_browse.getStartObsLabel();
        let viewNamespace = opus.getViewNamespace();
        let galleryBoundingRect = viewNamespace.galleryBoundingRect;
        let lastObs = $(`${tab} .op-thumbnail-container`).last().data("obs");

        // Update obsNum in infiniteScroll instances.
        // This obsNum is the first item in current page
        // (will be used to set scrollbar position in renderGalleryAndTable).
        // Set scrollbarOffset to 0 so that full startObs item can be displayed
        // after moving slider.
        let galleryValue = value;
        if (o_browse.isGalleryView()) {
            $(`${tab} .op-gallery-view`).infiniteScroll({
                "sliderObsNum": galleryValue,
                "scrollbarObsNum": value,
                "scrollbarOffset": 0
            });
        } else {
            // Calculate the gallery startObs
            galleryValue = (o_utils.floor((value - 1)/galleryBoundingRect.x) *
                            galleryBoundingRect.x + 1);
            $(`${tab} .op-gallery-view`).infiniteScroll({
                "sliderObsNum": galleryValue,
                "scrollbarObsNum": value,
                "scrollbarOffset": 0
            });
        }
        $(`${tab} .op-data-table-view`).infiniteScroll({
            "sliderObsNum": value,
            "scrollbarObsNum": value,
            "scrollbarOffset": 0
        });

        opus.prefs[startObsLabel] = value;

        if (elem.length > 0) {
            // When slider is moved to an obs close to the last cached obs (less than the number of
            // items fit on one page), we will load more data. This will make sure slider value
            // stays at where it's been dragged to even if that value is very close to the edge of
            // cached obs. We will check if the cached lastObs is the last obs based on the search.
            // This will make sure when dragging slider all the way to the right and there is no data
            // load triggered, scrollbar position will be set properly.
            if (lastObs - galleryValue < o_browse.getLimit() && lastObs !== viewNamespace.totalObsCount) {
                let contentsView = o_browse.getScrollContainerClass();
                $(`${tab} ${contentsView}`).infiniteScroll("loadNextPage");
            } else {
                o_browse.setScrollbarPosition(value, value);
            }
        } else {
            // When scrolling on slider and loadData is called, we will fetch 3 * getLimit items
            // (one current page, one next page, and one previous page) starting from obsNum.
            // obsNum will be the very first obs for data rendering this time
            // Use galleryValue here so that thumbnail image will be rendered & aligned properly.
            let obsNum = Math.max(galleryValue - o_browse.getLimit(), 1);

            // If obsNum is 1, previous page will have value - 1 items, so we render value - 1 + 2 * o_browse.getLimit() items
            // else we render 2 * o_browse.getLimit() items.
            let customizedLimitNum = obsNum === 1 ? galleryValue - 1 + 2 * o_browse.getLimit() : 3 * o_browse.getLimit();
            viewNamespace.reloadObservationData = true;
            o_browse.loadData(view, obsNum, customizedLimitNum);
        }
    },

    // find the first displayed observation index & id in the upper left corner
    updateSliderHandle: function(view, browserResized=false, isDOMChanged=false, isScrolling=false) {
        // Only update the slider & obSnum in infiniteScroll instances when the user
        // is at browse tab
        let tab = opus.getViewTab(view);
        let selector = (o_browse.isGalleryView(view) ?
                        `${tab} .gallery .op-thumbnail-container` :
                        `${tab} .op-data-table tbody tr`);
        let startObsLabel = o_browse.getStartObsLabel(view);

        let numObservations = $(selector).length;
        if (numObservations > 0) {
            // When we update the slider, the following steps are run:
            // 1. Get the current startObs (top left item in gallery view in current page)
            //    and top obsNum (top item in table view and one of top row items in gallery
            //    view) that scrollbar is at.
            //    - If browser is resized, realign DOMs by deleting some cached obSnum to make
            //      sure first cached obs are at the correct row boundary. If we don't do so,
            //      all rendered obs will be with the wrong row boundary after browser resizing.
            // 2. Get the scrollbar offset for both gallery and table view.
            // 3. Update the slider value and data in infiniteScroll instances and URL using
            //    the data obtained from above 2 steps.
            let obsNumObj = o_browse.realignDOMAndGetStartObsAndScrollbarObsNum(selector, browserResized,
                                                                                isDOMChanged, isScrolling);
            let obsNum = obsNumObj.startObs;
            let currentScrollObsNum = obsNumObj.scrollbarObsNum;
            let scrollbarOffset = o_browse.getScrollbarOffset(obsNum, currentScrollObsNum);
            o_browse.setSliderParameters(obsNum, currentScrollObsNum, scrollbarOffset.galleryOffset,
                                         scrollbarOffset.tableOffset);
        }

        let currentSliderValue = $(`${tab} .op-observation-slider`).slider("option", "value");
        let currentSliderMax = $(`${tab} .op-observation-slider`).slider("option", "max");

        let galleryImages = opus.getViewNamespace(view).galleryBoundingRect;

        let numberOfObsFitOnTheScreen = (o_browse.isGalleryView(view) ? galleryImages.x * galleryImages.y :
                                         galleryImages.tr);
        if ((opus.prefs[startObsLabel] + numObservations - 1) < numberOfObsFitOnTheScreen ||
            (currentSliderValue <= 1 && currentSliderValue >= currentSliderMax)) {
            // disable the slider because the observations don't fill the browser window
            $(`${tab} .op-slider-pointer`).css("width", "3ch");
            // Make sure slider always move to the most left before being disabled.
            $(`${tab} .op-observation-slider`).slider({"value": 1});
            $(`${tab} .op-observation-number`).html("-");
            $(`${tab} .op-slider-nav`).addClass("op-button-disabled");
        }
    },

    realignDOMAndGetStartObsAndScrollbarObsNum: function(selector, browserResized, isDOMChanged, isScrolling) {
        /**
         * Get the current startObs (obsNum, for slider number) in both
         * gallery (top-left item) and table (top item) views. Also get
         * the scrollbar obsNum (currentScrollObsNum, for setting scrollbar
         * location). In gallery view, scrollbar obsNum will be one of
         * items in the top row (can be different from gallery startObs).
         * In table view, scrollbar obsNum will be the top item (the same
         * as table startObs). If browser is resized, realign DOMs by
         * deleting some observations from the beginning. This will make
         * sure the first cached obs is at the correct row boundary
         * after browser resizing (which means (first obs - 1) % row size
         * is equal to 0). If we don't realign DOMs, first rendered obs
         * will be at the wrong row boundary, and all rendered obs will
         * be with the wrong row boundary ((first obs - 1) % row size
         * will not be 0).
         */
        let tab = opus.getViewTab();
        let viewNamespace = opus.getViewNamespace();
        let galleryBoundingRect = viewNamespace.galleryBoundingRect;
        // this will get the top left obsNum for gallery view or the top obsNum for table view
        let firstCachedObs = $(selector).first().data("obs");

        let numToDelete = 0;

        // When we keep resizing browser and more DOMs are deleted, infiniteScroll load will
        // trigger to load new data (previous page). During the time when infiniteScroll is
        // still loading (before all new obs are rendered), if we keep resizing and cause some
        // DOMs to get deleted, at the end after load is done, there will be some DOMs missing
        // between the end of newly loaded obs and beginning of old cached obs. So we add the
        // protection here. Another updateSliderHandle will be called to realign DOMS after all
        // new obs are rendered in infiniteScrollLoadEventListener.
        if ((browserResized || isDOMChanged) && !viewNamespace.infiniteScrollLoadInProgress) {
            // We delete cached obs when we are in gallery view or switch from table to gallery view.
            if (o_browse.isGalleryView()) {
                numToDelete = o_browse.deleteObsToCorrectRowBoundary(tab, firstCachedObs);
                // update firstCachedObs after first couple observations are deleted so that slider
                // will be upddated to the correct value when browser is resized
                firstCachedObs = $(selector).first().data("obs");
            }
        }

        let calculatedObsNumObj = o_browse.calculateCurrentStartObs(selector, firstCachedObs);
        let obsNum = calculatedObsNumObj.startObs;
        let currentScrollObsNum = calculatedObsNumObj.scrollbarObsNum;

        // If resize happened and some obs are deleted, we will make sure startObs right before resizing is
        // still in top row of gallery view. This will also make new startObs smaller than previous startObs
        // when resizing happened.
        let contentsView = o_browse.getScrollContainerClass();
        let prevObsNumBeforeResizing = $(`${tab} ${contentsView}`).data("infiniteScroll").options.sliderObsNum;
        if (browserResized || isDOMChanged) {
            if (o_browse.isGalleryView()) {
                obsNum = (Math.max((o_utils.floor((prevObsNumBeforeResizing - 1)/galleryBoundingRect.x) *
                galleryBoundingRect.x + 1), 1));
            }
        }

        // In gallery view, if scrollbarObsNum in infiniteScroll instance is:
        // (1) still within the current startObs' boundary
        // (2) larger than max slider value when current startObs is equal to max slider value
        // We want to make sure it didn't get updated to startObs. This will make sure table
        // view scrollbar location stays at where it's been left off when we switch back to
        // table view again.
        let nextObsNum = obsNum + galleryBoundingRect.x;
        let previousScrollObsNum = $(`${tab} ${contentsView}`).data("infiniteScroll").options.scrollbarObsNum;
        let maxSliderVal = o_browse.getSliderMaxValue();
        obsNum = Math.min(obsNum, maxSliderVal);

        if ((previousScrollObsNum >= obsNum && previousScrollObsNum < nextObsNum) ||
            (obsNum === maxSliderVal && previousScrollObsNum > maxSliderVal)) {
            currentScrollObsNum = o_browse.isGalleryView() ? previousScrollObsNum : currentScrollObsNum;
        }

        // Properly set obsNum to make sure the last row is fully displayed when scrollbar
        // reaches the end of the data.
        let lastObs = $(`${tab} .op-thumbnail-container`).last().data("obs");
        if (lastObs === viewNamespace.totalObsCount) {
            if (o_browse.isGalleryView()) {
                if (viewNamespace.galleryScrollbar.reach.y === "end" &&
                    obsNum >= maxSliderVal - galleryBoundingRect.x && isScrolling) {
                    obsNum = maxSliderVal;
                    if (previousScrollObsNum > maxSliderVal) {
                        currentScrollObsNum = previousScrollObsNum;
                    } else {
                        currentScrollObsNum = Math.min(currentScrollObsNum, maxSliderVal);
                    }
                }
            } else {
                if (viewNamespace.tableScrollbar.reach.y === "end" &&
                    obsNum >= maxSliderVal - galleryBoundingRect.trFloor) {
                    obsNum = maxSliderVal;
                }
            }
        }

        // When resizing happened, we need to manually set the scrollbar location so that:
        // 1. In gallery view, previous startObs (before resizing) is always in the top row.
        // 2. In table view, the top obs will stay the same.
        if (browserResized || isDOMChanged) {
            currentScrollObsNum = previousScrollObsNum;
            let infiniteScrollDataObj = $(`${tab} ${contentsView}`).data("infiniteScroll").options;
            let offset = infiniteScrollDataObj.scrollbarOffset;

            // When resizing with Ctrl + "+"/"-" (it triggers "scroll" event first, and then "resize" event),
            // sometimes the previous startObs will be moved to one row ahead of current top row. The
            // scrollbarOffset stored from updateSliderHandle in "scroll" event will have an absolute value
            // close to image size which will then set the scrollbar position with one row offset from
            // updateSliderHandle in "resize" event later. So we reset offset to 0 if the value stored in
            // infiniteScroll instance will cause one row difference in setScrollbarPosition.
            let compareFactor = o_browse.imageSize * o_browse.galleryImageViewableFraction;
            offset = (o_browse.isGalleryView() ? (Math.abs(offset) > compareFactor ? 0 : offset) : offset);

            // Set offset for scrollbar position so that it will have smooth scrolling in both
            // gallery and table view when infiniteScroll load is triggered.
            o_browse.setScrollbarPosition(obsNum, currentScrollObsNum, undefined, offset);
        }

        return {"startObs": obsNum, "scrollbarObsNum": currentScrollObsNum};
    },

    calculateCurrentStartObs: function(selector, firstCachedObs) {
        /**
         * Calculation of the current startObs based on rendered observations.
         */
        let tab = opus.getViewTab();
        let viewNamespace = opus.getViewNamespace();
        let galleryBoundingRect = viewNamespace.galleryBoundingRect;

        let firstCachedObsTop = $(selector).first().offset().top;
        let alignedCachedFirstObs = (o_browse.isGalleryView() ? (o_utils.floor((firstCachedObs - 1)/
                                     galleryBoundingRect.x) * galleryBoundingRect.x + 1) : firstCachedObs);

        // For gallery view, the topBoxBoundary is the top of .gallery-contents
        // For table view, we will set the topBoxBoundary to be the bottom of thead
        // (account for height of thead)
        let browseContentsContainerTop = $(`${tab} .gallery-contents`).offset().top;
        let topBoxBoundary = (o_browse.isGalleryView() ?
                              browseContentsContainerTop : browseContentsContainerTop +
                              $(`${tab} .op-data-table thead th`).outerHeight());

        // table: obsNum = alignedCachedFirstObs + number of row
        // gallery: obsNum = alignedCachedFirstObs + number of row * number of obs in a row
        // Note: in table view, if there are more than one row, we divide by the 2nd table tr's
        // height because in some corner cases, the first table tr's height will be 1px larger
        // than rest of tr, and this will mess up the calculation.
        let tableRowHeight = ($(`${tab} tbody tr`).length === 1 ? $(`${tab} tbody tr`).outerHeight() :
                              $(`${tab} tbody tr`).eq(1).outerHeight());

        let obsNumDiff = (o_browse.isGalleryView() ?
                          o_utils.floor((topBoxBoundary - firstCachedObsTop +
                                         o_browse.imageSize * o_browse.galleryImageViewableFraction) /
                                        o_browse.imageSize) * galleryBoundingRect.x :
                          o_utils.floor((topBoxBoundary - firstCachedObsTop +
                                         tableRowHeight * o_browse.galleryImageViewableFraction) /
                                        tableRowHeight));

        let obsNum = Math.max((obsNumDiff + alignedCachedFirstObs), 1);

        // currentScrollObsNum: the current top item in table view. This item is
        // also one of the top row items in gallery view
        // (it will be used to updated the table view scrollbar location).
        let currentScrollObsNum = obsNum;

        // obsNum: startObs, the most top left obsNum in gallery.
        // (it will be used to updated slider obsNum).
        // The calculation below is to make sure we are getting the first item in the
        // top row in gallery view.
        obsNum = (o_browse.isGalleryView() ? Math.max((o_utils.floor((obsNum - 1)/galleryBoundingRect.x) *
                  galleryBoundingRect.x + 1), 1) : obsNum);

        return {"startObs": obsNum, "scrollbarObsNum": currentScrollObsNum};
    },

    deleteObsToCorrectRowBoundary: function(tab, firstCachedObs) {
        /**
         * If browser window is resized, delete some cached observations
         * to make sure row boundary is correct. When browser is resized,
         * the first cached obs will always be rendered as the first item
         * of the top row of all rendered obs. If we don't delete some
         * observations from the beginning, the first cached obs will be
         * at the wrong row boundary. And all rendered obs will be at the
         * wrong row boundary ((first obs - 1) % row size will not
         * be 0). So we delete some observations and that way the first
         * cached obs is at the correct row boundary after resizing (
         * (first obs - 1) % row size is equal to 0).
         */
        let viewNamespace = opus.getViewNamespace();
        let galleryBoundingRect = viewNamespace.galleryBoundingRect;
        let numToDelete = ((galleryBoundingRect.x - (firstCachedObs - 1) % galleryBoundingRect.x) %
                           galleryBoundingRect.x);

        let galleryObsElem = $(`${tab} .gallery [data-obs]`);
        let tableObsElem = $(`${tab} .op-data-table-view [data-obs]`);
        // delete first "numToDelete" obs if row size is changed
        for (let count = 0; count < numToDelete; count++) {
            o_browse.deleteCachedObservation(galleryObsElem, tableObsElem, count, viewNamespace);
        }

        return numToDelete;
    },

    getSliderMaxValue: function() {
        /**
         * Get the maximum value for slider based on gallery view row
         * boundary.
         */
        let viewNamespace = opus.getViewNamespace();
        let galleryBoundingRect = viewNamespace.galleryBoundingRect;
        let dataResultCount = viewNamespace.totalObsCount;
        let firstObsInLastRow = (o_utils.floor((dataResultCount - 1)/galleryBoundingRect.x) *
                                 galleryBoundingRect.x + 1);

        // Add one more row to max slider value. This will make sure the last row is fully displayed
        // when slider is moved to the end.
        let maxSliderVal = (o_browse.isGalleryView() ?
                            firstObsInLastRow - galleryBoundingRect.x * (galleryBoundingRect.yFloor-1) :
                            viewNamespace.totalObsCount - galleryBoundingRect.trFloor + 1);
        // Max slider value can't go negative
        maxSliderVal = Math.max(maxSliderVal, 1);
        return maxSliderVal;
    },

    setSliderParameters: function(obsNum, currentScrollObsNum, galleryOffset, tableOffset) {
        /**
         * Change the slider value and update data in infiniteScroll
         * instances.
         */
        let tab = opus.getViewTab();
        let viewNamespace = opus.getViewNamespace();
        let galleryBoundingRect = viewNamespace.galleryBoundingRect;
        let startObsLabel = o_browse.getStartObsLabel();
        let maxSliderVal = o_browse.getSliderMaxValue();

        if (maxSliderVal >= obsNum) {
            // "sliderObsNum" will be the startObs.
            // "scrollbarObsNum" will be the obsNum at current scrollbar location.
            // In table view, it's the top obsNum. In gallery view, it's one of obsNums in the top row.
            $(`${tab} .op-gallery-view`).infiniteScroll({
                "sliderObsNum": obsNum,
                "scrollbarObsNum": currentScrollObsNum,
                "scrollbarOffset": galleryOffset
            });
            $(`${tab} .op-data-table-view`).infiniteScroll({
                "sliderObsNum": obsNum,
                "scrollbarObsNum": currentScrollObsNum,
                "scrollbarOffset": tableOffset
            });
            opus.prefs[startObsLabel] = obsNum;

            $(`${tab} .op-observation-number`).html(o_utils.addCommas(obsNum));
            $(`${tab} .op-slider-pointer`).css("width", `${o_utils.addCommas(maxSliderVal).length*0.7}em`);

            // just make the step size the number of the obserations across the page...
            // if the observations have not yet been rendered, leave the default, it will get changed later
            if (galleryBoundingRect.x > 0) {
                o_browse.gallerySliderStep = galleryBoundingRect.x;
            }
            if (o_browse.isGalleryView()) {
                $(`${tab} .op-observation-slider`).slider({
                    "step": o_browse.gallerySliderStep,
                });
            } else {
                $(`${tab} .op-observation-slider`).slider({
                    "step": 1,
                });
            }
            $(`${tab} .op-observation-slider`).slider({
                "value": obsNum,
                "max": maxSliderVal,
            });
        }
        $(`${tab} .op-slider-nav`).removeClass("op-button-disabled");
        // update startobs in url when scrolling
        o_hash.updateHash();
    },

    getScrollbarOffset: function(obsNum, currentScrollObsNum) {
        /**
         * Get galleryOffset and tableOffset, these values will be used
         * in the calculation in setScrollbarPosition and provide smooth
         * scrolling when infiniteScroll load event is triggered.
         */
        let tab = opus.getViewTab();
        let galleryTarget = $(`${tab} .op-thumbnail-container[data-obs="${obsNum}"]`);
        let tableTarget = $(`${tab} .op-data-table tbody tr[data-obs='${currentScrollObsNum}']`);
        let galleryOffset = 0;
        let tableOffset = 0;
        if (galleryTarget.length && tableTarget.length) {
            let galleryTargetTopPosition = galleryTarget.offset().top;
            let galleryContainerTopPosition = $(`${tab} .gallery-contents .op-gallery-view`).offset().top;
            galleryOffset = galleryTargetTopPosition - galleryContainerTopPosition;
            let tableTargetTopPosition = tableTarget.offset().top;
            let tableContainerTopPosition = $(`${tab} .op-data-table-view`).offset().top;
            let tableHeaderHeight = $(`${tab} .op-data-table thead th`).outerHeight();
            tableOffset = tableTargetTopPosition - tableContainerTopPosition - tableHeaderHeight;
        }

        return {"galleryOffset": galleryOffset, "tableOffset": tableOffset};
    },

    checkScroll: function() {
        // this will make sure ps-scroll-up is triggered to prefetch
        // previous data when scrollbar reaches to up scroll threshold point.
        let tab = opus.getViewTab();
        let view = opus.prefs.view;
        let contentsView = o_browse.getScrollContainerClass();
        if ($(`${tab} ${contentsView}`).scrollTop() < infiniteScrollUpThreshold) {
            $(`${tab} ${contentsView}`).trigger("ps-scroll-up");
        }
        o_browse.updateSliderHandle(view, false, false, true);
        return false;
    },

    showMetadataDetailModal: function(opusId) {
        o_browse.loadPageIfNeeded("prev", opusId);
        o_browse.updateGalleryView(opusId);
        // this is to make sure modal is at its original position when open again
        $("#galleryView .modal-dialog").css({top: 0, left: 0});
        $("#galleryView").modal("show");

        // Do the fake API call to write in the Apache log files that
        // we showed the modal for this OPUSID. This is what the previous
        // version of OPUS did so the log_analyzer already handles it. Note that
        // we won't get separate log entries as the user navigates through
        // the obs using the arrows because we don't want to overload the
        // network with an entry for each opus id.
        let fakeUrl = `/opus/__fake/__viewmetadatamodal/${opusId}.json`;
        $.getJSON(fakeUrl, function(data) {
        });

    },

    hideGalleryViewModal: function() {
        $("#galleryView").modal("hide");
        o_browse.metadataDetailOpusId = "";
    },

    hideMenu: function() {
        $("#op-obs-menu").removeClass("show").hide();
    },

    showMenu: function(e, opusId) {
        // make this like a default right click menu
        let tab = opus.getViewTab();
        if ($("#op-obs-menu").hasClass("show")) {
            o_browse.hideMenu();
        }
        let inCart = (o_cart.isIn(opusId) ? "" : "remove");
        let buttonInfo = o_browse.cartButtonInfo(inCart);
        $("#op-obs-menu .dropdown-header").html(opusId);
        $("#op-obs-menu [data-action='cart']").html(`<i class="${buttonInfo[tab].icon}"></i>${buttonInfo[tab].title}`);
        $("#op-obs-menu [data-action='cart']").attr("data-id", opusId);
        $("#op-obs-menu [data-action='info']").attr("data-id", opusId);
        $("#op-obs-menu [data-action='info']").attr("href", o_browse.getDetailURL(opusId));
        $("#op-obs-menu [data-action='downloadCSV']").attr("href",`/opus/__api/metadata_v2/${opusId}.csv?cols=${opus.prefs.cols.join()}`);
        $("#op-obs-menu [data-action='downloadCSVAll']").attr("href",`/opus/__api/metadata_v2/${opusId}.csv`);
        $("#op-obs-menu [data-action='downloadData']").attr("href",`/opus/__api/download/${opusId}.zip?cols=${opus.prefs.cols.join()}`);
        $("#op-obs-menu [data-action='downloadURL']").attr("href",`/opus/__api/download/${opusId}.zip?urlonly=1&cols=${opus.prefs.cols.join()}`);

        // use the state of the current selected observation to set the icons if one has been selected,
        // otherwise use the state of the current observation - this will identify what will happen to the range
        let rangeSelected = o_browse.isRangeSelectEnabled(tab);
        let rangeText = "";
        if (rangeSelected !== undefined) {
            rangeText = `<i class='fas fa-sign-out-alt fa-rotate-180'></i>End ${buttonInfo[tab].rangeTitle}`;
        } else {
            rangeText = `<i class='fas fa-sign-out-alt'></i>Start ${buttonInfo[tab].rangeTitle}`;
        }

        $("#op-obs-menu .dropdown-item[data-action='range']").html(rangeText);

        let menu = {"height":$("#op-obs-menu").innerHeight(), "width":$("#op-obs-menu").innerWidth()};
        let top = ($(tab).innerHeight() - e.pageY > menu.height) ? e.pageY-5 : e.pageY-menu.height;
        let left = ($(tab).innerWidth() - e.pageX > menu.width)  ? e.pageX-5 : e.pageX-menu.width;

        $("#op-obs-menu").css({
            display: "block",
            top: top,
            left: left
        }).addClass("show")
            .attr("data-id", opusId);
    },

    getDetailURL: function(opusId) {
        let hashArray = o_hash.getHashArray();
        hashArray.detail = opusId;
        hashArray.view = "detail";
        let link = "/opus/#/" + o_hash.hashArrayToHashString(hashArray);
        return link;
    },

    showDetail: function(e, opusId) {
        o_browse.hideMenu();
        let url = o_browse.getDetailURL(opusId);
        if (e.handleObj.origType === "contextmenu") {
            // handles command click to open in new tab
            $(e.target).parent().attr("href", url);
        } else if (e.ctrlKey || e.metaKey) {
            // open detail view in new browser tab
            e.preventDefault();
            window.open(url, "_blank");
        }  else {
            opus.prefs.detail = opusId;
            opus.changeTab("detail");
            $('a[href="#detail"]').tab("show");
        }
    },

    getGalleryElement: function(opusId) {
        let tab = opus.getViewTab();
        return $(`${tab} .op-thumbnail-container[data-id=${opusId}]`);
    },

    getDataTableInputElement: function(opusId) {
        return $(`.op-data-table div[data-id=${opusId}]`).parent();
    },

    highlightStartOfRange: function(opusId) {
        o_browse.getGalleryElement(opusId).addClass("selected hvr-ripple-in b-a-2");
        o_browse.getDataTableInputElement(opusId).addClass("hvr-ripple-in b-a-2");
    },

    startRangeSelect: function(opusId) {
        let tab = opus.getViewTab();
        let galleryElement = o_browse.getGalleryElement(opusId);
        let obsNum = galleryElement.data("obs");
        let action = (galleryElement.hasClass("op-in-cart") ? "removerange" : "addrange");
        let actionText = (action === "removerange" ? "Remove range from cart" : "Add range to cart");
        if (tab === "#cart") {
            actionText = (action === "removerange" ? "Move range to recycle bin" : "Restore range from recycle bin");
        }
        $(`${tab} .op-range-select-info-box`).html(`${actionText} starting at observation #${obsNum} ${opusId}  (ESC to cancel)`).addClass("op-range-select");
        $(`${tab} .op-gallery-view`).infiniteScroll({
            "rangeSelectOpusID": opusId,
            "rangeSelectObsNum": obsNum,
            "rangeSelectOption": action
        });
        o_browse.highlightStartOfRange(opusId);
    },

    undoRangeSelect: function() {
        let tab = opus.getViewTab();

        let startElem = $(tab).find(".selected");
        if (startElem.length) {
            $(startElem).removeClass("selected hvr-ripple-in b-a-2");
            let opusId = $(startElem).data("id");
            o_browse.getDataTableInputElement(opusId).removeClass("hvr-ripple-in b-a-2");
        }
        $(`${tab} .op-gallery-view`).data("infiniteScroll").options.rangeSelectOpusID = undefined;
        $(`${tab} .op-gallery-view`).data("infiniteScroll").options.rangeSelectObsNum = undefined;
        $(`${tab} .op-gallery-view`).data("infiniteScroll").options.rangeSelectOption = undefined;
        $(`${tab} .op-range-select-info-box`).removeClass("op-range-select");
    },

    isRangeSelectEnabled: function(tab) {
        return $(`${tab} .op-gallery-view`).data("infiniteScroll").options.rangeSelectOption;
    },

    openDetailTab: function() {
        o_browse.hideGalleryViewModal();
        opus.changeTab("detail");
    },

    showPageLoaderSpinner: function() {
        if (o_browse.pageLoaderSpinnerTimer === null) {
            o_browse.pageLoaderSpinnerTimer = setTimeout(function() {
                $(`.op-page-loading-status > .loader`).show(); }, opus.spinnerDelay);
        }
    },

    hidePageLoaderSpinner: function() {
        if (o_browse.pageLoaderSpinnerTimer !== null) {
            // The right way to fix this is probably to reference count the on/off actions,
            // since they should always be paired, and that way the spinner won't turn off
            // until the last operation is complete. However, this sounds like a recipe for bugs,
            // and it isn't a common occurrence
            clearTimeout(o_browse.pageLoaderSpinnerTimer);
            $(`.op-page-loading-status > .loader`).hide();
            o_browse.pageLoaderSpinnerTimer = null;
        }
    },

    /******************************************/
    /********* SELECT METADATA DIALOG *********/
    /******************************************/

    // metadata selector behaviors
    addSelectMetadataBehaviors: function() {
        // Global within this function so behaviors can communicate
        /* jshint varstmt: false */
        var currentSelectedMetadata = opus.prefs.cols.slice();
        /* jshint varstmt: true */

        $("#op-select-metadata").on("hide.bs.modal", function(e) {
            // update the data table w/the new columns
            if (!o_utils.areObjectsEqual(opus.prefs.cols, currentSelectedMetadata)) {
                let tab = opus.getViewTab();
                o_browse.clearObservationData(true); // Leave startobs alone
                o_hash.updateHash(); // This makes the changes visible to the user
                o_browse.initTable(tab, opus.colLabels, opus.colLabelsNoUnits);
                o_browse.loadData(opus.prefs.view);
            } else {
                // remove spinner if nothing is re-draw when we click save changes
                o_browse.hidePageLoaderSpinner();
            }
        });

        $("#op-select-metadata").on("show.bs.modal", function(e) {
            // this is to make sure modal is back to it original position when open again
            $("#op-select-metadata .modal-dialog").css({top: 0, left: 0});
            o_browse.adjustSelectMetadataHeight();
            // save current column state so we can look for changes
            currentSelectedMetadata = opus.prefs.cols.slice();

            o_browse.hideMenu();
            o_browse.renderSelectMetadata();

            // Do the fake API call to write in the Apache log files that
            // we invoked the metadata selector so log_analyzer has something to
            // go on
            let fakeUrl = "/opus/__fake/__selectmetadatamodal.json";
            $.getJSON(fakeUrl, function(data) {
            });
        });

        $("#op-select-metadata .op-all-metadata-column").on("click", '.submenu li a', function() {
            let slug = $(this).data('slug');
            if (!slug) { return; }

            let chosenSlugSelector = `#cchoose__${slug}`;
            let menuSelector = `#op-select-metadata .op-all-metadata-column a[data-slug=${slug}]`;

            if ($(chosenSlugSelector).length === 0) {
                // this slug was previously unselected, add to cols
                o_menu.markMenuItem(menuSelector);
                o_browse.addColumn(slug);
                opus.prefs.cols.push(slug);
            } else {
                // slug had been checked, remove from the chosen
                o_menu.markMenuItem(menuSelector, "unselected");
                opus.prefs.cols.splice($.inArray(slug,opus.prefs.cols), 1);
                $(chosenSlugSelector).fadeOut(200, function() {
                    $(this).remove();
                });
            }
            return false;
        });

        // removes chosen column
        $("#op-select-metadata .op-selected-metadata-column").on("click", "li .unselect", function() {
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
                let menuSelector = `#op-select-metadata .op-all-metadata-column a[data-slug=${slug}]`;
                o_menu.markMenuItem(menuSelector, "unselected");
            }
            return false;
        });

        // buttons
        $("#op-select-metadata").on("click", ".btn", function() {
            switch($(this).attr("type")) {
                case "reset":
                    opus.prefs.cols = [];
                    o_browse.resetMetadata(opus.defaultColumns);
                    break;
                case "submit":
                    o_browse.showPageLoaderSpinner();
                    break;
                case "cancel":
                    opus.prefs.cols = [];
                    o_browse.resetMetadata(currentSelectedMetadata, true);
                    break;
            }
        });
    },  // /addSelectMetadataBehaviors

    renderSelectMetadata: function() {
        if (!o_browse.selectMetadataDrawn) {
            let url = "/opus/__forms/metadata_selector.html?" + o_hash.getHash();
            $(".modal-body.op-select-metadata-details").load( url, function(response, status, xhr)  {
                o_browse.selectMetadataDrawn = true;  // bc this gets saved not redrawn
                $("#op-select-metadata .op-reset-button").hide(); // we are not using this

                // since we are rendering the left side of metadata selector w/the same code that builds the select menu,
                // we need to unhighlight the selected widgets
                o_menu.markMenuItem("#op-select-metadata .op-all-metadata-column a", "unselect");

                // display check next to any currently used columns
                $.each(opus.prefs.cols, function(index, col) {
                    o_menu.markMenuItem(`#op-select-metadata .op-all-metadata-column a[data-slug="${col}"]`);
                });

                o_browse.addSelectMetadataBehaviors();

                o_browse.allMetadataScrollbar = new PerfectScrollbar("#op-select-metadata-contents .op-all-metadata-column", {
                    minScrollbarLength: opus.minimumPSLength
                });
                o_browse.selectedMetadataScrollbar = new PerfectScrollbar("#op-select-metadata-contents .op-selected-metadata-column", {
                    minScrollbarLength: opus.minimumPSLength
                });

                $(".op-selected-metadata-column > ul").sortable({
                    items: "li",
                    cursor: "grab",
                    stop: function(event, ui) { o_browse.metadataDragged(this); }
                });
                o_browse.adjustSelectMetadataHeight();
            });
        }
    },

    addColumn: function(slug) {
        let menuSelector = `#op-select-metadata .op-all-metadata-column a[data-slug=${slug}]`;
        o_menu.markMenuItem(menuSelector);

        let label = $(menuSelector).data("qualifiedlabel");
        let info = `<i class="fas fa-info-circle" title="${$(menuSelector).find('*[title]').attr("title")}"></i>`;
        let html = `<li id="cchoose__${slug}" class="ui-sortable-handle"><span class="info">&nbsp;${info}</span>${label}<span class="unselect"><i class="far fa-trash-alt"></span></li>`;
        $(".op-selected-metadata-column > ul").append(html);
    },

    // columns can be reordered wrt each other in 'metadata selector' by dragging them
    metadataDragged: function(element) {
        let cols = $.map($(element).sortable("toArray"), function(item) {
            return item.split("__")[1];
        });
        opus.prefs.cols = cols;
    },

    resetMetadata: function(cols, closeModal) {
        opus.prefs.cols = cols.slice();

        if (closeModal == true) {
            $("#op-select-metadata").modal('hide');
        }

        // uncheck all on left; we will check them as we go
        o_menu.markMenuItem("#op-select-metadata .op-all-metadata-column a", "unselect");

        // remove all from selected column
        $("#op-select-metadata .op-selected-metadata-column li").remove();

        // add them back and set the check
        $.each(cols, function(index, slug) {
            o_browse.addColumn(slug);
        });
    },

    adjustSelectMetadataHeight: function() {
        /**
         * Set the height of the "Select Metadata" dialog based on the browser size.
         */
        $(".op-select-metadata-headers").show(); // Show now so computations are accurate
        $(".op-select-metadata-headers-hr").show();
        let footerHeight = $(".app-footer").outerHeight();
        let mainNavHeight = $("#op-main-nav").outerHeight();
        let modalHeaderHeight = $("#op-select-metadata .modal-header").outerHeight();
        let modalFooterHeight = $("#op-select-metadata .modal-footer").outerHeight();
        let selectMetadataHeadersHeight = $(".op-select-metadata-headers").outerHeight()+30;
        let selectMetadataHeadersHRHeight = $(".op-select-metadata-headers-hr").outerHeight();
        /* If modalHeaderHeight is zero, the dialog is in the process of being rendered
           and we don't have valid data yet. If we set the height based on the zeros,
           we get an annoying "jump" in the dialog size after it's done rendering.
           So we use a default value that will cover the common case of a dialog wide
           enough to cause excessive header word wrap.
        */
        if (modalHeaderHeight === 0) {
            modalHeaderHeight = 57;
            modalFooterHeight = 68;
            selectMetadataHeadersHeight = 122;
            selectMetadataHeadersHRHeight = 1;
        }
        let totalNonScrollableHeight = (footerHeight + mainNavHeight + modalHeaderHeight +
                                        modalFooterHeight + selectMetadataHeadersHeight +
                                        selectMetadataHeadersHRHeight);
        /* 55 is a rough guess for how much space we want below the dialog, when possible.
           130 is the minimum size required to display four metadata fields.
           Anything less than that makes the dialog useless. In that case we hide the
           header text to give us more room. */
        let height = Math.max($(window).height()-totalNonScrollableHeight-55);
        if (height < 130) {
            $(".op-select-metadata-headers").hide();
            $(".op-select-metadata-headers-hr").hide();
            height += selectMetadataHeadersHeight + selectMetadataHeadersHRHeight;
        }
        $(".op-all-metadata-column").css("height", height);
        $(".op-selected-metadata-column").css("height", height);
    },

    selectMetadataMenuContainerHeight: function() {
        return $(".op-all-metadata-column").outerHeight();
    },

    selectedMetadataContainerHeight: function() {
        return $(".op-selected-metadata-column").outerHeight();
    },

    hideOrShowSelectMetadataMenuPS: function() {
        let containerHeight = $(".op-all-metadata-column").height();
        let menuHeight = $(".op-all-metadata-column .op-search-menu").height();
        if (o_browse.allMetadataScrollbar) {
            if (containerHeight >= menuHeight) {
                if (!$(".op-all-metadata-column .ps__rail-y").hasClass("hide_ps__rail-y")) {
                    $(".op-all-metadata-column .ps__rail-y").addClass("hide_ps__rail-y");
                    o_browse.allMetadataScrollbar.settings.suppressScrollY = true;
                }
            } else {
                $(".op-all-metadata-column .ps__rail-y").removeClass("hide_ps__rail-y");
                o_browse.allMetadataScrollbar.settings.suppressScrollY = false;
            }
            o_browse.allMetadataScrollbar.update();
        }
    },

    hideOrShowSelectedMetadataPS: function() {
        let containerHeight = $(".op-selected-metadata-column").height();
        let selectedMetadataHeight = $(".op-selected-metadata-column .ui-sortable").height();

        if (o_browse.selectedMetadataScrollbar) {
            if (containerHeight >= selectedMetadataHeight) {
                if (!$(".op-selected-metadata-column .ps__rail-y").hasClass("hide_ps__rail-y")) {
                    $(".op-selected-metadata-column .ps__rail-y").addClass("hide_ps__rail-y");
                    o_browse.selectedMetadataScrollbar.settings.suppressScrollY = true;
                }
            } else {
                $(".op-selected-metadata-column .ps__rail-y").removeClass("hide_ps__rail-y");
                o_browse.selectedMetadataScrollbar.settings.suppressScrollY = false;
            }
            o_browse.selectedMetadataScrollbar.update();
        }
    },

    /*************************************************/
    /********* END OF SELECT METADATA DIALOG *********/
    /*************************************************/


    getViewInfo: function() {
        // this function returns some data you need depending on whether
        // you are in #cart or #browse views
        let namespace = "#browse";
        let prefix = "";
        if (opus.prefs.view == "cart") {
            namespace = "#cart";
            prefix = "cart_";
        }
        return {"namespace":namespace, "prefix":prefix};

    },

    updateBrowseNav: function() {
        o_browse.fading = true;
        let tab = opus.getViewTab();
        let contentsView = o_browse.getScrollContainerClass();

        let galleryInfiniteScroll = $(`${tab} .op-gallery-view`).data("infiniteScroll");
        let tableInfiniteScroll = $(`${tab} .op-data-table-view`).data("infiniteScroll");

        let browseViewSelector = $(`${tab} .op-browse-view`);

        let suppressScrollY = false;

        if (o_browse.isGalleryView()) {
            $(".op-data-table-view", tab).hide();
            $(`${tab} .op-gallery-view`).fadeIn("done", function() {o_browse.fading = false;});

            browseViewSelector.html("<i class='far fa-list-alt'></i>&nbsp;View Table");
            browseViewSelector.attr("title", "View sortable metadata table");
            browseViewSelector.data("view", "data");

            suppressScrollY = false;
        } else {
            $(`${tab} .op-gallery-view`).hide();
            $(`${tab} .op-data-table-view`).fadeIn("done", function() {o_browse.fading = false;});

            browseViewSelector.html("<i class='far fa-images'></i>&nbsp;View Gallery");
            browseViewSelector.attr("title", "View sortable thumbnail gallery");
            browseViewSelector.data("view", "gallery");

            suppressScrollY = true;
        }
        opus.getViewNamespace().galleryScrollbar.settings.suppressScrollY = suppressScrollY;

        // sync up scrollbar position
        if (galleryInfiniteScroll && tableInfiniteScroll) {
            let startObs = $(`${tab} ${contentsView}`).data("infiniteScroll").options.sliderObsNum;
            let scrollbarObs = $(`${tab} ${contentsView}`).data("infiniteScroll").options.scrollbarObsNum;
            o_browse.setScrollbarPosition(startObs, scrollbarObs);
        }
    },

    updateStartobsInUrl: function(view, url, startObs) {
        let obsStr = o_browse.getStartObsLabel(view);
        // remove any existing startobs= slug
        url = $.grep(url.split('&'), function(pair, index) {
            return !pair.startsWith(obsStr);
        }).join('&');

        url += `&${obsStr}=${startObs}`;
        return url;
    },

    updateViewInUrl: function(view, url) {
        // remove any existing view= slug
        let slug = "view";
        url = $.grep(url.split('&'), function(pair, index) {
            return !pair.startsWith(slug);
        }).join('&');

        url += `&${slug}=${view}`;
        return url;
    },

    renderGalleryAndTable: function(data, url, view) {
        // render the gallery and table at the same time.
        let tab = opus.getViewTab(view);
        let viewNamespace = opus.getViewNamespace(view);
        let contentsView = o_browse.getScrollContainerClass(view);
        let selector = `${tab} ${contentsView}`;
        let infiniteScrollDataObj = $(selector).data("infiniteScroll").options;

        // this is the list of all observations requested from dataimages.json
        let galleryHtml = "";
        let tableHtml = "";

        if (data.count == 0) {
            // either there are no selections OR this is signaling the end of the infinite scroll
            if (data.total_obs_count == 0) {   // empty results, post message
                $(`${tab} .navbar`).addClass("op-button-disabled");
                $(`${tab} .gallery`).empty();
                $(`${tab} .op-data-table tbody`).empty();
                $(`${tab} .op-data-table-view`).hide();
                $(`${tab} .op-results-message`).show();
            } else {
                // end of infinite scroll OR invalid startObs
                if (opus.prefs[o_browse.getStartObsLabel()] > data.total_obs_count) {
                    // handle a corner case where a user has changed the startobs to be greater than total_obs_count
                    // just reset back to 1 and get a new page
                    opus.prefs[o_browse.getStartObsLabel()] = 1;
                    o_hash.updateHash();
                    $("#galleryViewContents").addClass("op-disabled");
                    $(`${tab} ${contentsView}`).infiniteScroll("loadNextPage");
                } else {
                    // we've hit the end of the infinite scroll.
                    o_browse.hidePageLoaderSpinner();
                }
                return;
            }
        } else {
            let lastObs = $(`${tab} .op-thumbnail-container`).last().data("obs");
            let append = (lastObs === undefined || data.start_obs > lastObs);

            o_browse.manageObservationCache(data.count, append, view);
            $(`${tab} .op-results-message`).hide();
            $(`${tab} .navbar`).removeClass("op-button-disabled");
            if (o_browse.isGalleryView(view)) {
                $(`${tab} .op-gallery-view`).show();
            } else {
                $(`${tab} .op-data-table-view`).show();
            }

            viewNamespace.totalObsCount = data.total_obs_count;

            $.each(data.page, function(index, item) {
                let opusId = item.opusid;
                // we have to store the relative observation number because we may not have pages in succession, this is for the slider position
                viewNamespace.observationData[opusId] = item.metadata;	// for galleryView, store in global array
                let buttonInfo = o_browse.cartButtonInfo((item.cart_state === "cart" ? "" : "remove"));

                let mainTitle = `#${item.obs_num}: ${opusId}\r\nClick to enlarge (slideshow mode)\r\Ctrl+click to ${buttonInfo[tab].title.toLowerCase()}\r\nShift+click to start/end range`;

                // gallery
                let images = item.images;
                let url = o_browse.getDetailURL(opusId);

                // DEBBY
                galleryHtml += `<div class="op-thumbnail-container ${(item.cart_state === "cart" ? 'op-in-cart' : '')}" data-id="${opusId}" data-obs="${item.obs_num}">`;
                galleryHtml += `<a href="${url}" class="thumbnail" data-image="${images.full.url}">`;
                galleryHtml += `<img class="img-thumbnail img-fluid" src="${images.thumb.url}" alt="${images.thumb.alt_text}" title="${mainTitle}">`;

                // whenever the user clicks an image to show the modal, we need to highlight the selected image w/an icon
                galleryHtml += '<div class="op-modal-overlay">';
                galleryHtml += '<p class="content-text"><i class="fas fa-binoculars fa-4x text-info" aria-hidden="true"></i></p>';
                galleryHtml += '</div></a>';

                // recycle bin icon container
                galleryHtml += `<div class="op-recycle-overlay ${((tab === "#cart" && item.cart_state === "recycle") ? '' : 'op-hide-element')}" title="${mainTitle}">`;
                galleryHtml += '<p class="content-text"><i class="fas fa-recycle fa-4x text-success" aria-hidden="true"></i></p>';
                galleryHtml += '</div></a>';

                galleryHtml += '<div class="op-thumb-overlay">';
                galleryHtml += `<div class="op-tools dropdown" data-id="${opusId}">`;
                galleryHtml +=     '<a href="#" data-icon="info" title="View observation detail (use Ctrl for new tab)"><i class="fas fa-info-circle fa-xs"></i></a>';

                galleryHtml +=     `<a href="#" data-icon="cart" title="${buttonInfo[tab].title}"><i class="${buttonInfo[tab].icon} fa-xs"></i></a>`;
                galleryHtml +=     '<a href="#" data-icon="menu" title="More options"><i class="fas fa-bars fa-xs"></i></a>';
                galleryHtml += '</div>';
                galleryHtml += '</div></div>';

                // table row
                let checked = item.cart_state === "cart" ? " checked" : "";
                let recycled = (tab === "#cart" && item.cart_state === "recycle") ? "class='text-success op-recycled'" : "";
                let checkbox = `<input type="checkbox" name="${opusId}" value="${opusId}" class="multichoice"${checked}/>`;
                let minimenu = `<a href="#" data-icon="menu" title="More options"><i class="fas fa-bars fa-xs"></i></a>`;
                let row = `<td class="op-table-tools"><div class="op-tools mx-0 form-group" title="Click to ${buttonInfo[tab].title.toLowerCase()}\r\nShift+click to start/end range" data-id="${opusId}">${checkbox} ${minimenu}</div></td>`;
                let tr = `<tr data-id="${opusId}" ${recycled} data-target="#galleryView" data-obs="${item.obs_num}" title="${mainTitle}">`;
                $.each(item.metadata, function(index, cell) {
                    row += `<td>${cell}</td>`;
                });
                tableHtml += `${tr}${row}</tr>`;
            });

            galleryHtml += "</div>";
            // wondering if there should be more logic here to determine if the new block of observations
            // is contiguous w/the existing block of observations, not just before/after...
            if (append) {
                $(".gallery", tab).append(galleryHtml);
                $(".op-data-table-view tbody", tab).append(tableHtml);
            } else {
                $(".gallery", tab).prepend(galleryHtml);
                $(".op-data-table-view tbody", tab).prepend(tableHtml);
            }
        }

        // we must always use the op-gallery-view infinite scroll object for the rangeSelectOpusID because we only
        // keep track of the range select variables in one of the infinite scroll objects.
        let rangeSelectOpusID = $(`${tab} .op-gallery-view`).data("infiniteScroll").options.rangeSelectOpusID;
        o_browse.highlightStartOfRange(rangeSelectOpusID);

        // Note: we have to manually set the scrollbar position.
        // - scroll up: when we scroll up and a new page is fetched, we want to keep scrollbar position at the current startObs,
        //   instead of at the first item in newly fetched page.
        // - scroll slider: when we load 3 * getLimit items, we want to keep scrollbar in the middle page.
        // - scroll down: theoretically, infiniteScroll will take care of scrollbar position, but we still have to manually set
        //   it for the case when cached data is removed so that scrollbar position is always correct (and never reaches to the
        //   end until it reaches to the end of the data)
        o_browse.setScrollbarPosition(infiniteScrollDataObj.sliderObsNum,
                                      infiniteScrollDataObj.scrollbarObsNum, view,
                                      infiniteScrollDataObj.scrollbarOffset);

        o_browse.hidePageLoaderSpinner();
        o_browse.updateSliderHandle(view);
        o_hash.updateHash();
    },

    initTable: function(tab, columns, columnsNoUnits) {
        // prepare table and headers...
        $(`${tab} .op-data-table > thead`).empty();
        $(`${tab} .op-data-table > tbody`).empty();

        // NOTE:  At some point, ORDER needs to be identified in the table, as to which column we are ordering on

        // because i need the slugs for the columns
        let hashArray = o_hash.getHashArray();
        let slugs = hashArray.cols.split(",");
        let order = hashArray.order.split(",");
        // we only want to sort the column based on first slug in order for now
        order.splice(1);

        opus.colLabels = columns;
        opus.colLabelsNoUnits = columnsNoUnits;

        // check all box
        //let checkbox = "<input type='checkbox' name='all' value='all' class='multichoice'>";
        $(`${tab} .op-data-table-view thead`).append("<tr></tr>");
        $(`${tab} .op-data-table-view thead tr`).append("<th scope='col' class='sticky-header'></th>");
        $.each(columns, function(index, header) {
            let slug = slugs[index];

            // Store label (without units) of each header in data-label attributes
            let label = columnsNoUnits[index];

            // Assigning data attribute for table column sorting
            let icon = ($.inArray(slug, order) >= 0 ? "-down" : ($.inArray("-"+slug, order) >= 0 ? "-up" : ""));
            let columnSorting = icon === "-down" ? "sort-asc" : icon === "-up" ? "sort-desc" : "none";
            let columnOrdering = `<a href='' data-slug='${slug}' data-label='${label}'><span>${header}</span><span data-sort='${columnSorting}' class='column_ordering fas fa-sort${icon}'></span></a>`;

            $(`${tab} .op-data-table-view thead tr`).append(`<th id='${slug} 'scope='col' class='sticky-header'><div>${columnOrdering}</div></th>`);
        });

        o_browse.initResizableColumn(tab);
    },

    initResizableColumn: function(tab) {
        $(`${tab} .op-data-table th div`).resizable({
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
                listHtml += ` <i class="${pillSortUpArrow}"></i>`;
            } else {
                listHtml += "<span class='flip-sort' title='Change to descending sort'>";
                listHtml += label;
                listHtml += ` <i class="${pillSortDownArrow}"></i>`;
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

    // number of images that can be fit in current window size
    getLimit: function(view) {
        // default the function to use to be the one in o_browse because there is not one available in o_search
        let galleryBoundingRect = opus.getViewNamespace(view).galleryBoundingRect;
        return (galleryBoundingRect.x * galleryBoundingRect.yCeil);
    },

    getDataURL: function(view, startObs, customizedLimitNum=undefined) {
        let base_url = "/opus/__api/dataimages.json?";
        let hashString = o_hash.getHash();

        //TODO: we should be able to combine these url tweaker functions into a single function, perhaps in hash.js
        let url = hashString + '&reqno=' + opus.lastLoadDataRequestNo[view];
        url = o_browse.updateViewInUrl(view, url);
        url = base_url + o_browse.updateStartobsInUrl(view, url, startObs);

        // need to add limit - getting twice as much so that the prefetch is done in one get instead of two.
        let limitNum = customizedLimitNum === undefined ? o_browse.getLimit(view) * 2 : customizedLimitNum;

        url += `&limit=${limitNum}`;

        return url;
    },

    // check the cache of both rendered elements and variable observationData; remove 'far away' observations
    // from cache to avoid buildup of too much data in the browser which slows things down
    // Two functions; one to delete single elements, just a tool for the main one, manageObservationCache, to loop.
    // NOTE: There is a problem here in that it only removes the same number of observations as we are trying
    // to add. If the browser has shrunk, the cache will maintain its larger size forever, or at least until
    // a forced flush is done by page reload or large slider motion or search change or hitting the browse tab button.
    manageObservationCache: function(count, append, view) {
        let tab = opus.getViewTab(view);
        let viewNamespace = opus.getViewNamespace(view);
        let galleryObsElem = $(`${tab} .gallery [data-obs]`);
        let tableObsElem = $(`${tab} .op-data-table-view [data-obs]`);

        if (galleryObsElem.length === 0) {
            // this only happens when there are no elements rendered, so why bother...
            // probably don't need to check both, but why not...
            return;
        }

        let lastIndex = galleryObsElem.last().index();
        let totalCachedObservations = lastIndex + 1;
        if (totalCachedObservations + count > viewNamespace.maxCachedObservations) {
            // if we are appending, remove from the top
            count = Math.min(count, totalCachedObservations);
            if (append) {
                // this is theoretically the faster way to delete lots of data, as jquery selector eval is slow
                for (let index = 0; index < count ; index++) {
                    o_browse.deleteCachedObservation(galleryObsElem, tableObsElem, index, viewNamespace);
                }
            } else {
                let deleteTo = totalCachedObservations - count;
                for (let index = lastIndex; index >= deleteTo; index--) {
                    o_browse.deleteCachedObservation(galleryObsElem, tableObsElem, index, viewNamespace);
                }
            }
        }
    },

    deleteCachedObservation: function(galleryObsElem, tableObsElem, index, viewNamespace) {
        // don't delete the metadata if the observation is in the cart
        let delOpusId = galleryObsElem.eq(index).data("id");
        if ($("#galleryView").hasClass("show")) {
            if (delOpusId === $("#galleryViewContents .op-cart-toggle").data("id")) {
                o_browse.hideGalleryViewModal();
            }
        }
        delete viewNamespace.observationData[delOpusId];
        galleryObsElem.eq(index).remove();
        tableObsElem.eq(index).remove();
    },

    isGalleryView: function(view) {
        let browse = o_browse.getBrowseView(view);
        return opus.prefs[browse] === "gallery";
    },

    getBrowseView: function(view) {
        view = (view === undefined ? opus.prefs.view : view);
        return (view === "cart" ? "cart_browse" : "browse");
    },

    // return the infiniteScroll container class for either gallery or table view
    getScrollContainerClass: function(view) {
        return (o_browse.isGalleryView(view) ? ".op-gallery-view" : ".op-data-table-view");
    },

    getStartObsLabel: function(view) {
        view = (view === undefined ? opus.prefs.view : view);
        return (view === "cart" ? "cart_startobs" : "startobs");
    },

    // Instantiate infiniteScroll
    initInfiniteScroll: function(view, selector) {
        let tab = `#${view}`;
        let startObsLabel = o_browse.getStartObsLabel(view);
        let viewNamespace = opus.getViewNamespace(view);

        if (!$(selector).data("infiniteScroll")) {
            $(selector).infiniteScroll({
                path: function() {
                    let obsNum = Math.max(opus.prefs[startObsLabel], 1);
                    let customizedLimitNum;
                    let lastObs = $(`${tab} .op-thumbnail-container`).last().data("obs");
                    let firstCachedObs = $(`${tab} .op-thumbnail-container`).first().data("obs");

                    // need to calc here due to race condition; values needed for url getLimit size
                    viewNamespace.galleryBoundingRect = o_browse.countGalleryImages(view);
                    viewNamespace.infiniteScrollLoadInProgress = true;
                    let galleryBoundingRect = viewNamespace.galleryBoundingRect;
                    // When loading a pasted URL in table view with a startObs not aligned with current
                    // browser size, the first cached obs won't be aligned with browser size. We calculate
                    // the alignedCachedFirstObs and use it as the startObs in the path for infiniteScroll
                    // to load previous page, so that when load prev page is triggered, all rendered obs will
                    // be aligned with the browser size.
                    let alignedCachedFirstObs =  (o_utils.floor((firstCachedObs - 1)/
                                                  galleryBoundingRect.x) * galleryBoundingRect.x + 1);
                    let extraObsToMatchRowBoundary = (firstCachedObs - 1) % galleryBoundingRect.x;

                    let infiniteScrollData = $(selector).data("infiniteScroll");
                    if (infiniteScrollData !== undefined && infiniteScrollData.options.loadPrevPage === true) {
                        // Direction: scroll up, we prefetch 1 * o_browse.getLimit() items
                        if (obsNum !== 1) {
                            // prefetch o_browse.getLimit() items ahead of firstCachedObs, update the startObs to be passed into url
                            obsNum = Math.max(alignedCachedFirstObs - o_browse.getLimit(view), 1);

                            // If obsNum to be passed into api url is 1, we will pass firstCachedObs - 1 as limit
                            // else we'll pass in o_browse.getLimit() as limit
                            customizedLimitNum = (obsNum === 1 ?  alignedCachedFirstObs - 1 + extraObsToMatchRowBoundary
                                                  : o_browse.getLimit(view) + extraObsToMatchRowBoundary);

                            // Update the obsNum in infiniteScroll instances with firstCachedObs
                            // This will be used to set the scrollbar position later
                            alignedCachedFirstObs = Math.max(alignedCachedFirstObs, 1);
                            if (infiniteScrollData) {
                                $(`${tab} .op-gallery-view`).infiniteScroll({"sliderObsNum": alignedCachedFirstObs});
                                $(`${tab} .op-data-table-view`).infiniteScroll({"sliderObsNum": firstCachedObs});
                                opus.prefs[startObsLabel] = o_browse.isGalleryView() ? alignedCachedFirstObs : firstCachedObs;
                            }
                        } else {
                            customizedLimitNum = 0;
                        }
                    } else {
                        // Direction: scroll down, we prefetch 1 * o_browse.getLimit() items (symmetric to scroll up)
                        // NOTE: we can change the number of prefetch items by changing customizedLimitNum
                        // start from the last observation drawn; if none yet drawn, start from opus.prefs.startobs
                        obsNum = (lastObs !== undefined ? lastObs + 1 : obsNum);
                        customizedLimitNum = o_browse.getLimit(view);

                        // We will update the obsNum in InfiniteScroll instances with the startObs values
                        // right before infiniteScroll load event is triggered. This will be used to properly
                        // set the scrollbar and slider location after new data is loaded.
                        let scrollbarObsNum = opus.prefs[startObsLabel];

                        // Update the obsNum in infiniteScroll instances with the first obsNum of the row above current last page
                        // This will be used to set the scrollbar position later
                        scrollbarObsNum = Math.max(scrollbarObsNum, 1);
                        if (infiniteScrollData && obsNum <= viewNamespace.totalObsCount) {
                            $(`${tab} .op-gallery-view`).infiniteScroll({"sliderObsNum": scrollbarObsNum});
                            $(`${tab} .op-data-table-view`).infiniteScroll({"sliderObsNum": scrollbarObsNum});
                            opus.prefs[startObsLabel] = scrollbarObsNum;
                        }
                    }

                    // If there is no Cached data at all, loadData function will be called to
                    // render initial data, during this time, we want to make sure infintieScroll
                    // doesn't render any data to avoid duplicated cached obs.
                    if (viewNamespace.loadDataInProgress || ($(`${tab} .op-data-table tbody tr`).length === 0 &&
                        $(`${tab} .gallery .op-thumbnail-container`).length === 0)) {
                        customizedLimitNum = 0;
                    }

                    // if totalObsCount is not yet defined, we still need to init the infinite scroll...
                    //if (viewNamespace.totalObsCount === undefined || obsNum <= viewNamespace.totalObsCount) {
                        let path = o_browse.getDataURL(view, obsNum, customizedLimitNum);
                        return path;
                    //}
                    // returning no value indicates end of infinite scroll... but apparently doesn't work at moment.
                    // NOTE: leaving this commented out code in place with the hope that we will find a solution.
                    //return null;
                },
                responseType: "text",
                status: `${tab} .op-page-load-status`,
                elementScroll: true,
                history: false,
                // threshold point for scroll down
                scrollThreshold: 200,
                checkLastPage: false,
                loadPrevPage: false,
                // store the most top left obsNum in gallery or the most top obsNum in table
                obsNum: 1,
                debug: false,
            });

            $(selector).on("request.infiniteScroll", function(event, path) {
                // Remove spinner when infiniteScroll reaches to both ends
                let contentsView = o_browse.getScrollContainerClass(view);
                let viewNamespace = opus.getViewNamespace(view);
                let infiniteScrollData = $(`${tab} ${contentsView}`).data("infiniteScroll");
                let firstObs = $(`${tab} .op-thumbnail-container`).first().data("obs");
                let lastObs = $(`${tab} .op-thumbnail-container`).last().data("obs");

                if (infiniteScrollData.options.loadPrevPage === true) {
                    if (firstObs === 1) {
                        $(".infinite-scroll-request").hide();
                    }
                } else {
                    if (lastObs === viewNamespace.totalObsCount) {
                        $(".infinite-scroll-request").hide();
                    }
                }
            });

            let eventListenerWithView = function(event, response, path) {
                o_browse.infiniteScrollLoadEventListener(event, response, path, view);
            };
            $(selector).on("load.infiniteScroll", eventListenerWithView);
        }
    },

    loadData: function(view, startObs, customizedLimitNum=undefined) {
        /**
         * Fetch initial data when reloading page, changing sort order,
         * or switching to browse tab after search is changed.
         */
        let tab = opus.getViewTab(view);
        let startObsLabel = o_browse.getStartObsLabel(view);
        let contentsView = o_browse.getScrollContainerClass(view);
        let viewNamespace = opus.getViewNamespace(view);
        let galleryBoundingRect = viewNamespace.galleryBoundingRect;

        let galleryInfiniteScroll = $(`${tab} .op-gallery-view`).data("infiniteScroll");
        let tableInfiniteScroll = $(`${tab} .op-data-table-view`).data("infiniteScroll");

        startObs = (startObs === undefined ? opus.prefs[startObsLabel] : startObs);
        // Make sure startObs is adjusted based on correct row boundary.
        // This will make sure, in gallery view, when URL with a startobs not aligned with current
        // browser size is pasted, that startobs will be adjusted to a new value which is aligned
        // with the browser size.
        startObs = (o_browse.isGalleryView() ? (o_utils.floor((startObs - 1)/galleryBoundingRect.x) *
                    galleryBoundingRect.x + 1) : startObs);

        if (!viewNamespace.reloadObservationData) {
            // if the request is a block far away from current page cache, flush the cache and start over
            let elem = $(`${tab} [data-obs="${startObs}"]`);
            let lastObs = $(`${tab} [data-obs]`).last().data("obs");
            let firstObs = $(`${tab} [data-obs]`).first().data("obs");

            // if the startObs is not already rendered and is obviously not contiguous, clear the cache and start over
            // ... but only if this is not an ampty results queue..
            if (viewNamespace.totalObsCount !== 0) {
                if (lastObs === undefined || firstObs === undefined || elem.length === 0 ||
                    (startObs > lastObs + 1) || (startObs < firstObs - 1)) {
                    viewNamespace.reloadObservationData = true;
                } else {
                    // wait! is this page already drawn?
                    // if startObs drawn, move the slider to that line, fetch if need be after
                    if (startObs >= firstObs && startObs <= lastObs) {
                        // may need to do a prefetch here...
                        if (galleryInfiniteScroll && tableInfiniteScroll) {
                            startObs = $(`${tab} ${contentsView}`).data("infiniteScroll").options.sliderObsNum;
                        }
                        o_browse.setScrollbarPosition(startObs, startObs, view);
                        o_browse.hidePageLoaderSpinner();
                        return;
                    }
                }
            } else {
                o_browse.hidePageLoaderSpinner();
                return;
            }
        }

        o_browse.showPageLoaderSpinner();
        // Note: when browse page is refreshed, startObs passed in (from activateBrowseTab) will start from 1
        let url = o_browse.getDataURL(view, startObs, customizedLimitNum);
        viewNamespace.loadDataInProgress = true;
        // metadata; used for both table and gallery
        $.getJSON(url, function(data) {
            if (data.reqno < opus.lastLoadDataRequestNo[view]) {
                // make sure to remove spinner before return
                o_browse.hidePageLoaderSpinner();
                return;
            }

            o_browse.initTable(tab, data.columns, data.columns_no_units);

            $(`${tab} .op-gallery-view`).scrollTop(0);
            $(`${tab} .op-data-table-view`).scrollTop(0);

            // Because we redraw from the beginning on user inputted page, we need to remove previous drawn thumb-pages
            viewNamespace.observationData = {};
            $(`${tab} .gallery`).empty();
            o_browse.hideGalleryViewModal();
            o_browse.renderGalleryAndTable(data, this.url, view);

            if (o_browse.metadataDetailOpusId != "") {
                o_browse.metadataboxHtml(o_browse.metadataDetailOpusId, view);
            }
            o_browse.updateSortOrder(data);

            viewNamespace.reloadObservationData = false;
            viewNamespace.loadDataInProgress = false;

            // When pasting a URL, prefetch some data from previous page so that scrollbar will
            // stay in the middle. This step has to be performed after loadData is done (loadDataInProgress
            // is set to false).
            let firstObs = $(`${tab} [data-obs]`).first().data("obs");
            if (startObs === firstObs && firstObs !== 1) {
                $(`${tab} ${contentsView}`).trigger("ps-scroll-up");
            }
        });
    },

    infiniteScrollLoadEventListener: function(event, response, path, view) {
        let viewNamespace = opus.getViewNamespace(view);
        o_browse.showPageLoaderSpinner();
        let data = JSON.parse(response);

        let tab = opus.getViewTab(view);

        o_browse.renderGalleryAndTable(data, path, view);
        $(`${tab} .op-gallery-view`).infiniteScroll({"loadPrevPage": false});
        $(`${tab} .op-data-table-view`).infiniteScroll({"loadPrevPage": false});

        // Maybe we only care to do this if the modal is visible...  right now, just let it be.
        // Update to make prev button appear when prefetching previous page is done
        if (o_browse.metadataDetailOpusId !== "" &&
            !$("#galleryViewContents .op-prev").data("id") &&
            $("#galleryViewContents .op-prev").hasClass("op-button-disabled")) {
            let prev = $(`${tab} tr[data-id=${o_browse.metadataDetailOpusId}]`).prev("tr");
            prev = (prev.data("id") ? prev.data("id") : "");

            $("#galleryViewContents .op-prev").data("id", prev);
            $("#galleryViewContents .op-prev").toggleClass("op-button-disabled", (prev === ""));
        }

        // Update to make next button appear when prefetching next page is done
        if (o_browse.metadataDetailOpusId !== "" &&
            !$("#galleryViewContents .op-next").data("id") &&
            $("#galleryViewContents .op-next").hasClass("op-button-disabled")) {
            let next = $(`${tab} tr[data-id=${o_browse.metadataDetailOpusId}]`).next("tr");
            next = (next.data("id") ? next.data("id") : "");

            $("#galleryViewContents .op-next").data("id", next);
            $("#galleryViewContents .op-next").toggleClass("op-button-disabled", (next === ""));
        }

        // if left/right arrow are disabled, make them clickable again
        $("#galleryViewContents").removeClass("op-disabled");
        viewNamespace.infiniteScrollLoadInProgress = false;

        if (data.count !== 0) {
            // Realign DOMS after all new obs are rendered. This will make sure all DOMs are aligned
            // when browser is resized in the middle of infiniteScroll load.
            o_browse.updateSliderHandle(view, false, true);
        }
    },

    activateBrowseTab: function() {
        opus.getViewNamespace().galleryBoundingRect = o_browse.countGalleryImages();
        // reset range select
        o_browse.undoRangeSelect();

        o_browse.showPageLoaderSpinner();
        o_browse.updateBrowseNav();
        o_browse.renderSelectMetadata();   // just do this in background so there's no delay when we want it...
        // Call the following two functions to make sure the height of .op-gallery-view and .op-data-table-view
        // are set. This will prevent the height of data obs containers from jumping when the page is loaded,
        // and avoid the wrong calculation of container position in setScrollbarPosition.
        o_browse.adjustBrowseHeight();
        o_browse.adjustTableSize();

        o_browse.loadData(opus.prefs.view);
    },

    countTableRows: function(view) {
        let tab = opus.getViewTab(view);
        let height = o_browse.calculateGalleryHeight(view);
        let trCountFloor = 1;

        if ($(`${tab} .op-data-table tbody tr[data-obs]`).length > 0) {
            trCountFloor = o_utils.floor((height-$("th").outerHeight()) /
                                         $(`${tab} .op-data-table tbody tr[data-obs]`).outerHeight());
        }
        opus.getViewNamespace(view).galleryBoundingRect.trFloor = trCountFloor;
        return trCountFloor;
    },

    countGalleryImages: function(view) {
        let tab = opus.getViewTab(view);
        let viewNamespace = opus.getViewNamespace(view);
        let width = o_browse.calculateGalleryWidth(view);
        let height = o_browse.calculateGalleryHeight(view);

        let trCountFloor = viewNamespace.galleryBoundingRect.trFloor;
        if (!o_browse.isGalleryView(view) && $(`${tab} .op-data-table tbody tr[data-obs]`).length > 0) {
            trCountFloor = o_utils.floor((height-$("th").outerHeight()) /
                                         $(`${tab} .op-data-table tbody tr[data-obs]`).outerHeight());
        }

        let xCount = o_utils.floor(width/o_browse.imageSize);
        // This is the total number of rows that are at least partially visible
        let yCountCeil = o_utils.ceil(height/o_browse.imageSize);
        // This is the total number of rows that are completely visible
        let yCountFloor = o_utils.floor(height/o_browse.imageSize);
        // This is the total number of rows that are visible as much as we think is visually useful
        let yCountPartial = o_utils.floor((height + o_browse.imageSize*(1-o_browse.galleryImageViewableFraction)) /
                                          o_browse.imageSize);

        // update the number of cached observations based on screen size
        // for now, only bother when we update the browse tab...
        // rounding because the factor value can be a FP number.
        viewNamespace.maxCachedObservations = Math.round(xCount * yCountCeil * viewNamespace.cachedObservationFactor);

        return {"x": xCount,
                "yCeil": yCountCeil, "yFloor": yCountFloor, "yPartial": yCountPartial,
                "trFloor": trCountFloor};
    },


    // calculate the height of the gallery by removing all the non-gallery contaniner elements
    calculateGalleryHeight: function(view) {
        let tab = opus.getViewTab(view);
        let footerHeight = $(".app-footer").outerHeight();
        let mainNavHeight = $("#op-main-nav").outerHeight();
        let navbarHeight = $(`${tab} .panel-heading`).outerHeight();
        let totalNonGalleryHeight = footerHeight + mainNavHeight + navbarHeight;
        return $(window).height()-totalNonGalleryHeight;
    },

    calculateGalleryWidth: function(view) {
        let tab = opus.getViewTab(view);
        let width = $(`${tab} .gallery-contents`).width();
        if (width <= 0) {
            width = $(window).width();
            if (tab === "#cart") {
                let leftPanelWidth = parseInt($(".cart_details").css("min-width"));
                width -= leftPanelWidth;
            }
        } else {
            // We don't know why, but the .gallery-contents container is always
            // a little bit too wide, but it's consistent between browsers.
            // It's like there's a hidden margin that the browser is using to
            // compute reflow. This hack fixes that.
            width -= (tab === "#cart" ? 4 : 6);
        }
        return width;
    },

    adjustBrowseHeight: function(browserResized=false, isDOMChanged=false) {
        let tab = opus.getViewTab();
        let view = opus.prefs.view;
        let containerHeight = o_browse.calculateGalleryHeight();
        $(`${tab} .gallery-contents`).height(containerHeight);
        $(`${tab} .gallery-contents .op-gallery-view`).height(containerHeight);

        let viewNamespace = opus.getViewNamespace();
        viewNamespace.galleryScrollbar.update();
        viewNamespace.galleryBoundingRect = o_browse.countGalleryImages();

        // make sure slider is updated when window is resized
        o_browse.updateSliderHandle(view, browserResized, isDOMChanged);
    },

    adjustTableSize: function() {
        let tab = opus.getViewTab();
        let containerWidth = $(`${tab} .gallery-contents`).width();
        let containerHeight = $(`${tab} .gallery-contents`).height();
        $(`${tab} .op-data-table-view`).width(containerWidth);
        $(`${tab} .op-data-table-view`).height(containerHeight);
        opus.getViewNamespace().tableScrollbar.update();
    },

    adjustBrowseDialogPS: function() {
        let containerHeight = $("#galleryViewContents .op-metadata-details").height();
        let browseDialogHeight = $("#galleryViewContents .op-metadata-details .contents").height();

        if (o_browse.modalScrollbar) {
            if (containerHeight > browseDialogHeight) {
                if (!$("#galleryViewContents .op-metadata-details .ps__rail-y").hasClass("hide_ps__rail-y")) {
                    $("#galleryViewContents .op-metadata-details .ps__rail-y").addClass("hide_ps__rail-y");
                    o_browse.modalScrollbar.settings.suppressScrollY = true;
                }
            } else {
                $("#galleryViewContents .op-metadata-details .ps__rail-y").removeClass("hide_ps__rail-y");
                o_browse.modalScrollbar.settings.suppressScrollY = false;
            }
            o_browse.modalScrollbar.update();
        }
    },

    cartButtonInfo: function(status) {
        let tab = opus.getViewTab();
        let browse_icon = "fas fa-cart-plus";
        let browse_title = "Add to cart";
        let browse_rangeTitle = "add range";
        let cart_icon = "fas fa-undo";
        let cart_title = "Restore from recycle bin";
        let cart_rangeTitle = "restore range from recycle bin";
        if (status != "remove") {
            browse_icon = "far fa-trash-alt";
            browse_title = "Remove from cart";
            browse_rangeTitle = "remove range";
            cart_icon = "fas fa-recycle";
            cart_title = "Move to recycle bin";
            cart_rangeTitle = "move range to recycle bin";
        }
        return  {"#browse": {"icon":browse_icon, "title":browse_title, "rangeTitle":browse_rangeTitle},
                 "#cart":   {"icon":cart_icon,   "title":cart_title,   "rangeTitle":cart_rangeTitle}};
    },

    updateCartIcon: function(opusId, action) {
        let buttonInfo = o_browse.cartButtonInfo(action);
        let selector = `.op-thumb-overlay [data-id=${opusId}] [data-icon="cart"]`;
        $.each(["#browse", "#cart"], function(index, tab) {
            $(`${tab} ${selector}`).html(`<i class="${buttonInfo[tab].icon} fa-xs"></i>`);
            $(`${tab} ${selector}`).prop("title", buttonInfo[tab].title);
        });

        let tab = opus.getViewTab();
        let modalCartSelector = `#galleryViewContents .bottom .op-cart-toggle[data-id=${opusId}]`;
        if ($("#galleryView").is(":visible") && $(modalCartSelector).length > 0) {
            $(modalCartSelector).html(`<i class="${buttonInfo[tab].icon} fa-2x"></i>`);
            $(modalCartSelector).prop("title", `${buttonInfo[tab].title} (spacebar)`);
        }
    },

    getNextPrevHandles: function(opusId, view) {
        let tab = opus.getViewTab(view);
        let idArray = $(`${tab} .op-thumbnail-container[data-obs]`).map(function() {
            return $(this).data("id");
        });
        let next = $.inArray(opusId, idArray) + 1;
        next = (next < idArray.length ? idArray[next] : "");

        let prev = $.inArray(opusId, idArray) - 1;
        prev = (prev < 0 ? "" : idArray[prev]);

        return {"next": next, "prev": prev};
    },

    metadataboxHtml: function(opusId, view) {
        let viewNamespace = opus.getViewNamespace(view);
        let tab = opus.getViewTab();
        o_browse.metadataDetailOpusId = opusId;

        // list columns + values
        let html = "<dl>";
        $.each(opus.colLabels, function(index, columnLabel) {
            if (opusId === "" || viewNamespace.observationData[opusId] === undefined || viewNamespace.observationData[opusId][index] === undefined) {
                opus.logError(`metadataboxHtml: in each, observationData may be out of sync with colLabels; opusId = ${opusId}, colLabels = ${opus.colLabels}`);
            } else {
                let value = viewNamespace.observationData[opusId][index];
                html += `<dt>${columnLabel}:</dt><dd>${value}</dd>`;
            }
        });
        html += "</dl>";
        $("#galleryViewContents .contents").html(html);

        let nextPrevHandles = o_browse.getNextPrevHandles(opusId, view);
        let status = o_cart.isIn(opusId) ? "" : "remove";
        let buttonInfo = o_browse.cartButtonInfo(status);

        // prev/next buttons - put this in galleryView html...
        html = `<div class="col"><a href="#" class="op-cart-toggle" data-id="${opusId}" title="${buttonInfo[tab].title} (spacebar)"><i class="${buttonInfo[tab].icon} fa-2x float-left"></i></a></div>`;
        html += `<div class="col text-center op-obs-direction">`;
        let opPrevDisabled = (nextPrevHandles.prev == "" ? "op-button-disabled" : "");
        let opNextDisabled = (nextPrevHandles.next == "" ? "op-button-disabled" : "");
        html += `<a href="#" class="op-prev text-center ${opPrevDisabled}" data-id="${nextPrevHandles.prev}" title="Previous image: ${nextPrevHandles.prev} (left arrow key)"><i class="far fa-arrow-alt-circle-left fa-2x"></i></a>`;
        html += `<a href="#" class="op-next ${opNextDisabled}" data-id="${nextPrevHandles.next}" title="Next image: ${nextPrevHandles.next} (right arrow key)"><i class="far fa-arrow-alt-circle-right fa-2x"></i></a>`;
        html += `</div>`;

        // mini-menu like the hamburger on the observation/gallery page
        html += `<div class="col"><a href="#" class="menu pr-3 float-right" data-toggle="dropdown" role="button" data-id="${opusId}" title="More options"><i class="fas fa-bars fa-2x"></i></a></div>`;
        $("#galleryViewContents .bottom").html(html);
    },

    updateGalleryView: function(opusId) {
        let tab = opus.getViewTab();
        $(tab).find(".op-modal-show").removeClass("op-modal-show");
        $(tab).find(`[data-id='${opusId}'] div.op-modal-overlay`).addClass("op-modal-show");
        $(tab).find(`tr[data-id='${opusId}']`).addClass("op-modal-show");
        // if the observation is in the recycle bin, move the icon over a bit so there is not conflict w/the binoculars
        $(tab).find(`[data-id='${opusId}'] div.op-recycle-overlay`).addClass("op-modal-show");

        let imageURL = $(tab).find(`[data-id='${opusId}'] > a.thumbnail`).data("image");
        o_browse.updateMetaGalleryView(opusId, imageURL);
    },


    updateMetaGalleryView: function(opusId, imageURL) {
        let tab = opus.getViewTab();
        let element = (o_browse.isGalleryView() ? $(`${tab} .op-thumbnail-container[data-id=${opusId}]`) : $(`${tab} tr[data-id=${opusId}]`));
        let obsNum = $(element).data("obs");
        let title = `#${obsNum}: ${opusId}\r\nClick for full-size image`;

        $("#galleryViewContents .left").html(`<a href="${imageURL}" target="_blank"><img src="${imageURL}" title="${title}" class="op-slideshow-image-preview"/></a>`);
        o_browse.metadataboxHtml(opusId);
    },

    clearObservationData: function(leaveStartObs) {
        if (!leaveStartObs) {
            // Normally when we delete all the data we want to force a return to the top because
            // we don't know what data is going to be loaded. But in some circumstances
            // (like updating metadata columns) we know we're going to reload exactly the same
            // data so we can keep our place.
            opus.prefs.startobs = 1; // reset startobs to 1 when data is flushed
            opus.prefs.cart_startobs = 1;
            $(`.op-gallery-view`).infiniteScroll({"scrollbarObsNum": 1});
            $(`.op-gallery-view`).infiniteScroll({"sliderObsNum": 1});
            $(`.op-data-table-view`).infiniteScroll({"scrollbarObsNum": 1});
            $(`.op-data-table-view`).infiniteScroll({"sliderObsNum": 1});
        }
        o_cart.reloadObservationData = true;  // forces redraw of cart tab
        o_cart.observationData = {};
        o_browse.reloadObservationData = true;  // forces redraw of browse tab
        o_browse.observationData = {};
    },

    clearBrowseObservationDataAndEraseDOM: function(leaveStartObs=false) {
        if (!leaveStartObs) {
            opus.prefs.startobs = 1; // reset startobs to 1 when data is flushed
            $("#browse .op-gallery-view").infiniteScroll({"scrollbarObsNum": 1});
            $("#browse .op-gallery-view").infiniteScroll({"sliderObsNum": 1});
            $("#browse .op-data-table-view").infiniteScroll({"scrollbarObsNum": 1});
            $("#browse .op-data-table-view").infiniteScroll({"sliderObsNum": 1});
        }
        o_browse.reloadObservationData = true;  // forces redraw of browse tab
        o_browse.observationData = {};
        // Just so the user doesn't see old data lying around while waiting for a reload
        // XXX For some reason having these lines here makes data sometimes double-load
        // when the scrollbar isn't at the top, so for now this is disabled and the
        // user might occasionally see old data briefly while the new stuff loads.
        $("#browse .gallery").empty();
        $("#browse .op-data-table tbody").empty();
    },
};
