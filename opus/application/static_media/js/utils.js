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
