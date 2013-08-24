var o_detail = {

    getDetail: function (ring_obs_id) {
        opus.prefs['detail'] = ring_obs_id;
        $('#detail_tab').fadeIn();
        $('#detail').html(opus.spinner);
        $('#detail_extra').html(ring_obs_id);
        $("#tabs").tabs("select","#detail");
        $("#detail").load("/opus/api/detailpage/" + ring_obs_id + ".html", function(){ });
    },



};