/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* globals $, PerfectScrollbar */
/* globals o_browse, o_hash, o_menu, o_utils, o_widgets, opus */

/******************************************/
/********* SELECT METADATA DIALOG *********/
/******************************************/
const metadataModalHeightBreakPoint = 400;
const gapBetweenBottomEdgeAndMetadataModal = 55;

/* jshint varstmt: false */
var o_selectMetadata = {
/* jshint varstmt: true */
    // PS scrollbars - defining here; they will need to be set to NULL to release
    // memory and enable garbage collection whenever a new render of the modal is requested
    allMetadataScrollbar: null,
    selectedMetadataScrollbar: null,

    // A flag to determine if the sortable item sorting is happening. This
    // will be used in mutation observer to determine if scrollbar location should
    // be set.
    isSortingHappening: false,

    spinnerTimer: null,

    // save the original copy in case we need to discard
    originalOpusPrefsCols: [],

    lastSavedSelected: [],
    lastMetadataMenuRequestNo: 0,

    // metadata selector behaviors
    addBehaviors: function() {
        // global to allow the modal event handlers to communicate
        /* jshint varstmt: false */
        var clickedX = false;
        /* jshint varstmt: true */

        $("#op-select-metadata").on("show.bs.modal", function(e) {
            // this is to make sure modal is back to it original position when open again
            $("#op-select-metadata .modal-dialog").css({top: 0, left: 0});
            o_selectMetadata.saveOpusPrefsCols();
            o_selectMetadata.adjustHeight();
            o_browse.hideMenus();
            console.log("=======render when clicking select metadata modal====")
            o_selectMetadata.render();

            // Do the fake API call to write in the Apache log files that
            // we invoked the metadata selector so log_analyzer has something to
            // go on
            let fakeUrl = "/opus/__fake/__selectmetadatamodal.json";
            $.getJSON(fakeUrl, function(data) {
            });
        });

        $("#op-select-metadata .close").on("click", function(e) {
            clickedX = true;
        });

        $("#op-select-metadata").on("hide.bs.modal", function(e) {
            // update the data table w/the new columns
            if (!o_utils.areObjectsEqual(opus.prefs.cols, o_selectMetadata.originalOpusPrefsCols)) {
                // only pop up the confirm modal if the user clicked the 'X' in the corner
                if (clickedX) {
                    clickedX = false;
                    let targetModal = $(this).find("[data-target]").data("target");
                    $(`#${targetModal}`).modal("show");
                } else {
                    o_selectMetadata.saveChanges();
                    return;
                }
            }
            // remove spinner if nothing is re-draw when we click save changes
            o_browse.hidePageLoaderSpinner();
        });

        $("#op-select-metadata").on("click", ".op-all-metadata-column .submenu li a", function() {
            let slug = $(this).data('slug');
            if (!slug) { return; }

            let chosenSlugSelector = `#cchoose__${slug}`;
            if ($(chosenSlugSelector).length === 0) {
                // this slug was previously unselected, add to cols
                o_selectMetadata.addColumn(slug);
            } else {
                // slug had been checked, remove from the chosen
                o_selectMetadata.removeColumn(slug);
            }
            return false;
        });

        // removes chosen column
        $("#op-select-metadata").on("click", ".op-selected-metadata-column li .op-selected-metadata-unselect", function() {
            let slug = $(this).parent().attr("id").split('__')[1];
            o_selectMetadata.removeColumn(slug);
            return false;
        });

        // collapse/expand the add field for the slide view
        $("#op-select-metadata").on("show.bs.collapse hide.bs.collapse", function(e) {
            let collapsibleID = $(e.target).attr("id");
            if (collapsibleID !== undefined) {
                collapsibleID = collapsibleID.replace("submenu", "mini");
                $(`#${collapsibleID}`).collapse("toggle");
            }
        });

        // buttons
        $("#op-select-metadata").on("click", ".btn", function() {
            switch($(this).attr("type")) {
                case "reset":
                    o_selectMetadata.resetMetadata();
                    break;
                case "submit":
                    break;
                case "cancel":
                    o_selectMetadata.discardChanges();
                    break;
            }
        });

        $("#op-select-metadata").on("click", ".op-download-csv", function(e) {
            let namespace = opus.getViewNamespace();
            namespace.downloadCSV(this);
        });
    },  // /addSelectMetadataBehaviors

    showMenuLoaderSpinner: function() {
        o_selectMetadata.spinnerTimer = setTimeout(function() {
            $(".op-select-metadata-load-status > .loader").show();
            $(".op-select-metadata-row-contents").css("opacity", "0.1");
            o_utils.disableUserInteraction();
        }, opus.spinnerDelay);
    },

    hideMenuLoaderSpinner: function() {
        if (o_selectMetadata.spinnerTimer !== null) {
            clearTimeout(o_selectMetadata.spinnerTimer);
            $(".op-select-metadata-load-status > .loader").hide();
            $(".op-select-metadata-row-contents").css("opacity", "1");
            o_selectMetadata.spinnerTimer = null;
        }
        o_utils.enableUserInteraction();
    },

    render: function() {
        let tab = opus.getViewTab();
        let downloadTitle = (tab === "#cart" ? "Download a CSV of selected metadata for all observations in the cart" : "Download CSV of selected metadata for ALL observations in current results");
        let buttonTitle = (tab === "#cart" ? "Download CSV (in cart)" : "Download CSV (all results)");

        if (!o_selectMetadata.rendered) {
            o_selectMetadata.showMenuLoaderSpinner();

            // We use getFullHashStr instead of getHash because we want the updated
            // version of widgets= even if the main URL hasn't been updated yet
            let hash = o_hash.getFullHashStr();

            // Figure out which categories are already expanded
            // if the add selected metadata menu from the slide show is open, use those expanded categories instead
            let id = $("#op-add-metadata-fields").hasClass("show") ? "#op-add-metadata-fields" : "#op-select-metadata";
            let numberCategories = $(`${id} .op-submenu-category`).length;
            let expandedCategoryLinks = $(`${id} .op-submenu-category`).not(".collapsed");
            let expandedCategories = [];
            $.each(expandedCategoryLinks, function(index, linkObj) {
                expandedCategories.push($(linkObj).data("cat"));
            });
            let expandedCats = "";
            if (numberCategories > 0) {
                /* If there aren't any categories, it means this is the first time we're
                   loading the select metadata menu so let the backend do its default
                   behavior. Otherwise, specify the categories to expand. */
                if (hash !== "") {
                    expandedCats = "&";
                }
                expandedCats += "expanded_cats=" + expandedCategories.join();
            }
            o_selectMetadata.lastMetadataMenuRequestNo++;
            let url = `/opus/__metadata_selector.json?${hash}${expandedCats}&reqno=${o_selectMetadata.lastMetadataMenuRequestNo}`;
            console.log("$$$$$$")
            console.log(url)

            $.getJSON(url, function(data) {
                if (data.reqno < o_selectMetadata.lastMetadataMenuRequestNo) {
                    return;
                }
                // cleanup first
                o_selectMetadata.allMetadataScrollbar = null;
                o_selectMetadata.selectedMetadataScrollbar = null;
                $("#op-select-metadata .op-selected-metadata-column > ul").sortable("destroy");

                $("#op-select-metadata-contents").html(data.html);
                $("#op-add-metadata-fields .op-select-list").html(data.add_field_html);
                $("#op-select-metadata .op-reset-button").hide(); // we are not using this

                // since we are rendering the left side of metadata selector w/the same code that builds the select menu,
                // we need to unhighlight the selected widgets
                o_menu.markMenuItem("#op-select-metadata .op-all-metadata-column a", "unselect");

                // display check next to any currently used columns
                $.each(opus.prefs.cols, function(index, col) {
                    o_menu.markMenuItem(`#op-select-metadata .op-all-metadata-column a[data-slug="${col}"]`);
                    let elem = $(`#op-add-metadata-fields .op-select-list a[data-slug="${col}"]`).parent();
                    elem.remove();
                });
                //remove category from the add menu if it's empty
                $(`#op-add-metadata-fields .op-search-menu-category ul`).each(function(index, elem) {
                    $(elem).find(".submenu").each(function(i, subelem) {
                        if ($(subelem).find("li").length === 0) {
                            $(subelem).parent().remove();
                        }
                    });
                    if ($(elem).find("li").length === 0) {
                        $(elem).parent().remove();
                    }
                });
                o_browse.checkForEmptyMetadataList();

                o_menu.wrapTriangleArrowAndLastWordOfMenuCategory("#op-select-metadata");

                o_selectMetadata.allMetadataScrollbar = new PerfectScrollbar("#op-select-metadata-contents .op-all-metadata-column", {
                    minScrollbarLength: opus.minimumPSLength
                });
                o_selectMetadata.selectedMetadataScrollbar = new PerfectScrollbar("#op-select-metadata-contents .op-selected-metadata-column", {
                    minScrollbarLength: opus.minimumPSLength
                });

                // Initialize all tooltips using tooltipster in select metadata menu
                $(".op-metadata-selector-tooltip").tooltipster({
                    maxWidth: opus.tooltipsMaxWidth,
                    theme: opus.tooltipsTheme,
                    delay: opus.tooltipsDelay,
                });
                // Initialize all tooltips using tooltipster in menu.html
                $(".op-all-metadata-column .op-menu-tooltip").tooltipster({
                    maxWidth: opus.tooltipsMaxWidth,
                    theme: opus.tooltipsTheme,
                    delay: opus.tooltipsDelay,
                });

                $("#op-select-metadata a.op-download-csv").tooltipster("content", downloadTitle);
                $("#op-select-metadata a.op-download-csv").text(buttonTitle);

                $("#op-select-metadata .op-selected-metadata-column > ul").sortable({
                    items: "li",
                    cursor: "grab",
                    containment: "parent",
                    tolerance: "pointer",
                    stop: function(event, ui) {
                        o_selectMetadata.metadataDragged(this);
                        o_selectMetadata.isSortingHappening = false;
                    },
                    start: function(event, ui) {
                        o_widgets.getMaxScrollTopVal(event.target);
                        o_selectMetadata.isSortingHappening = true;
                    },
                    sort: function(event, ui) {
                        o_widgets.preventContinuousDownScrolling(event.target);
                    }
                });

                // Prevent overscrolling on ps in selected metadata fields when scrolling
                // inside unit dropdown when the list has reached to both ends
                $(".op-selected-metadata-column .op-scrollable-menu").on("scroll wheel", function(e) {
                    e.stopPropagation();
                });

                if (opus.prefs.cols.length <= 1) {
                    $("#op-select-metadata .op-selected-metadata-column .op-selected-metadata-unselect").hide();
                }
                // save the current selected metadata
                o_selectMetadata.lastSavedSelected = $("#op-select-metadata .op-selected-metadata-column > ul").find("li");
                o_selectMetadata.saveOpusPrefsCols();
                o_selectMetadata.adjustHeight();
                o_selectMetadata.hideOrShowPS();
                o_selectMetadata.hideOrShowMenuPS();
                o_selectMetadata.hideMenuLoaderSpinner();
                o_selectMetadata.rendered = true;
            });
        }
        $("#op-select-metadata a.op-download-csv").tooltipster("content", downloadTitle);
        $("#op-select-metadata a.op-download-csv").text(buttonTitle);
    },

    reRender: function() {
        o_selectMetadata.rendered = false;
        o_selectMetadata.render();
    },

    saveOpusPrefsCols: function() {
        o_selectMetadata.originalOpusPrefsCols = opus.prefs.cols.map((x) => x);
    },

    addColumn: function(slug) {
        let menuSelector = `#op-select-metadata .op-all-metadata-column a[data-slug=${slug}]`;
        o_menu.markMenuItem(menuSelector);
        opus.prefs.cols.push(slug);

        let label = $(menuSelector).data("qualifiedlabel");
        let info = `<i class="fas fa-info-circle op-metadata-selector-tooltip" title="${$(menuSelector).find(".tooltipstered").tooltipster("content")}"></i>`;
        // TODO: need to append unit after label, and make label
        let html = `<li id="cchoose__${slug}" class="ui-sortable-handle"><span class="op-selected-metadata-info">&nbsp;${info}</span>${label}<span class="op-selected-metadata-unselect"><i class="far fa-trash-alt"></span></li>`;
        $(".op-selected-metadata-column > ul").append(html);
        if ($(".op-selected-metadata-column li").length > 1) {
            $(".op-selected-metadata-column .op-selected-metadata-unselect").show();
        }

        $(".op-metadata-selector-tooltip").tooltipster({
            maxWidth: opus.tooltipsMaxWidth,
            theme: opus.tooltipsTheme,
            delay: opus.tooltipsDelay,
        });

    },

    removeColumn: function(slug) {
        let colIndex = $.inArray(slug, opus.prefs.cols);
        if (colIndex < 0 || opus.prefs.cols.length <= 1) {
            return;
        }
        opus.prefs.cols.splice(colIndex, 1);

        let menuSelector = `#op-select-metadata .op-all-metadata-column a[data-slug=${slug}]`;
        o_menu.markMenuItem(menuSelector, "unselected");

        $(`#cchoose__${slug}`).fadeOut(200, function() {
            $(this).remove();
            if ($(".op-selected-metadata-column li").length <= 1) {
                $(".op-selected-metadata-column .op-selected-metadata-unselect").hide();
            }
        });
    },

    // columns can be reordered wrt each other in 'metadata selector' by dragging them
    metadataDragged: function(element) {
        let cols = $.map($(element).sortable("toArray"), function(item) {
            return item.split("__")[1];
        });
        opus.prefs.cols = cols;
    },

    discardChanges: function() {
        // uncheck all on left; we will check them as we go
        o_menu.markMenuItem("#op-select-metadata .op-all-metadata-column a", "unselect");
        // remove all from selected column
        $("#op-select-metadata .op-selected-metadata-column li").remove();
        opus.prefs.cols = o_selectMetadata.originalOpusPrefsCols.map((x) => x);

        // add them back in...
        $(opus.prefs.cols).each(function(index, slug) {
            let menuSelector = `#op-select-metadata .op-all-metadata-column a[data-slug=${slug}]`;
            o_menu.markMenuItem(menuSelector);
        });
        $(o_selectMetadata.lastSavedSelected).each(function(index, selected) {
            $("#op-select-metadata .op-selected-metadata-column > ul").append(selected);
        });
        $("#op-select-metadata .op-selected-metadata-column").find("li").show();
        $("#op-select-metadata").modal("hide");
    },

    resetMetadata: function() {
        // uncheck all on left; we will check them as we go
        o_menu.markMenuItem("#op-select-metadata .op-all-metadata-column a", "unselect");

        // remove all from selected column
        $("#op-select-metadata .op-selected-metadata-column li").remove();
        opus.prefs.cols = [];

        // add them back and set the check
        $.each(opus.defaultColumns, function(index, slug) {
            o_selectMetadata.addColumn(slug);
        });
    },

    saveChanges: function() {
        o_selectMetadata.lastSavedSelected = $("#op-select-metadata .op-selected-metadata-column > ul").find("li");
        o_browse.clearObservationData(true); // Leave startobs alone
        o_hash.updateURLFromCurrentHash(); // This makes the changes visible to the user
        o_utils.disableUserInteraction();
        o_selectMetadata.reRender();
        // if the metadata is no longer default, we need to enable the reset button on the Search tab
        if (!opus.isMetadataDefault()) {
            $(".op-reset-button .op-reset-search-metadata").prop("disabled", false);
        } else {
            if ($(".op-reset-button .op-reset-search").prop("disabled")) {
                $(".op-reset-button .op-reset-search-metadata").prop("disabled", true);
            }
        }
        o_browse.loadData(opus.prefs.view, false);
    },

    adjustHeight: function() {
        /**
         * Set the height of the "Select Metadata" dialog based on the browser size.
         */
        $(".op-select-metadata-headers").show(); // Show now so computations are accurate
        $(".op-select-metadata-headers-hr").show();
        let footerHeight = $(".app-footer").outerHeight();
        let mainNavHeight = $(".op-reset-opus").outerHeight() +
                            $("#op-main-nav").innerHeight() - $("#op-main-nav").height();
        let modalHeaderHeight = $("#op-select-metadata .modal-header").outerHeight();
        let modalFooterHeight = $("#op-select-metadata .modal-footer").outerHeight();
        let selectMetadataHeadersHeight = $(".op-select-metadata-headers").outerHeight()+30;
        let selectMetadataHeadersHRHeight = $(".op-select-metadata-headers-hr").outerHeight();
        let buttonHeight = $("#op-select-metadata .op-download-csv").outerHeight();
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
            buttonHeight = 35;
        }
        let totalNonScrollableHeight = (footerHeight + mainNavHeight + modalHeaderHeight +
                                        modalFooterHeight + selectMetadataHeadersHeight +
                                        selectMetadataHeadersHRHeight);
        /* 55 is a rough guess for how much space we want below the dialog, when possible.
           130 is the minimum size required to display four metadata fields.
           Anything less than that makes the dialog useless. In that case we hide the
           header text to give us more room. */
        let height = (($(window).height() > metadataModalHeightBreakPoint) ?
                      $(window).height()-totalNonScrollableHeight-gapBetweenBottomEdgeAndMetadataModal : $(window).height()-totalNonScrollableHeight);

        if (height < 130) {
            $(".op-select-metadata-headers").hide();
            $(".op-select-metadata-headers-hr").hide();
            height += selectMetadataHeadersHeight + selectMetadataHeadersHRHeight;
        }
        $(".op-all-metadata-column").css("height", height);
        $(".op-selected-metadata-column").css("height", height - buttonHeight);
    },

    menuContainerHeight: function() {
        return $(".op-all-metadata-column").outerHeight();
    },

    containerHeight: function() {
        return $(".op-selected-metadata-column").outerHeight();
    },

    hideOrShowMenuPS: function() {
        let containerHeight = $(".op-all-metadata-column").height();
        let menuHeight = $(".op-all-metadata-column .op-search-menu").height();
        if (o_selectMetadata.allMetadataScrollbar) {
            if (containerHeight >= menuHeight) {
                if (!$(".op-all-metadata-column .ps__rail-y").hasClass("hide_ps__rail-y")) {
                    $(".op-all-metadata-column .ps__rail-y").addClass("hide_ps__rail-y");
                    o_selectMetadata.allMetadataScrollbar.settings.suppressScrollY = true;
                }
            } else {
                $(".op-all-metadata-column .ps__rail-y").removeClass("hide_ps__rail-y");
                o_selectMetadata.allMetadataScrollbar.settings.suppressScrollY = false;
            }
            o_selectMetadata.allMetadataScrollbar.update();
        }
    },

    hideOrShowPS: function() {
        let containerHeight = $(".op-selected-metadata-column").height();
        let selectedMetadataHeight = $(".op-selected-metadata-column .ui-sortable").height();

        if (o_selectMetadata.selectedMetadataScrollbar) {
            if (containerHeight >= selectedMetadataHeight) {
                if (!$(".op-selected-metadata-column .ps__rail-y").hasClass("hide_ps__rail-y")) {
                    $(".op-selected-metadata-column .ps__rail-y").addClass("hide_ps__rail-y");
                    o_selectMetadata.selectedMetadataScrollbar.settings.suppressScrollY = true;
                }
            } else {
                $(".op-selected-metadata-column .ps__rail-y").removeClass("hide_ps__rail-y");
                o_selectMetadata.selectedMetadataScrollbar.settings.suppressScrollY = false;
            }
            o_selectMetadata.selectedMetadataScrollbar.update();
        }
    },
};
