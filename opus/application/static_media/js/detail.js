/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $, _, PerfectScrollbar */
/* globals o_hash, opus, o_browse, o_cart, o_utils */

/* jshint varstmt: false */
var o_detail = {
/* jshint varstmt: true */

    activateDetailTab: function(opusId) {

        // Get the x & y coordinate of the current cursor when moving mouse in detail preview
        // image. Reposition the tooltip based on the cursor location.
        $("#detail").on("mousemove", ".op-detail-prev-img-tooltip" , function(e) {
            o_utils.onMouseMoveHandler(e, $(e.target));
        });

        $("#detail").on("click", ".op-download-csv", function() {
            let colStr = opus.prefs.cols.join(',');
            $(this).attr("href", `/opus/__api/metadata/${opusId}.csv?cols=${colStr}`);
        });

        $("#detail").on("click", "a[data-action]", function() {
            let action = $(this).data("action");
            let opusId = $(this).data("id");
            switch(action) {
                case "add":
                case "remove":
                    if (opusId) {
                        o_browse.reloadObservationData = true;
                        o_cart.reloadObservationData = true;
                        o_utils.disableUserInteraction();
                        o_cart.editAndHighlightObs([], opusId, action);
                    }
                    break;
                case "downloadData":
                    $(this).attr("href", `/opus/__api/download/${opusId}.zip?cols=${opus.prefs.cols.join()}`);
                    break;
                case "downloadURL":
                    $(this).attr("href", `/opus/__api/download/${opusId}.zip?urlonly=1&cols=${opus.prefs.cols.join()}`);
                    break;
                case "share":
                    if (opusId) {
                        let urlToShare = $(this).attr("href");
                        o_detail.copyToClipboard(urlToShare)
                            .then(() => o_detail.showShareMessage("URL copied!"))
                            .catch(() => o_detail.showShareMessage("Error copying URL"));
                    }
                    break;
            }
            return false;
        });

        opus.prefs.detail = opusId;
        let detailSelector = "#detail .panel";

        if (!opusId) {
            // helpful
            let html = ' \
                <div style = "margin:20px"><h2>No Observation Selected</h2>   \
                <p>To view details about an observation, click on the Browse Results tab<br>  \
                at the top of the page. Click on a thumbnail and then "View Detail".</p>   \
                </div>';

            $(detailSelector).html(html).fadeIn();

            return;
        }

        $(detailSelector).html(opus.spinner);

        $(detailSelector).load("/opus/__initdetail/" + opusId + ".html",
            function(response, status, xhr) {
                if (status == 'error') {
                    let html = ' \
                        <div style = "margin:20px"><h2>Bad OPUS ID</h2>   \
                        <p>The specified OPUS_ID (or old RING_OBS_ID) was not found in the database.</p>   \
                        </div>';

                    $(detailSelector).html(html).fadeIn();
                    return;
                }
                let urlToShare = `${window.location.origin}${window.location.pathname}#/view=detail&detail=${opusId}`;
                $(".op-detail-share a[data-action='share']").attr("href", urlToShare);

                let colStr = opus.prefs.cols.join(',');
                let arrOfDeferred = [];
                // get the column metadata, this part is fast
                let urlMetadataColumn = `/opus/__api/metadata/${opusId}.html?${o_hash.getHash()}&url_cols=${colStr}`;
                $("#cols_metadata_"+opusId)
                    .load(urlMetadataColumn, function() {
                        $(this).hide().fadeIn("fast");
                    }
                );

                // get categories and then send for data for each category separately:
                let urlCategories = "/opus/__api/categories/" + opusId + ".json?" + o_hash.getHash();
                $.getJSON(urlCategories, function(categories) {
                    $.each(categories, function(idx, val) {
                        arrOfDeferred.push($.Deferred());
                    });

                    for (let idx = 0; idx < categories.length; idx++) {
                        const currentDeferred = arrOfDeferred[idx];
                        let tableName = categories[idx].table_name;
                        let label = categories[idx].label;
                        let html = '<h3>' + label + '</h3><div class="detail_' + tableName + '">Loading <span class="spinner">&nbsp;</span></div>';
                        $("#all_metadata_" + opusId).append(html);

                        // now send for data
                        let urlMetadata = `/opus/__api/metadata/${opusId}.html?cats=${tableName}&url_cols=${colStr}`;
                        $("#all_metadata_" + opusId + ' .detail_' + tableName).load(urlMetadata, function() {
                                $(this).hide().slideDown("fast");
                                currentDeferred.resolve();
                            }
                        );

                    } // end json loop

                    // Wait until all .load are done, and then update perfectScrollbar
                    $.when.apply(null, arrOfDeferred).then(function() {
                        let initDetailPageScrollbar = _.debounce(o_detail.initAndUpdatePerfectScrollbar, 200);
                        initDetailPageScrollbar();
                        // Initialize all tooltips using tooltipster in the metadata area of the detail tab
                        $(".op-detail-metadata-tooltip").tooltipster({
                            maxWidth: opus.tooltipsMaxWidth,
                            theme: opus.tooltipsTheme,
                            delay: opus.tooltipsDelay,
                        });
                        // Init flexslider
                        $('.flexslider').flexslider({
                            pauseOnHover: true,
                            slideshow: false,
                            prevText: "",
                            nextText: ""
                        });
                        o_detail.adjustDetailImgNavBtns();
                    });
                });
                // Initialize all tooltips using tooltipster in detail.html
                $(".op-detail-tooltip").tooltipster({
                    maxWidth: opus.tooltipsMaxWidth,
                    theme: opus.tooltipsTheme,
                    delay: opus.tooltipsDelay,
                });
                $(".op-detail-prev-img-tooltip").tooltipster({
                    maxWidth: opus.tooltipsMaxWidth,
                    theme: opus.tooltipsTheme,
                    delay: opus.tooltipsDelay,
                    // Make sure the tooltip position is next to the cursor when users mouse
                    // over to the detail preview image.
                    functionPosition: function(instance, helper, position){
                        return o_utils.setPreviewImageTooltipPosition(helper, position);
                    }
                });

            } // /detail.load
        );
    }, // / activateDetailTab

    copyToClipboard: function(urlToCopy) {
        // navigator clipboard api needs a secure context (https)
        if (navigator.clipboard && window.isSecureContext) {
            // navigator clipboard api method'
            return navigator.clipboard.writeText(urlToCopy);
        } else {
            // text area method
            let textArea = document.createElement("textarea");
            textArea.value = urlToCopy;
            // make the textarea out of viewport
            textArea.style.position = "fixed";
            textArea.style.left = "-999999px";
            textArea.style.top = "-999999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            return new Promise((res, rej) => {
                // here the magic happens
                if (document.execCommand('copy')) {
                    res();
                } else {
                    rej();
                }
                textArea.remove();
            });
        }
    },

    showShareMessage: function(message) {
        $(".op-share-message").text(message).fadeIn();
        setTimeout(function() {
            $(".op-share-message").fadeOut("slow");
        }, 2000 );
    },

    // Note: PS is init every time when html is rendered. The previous PS will be garbage collected and there isn't a memory leak here even though we're calling new (to init ps) over and over.
    initAndUpdatePerfectScrollbar: function() {
        // Enable default scrollbar for Ctrl + F search scroll to work in Chrome and Firefox.
        if (opus.currentBrowser === "chrome" || opus.currentBrowser === "firefox") {
            $(".op-detail-metadata").addClass("op-enable-default-scrolling");
        }

        o_detail.detailPageScrollbar = new PerfectScrollbar(".op-detail-metadata", {
            minScrollbarLength: opus.minimumPSLength,
            suppressScrollX: true,
        });
        o_detail.adjustDetailHeight();
    },

    showDetailThumbInNav: function(imageHtml) {
        if (imageHtml === undefined) {
            if (opus.prefs.detail != "") {
                let url = "/opus/__api/image/thumb/" + opus.prefs.detail + ".json";
                $.getJSON(url, function(image)  {
                    let imageObj = image.data[0];
                    imageHtml = `<img class="op-nav-detail-image op-detail-img-tooltip" src="${imageObj.url}"
                                      alt="${imageObj.alt_text}"
                                      title="${imageObj.opus_id}">`;
                    $("#op-main-nav .nav-link .op-selected-detail").html(`${imageHtml}`);

                    // Init tooltip of the detail prev image in the main nav bar
                    $(".op-detail-img-tooltip").tooltipster({
                        maxWidth: opus.tooltipsMaxWidth,
                        theme: opus.tooltipsTheme,
                        delay: opus.tooltipsDelay,
                    });
                });
            }
        } else {
            $("#op-main-nav .nav-link .op-selected-detail").html(`${imageHtml}`);
        }
        // Init tooltip of the cart button in detail tab
        $(".op-detail-cart-tooltip").tooltipster({
            maxWidth: opus.tooltipsMaxWidth,
            theme: opus.tooltipsTheme,
            delay: opus.tooltipsDelay,
        });
    },

    adjustDetailHeight: function() {
        let footerHeight = $(".footer").outerHeight();
        let mainNavHeight = $("#op-main-nav").outerHeight();
        let detailTabPaddingTop = ($("#detail").outerHeight() - $("#detail").height())/2;
        let detailHeaderHeight = $(".op-detail-metadata-header h1").outerHeight(true) + $(".op-detail-metadata-header .row").outerHeight(true);
        // When detail image is moved to the top of detail left pane, we have to
        // account for the height of detail image as well when calculating the containerHeight
        let detailImgHeight = 0;
        if ($(".op-detail-img").length && $(".op-detail-metadata-container").length) {
            detailImgHeight = ($(".op-detail-img").offset().top !== $(".op-detail-metadata-container").offset().top ?
                               $(".op-detail-img").outerHeight() : 0);
        }
        let containerHeight = ($(window).height() - footerHeight - mainNavHeight -
                               detailHeaderHeight - detailTabPaddingTop - detailImgHeight);

        if (o_detail.detailPageScrollbar) {
            $(".op-detail-metadata").height(containerHeight);
            o_detail.detailPageScrollbar.update();
        }
    },

    // Adjust the positions of detail preview image nav buttons "<" & ">" to make them
    // stay right next to the image at both sides.
    adjustDetailImgNavBtns: function() {
            // By default when css left & right of "<" & ">" are 0, those two buttons stay
            // within the image container with their arrow tips touching the left & right
            // borders of the container. The width of "<" & ">" is bit more than 25px.
            // To move buttons out of the image, we need to set css left & right to at least
            // -(26px + some values) so that buttons won't be too close the image.
            // Therefore we pick 40 here.
            let offset = 40;
            let imgWidth = $(".op-detail-img img").outerWidth();
            let imgContainerWidth = $(".op-no-select .flexslider").outerWidth();
            let distanceBetweenImgAndNavBtns = (imgContainerWidth-imgWidth)/2 - offset;

            $(".flexslider .flex-direction-nav .flex-prev").css("left", distanceBetweenImgAndNavBtns);
            $(".op-detail-img .flexslider:hover .flex-direction-nav .flex-prev").css("left", distanceBetweenImgAndNavBtns);
            $(".flexslider .flex-direction-nav .flex-next").css("right", distanceBetweenImgAndNavBtns);
            $(".op-detail-img .flexslider:hover .flex-direction-nav .flex-next").css("right", distanceBetweenImgAndNavBtns);
    },

};
