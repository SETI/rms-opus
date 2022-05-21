/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* globals $, PerfectScrollbar */
/* globals o_browse, o_hash, o_utils, o_selectMetadata, opus */

// The download data left pane will become a slide panel when screen width
// is equal to or less than the threshold point.
const cartLeftPaneThreshold = 1100;
// The download data left pane will be closed when the screen width is equal to
// or less than the current threshold and the screen height is also less than
// the height threshold
const cartLeftPaneMinHeight = 460;
// Max height for the contents of download links history (.popover-body) before we enable PS.
const downloadLinksPBMaxHeight = 200;
// Html string for customized popover window. The reason we don't put the whole html
// element in DOM first and retrieve by .html() later is because we need to attach
// ps to .popover-body, and by adding the whole popover element in html first, there
// will be two .popover-body elements (one from the inserted DOM at the beginning and
// one from actual popover window). Jquery selector will only select the first
// .popover-body and failed to attached the ps to the actual popover window. (Note: there
// is no proper way to distinguish between them because the 2nd one is the duplicate of
// the 1st one).
const downloadLinksPopoverTemplate = "<div class='popover' role='tooltip'>" +
                                     "<div class='arrow'></div>" +
                                     "<h3 class='popover-header'></h3>" +
                                     "<div class='popover-body'></div>" +
                                     "<div class='popover-footer'>" +
                                     "<a tabindex='0' role='button' class='op-cite-opus-btn op-no-select'>" +
                                     "How to Cite OPUS" +
                                     "</a>" +
                                     "<button class='op-clear-history-btn btn btn-sm btn-secondary'" +
                                     "type='button' title='Clear all history' disabled>Clear All</button></div>" +
                                     "</div>";
const downloadLinksPopoverTitle = "Download Archive Links" +
                                  "<button " +
                                  "class='close-download-links-history btn-sm py-0 pe-0 ps-2 border-0' " +
                                  "type='button'>&nbsp;" +
                                  "<i class='fas fa-times'></i>" +
                                  "</button>";

/* jshint varstmt: false */
var o_cart = {
/* jshint varstmt: true */
    // tableScrollbar and galleryScrollbar are common vars w/browse.js
    tableScrollbar: new PerfectScrollbar("#cart .op-data-table-view", {
        minScrollbarLength: opus.galleryAndTablePSLength,
        maxScrollbarLength: opus.galleryAndTablePSLength,
    }),
    galleryScrollbar: new PerfectScrollbar("#cart .op-gallery-view", {
        suppressScrollX: true,
        minScrollbarLength: opus.galleryAndTablePSLength,
        maxScrollbarLength: opus.galleryAndTablePSLength,
    }),

    // these vars are common w/o_browse
    reloadObservationData: true, // start over by reloading all data
    metadataDetailEdit: false, // is the metadata detail view currently in edit mode?
    observationData: {},  // holds observation column data
    totalObsCount : undefined,
    recycledCount : undefined,
    cachedObservationFactor: 4,     // this is the factor times the screen size to determine cache size
    maxCachedObservations: 1000,    // max number of observations to store in cache, will be updated based on screen size
    galleryBoundingRect: {'x': 0, 'yCell': 0, 'yFloor': 0, 'yPartial': 0, 'trFloor': 0},
    gallerySliderStep: 10,
    // opusID of the last slide show/gallery view modal after it is closed
    lastMetadataDetailOpusId: "",

    // unique to o_cart
    lastRequestNo: 0,           // for status
    lastProductCountRequestNo: 0,   // just for the product counts in sidebar
    downloadInProcess: false,
    cartCountSpinnerTimer: null,    // We have a single global spinner timer to handle overlapping API calls
    downloadSpinnerTimer: null, // similarly to why we have a single global lastRequestNo

    // collector for all cart status error messages
    statusDataErrorCollector: [],

    loadDataInProgress: false,
    infiniteScrollLoadInProgress: false,
    /**
     *
     *  managing cart communication between server and client and
     *  all interaction on the cart tab
     *
     *  for the visual interaction on the browse table/gallery view when adding/removing
     *  from cart see browse.js
     *
     **/

    addCartBehaviors: function() {
        // nav bar
        $("#cart").on("click", ".op-download-csv", function(e) {
            o_cart.downloadCSV(this);
        });

        $("#cart").on("click", ".downloadData", function(e) {
            // prevent url hash from being changed to # (in a tag href)
            e.preventDefault();
            o_cart.downloadZip("create_zip_data_file", "Internal error creating data zip file");
        });

        $("#cart").on("click", ".downloadURL", function(e) {
            // prevent url hash from being changed to # (in a tag href)
            e.preventDefault();
            o_cart.downloadZip("create_zip_url_file", "Internal error creating URL zip file");
        });

        // Display the whole series of modals.
        // This will keep displaying multiple error message modals one after another when the previous modal is closed.
        $("#op-cart-status-error-msg-modal").on("hidden.bs.modal", function(e) {
            if (o_cart.statusDataErrorCollector.length !== 0) {
                $("#op-cart-status-error-msg-modal .modal-body").text(o_cart.statusDataErrorCollector.pop());
                $("#op-cart-status-error-msg-modal").modal("show");
            }
        });

        // Click to open the download data panel when that nav-link is available
        $("#cart").on("click", ".op-cart-slide-download-panel", function(e) {
            o_cart.displayCartLeftPane();
            $("#op-cart-download-panel").toggle("slide", {direction:"left"}, function() {
                $(".op-overlay").addClass("active");
                $("#op-cart-download-panel").addClass("active");
            });
        });

        // Clicking on the "X" in the corner of the download data panel
        $("#op-cart-download-panel .close, .op-overlay").on("click", function() {
            opus.hideHelpAndCartPanels();
            return false;
        });

        // check an input on selected products and images updates file_info
        $("#cart").on("click", ".op-download-options-product-types input", function(e) {
            let productCategory = $(e.currentTarget).data("category");
            let productInputs = $(`input[data-category="${productCategory}"]`);

            let prodTypeSelectAllBtn = $(`.op-cart-select-btn[data-category="${productCategory}"]`);
            let prodTypeDeselectAllBtn = $(`.op-cart-deselect-btn[data-category="${productCategory}"]`);
            let isAllCatOptionsChecked = o_cart.isAllOptionStatusTheSame(productInputs);
            let isAllCatOptionsUnchecked = o_cart.isAllOptionStatusTheSame(productInputs, false);

            let allCheckboxesOptions = $(".op-download-options-product-types input");
            let isAllOptionsChecked = o_cart.isAllOptionStatusTheSame(allCheckboxesOptions);
            let isAllOptionsUnchecked = o_cart.isAllOptionStatusTheSame(allCheckboxesOptions, false);

            o_cart.updateSelectDeselectBtn(isAllCatOptionsChecked, isAllCatOptionsUnchecked,
                                           prodTypeSelectAllBtn, prodTypeDeselectAllBtn);
            o_cart.updateSelectDeselectBtn(isAllOptionsChecked, isAllOptionsUnchecked,
                                           ".op-cart-select-all-btn", ".op-cart-deselect-all-btn");

            o_cart.updateDownloadFileInfo();
        });

        // Event handler when clicking "Select all product types" and "Deselect all product types" buttons.
        $("#cart").on("click", ".op-cart-select-all-btn, .op-cart-deselect-all-btn", function(e) {
            let productList = $(".op-download-options-product-types input");
            o_cart.updateCheckboxes(e.target, productList);

            if ($(e.target).hasClass("op-cart-select-all-btn")) {
                $(".op-cart-select-btn").prop("disabled", true);
                $(".op-cart-deselect-btn").prop("disabled", false);
            } else {
                $(".op-cart-select-btn").prop("disabled", false);
                $(".op-cart-deselect-btn").prop("disabled", true);
            }
        });

        // Event handler when clicking "v" and "x" buttons in each product type.
        $("#cart").on("click", ".op-cart-select-btn, .op-cart-deselect-btn", function(e) {
            let productCategory = $(e.currentTarget).data("category");
            let productList = $(`input[data-category="${productCategory}"]`);

            o_cart.updateCheckboxes(e.currentTarget, productList);

            let allCheckboxesOptions = $(".op-download-options-product-types input");
            let isAllOptionsChecked = o_cart.isAllOptionStatusTheSame(allCheckboxesOptions);
            let isAllOptionsUnchecked = o_cart.isAllOptionStatusTheSame(allCheckboxesOptions, false);

            o_cart.updateSelectDeselectBtn(isAllOptionsChecked, isAllOptionsUnchecked,
                                           ".op-cart-select-all-btn", ".op-cart-deselect-all-btn");
        });

        // Initialize popover window for download links at the lower right corner in footer area.
        $(".footer .op-download-links-btn").popover({
            html: true,
            container: "body",
            title: downloadLinksPopoverTitle,
            template: downloadLinksPopoverTemplate,
            // Make sure popover are only triggered by manual event, and we will set the
            // event handler manually on buttons to open/close popover. The reason we do
            // this is to make sure when popover is manully open by show method, it will
            // close by clicking the button once only. If we didn't set this manual and
            // add event handler manually, we need to click the button twice to close a
            // manually open popover.
            trigger: "manual",
            content: function() {
                return $("#op-download-links").html();
            }
        });

        // Toggle popover window when clicking download history button at the footer
        $(".footer .op-download-links-btn").on("click", function() {
            $(".footer .op-download-links-btn").popover("toggle");
        });

        // Close popover when clicking "x" button on the popover title
        $(document).on("click", ".close-download-links-history", function() {
            $(".footer .op-download-links-btn").popover("hide");
        });

        $(document).on("click", ".op-clear-history-btn", function() {
            o_cart.clearDownloadLinksHistory();
        });

        // Handle the "How to Cite OPUS" button
        $(document).on("click", ".op-cite-opus-btn", function() {
            if (!$(".op-cite-opus-btn").hasClass("op-prevent-pointer-events")) {
                opus.displayHelpPane("citing");
            }
        });
    },

    updateDownloadFileInfo: function() {
        /**
         * Update file info after selecting/deselecting download data.
         */
        o_cart.showDownloadSpinner();
        let add_to_url = o_cart.getDownloadFiltersChecked();
        o_cart.lastRequestNo++;
        let url = "/opus/__cart/status.json?reqno=" + o_cart.lastRequestNo + "&" + add_to_url + "&download=1";
        $.getJSON(url, function(data) {
            if (data.reqno < o_cart.lastRequestNo) {
                return;
            }
            o_cart.updateCartStatus(data);
        });
    },

    updateCheckboxes: function(target, checkboxesOptions) {
        /**
         * Update checkboxes and disable/enable select all & deselect all
         * buttons correspondingly.
         */
        if (($(target).hasClass("op-cart-select-btn") ||
             $(target).hasClass("op-cart-select-all-btn"))) {
            $(checkboxesOptions).prop("checked", true);
        } else if (($(target).hasClass("op-cart-deselect-btn") ||
                    $(target).hasClass("op-cart-deselect-all-btn"))) {
            $(checkboxesOptions).prop("checked", false);
        } else {
            opus.logError("Target button in download data left pane has the wrong class.");
        }
        $(target).prop("disabled", true);
        $(target).siblings().prop("disabled", false);
        o_cart.updateDownloadFileInfo();
    },

    updateSelectDeselectBtn: function(enableSelectAll, enableDeselectAll, selectBtn, deselectBtn) {
        /**
         * Enable/disable select all and deselect all buttons based on
         * parameters enableSelectAll & enableDeselectAll passed in.
         */
         if (enableSelectAll) {
             $(selectBtn).prop("disabled", true);
             $(deselectBtn).prop("disabled", false);
         } else if (enableDeselectAll) {
             $(selectBtn).prop("disabled", false);
             $(deselectBtn).prop("disabled", true);
         } else {
             $(selectBtn).prop("disabled", false);
             $(deselectBtn).prop("disabled", false);
         }
    },

    isAllOptionStatusTheSame: function(productList, checked=true) {
        /**
         * Check if all download options of a product type are the same,
         * return true if all options are selected (when checked is true)
         * or if all options are deselected (when checked is false). This
         * needs to be executed after updateCheckboxes (wait until all
         * checkboxes properties are updated).
         */
        if (productList.length === 1) {
            return checked === productList.is(":checked");
        }
        for (const productOption of productList) {
            if ($(productOption).prop("checked") !== checked) {
                return false;
            }
        }
        return true;
    },

    displayCartLeftPane: function() {
        /**
         * Move download data elements between original left pane and slide panel
         * depending on the screen width
         */
        // We use detach here to keep the event handlers attached to elements
        let html = $("#op-download-options-container").detach();
        if ($(window).width() <= cartLeftPaneThreshold) {
            $("#op-cart-download-panel .op-header-text").html("<h2>Download Data</h2>");
            $("#op-cart-download-panel .op-card-contents").html(html);
            $(".op-download-panel-title").hide();
        } else {
            opus.hideHelpAndCartPanels();
            $(".op-cart-details").html(html);
            $(".op-download-panel-title").show();
        }
        o_cart.adjustProductInfoHeight();
    },

    isScreenNarrow: function(tab) {
        return (tab === "#cart" && $(window).height() <= cartLeftPaneMinHeight);
    },

    isScreenShort: function(tab) {
        return (tab === "#cart" && $(window).width() <= cartLeftPaneThreshold);
    },

    // download filters
    getDownloadFiltersChecked: function() {
        // returned as url string
        let productTypes = [];
        $(".op-download-options-product-types input:checkbox:checked").each(function() {
            productTypes.push($(this).val());
        });
        return "types="+productTypes.join(',');
    },

    downloadZip: function(type, errorMsg) {
        if (o_cart.downloadInProcess) {
            return false;
        }

        opus.downloadInProcess = true;

        // Open the download links popover so the user can see the spinner
        $(".op-download-links-btn").show();
        $(".footer .op-download-links-btn").popover("show");
        $(".op-download-links-contents .spinner").show();
        // prevent popover window from jumping when displaying the spinner
        $(".footer .op-download-links-btn").popover("update");

        let add_to_url = o_cart.getDownloadFiltersChecked();
        let url = "/opus/__cart/download.json?" + add_to_url + "&" + o_hash.getHash();
        url += (type == "create_zip_url_file" ? "&urlonly=1" : "");

        // Check if the "Flat zip file structure" is selected.
        let hierarchical = $(".op-download-flat-zip-file-structure input").prop("checked") ? 0 : 1;
        // Check download file format.
        let fmt = $(".op-download-format option:selected").val();
        url += `&hierarchical=${hierarchical}&fmt=${fmt}`;
        $.ajax({
            url: url,
            dataType: "json",
            success: function(data) {
                if (data.error !== undefined) {
                    // hide the spinner and display error message in an open modal
                    $(".op-download-links-contents .spinner").hide();
                    $(".footer .op-download-links-btn").popover("update");
                    $("#op-download-links-error-msg-modal .modal-body").text(data.error);
                    $("#op-download-links-error-msg-modal").modal("show");
                } else {
                    // To dynamically update and display contents of an open popover, we have to make sure html
                    // in both (1) #op-download-links (content when popover is initialized) and (2) .popover-body
                    // (when popover is open) are synced up with updates. To achieve this, we have to call show
                    // method from popover to update content, and make sure the selector managing DOM are selecting
                    // the same elements in both #op-download-links and .popover-body. (length === 2).
                    $(".op-download-links-btn").show();
                    $(".footer .op-download-links-btn").popover("show");

                    // Set the max height for the window of download links history
                    $(".popover-body").css("max-height", downloadLinksPBMaxHeight);
                    $(".op-download-links-contents .op-empty-history").remove();
                    $(".op-download-links-contents .spinner").hide();
                    let latestLink = $(`<li><a href = "${data.filename}" download>${data.filename}</a></li>`);
                    $(".op-download-links-contents ul.op-zipped-files li:nth-child(1)").after(latestLink);
                    $(".op-clear-history-btn").prop("disabled", false);
                    $(".op-download-links-btn").removeClass("op-a-tag-btn-disabled");
                    o_cart.enablePSinDownloadLinksWindow();
                }
            },
            error: function(e) {
                // hide the spinner and display error message in an open modal
                $(".op-download-links-contents .spinner").hide();
                $(".footer .op-download-links-btn").popover("update");
                $("#op-download-links-error-msg-modal .modal-body").text(errorMsg);
                $("#op-download-links-error-msg-modal").modal("show");
            },
            complete: function() {
                o_cart.downloadInProcess = false;
            }
        });
    },

    enablePSinDownloadLinksWindow: function() {
        /**
         * Initialize and update PS in download links window when the height
         * of the popover window reaches to the max.
         */
        if ($(".popover-body").outerHeight() >= downloadLinksPBMaxHeight) {
            if (!o_cart.downloadLinksScrollbar) {
                o_cart.downloadLinksScrollbar = new PerfectScrollbar(".popover-body", {
                    suppressScrollX: true,
                });
            }
            o_cart.downloadLinksScrollbar.update();
        }
    },

    clearDownloadLinksHistory: function() {
        /**
         * Clear the download links history in the popover window
         */
        $(".footer .op-download-links-btn").popover("show");
        $(".op-zipped-files li:not(:first-child)").remove();
        $(".footer .op-download-links-btn").popover("update");
        $(".op-clear-history-btn").prop("disabled", true);
        $(".op-download-links-btn").addClass("op-a-tag-btn-disabled");
    },

    adjustProductInfoHeight: function() {
        let containerHeight = o_browse.calculateGalleryHeight();
        let footerHeight = $(".footer").outerHeight();
        let mainNavHeight = $(".op-reset-opus").outerHeight() +
                            $("#op-main-nav").innerHeight() - $("#op-main-nav").height();
        let downloadOptionsHeight = $(window).height() - (footerHeight + mainNavHeight);
        let cardHeaderHeight = $("#op-cart-download-panel .card-header").outerHeight();
        let downloadOptionsHeaderHeight = $(".op-download-options-header").outerHeight();
        let productTypesTableHeader = $(".op-product-type-table-header").outerHeight();
        let downloadContainerTopPadding = 0;
        if ( $("#cart-sidebar").length && $("#op-download-options-container").length) {
            downloadContainerTopPadding = $("#cart-sidebar").offset().top -
                                          $("#op-download-options-container").offset().top;
        }
        let downloadOptionsScrollableHeight = (downloadOptionsHeight - downloadOptionsHeaderHeight -
                                               productTypesTableHeader - downloadContainerTopPadding);

        $("#cart .op-gallery-contents").height(containerHeight);
        if ($(window).width() < cartLeftPaneThreshold) {
            downloadOptionsHeight = downloadOptionsHeight - cardHeaderHeight;
            downloadOptionsScrollableHeight = (downloadOptionsHeight - downloadOptionsHeaderHeight -
                                               productTypesTableHeader);
        }

        $("#cart .sidebar_wrapper").height(downloadOptionsHeight);
        $(".op-product-type-table-body").height(downloadOptionsScrollableHeight);

        if (o_cart.downloadOptionsScrollbar) {
            o_cart.downloadOptionsScrollbar.update();
        }

        o_cart.galleryScrollbar.update();
        o_cart.tableScrollbar.update();
    },

    updateCartStatus: function(status) {
        o_cart.totalObsCount = status.count + status.recycled_count;
        o_cart.recycledCount = status.recycled_count;
        o_cart.hideCartCountSpinner(status.count, status.recycled_count);
        if (status.total_download_size_pretty !== undefined && status.total_download_count !== undefined) {
            o_cart.hideDownloadSpinner(status.total_download_size_pretty, status.total_download_count);
        }

        if (status.recycled_count === 0) {
            $("[data-bs-target='#op-empty-recycle-bin-modal']").addClass("op-button-disabled");
            $("[data-bs-target='#op-restore-recycle-bin-modal']").addClass("op-button-disabled");
        } else {
            $("[data-bs-target='#op-empty-recycle-bin-modal']").removeClass("op-button-disabled");
            $("[data-bs-target='#op-restore-recycle-bin-modal']").removeClass("op-button-disabled");
        }

        if (status.count === 0) {
            $(".op-download-options").addClass("op-button-disabled");
        } else {
            $(".op-download-options").removeClass("op-button-disabled");
        }

        // update the panel numbers if we received them...
        if (status.product_cat_list !== undefined) {
            for (let index = 0; index < status.product_cat_list.length; index++) {
                let slugList = status.product_cat_list[index][1];
                for (let slugNdx = 0; slugNdx < slugList.length; slugNdx++) {
                    let slugName = slugList[slugNdx].slug_name;
                    $(`#op-product-${slugName} .op-options-obs`).html(o_utils.addCommas(slugList[slugNdx].product_count));
                    $(`#op-product-${slugName} .op-options-files`).html(o_utils.addCommas(slugList[slugNdx].download_count));
                    $(`#op-product-${slugName} .op-options-size`).html(slugList[slugNdx].download_size_pretty);
                }
            }
        }
    },

    // init an existing cart on page load
    initCart: function() {
        o_cart.showCartCountSpinner();

        // returns any user cart saved in session
        o_cart.lastRequestNo++;
        $.getJSON("/opus/__cart/status.json?reqno=" + o_cart.lastRequestNo, function(data) {
            if (data.reqno < o_cart.lastRequestNo) {
                return;
            }
            o_cart.updateCartStatus(data);
        });
    },

    // get Cart tab
    activateCartTab: function() {
        let view = opus.prefs.view;

        opus.getViewNamespace().galleryBoundingRect = o_browse.countGalleryImages();

        o_browse.updateBrowseNav();
        o_selectMetadata.render();   // just do this in background so there's no delay when we want it...

        if (o_cart.reloadObservationData) {
            let zippedFiles_html = $(".op-zipped-files", "#cart").html();
            $("#cart .op-results-message").hide();
            $("#cart .gallery").empty();
            $("#cart .op-data-table tbody").empty();
            o_browse.showPageLoaderSpinner();

            let hash = o_hash.getHash();

            // Figure out which product types are not selected
            let notSelectedProductsList = $("#op-cart-summary .op-download-options-product-types :checkbox:not(:checked)");
            let notSelectedProductInfoSlugName = [];
            $.each(notSelectedProductsList, function(index, linkObj) {
                notSelectedProductInfoSlugName.push($(linkObj).val());
            });
            let notSelected = "";
            if (hash !== "") {
                notSelected = "&";
            }
            notSelected += "unselected_types=" + notSelectedProductInfoSlugName.join();
            let selected = o_cart.getDownloadFiltersChecked();
            // make sure that if there are not types because this was a refresh, we reset the types to 'all'
            if (selected === "types=") {
                selected = "";
            }

            o_cart.lastProductCountRequestNo++;
            let url = `/opus/__cart/view.json?${hash}${notSelected}&${selected}&reqno=${o_cart.lastProductCountRequestNo}`;

            $.getJSON(url, function(data) {
                if (data.reqno < o_cart.lastProductCountRequestNo) {
                    return;
                }
                // this div lives in the nav menu template
                $("#op-download-options-container", "#cart").hide().html(data.html).fadeIn();
                o_cart.hideCartCountSpinner(data.count, data.recycled_count);
                o_cart.hideDownloadSpinner();

                // Init perfect scrollbar when .op-download-options-product-types is rendered.
                o_cart.downloadOptionsScrollbar = new PerfectScrollbar(".op-product-type-table-body", {
                    minScrollbarLength: opus.minimumPSLength,
                        suppressScrollX: true,
                });

                // Depending on the screen width, we move download data elements
                // to either original left pane or slide panel
                o_cart.displayCartLeftPane();

                if (o_cart.downloadInProcess) {
                    $(".spinner", "#op-cart-summary").fadeIn();
                }

                let startObsLabel = o_browse.getStartObsLabel();
                let startObs = Math.max(opus.prefs[startObsLabel], 1);
                startObs = (startObs > o_cart.totalObsCount  ? 1 : startObs);
                o_browse.loadData(view, true, startObs);

                if (zippedFiles_html) {
                    $(".op-zipped-files", "#cart").html(zippedFiles_html);
                }
            });
        } else {
            // Make sure "Add all results to cart" is still hidden in cart tab when user switches
            // back to cart tab without reloading obs data in cart tab.
            $("#op-obs-menu .dropdown-item[data-action='addall']").addClass("op-hide-element");
        }
    },

    isIn: function(opusId) {
        return  $("[data-id='"+opusId+"'].op-thumbnail-container").hasClass("op-in-cart");
    },

    // 3 actions:
    // Empty Cart - empty the cart completely;
    // Empty Recycle Bin - empty the recycle bin
    // Restore Recycle Bin - restore all observations in the recycle bin to the cart
    emptyCartOrRecycleBin: function(what) {
        // to disable clicks:
        o_utils.disableUserInteraction();
        o_browse.hideMetadataDetailModal();
        o_cart.showCartCountSpinner();
        o_cart.showDownloadSpinner();

        // what == "cart" or "recycleBin"
        let recycleBin = (what === "cart" ? 0 : 1);
        o_cart.lastRequestNo++;

        // change indicator to zero and let the server know:
        let url = `/opus/__cart/reset.json?reqno=${o_cart.lastRequestNo}&recyclebin=${recycleBin}&download=1`;

        $.getJSON(url, function(data) {
            if (data.reqno < o_cart.lastRequestNo) {
                return;
            }
            o_cart.reloadObservationData = true;
            o_browse.reloadObservationData = true;
            o_cart.observationData = {};
            opus.prefs.cart_startobs = 1;
            let detailCartElem = $(".op-detail-cart a");
            if (detailCartElem.length > 0) {
                detailCartElem.data("action", "add");
                detailCartElem.attr("title", "Add to cart");
                detailCartElem.find("i").attr("class", "fas fa-cart-plus fa-xs");
            }
            opus.changeTab("cart");
            o_utils.enableUserInteraction();
        });

/*        let buttonInfo = o_browse.cartButtonInfo("remove");
        $("#cart .op-thumbnail-container.op-in-cart [data-icon=cart]").html(`<i class="${buttonInfo["#cart"].icon} fa-xs"></i>`);
        $("#cart .op-thumbnail-container.op-in-cart").removeClass("op-in-cart");
        $("#cart .op-data-table-view input").prop("checked", false); */
    },

    restoreRecycleBin: function() {
        // to disable clicks:
        o_utils.disableUserInteraction();
        o_cart.showCartCountSpinner();
        o_cart.showDownloadSpinner();

        let tab = opus.getViewTab();
        o_cart.lastRequestNo++;

        let url = `/opus/__cart/addall.json?reqno=${o_cart.lastRequestNo}&view=cart&download=1&recyclebin=1`;

        $.getJSON(url, function(data) {
            if (data.reqno < o_cart.lastRequestNo) {
                return;
            }
            o_cart.updateCartStatus(data);
            o_utils.enableUserInteraction();
        });

        o_browse.reloadObservationData = true;
        let buttonInfo = o_browse.cartButtonInfo("restore");
        let selector = `#cart .op-thumb-overlay [data-icon="cart"]`;
        $(selector).html(`<i class="${buttonInfo["#cart"].icon} fa-xs"></i>`);
        $(selector).prop("title", buttonInfo["#cart"].title);
        $("#cart .op-thumbnail-container").addClass("op-in-cart");
        $("#cart .op-thumbnail-container .op-recycle-overlay").addClass("op-hide-element");
        $("#cart tr[data-id]").removeClass("text-success op-recycled");
        $("#cart .op-thumbnail-container[data-id] .op-recycle-overlay").addClass("op-hide-element");
        $(".op-gallery-view-body .op-cart-toggle").attr("title", `${buttonInfo[tab].title} (spacebar)`);
        $(".op-gallery-view-body .op-cart-toggle").html(`<i class="${buttonInfo[tab].icon} fa-2x float-left"></i>`);
    },

    // action = add/remove/addrange/removerange/addall
    getEditURL: function(opusId, action) {
        let tab = opus.getViewTab();
        let url = "/opus/__cart/" + action + ".json?";
        // only add to recycle bin if the edit occurs on the #cart tab
        let recycleBin = (tab === "#cart" ? 1 : 0);
        switch (action) {
            case "add":
                url += `opusid=${opusId}`;
                break;

            case "remove":
                url += `opusid=${opusId}&recyclebin=${recycleBin}`;
                break;

            case "addrange":
                url += `range=${opusId}&${o_hash.getHash()}`;
                break;

            case "removerange":
                url += `range=${opusId}&${o_hash.getHash()}&recyclebin=${recycleBin}`;
                break;

            case "addall":
                url += o_hash.getHash();
                break;
        }

        // Minor performance check - if we don't need a total download size, don't bother
        // Only the cart tab is interested in updating that count at this time.
        if (tab === "#cart") {
            url += "&download=1&" + o_cart.getDownloadFiltersChecked();
        }
        return url;
    },

    sendEditRequest: function(url) {
        o_cart.lastRequestNo++;
        o_utils.disableUserInteraction();
        return $.getJSON(url + "&reqno=" + o_cart.lastRequestNo);
    },

    toggleInCart: function(fromOpusId, toOpusId) {
        let tab = opus.getViewTab();

        let length = null;
        let fromIndex = null;
        let action = null;
        let elementArray = $(`${tab} .op-thumbnail-container`);
        let opusIdRange = fromOpusId;

        o_cart.reloadObservationData = true;

        o_cart.showCartCountSpinner();
        o_cart.showDownloadSpinner();
        o_browse.showPageLoaderSpinner();

        // handle it as range
        if (toOpusId !== undefined) {
            action = $(`${tab} .op-gallery-view`).data("infiniteScroll").options.rangeSelectOption;
            let fromObsNum = $(`${tab} .op-gallery-view`).data("infiniteScroll").options.rangeSelectObsNum;
            let toObsNum = o_browse.getGalleryElement(toOpusId).data("obs");

            // reorder if need be
            if (fromObsNum > toObsNum) {
                [fromObsNum, toObsNum] = [toObsNum, fromObsNum];
                [fromOpusId, toOpusId] = [toOpusId, fromOpusId];
            }
            opusIdRange = `${fromOpusId},${toOpusId}`;
            let fromElem = $(`${tab} .op-gallery-view`).find(`[data-obs=${fromObsNum}]`);
            let toElem = $(`${tab} .op-gallery-view`).find(`[data-obs=${toObsNum}]`);
            length = toObsNum - fromObsNum + 1;
            // note that only one of the range endpoints can potentially be not present in the DOM,
            // as we know the user just clicked on one of them to get here.
            if (fromElem.length > 0) {
                length = (toElem.length === 0 ? elementArray.length - $(`${tab} .op-thumbnail-container`).index(fromIndex) : length);
                fromIndex = $(`${tab} .op-thumbnail-container`).index(fromElem);
            } else {
                length = $(`${tab} .op-thumbnail-container`).index(toElem) + 1; // 0-based index
                fromIndex = 0;
            }
        } else {
            length = 1;
            let fromElem = o_browse.getGalleryElement(fromOpusId);
            fromIndex = $(`${tab} .op-thumbnail-container`).index(fromElem);
            action = (fromElem.hasClass("op-in-cart") ? "remove" : "add");
        }

        o_cart.editAndHighlightObs(elementArray.splice(fromIndex, length), opusIdRange, action);
        o_browse.undoRangeSelect(tab);
        return action;
    },

    addAllToCart: function() {
        /**
         * Add all observations to the cart. Also highlight all observations
         * in browse tab.
         */
        let tab = opus.getViewTab();
        // Set reloadObservationData to true to load the latest data in cart tab later
        // (call "/opus/__cart/view.html" in activateCartTab).
        o_cart.reloadObservationData = true;

        o_cart.showCartCountSpinner();
        o_cart.showDownloadSpinner();
        o_browse.showPageLoaderSpinner();

        let elementArray = $(`${tab} .op-thumbnail-container`);
        o_cart.editAndHighlightObs(elementArray, null, "addall");
        o_browse.undoRangeSelect(tab);
    },

    editAndHighlightObs: function(elementArray, opusIdRange, action) {
        /**
         * Perform add/remove/addrange/removerange/addall and highlight/de-highlight observations.
         */
        let url = o_cart.getEditURL(opusIdRange, action);

        // just so we don't have to continually check for both addrange and add...
        action = (action === "addrange" || action === "add" || action === "addall" ? "add" : action);
        let status = (action === "add" ?  "add" : "remove");
        let checked = (action === "add");

        // we use when here so that we can change the thumbnail highlighting while we wait for the json to return
        $.when(o_cart.sendEditRequest(url)).done(function(statusData) {
            o_utils.enableUserInteraction();
            if (statusData.error) {
                // if previous error modal is currently open, we store the error message for later displaying
                if ($("#op-cart-status-error-msg-modal").hasClass("show")) {
                    o_cart.statusDataErrorCollector.push(statusData.error);
                } else {
                    $("#op-cart-status-error-msg-modal .modal-body").text(statusData.error);
                    $("#op-cart-status-error-msg-modal").modal("show");
                }
            } else {
                $.each(elementArray, function(index, elem) {
                    let opusId = $(elem).data("id");
                    /// NOTE: we need to mark the elements on BOTH browse and cart page for delete but not recycle bin
                    if (action === "add") {
                        $(`.op-thumbnail-container[data-id=${opusId}]`).addClass("op-in-cart");
                        $(`#cart tr[data-id=${opusId}]`).removeClass("text-success op-recycled");
                        $(`#cart .op-thumbnail-container[data-id=${opusId}] .op-recycle-overlay`).addClass("op-hide-element");
                        if ($(`.op-gallery-view-body .op-cart-toggle[data-id="${opusId}"]`).length > 0) {
                            $(".op-gallery-view-body .op-metadata-details .op-recycle-modal").addClass("op-hide-element");
                        }
                    } else {
                        $(`.op-thumbnail-container[data-id=${opusId}]`).removeClass("op-in-cart");
                        $(`#cart tr[data-id=${opusId}]`).addClass("text-success op-recycled");
                        $(`#cart .op-thumbnail-container[data-id=${opusId}] .op-recycle-overlay`).removeClass("op-hide-element");
                        if ($(`.op-gallery-view-body .op-cart-toggle[data-id="${opusId}"]`).length > 0) {
                            $(".op-gallery-view-body .op-metadata-details .op-recycle-modal").removeClass("op-hide-element");
                        }
                    }
                    $("input[name="+opusId+"]").prop("checked", checked);
                    o_browse.updateCartIcon(opusId, status);
                });
                if (opus.getCurrentTab() === "detail") {
                    let buttonInfo = o_browse.cartButtonInfo(action);
                    let newAction = buttonInfo["#browse"].rangeTitle.split(" ")[0];
                    let opusId = $(".op-detail-cart a").data("id");
                    $(".op-detail-cart").html(`<a href="#" data-icon="cart" data-action="${newAction}" data-id="${opusId}" title="${buttonInfo["#browse"].title}"><i class="${buttonInfo["#browse"].icon}"></i></a>`);
                }
            }
            o_cart.updateCartStatus(statusData);
            o_browse.hidePageLoaderSpinner();
        });
    },

    showCartCountSpinner: function() {
        if (o_cart.cartCountSpinnerTimer === null) {
            o_cart.cartCountSpinnerTimer = setTimeout(function() {
                $("#op-cart-count").html(opus.spinner);
                if ($("#op-recycled-count").length) {
                    $("#op-recycled-count").html(opus.spinner);
                }
            }, opus.spinnerDelay);
        }
    },

    hideCartCountSpinner: function(cartCount, recycledCount) {
        $("#op-cart-count").html(o_utils.addCommas(cartCount));
        if ($("#op-recycled-count").length) {
            $("#op-recycled-count").html(o_utils.addCommas(recycledCount));
        }
        if (o_cart.cartCountSpinnerTimer !== null) {
            // This should always be true - we're just being careful
            clearTimeout(o_cart.cartCountSpinnerTimer);
            o_cart.cartCountSpinnerTimer = null;
        }
    },

    showDownloadSpinner: function() {
        if (o_cart.downloadSpinnerTimer === null) {
            o_cart.downloadSpinnerTimer = setTimeout(function() {
                $("#op-total-download-size").hide();
                $("#op-total-download-count").hide();
                $(".op-total-size .spinner").addClass("op-show-spinner");
                $(".op-total-download .spinner").addClass("op-show-spinner");
            }, opus.spinnerDelay);
        }
    },

    hideDownloadSpinner: function(downloadSize, downloadCount) {
        $(".op-total-size .spinner").removeClass("op-show-spinner");
        $(".op-total-download .spinner").removeClass("op-show-spinner");

        // for cart/download data panel only
        if (downloadSize !== undefined && downloadCount !== undefined) {
            $("#op-total-download-size").html(downloadSize).fadeIn();
            $("#op-total-download-count").html(o_utils.addCommas(downloadCount)).fadeIn();
        }

        if (o_cart.downloadSpinnerTimer !== null) {
            // This should always be true - we're just being careful
            clearTimeout(o_cart.downloadSpinnerTimer);
            o_cart.downloadSpinnerTimer = null;
        }
    },

    downloadCSV: function(obj) {
        let colStr = opus.prefs.cols.join(',');
        let orderStr = opus.prefs.order.join(",");
        $(obj).attr("href", `/opus/__cart/data.csv?cols=${colStr}&order=${orderStr}`);
    },
};
