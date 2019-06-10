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
    modalScrollbar: new PerfectScrollbar("#galleryViewContents .metadata", {
        minScrollbarLength: opus.minimumPSLength
    }),

    // these vars are common w/o_cart
    reloadObservationData: true, // start over by reloading all data
    observationData: {},  // holds observation column data
    totalObsCount: undefined,
    cachedObservationFactor: 4,     // this is the factor times the screen size to determine cache size
    maxCachedObservations: 1000,    // max number of observations to store in cache, will be updated based on screen size
    galleryBoundingRect: {'x': 0, 'y': 0},

    // unique to o_browse
    gallerySliderStep: 10,
    imageSize: 100,     // default

    metadataDetailOpusId: "",
    metadataSelectorDrawn: false,

    tempHash: "",
    onRenderData: false,
    fading: false,  // used to prevent additional clicks until the fade animation complete
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
                        o_browse.updateSliderHandle();
                    }
                }
            }
        });

        $("#op-metadata-selector").modal({
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
        $(".gallery").on("click", ".thumbnail", function(e) {
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
            let startElem = $(`${tab} .thumb.gallery`).find(".selected");

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

        $(".op-data-table").on("click", "td:not(:first-child)", function(e) {
            let opusId = $(this).parent().data("id");
            e.preventDefault();
            o_browse.hideMenu();

            let tab = opus.getViewTab();
            let startElem = $(`${tab} .thumb.gallery`).find(".selected");

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
                o_browse.showMetadataDetailModal(opusId);
            }
        });

        // thumbnail overlay tools
        $('.gallery, .op-data-table').on("click", ".op-tools a", function(e) {
            //snipe the id off of the image..
            let opusId = $(this).parent().data("id");

            switch ($(this).data("icon")) {
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
            return false;
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
            $(".op-page-loading-status > .loader").show();
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
            $(".op-page-loading-status > .loader").show();
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
            $(".op-page-loading-status > .loader").show();
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
                    let startElem = $(tab).find(".selected");
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
                    break;
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
                o_browse.hideGalleryViewModal();
                $("#op-metadata-selector").modal('hide');
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
        let startElem = $(e.delegateTarget).find(".selected");
        if (startElem.length == 0) {
            o_browse.startRangeSelect(opusId);
        } else {
            let fromOpusId = $(startElem).data("id");
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
            headers.attr("class", defaultTableSortArrow);
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
        let element = (o_browse.isGalleryView() ? $(`${tab} .thumbnail-container[data-id=${opusId}]`) : $(`${tab} tr[data-id=${opusId}]`));
        let obsNum = $(element).data("obs");

        let checkView = (direction === "next" ? obsNum <= maxObs : obsNum > 0);

        if (checkView) {
            // make sure the current element that the modal is displaying is viewable
            if (!element.isOnScreen($(`${tab} .gallery-contents`))) {
                let galleryBoundingRect = opus.getViewNamespace().galleryBoundingRect;

                let startObs = $(`${tab} ${contentsView}`).data("infiniteScroll").options.obsNum;

                // if the binoculars have scrolled up, then reset the screen to the top;
                // if the binoculars have scrolled down off the screen, then scroll up just until the they are visible in bottom row
                if (obsNum > startObs) {    // the binoculars have scrolled off bottom
                    if (o_browse.isGalleryView()) {
                        obsNum = Math.max(obsNum - (galleryBoundingRect.x * (galleryBoundingRect.y - 1)), 1);
                    } else {
                        obsNum = Math.max(obsNum - galleryBoundingRect.tr + 1, 1);
                    }
                }
                o_browse.onUpdateSlider(obsNum);
            }
        }
    },

    setScrollbarPosition: function(obsNum, view) {
        let tab = opus.getViewTab(view);
        let galleryTarget = $(`${tab} .thumbnail-container[data-obs="${obsNum}"]`);
        let tableTarget = $(`${tab} .op-data-table tbody tr[data-obs='${obsNum}']`);

        // Make sure obsNum is rendered before setting scrollbar position
        if (galleryTarget.length && tableTarget.length) {
            let galleryTargetTopPosition = galleryTarget.offset().top;
            let galleryContainerTopPosition = $(`${tab} .gallery-contents .op-gallery-view`).offset().top;
            let galleryScrollbarPosition = $(`${tab} .gallery-contents .op-gallery-view`).scrollTop();

            let galleryTargetFinalPosition = galleryTargetTopPosition - galleryContainerTopPosition + galleryScrollbarPosition;
            $(`${tab} .gallery-contents .op-gallery-view`).scrollTop(galleryTargetFinalPosition);

            // make sure it's scrolled to the correct position in table view
            let tableTargetTopPosition = tableTarget.offset().top;
            let tableContainerTopPosition = $(`${tab} .op-data-table-view`).offset().top;
            let tableScrollbarPosition = $(`${tab} .op-data-table-view`).scrollTop();
            let tableHeaderHeight = $(`${tab} .op-data-table thead th`).outerHeight();

            let tableTargetFinalPosition = (tableTargetTopPosition - tableContainerTopPosition +
                                            tableScrollbarPosition - tableHeaderHeight);
            $(`${tab} .op-data-table-view`).scrollTop(tableTargetFinalPosition);
        }
    },

    // called when the slider is moved...
    onUpdateSliderHandle: function(value) {
        value = (value == undefined? 1 : value);
        $("#browse .op-observation-number").html(o_utils.addCommas(value));
    },

    // This function will be called when we scroll the slide to a target value
    onUpdateSlider: function(value) {
        let view = opus.prefs.view;
        let tab = opus.getViewTab();
        let elem = $(`${tab} .thumbnail-container[data-obs="${value}"]`);
        let startObsLabel = o_browse.getStartObsLabel();
        let viewNamespace = opus.getViewNamespace();

        // Update obsNum in infiniteScroll instances.
        // This obsNum is the first item in current page
        // (will be used to set scrollbar position in renderGalleryAndTable).
        $(`${tab} .op-gallery-view`).infiniteScroll({"obsNum": value});
        $(`${tab} .op-data-table-view`).infiniteScroll({"obsNum": value});
        opus.prefs[startObsLabel] = value;

        if (elem.length > 0) {
            o_browse.setScrollbarPosition(value);
        } else {
            // When scrolling on slider and loadData is called, we will fetch 3 * getLimit items
            // (one current page, one next page, and one previous page) starting from obsNum.
            // obsNum will be the very first obs for data rendering this time
            let obsNum = Math.max(value - o_browse.getLimit(), 1);

            // If obsNum is 1, previous page will have value - 1 items, so we render value - 1 + 2 * o_browse.getLimit() items
            // else we render 2 * o_browse.getLimit() items.
            let customizedLimitNum = obsNum === 1 ? value - 1 + 2 * o_browse.getLimit() : 3 * o_browse.getLimit();
            viewNamespace.reloadObservationData = true;
            o_browse.loadData(view, obsNum, customizedLimitNum);
        }
    },

    // find the first displayed observation index & id in the upper left corner
    updateSliderHandle: function(browserResized=false) {
        let tab = opus.getViewTab();
        let selector = (o_browse.isGalleryView() ?
                        `${tab} .gallery .thumbnail-container` :
                        `${tab} .op-data-table tbody tr`);
        let startObsLabel = o_browse.getStartObsLabel();

        if ($(selector).length > 0) {
            $(`${tab} .op-slider-nav`).removeClass("op-button-disabled");
            let viewNamespace = opus.getViewNamespace();
            let galleryBoundingRect = viewNamespace.galleryBoundingRect;

            // this will get the top left obsNum for gallery view or the top obsNum for table view
            let firstCachedObs = $(selector).first().data("obs");
            let firstCachedObsTop = $(selector).first().offset().top;
            let calculatedFirstObs = (o_utils.floor((firstCachedObs - 1)/galleryBoundingRect.x) *
                                      galleryBoundingRect.x + 1);
            // For gallery view, the topBoxBoundary is the top of .gallery-contents

            // For table view, we will set the topBoxBoundary to be the bottom of thead
            // (account for height of thead)
            let topBoxBoundary = (o_browse.isGalleryView() ?
                              $(`${tab} .gallery-contents`).offset().top :
                              $(`${tab} .gallery-contents`).offset().top + $(`${tab} .op-data-table thead th`).outerHeight());

            // table: obsNum = calculatedFirstObs + number of row
            // gallery: obsNum = calculatedFirstObs + number of row * number of obs in a row
            let obsNumDiff = (o_browse.isGalleryView() ?
                              Math.round((topBoxBoundary - firstCachedObsTop)/o_browse.imageSize) *
                              galleryBoundingRect.x :
                              Math.round((topBoxBoundary - firstCachedObsTop)/$(`${tab} tbody tr`).outerHeight()));

            let obsNum = obsNumDiff + calculatedFirstObs;
            if (browserResized) {
                // At this point of time, galleryBoundingRect is updated with new row size
                // from countGalleryImages in adjustBrowseHeight.
                let numToDelete = ((galleryBoundingRect.x - (firstCachedObs - 1) % galleryBoundingRect.x) %
                                   galleryBoundingRect.x);

                let galleryObsElem = $(`${tab} .gallery [data-obs]`);
                let tableObsElem = $(`${tab} .op-data-table-view [data-obs]`);
                // delete first "numToDelete" obs if row size is changed
                if (numToDelete !== 0) {
                    for (let count = 0; count < numToDelete; count++) {
                        o_browse.deleteCachedObservation(galleryObsElem, tableObsElem, count, viewNamespace);
                    }
                }
            }

            let dataResultCount = viewNamespace.totalObsCount;
            let firstObsInLastRow = (o_utils.floor((dataResultCount - 1)/galleryBoundingRect.x) *
                                galleryBoundingRect.x + 1);
            let maxSliderVal = firstObsInLastRow - galleryBoundingRect.x * (galleryBoundingRect.y - 1);

            // Update obsNum in both infiniteScroll instances.
            // Store the most top left obsNum in gallery for both infiniteScroll instances
            // (this will be used to updated slider obsNum).
            if (o_browse.isGalleryView()) {
                obsNum = (o_utils.floor((obsNum - 1)/galleryBoundingRect.x) *
                          galleryBoundingRect.x + 1);
            }

            if (maxSliderVal >= obsNum) {
                $(`${tab} .op-gallery-view`).infiniteScroll({"obsNum": obsNum});
                $(`${tab} .op-data-table-view`).infiniteScroll({"obsNum": obsNum});
                opus.prefs[startObsLabel] = obsNum;

                $(`${tab} .op-observation-number`).html(o_utils.addCommas(obsNum));
                $(`${tab} .op-slider-pointer`).css("width", `${o_utils.addCommas(maxSliderVal).length*0.7}em`);

                // just make the step size the number of the obserations across the page...
                // if the observations have not yet been rendered, leave the default, it will get changed later
                if (galleryBoundingRect.x > 0) {
                    o_browse.gallerySliderStep = galleryBoundingRect.x;
                }
                $("#op-observation-slider").slider({
                    "value": obsNum,
                    "step": o_browse.gallerySliderStep,
                    "max": maxSliderVal,
                });
            }
            // update startobs in url when scrolling
            o_hash.updateHash(true);
        } else {
            // disable the slider because there are no observations
            $(`${tab} .op-slider-nav`).addClass("op-button-disabled");
            $(`${tab} .op-slider-pointer`).css("width", "1ch");
            $(`${tab} .op-observation-number`).html("?");
        }
    },

    checkScroll: function() {
        // this will make sure ps-scroll-up is triggered to prefetch
        // previous data when scrollbar reaches to up scroll threshold point.
        let tab = opus.getViewTab();
        let contentsView = o_browse.getScrollContainerClass();
        if ($(`${tab} ${contentsView}`).scrollTop() < infiniteScrollUpThreshold) {
            $(`${tab} ${contentsView}`).trigger("ps-scroll-up");
        }
        o_browse.updateSliderHandle();
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
        let tab = opus.getViewTab();
        let selectedElem = $(tab).find(".selected");
        if (selectedElem.length != 0) {
            inCart = (o_cart.isIn($(selectedElem).data("id")) ? "" : "in");
        }
        let addRemoveText = (inCart != "in" ? "remove range from" : "add range to");

        let rangeText = (selectedElem.length === 0 ?
                            `<i class='fas fa-sign-out-alt'></i>Start ${addRemoveText} cart here` :
                            `<i class='fas fa-sign-out-alt fa-rotate-180'></i>End ${addRemoveText} cart here`);
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

    showDetail: function(e, opusId) {
        opus.prefs.detail = opusId;
        if (e.shiftKey || e.ctrlKey || e.metaKey) {
            // handles command click to open in new tab
            let hashArray = o_hash.getHashArray();
            hashArray.detail = opusId;
            let link = "/opus/#/" + o_hash.hashArrayToHashString(hashArray);
            link = link.replace("view=browse", "view=detail");
            window.open(link, '_blank');
        } else {
            opus.prefs.detail = opusId;
            opus.changeTab("detail");
            $('a[href="#detail"]').tab("show");
        }
    },

    getGalleryElement: function(opusId) {
        let tab = opus.getViewTab();
        return $(`${tab} .thumbnail-container[data-id=${opusId}]`);
    },

    getDataTableInputElement: function(opusId) {
        return $(`.op-data-table div[data-id=${opusId}]`).parent();
    },

    startRangeSelect: function(opusId) {
        o_browse.undoRangeSelect(); // probably not necessary...
        o_browse.getGalleryElement(opusId).addClass("selected hvr-ripple-in b-a-2");
        o_browse.getDataTableInputElement(opusId).addClass("hvr-ripple-in b-a-2");
    },

    undoRangeSelect: function() {
        let tab = opus.getViewTab();
        let startElem = $(tab).find(".selected");
        if (startElem.length) {
            $(startElem).removeClass("selected hvr-ripple-in b-a-2");
            let opusId = $(startElem).data("id");
            o_browse.getDataTableInputElement(opusId).removeClass("hvr-ripple-in b-a-2");
        }
    },

    openDetailTab: function() {
        o_browse.hideGalleryViewModal();
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
        let menuSelector = `#op-metadata-selector .op-all-metadata-column a[data-slug=${slug}]`;
        o_menu.markMenuItem(menuSelector);

        let label = $(menuSelector).data("qualifiedlabel");
        let info = `<i class="fas fa-info-circle" title="${$(menuSelector).find('*[title]').attr("title")}"></i>`;
        let html = `<li id="cchoose__${slug}">${info}${label}<span class="unselect"><i class="far fa-trash-alt"></span></li>`;
        $(".op-selected-metadata-column > ul").append(html);
    },

    resetMetadata: function(cols, closeModal) {
        opus.prefs.cols = cols.slice();

        if (closeModal == true) {
            $("#op-metadata-selector").modal('hide');
        }

        // uncheck all on left; we will check them as we go
        o_menu.markMenuItem("#op-metadata-selector .op-all-metadata-column a", "unselect");

        // remove all from selected column
        $("#op-metadata-selector .op-selected-metadata-column li").remove();

        // add them back and set the check
        $.each(cols, function(index, slug) {
            o_browse.addColumn(slug);
        });
    },

    // metadata selector behaviors
    addMetadataSelectorBehaviors: function() {
        // Global within this function so behaviors can communicate
        /* jshint varstmt: false */
        var currentSelectedMetadata = opus.prefs.cols.slice();
        /* jshint varstmt: true */

        $("#op-metadata-selector").on("hide.bs.modal", function(e) {
            // update the data table w/the new columns
            if (!o_utils.areObjectsEqual(opus.prefs.cols, currentSelectedMetadata)) {
                let tab = opus.getViewTab();
                o_browse.clearObservationData();
                o_hash.updateHash(); // This makes the changes visible to the user
                o_browse.initTable(tab, opus.colLabels, opus.colLabelsNoUnits);
                o_browse.loadData(opus.prefs.view);
            } else {
                // remove spinner if nothing is re-draw when we click save changes
                $(".op-page-loading-status > .loader").hide();
            }
        });

        $("#op-metadata-selector").on("show.bs.modal", function(e) {
            // this is to make sure modal is back to it original position when open again
            $("#op-metadata-selector .modal-dialog").css({top: 0, left: 0});
            // save current column state so we can look for changes
            currentSelectedMetadata = opus.prefs.cols.slice();

            o_browse.hideMenu();
            o_browse.renderMetadataSelector();

            // Do the fake API call to write in the Apache log files that
            // we invoked the metadata selector so log_analyzer has something to
            // go on
            let fakeUrl = "/opus/__fake/__selectmetadatamodal.json";
            $.getJSON(fakeUrl, function(data) {
            });
        });

        $("#op-metadata-selector .op-all-metadata-column").on("click", '.submenu li a', function() {
            let slug = $(this).data('slug');
            if (!slug) { return; }

            let chosenSlugSelector = `#cchoose__${slug}`;
            let menuSelector = `#op-metadata-selector .op-all-metadata-column a[data-slug=${slug}]`;

            if ($(chosenSlugSelector).length === 0) {
                // this slug was previously unselected, add to cols
                o_menu.markMenuItem(menuSelector);
                o_browse.addColumn(slug);
                opus.prefs.cols.push(slug);
            } else {
                // slug had been checked, remove from the chosen
                o_menu.markMenuItem(menuSelector, "unselected");
                opus.prefs.cols.splice($.inArray(slug,opus.prefs.cols), 1);
                $(chosenSlugSelector).remove();
            }
            return false;
        });

        // removes chosen column
        $("#op-metadata-selector .op-selected-metadata-column").on("click", "li .unselect", function() {
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
                let menuSelector = `#op-metadata-selector .op-all-metadata-column a[data-slug=${slug}]`;
                o_menu.markMenuItem(menuSelector, "unselected");
            }
            return false;
        });

        // buttons
        $("#op-metadata-selector").on("click", ".btn", function() {
            switch($(this).attr("type")) {
                case "reset":
                    opus.prefs.cols = [];
                    o_browse.resetMetadata(opus.defaultColumns);
                    break;
                case "submit":
                    $(".op-page-loading-status > .loader").show();
                    break;
                case "cancel":
                    opus.prefs.cols = [];
                    o_browse.resetMetadata(currentSelectedMetadata, true);
                    break;
            }
        });
    },  // /addMetadataSelectorBehaviors

    // there are interactions that are applied to different code snippets,
    // this returns the namespace, view_var
    // that distinguishes cart vs result tab views
    // NOTE: get rid of all this with a framework!
    // usage:
    // utility function to figure out what view we are in
    /*
        // usage
        view_info = o_browse.getViewInfo();
        namespace = view_info['namespace'];
        prefix = view_info['prefix'];
    */
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

        let suppressScrollY = false;

        if (o_browse.isGalleryView()) {
            $(".op-data-table-view", tab).hide();
            $(".op-gallery-view", tab).fadeIn("done", function() {o_browse.fading = false;});

            $(".op-browse-view", tab).html("<i class='far fa-list-alt'></i>&nbsp;View Table");
            $(".op-browse-view", tab).attr("title", "View sortable metadata table");
            $(".op-browse-view", tab).data("view", "data");

            suppressScrollY = false;
        } else {
            $(".op-gallery-view", tab).hide();
            $(".op-data-table-view", tab).fadeIn("done", function() {o_browse.fading = false;});

            $(".op-browse-view", tab).html("<i class='far fa-images'></i>&nbsp;View Gallery");
            $(".op-browse-view", tab).attr("title", "View sortable thumbnail gallery");
            $(".op-browse-view", tab).data("view", "gallery");

            suppressScrollY = true;
        }
        opus.getViewNamespace().galleryScrollbar.settings.suppressScrollY = suppressScrollY;

        // sync up scrollbar position
        if (galleryInfiniteScroll && tableInfiniteScroll) {
            let startObs = $(`${tab} ${contentsView}`).data("infiniteScroll").options.obsNum;
            o_browse.setScrollbarPosition(startObs);
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

    renderMetadataSelector: function() {
        if (!o_browse.metadataSelectorDrawn) {
            let url = "/opus/__forms/metadata_selector.html?" + o_hash.getHash();
            $(".modal-body.metadata").load( url, function(response, status, xhr)  {

                o_browse.metadataSelectorDrawn = true;  // bc this gets saved not redrawn
                $("#op-metadata-selector .op-reset-button").hide(); // we are not using this

                // since we are rendering the left side of metadata selector w/the same code that builds the select menu,
                // we need to unhighlight the selected widgets
                o_menu.markMenuItem("#op-metadata-selector .op-all-metadata-column a", "unselect");

                // display check next to any currently used columns
                $.each(opus.prefs.cols, function(index, col) {
                    o_menu.markMenuItem(`#op-metadata-selector .op-all-metadata-column a[data-slug="${col}"]`);
                });

                o_browse.addMetadataSelectorBehaviors();

                o_browse.allMetadataScrollbar = new PerfectScrollbar("#op-metadata-selector-contents .op-all-metadata-column", {
                    minScrollbarLength: opus.minimumPSLength
                });
                o_browse.selectedMetadataScrollbar = new PerfectScrollbar("#op-metadata-selector-contents .op-selected-metadata-column", {
                    minScrollbarLength: opus.minimumPSLength
                });

                // dragging to reorder the chosen
                $( ".op-selected-metadata-column > ul").sortable({
                    items: "li",
                    cursor: "grab",
                    stop: function(event, ui) { o_browse.metadataDragged(this); }
                });
            });
        }
    },

    renderGalleryAndTable: function(data, url, view) {
        // render the gallery and table at the same time.
        let tab = opus.getViewTab(view);
        let viewNamespace = opus.getViewNamespace(view);
        let contentsView = o_browse.getScrollContainerClass(view);
        let selector = `${tab} ${contentsView}`;
        let infiniteScrollData = $(selector).data("infiniteScroll");

        // this is the list of all observations requested from dataimages.json
        let galleryHtml = "";
        let tableHtml = "";

        if (data.count == 0) {
            // either there are no selections OR this is signaling the end of the infinite scroll
            // for now, just post same message to both #browse & #cart tabs
            if (data.start_obs == 1) {
                if (view === "browse") {
                    // note: this only displays in gallery view; might want to gray out option for table view when no search results.
                    galleryHtml += '<div class="thumbnail-message">';
                    galleryHtml += '<h2>Your search produced no results</h2>';
                    galleryHtml += '<p>Remove or edit one or more of the search criteria selected on the Search tab ';
                    galleryHtml += 'or click on the Reset Search button to reset the search criteria to default.</p>';
                    galleryHtml += '</div>';
                } else {
                    $("#cart .navbar").hide();
                    $("#cart .sort-order-container").hide();
                    $("#cart .op-data-table-view").hide();
                    galleryHtml += '<div class="thumbnail-message">';
                    galleryHtml += '<h2>Your cart is empty</h2>';
                    galleryHtml += '<p>To add observations to the cart, click on the Browse Results tab ';
                    galleryHtml += 'at the top of the page, mouse over the thumbnail gallery images to reveal the tools, ';
                    galleryHtml += 'then click on the cart icon.  </p>';
                    galleryHtml += '</div>';
                }
                $(".gallery", tab).html(galleryHtml);
            } else {
                if (opus.prefs[o_browse.getStartObsLabel()] > data.total_obs_count) {
                    // handle a corner case where a user has changed the startobs to be greater than total_obs_count
                    // just reset back to 1 and get a new page
                    opus.prefs[o_browse.getStartObsLabel()] = 1;
                    o_hash.updateHash();
                    $("#galleryViewContents").addClass("op-disabled");
                    $(`${tab} ${contentsView}`).infiniteScroll("loadNextPage");
                } else {
                    // we've hit the end of the infinite scroll.
                    $(".op-page-loading-status > .loader").hide();
                }
                return;
            }
        } else {
            let append = (data.start_obs > $(`${tab} .thumbnail-container`).last().data("obs"));

            o_browse.manageObservationCache(data.count, append, view);
            $(`${tab} .navbar`).show();
            $(`${tab} .sort-order-container`).show();

            viewNamespace.totalObsCount = data.total_obs_count;

            $.each(data.page, function(index, item) {
                let opusId = item.opusid;
                // we have to store the relative observation number because we may not have pages in succession, this is for the slider position
                viewNamespace.observationData[opusId] = item.metadata;	// for galleryView, store in global array

                let mainTitle = `#${item.obs_num}: ${opusId}\r\nClick to enlarge\r\Ctrl+click to toggle cart\r\nShift+click to start/end range`;

                // gallery
                let images = item.images;
                galleryHtml += `<div class="thumbnail-container ${(item.in_cart ? 'op-in-cart' : '')}" data-id="${opusId}" data-obs="${item.obs_num}">`;
                galleryHtml += `<a href="#" class="thumbnail" data-image="${images.full.url}">`;
                galleryHtml += `<img class="img-thumbnail img-fluid" src="${images.thumb.url}" alt="${images.thumb.alt_text}" title="${mainTitle}">`;
                // whenever the user clicks an image to show the modal, we need to highlight the selected image w/an icon
                galleryHtml += '<div class="modal-overlay">';
                galleryHtml += '<p class="content-text"><i class="fas fa-binoculars fa-4x text-info" aria-hidden="true"></i></p>';
                galleryHtml += '</div></a>';

                galleryHtml += '<div class="op-thumb-overlay">';
                galleryHtml += `<div class="op-tools dropdown" data-id="${opusId}">`;
                galleryHtml +=     '<a href="#" data-icon="info" title="View observation detail (use CTRL for new tab)"><i class="fas fa-info-circle fa-xs"></i></a>';

                let buttonInfo = o_browse.cartButtonInfo((item.in_cart ? 'add' : 'remove'));
                galleryHtml +=     `<a href="#" data-icon="cart" title="${buttonInfo.title}"><i class="${buttonInfo.icon} fa-xs"></i></a>`;
                galleryHtml +=     '<a href="#" data-icon="menu" title="More options"><i class="fas fa-bars fa-xs"></i></a>';
                galleryHtml += '</div>';
                galleryHtml += '</div></div>';

                // table row
                let checked = item.in_cart ? " checked" : "";
                let checkbox = `<input type="checkbox" name="${opusId}" value="${opusId}" class="multichoice"${checked}/>`;
                let minimenu = `<a href="#" data-icon="menu" title="More options"><i class="fas fa-bars fa-xs"></i></a>`;
                let row = `<td class="op-table-tools"><div class="op-tools mx-0 form-group" title="Toggle cart\r\nShift+click to start/end range" data-id="${opusId}">${checkbox} ${minimenu}</div></td>`;
                let tr = `<tr data-id="${opusId}" data-target="#galleryView" data-obs="${item.obs_num}" title="${mainTitle}">`;
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

        // Note: we have to manually set the scrollbar position.
        // - scroll up: when we scroll up and a new page is fetched, we want to keep scrollbar position at the current startObs,
        //   instead of at the first item in newly fetched page.
        // - scroll slider: when we load 3 * getLimit items, we want to keep scrollbar in the middle page.
        // - scroll down: theoretically, infiniteScroll will take care of scrollbar position, but we still have to manually set
        //   it for the case when cached data is removed so that scrollbar position is always correct (and never reaches to the
        //   end until it reaches to the end of the data)
        o_browse.setScrollbarPosition(infiniteScrollData.options.obsNum, view);

        $(".op-page-loading-status > .loader").hide();
        o_browse.updateSliderHandle();
        o_hash.updateHash(true);
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
        return (galleryBoundingRect.x * galleryBoundingRect.y);
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
        if (limitNum === 0 || isNaN(limitNum)) {
            opus.logError(`limitNum:  ${limitNum}, customizedLimitNum = ${customizedLimitNum}`);
        }
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
            if (delOpusId === $("#galleryViewContents .select").data("id")) {
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
        viewNamespace.galleryBoundingRect = o_browse.countGalleryImages(view);

        if (!$(selector).data("infiniteScroll")) {
            $(selector).infiniteScroll({
                path: function() {
                    let obsNum = opus.prefs[startObsLabel];
                    let customizedLimitNum;
                    let lastObs = $(`${tab} .thumbnail-container`).last().data("obs");
                    let firstCachedObs = $(`${tab} .thumbnail-container`).first().data("obs");

                    let infiniteScrollData = $(selector).data("infiniteScroll");
                    if (infiniteScrollData !== undefined && infiniteScrollData.options.loadPrevPage === true) {
                        // Direction: scroll up, we prefetch 1 * o_browse.getLimit() items
                        if (obsNum !== 1) {
                            // prefetch o_browse.getLimit() items ahead of firstCachedObs, update the startObs to be passed into url
                            obsNum = Math.max(firstCachedObs - o_browse.getLimit(view), 1);

                            // If obsNum to be passed into api url is 1, we will pass firstCachedObs - 1 as limit
                            // else we'll pass in o_browse.getLimit() as limit
                            customizedLimitNum = obsNum === 1 ? firstCachedObs - 1 : o_browse.getLimit(view);

                            // Update the obsNum in infiniteScroll instances with firstCachedObs
                            // This will be used to set the scrollbar position later
                            if (infiniteScrollData) {
                                $(`${tab} .op-gallery-view`).infiniteScroll({"obsNum": firstCachedObs});
                                $(`${tab} .op-data-table-view`).infiniteScroll({"obsNum": firstCachedObs});
                                opus.prefs[startObsLabel] = firstCachedObs;
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
                        let scrollbarObsNum = Math.max(obsNum - o_browse.getLimit(view) - opus.getViewNamespace(view).galleryBoundingRect.x, 1);

                        // Update the obsNum in infiniteScroll instances with the first obsNum of the row above current last page
                        // This will be used to set the scrollbar position later
                        if (infiniteScrollData) {
                            $(`${tab} .op-gallery-view`).infiniteScroll({"obsNum": scrollbarObsNum});
                            $(`${tab} .op-data-table-view`).infiniteScroll({"obsNum": scrollbarObsNum});
                            opus.prefs[startObsLabel] = scrollbarObsNum;
                        }
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
                status: `${tab} .page-load-status`,
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
                let firstObs = $(`${tab} .thumbnail-container`).first().data("obs");
                let lastObs = $(`${tab} .thumbnail-container`).last().data("obs");

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

            function eventListenerWithView(event, response, path) {
                o_browse.infiniteScrollLoadEventListener(event, response, path, view);
            }
            $(selector).on("load.infiniteScroll", eventListenerWithView);
        }
    },

    loadData: function(view, startObs, customizedLimitNum=undefined) {
        let tab = opus.getViewTab(view);
        let startObsLabel = o_browse.getStartObsLabel(view);
        let contentsView = o_browse.getScrollContainerClass(view);
        let viewNamespace = opus.getViewNamespace(view);

        let galleryInfiniteScroll = $(`${tab} .op-gallery-view`).data("infiniteScroll");
        let tableInfiniteScroll = $(`${tab} .op-data-table-view`).data("infiniteScroll");

        startObs = (startObs === undefined ? opus.prefs[startObsLabel] : startObs);

        if (!viewNamespace.reloadObservationData) {
            // if the request is a block far away from current page cache, flush the cache and start over
            let elem = $(`${tab} [data-obs="${startObs}"]`);
            let lastObs = $(`${tab} [data-obs]`).last().data("obs");
            let firstObs = $(`${tab} [data-obs]`).first().data("obs");

            // if the startObs is not already rendered and is obviously not contiguous, clear the cache and start over
            if (lastObs === undefined || firstObs === undefined || elem.length === 0 ||
                (startObs > lastObs + 1) || (startObs < firstObs - 1)) {
                viewNamespace.reloadObservationData = true;
            } else {
                // wait! is this page already drawn?
                // if startObs drawn, move the slider to that line, fetch if need be after
                if (startObs >= firstObs && startObs <= lastObs) {
                    // may need to do a prefetch here...
                    if (galleryInfiniteScroll && tableInfiniteScroll) {
                        startObs = $(`${tab} ${contentsView}`).data("infiniteScroll").options.obsNum;
                    }
                    o_browse.setScrollbarPosition(startObs, view);
                    $(".op-page-loading-status > .loader").hide();
                    return;
                }
            }
        }

        $(".op-page-loading-status > .loader").show();
        // Note: when browse page is refreshed, startObs passed in (from activateBrowseTab) will start from 1
        let url = o_browse.getDataURL(view, startObs, customizedLimitNum);

        // metadata; used for both table and gallery
        $.getJSON(url, function(data) {
            if (data.reqno < opus.lastLoadDataRequestNo[view]) {
                // make sure to remove spinner before return
                $(".op-page-loading-status > .loader").hide();
                return;
            }

            if (viewNamespace.reloadObservationData) {
                o_browse.initTable(tab, data.columns, data.columns_no_units);

                $(`${tab} .op-gallery-view`).scrollTop(0);
                $(`${tab} .op-data-table-view`).scrollTop(0);
            }

            // Because we redraw from the beginning on user inputted page, we need to remove previous drawn thumb-pages
            $(`${tab} .thumbnail-container`).each(function() {
                let delOpusId = $(this).data("id");
                delete viewNamespace.observationData[delOpusId];
            });
            $(`${tab} .thumbnail-container`).remove();
            o_browse.hideGalleryViewModal();

            o_browse.renderGalleryAndTable(data, this.url, view);

            if (o_browse.metadataDetailOpusId != "") {
                o_browse.metadataboxHtml(o_browse.metadataDetailOpusId, view);
            }
            o_browse.updateSortOrder(data);

            viewNamespace.reloadObservationData = false;
        });
    },

    infiniteScrollLoadEventListener: function(event, response, path, view) {
        $(".op-page-loading-status > .loader").show();
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
    },

    activateBrowseTab: function() {
        // init o_browse.galleryBoundingRect
        opus.getViewNamespace().galleryBoundingRect = o_browse.countGalleryImages();
        // reset range select
        o_browse.undoRangeSelect();

        $(".op-page-loading-status > .loader").show();
        o_browse.updateBrowseNav();
        o_browse.renderMetadataSelector();   // just do this in background so there's no delay when we want it...

        o_browse.loadData(opus.prefs.view);
    },

    countTableRows: function(view) {
        let tab = opus.getViewTab(view);
        let height = o_browse.calculateGalleryHeight(view);
        let trCount = 1;

        if ($(`${tab} .op-data-table tbody tr[data-obs]`).length > 0) {
            trCount = o_utils.floor((height-$("th").outerHeight())/$(`${tab} .op-data-table tbody tr[data-obs]`).outerHeight());
        }
        opus.getViewNamespace(view).galleryBoundingRect.tr = trCount;
        return trCount;
    },

    countGalleryImages: function(view) {
        let tab = opus.getViewTab(view);
        let viewNamespace = opus.getViewNamespace(view);
        let width = o_browse.calculateGalleryWidth(view);
        let height = o_browse.calculateGalleryHeight(view);

        let trCount = 1;
        if ($(`${tab} .op-data-table tbody tr[data-obs]`).length > 0) {
            trCount = o_utils.floor((height-$("th").outerHeight())/$(`${tab} .op-data-table tbody tr[data-obs]`).outerHeight());
        }

        let xCount = o_utils.floor(width/o_browse.imageSize);
        let yCount = Math.round(height/o_browse.imageSize);
        // let yCount = Math.ceil(height/o_browse.imageSize);

        // update the number of cached observations based on screen size
        // for now, only bother when we update the browse tab...
        // rounding because the factor value can be a FP number.
        viewNamespace.maxCachedObservations = Math.round(xCount * yCount * viewNamespace.cachedObservationFactor);

        return {"x": xCount, "y": yCount, "tr": trCount};
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

    adjustBrowseHeight: function(browserResized=false) {
        let tab = opus.getViewTab();
        let containerHeight = o_browse.calculateGalleryHeight();
        $(`${tab} .gallery-contents`).height(containerHeight);
        $(`${tab} .gallery-contents .op-gallery-view`).height(containerHeight);

        let viewNamespace = opus.getViewNamespace();
        viewNamespace.galleryScrollbar.update();
        viewNamespace.galleryBoundingRect = o_browse.countGalleryImages();

        // make sure slider is updated when window is resized
        o_browse.updateSliderHandle(browserResized);
    },

    adjustTableSize: function() {
        let tab = opus.getViewTab();
        let containerWidth = $(`${tab} .gallery-contents`).width();
        let containerHeight = $(`${tab} .gallery-contents`).height();
        $(`${tab} .op-data-table-view`).width(containerWidth);
        $(`${tab} .op-data-table-view`).height(containerHeight);
        opus.getViewNamespace().tableScrollbar.update();
    },

    adjustMetadataSelectorMenuPS: function() {
        let containerHeight = $(".op-all-metadata-column").height();
        let menuHeight = $(".op-all-metadata-column .searchMenu").height();

        if (o_browse.allMetadataScrollbar) {
            if (containerHeight > menuHeight) {
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

    adjustSelectedMetadataPS: function() {
        let containerHeight = $(".op-selected-metadata-column").height();
        let selectedMetadataHeight = $(".op-selected-metadata-column .ui-sortable").height();

        if (o_browse.selectedMetadataScrollbar) {
            if (containerHeight > selectedMetadataHeight) {
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

    adjustBrowseDialogPS: function() {
        let containerHeight = $("#galleryViewContents .metadata").height();
        let browseDialogHeight = $(".metadata .contents").height();

        if (o_browse.modalScrollbar) {
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
        }
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
        let selector = `.op-thumb-overlay [data-id=${opusId}] [data-icon="cart"]`;
        $(selector).html(`<i class="${buttonInfo.icon} fa-xs"></i>`);
        $(selector).prop("title", buttonInfo.title);

        let modalCartSelector = `#galleryViewContents .bottom .select[data-id=${opusId}]`;
        if ($("#galleryView").is(":visible") && $(modalCartSelector).length > 0) {
            $(modalCartSelector).html(`<i class="${buttonInfo.icon} fa-2x"></i>`);
            $(modalCartSelector).prop("title", `${buttonInfo.title} (spacebar)`);
        }
    },

    getNextPrevHandles: function(opusId, view) {
        let tab = opus.getViewTab(view);
        let idArray = $(`${tab} .thumbnail-container[data-obs]`).map(function() {
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
        let status = o_cart.isIn(opusId) ? "" : "in";
        let buttonInfo = o_browse.cartButtonInfo(status);

        // prev/next buttons - put this in galleryView html...
        html = `<div class="col"><a href="#" class="select" data-id="${opusId}" title="${buttonInfo.title} (spacebar)"><i class="${buttonInfo.icon} fa-2x float-left"></i></a></div>`;
        html += `<div class="col text-center op-obs-direction">`;
        let opPrevDisabled = (nextPrevHandles.prev == "" ? "op-button-disabled" : "");
        let opNextDisabled = (nextPrevHandles.next == "" ? "op-button-disabled" : "");
        html += `<a href="#" class="op-prev text-center ${opPrevDisabled}" data-id="${nextPrevHandles.prev}" title="Previous image: ${nextPrevHandles.prev} (left arrow key)"><i class="far fa-hand-point-left fa-2x"></i></a>`;
        html += `<a href="#" class="op-next ${opNextDisabled}" data-id="${nextPrevHandles.next}" title="Next image: ${nextPrevHandles.next} (right arrow key)"><i class="far fa-hand-point-right fa-2x"></i></a>`;
        html += `</div>`;

        // mini-menu like the hamburger on the observation/gallery page
        html += `<div class="col"><a href="#" class="menu pr-3 float-right" data-toggle="dropdown" role="button" data-id="${opusId}" title="More options"><i class="fas fa-bars fa-2x"></i></a></div>`;
        $("#galleryViewContents .bottom").html(html);
    },

    updateGalleryView: function(opusId) {
        let tab = `#${opus.prefs.view}`;
        $(tab).find(".modal-show").removeClass("modal-show");
        $(tab).find(`[data-id='${opusId}'] div.modal-overlay`).addClass("modal-show");
        $(tab).find(`tr[data-id='${opusId}']`).addClass("modal-show");
        let imageURL = $(tab).find(`[data-id='${opusId}'] > a.thumbnail`).data("image");
        o_browse.updateMetaGalleryView(opusId, imageURL);
    },


    updateMetaGalleryView: function(opusId, imageURL) {
        let tab = `#${opus.prefs.view}`;
        let element = (o_browse.isGalleryView() ? $(`${tab} .thumbnail-container[data-id=${opusId}]`) : $(`${tab} tr[data-id=${opusId}]`));
        let obsNum = $(element).data("obs");
        let title = `#${obsNum}: ${opusId}\r\nClick for full-size image`;

        $("#galleryViewContents .left").html(`<a href="${imageURL}" target="_blank"><img src="${imageURL}" title="${title}" class="op-slideshow-image-preview"/></a>`);
        o_browse.metadataboxHtml(opusId);
    },

    clearObservationData: function() {
        opus.prefs.startobs = 1; // reset startobs to 1 when data is flushed
        opus.prefs.cart_startobs = 1;
        o_cart.reloadObservationData = true;  // forces redraw of cart tab
        o_cart.observationData = {};
        o_browse.reloadObservationData = true;  // forces redraw of browse tab
        o_browse.observationData = {};
    },
};
