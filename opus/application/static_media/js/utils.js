/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */

/* jshint varstmt: false */
var o_utils = {
/* jshint varstmt: true */

    /**
     *
     *  some utils
     *
     **/


    // this is for comparing selections to lastSelections
    // expects an object whose values are all arrays
    areObjectsEqual: function(obj1, obj2) {
      // perhaps not fabulous; see https://stackoverflow.com/questions/3791516/comparing-native-javascript-objects-with-jquery
        return (JSON.stringify(obj1) == JSON.stringify(obj2));

    },

    // num is an int
    addCommas: function(num) {
          return num.toString().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,");
    },



};



/**
 * returns true if an element is visible, with decent performance
 * @param [scope] scope of the render-window instance; 
 * @returns {boolean}
 */
$.fn.isOnScreen = function(scope){
    let element = this;
    if (!element || !scope) {
        return;
    }
    let target = $(element);
    if (target.is(':visible') === false) {
        return false;
    }
    scope = $(scope);
    let top = scope.offset().top;
    let bottom = top + scope.height();
    let elementTop = target.offset().top;
    let elementBottom = elementTop + target.outerHeight();

    return ((elementBottom <= bottom) && (elementTop >= top));
};
