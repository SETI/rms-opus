var o_detail = {

    getDetail: function (ring_obs_id) {

        opus.prefs['detail'] = ring_obs_id;
        $('#detail_tab').fadeIn();

        if (!ring_obs_id) {
            // helpful
            html = ' \
                <div style = "margin:20px"><h2>No Observation Selected</h2>   \
                <p>To view details about an observation, click on the Browse Results tab<br>  \
                at the top of the page. Click on a thumbnail and then "View Detail".</p>   \
                </div>'

            $(html).appendTo($('#detail')).fadeIn();
            return;
        }

        $('#detail').html(opus.spinner);
        $('#detail_extra').html(ring_obs_id);

        $("#detail").load("/opus/api/detail/" + ring_obs_id + ".html", function(){

            // get the column metadata, this part is fast
            url = "/opus/api/metadata/" + ring_obs_id + ".html?" + o_hash.getHash();
            $("#cols_metadata")
                .load(url, function() {
                    $(this).hide().fadeIn("fast");
                }
            );

            // get categories and then send for data for each category separately:
            url = "/opus/api/categories/" + ring_obs_id + ".json?" + o_hash.getHash();
            $.getJSON(url, function(json) {
                for (var index in json) {
                  name = json[index]['table_name'];
                  label = json[index]['label'];
                  var html = '<h3>' + label + '</h3><div class = "detail_' + name + '">Loading <span class = "spinner">&nbsp;</span></div>'
                  $("#all_metadata_" + ring_obs_id).append(html);

                  // now send for data
                  url ="/opus/api/metadata/" + ring_obs_id + ".html?cats=" + name;
                  $("#all_metadata_" + ring_obs_id + ' .detail_' + name)
                      .load(url, function() {
                          $(this).hide().slideDown("fast");
                      }
                  );
                } // end json loop

            });

          } // /detail.load
        );
    }, // / getDetail

};
