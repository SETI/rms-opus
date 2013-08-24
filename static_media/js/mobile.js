$(document).ready(function() {

    $('#gallery li').live("tap", function(){
        $(this).addClass('gallery_hover').removeClass('gallery_default');
        $(mopus.thumb_clicked).removeClass('gallery_hover').addClass('gallery_visited');
        mopus.thumb_clicked = this;
    });
    $('#gallery li').live("click", function(){
           $(this).addClass('gallery_hover').removeClass('gallery_default');
           $(mopus.thumb_clicked).removeClass('gallery_hover').addClass('gallery_visited');
           mopus.thumb_clicked = this;
    });

    // user clicks menu link to gallery page
    $('.gallery_link').live("click",function() {
         console.log('gallery_link clicked');
         $("#gallery li").remove();
         mopus.volume_id = $(this).attr("id").split('__')[1];
         mopus.page=1
         mopus.getGallery(mopus.volume_id,1);
    });

    // checks to 'more' footer bar
    $('#more_gallery').live("click",function() {
        mopus.more_gallery_clicked++
        mopus.getGallery(mopus.volume_id,mopus.more_gallery_clicked)
    });

    // turn off the interval timer when gallery page is not showing, turn it back on when returning
    $('#gallery_page').live('pageshow',function(event,ui) {
        console.log('page show');
        mopus.gallery_watch_return_interval = setInterval(mopus.galleryScrollWatch, mopus.scroll_interval);
    });
    $('#gallery_page').live('pagehide',function(event,ui) {
        console.log('page HIDE');
        // mopus.gallery_watch_interval = clearInterval(mopus.gallery_watch_interval);
    });

});

var mopus = {

   scroll_interval:500,

   page:1,

   volume_id:'',

   gallery_watch_interval:'',

   thumb_clicked:'',

   getGallery: function(volume_id,page) {

        mopus.gallery_watch_interval = clearInterval(mopus.gallery_watch_interval);
        mopus.gallery_watch_return_interval = clearInterval(mopus.gallery_watch_return_interval);

        if($("#gallery").is(":hidden")) {
            // gallery view is hidden
            if ($('#detail').is(":hidden") == false) {
                // detail is showing, don't get a gallery
                return;
            }
            else {
                // gallery and detail are not showing, set page back to 1 and return;
                mopus.page=1;
                return;
            }
        }

        page = mopus.page++;
        console.log('going for page ' + page)

        $('#gallery_footer1').html('<p class = "spinner">&nbsp;</p>');

        url = "/opus/mobile/gallery/" + volume_id + '/' + page + '.json';
        $.ajax({ url:url,
            success: function(json) {
                var static_url = json['static'];
                var data = json['data'];
                var loaded = 0;
                var total = json['data'].length;
                var images = [];

                // here we preload all the images before writing them to the DOM
                // which removes some mobile browser strangeness
                // preloading inspired by brilliance! --> http://binarykitten.me.uk/dev/jq-plugins/107-jquery-image-preloader-plus-callbacks.html
                var html = '';
                for (var i=0;i<data.length;i++) {
                    var ring_obs_id = data[i][0];
                    var thumb = static_url + data[i][1];
                    images[i] = new Image();
                    images[i].src = thumb;
                    html += '<li class = "gallery_default" id = "thumb__' + ring_obs_id + '">' +
                    		        '<a data-rel="dialog" href = "/mobile/image/' + ring_obs_id + '.html">' +
                    			        '<img src = "' + thumb + '">' +
                    		        '</a></li>';
                    images[i].onload = function() {
                        loaded++;
                        if (loaded == total) {
                            $(html).appendTo('#gallery');
                            $('#gallery_footer1').html('<p>&nbsp;</p>');
                            mopus.gallery_watch_interval = setInterval(mopus.galleryScrollWatch, mopus.scroll_interval);                        }
                    }
                }
            }
        });
    },

    lastImageScrolledIntoView: function() {

            if (!$('#gallery li').last().offset()) return;

            var docViewTop = $(window).scrollTop();
            var docViewBottom = docViewTop + $(window).height();

            var elemTop = $('#gallery li').last().offset().top;
            var elemBottom = elemTop + $('#gallery li').last().height();

            var lg = [docViewTop, docViewBottom, elemTop,elemBottom ];

            /** debuggy stuff
            if ((elemBottom >= docViewTop) && (elemTop <= docViewBottom)
              && (elemBottom <= docViewBottom) &&  (elemTop >= docViewTop) ) {
                  console.log(true);
                  id = $('#gallery li').last().attr('id');
                  console.log('for ' + id);
              } else console.log(false);
            **/

            return ((elemBottom >= docViewTop) && (elemTop <= docViewBottom)
              && (elemBottom <= docViewBottom) &&  (elemTop >= docViewTop) );
        },

        galleryScrollWatch: function() {

            if (mopus.lastImageScrolledIntoView()) {
                mopus.getGallery(mopus.volume_id);
            }
        },


}