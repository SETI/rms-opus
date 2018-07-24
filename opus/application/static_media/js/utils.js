
var o_utils = {           
    
    /**
     *
     *  some utils
     *
     **/
    
    
    // this is for comparing selections to last_selections
    // expects an object whose values are all arrays
    areObjectsEqual: function(obj1, obj2) { 
        
        boo = (JSON.stringify(obj1) == JSON.stringify(obj2)); 
        return boo;
        
    },
    
    // num is an int
    addCommas: function(num){ 
          return num.toString().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,");
    },   
    
                       
    
};