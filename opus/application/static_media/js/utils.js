/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals opus, $ */

/* jshint varstmt: false */
var o_utils = {
/* jshint varstmt: true */

    /**
     *
     *  some utils
     *
     **/
    ignoreArrowKeys: false,

    areObjectsEqual: function(obj1, obj2) {
        /**
         * This is for comparing objects whose values are all arrays.
         * NOTE: We don't want to use JSON.stringify to directly compare
         * two objects because the order of keys in the object will matter
         * in that case.
         **/
        if (Object.keys(obj1).length !== Object.keys(obj2).length) {
            return false;
        }
        for (const key of Object.keys(obj1)) {
            if (!(key in obj2)) {
                return false;
            } else {
                // expect the array (value) of the same key to be the same for both objects
                if (JSON.stringify(obj1[key]) !== JSON.stringify(obj2[key])) {
                    return false;
                }
            }
        }
        return true;
    },

    // num is an int
    addCommas: function(num) {
          return num.toString().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,");
    },

    // account for FP non-integer inprecision math in javascript
    floor: function(num) {
        return Math.floor(num + 0.0000001);
    },

    ceil: function(num) {
        return Math.ceil(num - 0.0000001);
    },

    // these functions are used to prevent the user from moving off the
    // browse/cart tab which can cause a race condition
    disableUserInteraction: function(e) {
        $("body").addClass("op-prevent-pointer-events");
        $(".modal-content").addClass("op-prevent-pointer-events");
        o_utils.ignoreArrowKeys = true;
    },

    enableUserInteraction: function(e) {
        $("body").removeClass("op-prevent-pointer-events");
        $(".modal-content").removeClass("op-prevent-pointer-events");
        o_utils.ignoreArrowKeys = false;
    },

    // Break apart the window.location and return just the protocol and hostname
    getWindowURLPrefix: function() {
        let urlPrefix = `${window.location.protocol}//${window.location.hostname}`;
        if (window.location.port) {
            urlPrefix += `:${window.location.port}`;
        }
        return urlPrefix;
    },

    getSlugOrDataWithoutCounter: function(slugOrData) {
        /**
         * Takes in a slugOrData from input's name attribute and if there are
         * multiple inputs, return the version without trailing counter.
         */
        let slugNoCounterMatchObj = slugOrData.match(/(.*)_[0-9]+$/);
        return (slugNoCounterMatchObj ? slugNoCounterMatchObj[1] : slugOrData);
    },

    getSlugOrDataTrailingCounterStr: function(slugOrData) {
        /**
         * Takes in a slugOrData from input's name attribute and if there are
         * multiple inputs, return the trailing counter, else return an
         * empty string.
         */
        let trailingCounterMatchObj = slugOrData.match(/_([0-9]+)$/);
        return (trailingCounterMatchObj ? trailingCounterMatchObj[1] : "");
    },

    convertToTrailingCounterStr: function(num, numOfDigits=2) {
        /**
         * Takes in a number and left zero pad the give number to the
         * specified number of digits. By default, we want a 2-digit string.
         * 1 -> "01"
         * 2 -> "02"
         * ...
         * 9 -> "09"
         * 10 -> "10"
         */
        return ("0" + num).slice(-numOfDigits);
    },

    // Deep clone an object with arrays as values.
    // NOTE: the following method won't deep clone values if they are functions
    // or inner objects. In our case, we only have arrays as values.
    deepCloneObj: function(obj) {
        return JSON.parse(JSON.stringify(obj));
    },

    // This function is patterned after slug_name_for_sfc_target in import_util.py.
    getSurfacegeoTargetSlug: function(target) {
        /**
         * Take in a surface geo target pretty name and return a slug name
         * for the target.
         */
        let slugName = target.toLowerCase();
        // remove all "_", "/", and " "
        slugName = slugName.replace(/_/g, "").replace(/\//g, "").replace(/ /g, "");
        return slugName;
    },

    // Get the x & y coordinate of the current cursor when moving mouse in the traget el.
    // Reposition the tooltip based on the cursor location (set in functionPosition callback).
    onMouseMoveHandler: function(e, targetTooltipster) {
        clearTimeout(opus.timer);
        opus.mouseX = e.clientX;
        opus.mouseY = e.clientY;
        opus.timer = setTimeout(function() {
            if (targetTooltipster.length) {
                targetTooltipster.tooltipster("instance").reposition();
            }
        }, opus.tooltipsDelay);
    },

    // Set the position of the preview image tooltip
    setPreviewImageTooltipPosition: function(helper, position) {
        let tooltipWidth = position.size.width;
        let tooltipHeight = position.size.height;
        let offsetToWindow = 5;
        let arrowOffset = 15;
        let windowWidth = helper.geo.window.size.width;
        // make sure the tooltip is not cut off.
        if (opus.mouseY - tooltipHeight - offsetToWindow < 0) {
            position.coord.top = opus.mouseY;
            position.side = "bottom";
        } else {
            position.coord.top = opus.mouseY - tooltipHeight;
            position.side = "top";
        }

        if (opus.mouseX + tooltipWidth + offsetToWindow > windowWidth) {
            position.coord.left = opus.mouseX - tooltipWidth + arrowOffset;
        } else if (opus.mouseX - tooltipWidth - offsetToWindow < 0) {
            position.coord.left = opus.mouseX - arrowOffset;
        } else {
            position.coord.left = opus.mouseX - tooltipWidth/2;
        }

        position.target = opus.mouseX;
        return position;
    },

    // Return the slug without a unit
    getSlugWithoutUnit: function(slug) {
        let idx = slug.indexOf(":");
        slug = idx === -1 ? slug : slug.slice(0, idx);
        return slug;
    }
};

/**
 * returns true if an element is visible
 */
$.fn.isOnScreen = function(scope, slop) {
    if (!this || !scope) {
        return;
    }
    let target = $(this);
    if (target.is(':visible') === false) {
        return false;
    }
    scope = $(scope);
    let top = scope.offset().top;
    let positionTop = scope.position().top;
    let bottom = (top + scope.height()) - positionTop;
    let elementHeight = target.outerHeight();
    let offset = elementHeight * slop;   // allow part of the object to be off screen
    let elementTop = target.offset().top;
    let sidesInBounds = true;

    // hack to take care of table header height
    if (this.is("tr")) {
        top += $("th").outerHeight();
        // For a table item, the bottom border will be the top of the footer.
        bottom = $(".footer").offset().top;
        // Make sure highlighted table item is fully displayed.
        offset = elementHeight;
    } else {
        // check left and right for modals
        let left = scope.offset().left;
        let elementLeft = target.offset().left;
        let right = left + scope.outerWidth();
        let elementRight = elementLeft + target.outerWidth();

        sidesInBounds = (elementLeft > left && elementRight < right);
    }

    return ((elementTop + offset <= bottom) && (elementTop >= top)) && sidesInBounds;
};
