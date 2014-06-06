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

         // the gallery/table toggle
         $('#browse').on("click", '.browse_view', function() {

            var browse_view = $(this).text().split(' ')[1];  // table or gallery
            var hiding, showing
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
            if (!$('.' + showing, namespace).length) {
                o_browse.getBrowseTab();
            } else {
                // change the text on the link in the browse nav
                if (opus.prefs.browse == 'gallery') {
                    $('.browse_view', namespace).text('view table');
                } else {
                    $('.browse_view', namespace).text('view gallery');
                }
            }

            return false;
        });

      // 'add range' adds a range of observations to collection
        $('#browse').on("click", '.addrange', function() {

            if ($('.addrange', '#browse').text() != "add range") {
                alert('please select an observation to begin your range');
                return false;
            }
            opus.addrange_clicked = true;
            $('.addrange','#browse').text("select range start");
            return false;
        });

        // click a browse tools icon
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

                // handle the visual indication of state
                o_browse.toggleBrowseInCollectionStyle(ring_obs_id, this);

                // is this checked? or unchecked..
                action = 'remove';
                if ($(this).parent().hasClass("in")) {
                    action = 'add';  // this ring_obs_id is being added to cart
                }

                // make sure the checkbox for this observation in the other view (either data or gallery)
                // is also checked/unchecked - if that view is drawn
                for (var key in opus.all_browse_views) {
                    bv = opus.all_browse_views[key];
                    checked = false;
                    if (action == 'add') checked = true;
                    try {
                        $('#' + bv + 'input__' + ring_obs_id).attr('checked',checked);
                    } catch(e) { } // view not drawn yet so no worries
                }

                // check if we are clicking as part of an 'add range' interaction
                if (!opus.addrange_clicked) {

                    // no add range, just add this obs to collection
                    o_collections.editCollection(ring_obs_id,action);

                } else {
                    // addrange clicked

                    element = "li";
                    if (opus.prefs.browse == 'data') {
                            element = "td";
                    }
                    if (!opus.addrange_min) {

                        // this is the min side of the range
                        $('.addrange','#browse').text("select range end");
                        index = $('#gallery__' + ring_obs_id).index();
                        opus.addrange_min = { "index":index, "ring_obs_id":ring_obs_id };

                    } else {
                        // we have both sides of range

                        $('.addrange','#browse').text("add range");
                        index = $('#gallery__' + ring_obs_id).index();

                        if (index > opus.addrange_min['index']) {
                            range = opus.addrange_min['ring_obs_id'] + "," + ring_obs_id;
                            o_browse.checkRangeBoxes(opus.addrange_min['ring_obs_id'], ring_obs_id);
                        } else {
                            // user clicked later box first, reverse them for server..
                            range = ring_obs_id + "," + opus.addrange_min['ring_obs_id'];
                            o_browse.checkRangeBoxes(ring_obs_id, opus.addrange_min['ring_obs_id']);
                        }

                        o_collections.editCollection(range,'addrange');

                        opus.addrange_clicked = false;
                        opus.addrange_min = false;

                    }
                }
            }

            return false;
        }); // end click a browse tools icon

        /*
        $('.column_ordering a', '#browse').live("click", function() {
            var order = $(this).parent().parent().attr("class");
            if ($(this).attr("class") == "descending") {
                order = '-' + order;
            }
            opus.prefs['order'] = order;
            opus.browse_tab_click = true;
            opus.last_page = {'browse':{'data':0, 'gallery':0 }};  // may need this too: 'colls_browse':{ 'data':0, 'gallery':0 }};
            o_browse.updatePage(1);
            return false;
        });

        */


        /*
        // results paging
        $('.next, .prev').live('click', function() {
            // all this does is update the number that shows in the box and then calls textInputMonitor
            page_no_elem = $(this).parent().next().find('.page_no');
            this_page = parseInt(page_no_elem.val(), 10);
            if ( $(this).hasClass("next")) {
                page = this_page + 1;
            } else if ($(this).hasClass("prev")) {
                 page = this_page - 1;
            }
            page_no_elem.val(page);
            o_browse.textInputMonitor(page_no_elem.attr("id"),500);
            return false;
        });

        // change page
        $('#page_no','#browse').live("change",function() {
            page = parseInt($(this).val(), 10);
            o_browse.updatePage(page);
        });
        $('#colls_page_no','#collections').live("change",function() {
            page = parseInt($(this).val(), 10);
            o_browse.updatePage(page);
        });


        // gallery thumbnail behaviors
        $('.get_detail_icon','#browse').live('click', function() {
            var ring_obs_id = $(this).attr("id").split('__')[1].split('/').join('-');

            // now ajax get the detail page:
            o_detail.getDetail(ring_obs_id);

            }); // end live

        // back to top link at bottom of gallery
        $('a[href=#top]','#browse').live('click',function() {
            $('html, body').animate({scrollTop:0}, 'slow');
            return false;
        });



        // this controls the page indicator bars you get with infinie scroll
        $(window).scroll(function() {
             o_browse.fixBrowseControls();
          });

        // close/open column chooser
        $('.get_column_chooser').live('click', function() {
                o_browse.getColumnChooser();
                return false;
        });

    */


    }, // end browse behaviors


    toggleBrowseInCollectionStyle: function(ring_obs_id, icon_a_element) {
        $(icon_a_element).parent().toggleClass("in"); // this class keeps parent visible when mouseout
        $(icon_a_element).find('i').toggleClass('thumb_selected_icon');
        $('#gallery__' + ring_obs_id + ' .thumb_overlay').toggleClass('thumb_selected');
    },


    browseControlIndicator: function(id) {
        view_info = o_browse.getViewInfo();
        namespace = view_info['namespace'];
        prefix = view_info['prefix'];
        add_to_url = view_info['add_to_url'];

        view_var = opus.prefs[prefix + 'browse'];

        // show on the browse menu container what view we are in.
        $('.browse_controls li', namespace).removeClass('view_indicator');
        if (id) {
            $(id).parent().addClass('view_indicator');
            return;
        }
        switch (opus.prefs[prefix+'browse']) {
            case 'data':
                $('.data_view', namespace).parent().addClass('view_indicator');
                break;

            default:
                $('.gallery_view', namespace).parent().addClass('view_indicator');
        }
    },

    addColumnChooserBehaviors: function() {

        // close the chooser box dialogue thingy
        $('#column_chooser .close').click(function() {
             $('#column_chooser').jqmHide();
             return false;
        });

        // a column is checked/unchecked
        $('.menu_list li a','#browse').click(function() {
            input = $(this).parent().find('input');
            if (!input.attr('checked')) {
                input.attr('checked',true);
            } else {
                input.attr('checked',false);
            }
            input.change(); // you have to do this to get the change event below to fire
            return false;
        });

        // removes chosen column with X
        $('.chosen_column_close').live("click",function() {
            slug = $(this).parent().attr('id').split('__')[1];
            input = $('#column_chooser_input__' + slug);
            input.attr('checked',false);
            input.change();
        });

        // a column is checked/unchecked, adds to / removes from 'chosen' column
        $('.column_checkbox input[type="checkbox"].param_input', '#browse').change(function() {
            slug = $(this).data('slug');
            label = $(this).data('label');
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
            o_hash.updateHash();

            // we are about to update the same page we just updated, it will replace
            // the one that is showing, so unset the last_page var
            view_info = o_browse.getViewInfo();
            prefix = view_info['prefix'];
            view_var = opus.prefs[prefix + 'browse'];
            // set last page to one before first page that is showing in the interface
            opus.last_page[prefix + 'browse'][view_var] = opus.prefs.page - 1;

            // now update the browse table
            o_browse.updatePage(opus.prefs.page);

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
             o_hash.updateHash();

            // we are about to update the same page we just updated, it will replace
            // the one that is showing, so unset the last_page var
            view_info = o_browse.getViewInfo();
            prefix = view_info['prefix'];
            view_var = opus.prefs[prefix + 'browse'];
            // set last page to one before first page that is showing in the interface
            opus.last_page[prefix + 'browse'][view_var] = opus.prefs.page - 1;

            // now update the browse table
            o_browse.updatePage(opus.prefs.page);

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
        if (o_browse.isScrolledIntoView('.browse_controls_container')) {
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


    /*
    // this is a lot of crap for keeping track of scroll position for when user returns to the page from another page - to be coninued
     $(window).resize(function() {
         // browser has been resized!
         // reset any page_bar locations
         for (element in opus.page_bar_offsets) {
             if (opus.page_bar_offsets[element]) { // only if they've already been set
                 opus.page_bar_offsets[element] = Math.floor($(element).parent().offset().top);
             }
         }
    });


    // see element name of current page showing
    // used to scroll to same location when switching from table to gallery view
    currentPageInView: function() {

        last_element = '';
        greater_than_found = false;
        page = false;

        window_scroll = $(window).scrollTop();

        for (element in opus.page_bar_offsets) {

            if (!opus.page_bar_offsets[element]) {
                // this one hasn't been set yet, find location of this page bar element
                opus.page_bar_offsets[element] = Math.floor($(element).parent().offset().top);
            }

            scrolltop = opus.page_bar_offsets[element];


            if (window_scroll >= scrolltop) {
                // user has scrolled past this element
                greater_than_found = true;
            } else if (greater_than_found) {
                    // this element is less than the scroll pos and the last element was greater
                    // so the last element is what page we are on
                    page = $(last_element).attr("id").split('__')[1];
                    break; // got what we wanted
            }

            last_element=element;
        }

        if (!page) {
            if (greater_than_found) {
                page = $(last_element).attr("id").split('__')[1];
            } else {
                page = opus.prefs.page;
            }
        }
        return 'inifite_scroll_' + opus.prefs.browse + '__' + page;
    },

    */


    checkRangeBoxes: function(ring_obs_id1, ring_obs_id2) {
        // make all list/td elements bt r1 and r2 be added to cart

        elements = ['#gallery__','#data__'];
        for (var key in elements) {
            element = elements[key];
            current_id = ring_obs_id1;
            while (current_id != ring_obs_id2) {

                // we know that the endpoints are already checked, so start with the next li element
                next_element = $(element + current_id, '#browse').next();
                /*
                if (next_element.hasClass("inifite_scroll_page")) {
                    // this is the infinite scroll indicator, continue to next
                    next_element = $(element + current_id, '#browse').next().next();
                }
                */
                // check the boxes:
                // $(next).find('input').attr('checked',true);
                if (!next_element.find('.tools').hasClass("in")) {  // if not already checked
                    icon_a_element = next_element.find('.fa-check').parent(); //
                    try {
                        ring_obs_id = next_element.attr("id").split('__')[1];
                        o_browse.toggleBrowseInCollectionStyle(ring_obs_id, icon_a_element);
                    } catch(e) {}
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

    createTooltip: function(element, title) {
        $(element).jqm();

    },


    startDataTable: function(namespace) {
        url = '/opus/table_headers.html?' + o_hash.getHash() + '&reqno=' + opus.lastRequestNo;
        if (namespace == '#collections') {
            url += '&colls=true';
        }
        $.ajax({ url: url,
                success: function(html) {
                    opus.table_headers_drawn = true;
                    $('.data', namespace).html(html);
                    o_browse.getBrowseTab();
                    $(".data .column_label", namespace).each(function() {

                        //o_browse.createTooltip(this, $(this).text() );

                     }); // end each
                     $(".data", namespace).stickyTableHeaders({ fixedOffset: 100 });

                }
        });

    },

    infiniteScrollPageIndicatorRow: function(page) {
        opus.prefs.view == 'browse' ? browse_prefix = '' : browse_prefix = 'colls_';

        id = 'inifite_scroll_' + browse_prefix + opus.prefs.browse + '__' + page;

        /*jshint multistr: true */
        data = '<tr class = "inifite_scroll_page">\
                <td><span class = "back_to_top"><a href = "#top">top</a></span></td> \
                <td colspan = "' + opus.prefs['cols'].length + '">\
                <span class = "infinite_scroll_page_container" id = "' + id + '">Page ' + page + '</span><span class = "infinite_scroll_spinner">' + opus.spinner + '</span> \
                </td></tr>';

        gallery = '<li class = "inifite_scroll_page">\
                   <span class = "back_to_top"><a href = "#top">back to top</a></span>\
                   <span class = "infinite_scroll_page_container" id = "' + id + '">Page ' + page + '</span><span class = "infinite_scroll_spinner">' + opus.spinner + '</span></li>';

        // opus.page_bar_offsets['#'+id] = false; // we look up the page loc later - to be continued

        if (opus.prefs.browse == 'gallery') {
            return gallery; }
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
        // this function handles fetching the browse views - gallery or table - for both the Browse and Collections tabs
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

    getBrowseTab: function() {

        var url = "/opus/api/images/small.html?alt_size=full&";

        view_info = o_browse.getViewInfo();
        namespace = view_info['namespace'];
        prefix = view_info['prefix'];
        add_to_url = view_info['add_to_url'];

        view_var = opus.prefs[prefix + 'browse'];  // either 'gallery' or 'data'

        opus.browse_empty = false;

        clearInterval(opus.scroll_watch_interval); // hold on cowboy only 1 page at a time

        o_browse.browseControlIndicator(false);

        if (opus.prefs[prefix + 'browse'] == 'data') {

            if (!opus.table_headers_drawn) {
                o_browse.startDataTable(namespace);
                return; // startDataTable() starts data table and then calls getBrowseTab again
            }
            url = '/opus/api/data.html?';
        }

        url += o_hash.getHash() + '&reqno=' + opus.lastRequestNo + add_to_url;

        $('#' + prefix + 'page_no', namespace).val(opus.prefs[prefix + 'page']);
        $('#' + prefix + 'pages', namespace).html(opus[prefix + 'pages']);

        // $(".browse_footer_label", '#browse').empty().html(opus.spinner);   made default

        opus.prefs[view_var] == 'gallery' ? footer_clicks = opus.browse_footer_clicks[prefix + 'gallery'] : footer_clicks = opus.browse_footer_clicks[prefix + 'data'];

        // figure out the page

        start_page = opus.prefs[prefix + 'page'];
        needs_indicator_bar = false;
        if (opus.browse_footer_clicked) {
            opus.browse_footer_clicked=false;
            needs_indicator_bar = true;
            page = parseInt(start_page, 10) + parseInt(footer_clicks, 10);
        } else {
            page = start_page;
        }

        if (opus[prefix + 'pages'] && page > opus[prefix + 'pages']) {
            // the page is higher than the total number of pages, reset it to the last page
            page = opus[prefix + 'pages'];
            $('#' + prefix + 'page_no', namespace).val(page); // reset the display
        }

        if (!page) {
            page = 1;  //
        }


        // did we already fetch this page?
        last_page = opus.last_page[prefix + 'browse'][view_var];
        if (page == last_page && !opus.browse_tab_click) {
            // we already fetched this page, do nothing
            return;
        }
        opus.browse_tab_click = false;

        if (page < 1) {
            page = 1;
            $('#' + prefix + 'page_no', namespace).val(page); // reset the display
        }

        if (needs_indicator_bar) {
            indicator_row = o_browse.infiniteScrollPageIndicatorRow(page);
            if (opus.prefs[view_var] == 'gallery') {
                $(indicator_row).appendTo('.gallery', namespace).show()
            } else {
                $(".data_table tr:last", namespace).after(indicator_row);
                $(".data_table tr:last", namespace).show();  // i dunno why couldn't chain these 2
            }
        }
        url += '&page=' + page;

        // NOTE if you change alt_size=full here you must also change it in gallery.html template
        $.ajax({ url: url,
            success: function(html){
               // bring in the new images
               function appendBrowsePage() {

                    // append browse page
                    for (var v in opus.all_browse_views) {
                        var bv = opus.all_browse_views[v];
                        if ($('.' + bv, namespace).is(":visible")) {
                            $('.' + bv, namespace).fadeOut();
                        }
                    }

                    if (view_var == 'data') {
                        $('.' + view_var + ' tbody', namespace).append(html);
                    } else {
                        $('.' + view_var, namespace).append(html);
                    }
                    $('.' + view_var, namespace).fadeIn();

                    opus.last_page[prefix + 'browse'][view_var] = page;

                    $('.infinite_scroll_spinner', namespace).fadeOut("fast");

                    // turn the scroll watch timer back on
                    opus.scroll_watch_interval = setInterval(o_browse.browseScrollWatch, 1000);

                    opus.prefs[view_var] == 'gallery' ? footer_clicks = opus.browse_footer_clicks[prefix + 'gallery'] : footer_clicks = opus.browse_footer_clicks[prefix + 'data'];

                    // if they've clicked here x times show the checkbox
                    if (parseInt(footer_clicks, 10) > opus.footer_clicks_trigger) {
                        $('.browse_footer_checkbox', namespace).html('<input type="checkbox" name="browse_auto" ' + opus.browse_auto + '>load automatically when scrolling to end');
                    }
               }


               appendBrowsePage();

                // get the browse nav header
                $.ajax({ url: "browse_headers.html",
                    success: function(html){
                       $('.browse_nav', namespace).hide().html(html);
                            // change the link text
                            if (opus.prefs.browse == 'gallery') {
                                $('.browse_view', namespace).text('view table');
                            } else {
                                $('.browse_view', namespace).text('view gallery');
                            }
                        $('.browse_nav', namespace).fadeIn();
                }});

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


    // we watch the paging inputs to wait for pauses before we trigger page change. UX, baby.
    textInputMonitor: function(field,ms) {

        // which field are we working on? defines which global monitor list we use
        switch(field) {
            case 'page':
                field_monitor = opus.page_monitor;
                prefix = '';
                break;
            case 'colls_page':
                field_monitor = opus.page_colls_monitor;
                prefix = 'colls_';
                break;
            default:
                var field_monitor = opus.text_field_monitor;
            }
            var value = parseInt($('#' + prefix + 'page_no').val(), 10);

        if (opus.input_timer) clearTimeout(opus.input_timer);

		opus.input_timer = setTimeout(
            function() {
                if (field_monitor[field_monitor.length-1]  == value){
					// the user has not moved in 2 seconds
					o_browse.updatePage(parseInt(value, 10));
					// opus.force_load = true;
					// setTimeout("o_hash.updateHash()",0);
					// tidy up, keep the array small..
					if (field_monitor.length > 3) field_monitor.shift();
				} else {
					// array is changing, user is still typing
					// maintain our array with our new value
                    field_monitor[field_monitor.length]  = value;
					o_browse.textInputMonitor(field,ms);
				}
            },ms);

            // update the global monitor
            switch(field) {
                case 'page':
                opus.page_monitor = field_monitor;
                break;
            case 'page_colls':
                opus.page_colls_monitor = field_monitor;
                break;
            default:
                opus.text_field_monitor = field_monitor;            }
        },

        updatePage: function(page) {
            opus.browse_footer_clicks = {'gallery':0, 'data':0};
			opus.prefs.page = page;
			o_hash.updateHash();
			$('.gallery', '#browse').empty();
			$(".data_container", '#browse').empty();
            o_browse.getBrowseTab();

        },

        // http://stackoverflow.com/questions/487073/jquery-check-if-element-is-visible-after-scroling thanks!
        isScrolledIntoView: function(elem) {

                var docViewTop = $(window).scrollTop();
                var docViewBottom = docViewTop + $(window).height();

                var elemTop = $(elem).offset().top;
                var elemBottom = elemTop + $(elem).height();

                return ((elemBottom >= docViewTop) && (elemTop <= docViewBottom) && (elemBottom <= docViewBottom) &&  (elemTop >= docViewTop) );
        },


        // this is on a setInterval
        browseScrollWatch: function() {
            // this is for the infinite scroll footer bar
            if (opus.browse_auto && o_browse.isScrolledIntoView('#end_of_page')) {
                if (opus.prefs.view=='browse') {
                    opus.prefs.browse == 'gallery' ? opus.browse_footer_clicks['gallery']++ : opus.browse_footer_clicks['data']++;
                } else if (opus.prefs.view=='collections'){
                    opus.prefs.colls_browse == 'gallery' ? opus.browse_footer_clicks['colls_gallery']++ : opus.browse_footer_clicks['colls_data']++;
                }
                opus.browse_footer_clicked=true;
                o_browse.getBrowseTab();
            }
        },

        GalleryFooterClick: function() {
           delay = 0;  // a pause before the next set of gallery images is drawn

           opus.browse_footer_clicked=true;
           // they clicked the footer bar, did they check the box?
           if ($('input[name=browse_auto]').is(':checked')) {   // box is checked
               if (opus.browse_auto != 'checked') {
                    // box was unchecked before and now it is checked,
                    // aka they are checking the box for the first time,
                    // slight pause to let them see their check get drawn
                   delay = 500;
                   opus.browse_auto = 'checked';
               }
           } else { // auto box is unchecked
               opus.browse_auto = '';
               opus.prefs.browse == 'gallery' ? opus.browse_footer_clicks['gallery']++ : opus.browse_footer_clicks['data']++;
               setTimeout('o_browse.getBrowseTab()',delay);
           }

           return false;
        },

        getColumnChooser: function() {
            /**
            offset = $('.data_table', '#browse').offset().top + $('.data_table .column_label', '#browse').height() + 10;
            left = $('.get_column_chooser').parent().offset().left - $('#column_chooser').width()  ;
            $('#column_chooser').css('top', Math.floor(offset) + 'px');
            $('#column_chooser').css('left', Math.floor(left) + 'px');
            **/

            if (opus.column_chooser_drawn) {
                if ($('#column_chooser').is(":visible")) {
                    $('#column_chooser').effect("highlight", {}, 3000);
                } else {
                    $('#column_chooser').jqmShow();
                }
                return;
            }

            // column_chooser has not been drawn, fetch it from the server and apply its behaviors:
            $('#column_chooser').html(opus.spinner);
            $('#column_chooser').jqm({
                overlay: 0,
            });

            $('#column_chooser').jqmShow();

            url = 'forms/column_chooser.html?' + o_hash.getHash();

            $('#column_chooser').load( url, function(response, status, xhr)  {
                       opus.column_chooser_drawn=true;

                       // we keep these all open in the column chooser, they are all closed by default
                       $('.menu_cat_triangle','#browse').toggleClass('opened_triangle');
                       $('.menu_cat_triangle','#browse').toggleClass('closed_triangle');

                       o_browse.addColumnChooserBehaviors();
                       $('#column_chooser','#browse').draggable();
                       $('#column_chooser','#browse').resizable();

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
            o_hash.updateHash();
            // if we are in gallery - just change the data-struct that gallery draws from
            // if we are in table -
            // $('.gallery', '#browse').html(opus.spinner);

            // we are about to update the same page we just updated, it will replace
            // the one that is showing, so unset the last_page var
            // we are about to update the same page we just updated, it will replace
            // the one that is showing, so unset the last_page var
            view_info = o_browse.getViewInfo();
            prefix = view_info['prefix'];
            view_var = opus.prefs[prefix + 'browse'];
            // set last page to one before first page that is showing in the interface
            opus.last_page[prefix + 'browse'][view_var] = opus.prefs.page - 1;
                        // now update the browse table
            o_browse.updatePage(opus.prefs.page);

            o_browse.updateBrowse();

        },


        // this is used to update the browse tab after a column change
        updateBrowse: function() {
            opus.browse_footer_clicks = 0;
            $('.data_table','#browse').remove();
            o_browse.getBrowseTab();
        },




};