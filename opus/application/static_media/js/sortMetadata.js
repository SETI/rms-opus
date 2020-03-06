/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* globals o_hash, o_browse, opus */

// font awesome icon class
const pillSortUpArrow = "fas fa-arrow-circle-up";
const pillSortDownArrow = "fas fa-arrow-circle-down";
const tableSortUpArrow = "fas fa-sort-up";
const tableSortDownArrow = "fas fa-sort-down";
const defaultTableSortArrow = "fas fa-sort";

var o_sortMetadata = {
    /**
    *
    *  all the things that happen when editting the sort on metadata
    *
    **/
    addSortMetadataBehaviours: function() {
        $(".op-sort-contents").sortable({
            items: "li",
            cursor: "grab",
            containment: "parent",
            tolerance: "pointer",
            stop: function(event, ui) {
                // rebuild new search order and reload page
                opus.prefs.order = [];
                $(this).find("li span.badge-pill").each(function(index, obj) {
                    let slug = $(obj).data("slug");
                    opus.prefs.order.push(slug);
                });
                o_hash.updateURLFromCurrentHash(); // This makes the changes visible to the user
                o_browse.loadData(opus.prefs.view);
            },
        });

        // click table column header to reorder by that column
        $("#browse, #cart").on("click", ".op-data-table-view th a",  function() {
            o_sortMetadata.onClickSortOrder($(this).data("slug"));
            return false;
        });

        // browse sort order - flip sort order of a slug
        $(".op-sort-contents").on("click", "li .flip-sort", function() {
            o_sortMetadata.onClickSortOrder($(this).parent().data("slug"));
        });

        // browse sort order - remove sort slug
        $(".op-sort-contents").on("click", "li .remove-sort", function() {
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

        $(".op-sort-order-add-icon").on("click", function() {
            console.log("click");
        });
    }, // end edit sort metadata behaviours

    onClickSortOrder: function(orderBy) {
        o_browse.showPageLoaderSpinner();

        // get order of opusid when table header is clicked
        let order = [];
        let orderIndex = -1;
        let hash = o_hash.getHashArray();
        if (hash.order) {
            order = hash.order.split(",");
        }

        let isDescending = true;
        let tableOrderIndicator = $(`[data-slug='${orderBy}'] .op-column-ordering`);
        let pillOrderIndicator = $(`.op-sort-contents span[data-slug="${orderBy}"] .flip-sort`);

        switch (tableOrderIndicator.data("sort")) {
            case "asc":
                // currently ascending, change to descending order
                isDescending = true;
                orderIndex = $.inArray(orderBy, order);
                orderBy = '-' + orderBy;
                break;

            case "desc":
                // currently descending, change to ascending order
                isDescending = false;
                orderIndex = $.inArray(`-${orderBy}`, order);
                break;

            case "none":
                // if not currently ordered, change to ascending
                isDescending = false;
                orderIndex = $.inArray(orderBy, order);
                break;
        }

        // if the user clicked on a header that is not yet in the order list, add it ...
        if (orderIndex < 0) {
            order.push(orderBy);
        } else {
            order[orderIndex] = orderBy;
        }
        opus.prefs.order = order;
        o_sortMetadata.updateOrderIndicator(tableOrderIndicator, pillOrderIndicator, isDescending, orderBy);

        o_hash.updateURLFromCurrentHash();
        o_sortMetadata.renderSortedDataFromBeginning();
    },

    // update order arrows right away when user clicks on sorting arrows in pill or table header
    // sync up arrows in both sorting pill and table header
    updateOrderIndicator: function(headerOrderIndicator, pillOrderIndicator, isDescending, slug) {
        let headerOrder = isDescending ? "desc" : "asc";
        let headerOrderArrow = isDescending ? tableSortUpArrow : tableSortDownArrow;
        let pillOrderTooltip = isDescending ? "Change to ascending sort" : "Change to descending sort";

        // If header already exists, we update the header arrow, else we do nothing
        if (headerOrderIndicator && headerOrderIndicator.length !== 0) {
            headerOrderIndicator.data("sort", `${headerOrder}`);
            headerOrderIndicator.attr("class", `op-column-ordering ${headerOrderArrow}`);
        }
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
        $(".op-sort-contents").html(listHtml);
        o_hash.updateURLFromCurrentHash();
    },

    renderSortedDataFromBeginning: function() {
        o_browse.clearObservationData();
        o_browse.loadData(opus.prefs.view);
    },
}
