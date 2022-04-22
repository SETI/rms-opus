/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* globals $, DEFAULT_SORT_ORDER */
/* globals o_hash, o_browse, o_utils, opus */

// font awesome icon class
const pillSortUpArrow = "fas fa-arrow-circle-up";
const pillSortDownArrow = "fas fa-arrow-circle-down";
const tableSortUpArrow = "fas fa-sort-up";
const tableSortDownArrow = "fas fa-sort-down";

let o_sortMetadata = {
    /**
    *
    *  all the things that happen when editting the sort on metadata
    *
    **/
    addBehaviours: function() {
        $(".op-sort-order-icon").attr("title", "Results are sorted by these metadata fields\nClick to reset sort fields to default");
        $(".op-sort-contents").sortable({
            items: "div.op-sort-only",
            cursor: "grab",
            containment: "parent",
            helper: "clone",
            tolerance: "intersect",
            cancel: ".op-no-sort",
            stop: function(event, ui) {
                // rebuild new search order and reload page
                let newOrder = [];
                $(this).find(".list-inline-item span.rounded-pill ").each(function(index, obj) {
                    let slug = $(obj).data("slug");
                    let descending = ($(obj).data("descending") === true ? "-" : "");
                    newOrder.push(`${descending}${slug}`);
                });
                // only bother if something actually changed...
                if (!o_utils.areObjectsEqual(opus.prefs.order, newOrder)) {
                    opus.prefs.order = o_utils.deepCloneObj(newOrder);
                    o_hash.updateURLFromCurrentHash(); // This makes the changes visible to the user
                    o_sortMetadata.renderSortedDataFromBeginning();
                }
            },
        });

        // click table column header to reorder by that column
        // On click, if there are already 2 items in the sort <opusId + slug>, display overwrite modal option
        // On ctrl click will append the selected sort
        $("#browse, #cart").on("click", ".op-data-table-view th a", function(e) {
            o_browse.hideMenus();
            let inOrderList = $(this).find(".op-column-ordering").data("sort") !== "none";
            if (!inOrderList && opus.prefs.order.length >= 9) {
                return false;
            }
            let slug = $(this).data("slug");
            if (inOrderList || opus.prefs.order.length <= 2 || (e.ctrlKey || e.metaKey || e.shiftKey)) {
                // if there are two or less sort options, always select append
                let append = (!inOrderList && opus.prefs.order.length <=2 ? false : true);
                // control/shift keys overrides and always appends
                append |= (e.ctrlKey || e.metaKey || e.shiftKey);
                o_sortMetadata.onClickSortOrder(slug, append);
            } else {
                $("#op-overwrite-sort-order").modal("show").data("slug", slug);
            }
            return false;
        });

        $(".op-sort-list").on("click", ".dropdown-item", function(e) {
            o_browse.hideMenus();
            o_sortMetadata.onClickSortOrder($(this).data("slug"));
            return false;
        });

        // browse sort order - flip sort order of a slug
        $(".op-sort-contents").on("click", ".op-flip-sort", function(e) {
            o_browse.hideMenus();
            o_sortMetadata.onClickSortOrder($(this).parent().data("slug"));
        });

        // browse sort order - remove sort slug
        $(".op-sort-contents").on("click", ".op-remove-sort", function(e) {
            o_browse.hideMenus();
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

            o_hash.updateURLFromCurrentHash();
            o_sortMetadata.renderSortedDataFromBeginning();
        });

        $(".op-sort-contents").on("click", ".op-sort-order-add-icon", function(e) {
            // allow the hover to work but the click appear to be disabled
            if ($(".op-sort-order-add-icon").hasClass("op-sort-add-disabled")) {
                return false;
            }
            // if the menu is already displayed, onclick should just close it.
            o_browse.hideMenu();
            if ($("#op-add-sort-metadata").hasClass("show")) {
                o_sortMetadata.hideMenu();
            } else {
                o_sortMetadata.showMenu(e);
            }
            return false;
        });

        $(".op-sort-order-icon").on("click", function(e) {
            // this will reset the current sort
            if (opus.prefs.order.join(",") !== DEFAULT_SORT_ORDER) {
                $("#op-reset-sort-order").modal("show");
            }
        });
    }, // end edit sort metadata behaviours

    onClickSortOrder: function(orderBy, addToSort=true) {
        o_browse.showPageLoaderSpinner();

        let newOrder = [];
        let orderIndex = -1;

        if (addToSort) {
            newOrder = opus.prefs.order;
        }

        let tableOrderIndicator = $(`[data-slug='${orderBy}'] .op-column-ordering`);
        let pillOrderIndicator = $(`.op-sort-contents span[data-slug="${orderBy}"] .op-flip-sort`);
        let isDescending = $(pillOrderIndicator).parent().data("descending") === true;

        // account for the case when the sort pill is present, but the metadata field column is not
        let sortOrder = (tableOrderIndicator.length !== 0 ? tableOrderIndicator.data("sort") : (isDescending ? "desc" : "asc"));

        switch (sortOrder) {
            case "asc":
                // currently ascending, change to descending order
                isDescending = true;
                orderIndex = $.inArray(orderBy, newOrder);
                orderBy = '-' + orderBy;
                break;

            case "desc":
                // currently descending, change to ascending order
                isDescending = false;
                orderIndex = $.inArray(`-${orderBy}`, newOrder);
                break;

            case "none":
                // if not currently ordered, change to ascending
                isDescending = false;
                orderIndex = $.inArray(orderBy, newOrder);
                break;
        }

        // if the user clicked on a header that is not yet in the order list, add it ...
        if (orderIndex < 0) {
            // opusid must always be last, so instead of push we splice.
            newOrder.splice(newOrder.length-1, 0, orderBy);
        } else {
            newOrder[orderIndex] = orderBy;
        }
        // push it here so that opusID is last
        if (!addToSort) {
            newOrder.push("opusid");
        }
        opus.prefs.order = newOrder;
        o_sortMetadata.updateOrderIndicator(tableOrderIndicator, pillOrderIndicator, isDescending, orderBy);

        o_hash.updateURLFromCurrentHash();
        o_sortMetadata.renderSortedDataFromBeginning();
    },

    hideMenu: function() {
        $("#op-add-sort-metadata").removeClass("show").hide();
    },

    showMenu: function(e) {
        // make this like a default right click menu
        let tab = opus.getViewTab();
        let contextMenu = "#op-add-sort-metadata";
        o_browse.hideMenu();

        let html = "";

        $(`${tab} .op-data-table-view th`).find("a[data-slug]").each(function(index, obj) {
            let slug = $(obj).data("slug");
            let label = $(obj).data("label");
            if ($(obj).find(".op-column-ordering").data("sort") === "none") {
                html += `<a class="dropdown-item font-sm" data-slug="${slug}" href="#">${label}</a>`;
            }
        });
        $("#op-add-sort-metadata .op-sort-list").html(html);

        let menu = {"height":$(contextMenu).innerHeight(), "width":$(contextMenu).innerWidth()};
        let top =  e.pageY;
        let left = ($(tab).innerWidth() - e.pageX > menu.width)  ? e.pageX + 12: e.pageX-menu.width;

        $(contextMenu).css({
            display: "block",
            top: top,
            left: left
        }).addClass("show");
    },

    // update order arrows right away when user clicks on sorting arrows in pill or table header
    // sync up arrows in both sorting pill and table header
    updateOrderIndicator: function(headerOrderIndicator, pillOrderIndicator, isDescending, slug) {
        let headerOrder = isDescending ? "desc" : "asc";
        let headerOrderArrow = isDescending ? tableSortUpArrow : tableSortDownArrow;

        // If header already exists, we update the header arrow, else we do nothing
        if (headerOrderIndicator && headerOrderIndicator.length !== 0) {
            headerOrderIndicator.data("sort", `${headerOrder}`);
            headerOrderIndicator.attr("class", `op-column-ordering ${headerOrderArrow}`);
        }
        $(pillOrderIndicator).parent().data("descending", (isDescending ? "true" : "false"));
    },

    updateSortOrder: function(data) {
        let tab = opus.getViewTab();
        let dragTooltip = "\nDrag to reorder";

        let addIconHtml = `<div class="op-no-sort list-inline-item">` +
                             `<div class="op-sort-order-add-icon" title="Add metadata fields to sort order">`+
                                `<i class="fas fa-plus"></i>` +
                             `</div>`;  // opusID pill will get tagged onto this later thus ending the </div>

        let tableColumnFields = {};
        $(`${tab} .op-data-table-view th`).find("a[data-slug]").each(function(index, obj) {
            tableColumnFields[$(obj).data("slug")] = index;
        });

        opus.prefs.order = [];
        $(".op-sort-contents").empty();
        $.each(data.order_list, function(index, order_entry) {
            let slug = order_entry.slug;
            let label = order_entry.label;
            let isDescending = order_entry.descending;
            let orderTooltip = (isDescending ? "Change to ascending sort" : "Change to descending sort") + (slug === "opusid" ? "" : dragTooltip);

            let removeable = order_entry.removeable;
            let itemClasses = (slug === "opusid" ? "op-sort-last" : "list-inline-item op-sort-only");

            let listHtml = `<div class='${itemClasses}'>`;
            listHtml += `<span class='badge rounded-pill bg-light' data-slug="${slug}" data-descending="${isDescending}">`;
            if (removeable) {
                listHtml += "<span class='op-remove-sort' title='Remove metadata field from sort'><i class='fas fa-times-circle'></i></span> ";
            }
            listHtml += `<span class='op-flip-sort' title='${orderTooltip}'>`;
            listHtml += label;
            listHtml += (isDescending ? `<i class="${pillSortUpArrow} ms-1"></i>` : `<i class="${pillSortDownArrow} ms-1"></i>`);
            listHtml += "</span></span></div>";

            let fullSlug = slug;
            if (isDescending) {
                fullSlug = "-" + slug;
            }
            opus.prefs.order.push(fullSlug);
            if (tableColumnFields[slug] !== undefined) {
                delete tableColumnFields[slug];
            }
            if (slug === "opusid") {
                addIconHtml += listHtml + "</div>";
            } else {
                $(".op-sort-contents").append(listHtml);
            }
        });
        $(".op-sort-contents").append(addIconHtml);

        // if all the metadata field columns are already in the sort list, disable the add button
        // limit the total number of sort columns to 9
        if (Object.keys(tableColumnFields).length === 0) {
            $(".op-sort-order-add-icon").addClass("op-sort-add-disabled");
            $(".op-sort-order-add-icon").attr("title", "All selected metadata fields have been used");
        } else if (opus.prefs.order.length >= 9) {
            $(".op-sort-order-add-icon").addClass("op-sort-add-disabled");
            $(".op-sort-order-add-icon").attr("title", "The maximum of nine metadata sort fields has been reached");
        } else {
            $(".op-sort-order-add-icon").removeClass("op-sort-add-disabled");
        }
        o_hash.updateURLFromCurrentHash();
    },

    resetSortOrder: function () {
        opus.prefs.order = DEFAULT_SORT_ORDER;
        o_hash.updateURLFromCurrentHash();
        o_sortMetadata.renderSortedDataFromBeginning();
    },

    renderSortedDataFromBeginning: function(closeMetadataDetailView=true) {
        o_utils.disableUserInteraction();
        o_browse.clearObservationData();
        o_browse.loadData(opus.prefs.view, closeMetadataDetailView);
    },
};
