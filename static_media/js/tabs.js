var o_tabs = {   
    
    /**
     *
     *  all about the tab handling - does not include tab content
     *
     **/
    
    initTabs: function() {
        
        var tab = 0;    
        if (opus.prefs.view=='browse') tab=1;
        if (opus.prefs.view=='detail') tab=2; 
        if (opus.prefs.view=='collections') tab=3; 
          
        var $tabs = $("#tabs").tabs({
           selected: tab,
           // closable: true,
           
           // makes it so a newly added tab is immediately selected
           add: function(event, ui) {                
               // $tabs.tabs('select', '#' + ui.panel.id); 
               $tabs.tabs('select', '#' + $(ui.panel).attr("id"));
           },
           
           select: function(event, ui) {
               // adding the currently selected tab to the hash
               var view = $(ui.panel).attr("id"); 
               opus.prefs.view = view;
               o_hash.updateHash();
               
               // results tab behaviors             
               if (opus.prefs.view=='browse') {    
                   opus.browse_tab_click = true;
                   if (opus.browse_empty) o_browse.getBrowseTab();     
               }    
               if (opus.prefs.view == 'search') {   
                   o_search.getSearchTab();      
                   window.scrollTo(0,0);
               }    
               if (opus.prefs.view == 'collections') {
                   o_collections.getCollectionsTab();                 
                   window.scrollTo(0,0); 
               } 
               if (opus.prefs.view == 'detail') {
                   window.scrollTo(0,0); 
               }   
           }, 
           
           error:function (err){  
           }
           
        }); 
        
        if ($tabs) {   
        } else {
        }
        
                            
        
    },  

/**    
    //  ids removes the close button from the uncloseable tabs
    // tabs = [] of tab ids like: ['#search_tab','#browse_tab']
    removeCloseButtons: function(tabs) {
        for (k in tabs) {
            $(tabs[k] + ' a:last').remove();
        }    
    },        

   
**/     
    
    
};