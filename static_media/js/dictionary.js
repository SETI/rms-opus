String.replacei = String.prototype.replacei = function (rep, rby) {
    var pos = this.toLowerCase().indexOf(rep.toLowerCase());
    return pos == -1 ? this : this.substr(0, pos) + rby + this.substr(pos + rep.length);
};

function removeSpecialChars(str) {
  var html = $.parseHTML(str); //we have to double munge it to get rid of tags since we start  with escape chars
  html = $.parseHTML($(html).text());
  var text = $(html).text();
  return text;
}

function postContents(response, searchText) {
  var html = "";
  definition = removeSpecialChars(response.definition)
  if (searchText != undefined) {
    definition = definition.replacei(searchText, "<mark class='search'>"+searchText+"</mark>")
  }
  html += "<div class='context'>" + response.context__description + "</div></br>";
  html += "<div class='description'>" + definition + "</div></br>";
  html += "<div class='importDate'>" + response.term__import_date + "</div></br>";
  return html;
}

function buildDefinitionListHTML(response, searchText) {
  var length = response.length;
  var html = "<div class='definitionList'>";
  if (length > 0) {
    html += "<ul>";
    for (var index = 0; index < length; index++) {
      var next =index + 1;
      html += "<li>";
      html += "<div class='term'>" + response[index].term__term_nice + "</div></br>";
      // this should actually be a while loop...
      if (next < length && (response[index].term__term_nice == response[next].term__term_nice)) {
        html += "<ul>";
        html += "<li>"+postContents(response[index], searchText) + "</li>";
        index++;
        html += "<li>"+postContents(response[index], searchText) + "</li></ul>";
      } else {
        html += postContents(response[index], searchText);
      }
      html += "</li>";
    }
    html += "</ul>";
  } else {
    html += "No results found.";
  }
  html += "</div>";
  return html;
}

function searchDictionary(searchText, thepanel) {
  var url = "/dictionary/search.json/" + searchText;
  $.getJSON(url, function(response) {
      var html = buildDefinitionListHTML(response, searchText)
      thepanel.html(html);
  });
}

$( function() {
  var currentElement = "";
  $( ".alphabetlist").click(function( event ){
    var targetElement = 'def-'+event.currentTarget.id;
    if (currentElement != targetElement) {
      if (currentElement != "") {
        $("#"+currentElement).hide();
      }
      currentElement = targetElement;
    }
    if ($("#"+targetElement).length == 0) {
      $("#dictionaryContainer").append("<div id='"+targetElement+"' class='dictionaryContent'>Loading... please wait.</div>")
      var url = "/dictionary/list.json/" + event.currentTarget.id + "/";
      $.getJSON(url, function(response) {
        var html = buildDefinitionListHTML(response)
        $("#"+targetElement).html(html);
      });
    }
    $("#"+targetElement).show();
  });
  $( "#searchbox" ).submit(function( event ) {
    //val searchText = $("input[name=q]").val();
    var searchText = $("input[name=q]").val();
    if (searchText != "") {
      var thepanel = $(".cd-panel-content");
      searchDictionary(searchText, thepanel);
      $("#searchTitle").html("Searching for: '"+searchText+"'");
      $('.cd-panel').addClass('is-visible');
    }
    event.preventDefault();
  });
  //close the search panel
  $('.cd-panel').on('click', function (event) {
    if ($(event.target).is('.cd-panel') || $(event.target).is('.cd-panel-close')) {
      $('.cd-panel').removeClass('is-visible');
      event.preventDefault();
    }
  });
});
