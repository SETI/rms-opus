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

         // browse nav menu - the gallery/table toggle
         $('#browse').on("click", '.browse_view', function() {

            if (opus.scroll_watch_interval) {
                clearInterval(opus.scroll_watch_interval); // hold on cowgirl only 1 page at a time
            }

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
                $('.browse_view', namespace).text('view table');
            } else {
                $('.browse_view', namespace).text('view gallery');
            }

            // do we need to fetch a new browse tab?
            if ((opus.prefs.browse == 'gallery' && !opus.gallery_begun) ||
                (opus.prefs.browse == 'data' && !opus.table_headers_drawn)) {
                o_browse.getBrowseTab();
            } else {
                // not loading browse, turn scroll watch back on
                opus.scroll_watch_interval = setInterval(o_browse.browseScrollWatch, 1000);
            }

            // $('#' + prefix + 'page', namespace).val(opus.prefs.page[prefix + showing]);

            // reset scroll position (later we'll be smarter)
            // window.scroll(0,0);
            window.scroll(0,opus.browse_view_scrolls[showing]); // restore previous scroll position

            return false;
        });


        // browse nav menu - add range - begins add range interaction
        $('#browse').on("click", '.addrange', function() {

            if ($('.addrange', '#browse').text() == "add range") {
                opus.addrange_clicked = true;
                $('.addrange','#browse').text("select range start");
                return false;
            }
        });

        // data_table - click a table row adds to cart
        $('#browse').on("click", ".data_table tr", function() {
            ring_obs_id = $(this).attr("id").substring(6);
            $(this).find('.data_checkbox').toggleClass('fa-check-square-o').toggleClass('fa-square-o');
            action = 'remove';
            if ($(this).find('.data_checkbox').hasClass('fa-check-square-o')) {
                // this is checked, we are unchecking it now
                action = 'add';
            }

            // make sure the checkbox for this observation in the other view (either data or gallery)
            // is also checked/unchecked - if that view is drawn
            try {
                o_browse.toggleBrowseInCollectionStyle(ring_obs_id);
            } catch(e) { } // view not drawn yet so no worries

            // check if we are clicking as part of an 'add range' interaction
            if (!opus.addrange_clicked) {

                // no add range, just add this obs to collection
                o_collections.editCollection(ring_obs_id,action);

            } else {

                o_browse.addRangeHandler(ring_obs_id);
            }



        });

        // thumbnail overlay tools
        $('.gallery').on("click", ".tools-bottom a", function() {

            ring_obs_id = $(this).parent().parent().attr("id").substring(9);
            $(this).parent().show();

            // click to view detail page
            if ($(this).find('i').hasClass('fa-list-alt')) {
                opus.prefs.view = 'detail';
                opus.prefs.detail = ring_obs_id;
                opus.triggerNavbarClick();
            }

            // click to view colorbox
            if ($(this).find('i').hasClass('fa-search-plus')) {
                // trigger colorbox, same as clicking anywhere on the thumbnail
                $('#gallery__' + ring_obs_id + "> a").trigger("click");
            }

            // click to add/remove from  cart
            if ($(this).find('i').hasClass('fa-check')) {

                // user has checked a checkbox or clicked the checkmark on a thumbnail

                // toggle thumbnail indicator state
                o_browse.toggleBrowseInCollectionStyle(ring_obs_id);

                // is this checked? or unchecked..
                action = 'remove';
                if ($(this).parent().hasClass("in")) {
                    action = 'add';  // this ring_obs_id is being added to cart
                }


                // make sure the checkbox for this observation in the other view (either data or gallery)
                // is also checked/unchecked - if that view is drawn
                try {
                    $('#data__' + ring_obs_id).find('.data_checkbox').toggleClass('fa-check-square-o').toggleClass('fa-square-o');
                } catch(e) { } // view not drawn yet so no worries

                // check if we are clicking as part of an 'add range' interaction
                if (!opus.addrange_clicked) {

                    // no add range, just add this obs to collection
                    o_collections.editCollection(ring_obs_id,action);

                } else {
                    // addrange clicked
                    o_browse.addRangeHandler(ring_obs_id);
                }
            }

            return false;

        }); // end click a browse tools icon


        // click table column header to reorder by that column
        $('#browse').on("click", '.data_table th a',  function() {
            var order_by =  $(this).data('slug');
            var order_indicator = $(this).find('.column_ordering');

            if (order_indicator.hasClass('fa-sort-asc')) {
                // currently ascending, change to descending order
                order_indicator.removeClass('fa-sort-asc');
                order_indicator.addClass('fa-sort-desc');
                order_by = '-' + order_by

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



        // results paging
        $("#browse").on("click", "a.next, a.prev", function() {
            // all this does is update the number that shows in the box and then calls textInputMonitor
            page_no_elem = $(this).parent().parent().find('.page_no');
            this_page = parseInt(page_no_elem.val(), 10);
            if ( $(this).hasClass("next")) {
                page = this_page + 1;
            } else if ($(this).hasClass("prev")) {
                 page = this_page - 1;
            }
            page_no_elem.val(page);
            o_browse.textInputMonitor();
            return false;
        });

        // change page manually
        /*
        $('#page_no','#browse').on("change",function() {
            page = parseInt($(this).val(), 10);
            o_browse.updatePage(page);
        });
        $('#colls_page_no','#collections').live("change",function() {
            page = parseInt($(this).val(), 10);
            o_browse.updatePage(page);
        });


        */

        // back to top link at bottom of gallery
        $('#browse').on('click', 'a[href=#top]', function() {
            $('html, body').animate({scrollTop:0}, 'slow');
            return false;
        });


        // this controls the page indicator bars you get with infinie scroll
        $(window).scroll(function() {
             o_browse.fixBrowseControls();
          });

        // close/open column chooser
        $('#browse').on("click", '.get_column_chooser', function() {
                o_browse.getColumnChooser();
                return false;
        });

    }, // end browse behaviors

    pageInViewIndicator: function() {
        // what page no is currently scrolled into view?
        view_info = o_browse.getViewInfo();
        namespace = view_info['namespace']; // either '#collection' or '#browse'
        prefix = view_info['prefix'];       // either 'colls_' or ''
        add_to_url = view_info['add_to_url'];  // adds colls=true if in collections view

        view_var = opus.prefs[prefix + 'browse'];  // either 'gallery' or 'data'

        first_page = opus.prefs.page[prefix + view_var];

        page = first_page;
        /*
        if (page == 1) {
            page = 2; // there is never a page 1 indicator bar, start with 2
        }
        */


        if ($(window).scrollTop() === 0 || opus.browse_footer_clicks[prefix + view_var] === 0) {
            // there has been no scrolling, set it to first page
            $('#' + prefix + 'page', namespace).val(first_page);
            return;
        }

        no_length = 0;
        while (page <= (opus.browse_footer_clicks[prefix + view_var] + first_page)) { // opus.pages
            elem = '#infinite_scroll_' + prefix + opus.prefs.browse + '__' + page;
            if ($(elem).length) {
                elem_scroll = $(elem, namespace).offset().top;
                if (elem_scroll + $(window).height() >  $('.top_navbar', namespace).offset().top ) {
                    // the first one that's greater than the window is the page
                    $('#' + prefix + 'page', namespace).val(page);
                    return;
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

    addRangeHandler: function(ring_obs_id) {

        element = "li";  // elements to loop thru
        if (opus.prefs.browse == 'data') {
                element = "td";
        }

        if (!opus.addrange_min) {
            // this is the min side of the range
            $('.addrange','#browse').text("select range end");
            index = $('#' + opus.prefs.browse + '__' + ring_obs_id).index();
            opus.addrange_min = { "index":index, "ring_obs_id":ring_obs_id };

        } else {

            // we have both sides of range
            $('.addrange','#browse').text("add range");

            index = $('#' + opus.prefs.browse + '__' + ring_obs_id).index();

            if (index > opus.addrange_min['index']) {
                range = opus.addrange_min['ring_obs_id'] + "," + ring_obs_id;
                o_browse.checkRangeBoxes(opus.addrange_min['ring_obs_id'], ring_obs_id);
            } else {
                // user clicked later box first, reverse them for server..
                range = ring_obs_id + "," + opus.addrange_min['ring_obs_id'];
                o_browse.checkRangeBoxes(ring_obs_id, opus.addrange_min['ring_obs_id']);
            }  // i don't like this

            o_collections.editCollection(range,'addrange');

            opus.addrange_clicked = false;
            opus.addrange_min = false;

        }

    },

    toggleBrowseInCollectionStyle: function(ring_obs_id) {
        icon_a_element = ".tools-bottom a"
        $('#gallery__' + ring_obs_id + ' ' + icon_a_element).parent().toggleClass("in"); // this class keeps parent visible when mouseout
        $('#gallery__' + ring_obs_id + ' ' + icon_a_element).find('i').toggleClass('thumb_selected_icon');
        $('#gallery__' + ring_obs_id + ' .thumb_overlay').toggleClass('thumb_selected');
    },


    addColumnChooserBehaviors: function() {

        // a column is checked/unchecked
        $('.column_chooser').on("click", '.submenu li a', function() {

            slug = $(this).data('slug');
            label = $(this).attr("title");
            cols = opus.prefs['cols'];
            checkmark = $(this).find('i').first();

            if (!checkmark.is(":visible")) {

                checkmark.show();

                if (jQuery.inArray(slug,cols) < 0) {
                    // this slug was previously unselected, add to cols
                    $('<li id = "cchoose__' + slug + '">' + label + '<span class = "chosen_column_close">X</span></li>').hide().appendTo('.chosen_columns>ul').fadeIn();
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
            if (view_var == 'data') {
                o_browse.updatePage();
            } else {
                o_hash.updateHash();
            }

            return false;
        });


        // removes chosen column with X
        $('.column_chooser').on("click",'.chosen_column_close', function() {
            slug = $(this).parent().attr('id').split('__')[1];
            input = $('#column_chooser_input__' + slug);
            input.attr('checked',false);
            input.change();
        });

        // a column is checked/unchecked, adds to / removes from 'chosen' column
        $('.column_checkbox input[type="checkbox"].param_input', '#browse').change(function() {
            slug = $(this).data('slug');
            label = $(this).attr("title");
            cols = opus.prefs['cols'];

            if ($(this).is(':checked')) {
                // checkbox is checked
                if (jQuery.inArray(slug,cols) < 0) {
                    // this slug was previously unselected, add to cols
                    // $('#cchoose__' + slug).fadeOut().remove();
                    $('<li id = "cchoose__' + slug + '">' + label + '<span class = "chosen_column_close">X</span></li>').hide().appendTo('.chosen_columns>ul').fadeIn();
                    cols.push(slug);
                }
            } else {

                // checkbox is unchecked
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
            o_browse.updatePage();

         });

         // group header checkbox - lets user add/remove group of columns at a time
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
            o_browse.updatePage();

         });
    },

    fixBrowseControls: function() {
        return;
        /**
        if (opus.prefs.view != "browse") return;

        window_scroll = $(window).scrollTop();

        if (!window_scroll) {
            // we are at teh top of page
            if (opus.current_fixed_bar) {
                // we scrolled to top from elsewhere, unfix the control bar
                $(opus.current_fixed_bar).removeClass('browse_fixed');
            }
            return;
        }

        // this is for fixing the browse_controls
        if (o_browse.isAlmostScrolledIntoView('.browse_controls_container')) {
            if (opus.browse_controls_fixed) {
                // browse controls container is in view,
                // but browse controls are still fixed at top of page, move it back
                opus.browse_controls_fixed = false;
                $('.browse_controls','#browse').removeClass('browse_fixed');
            }
        } else {
            if (!opus.browse_controls_fixed) {
                // user is scrolling down the page and gallery controls have floated away
                // bring them back to top of page so they can be accessed
                opus.browse_controls_fixed = true;
                $('.browse_controls').addClass("browse_fixed");
            }
        }
        **/
    },

    // checkboxes
    checkRangeBoxes: function(ring_obs_id1, ring_obs_id2) {
        // make all list/td elements bt r1 and r2 be added to cart

        elements = ['#gallery__','#data__'];
        for (var key in elements) {
            element = elements[key];
            current_id = ring_obs_id1;
            while (current_id != ring_obs_id2) {

                // we know that the endpoints are already checked, so start with the next li element
                next_element = $(element + current_id, '#browse').next();

                if (next_element.hasClass("infinite_scroll_page")) {
                    // this is the infinite scroll indicator, continue to next
                    next_element = $(element + current_id, '#browse').next().next();
                }

                // check the boxes:
                if (element == '#gallery__') {
                    if (!next_element.find('.tools').hasClass("in")) {  // if not already checked
                        try {
                            ring_obs_id = next_element.attr("id").split('__')[1];
                            o_browse.toggleBrowseInCollectionStyle(ring_obs_id);
                        } catch(e) {}
                    }
                } else {
                    if (!next_element.find('.data_checkbox').hasClass('fa-check-square-o')) {
                        // box is not checked so checkity check it
                        next_element.find('.data_checkbox').toggleClass('fa-check-square-o').toggleClass('fa-square-o');
                    }

                }

                // now move along
                try {
                    current_id = next_element.attr("id").split('__')[1];
                } catch(e) {
                    break;  // no next_id means the view isn't drawn, so we don't need to worry about it
                }
            }
        }
    },

    startDataTable: function(namespace) {
        url = '/opus/table_headers.html?' + o_hash.getHash() + '&reqno=' + opus.lastRequestNo;
        if (namespace == '#collections') {
            url += '&colls=true';
        }
        $.ajax({ url: url,
            success: function(html) {
                $('.data', namespace).append(html);
                $(".data .data_table", namespace).stickyTableHeaders({ fixedOffset: 85 });
                opus.table_headers_drawn = true;
                o_browse.getBrowseTab();
            }
        });

    },

    // footer bar, indicator bar, browse footer bar
    infiniteScrollPageIndicatorRow: function(page) {
        // this is the bar that appears below each infinite scroll page to indicate page no

        opus.prefs.view == 'browse' ? browse_prefix = '' : browse_prefix = 'colls_';

        id = 'infinite_scroll_' + browse_prefix + opus.prefs.browse + '__' + page;

        /*jshint multistr: true */
        data = '<tr class = "infinite_scroll_page">\
                    <td colspan = "' + (opus.prefs['cols'].length +1) + '">\
                        <div class="navbar-inverse"> \
                            <span class = "back_to_top"><a href = "#top">back to top</a></span> \
                            <span class = "infinite_scroll_page_container" id = "' + id + '">Page ' + page + '</span><span class = "infinite_scroll_spinner">' + opus.spinner + '</span> \
                        </div>\
                </td>\
                </tr>';

        gallery = '<li class = "infinite_scroll_page navbar-inverse">\
                       <span class = "back_to_top"><a href = "#top">back to top</a></span>\
                       <span class = "infinite_scroll_page_container" id = "' + id + '">Page ' + page + '</span>\
                       <span class = "infinite_scroll_spinner">' + opus.spinner + '</span>\
                   </li>';

        // opus.page_bar_offsets['#'+id] = false; // we look up the page loc later - to be continued

        if (opus.prefs.browse == 'gallery') {
            return gallery;
        }
        return data;
    },


    // there are interactions that are applied to different code snippets,
    // this returns the namespace, view_var, prefix, and add_to_url
    // that distinguishes collections vs result tab views
    // usage:
    /*
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
        var prefix, page;
        if (opus.prefs.view == 'collection') {
            prefix = 'colls_';
        }
        if (opus.prefs.view == 'browse') {
            if (opus.prefs.browse == 'data') {
                page = opus.prefs.page[prefix + 'data'];
            } else {
                page = opus.prefs.page[prefix + 'gallery'];
            }
        }
        if (!page) { page = 1; }

        return page;
    },

    getBrowseTab: function() {

        view_info = o_browse.getViewInfo();
        namespace = view_info['namespace']; // either '#collection' or '#browse'
        prefix = view_info['prefix'];       // either 'colls_' or ''
        add_to_url = view_info['add_to_url'];  // adds colls=true if in collections view

        view_var = opus.prefs[prefix + 'browse'];  // either 'gallery' or 'data'

        if (opus.scroll_watch_interval) {
            clearInterval(opus.scroll_watch_interval); // hold on cowgirl only 1 page at a time
        }

        var url = "/opus/api/images/small.html?alt_size=full&";
        if (opus.prefs[prefix + 'browse'] == 'data') {
            url = '/opus/api/data.html?';

            // get table headers for table view
            if (!opus.table_headers_drawn) {
                o_browse.startDataTable(namespace);
                return; // startDataTable() starts data table and then calls getBrowseTab again
            }
        }
        url += o_hash.getHash() + '&reqno=' + opus.lastRequestNo + add_to_url;

        footer_clicks = opus.browse_footer_clicks[prefix + view_var]; // default: {'gallery':0, 'data':0, 'colls_gallery':0, 'colls_data':0 };

        // figure out the page
        start_page = opus.prefs.page[prefix + view_var]; // default: {'gallery':1, 'data':1, 'colls_gallery':1, 'colls_data':1 };

        page = parseInt(start_page, 10) + parseInt(footer_clicks, 10);
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
            if (view_var == 'gallery') {
                $(indicator_row).appendTo('.gallery', namespace).show();
            } else {
                $(".data_table tr:last", namespace).after(indicator_row);
                $(".data_table tr:last", namespace).show();  // i dunno why couldn't chain these 2
            }
        }


        url += '&page=' + page;

        opus.prefs[prefix + view_var] = page;

        // NOTE if you change alt_size=full here you must also change it in gallery.html template
        $.ajax({ url: url,
            success: function(html){
               // bring in the new page
               function appendBrowsePage() { // for chaining effects

                    // hide the views that aren't supposed to be showing
                    for (var v in opus.all_browse_views) {
                        var bv = opus.all_browse_views[v];
                        if ($('.' + bv, namespace).is(":visible") && bv != opus.prefs.browse) {
                            $('.' + bv, namespace).hide();
                        }
                    }
                    // append the new html
                    if (view_var == 'data') {
                        $(html).appendTo($('.' + view_var + ' tbody', namespace)).fadeIn();
                    } else {
                        opus.gallery_begun = true;
                        $(html).appendTo($('.' + view_var, namespace)).fadeIn();
                    }

                    // fade out the spinner
                    $('.infinite_scroll_spinner', namespace).fadeOut("fast");

               }

                // get the browse nav header?
                if (!opus.gallery_begun) {
                    $.ajax({ url: "/opus/browse_headers.html",
                        success: function(html){
                            $('.browse_nav', namespace).html(html);
                            // change the link text
                            if (opus.prefs.browse == 'gallery') {
                                $('.browse_view', namespace).text('view table');
                            } else {
                                $('.browse_view', namespace).text('view gallery');
                            }
                    }});
                }

                // doit!
                appendBrowsePage();

                o_browse.pageInViewIndicator();

                // $('#' + prefix + 'page', namespace).html(page);

                // turn the scroll watch timer back on
                opus.scroll_watch_interval = setInterval(o_browse.browseScrollWatch, 1000);

                o_browse.textInputMonitor();

                // setup colorbox
                var $overflow = '';
                var colorbox_params = {
                    rel: 'colorbox',

                    className:"gallery_overlay_bg",

                    reposition:false,
                    scalePhotos:true,
                    scrolling:false,
                    previous: '<i class="ace-icon fa fa-arrow-left"></i>',
                    next: '<i class="ace-icon fa fa-arrow-right"></i>',
                    close:'&times;',
                    current:'{current} of {total}',
                    maxWidth:'100%',
                    maxHeight:'100%',
                    onOpen:function(){
                        $overflow = document.body.style.overflow;
                        document.body.style.overflow = 'hidden';
                    },
                    onClosed:function(){
                        document.body.style.overflow = $overflow;
                    },
                    onComplete:function(){
                        $.colorbox.resize();
                    }
                };
                $('.ace-thumbnails [data-rel="colorbox"]').colorbox(colorbox_params);

            }

        });
    },


    // we watch the paging input fields to wait for pauses before we trigger page change. UX!
    // this funciton starts that monitor based on what view is currently up
    // it also clears any old one.
    textInputMonitor: function() {
        // which field are we working on? defines which global monitor list we use

        ms = 500;

        view_var = opus.prefs[prefix + 'browse'];  // either 'gallery' or 'data'
        view_info = o_browse.getViewInfo();
        namespace = view_info['namespace']; // either '#collection' or '#browse'
        prefix = view_info['prefix'];       // either 'colls_' or ''

        field_monitor = opus[prefix + 'page_monitor_' + view_var];
        var value = parseInt($('#' + prefix + 'page_no').val(), 10);

        // clear the old monitor and start a new one
        if (opus.input_timer) clearTimeout(opus.input_timer);
		opus.input_timer = setTimeout(
            function() {
                if (field_monitor[field_monitor.length-1]  == value){
					// the user has not moved in 2 seconds
					o_browse.updatePage(parseInt(value, 10));
					// opus.force_load = true;
					// setTimeout("o_hash.updateHash()",0);
					// tidy up, keep the array small..
					if (field_monitor.length > 3) field_monitor.shift(); // keep it trimmed
				} else {
					// array is changing, user is still typing
					// maintain our array with our new value
                    field_monitor[field_monitor.length]  = value;
					// o_browse.textInputMonitor();
				}
            },ms);

            // update the global monitor
            opus[prefix + 'page_monitor_' + view_var] = field_monitor;
        },


        resetQuery: function() {
            /*
            when the user changes the query and all this stuff is already drawn
            need to reset all of it
            */
            opus.browse_footer_clicks = {"gallery":0, "data":0, "colls_gallery":0, "colls_data":0 };
            browse_view_scrolls = reset_browse_view_scrolls;
            opus.table_headers_drawn = false;
            opus.gallery_begun = false;
            $('.data').empty();  // yes all namespaces
            $('.gallery').empty();
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


        // this is on a setInterval
        browseScrollWatch: function() {

            view_info = o_browse.getViewInfo();
            prefix = view_info['prefix']; // none or colls_
            view_var = opus.prefs[prefix + 'browse'];  // data or gallery

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

        getColumnChooser: function() {
            /**
            offset = $('.data_table', '#browse').offset().top + $('.data_table .column_label', '#browse').height() + 10;
            left = $('.get_column_chooser').parent().offset().left - $('.column_chooser').width()  ;
            $('.column_chooser').css('top', Math.floor(offset) + 'px');
            $('.column_chooser').css('left', Math.floor(left) + 'px');
            **/


            if (opus.column_chooser_drawn) {
                if ($('.column_chooser').is(":visible")) {
                    var scrollto = $(window).scrollTop() + 20;
                    $('.column_chooser').css("top", scrollto);
                    $('.column_chooser').effect("highlight", {}, 3000);
                } else {
                    // wtf
                    $('.column_chooser').dialog({
                            height: 600,
                            width: 900,
                            modal: true,
                            resizable: true,
                            draggable:true,
                            dialogClass: 'no-close success-dialog'
                        });
                }
                return;
            }

            // column_chooser has not been drawn, fetch it from the server and apply its behaviors:
            $('.column_chooser').html(opus.spinner);
            $('.column_chooser').dialog({
                    height: 600,
                    width: 900,
                    modal: true,
                    resizable: true,
                    draggable:true,
                    dialogClass: 'no-close success-dialog'
                });


            url = 'forms/column_chooser.html?' + o_hash.getHash();

            $('.column_chooser').load( url, function(response, status, xhr)  {

               opus.column_chooser_drawn=true;  // this gets saved not redrawn

               o_browse.addColumnChooserBehaviors();

               // we keep these all open in the column chooser, they are all closed by default
               /* todo */

               // dragging to reorder the chosen
               $( ".chosen_columns>ul").sortable({
                   cursor: 'crosshair',
                   stop: function(event, ui) { o_browse.columnsDragged(this); }
               });
            });
        },

        columnsDragged: function(element) {
            var cols = $(element).sortable('toArray');
            $.each(cols, function(key, value)  {
                cols[key] = value.split('__')[1];
            });
            opus.prefs['cols'] = cols;
            // if we are in gallery - just change the data-struct that gallery draws from
            // if we are in table -
            // $('.gallery', '#browse').html(opus.spinner);

            // we are about to update the same page we just updated, it will replace
            // the one that is showing,

            // set last page to one before first page that is showing in the interface
            o_browse.updatePage();

        },






};