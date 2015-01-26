var o_detail = {

    getDetail: function (ring_obs_id) {
        opus.prefs['detail'] = ring_obs_id;
        $('#detail_tab').fadeIn();
        $('#detail').html(opus.spinner);
        $('#detail_extra').html(ring_obs_id);

        $("#detail").load("/opus/api/detail/" + ring_obs_id + ".html", function(){

            // get the column metadata
            url = "/opus/api/metadata/" + ring_obs_id + ".html?" + o_hash.getHash();
            $("#cols_metadata")
                .load(url, function() {
                    $(this).hide().fadeIn("fast");
                }
            );

            // it might be good here to instead:
            // - ask for list of tables
            // - stub out the menu
            // - send separate ajax call all at once for each table
            //   (yay apache will give us multithreading!)
            url ="/opus/api/metadata/" + ring_obs_id + ".html";
            $("#all_metadata")
                .load(url, function() {
                    $(this).hide().fadeIn("fast");
                }
            );
            }
        );
    }, // / getDetail

};