/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $ */

/* jshint varstmt: false */
var o_utils = {
/* jshint varstmt: true */

    /**
     *
     *  some utils
     *
     **/
    areObjectsEqual: function(obj1, obj2) {
        /**
         * This is for comparing selections or lastSelections
         * Expects objects whose values are all arrays.
         * NOTE: We don't want to use JSON.stringify to directly compare
         * two objects because the order of keys in the object will matter
         * in that case.
         **/
        if (Object.keys(obj1).length !== Object.keys(obj2).length) {
            return false;
        }
        for (const key in obj1) {
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
    },

    enableUserInteraction: function(e) {
        $("body").removeClass("op-prevent-pointer-events");
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
    let bottom = top + scope.height();
    let elementHeight = target.outerHeight();
    let offset = elementHeight * slop;   // allow part of the object to be off screen
    let elementTop = target.offset().top;
    // hack to take care of table header height
    if (this.is("tr")) {
        top += $("th").outerHeight();
    }

    return (elementTop + offset <= bottom) && (elementTop >= top);
};
