var o_detail = {

    getDetail: function (opus_id) {

        $("#detail").on("click", ".download_csv", function() {
            $(this).attr("href", "/opus/__api/metadata_v2/"+opus_id+".csv?"+ o_hash.getHash());
        });

        $("#detail").on("click", "a[data-action]", function() {
            let href = $(this).attr("href").split('?')[0];
            switch($(this).data("action")) {
                case "downloadData":
                    $(this).attr("href", `/opus/__api/download/${opusId}.zip?cols=${opus.prefs.cols.join()}`);
                    break;
                case "downloadURL":
                    $(this).attr("href", `/opus/__api/download/${opusId}.zip?urlonly=1&cols=${opus.prefs.cols.join()}`);
                    break;
            }
            //return false;
        });

        opus.prefs.detail = opus_id;
        let detailSelector = "#detail .panel";

        if (!opus_id) {
            // helpful
            html = ' \
                <div style = "margin:20px"><h2>No Observation Selected</h2>   \
                <p>To view details about an observation, click on the Browse Results tab<br>  \
                at the top of the page. Click on a thumbnail and then "View Detail".</p>   \
                </div>'

            $(detailSelector).html(html).fadeIn();

            return;
        }

        $(detailSelector).html(opus.spinner);

        $(detailSelector).load("/opus/__initdetail/" + opus_id + ".html",
            function(response, status, xhr){
                if (status == 'error') {
                    html = ' \
                        <div style = "margin:20px"><h2>Bad OPUS ID</h2>   \
                        <p>The specified OPUS_ID (or old RING_OBS_ID) was not found in the database.</p>   \
                        </div>'

                    $(detailSelector).html(html).fadeIn();
                    return;
                }
                let arrOfDeferred = [];
                // get the column metadata, this part is fast
                url = "/opus/__api/metadata_v2/" + opus_id + ".html?" + o_hash.getHash();
                $("#cols_metadata_"+opus_id)
                    .load(url, function() {
                        $(this).hide().fadeIn("fast");
                    }
                );

                // get categories and then send for data for each category separately:
                url = "/opus/__api/categories/" + opus_id + ".json?" + o_hash.getHash();
                $.getJSON(url, function(categories) {
                    $.each(categories, function(idx, val) {
                        arrOfDeferred.push($.Deferred());
                    })

                    for (let index in categories) {
                        name = categories[index]['table_name'];
                        label = categories[index]['label'];
                        var html = '<h3>' + label + '</h3><div class = "detail_' + name + '">Loading <span class = "spinner">&nbsp;</span></div>'
                        $("#all_metadata_" + opus_id).append(html);

                        // now send for data
                        url ="/opus/__api/metadata_v2/" + opus_id + ".html?cats=" + name;
                        $("#all_metadata_" + opus_id + ' .detail_' + name)
                            .load(url, function() {
                                $(this).hide().slideDown("fast");
                                arrOfDeferred[index].resolve();
                            }
                        );

                    } // end json loop

                    // Wait until all .load are done, and then update perfectScrollbar
                    $.when.apply(null, arrOfDeferred).then(function() {
                        let initDetailPageScrollbar = _.debounce(o_detail.initAndUpdatePerfectScrollbar, 200);
                        initDetailPageScrollbar();
                    })
                });
            } // /detail.load
        );
    }, // / getDetail

    initAndUpdatePerfectScrollbar: function() {
        o_detail.detailPageScrollbar = new PerfectScrollbar(".detail-metadata");
        o_detail.detailPageScrollbar.update()
    },

    adjustDetailHeight: function() {
        let containerHeight = $(window).height()-100;
        if(o_detail.detailPageScrollbar) {
            $(".detail-metadata").height(containerHeight);
            o_detail.detailPageScrollbar.update();
        }
    },

};
