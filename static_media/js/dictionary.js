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
  if (length > 0) {
    var html = "<ul>";
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
    var html = "No results found."
  }
  return html
}

function searchDictionary(searchText, thepanel) {
  var url = "/dictionary/search.json/" + searchText;
  $.getJSON(url, function(response) {
      var html = buildDefinitionListHTML(response, searchText)
      thepanel.html(html);
  });
}

function retrieveDefinition(alpha, thepanel) {
  var url = "/dictionary/list.json/" + alpha + "/";
  $.getJSON(url, function(response) {
    var html = buildDefinitionListHTML(response)
    thepanel.html(html);
  });
}

$( function() {
  $( "#accordion" ).accordion({
    heightStyle: "content",
    header: "h3",
    collapsible: true,
    active: false,
    animate: 200,
    activate: function( event, ui ) {
      var id = ui.newHeader.attr("id");
      var panel = ui.newPanel;
      if (id !== undefined && ui.newHeader.attr("stuffed") == undefined) {
        retrieveDefinition(id, panel);
        ui.newHeader.attr("stuffed", true);
      }
    }
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
