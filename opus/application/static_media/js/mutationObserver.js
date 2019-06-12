/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $, _ */
/* globals o_browse, o_cart, o_search, opus */

/* jshint varstmt: false */
var o_mutationObserver = {
/* jshint varstmt: true */
    // MutationObserver: detect any DOM changes and update ps correspondingly
    observePerfectScrollbar: function() {
        // Config object: tell the MutationObserver what type of changes to be detected
        let switchTabObserverConfig = {
            attributeFilter: ["class"], // detect action of switching tabs
        };

        // select metadata, widgets and sidebar menu items can be collapsed, so we need to detect attribute changes
        // set attributes to true
        let generalObserverConfig = {
            attributes: true,
            childList: true,
            subtree: true,
        };

        // detect add/removal of each element's children
        let childListObserverConfig = {
            childList: true,
            subtree: true,
        };

        // detect attribute changes of each element
        let attrObserverConfig = {
            attributes: true,
            subtree: true,
        };

        let searchSideBarHeightChanged = _.debounce(o_search.searchSideBarHeightChanged, 200);
        let searchWidgetHeightChanged = _.debounce(o_search.searchHeightChanged, 200);
        let searchHeightChanged = _.debounce(o_search.searchHeightChanged, 200);
        let adjustBrowseHeight = _.debounce(o_browse.adjustBrowseHeight, 200);
        let adjustTableSize = _.debounce(o_browse.adjustTableSize, 200);
        let adjustProductInfoHeight = _.debounce(o_cart.adjustProductInfoHeight, 200);
        let adjustHelpPanelHeight = _.debounce(opus.adjustHelpPanelHeight, 200);
        let adjustMetadataSelectorMenuPS = _.debounce(o_browse.adjustMetadataSelectorMenuPS, 200);
        let adjustSelectedMetadataPS = _.debounce(o_browse.adjustSelectedMetadataPS, 200);
        let adjustBrowseDialogPS = _.debounce(o_browse.adjustBrowseDialogPS, 200);

        // Init MutationObserver with a callback function. Callback will be called when changes are detected.
        let switchTabObserver = new MutationObserver(function(mutationsList) {
            // this is for switch from other tabs to target page
            searchHeightChanged();
            adjustBrowseHeight();
            adjustTableSize();
            adjustProductInfoHeight();
        });

        // ps in search sidebar
        let searchSidebarObserver = new MutationObserver(function(mutationsList) {
            let lastMutationIdx = mutationsList.length - 1;
            mutationsList.forEach((mutation, idx) => {
                if (mutation.type === "childList") {
                    // update ps when there are any children added/removed
                    searchSideBarHeightChanged();
                } else if (mutation.type === "attributes") {
                    // at the last mutation
                    if (idx === lastMutationIdx) {
                        if (mutation.target.classList.value.match(/collapse/)) {
                            // If a collapse/expand happened (attribute changes),
                            // we only update ps at the last mutation when the animation
                            // finishes and class/style are finalized.
                            // Note we call the original version here, not the debounced
                            // version, because we need the PS to be visible instantly in
                            // order for scrollTop to work below.
                            o_search.searchSideBarHeightChanged();
                            // if the collapse opens below the viewable area, move the scrollbar
                            // only move the scrollbar if we open the menu item
                            let lastElement = $(mutation.target).children().last();
                            if (mutation.target.classList.value.match(/show/) &&
                                !lastElement.isOnScreen("#sidebar-container", 1)) {
                                let containerHeight = o_search.searchBarContainerHeight();
                                let containerTop = $("#sidebar-container").offset().top;
                                let containerBottom = containerHeight + containerTop;
                                let elementTop = lastElement.offset().top;
                                let elementHeight = lastElement.outerHeight();
                                let newScrollPosition = $("#sidebar-container").scrollTop() + (elementTop + elementHeight - containerBottom);
                                $("#sidebar-container").scrollTop(newScrollPosition);
                            }
                        } else if (mutation.target.classList.value.match(/spinner/)) {
                            // If new submenu is added but spinner is still running, we update ps after spinner is done
                            searchSideBarHeightChanged();
                        }
                    }
                }
            });
        });

        // ps in search widgets
        let searchWidgetObserver = new MutationObserver(function(mutationsList) {
            let lastMutationIdx = mutationsList.length - 1;
            mutationsList.forEach((mutation, idx) => {
                if (mutation.type === "childList") {
                    // update ps when there is any children added/removed
                    searchWidgetHeightChanged();
                } else if (mutation.type === "attributes") {
                    // at the last mutation
                    if (idx === lastMutationIdx) {
                        if (mutation.target.classList.value.match(/collapse/)) {
                            // If there is a collapse/expand happened (attribute changes), we only update ps when the animation finishes and class/style are finalized
                            searchWidgetHeightChanged();
                        } else if (mutation.target.classList.value.match(/spinner/)) {
                            // If new widget is added but spinner is still spinning, we update ps after spinner is done
                            searchWidgetHeightChanged();
                        } else if (mutation.target.classList.value.match(/mult_group/)) {
                            // If new mult_group is open inside widgets, we update ps
                            searchWidgetHeightChanged();
                        }
                    }
                }
            });
        });

        // ps in cart page
        let cartObserver = new MutationObserver(function(mutationsList) {
            adjustProductInfoHeight();
        });

        // ps in help page
        let helpPanelObserver = new MutationObserver(function(mutationsList) {
            mutationsList.forEach((mutation, idx) => {
                //ignore attribute change in ps to avoid infinite loop of callback function caused by ps update
                if (!mutation.target.classList.value.match(/ps/)) {
                    adjustHelpPanelHeight();
                }
            });
        });

        // ps in select metadata modal
        let metadataSelectorObserver = new MutationObserver(function(mutationsList) {
            adjustMetadataSelectorMenuPS();
            adjustSelectedMetadataPS();
        });

        let metadataSelectorMenuObserver = new MutationObserver(function(mutationsList) {
            let lastMutationIdx = mutationsList.length - 1;
            mutationsList.forEach((mutation, idx) => {
                if (idx === lastMutationIdx) {
                    if (mutation.target.classList.value.match(/submenu.collapse/)) {
                        // If a collapse/expand happened (attribute changes),
                        // we only update ps at the last mutation when the animation
                        // finishes and class/style are finalized.
                        // Note we call the original version here, not the debounced
                        // version, because we need the PS to be visible instantly in
                        // order for scrollTop to work below.
                        o_browse.adjustMetadataSelectorMenuPS();
                        // if the collapse opens below the viewable area, move the scrollbar
                        // only move the scrollbar if we open the menu item
                        let lastElement = $(mutation.target).children().last();
                        if (mutation.target.classList.value.match(/show/) &&
                            !lastElement.isOnScreen(".op-all-metadata-column", 1)) {
                            let containerHeight = o_browse.metadataSelectorMenuContainerHeight();
                            let containerTop = $(".op-all-metadata-column").offset().top;
                            let containerBottom = containerHeight + containerTop;
                            let elementTop = lastElement.offset().top;
                            let elementHeight = lastElement.outerHeight();
                            let newScrollPosition = $(".op-all-metadata-column").scrollTop() + (elementTop + elementHeight - containerBottom);
                            $(".op-all-metadata-column").scrollTop(newScrollPosition);
                        }
                    }
                }
            });
        });

        let selectedMetadataObserver = new MutationObserver(function(mutationsList) {
            let lastMutationIdx = mutationsList.length - 1;
            mutationsList.forEach((mutation, idx) => {
                if (idx === lastMutationIdx) {
                    if (mutation.target.classList.value.match(/ui-sortable/)) {
                        // Note we call the original version here, not the debounced
                        // version, because we need the PS to be visible instantly in
                        // order for scrollTop to work below.
                        o_browse.adjustSelectedMetadataPS();
                        // if the new item appears below the viewable area, move the scrollbar
                        let lastElement = $(mutation.target).children().last();
                        if (!lastElement.isOnScreen(".op-selected-metadata-column", 1)) {
                            let containerHeight = o_browse.selectedMetadataContainerHeight();
                            let containerTop = $(".op-selected-metadata-column").offset().top;
                            let containerBottom = containerHeight + containerTop;
                            let elementTop = lastElement.offset().top;
                            let elementHeight = lastElement.outerHeight();
                            let newScrollPosition = $(".op-selected-metadata-column").scrollTop() + (elementTop + elementHeight - containerBottom);
                            $(".op-selected-metadata-column").scrollTop(newScrollPosition);
                        }
                    }
                }
            });
        });

        // ps in browse dialog
        let browseDialogObserver = new MutationObserver(function(mutationsList) {
            adjustBrowseDialogPS();
        });

        // ps in gallery view
        let galleryViewObserver = new MutationObserver(function(mutationsList) {
            adjustBrowseHeight();
        });

        // ps in table view
        let tableViewObserver = new MutationObserver(function(mutationsList) {
            adjustTableSize();
        });

        // update ps when switching between gallery and table view
        let switchGalleryAndTableObserver = new MutationObserver(function(mutationsList) {
            adjustBrowseHeight();
            adjustTableSize();
        });

        // target node: target element that MutationObserver is observing, need to be a node
        let searchTab = $("#search")[0];
        let browseTab = $("#browse")[0];
        let cartTab = $("#cart")[0];
        let searchSidebar = $("#sidebar")[0];
        let searchWidget = $("#op-search-widgets")[0];
        let helpPanel = $("#op-help-panel")[0];
        let metadataSelector = $("#op-metadata-selector")[0];
        let metadataSelectorContents = $("#op-metadata-selector-contents")[0];
        let browseDialogModal = $("#galleryView.modal")[0];
        let galleryView = $(".gallery")[0];
        let tableView = $(".op-data-table")[0];
        let switchGalleryAndTable = $(".op-browse-view")[0];

        // Note:
        // The reason of observing sidebar and widdget content element (ps sibling) in search page instead of observing the whole page (html structure) is because:
        /* We want to update ps (attribute changes) in observer callback function.
        If the target node (ex: #sidebar-container, #widget-container, or #app) has a child ps element which is updating, callback function will be triggered again due to another detection of attributes change from that ps update.
        It will end up being a non-stop call of callback function.
        By observing each content element (ps silbling), ps update will not trigger callback function since ps element is not a child element of target node (content element), and this will prevent that non-stop call of callback function. */
        // Watch for changes:
        // update ps when switching tabs
        switchTabObserver.observe(searchTab, switchTabObserverConfig);
        switchTabObserver.observe(browseTab, switchTabObserverConfig);
        switchTabObserver.observe(cartTab, switchTabObserverConfig);
        // update ps in search page
        searchSidebarObserver.observe(searchSidebar, generalObserverConfig);
        searchWidgetObserver.observe(searchWidget, generalObserverConfig);
        // update ps in cart page, including both o_cart.cartGalleryScrollbar and o_cart.downloadOptionsScrollbar
        cartObserver.observe(cartTab, childListObserverConfig);
        // update ps in help panel
        helpPanelObserver.observe(helpPanel, attrObserverConfig);
        // update ps when select metadata modal open/close,
        metadataSelectorObserver.observe(metadataSelector, {attributes: true});
        // udpate ps when select metadata menu expand/collapse
        metadataSelectorMenuObserver.observe(metadataSelectorContents, attrObserverConfig);
        // update ps when selected metadata are added/removed
        selectedMetadataObserver.observe(metadataSelectorContents, childListObserverConfig);
        // update ps when browse dialog open/close
        browseDialogObserver.observe(browseDialogModal, {attributes: true});
        // udpate ps in browse gallery view
        galleryViewObserver.observe(galleryView, generalObserverConfig);
        // update ps in browse table view
        tableViewObserver.observe(tableView, generalObserverConfig);
        // update ps when switching between gallery and table view
        switchGalleryAndTableObserver.observe(switchGalleryAndTable, attrObserverConfig);
    },
};
