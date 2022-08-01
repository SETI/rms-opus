/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* globals $, PerfectScrollbar */
/* globals o_cart, o_hash, o_utils, o_selectMetadata, o_sortMetadata, o_menu, o_widgets, opus */
/* globals MAX_SELECTIONS_ALLOWED */

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
    modalScrollbar: new PerfectScrollbar(".op-metadata-detail-view-body .op-metadata-details", {
        minScrollbarLength: opus.minimumPSLength
    }),

    // these vars are common w/o_cart
    reloadObservationData: true, // start over by reloading all data
    metadataDetailEdit: false, // is the metadata detail view currently in edit mode?
    observationData: {},  // holds observation column data
    totalObsCount: undefined,
    cachedObservationFactor: 4,     // this is the factor times the screen size to determine cache size
    maxCachedObservations: 1000,    // max number of observations to store in cache, will be updated based on screen size
    galleryBoundingRect: {'x': 0, 'yCell': 0, 'yFloor': 0, 'yPartial': 0, 'trFloor': 0},
    gallerySliderStep: 10,
    // opusID of the last slide show/gallery view modal after it is closed
    lastMetadataDetailOpusId: "",

    // The viewable fraction of an item's height such that it will be treated as present on the screen
    galleryImageViewableFraction: 0.8,

    // A flag to determine if the sortable item sorting is happening. This
    // will be used in mutation observer to determine if scrollbar location should
    // be set.
    isSortingHappening: false,

    // unique to o_browse
    imageSize: 100,     // default

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

        // Get the x coordinate of the current cursor when moving mouse in the table view.
        // Also when moving around in the same table row, reposition the tooltip so that
        // it stays right next to the cursor. Work for both browse/cart data table.
        $(".op-data-table tbody").on("mousemove", function(e) {
            o_utils.onMouseMoveHandler(e, $(e.target).parent("tr"));
        });

        // Get the x & y coordinate of the current cursor when moving mouse in metadatabox
        // image. Reposition the tooltip based on the cursor location.
        $(".op-metadata-detail-view-body").on("mousemove", ".op-slideshow-image-preview" , function(e) {
            o_utils.onMouseMoveHandler(e, $(e.target));
        });

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
            o_browse.hideMenus();
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

            o_browse.hideMenus();
            let browse = o_browse.getBrowseView();
            opus.prefs[browse] = $(this).data("view");
            if (!o_browse.isGalleryView()) {
                // update this when we switch to table view
                o_browse.countTableRows();
            }

            o_hash.updateURLFromCurrentHash();
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
            o_browse.downloadCSV(this);
        });

        // 1 - click on thumbnail opens modal window
        // 2-  Shift+click or menu/"Start Add[Remove] Range Here" starts a range
        //          Shfit+click on menu/"End Add[Remove] Range Here" ends a range
        //          Clicking on a cart/trash can anywhere aborts the range selection
        // 3 - ctrl click - alternate way to add to cart
        // NOTE: range can go forward or backwards

        // images...
        $(".gallery").on("click", ".thumbnail, .op-recycle-overlay, .op-detail-overlay, .op-last-modal-overlay", function(e) {
            let elem = $(this).parent();
            // Init the cursor position so that the image tooltip will be properly positioned if
            // the cursor is right on the image when the metadatabox is open for the first time.
            opus.mouseX = e.clientX;
            opus.mouseY = e.clientY;
            o_browse.onGalleryOrRowClick(elem, e);
        });

        $(".op-data-table").on("click", "td:not(:first-child)", function(e) {
            let elem = $(this).parent();
            // Init the cursor position so that the image tooltip will be properly positioned if
            // the cursor is right on the image when the metadatabox is open for the first time.
            opus.mouseX = e.clientX;
            opus.mouseY = e.clientY;
            o_browse.onGalleryOrRowClick(elem, e);
        });

        // data_table - clicking a table row adds to cart
        $(".op-data-table").on("click", ":checkbox", function(e) {
            // Click the checkbox of each individual observation
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

            o_sortMetadata.hideMenu();
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

        $("#op-metadata-detail-view-content, #op-select-metadata .modal-content").draggable({
            cancel: ".contents",
            containment: "document",
            start: function(event, ui) {
                o_browse.hideMenus();
            },
        });

        $("#op-metadata-detail-view .modal-content").resizable({
            handles: "n, e, s, w, ne, se, sw, nw",
            minWidth: 250,
            minHeight: 240,
            start: function(event, ui) {
                // update the tools buttons for min/max to enable on start
                o_browse.updateMetadataDetailViewTool("min", false);
                o_browse.updateMetadataDetailViewTool("max", false);
            },
            resize: function(event, ui) {
                o_browse.keepMetadataResizeContained();
                o_browse.onResizeMetadataDetailView();
                o_browse.adjustMetadataDetailDialogPS(true);
            },
            stop: function(event, ui) {
                o_browse.checkForMaximizeMetadataDetailView();
            },
        }).on("resize", function(e) {
            e.stopPropagation();
        });

        $(".app-body").on("shown.bs.modal", "#op-metadata-detail-view", function(e) {
            opus.getViewNamespace().lastMetadataDetailOpusId = "";
            o_browse.checkForMaximizeMetadataDetailView();
            o_browse.onResizeMetadataDetailView();
        });

        $(".app-body").on("hide.bs.modal", "#op-metadata-detail-view", function(e) {
            let tab = o_browse.getViewInfo().namespace;
            $(tab).find(".op-modal-show").removeClass("op-modal-show");
            let elem = $(`${tab} [data-id='${opus.metadataDetailOpusId}'] .op-last-modal-overlay`);
            if (elem.length > 0) {
                elem.removeClass("op-hide-element");
            }
            opus.getViewNamespace().lastMetadataDetailOpusId = opus.metadataDetailOpusId;
            opus.metadataDetailOpusId = "";
            o_browse.removeEditMetadataDetails();
        });

        $(".op-slide-minimize").on("click", function(e) {
            let selector = "#op-metadata-detail-view-content";
            // don't do anything if already minimized..
            if ($(selector).resizable("instance").min !== true) {
                let width = $(selector).resizable("option", "minWidth");
                let height = $(selector).resizable("option", "minHeight");
                o_browse.updateMetadataDetailViewTool("min", true);
                o_browse.centerMetadataDetailViewToDefault(width, height);
            }
        });

        $(".op-slide-maximize").on("click", function(e) {
            // if no style defined, must already be maximized.
            let selector = "#op-metadata-detail-view-content";
            if ($(selector).resizable("instance").max !== true) {
                let width = $("#op-metadata-detail-view .modal-dialog").width();
                let height = $("#op-metadata-detail-view .modal-dialog").height();
                o_browse.updateMetadataDetailViewTool("max", true);
                o_browse.centerMetadataDetailViewToDefault(width, height);
            }
        });

        $(".op-slide-dock").on("click", function(e) {
            /* NOT YET IMPLEMENTED */
            // remove resizable for the moment; maybe change to just e-w
            let slidePanel = $("#op-metadata-detail-view-content .op-metadata-detail-view-body").detach();
            $(".op-metadata-detail-view-docked").html(slidePanel);
            $(".op-metadata-detail-view-docked").show();
        });

        $(".op-metadata-detail-view-body").on("click", "a.op-cart-toggle", function(e) {
            let opusId = $(this).data("id");
            if (opusId) {
                // clicking on the cart/trash can aborts range select
                o_browse.undoRangeSelect();
                o_cart.toggleInCart(opusId);
            }
            return false;
        });

        $(".op-metadata-detail-view-body").on("click", "a.op-prev,a.op-next", function(e) {
            let action = $(this).hasClass("op-prev") ? "prev" : "next";
            let opusId = $(this).data("id");
            let obsNum = $(this).data("obs");

            if (opusId) {
                o_browse.removeEditMetadataDetails();
                o_browse.loadPageIfNeeded(action, opusId);
                obsNum += (action === "prev" ? -1 : 1);
                o_browse.updateMetadataDetailView(opusId, obsNum);
            }
            return false;
        });

        $(".op-metadata-detail-view-body").on("click", "a.menu", function(e) {
            let opusId = $(this).data("id");
            o_browse.showMenu(e, opusId);
            return false;
        });

        $(".op-metadata-detail-view-body").on("click", "a.op-edit-metadata-button", function(e) {
            let action = $(this).attr("action");
            if (action === "edit") {
                o_browse.initEditMetadataDetails();
            } else {
                o_browse.removeEditMetadataDetails();
            }
            return false;
        });

        $(".op-select-list").on("click", ".dropdown-item", function(e) {
            o_browse.hideMenus();
            return false;
        });

        $(".op-metadata-detail-view-body").on("click", "a.op-metadata-detail-add", function(e) {
            // allow the hover to work but the click appear to be disabled
            if ($(".op-metadata-detail-add").hasClass("op-add-disabled")) {
                return false;
            }
            let slug = $(this).closest("ul").data("slug");
            // save anything that was changed via sort/trash before the dropdown is displayed
            o_browse.onDoneUpdateMetadataDetails();
            o_browse.showMetadataList(e);
            $("#op-add-metadata-fields").data("slug", slug);

            return false;
        });

        $(".op-metadata-detail-view-body").on("click", "a.op-metadata-detail-remove", function(e) {
            let slug = $(this).closest("ul").data("slug");
            o_menu.markMenuItem(`#op-add-metadata-fields .op-select-list a[data-slug="${slug}"]`, "unselect");
            $(this).closest("ul").remove();
            if ($("a.op-metadata-detail-remove").length <= 1) {
                $("a.op-metadata-detail-remove").addClass("op-button-disabled");
            }
            o_browse.onDoneUpdateMetadataDetails();
            return false;
        });

        // Toggle the submenu category and avoid dropdown menu #op-add-metadata-fields from closing
        // When clicking inside #op-add-metadata-fields.
        $("#op-add-metadata-fields").on("click", ".op-submenu-category, .op-search-menu-category", function(e) {
            e.stopPropagation();
            // Prevent dropdown menu from jumping when clicking on categories with scrollbar appears
            // and disappears.
            e.preventDefault();
            let collapsibleID = $(this).attr("href");
            if (collapsibleID !== undefined) {
                $(`${collapsibleID}`).collapse("toggle");
                collapsibleID = collapsibleID.replace("mini", "submenu");
                $(`${collapsibleID}`).collapse("toggle");
            }
        });

        $("#op-add-metadata-fields .op-select-list").on("click", '.submenu li a', function(e) {
            let slug = $(this).data('slug');
            if (!slug) { return; }
            let contextMenu = "#op-add-metadata-fields";

            let parentSlug = $(contextMenu).data("slug");
            let direction = $(contextMenu).data("direction");
            let index = $.inArray(parentSlug, opus.prefs.cols);
            if (index >= 0) {
                if (direction === "after") {
                    index++;
                }
                opus.prefs.cols.splice(index, 0, slug);
                // save the last slug that was added so that we can make sure it is visible on scroll
                $(contextMenu).data("last", slug);
                $((`${contextMenu} .op-select-list a[data-slug="${slug}"]`)).hide();

                o_selectMetadata.saveChanges();
                o_selectMetadata.reRender();
            }
            // remove the disable in case there was only one field to start with...
            $("a.op-metadata-detail-remove").removeClass("op-button-disabled");
            o_browse.hideMetadataList();
            o_browse.hideTableMetadataTools(e);
            return false;
        });

        // prevent drag of gallery modal while the add field menu is present
        $("#op-add-metadata-fields").on("mousedown", function(e) {
            e.stopPropagation();
            e.preventDefault();
        });

        // Click add all to cart icon in the first column of the browse table header
        $(".op-data-table-view").on("click", ".op-table-header-addall", function(e) {
            o_browse.confirmationBeforeAddAll();
        });

        $(".op-data-table-view").on("mouseenter", "th.op-draggable", function(e) {
            if ($(".op-metadata-detail-add").hasClass("op-add-disabled") || o_browse.isSortingHappening) {
                return false;
            }
            let slug = $(this).attr("id");
            o_browse.showTableMetadataTools(e, slug);
        });

        $(".op-data-table-view").on("mouseleave", "th.op-draggable", function(e) {
            let tab = opus.getViewTab();
            let tools = $(`${tab} .op-edit-field-tool`);
            if (e.pageY < Math.floor(tools.offset().top)  ||
               (e.pageY > tools.outerHeight() + tools.offset().top) ||
               (e.pageX < tools.offset().left) ||
               (e.pageX > tools.outerWidth() + tools.offset().left)) {
                o_browse.hideMetadataList(e);
                o_browse.hideTableMetadataTools(e);
            }
        });

        $("#op-add-metadata-fields").on("mouseleave", function(e) {
            o_browse.hideMetadataList(e);
            o_browse.hideTableMetadataTools(e);
        });

        $(".op-edit-field-tool").on("mouseleave", function(e) {
            // only hide the edit metadata field tool bar if the add metadata menu is not showing
            if (!$("#op-add-metadata-fields").hasClass("show")) {
                o_browse.hideTableMetadataTools(e);
            }
        });

        $(".op-edit-field-tool a").on("click", function(e) {
            let action = $(this).data("action");
            let tab = opus.getViewTab();
            let slug = $(`${tab} .op-edit-field-tool`).data("slug");
            switch (action) {
                case "addBefore":
                    $("#op-add-metadata-fields").data("slug", slug);
                    $("#op-add-metadata-fields").data("direction", "before");
                    o_browse.showMetadataList(e);
                    break;
                case "remove":
                    o_menu.markMenuItem(`#op-add-metadata-fields .op-select-list a[data-slug="${slug}"]`, "unselect");
                    opus.prefs.cols = opus.prefs.cols.filter(col => col !== slug);
                    o_browse.onDoneUpdateFromTableMetadataDetails(e);
                    break;
                case "addAfter":
                    $("#op-add-metadata-fields").data("slug", slug);
                    $("#op-add-metadata-fields").data("direction", "after");
                    o_browse.showMetadataList(e);
                    break;
            }
            return false;
        });

        $("#op-obs-menu").on("click", '.dropdown-header',  function(e) {
            o_browse.hideMenus();
            return false;
        });

        $("#op-obs-menu").on("click", '.dropdown-item',  function(e) {
            let retValue = false;
            let opusId = $(this).parent().attr("data-id");
            o_browse.hideMenus();

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

                case "addall":
                    o_browse.confirmationBeforeAddAll();
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
                let tab = ui.handle.dataset.bsTarget;
                o_browse.onSliderHandleMoving(tab, ui.value);
                o_browse.hideMenus();
            },
            stop: function(event, ui) {
                let tab = ui.handle.dataset.bsTarget;
                o_browse.onSliderHandleStop(tab, ui.value);
            }
        });

        $(document).on("keydown click", function(e) {
            // don't close the mini-menu on the ctrl key in case the user
            // is trying to open a new window for detail
           if (!(e.ctrlKey || e.metaKey)) {
                o_browse.hideMenus();
            }

            if (o_utils.ignoreArrowKeys &&
                ((e.which || e.keyCode) == 37 || (e.which || e.keyCode) == 39)) {
                e.preventDefault();
                return;
            }

            if ((e.which || e.keyCode) == 27) { // esc - close modals
                o_browse.hideMetadataDetailModal();
                $("#op-select-metadata").modal('hide');
                // reset range select
                o_browse.undoRangeSelect();
            }

            if ($("#op-metadata-detail-view").hasClass("show")) {
                if (o_browse.pageLoaderSpinnerTimer === null) {
                    /*  Catch the right/left arrow and spacebar while in the modal
                        Up: 38
                        Down: 40
                        Right: 39
                        Left: 37
                        Space: 32 */
                    let viewNamespace = opus.getViewNamespace();
                    let offset = 0;
                    let obsNum = $("#op-metadata-detail-view-content .op-obs-direction a").data("obs");
                    // the || is for cross-browser support; firefox does not support keyCode
                    switch (e.which || e.keyCode) {
                        case 32:  // spacebar
                            if (opus.metadataDetailOpusId !== "" && opus.metadataDetailOpusId !== undefined) {
                                o_browse.undoRangeSelect();
                                o_cart.toggleInCart(opus.metadataDetailOpusId);
                            }
                            break;
                        case 37:  // prev
                            obsNum--;
                            o_browse.moveToNextMetadataSlide(obsNum, "prev");
                            break;
                        case 39:  // next
                            obsNum++;
                            o_browse.moveToNextMetadataSlide(obsNum, "next");
                            break;
                        case 38:  // up
                            // decrement the current obsNum by 1 if table view such that up and left behave the same for the table view,
                            // otherwise by number of observations per row
                            offset = (o_browse.isGalleryView() ? viewNamespace.galleryBoundingRect.x : 1);
                            obsNum -= offset;
                            o_browse.moveToNextMetadataSlide(obsNum, "prev");
                            break;
                        case 40:  // down
                            // increment the current obsNum by 1 if table view such that down and right behave the same for the table view,
                            // otherwise by number of observations per row
                            offset = (o_browse.isGalleryView() ? viewNamespace.galleryBoundingRect.x : 1);
                            obsNum += offset;
                            o_browse.moveToNextMetadataSlide(obsNum, "next");
                            break;
                        default:
                            // allow exception handling to propagate
                            // fixes the bug that prevented click on the slide to open a full size image
                            return true;
                    }
                    e.preventDefault();
                }
                return false;
            }
            // don't return false here or it will snatch all the user input!
        });
    }, // end browse behaviors

    onGalleryOrRowClick: function(obj, e) {
        // make sure selected slide show modal thumb is unhighlighted, as clicking on this closes
        // the slide show modal but is not caught in time before hidden.bs to get correct opusId
        e.preventDefault();
        o_browse.hideMenus();

        if (obj !== null) {
            let opusId = obj.data("id");
            let obsNum = obj.data("obs");

            // Detecting ctrl (windows) / meta (mac) key.
            if (e.ctrlKey || e.metaKey) {
                o_cart.toggleInCart(opusId);
                o_browse.undoRangeSelect();
            }
            // Detecting shift key
            else if (e.shiftKey) {
                o_browse.cartShiftKeyHandler(e, opusId);
            } else {
                o_browse.showMetadataDetailModal(opusId, obsNum);
            }
        }
    },

    confirmationBeforeAddAll: function() {
        /**
         * Display a modal before add all action. If the result count is more
         * than MAX_SELECTIONS_ALLOWED, display a warning modal to ask user
         * to reduce the number of obs before add all aciton. If the result
         * count is less than MAX_SELECTIONS_ALLOWED, display a confirmation
         * modal.
         */
        if (o_browse.totalObsCount <= MAX_SELECTIONS_ALLOWED) {
            $("#op-addall-to-cart-modal").modal("show");
        } else {
            let warningMsg = "There are too many results to add them all to the cart. " +
                             "Please reduce the number of results to " +
                             ` ${o_utils.addCommas(MAX_SELECTIONS_ALLOWED)} ` +
                             "or fewer and try again.";
            $("#op-addall-warning-msg-modal .modal-body").text(warningMsg);
            $("#op-addall-warning-msg-modal").modal("show");
        }
    },

    cartShiftKeyHandler: function(e, opusId) {
        let tab = opus.getViewTab();
        let fromOpusId = $(`${tab} .op-gallery-view`).data("infiniteScroll").options.rangeSelectOpusID;
        if (fromOpusId === undefined) {
            o_browse.startRangeSelect(opusId);
        } else {
            o_cart.toggleInCart(fromOpusId, opusId);
        }
    },

    loadPageIfNeeded: function(direction, opusId) {
        // opusId will be empty at the end of the observations, so just return out.
        if (opusId === "") {
            return;
        }
        let tab = opus.getViewTab();
        let contentsView = o_browse.getScrollContainerClass();
        let viewNamespace = opus.getViewNamespace();
        opus.metadataDetailOpusId = opusId;

        let maxObs = viewNamespace.totalObsCount;
        let element = (o_browse.isGalleryView() ? $(`${tab} .op-thumbnail-container[data-id=${opusId}]`) : $(`${tab} tr[data-id=${opusId}]`));
        let obsNum = $(element).data("obs");

        let checkView = (direction === "next" ? obsNum <= maxObs : obsNum > 0);

        if (checkView) {
            // make sure the current element that the modal is displaying is viewable
            if (!element.isOnScreen($(`${tab} .op-gallery-contents`), 0.5)) {
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
            let galleryContainerTopPosition = $(`${tab} .op-gallery-contents .op-gallery-view`).offset().top;
            let galleryScrollbarPosition = $(`${tab} .op-gallery-contents .op-gallery-view`).scrollTop();

            let galleryTargetFinalPosition = (galleryTargetTopPosition - galleryContainerTopPosition +
                                              galleryScrollbarPosition - offset);
            $(`${tab} .op-gallery-contents .op-gallery-view`).scrollTop(galleryTargetFinalPosition);

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

        // Properly set loadOnScroll. This will avoid loadOnScroll being false when the user
        // drags the slider from the most right end to the middle.
        if ($(`${tab} .op-gallery-view`).data("infiniteScroll") &&
            $(`${tab} .op-data-table-view`).data("infiniteScroll")) {
            if (value >  viewNamespace.totalObsCount) {
                $(`${tab} .op-gallery-view`).infiniteScroll({"loadOnScroll": false});
                $(`${tab} .op-data-table-view`).infiniteScroll({"loadOnScroll": false});
            } else {
                $(`${tab} .op-gallery-view`).infiniteScroll({"loadOnScroll": true});
                $(`${tab} .op-data-table-view`).infiniteScroll({"loadOnScroll": true});
            }
        }

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
            o_browse.loadData(view, true, obsNum, customizedLimitNum);
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

        let numberOfObsFitOnTheScreen = (o_browse.isGalleryView(view) ? galleryImages.x * galleryImages.yFloor :
                                         galleryImages.trFloor);
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

        // For gallery view, the topBoxBoundary is the top of .op-gallery-contents
        // For table view, we will set the topBoxBoundary to be the bottom of thead
        // (account for height of thead)
        let browseContentsContainerTop = $(`${tab} .op-gallery-contents`).offset().top;
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
            let numberWidth = o_utils.addCommas(maxSliderVal).length*0.55+0.7;
            $(`${tab} .op-slider-pointer`).css("width", `${numberWidth}em`);
            // See https://stackoverflow.com/questions/5540170/jquery-ui-sliders-hops-when-clicked
            $(`${tab} .op-slider-pointer`).css("margin-left", `-${numberWidth/2}em`);
            // This offsets the slider bar from the "Observation #" text
            $(`${tab} .op-observation-slider`).css("margin-left", `${numberWidth/2-0.5}em`);
            $(`${tab} .op-observation-slider`).css("margin-right", `${numberWidth/2-0.5}em`);

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
        o_hash.updateURLFromCurrentHash();
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
            let galleryContainerTopPosition = $(`${tab} .op-gallery-contents .op-gallery-view`).offset().top;
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

    // for the mutationObserver code on browser resize...
    adjustMetadataDetailViewSize: function() {
        if ($("#op-metadata-detail-view").hasClass("show")) {
            o_browse.checkForMaximizeMetadataDetailView(true);
            o_browse.keepMetadataDetailViewInview();
            o_browse.onResizeMetadataDetailView();
        }
    },

    updateMetadataDetailViewTool: function(which, enabled) {
        let content = $("#op-metadata-detail-view-content");
        switch (which) {
            case "min":
                content.resizable("instance").min = enabled;
                if (enabled) {
                    $(".op-slide-minimize").addClass("op-button-disabled");
                    $(".op-slide-maximize").removeClass("op-button-disabled");
                    content.resizable("instance").max = false;
                } else {
                    $(".op-slide-minimize").removeClass("op-button-disabled");
                }
                break;
            case "max":
                content.resizable("instance").max = enabled;
                if (enabled) {
                    $(".op-slide-maximize").addClass("op-button-disabled");
                    $(".op-slide-minimize").removeClass("op-button-disabled");
                    content.resizable("instance").min = false;
                } else {
                    $(".op-slide-maximize").removeClass("op-button-disabled");
                }
                break;
            }
    },

    centerMetadataDetailViewToDefault: function(width, height) {
        let options = {};
        if (width !== undefined) {
            options.width = width;
        }
        if (height !== undefined) {
            options.height = height;
        }
        options.top = "";
        options.left = "";
        let selector = "#op-metadata-detail-view-content";
        $(selector).animate(options, function() {
            // Animation complete.
            o_browse.onResizeMetadataDetailView();
            o_browse.adjustMetadataDetailDialogPS(true);
            if ($(selector).resizable("instance").max) {
                $(this).removeAttr("style");
            }
        });
        // this separate animate takes care of recentering the dialog by setting top/left to default
        let top = $("#op-metadata-detail-view .modal-dialog").outerHeight() * 0.10;
        $("#op-metadata-detail-view .modal-dialog").animate({
            top: top,
            left: "",
        }, function () {
            if ($(selector).resizable("instance").max) {
                $(this).removeAttr("style");
            }
        });
    },

    checkForMaximizeMetadataDetailView: function(browserResize) {
        let content = $("#op-metadata-detail-view .modal-content");
        let dialog = $("#op-metadata-detail-view .modal-dialog");

        let outerWidth = content.outerWidth();
        let outerHeight = content.outerHeight();
        let padding = outerWidth - content.width();

        let maxWidth = dialog.width();
        let maxHeight = dialog.height();

        let width = (outerWidth > maxWidth ? maxWidth : outerWidth);
        let height = (outerHeight > maxHeight ? maxHeight : outerHeight);

        if (content.resizable("instance").max === true) {
            content.width(maxWidth-padding);
            content.height(maxHeight-padding);
        } else {
            let min = (Math.round(content.resizable("option").minHeight) == Math.round(height) &&
                       Math.round(content.resizable("option").minWidth) == Math.round(width));
            o_browse.updateMetadataDetailViewTool("min", min);

            let max = (Math.round(maxWidth) == Math.round(width) &&
                       Math.round(maxHeight) == Math.round(height));
            o_browse.updateMetadataDetailViewTool("max", max);
        }

        if (content.resizable("instance").min === false) {
            if (outerWidth != width) {
                content.width(width-padding);
            }
            if (outerHeight != height) {
                content.height(height-padding);
            }
        }

        content.resizable("option", "maxWidth", maxWidth);
        content.resizable("option", "maxHeight", maxHeight);
    },

    keepMetadataResizeContained: function() {
        let content = $("#op-metadata-detail-view .modal-content");

        let top = (content.offset().top < 0 ? 0 : content.offset().top);
        let left = (content.offset().left < 0 ? 0 : content.offset().left);
        let width = content.width();
        let height = content.height();

        // if the top or left has gone negative, just adjust
        if (top !== content.offset().top || left !== content.offset().left) {
            width = (content.offset().left < 0 ? width + content.offset().left : width);
            height = (content.offset().top < 0 ? height + content.offset().top : height);
            content.offset({top: top, left: left});
            content.outerWidth(width);
            content.outerHeight(height);
        } else {
            // otherwise, see if the bottom or right side are out of view
            // but don't modify top/left
            let bodyWidth = $("body").width();
            let bodyHeight = $("body").height();
            if (left + width > bodyWidth) {
                content.outerWidth(bodyWidth - left);
            }
            if (top + height > bodyHeight) {
                content.outerHeight(bodyHeight - top);
            }
        }
    },

    keepMetadataDetailViewInview: function() {
        let content = $("#op-metadata-detail-view .modal-content");
        let adjust = false;

        let top = content.offset().top;
        let left = content.offset().left;
        let bodyWidth = $("body").width();
        let bodyHeight = $("body").height() - $("footer").height();
        let width = content.outerWidth();
        let height = content.outerHeight();

        if (left < 0) {
            left = 0;
            adjust = true;
        }

        if (bodyWidth - left < width) {
            left = bodyWidth - width;
            adjust = true;
        }

        if (top < 0) {
            top = 0;
            adjust = true;
        }

        if (bodyHeight - top < height) {
            top = bodyHeight - height;
            adjust = true;
        }

        if (adjust) {
            content.offset({top: top, left: left});
        }
    },

    onResizeMetadataDetailView: function() {
        let content = $("#op-metadata-detail-view .modal-content");
        let width = content.width();
        let height = content.height();
        let resizeSmall = false;

        if ((width < 300 || height <= 400)) {
            content.addClass("op-resize-small");
            resizeSmall = true;

            // need to resize the add metadata menu as well and X in the corner
            content.find("i.fa-times-circle").removeClass("fa-lg");
            $("#op-add-metadata-fields .op-select-list").addClass("op-resize-small");
        } else {
            content.removeClass("op-resize-small");
            content.find("i.fa-times-circle").addClass("fa-lg");
            $("#op-add-metadata-fields .op-select-list").removeClass("op-resize-small");
        }
        $("#op-metadata-detail-view-content .row.bottom").removeClass(function(index, css) {
            return (css.match(/\pb-\S+/g) || []).join(' ');
        });

        //Move modal image to the top and metadata info to the bottom.
        if ((width <= 480 && height > 400) || (width <= 450)) {
            // once the modal narrows, we don't need this to wrap so remove it
            $(".op-metadata-detail-edit").removeClass("op-metadata-detail-edit-wrap");
            $(".op-metadata-detail-edit-message").removeClass("ps-0");

            $("#op-metadata-detail-view-content .row:not('.bottom')").addClass("flex-column");
            $("#op-metadata-detail-view-content .right").addClass("op-remove-col");
            $("#op-metadata-detail-view-content .row.bottom").addClass("py-0");
            $(".op-metadata-detail-view-body").addClass("py-0");

            $(".op-metadata-details-container, .op-metadata-details, .op-metadata-detail-add").addClass("ps-3");
            let paddingBottom = (height <= 360 ? "pb-2" : "pb-3");
            $("#op-metadata-detail-view-content .row.bottom").addClass(paddingBottom);
            $("#op-metadata-detail-view-content .left").removeClass("col-lg-7");
            $("#op-metadata-detail-view-content .left").addClass("col-lg-5 pt-4 pb-3");
            $("#op-metadata-detail-view-content .right").removeClass("col-lg-5");
            $("#op-metadata-detail-view-content .right").addClass("col-lg-7");
        } else {
            if ((resizeSmall && width <= 650) || (!resizeSmall && width <= 750)) {
                // wrap the edit message if it exists when narrow
                $(".op-metadata-detail-edit").addClass("op-metadata-detail-edit-wrap");
                $(".op-metadata-detail-edit-message").addClass("ps-0");
            } else {
                $(".op-metadata-detail-edit").removeClass("op-metadata-detail-edit-wrap");
                $(".op-metadata-detail-edit-message").removeClass("ps-0");
            }
            $("#op-metadata-detail-view-content .row:not('.bottom')").removeClass("flex-column");
            $("#op-metadata-detail-view-content .right").removeClass("op-remove-col");
            $("#op-metadata-detail-view-content .row.bottom").removeClass("py-0");
            $(".op-metadata-detail-view-body").removeClass("py-0");

            $(".op-metadata-details-container, .op-metadata-details, .op-metadata-detail-add").removeClass("ps-3");
            $("#op-metadata-detail-view-content .left").addClass("col-lg-7");
            $("#op-metadata-detail-view-content .left").removeClass("col-lg-5 pt-4 pb-3");
            $("#op-metadata-detail-view-content .right").addClass("col-lg-5");
            $("#op-metadata-detail-view-content .right").removeClass("col-lg-7");
        }
    },

    showMetadataDetailModal: function(opusId, obsNum) {
        if (o_browse.pageLoaderSpinnerTimer !== null) {
            // if the spinner is active, do not allow modal to become active
            return;
        }
        o_browse.loadPageIfNeeded("prev", opusId);
        o_browse.updateMetadataDetailView(opusId, obsNum);
        if (!$("#op-metadata-detail-view").hasClass("show")) {
            // this is to make sure the gallery view/slide modal is at its original position when open again
            // BUT if the gallery view modal was already open and the user is just
            // clicking on a different observation, don't recenter...
            let left = $("#op-metadata-detail-view .modal-content").position().left - $("#op-metadata-detail-view .modal-content").offset().left;
            $("#op-metadata-detail-view .modal-dialog").css({top: "", left: ""});
            $("#op-metadata-detail-view .modal-content").css({top: "", left: left});
        }
        $("#op-metadata-detail-view").modal("show");

        let tab = opus.getViewTab();
        $(`${tab} .op-thumbnail-container .op-last-modal-overlay`).addClass("op-hide-element");

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

    hideMetadataDetailModal: function() {
        $("#op-metadata-detail-view").modal("hide");
        opus.metadataDetailOpusId = "";
    },

    hideMenu: function() {
        $("#op-obs-menu").removeClass("show").hide();
    },

    hideMenus: function() {
        o_browse.hideMenu();
        o_browse.hideMetadataList();
        o_sortMetadata.hideMenu();
    },

    showMenu: function(e, opusId) {
        // make this like a default right click menu
        let tab = opus.getViewTab();
        if ($("#op-obs-menu").hasClass("show")) {
            o_browse.hideMenu();
        }
        let action = (o_cart.isIn(opusId) ? "" : "remove");
        let buttonInfo = o_browse.cartButtonInfo(action);
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
            let rangeButtonInfo = o_browse.cartButtonInfo(rangeSelected === "removerange" ? "" : "remove");
            rangeText = `<i class='fas fa-sign-out-alt fa-rotate-180'></i>End ${rangeButtonInfo[tab].rangeTitle}`;
        } else {
            rangeText = `<i class='fas fa-sign-out-alt'></i>Start ${buttonInfo[tab].rangeTitle}`;
        }

        $("#op-obs-menu .dropdown-item[data-action='range']").html(rangeText);

        let menu = {"height":$("#op-obs-menu").innerHeight(), "width":$("#op-obs-menu").innerWidth()};
        let top = ($(tab).innerHeight() - e.pageY > menu.height) ? e.pageY-5 : e.pageY-menu.height;
        let left = ($(tab).innerWidth() - e.pageX > menu.width)  ? e.pageX-5 : e.pageX-menu.width;

        // Make sure hamburger won't go off the screen
        if (top < 0) {
            top = 0;
        } else if ((top + menu.height) > $(window).height()) {
            top -= (top + menu.height - $(window).height());
        }

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
        o_browse.hideMenus();

        // If the item is selected as 'DETAIL', show the 'DETAIL' text in the corner
        // Hide any previous selected 'DETAIL' designation first... this will
        //      hide 'DETAIL' on both browse and cart
        $(".op-thumbnail-container .op-detail-overlay").addClass("op-hide-element");
        let elem = $(`[data-id='${opusId}'] .op-detail-overlay`);
        if (elem.length > 0) {
            elem.removeClass("op-hide-element");
        }

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
        o_browse.hideMetadataDetailModal();
        opus.changeTab("detail");
    },

    showPageLoaderSpinner: function() {
        if (o_browse.pageLoaderSpinnerTimer === null) {
            o_browse.pageLoaderSpinnerTimer = setTimeout(function() {
                $(".op-page-loading-status > .loader").show(); }, opus.spinnerDelay);
        }
    },

    hidePageLoaderSpinner: function() {
        if (o_browse.pageLoaderSpinnerTimer !== null) {
            // The right way to fix this is probably to reference count the on/off actions,
            // since they should always be paired, and that way the spinner won't turn off
            // until the last operation is complete. However, this sounds like a recipe for bugs,
            // and it isn't a common occurrence
            clearTimeout(o_browse.pageLoaderSpinnerTimer);
            $(".op-page-loading-status > .loader").hide();
            o_browse.pageLoaderSpinnerTimer = null;
        }
        // this is here because if the selectMetadata modal was the cause of the change AND the op-metadata-detail-view modal
        // is showing, the detail/right side of the gallery view is not done redrawing until here.
        $(".op-metadata-details > .loader").hide();
        o_utils.enableUserInteraction();
    },

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
            browseViewSelector.data("view", "data");
            // After tooltipster is initialized, if we want to change the title, we need to do it
            // by changing the content instead of updating the title attribute.
            $(".op-browse-view-tooltip").tooltipster("content", "View sortable metadata table");

            suppressScrollY = false;
        } else {
            $(`${tab} .op-gallery-view`).hide();
            $(`${tab} .op-data-table-view`).fadeIn("done", function() {o_browse.fading = false;});

            browseViewSelector.html("<i class='far fa-images'></i>&nbsp;View Gallery");
            browseViewSelector.data("view", "gallery");
            // After tooltipster is initialized, if we want to change the title, we need to do it
            // by changing the content instead of updating the title attribute.
            $(".op-browse-view-tooltip").tooltipster("content", "View sortable thumbnail gallery");

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

        let hashArray = o_hash.getHashArray();
        let slugs = hashArray.cols.split(",");

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
                    o_hash.updateURLFromCurrentHash();
                    $(".op-metadata-detail-view-body").addClass("op-disabled");
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
                viewNamespace.observationData[opusId] = item.metadata;    // for op-metadata-detail-view, store in global array
                let buttonInfo = o_browse.cartButtonInfo((item.cart_state === "cart" ? "" : "remove"));

                let mainTitle = `#${item.obs_num}: ${opusId}<br>Click to enlarge (slideshow mode)<br>Ctrl+click to ${buttonInfo[tab].title.toLowerCase()}<br>Shift+click to start/end range`;

                // gallery
                let images = item.images;
                let url = o_browse.getDetailURL(opusId);

                // DEBBY
                galleryHtml += `<div class="op-thumbnail-container ${(item.cart_state === "cart" ? 'op-in-cart' : '')}" data-id="${opusId}" data-obs="${item.obs_num}">`;
                galleryHtml += `<a href="${url}" class="thumbnail" data-image="${images.full.url}">`;
                galleryHtml += `<img class="img-thumbnail img-fluid op-browse-gallery-tooltip" src="${images.thumb.url}" alt="${images.thumb.alt_text}" title="${mainTitle}">`;

                // whenever the user clicks an image to show the modal, we need to highlight the selected image w/an icon
                galleryHtml += '<div class="op-modal-overlay">';
                galleryHtml += '<p class="content-text"><i class="fas fa-binoculars fa-4x text-info" aria-hidden="true"></i></p>';
                galleryHtml += '</div></a>';
                galleryHtml += `<div class="op-last-modal-overlay text-success op-hide-element op-browse-gallery-tooltip" title="Last viewed in slideshow mode"></div>`;

                // recycle bin icon container
                galleryHtml += `<div class="op-recycle-overlay ${((tab === "#cart" && item.cart_state === "recycle") ? '' : 'op-hide-element')} op-browse-gallery-tooltip" title="${mainTitle}">`;
                galleryHtml += '<p class="content-text"><i class="fas fa-recycle fa-4x text-success" aria-hidden="true"></i></p>';
                galleryHtml += '</div></a>';

                // detail overlay
                let hideDetail = (opus.prefs.detail === opusId ?  "" : "op-hide-element");
                galleryHtml += `<div class="op-detail-overlay text-success op-browse-gallery-tooltip ${hideDetail}" title="Shown on Detail tab"></div>`;

                galleryHtml += '<div class="op-thumb-overlay">';
                galleryHtml += `<div class="op-tools dropdown" data-id="${opusId}">`;
                galleryHtml += '<a class="op-browse-gallery-tooltip" href="#" data-icon="info" title="View observation detail (use Ctrl for new tab)"><i class="fas fa-info-circle fa-xs"></i></a>';

                galleryHtml += `<a class="op-browse-gallery-tooltip" href="#" data-icon="cart" title="${buttonInfo[tab].title}"><i class="${buttonInfo[tab].icon} fa-xs"></i></a>`;
                galleryHtml += '<a class="op-browse-gallery-tooltip" href="#" data-icon="menu" title="More options"><i class="fas fa-bars fa-xs"></i></a>';
                galleryHtml += '</div>';
                galleryHtml += '</div></div>';

                // table row
                let checked = item.cart_state === "cart" ? " checked" : "";
                let recycled = (tab === "#cart" && item.cart_state === "recycle") ? "class='text-success op-recycled'" : "";
                let checkbox = `<input type="checkbox" name="${opusId}" value="${opusId}" class="multichoice"${checked}/>`;
                let minimenu = `<a class="op-browse-table-tooltip" href="#" data-icon="menu" title="More options"><i class="fas fa-bars fa-xs"></i></a>`;
                let row = `<td class="op-table-tools"><div class="op-tools mx-0 form-group op-browse-table-tooltip" title="Click to ${buttonInfo[tab].title.toLowerCase()}<br>Shift+click to start/end range" data-id="${opusId}">${checkbox} ${minimenu}</div></td>`;

                let miniThumbnail = `<img class="op-browse-table-tooltip" src="${images.thumb.url}" alt="${images.thumb.alt_text}" title="${mainTitle}">`;
                row += `<td class="op-mini-thumbnail op-mini-thumbnail-zoom"><div>${miniThumbnail}</div></td>`;

                let tr = `<tr class="op-browse-table-tooltip" data-id="${opusId}" ${recycled} data-bs-target="#op-metadata-detail-view" data-obs="${item.obs_num}" title="${mainTitle}">`;
                $.each(item.metadata, function(index, cell) {
                    let slug = slugs[index];
                    row += `<td class="op-metadata-value" data-slug="${slug}">${cell}</td>`;
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

        let lastViewedOpusId = opus.getViewNamespace().lastMetadataDetailOpusId;
        let elem = $(`${tab} [data-id='${lastViewedOpusId}'] .op-last-modal-overlay`);
        if (elem.length > 0) {
            elem.removeClass("op-hide-element");
        }

        // we must always use the op-metadata-detail-view infinite scroll object for the rangeSelectOpusID because we only
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
        o_hash.updateURLFromCurrentHash();
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

        opus.colLabels = columns;
        opus.colLabelsNoUnits = columnsNoUnits;

        // check all box
        let addallIcon = "<button type='button'" +
                         "class='op-table-header-addall btn btn-link op-icon-tooltip-addall'" +
                         " title='Add All Results to Cart'>" +
                         "<i class='fas fa-cart-plus' data-action='addall'></i></button>";

        let tableHeaderFirstCol = `<th scope='col' class='sticky-header op-table-first-col'><div>${addallIcon}</div></th>`;
        // note: this column header will be empty
        let tableHeaderThumbnailCol = `<th scope='col' class='sticky-header op-table-first-col'></th>`;
        $(`${tab} .op-data-table-view thead`).append("<tr></tr>");
        $(`${tab} .op-data-table-view thead tr`).append(tableHeaderFirstCol);
        $(`${tab} .op-data-table-view thead tr`).append(tableHeaderThumbnailCol);

        $.each(columns, function(index, header) {
            let slug = slugs[index];

            // Store label (without units) of each header in data-label attributes
            let label = columnsNoUnits[index];

            // Assigning data attribute for table column sorting
            let positionAsc = $.inArray(slug, order);
            let positionDesc = $.inArray("-"+slug, order);

            let icon = "";
            let columnSorting = "none";
            let columnOrderPostion = "";
            let positionIndicatorClasses = "op-sort-position-indicator text-primary ms-1 font-xs";
            //let reorderTip = "Drag to reorder\n";
            let reorderTip = "";
            let orderToolTip = (opus.prefs.order.length < 9 ? `title='${reorderTip}Click to sort on this field<br>Ctrl+click to append to current sort'` : "title='Too many sort fields'");

            if (positionAsc >= 0) {
                orderToolTip = `title='${reorderTip}Change to descending sort'`;
                columnSorting = "asc";
                icon =  "-down";
                columnOrderPostion = `<span class="${positionIndicatorClasses}">${positionAsc+1}</span>`;
            } else if (positionDesc >= 0) {
                orderToolTip = `title='${reorderTip}Change to ascending sort'`;
                columnSorting = "desc";
                icon = "-up";
                columnOrderPostion = `<span class="${positionIndicatorClasses}">${positionDesc+1}</span>`;
            }

            let headerArr = header.split(" ");
            let lastWord = headerArr.pop();
            let spacing = headerArr.length ? "&nbsp;" : "";
            let lastWordWrappingGroup = `${headerArr.join(" ")}${spacing}<span class="op-last-word-group">${lastWord}` +
                                        `<span data-sort="${columnSorting}" class="op-column-ordering fas fa-sort${icon}">${columnOrderPostion}</span>`;
            let columnOrdering = `<a class="op-data-table-tooltip" href="" data-slug="${slug}" ${orderToolTip} data-label="${label}">${lastWordWrappingGroup}</a>`;

            $(`${tab} .op-data-table-view thead tr`).append(`<th id="${slug}" scope="col" class="op-draggable sticky-header"><div>${columnOrdering}</div></th>`);
        });

        o_browse.initResizableColumn(tab);
        //o_browse.initDraggableColumn(tab);

        // Init addall icon tooltip in the browse table
        $(`${tab} .op-icon-tooltip-addall, ${tab} .op-data-table-tooltip`).tooltipster({
            maxWidth: opus.tooltipsMaxWidth,
            theme: opus.tooltipsTheme,
            delay: opus.tooltipsDelay,
            contentAsHTML: true,
        });
    },

    initResizableColumn: function(tab) {
        $(`${tab} .op-data-table th div:not(:first)`).resizable({
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

    initDraggableColumn: function(tab) {
        function moveColumn(table, from, to) {
            let rows = $('tr', table);
            rows.each(function() {
                let cols = $(this).children("td");
                cols.eq(from).detach().insertBefore(cols.eq(to));
            });
        }

        let borderRightWidth = "border-right-width: 15px";
        $(`${tab} .op-data-table thead tr`).sortable({
            items: "th.op-draggable",
            axis: "x",
            cursor: "grab",
            containment: "parent",
            tolerance: "pointer",
            helper: function(e, ui) {
                // maintain width of all headers while moving
                $(e.currentTarget).find("th").each(function() {
                    $(this).width($(this).width());
                });

                return ui.clone();
            },
            stop: function(e, ui) {
                o_browse.isSortingHappening = false;
                let columnOrder = $(this).sortable("toArray");

                // only bother if something actually changed...
                if (!o_utils.areObjectsEqual(opus.prefs.cols, columnOrder)) {
                    let initialCol = opus.prefs.cols.indexOf(ui.item.attr("id")) + 2;
                    let finalCol = columnOrder.indexOf(ui.item.attr("id")) + 2;
                    moveColumn(".op-data-table", initialCol, finalCol);

                    opus.prefs.cols = o_utils.deepCloneObj(columnOrder);
                    o_hash.updateURLFromCurrentHash(); // This makes the changes visible to the user
                    o_sortMetadata.renderSortedDataFromBeginning();
                }
                $(".op-data-table th:last-child").css(borderRightWidth);
                $("tbody").animate({opacity: '1'});
            },
            start: function(e, ui) {
                // There is a tiny width difference (2px) between .ui-sortable-placeholder and the helper. This will
                // prevent the little table width shifting when sorting starts (all header texts are single line).
                ui.placeholder.width(ui.helper.width());

                $("tbody").animate({opacity: '0.1'});
                o_browse.hideTableMetadataTools();
                o_browse.isSortingHappening = true;
            },
        });
    },

    // number of images that can be fit in current window size
    getLimit: function(view) {
        // default the function to use to be the one in o_browse because there is not one available in o_search
        let galleryBoundingRect = opus.getViewNamespace(view).galleryBoundingRect;
        return (galleryBoundingRect.x * galleryBoundingRect.yCeil);
    },

    getDataURL: function(view, startObs, customizedLimitNum=undefined) {
        let base_url = "/opus/__api/dataimages.json?";
        // We use getFullHashStr instead of getHash because we want the updated
        // version of cols= even if the main URL hasn't been updated yet
        let hashString = o_hash.getFullHashStr();

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
        if ($("#op-metadata-detail-view").hasClass("show")) {
            if (delOpusId === $(".op-metadata-detail-view-body .op-cart-toggle").data("id")) {
                o_browse.hideMetadataDetailModal();
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

                    let path = o_browse.getDataURL(view, obsNum, customizedLimitNum);
                    let totalObs = viewNamespace.totalObsCount;
                    // When it reaches to the end of the search data, disable loadOnScroll so that it
                    // will not keep calling dataimages.json api with startObs larger the search results.
                    if (infiniteScrollData) {
                        if (obsNum > totalObs ) {
                            $(`${tab} .op-gallery-view`).infiniteScroll({"loadOnScroll": false});
                            $(`${tab} .op-data-table-view`).infiniteScroll({"loadOnScroll": false});
                        } else {
                            $(`${tab} .op-gallery-view`).infiniteScroll({"loadOnScroll": true});
                            $(`${tab} .op-data-table-view`).infiniteScroll({"loadOnScroll": true});
                        }
                    }
                    return path;
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

                loadOnScroll: true,
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

    loadData: function(view, closeMetadataDetailView=true, startObs=undefined, customizedLimitNum=undefined) {
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

        // Only show "Add all results to cart" in browse tab.
        if (tab === "#cart") {
            $("#op-obs-menu .dropdown-item[data-action='addall']").addClass("op-hide-element");
        } else {
            $("#op-obs-menu .dropdown-item[data-action='addall']").removeClass("op-hide-element");
        }

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

        if (closeMetadataDetailView) {
            o_browse.hideMetadataDetailModal();
        }
        o_browse.showPageLoaderSpinner();

        // Note: Increment the reqno here instead of getDataURL because infiniteScroll path also uses
        // getDataURL, and we don't want to increment the reqno for the infiniteScroll URL.
        opus.lastLoadDataRequestNo[view] += 1;
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

            if (closeMetadataDetailView) {
                o_browse.hideMetadataDetailModal();
            }
            o_browse.renderGalleryAndTable(data, this.url, view);
            // Initialize tooltips using tooltipster in browse gallery and table
            // Since we didn't set functionPosition, the tooltip will always open
            // in the middle of the gallery view's top edge.
            $(`${tab} .op-browse-gallery-tooltip`).tooltipster({
                maxWidth: opus.tooltipsMaxWidth,
                theme: opus.tooltipsTheme,
                delay: opus.tooltipsDelay,
                contentAsHTML: true,
            });
            $(`${tab} .op-browse-table-tooltip`).tooltipster({
                maxWidth: opus.tooltipsMaxWidth,
                theme: opus.tooltipsTheme,
                delay: opus.tooltipsDelay,
                contentAsHTML: true,
                functionBefore: function(instance, helper){
                    // Make sure all other tooltips are closed before a new one is opened
                    // in table view.
                    $.each($.tooltipster.instances(), function(i, inst){
                        inst.close();
                    });
                },
                // Make sure the tooltip position is next to the cursor when users
                // move around the same row in the browse table view. Without this
                // function, the tooltip will always open in the middle of the row.
                functionPosition: function(instance, helper, position){
                    return o_utils.setPreviewImageTooltipPosition(helper, position);
                }
            });

            if (opus.metadataDetailOpusId !== "") {
                o_browse.metadataboxHtml(opus.metadataDetailOpusId, view);
            }
            o_sortMetadata.updateSortOrder(data);

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
        if (opus.metadataDetailOpusId !== "" &&
            !$(".op-metadata-detail-view-body .op-prev").data("id") &&
            $(".op-metadata-detail-view-body .op-prev").hasClass("op-button-disabled")) {
            let prev = $(`${tab} tr[data-id=${opus.metadataDetailOpusId}]`).prev("tr");
            prev = (prev.data("id") ? prev.data("id") : "");

            $(".op-metadata-detail-view-body .op-prev").data("id", prev);
            $(".op-metadata-detail-view-body .op-prev").toggleClass("op-button-disabled", (prev === ""));
        }

        // Update to make next button appear when prefetching next page is done
        if (opus.metadataDetailOpusId !== "" &&
            !$(".op-metadata-detail-view-body .op-next").data("id") &&
            $(".op-metadata-detail-view-body .op-next").hasClass("op-button-disabled")) {
            let next = $(`${tab} tr[data-id=${opus.metadataDetailOpusId}]`).next("tr");
            next = (next.data("id") ? next.data("id") : "");

            $(".op-metadata-detail-view-body .op-next").data("id", next);
            $(".op-metadata-detail-view-body .op-next").toggleClass("op-button-disabled", (next === ""));
        }

        // if left/right arrow are disabled, make them clickable again
        $(".op-metadata-detail-view-body").removeClass("op-disabled");
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
        o_selectMetadata.render();   // just do this in background so there's no delay when we want it...
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
            // Note: in table view, if there is more than one row, we divide by the 2nd table tr's
            // height because in Firefox & Safari, the first table tr's height will be 1px larger
            // than rest of tr, and this will mess up the calculation.
            let tableRowHeight = ($(`${tab} .op-data-table tbody tr[data-obs]`).length === 1 ?
                                  $(`${tab} .op-data-table tbody tr[data-obs]`).outerHeight() :
                                  $(`${tab} .op-data-table tbody tr[data-obs]`).eq(1).outerHeight());
            trCountFloor = o_utils.floor((height-$(`${tab} .op-data-table th`).outerHeight()) / tableRowHeight);
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
        let footerHeight = $(".footer").outerHeight();
        let mainNavHeight = $("#op-main-nav").outerHeight();
        let navbarHeight = $(`${tab} .panel-heading`).outerHeight();
        // The main navbar (#op-main-nav) and the 2nd navbar (.panel-heading) have an overlapping
        // area, need to take this overlapped height into consideration when doing the calculation.
        // This will make sure there is no gap between the end of .op-gallery-contents and .footer.
        let navOverlappedHeight = $("#op-main-nav").offset().top + mainNavHeight -
                                  $(`${tab} .panel-heading`).offset().top;
        let totalNonGalleryHeight = footerHeight + mainNavHeight + navbarHeight - navOverlappedHeight;

        return $(window).height()-totalNonGalleryHeight;
    },

    calculateGalleryWidth: function(view) {
        let tab = opus.getViewTab(view);
        // This is the width of container that contains all thumbnail images.
        let width = $(`${tab} .op-gallery-contents .gallery`).width();
        if (width <= 0) {
            width = $(window).width();
            if (tab === "#cart") {
                let leftPanelWidth = parseInt($(".op-cart-details").css("min-width"));
                width -= leftPanelWidth;
            }
        }
        return width;
    },

    updateImageSize: function() {
        /**
         * Update the thumbnail image size based on the browser size.
         * The default value & updated value need to match min-height & min-width
         * values assigned to .op-thumbnail-container in opus.css.
         */
        if ($(window).width() <= opus.browserThresholdWidth ||
            $(window).height() <= opus.browserThresholdHeight) {
            // udpated thumbnail size: 90x90
            o_browse.imageSize = 90;
        } else {
            // default thumbnail size: 100x100
            o_browse.imageSize = 100;
        }
    },

    adjustBrowseHeight: function(browserResized=false, isDOMChanged=false) {
        let tab = opus.getViewTab();
        let view = opus.prefs.view;
        o_sortMetadata.hideMenu();

        // Check screen size and update o_browse.imageSize
        o_browse.updateImageSize();
        let containerHeight = o_browse.calculateGalleryHeight();
        $(`${tab} .op-gallery-contents`).height(containerHeight);
        $(`${tab} .op-gallery-contents .op-gallery-view`).height(containerHeight);

        let viewNamespace = opus.getViewNamespace();
        viewNamespace.galleryScrollbar.update();
        viewNamespace.galleryBoundingRect = o_browse.countGalleryImages();

        // make sure slider is updated when window is resized
        o_browse.updateSliderHandle(view, browserResized, isDOMChanged);

        // if the browser is past the @media break both vertically and horizontally,
        // close the download data panel
        if (o_cart.isScreenNarrow()) {
            if (o_cart.isScreenShort()) {
                opus.hideHelpAndCartPanels();
            }
            $(".op-download-links-btn").html("Download Not Available");
            $(".op-download-links-btn").addClass("op-a-tag-btn-disabled");
            $(".footer .op-download-links-btn").popover("hide");
        } else {
            $(".op-download-links-btn").html("Download Links History");
            if ($(".op-zipped-files > li").length > 1) {
                $(".op-download-links-btn").removeClass("op-a-tag-btn-disabled");
            }
        }
    },

    adjustTableSize: function() {
        let tab = opus.getViewTab();
        let containerWidth = $(`${tab} .op-gallery-contents`).width();
        let containerHeight = $(`${tab} .op-gallery-contents`).height();
        $(`${tab} .op-data-table-view`).width(containerWidth);
        $(`${tab} .op-data-table-view`).height(containerHeight);
        o_browse.hideMetadataList();
        o_browse.hideTableMetadataTools();
        opus.getViewNamespace().tableScrollbar.update();
    },

    adjustMetadataDetailDialogPS: function() {
        if (o_browse.isSortingHappening) {
            return;
        }
        // if we are in verical column mode, calculate the container height differently
        let containerHeight = ($("#op-metadata-detail-view-content .row").hasClass("flex-column") ? $(".op-metadata-detail-view-body .right").height() : $(".op-metadata-detail-view-body").height());
        let modalEditHeight = $(".op-metadata-detail-edit").outerHeight(true);
        let bottomRowHeight = $(".op-metadata-detail-view-body .bottom").outerHeight(true);
        let calculatedContainerHeight = containerHeight - modalEditHeight - bottomRowHeight;

        let container = ".op-metadata-detail-view-body .op-metadata-details";
        $(container).height(calculatedContainerHeight);
        // update the containerHeight w/the actual value for deciding to enable/disable PS
        containerHeight = $(container).height();
        let browseDialogHeight = $(".op-metadata-detail-view-body .op-metadata-details .contents").height();
        let slug = $("#op-add-metadata-fields").data("slug");
        if (slug !== undefined) {
            let currentElement = $(`ul[data-slug="${slug}"] a.op-metadata-detail-add`);
            // could have been deleted in interim, so best to check beforehand...
            if (currentElement !== undefined && $(currentElement).position() !== undefined) {
                let top = o_browse.adjustTopOfMetadataList(currentElement);
                $("#op-add-metadata-fields").css("top", top);
            }
        }

        if (o_browse.modalScrollbar) {
            o_browse.hideMetadataList();
            if (containerHeight > browseDialogHeight) {
                if (!$(".op-metadata-detail-view-body .op-metadata-details .ps__rail-y").hasClass("hide_ps__rail-y")) {
                    $(".op-metadata-detail-view-body .op-metadata-details .ps__rail-y").addClass("hide_ps__rail-y");
                    o_browse.modalScrollbar.settings.suppressScrollY = true;
                }
            } else {
                $(".op-metadata-detail-view-body .op-metadata-details .ps__rail-y").removeClass("hide_ps__rail-y");
                o_browse.modalScrollbar.settings.suppressScrollY = false;
                let lastAddedSlug = $("#op-add-metadata-fields").data("last");
                if (lastAddedSlug !== undefined) {
                    let addedElement =  $(`ul[data-slug="${lastAddedSlug}"]`);
                    // if any part of the newly added element is not on the screen, move the scrollbar down
                    if (!addedElement.isOnScreen($(container), 0)) {
                        let scrollUp = $(addedElement).height() + $(container).scrollTop();
                        $(container).scrollTop(scrollUp);
                    }
                }
            }
            // X-scrolling is not allowed in metadata detail modal.
            o_browse.modalScrollbar.settings.suppressScrollX = true;
            o_browse.modalScrollbar.update();
        }
        $("#op-add-metadata-fields").removeData("last");
    },

    cartButtonInfo: function(action) {
        let browse_icon = "fas fa-cart-plus";
        let browse_title = "Add to cart";
        let browse_rangeTitle = "add range";
        let cart_icon = "fas fa-undo";
        let cart_title = "Restore from recycle bin";
        let cart_rangeTitle = "restore range from recycle bin";
        if (action !== "remove") {
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
            $(`${tab} ${selector}`).tooltipster("content", buttonInfo[tab].title);
        });

        let tab = opus.getViewTab();
        let modalCartSelector = `.op-metadata-detail-view-body .bottom .op-cart-toggle[data-id=${opusId}]`;
        if ($("#op-metadata-detail-view").is(":visible") && $(modalCartSelector).length > 0) {
            $(modalCartSelector).html(`<i class="${buttonInfo[tab].icon} fa-2x"></i>`);
            $(modalCartSelector).tooltipster("content", `${buttonInfo[tab].title} (or press spacebar)`);
        }
    },

    getNextPrevHandles: function(opusId) {
        let tab = opus.getViewTab();
        let idArray = $(`${tab} .op-thumbnail-container[data-obs]`).map(function() {
            return $(this).data("id");
        });
        let next = $.inArray(opusId, idArray) + 1;
        next = (next < idArray.length ? idArray[next] : "");

        let prev = $.inArray(opusId, idArray) - 1;
        prev = (prev < 0 ? "" : idArray[prev]);

        return {"next": next, "prev": prev};
    },

    showTableMetadataTools: function(e, slug) {
        let tab = opus.getViewTab();
        let targetElem = e.currentTarget;
        let toolElem = `${tab} .op-edit-field-tool`;
        let left = $(targetElem).position().left +
                    $(`${tab} .op-data-table-view .table`).offset().left;
        let top = $(targetElem).offset().top +
                  $(targetElem).outerHeight();

        if (tab === "#cart") {
            if ($(".op-cart-details:visible").length > 0) {
                // need to calculate a new offset if the table has scrolled left behind the details window
                left -= $(".op-cart-details").outerWidth() + $(".op-cart-details").offset().left;
            } else {
                // when the details are collapsed, need to use the offset instead of position
                left = $(targetElem).offset().left +
                       $(`${tab} .op-data-table-view`).position().left -
                       $(`${tab} .op-data-table-view`).offset().left;
            }
            // because the cart is in a container, we need to account for the nav
            // there is a bit of overlap between the top of the cart gallery and navbar
            let offset = $("#op-main-nav").outerHeight() - $(".op-cart-gallery-side").offset().top;
            top -= $("#op-main-nav").outerHeight() - offset;
        }
        let width = $(targetElem).outerWidth();

        // need to adjust for the PerfectScrollbar overlaying a bit on the last field
        let lastSlug = opus.prefs.cols[opus.prefs.cols.length - 1];
        if (slug === lastSlug) {
            width -= $(`${tab} .op-data-table-view .ps__thumb-y`).width();
        }
        o_browse.checkForEmptyMetadataList();

        $(toolElem).css({
            display: "block",
            top: top,
            left: left,
            width: width,
            transform: "none",
        }).fadeIn("slow");

        $(toolElem).data("slug", slug);
    },

    hideTableMetadataTools: function() {
        let tab = opus.getViewTab();
        $(`${tab} .op-edit-field-tool`).removeClass("show").hide();
    },

    onDoneUpdateFromTableMetadataDetails: function(e) {
        o_utils.disableUserInteraction();
        o_hash.updateURLFromCurrentHash(); // This makes the changes visible to the user
        if (opus.prefs.cols.length <= 1) {
            $("a.op-metadata-detail-remove").addClass("op-button-disabled");
        } else {
            $("a.op-metadata-detail-remove").removeClass("op-button-disabled");
        }
        o_selectMetadata.saveChanges();
        o_selectMetadata.reRender();
        o_browse.hideMetadataList();
        o_browse.hideTableMetadataTools();
    },

    hideMetadataList: function() {
        $("#op-add-metadata-fields").removeClass("show").hide();
    },

    adjustTopOfMetadataList: function(elem) {
        let top = $(elem).offset().top;
        // if this is coming from the slideshow view, calulate the top differently
        if ($(elem).hasClass("op-metadata-details-tools")) {
            let menuHeight = $("#op-add-metadata-fields .op-select-list").height();
            let adjustedTop = top - (menuHeight + $(elem).height());
            top = (adjustedTop > 0 ? adjustedTop : top);
        }
        return top;
    },

    showMetadataList: function(e) {
        let targetPosition = $(e.currentTarget).offset();
        let top = o_browse.adjustTopOfMetadataList(e.currentTarget);
        let left = targetPosition.left + Math.ceil($(".fa-plus").outerWidth());
        let menuWidth = $("#op-add-metadata-fields").outerWidth();
        let tableWidth = $(".op-data-table-view").outerWidth();
        if (left + menuWidth > tableWidth) {
            left = targetPosition.left - menuWidth;
        }

        $("#op-add-metadata-fields").css({
            display: "block",
            top: top,
            left: left,
        }).addClass("show");
    },

    onDoneUpdateMetadataDetails: function(e) {
        o_utils.disableUserInteraction();
        let columnOrder = $.map($(".op-metadata-details ul"), function(n, i) {
            return $(n).data("slug");
        });
        // only bother if something actually changed...
        if (!o_utils.areObjectsEqual(opus.prefs.cols, columnOrder)) {
            opus.prefs.cols = o_utils.deepCloneObj(columnOrder);
            o_hash.updateURLFromCurrentHash(); // This makes the changes visible to the user
            // passing in false indicates to not close the gallery view on loadData
            o_selectMetadata.saveChanges();
            o_selectMetadata.reRender();
        } else {
            o_utils.enableUserInteraction();
        }
        o_browse.hideMetadataList();
    },

    initEditMetadataDetails: function() {
        let viewNamespace = opus.getViewNamespace();

        $(".op-edit-metadata-button").attr("action", "done").html(`<i class="fas fa-pencil-alt"></i> Done`);
        $(".op-metadata-detail-view-body .op-metadata-details .contents").sortable({
            items: "ul",
            cursor: "grabbing",
            containment: "parent",
            tolerance: "pointer",
            helper: "clone",
            stop: function(e, ui) {
                o_browse.onDoneUpdateMetadataDetails();
                o_browse.isSortingHappening = false;
            },
            start: function(e, ui) {
                ui.placeholder.height(ui.helper.height());
                o_widgets.getMaxScrollTopVal(e.target);
                o_browse.isSortingHappening = true;
            },
            sort: function(e, ui) {
                o_widgets.preventContinuousDownScrolling(e.target);
            },
        }).addClass("op-no-select");
        $(".op-detail-data").fadeTo("fast", 0.15);
        $(".op-metadata-details-tools").show();
        $(".op-metadata-detail-edit-message").show();
        $(".op-metadata-details").addClass("op-metadata-details-edit-enabled");
        if ($("a.op-metadata-detail-remove").length <= 1) {
            $("a.op-metadata-detail-remove").addClass("op-button-disabled");
        }
        o_browse.checkForEmptyMetadataList();
        viewNamespace.metadataDetailEdit = true;
    },

    checkForEmptyMetadataList: function() {
        // if there is only one metadata field left, disable the trash in both the slide show and table tools dropdown
        if ($(".op-select-list .op-search-menu").find("li").length === 0) {
            $(".op-metadata-detail-add").addClass("op-button-disabled");
        } else {
            $(".op-metadata-detail-add").removeClass("op-button-disabled");
        }
    },

    removeEditMetadataDetails: function() {
        let viewNamespace = opus.getViewNamespace();
        let detailContents = $(".op-metadata-detail-view-body .op-metadata-details .contents");

        detailContents.removeClass("op-no-select");
        $(".op-edit-metadata-button").attr("action", "edit").html(`<i class="fas fa-pencil-alt"></i> Edit`);
        $(".op-metadata-details").removeClass("op-metadata-details-edit-enabled");
        $(".op-metadata-details-tools").hide();
        $(".op-metadata-detail-edit-message").hide();
        if (detailContents.sortable("instance") !== undefined) {
            detailContents.sortable("destroy");
        }
        $(".op-detail-data").fadeTo("fast", 1);
        viewNamespace.metadataDetailEdit = false;
    },

    moveToNextMetadataSlide: function(obsNum, direction) {
        let viewNamespace = opus.getViewNamespace();
        if (obsNum >= 0 && obsNum <= viewNamespace.totalObsCount) {
            let tab = opus.getViewTab();
            let lastCachedObsNum = $(`${tab} .op-thumbnail-container`).last().data("obs");
            let detailOpusId;
            // Only allow the down/next arrow keys to proceed to the next row of observations if either we are at the end of total observations
            // OR if we are not yet at the end of the cached observations and waiting for the fetch to update the DOM
            // This is to prevent the alignment of the bottom row of the gallery view when we hit the end of the cached observations in the DOM,
            // which causes some unsigtly momentary jumping around
            if (lastCachedObsNum === viewNamespace.totalObsCount || obsNum + viewNamespace.galleryBoundingRect.x <= lastCachedObsNum) {
                detailOpusId = (o_browse.isGalleryView() ? $(tab).find(`.op-thumbnail-container[data-obs='${obsNum}']`).data("id") : $(tab).find(`tr[data-obs='${obsNum}']`).data("id"));
                o_browse.removeEditMetadataDetails();
                o_browse.loadPageIfNeeded(direction, detailOpusId);
                o_browse.updateMetadataDetailView(detailOpusId, obsNum);
            }
        }
    },

    metadataboxHtml: function(opusId, view) {
        let viewNamespace = opus.getViewNamespace(view);
        opus.metadataDetailOpusId = opusId;

        // list columns + values
        let html = "";
        let selectMetadataTitle = "Add metadata field after the current field";
        let removeTool = `<li class="op-metadata-details-tools me-2">` +
                         `<a href="#" class="op-metadata-detail-remove op-metadatabox-edit-tooltip" me-2 title="Remove selected metadata field"><i class="far fa-trash-alt"></i></a></li>`;
        let addTool = `<a href="#" class="op-metadata-details-tools op-metadata-detail-add op-metadatabox-edit-tooltip" title="${selectMetadataTitle}" data-bs-toggle="dropdown" role="button"><i class="fas fa-plus pe-1"> Add field here</i></a>`;
        $.each(opus.colLabels, function(index, columnLabel) {
            if (opusId === "" || viewNamespace.observationData[opusId] === undefined || viewNamespace.observationData[opusId][index] === undefined) {
                opus.logError(`metadataboxHtml: in each, observationData may be out of sync with colLabels; opusId = ${opusId}, colLabels = ${opus.colLabels}`);
            } else {
                let slug = opus.prefs.cols[index];
                let style = (viewNamespace.metadataDetailEdit ? `style="opacity: 0.15"` : "");
                let value = `<span class="op-detail-data" ${style}>${viewNamespace.observationData[opusId][index]}</span>`;
                html += `<ul class="list-inline mb-2" data-slug="${slug}">${removeTool}`;
                html += `<li class="op-metadata-detail-item">`;
                html += `<div class="op-metadata-term fw-bold">${columnLabel}:</div>`;
                html += `<div class="op-metadata-data ms-0">${value}${addTool}</div>`;
                html += `</li></ul>`;
            }
        });
        $(".op-metadata-detail-view-body .op-metadata-details .contents").html(html);

        // Initialize tooltips for:
        // - "+" and "trash" icons in the edit menu of metadata box
        // - "x" icon in the metadata box
        $(".op-metadatabox-edit-tooltip").tooltipster({
            maxWidth: opus.tooltipsMaxWidth,
            theme: opus.tooltipsTheme,
            delay: opus.tooltipsDelay,
        });

        // if it was last in edit mode, open in edit mode...
        if (viewNamespace.metadataDetailEdit) {
            o_browse.initEditMetadataDetails();
        } else {
            o_browse.removeEditMetadataDetails();
        }
    },

    updateMetadataDetailView: function(opusId, obsNum) {
        if (opusId) {
            let tab = opus.getViewTab();

            let nextPrevHandles = o_browse.getNextPrevHandles(opusId);
            let action = o_cart.isIn(opusId) ? "" : "remove";
            let buttonInfo = o_browse.cartButtonInfo(action);

            // prev/next buttons - put this in op-metadata-detail-view html...
            let html = `<div class="col"><a href="#" class="op-cart-toggle op-metadatabox-tooltip" data-id="${opusId}" title="${buttonInfo[tab].title} (or press spacebar)"><i class="${buttonInfo[tab].icon} fa-2x float-left"></i></a></div>`;
            html += `<div class="col text-center op-obs-direction">`;
            let opPrevDisabled = (nextPrevHandles.prev == "" ? "op-button-disabled" : "");
            let opNextDisabled = (nextPrevHandles.next == "" ? "op-button-disabled" : "");
            html += `<a href="#" class="op-prev text-center ${opPrevDisabled} op-metadatabox-tooltip" data-id="${nextPrevHandles.prev}" title="Previous image: ${nextPrevHandles.prev} (left arrow key)"><i class="far fa-arrow-alt-circle-left fa-2x"></i></a>`;
            html += `<a href="#" class="op-next ${opNextDisabled} op-metadatabox-tooltip" data-id="${nextPrevHandles.next}" title="Next image: ${nextPrevHandles.next} (right arrow key)"><i class="far fa-arrow-alt-circle-right fa-2x"></i></a>`;
            html += `</div>`;

            // mini-menu like the hamburger on the observation/gallery page
            html += `<div class="col text-start"><a href="#" class="menu pe-3 float-end text-center op-metadatabox-tooltip" data-bs-toggle="dropdown" role="button" data-id="${opusId}" title="More options"><i class="fas fa-bars fa-2x"></i></a></div>`;
            $(".op-metadata-detail-view-body .bottom").html(html);

            // update the binoculars here
            $(tab).find(".op-modal-show").removeClass("op-modal-show");
            $(tab).find(`[data-id='${opusId}'] div.op-modal-overlay`).addClass("op-modal-show");
            $(tab).find(`tr[data-id='${opusId}']`).addClass("op-modal-show");
            // if the observation is in the recycle bin, move the icon over a bit so there is not conflict w/the binoculars
            $(tab).find(`[data-id='${opusId}'] div.op-recycle-overlay`).addClass("op-modal-show");

            let imageURL = $(tab).find(`[data-id='${opusId}'] > a.thumbnail`).data("image");
            let title = `#${obsNum}: ${opusId}<br>Click for full-size image`;

            o_browse.metadataboxHtml(opusId);
            $(".op-metadata-detail-view-body .left").html(`<a href="${imageURL}" target="_blank"><img src="${imageURL}" title="${title}" class="op-slideshow-image-preview op-metadatabox-img-tooltip"/></a>`);
            $(".op-metadata-detail-view-body .op-obs-direction a").data("obs", obsNum);

            // Initialize tooltips for cart, hamburger, prev, and next icons in metadata box
            $(".op-metadatabox-tooltip").tooltipster({
                maxWidth: opus.tooltipsMaxWidth,
                theme: opus.tooltipsTheme,
                delay: opus.tooltipsDelay,
            });

            $(".op-metadatabox-img-tooltip").tooltipster({
                maxWidth: opus.tooltipsMaxWidth,
                theme: opus.tooltipsTheme,
                delay: opus.tooltipsDelay,
                contentAsHTML: true,
                onlyOne: true,
                // Make sure the tooltip position is next to the cursor when users mouse
                // over to the metadatabox image.
                functionPosition: function(instance, helper, position){
                    return o_utils.setPreviewImageTooltipPosition(helper, position);
                }
            });
        }
    },

    clearObservationData: function(leaveStartObs) {
        if (!leaveStartObs) {
            // Normally when we delete all the data we want to force a return to the top because
            // we don't know what data is going to be loaded. But in some circumstances
            // (like updating metadata columns) we know we're going to reload exactly the same
            // data so we can keep our place.
            opus.prefs.startobs = 1; // reset startobs to 1 when data is flushed
            opus.prefs.cart_startobs = 1;
            $(".op-gallery-view").infiniteScroll({"scrollbarObsNum": 1});
            $(".op-gallery-view").infiniteScroll({"sliderObsNum": 1});
            $(".op-data-table-view").infiniteScroll({"scrollbarObsNum": 1});
            $(".op-data-table-view").infiniteScroll({"sliderObsNum": 1});
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

    downloadCSV: function(obj) {
        let selectionsHashStr = o_hash.getHashStrFromSelections();
        if (selectionsHashStr !== "") {
            selectionsHashStr += "&";
        }
        let colStr = opus.prefs.cols.join(',');
        let resultCountStr = o_browse.totalObsCount.toString();
        let orderStr = opus.prefs.order.join(",");
        let csvLink = `/opus/__api/data.csv?${selectionsHashStr}cols=${colStr}&limit=${resultCountStr}&order=${orderStr}`;
        $(obj).attr("href", csvLink);
    },
};
