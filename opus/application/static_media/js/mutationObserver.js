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

        let adjustSearchSideBarHeight = _.debounce(o_search.adjustSearchSideBarHeight, 200);
        let adjustSearchWidgetHeight = _.debounce(o_search.adjustSearchHeight, 200);
        let adjustSearchHeight = _.debounce(o_search.adjustSearchHeight, 200);
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
            adjustSearchHeight();
            adjustBrowseHeight();
            adjustTableSize();
            adjustProductInfoHeight();
        });

        // ps in search sidebar
        let searchSidebarObserver = new MutationObserver(function(mutationsList) {
            let lastMutationIdx = mutationsList.length - 1;
            mutationsList.forEach((mutation, idx) => {
                if (mutation.type === "childList") {
                    // update ps when there is any children added/removed
                    adjustSearchSideBarHeight();
                } else if (mutation.type === "attributes") {
                    // at the last mutation
                    if (idx === lastMutationIdx) {
                        if (mutation.target.classList.value.match(/collapse/)) {
                            // If there is a collapse/expand happened (attribute changes), we only update ps at the last mutation when the animation finishes and class/style are finalized
                            adjustSearchSideBarHeight();
                        } else if (mutation.target.classList.value.match(/spinner/)) {
                            // If new submenu is added but spinner is still running, we update ps after spinner is done
                            adjustSearchSideBarHeight();
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
                    adjustSearchWidgetHeight();
                } else if (mutation.type === "attributes") {
                    // at the last mutation
                    if (idx === lastMutationIdx) {
                        if (mutation.target.classList.value.match(/collapse/)) {
                            // If there is a collapse/expand happened (attribute changes), we only update ps when the animation finishes and class/style are finalized
                            adjustSearchWidgetHeight();
                        } else if (mutation.target.classList.value.match(/spinner/)) {
                            // If new widget is added but spinner is still spinning, we update ps after spinner is done
                            adjustSearchWidgetHeight();
                        } else if (mutation.target.classList.value.match(/mult_group/)) {
                            // If new mult_group is open inside widgets, we update ps
                            adjustSearchWidgetHeight();
                        }
                    }
                }
            });
        });

        // ps in cart page
        let cartObserver = new MutationObserver(function(mutationsList) {
                // in cart page, we only need to detect element change. We don't need to worry about attribute change (no expanding/collapsing event). Whenever there is an element added/removed in cart page, o_cart.cartGalleryScrollbar and o_cart.downloadOptionsScrollbar are updated.
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
            mutationsList.forEach((mutation, idx) => {
                adjustMetadataSelectorMenuPS();
                adjustSelectedMetadataPS();
            });
        });

        let metadataSelectorMenuObserver = new MutationObserver(function(mutationsList) {
            let lastMutationIdx = mutationsList.length - 1;
            mutationsList.forEach((mutation, idx) => {
                if (idx === lastMutationIdx) {
                    if (mutation.target.classList.value.match(/submenu.collapse/)) {
                        adjustMetadataSelectorMenuPS();
                    }
                }
            });
        });

        let selectedMetadataObserver = new MutationObserver(function(mutationsList) {
            let lastMutationIdx = mutationsList.length - 1;
            mutationsList.forEach((mutation, idx) => {
                if (idx === lastMutationIdx) {
                    if (mutation.target.classList.value.match(/ui-sortable/)) {
                        adjustSelectedMetadataPS();
                    }
                }
            });
        });

        // ps in browse dialog
        let browseDialogObserver = new MutationObserver(function(mutationsList) {
            let lastMutationIdx = mutationsList.length - 1;
            mutationsList.forEach((mutation, idx) => {
                if (idx === lastMutationIdx) {
                    adjustBrowseDialogPS();
                }
            });
        });

        // ps in gallery view
        let galleryViewObserver = new MutationObserver(function(mutationsList) {
            let lastMutationIdx = mutationsList.length - 1;
            mutationsList.forEach((mutation, idx) => {
                if (idx === lastMutationIdx) {
                    adjustBrowseHeight();
                }
            });
        });

        // ps in table view
        let tableViewObserver = new MutationObserver(function(mutationsList) {
            let lastMutationIdx = mutationsList.length - 1;
            mutationsList.forEach((mutation, idx) => {
                if (idx === lastMutationIdx) {
                    adjustTableSize();
                }
            });
        });

        // target node: target element that MutationObserver is observing, need to be a node
        let searchTab = $("#search")[0];
        let browseTab = $("#browse")[0];
        let cartTab = $("#cart")[0];
        let searchSidebar = $("#sidebar")[0];
        let searchWidget = $("#op-search-widgets")[0];
        let helpPanel = $("#op-help-panel")[0];
        let metadataSelector = $("#metadataSelector")[0];
        let metadataSelectorContents = $("#metadataSelectorContents")[0];
        let browseDialogModal = $("#galleryView.modal")[0];
        let galleryView = $(".op-gallery-view")[0];
        let tableView = $("#dataTable")[0];

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
    },
};
