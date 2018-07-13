var o_browse = {

    /**
    *
    *  all the things that happen on the browse tab
    *
    *  do not underestimate this most magical method:
    • 
    •  o_browse.updatePage(no)
    *
    **/

    browseBehaviors: function() {

        // close the embedded metadata box
        $('#browse').on("click", ".embedded_data_viewer .fa-times ", function() {
            o_browse.embedded_data_viewer_toggle();
            opus.current_metadatabox = false;
            $(' .thumb_overlay').removeClass("browse_image_selected");  // remove any old

        });

        // mouse over a thumbnail
        $('#browse')
            .on("mouseenter", "ul.ace-thumbnails li",  // , ul.ace-thumbnails li>.tools
                function() {
                    $(this).find('.thumb_overlay').addClass("gallery_image_focus");
                })
            .on('mouseleave', 'ul.ace-thumbnails li', function() {
                // check and see if it should not be removed because it's being displayed in colorbox/embedded viewer
                if (!$(this).find('.thumb_overlay').hasClass('browse_image_selected')) {
                    $(this).find('.thumb_overlay').removeClass("gallery_image_focus");
                }
            });

        // browse nav menu - the gallery/table toggle
        $('#browse').on("click", '.browse_view', function() {

            clearInterval(opus.scroll_watch_interval); // hold on cowgirl only 1 page at a time

            var browse_view = $(this).text().split(' ')[1];  // data or gallery
            var hiding, showing;
            if (browse_view == 'gallery') {
                hiding = 'data';
                showing = 'gallery';
            } else {
                hiding = 'gallery';
                showing = 'data';
            }

            opus.prefs.browse = showing;
            o_hash.updateHash();

            $('.' + hiding, namespace).hide();
            $('.' + showing, namespace).fadeIn();

            // change the text on the link in the browse nav
            if (opus.prefs.browse == 'gallery') {
                // show the gallery's data viewer if something is selected:
                if ($('.browse_image_selected').length) {
                    o_browse.embedded_data_viewer_toggle();
                }

                // change the menu text
                $('.browse_view', namespace).text('view table');

            } else { // if not gallery

                // hide the gallery's embedded data viewer
                if ($('.embedded_data_viewer_wrapper').is(':visible')) {
                    o_browse.embedded_data_viewer_toggle();
                }

                // change the menu text
                $('.browse_view', namespace).text('view gallery');
            }

            // do we need to fetch a new browse tab?
            if ((opus.prefs.browse == 'gallery' && !opus.gallery_begun) ||
                (opus.prefs.browse == 'data' && !opus.table_headers_drawn)) {
                o_browse.getBrowseTab();
            } else {
                // not loading browse, turn scroll watch back on
                clearInterval(opus.scroll_watch_interval);  // always shut off just before, just in case
                opus.scroll_watch_interval = setInterval(o_browse.browseScrollWatch, 1000);
            }

            // reset scroll position
            window.scroll(0,opus.browse_view_scrolls[showing]); // restore previous scroll position

            return false;
        });

        // browse nav menu - download csv
        $('#browse').on("click", '.download_csv', function() {
            var col_str = opus.prefs.cols.join(',');
            var hash = [];
            for (var param in opus.selections) {
                if (opus.selections[param].length){
                    hash[hash.length] = param + '=' + opus.selections[param].join(',').replace(/ /g,'+');
                }
            }
            var q_str = hash.join('&');
            var csv_link = "/opus/api/data.csv?" + q_str + '&cols=' + col_str + '&limit=' + opus.result_count.toString();
            $(this).attr("href", csv_link);
        });

        // browse nav menu - add all to collection
        $('#browse').on("click", '.addall', function() {
          o_collections.editCollection('','addall');
          o_browse.checkAllRenderedElements();
          return false;
        });

        // browse nav menu - add range - begins add range interaction
        $('#browse').on("click", '.addrange', function() {
            // if someone clicks 'add range' this method
            // sets the addrange_clicked to true
            // then if they click a thumbnail next it is considered
            // part of the range
            var container =  $('.cart_control', '#browse');
            var link = $('.addrange', '#browse');
            var button_text = link.html();
            var element_name = 'thumbnail';
            if (opus.prefs.browse == 'data') {
              element_name = 'row';
            }
            var start_hint = "click on a " + element_name + " to define a range of selections";

            if (button_text = "add range") {
                // the first click of 'add range' begins the add-range interaction
                opus.addrange_clicked = true;
                link.html("select range start");
                link.popover('destroy');
                container.popover({
                  content: start_hint,
                  trigger:"click",
                  placement: "bottom",
                });
            }

          return false;

        });

        // data_table - clicking a table row adds to cart
        $('#browse').on("click", ".data_table tr", function() {

            var opus_id = $(this).attr("id").substring(6);
            $(this).find('.data_checkbox').toggleClass('fa-check-square-o').toggleClass('fa-square-o');
            var action = 'remove';
            if ($(this).find('.data_checkbox').hasClass('fa-check-square-o')) {
                // this is checked, we are unchecking it now
                action = 'add';
            }

            // make sure the checkbox for this observation in the other view (either data or gallery)
            // is also checked/unchecked - if that view is drawn
            try {
                o_browse.toggleBrowseInCollectionStyle(opus_id);
            } catch(e) { } // view not drawn yet so no worries

            // check if we are clicking as part of an 'add range' interaction
            if (!opus.addrange_clicked) {

                // no add range, just add this obs to collection
                o_collections.editCollection(opus_id,action);

            } else {
                o_browse.addRangeHandler(opus_id);
            }

        });


        // click embedded_data_viewer_image opens colorbox
        $('#browse').on("click", '.embedded_data_viewer_image a', function() {
            var opus_id = $(this).data("opus_id");
            $('#gallery__' + opus_id + "> a").trigger("click");
            return false;
        });


        // click thumbnail opens embedded data viewer
        $('.gallery').on("click", ".activeThumbnail", function(e) {
            // e.preventDefault();

            var opus_id = $(this).parent().attr("id").substring(9);

            if (opus.addrange_clicked) {
               // well actually they are selecting a range endpoint 'add range'
               // so they don't want data viewer they want 'add to cart''
               o_browse.toggleBrowseInCollectionStyle(opus_id);
               o_browse.cart_click_handler(opus_id, 'add');
               return false;
            }

            // if the user clicked on actual thumbnail, update the metadata box
            // if the user clicked on the metadata box image, show the colorbox
            if (!e.isTrigger) {
                // they clicked a thumbnail, open the embedded data viewer
                o_browse.updateEmbeddedMetadataBox(opus_id);
                return false;
            }

        });

        // thumbnail overlay tools
        $('.gallery').on("click", ".tools-bottom a", function(e) {
            $(this).parent().show();  // whu?

            var opus_id = $(this).parent().parent().attr("id").substring(9);

            // clicking thumbnail opens embedded data viewer
            if ($(this).hasClass('colorbox')) {
                $('#gallery__' + opus_id + "> a").trigger("click");
            }

            // click to view detail page
            if ($(this).find('i').hasClass('glyphicon-info-sign')) {
                if (e.shiftKey || e.ctrlKey || e.metaKey) {
                    // handles command click to open in new tab
                    var link = "/opus/#/" + o_hash.getHash();
                    link = link.replace("view=browse", "view=detail");
                    window.open(link, '_blank');
                } else {
                    o_browse.openDetailTab(opus_id);
                }
                // leave a highlight on the clicked thumbnail
                $(' .thumb_overlay').removeClass("gallery_image_focus").removeClass("browse_image_selected");  // remove any old
                $('#gallery__' + opus_id + ' .thumb_overlay').addClass("gallery_image_focus browse_image_selected");

                return false;
            }

            // click spyglass thingy to view colorbox
            if ($(this).find('i').hasClass('glyphicon-resize-full')) {
                // trigger colorbox, same as clicking anywhere on the thumbnail
                $('#gallery__' + opus_id + "> a").trigger("click");
            }

            // click to add/remove from  cart
            // gallery thumbnail cart checkmark thing
            if ($(this).find('i').hasClass('glyphicon-ok')) {
                // toggle thumbnail indicator state
                o_browse.toggleBrowseInCollectionStyle(opus_id);

                var icon_a_element = $('#gallery__' + opus_id + ' .tools-bottom a').parent();
                // is this checked? or unchecked..
                var action = 'remove';
                if (icon_a_element.hasClass("in")) {
                    action = 'add';  // this opus_id is being added to cart
                }
                o_browse.cart_click_handler(opus_id, action)
            }

            return false;
        }); // end click a browse tools icon


        // click table column header to reorder by that column
        $('#browse').on("click", '.data_table th a',  function() {
            var order_by =  $(this).data('slug');
            if (order_by == 'collection') {
              // Don't do anything if clicked on the "Selected" column
              return false;
            }
            var order_indicator = $(this).find('.column_ordering');
            if (order_indicator.hasClass('fa-sort-asc')) {
                // currently ascending, change to descending order
                order_indicator.removeClass('fa-sort-asc');
                order_indicator.addClass('fa-sort-desc');
                order_by = '-' + order_by;
            } else if (order_indicator.hasClass('fa-sort-desc')) {
                // change to not ordered
                order_indicator.removeClass('fa-sort-desc');
                order_by = "";

            } else {
                // not currently ordered, change to ascending
                order_indicator.addClass('fa-sort-asc');
            }
            opus.prefs['order'] = order_by;
            opus.prefs.page = default_pages; // reset pages to 1 when col ordering changes

            o_browse.updatePage();
            return false;
        });


        // results paging - next/prev links
        $("#browse").on("click", "a.next, a.prev", function() {
            // all this does is update the number that shows in the box and then calls textInputMonitor

            clearInterval(opus.scroll_watch_interval);  // turn this off while manually paging

            var view_info = o_browse.getViewInfo();
            var namespace = view_info['namespace']; // either '#collection' or '#browse'
            var prefix = view_info['prefix'];       // either 'colls_' or ''

            var page_no_elem = $('input#page');
            var this_page = page_no_elem.val();
            if (!this_page) {
                this_page = opus.prefs[prefix + 'page'];
            }

            var page = parseInt(this_page, 10);
            if ( $(this).hasClass("next")) {
                page++;
            } else if ($(this).hasClass("prev")) {
                page--;
            }
            if (page >=1 && page <= opus.pages) {
              page_no_elem.css('color', 'red');
              page_no_elem.val(page);
              o_browse.textInputMonitor();
            }
            return false;
        });

        // change page number via text entry field
        $('#browse').on("change", '#page','#browse', function() {
            var page = parseInt($(this).val(), 10);
            if (!page) { page = 1; }
            opus.prefs.page['data'] = parseInt(page, 10);
            opus.prefs.page['gallery'] = parseInt(page, 10);
            o_browse.updatePage(page);
        });
        // TODO combine this and the above
        $('#collections').on("change",'#colls_page', function() {
            var page = parseInt($(this).val(), 10);
            if (!page) { page = 1; }
            opus.prefs.page['colls_data'] = parseInt(page, 10);
            opus.prefs.page['colls_gallery'] = parseInt(page, 10);
            o_browse.updatePage(page);
        });

        // the "back to top" link at bottom of gallery
        $('#browse').on('click', 'a[href=#top]', function() {
            $('html, body').animate({scrollTop:0}, 'slow');
            return false;
        });

        // close/open column chooser, aka "choose columns"
        $('#browse, #colorbox').on("click", '.get_column_chooser', function() {
                if ($(this).hasClass('close_overlay')) {
                    // close the colorbox because it never wants
                    // to be under the column_chooser
                    $.colorbox.close();
                }
                o_browse.getColumnChooser();
                return false;
        });

    }, // end browse behaviors

    cart_click_handler: function(opus_id, action) {
        // behaviors for the click to add/remove from cart
        // whether that's from checkbox being clicked
        // or thumbnail clicked while 'add range' is happening

        // make sure the checkbox for this observation in the other view (either data or gallery)
        // is also checked/unchecked - if that view is drawn
        try {
            $('#data__' + opus_id).find('.data_checkbox').toggleClass('fa-check-square-o').toggleClass('fa-square-o');
        } catch(e) { } // view not drawn yet so no worries

        // check if we are clicking as part of an 'add range' interaction
        if (!opus.addrange_clicked) {
            // no add range, just add this obs to collection
            o_collections.editCollection(opus_id,action);

        } else {
            // addrange clicked
            o_browse.addRangeHandler(opus_id);
        }
    },

    openDetailTab: function(opus_id) {
        opus.mainTabDisplay('detail');  // make sure the main site tab label is displayed
        opus.prefs.view = 'detail';
        opus.prefs.detail = opus_id;
        opus.triggerNavbarClick();
    },

    // what page no is currently scrolled more into view?
    pageInViewIndicator: function() {

        var view_info = o_browse.getViewInfo();
        var namespace = view_info['namespace']; // either '#collection' or '#browse'
        var prefix = view_info['prefix'];       // either 'colls_' or ''
        var add_to_url = view_info['add_to_url'];  // adds colls=true if in collections view

        if ($('#' + prefix + 'page', namespace).is(":focus")) {
            // the page element has focus, user is typing, so leave it alone!
            return;
        }

        var view_var = opus.prefs[prefix + 'browse'];  // either 'gallery' or 'data'

        var first_page = opus.prefs.page[prefix + view_var];

        if ($(window).scrollTop() === 0 || opus.browse_footer_clicks[prefix + view_var] === 0) {
            // there has been no scrolling, set it to first page
            $('#' + prefix + 'page', namespace).val(first_page);
            return;
        }

        var no_length = 0;
        var page = first_page;
        while (page <= (opus.browse_footer_clicks[prefix + view_var] + first_page)) { // opus.pages
            var elem = '#infinite_scroll_' + prefix + opus.prefs.browse + '__' + page;
            if ($(elem).length) {
                var elem_scroll = $(elem, namespace).offset().top;
                try {
                    if (Math.abs(elem_scroll  -  $('.top_navbar', namespace).offset().top ) < $(window).height()/2) {
                        // the first one that's greater than the window is the page
                        $('#' + prefix + 'page', namespace).val(page);
                        return;
                    }
                } catch(e) {
                    // offset of top is undefined
                    return
                }

            } else {
                no_length = no_length + 1; // if we hit 2 in a row stop checking
                if (no_length > 2) {
                    // there aren't any more, if we are still here then:
                    break;
                }
            }
            page = page + 1;
        }


    },

    // user is adding range with the 'add range' button in the top menu
    addRangeHandler: function(opus_id) {

        var element = "li";  // elements to loop thru
        if (opus.prefs.browse == 'data') {
                element = "td";
        }

        if (!opus.addrange_min) {
            // this is only the min side of the range
            var end_hint = "select another thumbnail to make a range.";
            var element_name = 'thumbnail';
            if (opus.prefs.browse == 'data') {
              element_name = 'row';
            }
            $('.addrange','#browse').text("select range end");
            $('.cart_control','#browse').popover("destroy");
            $('.cart_control','#browse').popover({
              content: "click another " + element_name + " to complete the range",
              trigger:"click",
              placement: "bottom",
            });

            index = $('#' + opus.prefs.browse + '__' + opus_id).index();
            opus.addrange_min = { "index":index, "opus_id":opus_id };
            return;

        } else {
            var opus_id_min = opus.addrange_min['opus_id'];

            // we have both sides of range
            $('.addrange','#browse').text("add range");
            $('.cart_control','#browse').popover('destroy');

            var index = $('#' + opus.prefs.browse + '__' + opus_id).index();
            if (index > opus.addrange_min['index']) {
                range = opus_id_min + "," + opus_id;// ???
                o_browse.checkRangeBoxes(opus_id_min, opus_id);
            } else {
                // user clicked later box first, reverse them for server..
                range = opus_id + "," + opus_id_min;
                o_browse.checkRangeBoxes(opus_id, opus_id_min);
            }  // i don't like this

            o_collections.editCollection(range,'addrange');

            opus.addrange_clicked = false;
            opus.addrange_min = false;

        }

    },

    toggleBrowseInCollectionStyle: function(opus_id) {
        var icon_a_element = ".tools-bottom a";
        $('#gallery__' + opus_id + ' ' + icon_a_element).parent().toggleClass("in"); // this class keeps parent visible when mouseout
        $('#gallery__' + opus_id + ' ' + icon_a_element).find('i').toggleClass('thumb_selected_icon');
        $('#gallery__' + opus_id + ' .thumb_overlay').toggleClass('thumb_selected');

        if ($('#gallery__' + opus_id + ' ' + icon_a_element).parent().hasClass("in")) {
        } else {
        }

    },

    // column chooser behaviors
    addColumnChooserBehaviors: function() {

        // a column is checked/unchecked
        $('.column_chooser').off("click", '.submenu li a');
        $('.column_chooser').off("click", '.chosen_column_close');

        $('.column_chooser').on("click", '.submenu li a', function() {

            var slug = $(this).data('slug');

            if (!slug) {
                return true;  // just a 2nd level menu click, move along
            }

            var label = $(this).data('label');
            var def = $(this).find('i.fa-info-circle').attr("title");
            var cols = opus.prefs['cols'];
            var checkmark = $(this).find('i').first();

            if (!checkmark.is(":visible")) {

                checkmark.show();

                if (jQuery.inArray(slug,cols) < 0) {
                    // this slug was previously unselected, add to cols
                    $('<li id = "cchoose__' + slug + '">' + label + ' <i class = "fa fa-info-circle" title = "' + def + '"></i><span class = "chosen_column_close">X</span></li>').hide().appendTo('.chosen_columns>ul').fadeIn();
                    cols.push(slug);
                }

            } else {

                checkmark.hide();

                if (jQuery.inArray(slug,cols) > -1) {
                    // slug had been checked, removed from the chosen
                    cols.splice(jQuery.inArray(slug,cols),1);
                    $('#cchoose__' + slug).fadeOut(function() {
                        $(this).remove();
                    });
                }
            }

            opus.prefs['cols'] = cols;

            // we are about to update the same page we just updated, it will replace
            // the one that is showing,
            // set last page to one before first page that is showing in the interface
            // now update the browse table
            if (opus.prefs.browse == 'data') {
                o_browse.updatePage();
            } else {
                o_hash.updateHash();
                // refetch the browse data since that data has changed
                var view_info = o_browse.getViewInfo();
                var prefix = view_info['prefix'];       // either 'colls_' or ''
                var pages = opus.pages_drawn[prefix + 'gallery'];
                for (var i in pages) {
                    o_browse.getBrowseData(pages[i]);
                }
            }
            return false;
        });


        // removes chosen column with X
        $('.column_chooser').on("click",'.chosen_column_close', function() {
            var slug = $(this).parent().attr("id").split('__')[1];
            var checkmark = $('.all_columns .' + slug).find('i').first();

            checkmark.hide();

            if (jQuery.inArray(slug,opus.prefs['cols']) > -1) {
                // slug had been checked, removed from the chosen
                opus.prefs['cols'].splice(jQuery.inArray(slug,opus.prefs['cols']),1);
                $('#cchoose__' + slug).fadeOut(function() {
                    $(this).remove();
                });
            }

            // we are about to update the same page we just updated, it will replace
            // the one that is showing,
            // set last page to one before first page that is showing in the interface
            // now update the browse table
            if (opus.prefs.browse == 'data') {
                o_browse.updatePage();
            } else {
                o_hash.updateHash();

                var view_info = o_browse.getViewInfo();
                var prefix = view_info['prefix'];       // either 'colls_' or ''
                var pages = opus.pages_drawn[prefix + 'gallery'];
                for (var i in pages) {
                    o_browse.getBrowseData(pages[i]);
                }
            }


        });

         // group header checkbox - lets user add/remove group of columns at a time
         // this is not working
        /*
         $('#column_chooser input[type="checkbox"].cat_input').click(function() {
             cols = opus.prefs['cols'];
             if ($(this).is(':checked')) {
                 // group header checkbox is checked, now check all params in group
                 $(this).parent().parent().find('.menu_list input[type="checkbox"]').each(function() {
                     $(this).attr('checked',true);
                     slug = $(this).data('slug');
                     label = $(this).data('label');
                     if (jQuery.inArray(slug,cols) < 0) {
                         // this slug was previously unselected, add to cols
                         cols.push(slug);
                         $('<li id = "cchoose__' + slug + '">' + label + '<span class = "chosen_column_close">X</span></li>').hide().appendTo('.chosen_columns>ul').fadeIn();
                     }
                 });

             } else {
                 // deselect all in this category
                 $(this).parent().parent().find('.menu_list input[type="checkbox"]').each(function() {
                     $(this).attr('checked',false);
                     var slug = $(this).data('slug');
                     if (jQuery.inArray(slug,cols) > -1) {
                         cols.splice(jQuery.inArray(slug,cols),1);
                         $('#cchoose__' + slug).fadeOut(function() {
                             $(this).remove();
                         });
                     }
                 });
             }
             opus.prefs['cols'] = cols;

            // we are about to update the same page we just updated, it will replace
            // the one that is showing,
            // set last page to one before first page that is showing in the interface
            // now update the browse table
            if (opus.prefs.browse == 'data') {
                o_browse.updatePage();
            } else {
                o_hash.updateHash();

                view_info = o_browse.getViewInfo();
                prefix = view_info['prefix'];       // either 'colls_' or ''
                pages = opus.pages_drawn[prefix + 'gallery'];
                for (var i in pages) {
                    o_browse.getBrowseData(pages[i]);
                }
            }

         }); // /group header checkbox
        */




    },  // /addColumnChooserBehaviors

    checkAllRenderedElements: function() {
      // returns first and last opus_id that is rendered on the page

      // find the id of the first and last element showing on this page
      var first = "";
      var last = "";
      if (opus.prefs.browse == 'gallery') {
        el = $('.gallery li');
        first = el.first().attr('id');
        last = el.last().attr('id');
      } else {
        first = $('.data_table tbody tr:first').attr('id');
        last = $('.data_table tbody tr:last').attr('id');
      }

      var opus_id1 = first.split('__')[1];
      var opus_id2 = last.split('__')[1];

      o_browse.checkRangeBoxes(opus_id1, opus_id2);
    },

    // handles checking of a range of boxes in each view (table/gallery)
    checkRangeBoxes: function(opus_id1, opus_id2) {

        // make all list/td elements bt r1 and r2 be added to cart
        var elements = ['#gallery__','#data__'];
        for (var key in elements) {
            var element = elements[key];
            var current_id = opus_id1;
            var next_element = $(element + current_id, '#browse');
            while (current_id != opus_id2) {

                // thumbnail in the list
                if (next_element.hasClass("infinite_scroll_page")) {
                    // this is the infinite scroll indicator, continue to next
                    next_element = $(element + current_id, '#browse').next().next();
                }

                // check the boxes:
                if (element == '#gallery__') {
                    /* gallery view */
                    if (!next_element.find('.tools').hasClass("in")) {  // if not already checked
                        try {
                            opus_id = next_element.attr("id").split('__')[1];
                            o_browse.toggleBrowseInCollectionStyle(opus_id);
                        } catch(e) {
                        }
                    }
                } else {
                    /* this is table view */
                    if (!next_element.find('.data_checkbox').hasClass('fa-check-square-o')) {  // if not already checked
                        // box is not checked so checkity check it
                        $(next_element).find(".data_checkbox").addClass('fa-check-square-o').removeClass('fa-square-o');
                    }

                }

                // now move along
                try {
                    current_id = next_element.attr("id").split('__')[1];
                } catch(e) {
                    break;  // no next_id means the view isn't drawn, so we don't need to worry about it
                }

                next_element = $(element + current_id, '#browse').next();

            } // /while
        }
    },

    // this is like the table headers
    startDataTable: function(namespace) {
        var url = '/opus/table_headers.html?' + o_hash.getHash() + '&reqno=' + opus.lastRequestNo;
        if (namespace == '#collections') {
            url += '&colls=true';
        }
        $.ajax({ url: url,
            success: function(html) {
                $('.data', namespace).append(html);
                $(".data .data_table", namespace).stickyTableHeaders({ fixedOffset: 94 });
                opus.table_headers_drawn = true;
                o_browse.getBrowseTab();
            }
        });

    },

    // footer bar, indicator bar, browse footer bar
    infiniteScrollPageIndicatorRow: function(page) {
        // this is the bar that appears below each infinite scroll page to indicate page no

        (opus.prefs.view == 'browse') ? browse_prefix = '' : browse_prefix = 'colls_';

        var id = 'infinite_scroll_' + browse_prefix + opus.prefs.browse + '__' + page;

        if ($(id).length) {
            return;  // this is a hack because it sometimes draws it multiple times
        }

        var data;
        if (opus.prefs.browse == 'gallery') {
            data = '<li class = "infinite_scroll_page navbar-inverse">\
                       <span class = "back_to_top"><a href = "#top">back to top</a></span>\
                       <span class = "infinite_scroll_page_container page_' + page + '" id = "' + id + '">Page ' + page + '</span>\
                       <span class = "infinite_scroll_spinner">' + opus.spinner + '</span>\
                   </li>';
                   // opus.page_bar_offsets['#'+id] = false; // we look up the page loc later - to be continue            return gallery;
        } else {
            data = '<tr class = "infinite_scroll_page">\
                      <td colspan = "' + (opus.prefs['cols'].length +1) + '">\
                          <div class="navbar-inverse"> \
                              <span class = "back_to_top"><a href = "#top">back to top</a></span> \
                              <span class = "infinite_scroll_page_container" id = "' + id + '">Page ' + page + '</span><span class = "infinite_scroll_spinner">' + opus.spinner + '</span> \
                          </div>\
                  </td>\
                  </tr>';
        }
        return data;
    },


    // there are interactions that are applied to different code snippets,
    // this returns the namespace, view_var, prefix, and add_to_url
    // that distinguishes collections vs result tab views
    // NOTE: get rid of all this with a framework!
    // usage:
    // utility function to figure out what view we are in
    /*
        // usage
        view_info = o_browse.getViewInfo();
        namespace = view_info['namespace'];
        view_var = view_info['view_var'];
        prefix = view_info['prefix'];
        add_to_url = view_info['add_to_url'];
    */
    getViewInfo: function() {
        // this function returns some data you need depending on whether
        // you are in #collection or #browse views
        if (opus.prefs.view == 'collection') {
            namespace = '#collection';
            prefix = 'colls_';
            add_to_url = "&colls=true";
        } else {
            namespace = '#browse';
            prefix = '';
            add_to_url = "";
        }
        return {'namespace':namespace, 'prefix':prefix, 'add_to_url':add_to_url};

    },

    getCurrentPage: function() {
        // sometimes other functions need to know current page for whatever view we
        // are currently looking at..
        var view_info = o_browse.getViewInfo();
        var namespace = view_info['namespace']; // either '#collection' or '#browse'
        var prefix = view_info['prefix'];       // either 'colls_' or ''
        var view_var = opus.prefs[prefix + 'browse'];  // either 'gallery' or 'data'
        var page = 1;

        if (view_var == 'data') {
            page = opus.prefs.page[prefix + 'data'];
        } else {
            page = opus.prefs.page[prefix + 'gallery'];
        }
        if (!page) { page = 1; }

        return page;
    },

    getBrowseTab: function() {

        clearInterval(opus.scroll_watch_interval);  // always shut off just before, just in case

        var view_info = o_browse.getViewInfo();
        var namespace = view_info['namespace']; // either '#collection' or '#browse'
        var prefix = view_info['prefix'];       // either 'colls_' or ''
        var add_to_url = view_info['add_to_url'];  // adds colls=true if in collections view
        var view_var = opus.prefs[prefix + 'browse'];  // either 'gallery' or 'data'

        if (namespace == '#collection' & opus.colls_pages == 0) {
            // clicked on collections tab with nothing in collections,
            // give some helpful hint
            var html = ' \
                <div style = "margin:20px"><h2>You Have No Selections</h2>   \
                <p>To select observations, click on the Browse Results tab \
                at the top of the page,<br> mouse over the thumbnail gallery images to reveal the tools, \
                then click the <br>checkbox below a thumbnail.  </p>   \
                </div>'

            $(html).appendTo($('.gallery .ace-thumbnails', namespace)).fadeIn();
            return;
        }

        // only draw the navbar if we are in gallery mode... doesn't make sense in collection mode
        if (namespace == "#browse") {
          // get the browse nav header?
          $('.browse_nav', namespace).load( "/opus/browse_headers.html", function() {
            // change the link text
            if (opus.prefs.browse == 'gallery') {
                $('.browse_view', namespace).text('view table');
            } else {
                $('.browse_view', namespace).text('view gallery');
            }
            // total pages indicator
            $('#' + prefix + 'pages', namespace).html(opus[prefix + 'pages']);
            window.scroll(0,0);  // sometimes you have scrolled down the search tab
          });
        }

        var base_url = "/opus/api/images.html?";
        if (opus.prefs[prefix + 'browse'] == 'data') {
            base_url = '/opus/api/data.html?';

            // get table headers for table view
            if (!opus.table_headers_drawn) {
                window.scroll(0,0);  // sometimes you have scrolled down in the search tab
                o_browse.startDataTable(namespace);
                return; // startDataTable() starts data table and then calls getBrowseTab again
            }
        }
        var url = o_hash.getHash() + '&reqno=' + opus.lastRequestNo + add_to_url;

        var footer_clicks = opus.browse_footer_clicks[prefix + view_var]; // default: {'gallery':0, 'data':0, 'colls_gallery':0, 'colls_data':0 };

        // figure out the page
        var start_page = opus.prefs.page[prefix + view_var]; // default: {'gallery':1, 'data':1, 'colls_gallery':1, 'colls_data':1 };

        var page = parseInt(start_page, 10) + parseInt(footer_clicks, 10);

        // some outlier things that can go wrong with page (when user entered page #)
        if (!page) {
            page = 1;
        }
        else if (page < 1) {
            page = 1;
            $('#' + prefix + 'page_no', namespace).val(page); // reset the display
        }

        if (opus[prefix + 'pages'] && page > opus[prefix + 'pages']) {
            // page is higher than the total number of pages, reset it to the last page
            page = opus[prefix + 'pages'];
        }

        // draw indicator bar if needed
        if (page > 1) {
            indicator_row = o_browse.infiniteScrollPageIndicatorRow(page);

            if (!$('.page_' + page).length) {
                if (view_var == 'gallery') {
                    $(indicator_row).appendTo('.gallery .ace-thumbnails', namespace).show();
                } else {
                    // this is the data table view!
                    // do something:
                    $(".data_table tr:last", namespace).after(indicator_row);
                    $(".data_table tr:last", namespace).show();  // i dunno why couldn't chain these 2
                }
            }
        }

        url += '&page=' + page;

        // wait! is this page already drawn?
        if (opus.last_page_drawn[prefix + view_var] == page) {
            // this page is already drawn, just make sure it's showing and
            // start the scroll watch interval
            if (view_var == 'data') {
                $('.data tbody', namespace).fadeIn("fast");
            } else {
                $('.gallery .ace-thumbnails', namespace).fadeIn("fast");
            }
            opus.scroll_watch_interval = setInterval(o_browse.browseScrollWatch, 1000);
            return; // chill chill chill
        }

        if (view_var == 'gallery') {
            opus.pages_drawn[prefix + 'gallery'].push(page);
        }

        clearInterval(opus.scroll_watch_interval); // hold on cowgirl only 1 page at a time

        // NOTE if you change alt_size=full here you must also change it in gallery.html template
        $.ajax({ url: base_url + url,
            success: function(html){
               // bring in the new page
               function appendBrowsePage(page, prefix, view_var) { // for chaining effects

                    // hide the views that aren't supposed to be showing
                    /*
                    for (var v in opus.all_browse_views) {
                        var bv = opus.all_browse_views[v];
                        if ($('.' + bv, namespace).is(":visible") && bv != opus.prefs[prefix + 'browse']) {
                            $('.' + bv, namespace).hide();
                        }
                    }
                    */
                    // append the new html
                    if (view_var == 'data') {
                        $(html).appendTo($('.data tbody', namespace)).fadeIn();
                    } else {
                        opus.gallery_begun = true;
                        $(html).appendTo($('.gallery ul.ace-thumbnails', namespace)).fadeIn();
                    }

                    // fade out the spinner
                    $('.infinite_scroll_spinner', namespace).fadeOut("fast");

               }

                o_browse.getBrowseData(page);

                // doit!
                appendBrowsePage(page, prefix, view_var);
                opus.last_page_drawn[prefix + view_var] = page;

                o_browse.pageInViewIndicator();

                o_browse.initColorbox();

                o_hash.updateHash();
            },
            complete: function() {
                // turn the scroll watch timer back on
                clearInterval(opus.scroll_watch_interval);  // always shut off just before, just in case
                opus.scroll_watch_interval = setInterval(o_browse.browseScrollWatch, 1000);

            }

        });
    },

    getBrowseData: function(page) {

        var base_url = '/opus/api/data.json?';
        var columns;

        // we have to do a little hacking of the hash, we want page as we want it and opus_id too
        var new_hash = [];
        for (var i in o_hash.getHash().split('&')) {

            // is param a string or array???? this is odd
            var param = values = [];
            if (o_hash.getHash()) {
                param = o_hash.getHash().split('&')[i].split('=')[0];
                values = o_hash.getHash().split('&')[i].split('=')[1].split(',');
            } else {
                param = values = [];
            }


            // make sure opus_id is in columns
            columns = opus.prefs.cols;
            if (param == 'cols') {
                values = values.map( function(item) {
                  return item == 'ringobsid' ? 'opusid' : item;
                })
                if (jQuery.inArray('opusid', values) < 0) {
                    values.push('opusid');
                }
                columns = values.join(',');  // we need this after the ajax call
            }
            // make sure page is the page we were passed
            if (param == 'page') {
                values = [page];
            }
            // join them all together again
            new_hash.push(param + '=' + values.join(','));
        }

        // THIS MAKES NO SENSE XXX
        // Above we set columns to a comma-separated string, but here
        // it's magically a list again. WTF?
        columns = columns.map( function(item) {
          return item == 'ringobsid' ? 'opusid' : item;
        })
        var new_hash = new_hash.join('&');
        $.getJSON(base_url + new_hash, function(json) {
            // assign to data object
            var updated_ids = [];

            console.log(columns)

            for (var i in json.page) {
                var opus_id = json.page[i][columns.indexOf('opusid')];
                updated_ids.push(opus_id);
                opus.gallery_data[opus_id] = json.page[i];
            }

            // this endpoint also returns column labels:
            opus.col_labels = [];
            for (var i in json['columns']) {
              opus.col_labels.push(json['columns'][i]);
            }

            // update any currently rendered metadata box
            if (opus.current_metadatabox &&
                updated_ids.indexOf(opus.current_metadatabox) > -1) {
                o_browse.updateEmbeddedMetadataBox(opus.current_metadatabox);
            }

        });

    },


    // colorbox  is the gallery large image viewer thing
    initColorbox: function() {

        var left_margin = o_browse.colorbox_left_margin();

        // setup colorbox
        var $overflow = '';
        var colorbox_params = {
            rel: 'colorbox',
            className:"gallery_overlay_bg",
            top:'17px',
            left:left_margin,
            reposition:false,
            /* retinaImage:true, // maybe? */
            scrolling:true,
            previous: '<i class="ace-icon fa fa-arrow-left"></i>',
            next: '<i class="ace-icon fa fa-arrow-right"></i>',
            close:'&times;',
            current:'{current} of {total}',
            height:'90%',
            initialHeight:'90%',
            loop:false,

            onOpen:function(){
                // prevent scrolling for duration that colorbox is visible
                $overflow = document.body.style.overflow;
                document.body.style.overflow = 'hidden';
            },
            onLoad:function() {

                opus_id = $.colorbox.element().parent().attr("id").split('__')[1];
                // get pixel loc of right border of colorbox

                // draw the viewer if not already..
                if (!$('#colorbox .gallery_data_viewer').is(':visible')) { // :visible being used here to see if element exists
                    // .gallery_data_viewer does not exist
                    var right_border_colorbox = $('#colorbox').width() + $('#colorbox').position().left;
                    $('#colorbox .gallery_data_viewer').css({
                        left: right_border_colorbox + 5 + 'px'
                    });
                    $('#colorbox').append('<div class = "gallery_data_viewer"><div>');
                }

                // append the data to the data view container
                $('.gallery_data_viewer').html("<h2>" + opus_id + "</h2>");
                $('.embedded_data_viewer').html("<h2>" + opus_id + "</h2>");

                // update the view data
                o_browse.updateColorboxDataViewer(opus_id);


            },
            onClosed:function(){
                $('#cboxContent .gallery_data_viewer').hide();
                document.body.style.overflow = $overflow;  // return overflow to default.

                // add indicator around the thumb corresponding to the closed image
                opus_id = $.colorbox.element().parent().attr("id").split('__')[1];
                $(' .thumb_overlay').removeClass("gallery_image_focus").removeClass('browse_image_selected');  // remove any old
                $('#gallery__' + opus_id + ' .thumb_overlay').addClass("gallery_image_focus").addClass('browse_image_selected');


                if ($('.embedded_data_viewer_wrapper').is(":visible")) {
                    // embedded data viewer box is open, update it with current
                    o_browse.updateEmbeddedMetadataBox(opus_id);
                }


            },
            onComplete:function(){
                o_browse.adjust_gallery_data_viewer();
            }
        };

        $('.ace-thumbnails [data-rel="colorbox"]').colorbox(colorbox_params);

    },

    colorbox_left_margin: function() {
        var window_width = $(window).width();
        var left_margin = '5px';
        if (window_width > 1050) {
            left_margin = '15%';
        }
        return left_margin;
    },

    reset_colorbox: function() {
        // this is mainly used after a window resize
        // basically the library will do it for you but have to trigger that click
        // otherwise it won't do it on page resize but will do it on next/prev
        var opus_id = $.colorbox.element().parent().attr("id").split('__')[1];
        $('li#gallery__' + opus_id + ' a.activeThumbnail').trigger("click");
        o_browse.adjust_gallery_data_viewer();
    },

    adjust_gallery_data_viewer: function() {
        var right_border_colorbox = $('#colorbox').width() + $('#colorbox').position().left;
        // move metadatabox to be near colorbox
        $('#colorbox .gallery_data_viewer').animate({
            left: right_border_colorbox - 10 +  'px'
        }, 'fast');

    },

    metadataboxHtml: function(opus_id) {

        // list columns + values
        var html = '<dl>';
        for (var i in opus.prefs['cols']) {
            var column = opus.col_labels[i];  // use the label not the column title
            var value = opus.gallery_data[opus_id][i];
            html += '<dt>' + column + ':</dt><dd>' + value + '</dd>';

        }
        html += '</dl>';

        // add a link to detail page
        html += '<p><a href = "/opus/detail/' + opus_id + '.html" class = "gallery_data_link" data-opusid="' + opus_id + '">View Detail</a></p>';

        // add link to choose columns
        html += '<p><a href="" class="get_column_chooser close_overlay">choose columns</a></p>';
        $('.gallery_data_viewer').html(html);

        return html
    },

    updateEmbeddedMetadataBox: function(opus_id) {

        opus.current_metadatabox = opus_id;

        // handle which thumbnail has focus indicator outline
        $(' .thumb_overlay').removeClass("gallery_image_focus").removeClass('browse_image_selected');  // remove any old
        $('#gallery__' + opus_id + ' .thumb_overlay').addClass("gallery_image_focus browse_image_selected");

        // XXX This code should not be replacing _med with _full because there's
        // no guarantee that's how the filenames will be laid out. It needs
        // to do to URL queries, one for med and one for full.
        var url = '/opus/api/image/med/' + opus_id + '.json';
        $.getJSON(url, function(json) {

            var img = json['data'][0]['url'];
            var full = img.replace("_med", "_full");

            var html = '<i class = "fa fa-times"></i> \
                    <div class = "embedded_data_viewer_image edv_' + opus_id + '"> \
                    <a href = "' + full + '" data-opus_id="' + opus_id + '"> \
                    <img src = "' + img + '"></a> \
                    </div>';
            html += o_browse.metadataboxHtml(opus_id);

            if (!$('.embedded_data_viewer_wrapper').is(":visible")) {
                // embedded data viewer isn't visible, show it!
                o_browse.embedded_data_viewer_toggle();
            }

            // and update the data viewer
            var scroll_top = $('body').scrollTop();
            if (!scroll_top) { scroll_top = $('html').scrollTop(); }  // oh, browsers
            $('.embedded_data_viewer')
                    .hide()
                    .css({ 'top': scroll_top + "px"})
                    .html(html)
                    .fadeIn("fast");


            // add the 'get detail' behavior
            $('.embedded_data_viewer').on("click", '.gallery_data_link', function(e) {
                if (e.shiftKey || e.ctrlKey || e.metaKey) {
                    // handles command click to open in new tab
                    var link = "/opus/#/" + o_hash.getHash();
                    link = link.replace("view=browse", "view=detail");
                    window.open(link, '_blank');
                } else {
                    var opus_id = $(this).data('opusid');
                    o_browse.openDetailTab(opus_id);
                }
                return false;
            });


        }); // /getJSON

    },

    updateColorboxDataViewer: function(opus_id) {

        var html = o_browse.metadataboxHtml(opus_id);

        // add data viewer behaviors
        $('.gallery_data_viewer').on("click", '.gallery_data_link', function() {
            var opus_id = $(this).data('opusid');
            o_browse.openDetailTab(opus_id);
            $.colorbox.close();
            return false;
        });

        // some alignment adjustments
        if ($(window).width() > 1500) {
            $('.gallery_data_viewer').css("right", parseInt($(window).width()/2 - $('#colorbox').width(), 10) + "px");
        }

    },


    embedded_data_viewer_toggle: function(opus_id) {
        $('.gallery').toggleClass('col-lg-12').toggleClass('col-sm-7').toggleClass('col-md-9').toggleClass('col-lg-9');
        $('.embedded_data_viewer_wrapper').toggle();

    },

    // we watch the paging input fields to wait for pauses before we trigger page change. UX!
    // this funciton starts that monitor based on what view is currently up
    // it also clears any old one.
    // so it records the current value of #page input and then checks again ms later
    // if they match, it triggers refresh, if not then the user is still typing so moves on
    textInputMonitor: function() {
        // which field are we working on? defines which global monitor list we use
        var ms = 1500;

        var view_info = o_browse.getViewInfo();
        var namespace = view_info['namespace']; // either '#collection' or '#browse'
        var prefix = view_info['prefix'];       // either 'colls_' or ''
        var view_var = opus.prefs[prefix + 'browse'];  // either 'gallery' or 'data'

        var field_monitor = opus[prefix + 'page_monitor_' + view_var];

        // check the current value of the page indicator input now, then again in ms (2 seconds ish)
        var value = parseInt($('#page', namespace).val(), 10);

        // clear any old monitor and start a new one
        clearTimeout(opus.input_timer);
		    opus.input_timer = setTimeout(
            function() {

                if (field_monitor[field_monitor.length-1] == value){
					// the user has not moved in ms
                    $('input#page').css('color', 'black'); // change indicator color back to black
                    // change both views to the new page
                    opus.prefs.page[prefix + 'data'] = parseInt(value, 10);
                    opus.prefs.page[prefix + 'gallery'] = parseInt(value, 10);
					o_browse.updatePage();
					// opus.force_load = true;
					// setTimeout("o_hash.updateHash()",0);
					// tidy up, keep the array small..
					if (field_monitor.length > 3) field_monitor.shift(); // just keeping it trimmed
				} else {
					// array is changing fastly, user is still typing
					// maintain our array with our new value
                    if (value) {
                        field_monitor[field_monitor.length]  = value;
                        o_browse.textInputMonitor();
                    }
					// o_browse.textInputMonitor();
				}
            },ms);


            opus[prefix + 'page_monitor_' + view_var] = field_monitor;  // update the global monitor
        },


        resetQuery: function() {
            /*
            when the user changes the query and all this stuff is already drawn
            need to reset all of it (todo: replace with framework!)
            */
            $('.data').empty();  // yes all namespaces
            $('.gallery .ace-thumbnails').empty();
            opus.gallery_data = [];
            opus.pages_drawn = {"colls_gallery":[], "gallery":[]};
            opus.browse_footer_clicks = {"gallery":0, "data":0, "colls_gallery":0, "colls_data":0 };
            opus.last_page_drawn = {"gallery":0, "data":0, "colls_gallery":0, "colls_data":0 };
            opus.collection_change = true;  // forces redraw of collections tab because reset_last_page_drawn
            browse_view_scrolls = reset_browse_view_scrolls;
            opus.table_headers_drawn = false;
            opus.gallery_begun = false;
            opus.column_chooser_drawn = false;
            o_hash.updateHash();

        },

        updatePage: function() {

            /*
            reloads the current results view from server and
            sets other views back to undrawn
            gets page/view info from from getViewInfo()
            and opus.prefs[prefix + 'browse']
            */
            o_browse.resetQuery();
            o_browse.getBrowseTab();
        },

        // http://stackoverflow.com/questions/487073/jquery-check-if-element-is-visible-after-scroling thanks!
        isAlmostScrolledIntoView: function(elem) {

            var docViewTop = $(window).scrollTop() + $(window).height()/4;
            var docViewBottom = docViewTop + $(window).height();

            var elemTop = $(elem).offset().top;
            var elemBottom = elemTop + $(elem).height();
            var answer = (elemBottom >= docViewTop) && (elemTop <= docViewBottom) && (elemBottom <= docViewBottom) &&  (elemTop >= docViewTop);

            return (answer);
        },


        // infinite scroll
        // watch for browse tab scrolling, if footer in view get next page
        // this is on a setInterval
        browseScrollWatch: function() {

            var view_info = o_browse.getViewInfo();
            var prefix = view_info['prefix']; // none or colls_
            var view_var = opus.prefs[prefix + 'browse'];  // data or gallery

            // keep track of each views scroll position because UX
            opus.browse_view_scrolls[prefix + view_var] = $(window).scrollTop();

            o_browse.pageInViewIndicator();

            // this is for the infinite scroll footer bar
            if (o_browse.isAlmostScrolledIntoView('.end_of_page')) {

                if (opus.browse_footer_clicks[prefix + view_var] > (opus[prefix + 'pages'] -2)) {
                    return; // this can't be! so just don't
                }

                // scroll is in view, up the "footer clicks" for this view
                opus.browse_footer_clicks[prefix + view_var] = opus.browse_footer_clicks[prefix + view_var] + 1;


                o_browse.getBrowseTab();

            }
        },


        // column chooser
        getColumnChooser: function() {
            /**
            offset = $('.data_table', '#browse').offset().top + $('.data_table .column_label', '#browse').height() + 10;
            left = $('.get_column_chooser').parent().offset().left - $('.column_chooser').width()  ;
            $('.column_chooser').css('top', Math.floor(offset) + 'px');
            $('.column_chooser').css('left', Math.floor(left) + 'px');
            **/
            if (opus.column_chooser_drawn) {
                // it's already drawn, just move it into view
                if (!$('.column_chooser').is(":visible")) {
                    // wtf drawn but not visible?
                    $('.column_chooser').dialog({
                            open: function( event, ui ) {
                                $('.ui-dialog-titlebar-close').removeAttr("title");
                            },
                            height: 600,
                            width: 900,
                            modal: true,
                            draggable:true,
                            dialogClass: 'no-close success-dialog fixed-dialog'
                        });
                }
                return;
            }

            // column_chooser has not been drawn, fetch it from the server and apply its behaviors:
            $('.column_chooser').html(opus.spinner);
            $('.column_chooser').dialog({
                    create: function( event, ui ) {
                        $('.ui-dialog-titlebar-close').removeAttr("title");
                    },
                    height: 600,
                    width: 900,
                    modal: true,
                    draggable:true,
                    dialogClass: 'no-close success-dialog fixed-dialog'
            });


            var url = '/opus/forms/column_chooser.html?' + o_hash.getHash() + '&col_chooser=1';
            $('.column_chooser').load( url, function(response, status, xhr)  {

               opus.column_chooser_drawn=true;  // bc this gets saved not redrawn

               // we keep these all open in the column chooser, they are all closed by default
               // disply check next to any default columns
                for (var key in opus.prefs['cols']) {
                    $('.column_chooser .' + opus.prefs['cols'][key]).find('i').first().show();
                }

                o_browse.addColumnChooserBehaviors();

               // dragging to reorder the chosen
               $( ".chosen_columns>ul").sortable({
                   items: "li:not(.unsortable)",
                   cursor: 'move',
                   stop: function(event, ui) { o_browse.columnsDragged(this); }
               });
            });
        },


        // columns can be reordered wrt each other in 'column chooser' by dragging them
        columnsDragged: function(element) {
            var cols = $(element).sortable('toArray');
            cols.unshift('cchoose__opusid');  // manually add opusid to this list
            $.each(cols, function(key, value)  {
                cols[key] = value.split('__')[1];
            });
            opus.prefs['cols'] = cols;
            // if we are in gallery - just change the data-struct that gallery draws from
            // if we are in table -
            // $('.gallery', '#browse').html(opus.spinner);

            // we are about to update the same page we just updated, it will replace
            // the one that is showing,

            // we are about to update the same page we just updated, it will replace
            // the one that is showing,
            // set last page to one before first page that is showing in the interface
            // now update the browse table
            if (opus.prefs.browse == 'data') {
                o_browse.updatePage();
            } else {
                // update the hash
                o_hash.updateHash();

                // update the underlying column data that goes with
                // thumbnails currently rendered
                var view_info = o_browse.getViewInfo();
                var prefix = view_info['prefix'];       // either 'colls_' or ''
                var pages = opus.pages_drawn[prefix + 'gallery'];
                for (var i in pages) {
                    o_browse.getBrowseData(pages[i]);
                }
            }

        },

};
