/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* globals $, PerfectScrollbar */
/* globals o_browse, o_hash, opus */

/* jshint varstmt: false */
var o_cart = {
/* jshint varstmt: true */
    // cart
    cartChange: true, // cart has changed since last load of cart_tab
    lastRequestNo: 0,
    downloadInProcess: false,
    cartCount: 0,

    // collector for all cart status error messages
    statusDataErrorCollector: [],
    galleryBoundingRect: {'x': 0, 'y': 0},

    tableScrollbar: new PerfectScrollbar("#cart .op-data-table-view", {
        minScrollbarLength: opus.minimumPSLength
    }),
    galleryScrollbar: new PerfectScrollbar("#cart .op-gallery-view", {
        suppressScrollX: true,
        minScrollbarLength: opus.minimumPSLength
    }),
    downloadOptionsScrollbar: new PerfectScrollbar("#op-download-options-container", {
        minScrollbarLength: opus.minimumPSLength
    }),

    /**
     *
     *  managing cart communication between server and client and
     *  all interaction on the cart tab
     *
     *  for the visual interaction on the browse table/gallery view when adding/removing
     *  from cart see browse.js
     *
     **/

     cartBehaviors: function() {
        // nav bar
        $("#cart").on("click", ".op-download-csv", function(e) {
            let colStr = opus.prefs.cols.join(',');
            let orderStr = opus.prefs.order.join(",");
            $(this).attr("href", `/opus/__cart/data.csv?cols=${colStr}&order=${orderStr}`);
        });

        $("#cart").on("click", ".downloadData", function(e) {
            o_cart.downloadZip("create_zip_data_file", "Internal error creating data zip file");
        });

        $("#cart").on("click", ".downloadURL", function(e) {
            o_cart.downloadZip("create_zip_url_file", "Internal error creating URL zip file");
        });

        // check an input on selected products and images updates file_info
        $("#cart").on("click","#download_options input", function() {
            $("#op-total-download-size").hide();
            $(".op-total-size .spinner").addClass("op-show-spinner");

            let add_to_url = o_cart.getDownloadFiltersChecked();
            o_cart.lastRequestNo++;
            let url = "/opus/__cart/status.json?reqno=" + o_cart.lastRequestNo + "&" + add_to_url + "&download=1";
            $.getJSON(url, function(info) {
                if (info.reqno < o_cart.lastRequestNo) {
                    return;
                }
                $(".op-total-size .spinner").removeClass("op-show-spinner");
                $("#op-total-download-size").fadeOut().html(info.total_download_size_pretty).fadeIn();
            });
        });

        // Display the whole series of modals.
        // This will keep displaying multiple error message modals one after another when the previous modal is closed.
        $("#op-cart-status-error-msg").on("hidden.bs.modal", function(e) {
            if (o_cart.statusDataErrorCollector.length !== 0) {
                $("#op-cart-status-error-msg .modal-body").text(o_cart.statusDataErrorCollector.pop());
                $("#op-cart-status-error-msg").modal("show");
            }
        });
    },

    // download filters
    getDownloadFiltersChecked: function() {
        // returned as url string
        let productTypes = [];
        $("ul#product_types input:checkbox:checked").each(function() {
            productTypes.push($(this).val());
        });
        return "types="+productTypes.join(',');
    },

    downloadZip: function(type, errorMsg) {
        if (o_cart.downloadInProcess) {
            return false;
        }

        $("#op-download-links").show();
        opus.downloadInProcess = true;
        $(".spinner", "#op-download-links").fadeIn().css("display","inline-block");

        let add_to_url = o_cart.getDownloadFiltersChecked();
        let url = "/opus/__cart/download.json?" + add_to_url + "&" + o_hash.getHash();
        url += (type == "create_zip_url_file" ? "&urlonly=1" : "");
        $.ajax({
            url: url,
            dataType: "json",
            success: function(data) {
                if (data.error !== undefined) {
                    $(`<li>${data.error}</li>`).hide().prependTo("ul.zippedFiles", "#cart_summary").slideDown("fast");
                } else {
                    $(`<li><a href = "${data.filename}" download>${data.filename}</a></li>`).hide().prependTo("ul.zippedFiles", "#cart_summary").slideDown("slow");
                }
                $(".spinner", "#op-download-links").fadeOut();
            },
            error: function(e) {
                $(".spinner", "#op-download-links").fadeOut();
                $(`<li>${errorMsg}</li>`).hide().prependTo("ul.zippedFiles", "#cart_summary").slideDown("fast");
            },
            complete: function() {
                o_cart.downloadInProcess = false;
            }
        });
    },

    adjustProductInfoHeight: function() {
        let containerHeight = $(window).height()-120;
        let downloadOptionsContainer = $(window).height()-90;
        let cartSummaryHeight = $("#cart_summary").height();
        $("#cart .sidebar_wrapper").height(downloadOptionsContainer);
        $("#cart .gallery-contents").height(containerHeight);

        // The following steps will hide the y-scrollbar when it's not needed.
        // Without these steps, y-scrollbar will exist at the beginning, and disappear after the first attempt of scrolling
        if (downloadOptionsContainer > cartSummaryHeight) {
            if (!$("#op-download-options-container .ps__rail-y").hasClass("hide_ps__rail-y")) {
                $("#op-download-options-container .ps__rail-y").addClass("hide_ps__rail-y");
                o_cart.downloadOptionsScrollbar.settings.suppressScrollY = true;
            }
        } else {
            $("#op-download-options-container .ps__rail-y").removeClass("hide_ps__rail-y");
            o_cart.downloadOptionsScrollbar.settings.suppressScrollY = false;
        }

        o_cart.downloadOptionsScrollbar.update();
        o_cart.galleryScrollbar.update();
        o_cart.tableScrollbar.update();
    },

    updateCartStatus: function(status) {
        if (status.reqno < o_cart.lastRequestNo) {
            return;
        }
        o_cart.cartCount = status.count;
        $("#op-cart-count").html(o_cart.cartCount);
        if (status.total_download_size_pretty !== undefined) {
            $("#op-total-download-size").fadeOut().html(status.total_download_size_pretty).fadeIn();
        }
    },

    // init an existing cart on page load
    initCart: function() {
       // display cart badge spinner, it will get updated after the return of status.json
       $("#op-cart-count").html(opus.spinner);
       // returns any user cart saved in session
       o_cart.lastRequestNo++;
       $.getJSON("/opus/__cart/status.json?reqno=" + o_cart.lastRequestNo, function(statusData) {
           if (statusData.reqno < o_cart.lastRequestNo) {
               return;
           }
           o_cart.updateCartStatus(statusData);
       });
    },

    // get Cart tab
    getCartTab: function() {
        o_browse.renderMetadataSelector();   // just do this in background so there's no delay when we want it...
        if (o_cart.cartChange) {
            let zippedFiles_html = $(".zippedFiles", "#cart").html();

            // don't forget to remove existing stuff before append
            $("#cart .op-data-table > tbody").empty();  // yes all namespaces
            $("#cart .gallery").empty();

            // redux: and nix this big thing:
            $.ajax({ url: "/opus/__cart/view.html",
                success: function(html) {
                    // this div lives in the in the nav menu template
                    $("#op-download-options-container", "#cart").hide().html(html).fadeIn();

                    if (o_cart.downloadInProcess) {
                        $(".spinner", "#cart_summary").fadeIn();
                    }

                    let startObsLabel = o_browse.getStartObsLabel();
                    let startObs = opus.prefs[startObsLabel];
                    startObs = (startObs > o_cart.cartCount ? 1 : startObs);
                    o_browse.loadData(startObs);

                    if (zippedFiles_html) {
                        $(".zippedFiles", "#cart").html(zippedFiles_html);
                    }
                }
            });
        }
    },

    isIn: function(opusId) {
        return  $("[data-id='"+opusId+"'].thumbnail-container").hasClass("op-in-cart");
    },

    emptyCart: function(returnToSearch=false) {
        // change indicator to zero and let the server know:
        $.getJSON("/opus/__cart/reset.json", function(data) {
            $("#op-cart-count").html("0");
            o_cart.cartChange = true;
            $("#cart .navbar").hide();
            $("#cart .sort-order-container").hide();
            if (!returnToSearch) {
                opus.changeTab("cart");
            } else {
                opus.changeTab("search");
            }
        });

        let buttonInfo = o_browse.cartButtonInfo("in");
        $(".thumbnail-container.op-in-cart [data-icon=cart]").html(`<i class="${buttonInfo.icon} fa-xs"></i>`);
        $(".thumbnail-container.op-in-cart").removeClass("op-in-cart");
        $(".dataTable input").prop("checked", false);
    },

    toggleInCart: function(fromOpusId, toOpusId) {
        let fromElem = o_browse.getGalleryElement(fromOpusId);

        // handle it as range
        if (toOpusId != undefined) {
            let tab = opus.getViewTab();
            let action = (fromElem.hasClass("op-in-cart") ? "removerange" : "addrange");
            let toElem = o_browse.getGalleryElement(toOpusId);
            let fromIndex = $(`${tab} .thumbnail-container`).index(fromElem);
            let toIndex = $(`${tab} .thumbnail-container`).index(toElem);

            // reorder if need be
            if (fromIndex > toIndex) {
                [fromIndex, toIndex] = [toIndex, fromIndex];
            }
            let length = toIndex - fromIndex+1;
            /// NOTE: we need to mark the elements on BOTH browse and cart page
            let elementArray = $(`${tab} .thumbnail-container`);
            let opusIdRange = $(elementArray[fromIndex]).data("id") + ","+ $(elementArray[toIndex]).data("id");
            let addOpusIdList = [];
            $.each(elementArray.splice(fromIndex, length), function(index, elem) {
                let opusId = $(elem).data("id");
                let status = "in";
                if (action == "addrange") {
                    $(`.thumbnail-container[data-id=${opusId}]`).addClass("op-in-cart");
                    status = "out"; // this is only so that we can make sure the icon is a trash can
                } else {
                    $(`.thumbnail-container[data-id=${opusId}]`).removeClass("op-in-cart");
                    $(`.thumbnail-container[data-id=${opusId}]`).addClass("op-remove-from-cart");
                }
                $("input[name="+opusId+"]").prop("checked", (action == "addrange"));
                o_browse.updateCartIcon(opusId, status);
                // If we remove items from the cart on the cart page, the "ghosts" still stick around in the UI
                // but the backend doesn't know about them. This means you can't do an addrange in the UI that
                // includes ghosts because the backend won't know what you want to add. So for all addranges
                // we have to just add the observations one at a time, since we know what needs to be done here.
                if (action === "addrange" && opus.prefs.view === "cart") {
                    addOpusIdList.push(opusId);
                }
            });
            if (addOpusIdList.length !== 0) {
                let lastAddOpusId = addOpusIdList[addOpusIdList.length-1];
                for (const addOpusId of addOpusIdList) {
                    o_cart.editCart(addOpusId, "add", addOpusId === lastAddOpusId);
                }
            } else {
                o_cart.editCart(opusIdRange, action);
            }
            o_browse.undoRangeSelect(tab);
        } else {
            // note - doing it this way handles the obs on the browse tab at the same time
            let action = (fromElem.hasClass("op-in-cart") ? "remove" : "add");

            $(`.thumbnail-container[data-id=${fromOpusId}]`).toggleClass("op-in-cart");
            $("input[name="+fromOpusId+"]").prop("checked", (action === "add"));

            $(`#cart .thumbnail-container[data-id=${fromOpusId}]`).toggleClass("op-remove-from-cart");

            o_browse.updateCartIcon(fromOpusId, action);
            o_cart.editCart(fromOpusId, action);
            return action;
        }
    },

    // action = add/remove/addrange/removerange/addall
    editCart: function(opusId, action, updateBadges=true) {
        // If updateBadges is false, we set the spinners in motion but don't actually update them
        // This is used when we want to do a lot of cart operations in a row and only update
        // at the end
        o_cart.cartChange = true;

        let url = "/opus/__cart/" + action + ".json?";
        switch (action) {
            case "add":
            case "remove":
                url += "opusid=" + opusId;
                break;

            case "removerange":
            case "addrange":
                url += `range=${opusId}&${o_hash.getHash()}`;
                break;

            case "addall":
                url += o_hash.getHash();
                break;
        }

        // Minor performance check - if we don't need a total download size, don't bother
        // Only the cart tab is interested in updating that count at this time.
        let add_to_url = "";
        if (opus.prefs.view === "cart" && updateBadges) {
            add_to_url = "&download=1&" + o_cart.getDownloadFiltersChecked();
        }

        // display spinner next to cart badge & total size
        $("#op-cart-count").html(opus.spinner);
        $("#op-total-download-size").hide();
        $(".op-total-size .spinner").addClass("op-show-spinner");

        o_cart.lastRequestNo++;
        $.getJSON(url  + add_to_url + "&reqno=" + o_cart.lastRequestNo, function(statusData) {
            // display modal for every error message returned from api call
            if (statusData.error) {
                // if previous error modal is currently open, we store the error message for later displaying
                if ($("#op-cart-status-error-msg").hasClass("show")) {
                    o_cart.statusDataErrorCollector.push(statusData.error);
                } else {
                    $("#op-cart-status-error-msg .modal-body").text(statusData.error);
                    $("#op-cart-status-error-msg").modal("show");
                }
                // reload data
                // Note: we don't return after loadData because we still have to update the result count in cart badge (updateCartStatus)
                o_browse.galleryBegun = false;
                o_browse.loadData(1);
            }
            // we only update the cart badge result count from the latest request
            if (statusData.reqno < o_cart.lastRequestNo || !updateBadges) {
                return;
            }

            $(".op-total-size .spinner").removeClass("op-show-spinner");
            o_cart.updateCartStatus(statusData);
        });
    },
};
