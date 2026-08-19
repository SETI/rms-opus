/* jshint esversion: 6 */
/* jshint bitwise: true, curly: true, freeze: true, futurehostile: true */
/* jshint latedef: true, leanswitch: true, noarg: true, nocomma: true */
/* jshint nonbsp: true, nonew: true */
/* jshint varstmt: true */
/* jshint multistr: true */
/* globals $ */

String.replacei = Object.defineProperty(String.prototype, "replacei", {
  value: function(rep, rby) {
    let pos = this.toLowerCase().indexOf(rep.toLowerCase());
    return pos == -1 ? this : this.substr(0, pos) + rby + this.substr(pos + rep.length);
  }
});

function removeSpecialChars(str) {
  let html = $.parseHTML(str); //we have to double munge it to get rid of tags since we start  with escape chars
  html = $.parseHTML($(html).text());
  let text = $(html).text();
  return text;
}

function postContents(response, searchText) {
  let html = "";
  let definition = removeSpecialChars(response.definition);
  if (searchText != undefined) {
    definition = definition.replacei(searchText, "<mark class='search'>"+searchText+"</mark>");
  }
  let context = (response.context__description == undefined ? response.context: response.context__description);
  html += "<div class='context'>" + context + "</div></br>";
  html += "<div class='description'>" + definition + "</div></br>";
  let timestamp = (response.term__timestamp == undefined ? response.timestamp: response.term__timestamp);
  html += "<div class='importDate'>" + timestamp + "</div></br>";
  return html;
}

function buildDefinitionListHTML(response, searchText) {
  let length = response.length;
  let html = "<div class='definitionList'>";
  if (length > 0) {
    html += "<ul>";
    for (let index = 0; index < length; index++) {
      let next =index + 1;
      let term = (response[index].term__term_nice === undefined ? response[index].term : response[index].term__term_nice);
      let term_next = (next < length && (response[next].term__term_nice === undefined ? response[next].term : response[next].term__term_nice));

      html += "<li>";
      html += "<div class='term'>" + term.replace(/:/g, ": ").replace(/_/g, " ").toTitleCase() + "</div></br>";
      // this should actually be a while loop...term.replace(/_/g, ". ").
      if (next < length && (term == term_next)) {
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
  let url = "/__dictionary/search.json?term=" + searchText;
  $.getJSON(url, function(response) {
      let html = buildDefinitionListHTML(response, searchText);
      thepanel.html(html);
  });
}

$( function() {
  let currentElement = "";
  $( ".alphabetlist").click(function(event) {
    let targetElement = 'def-'+event.currentTarget.id;
    if (currentElement != targetElement) {
      if (currentElement != "") {
        $("#"+currentElement).hide();
      }
      currentElement = targetElement;
    }
    if ($("#"+targetElement).length == 0) {
      $("#dictionaryContainer").append("<div id='"+targetElement+"' class='dictionaryContent'>Loading... please wait.</div>");
      let url = "/__dictionary/list.json?alpha=" + event.currentTarget.id;
      $.getJSON(url, function(response) {
        let html = buildDefinitionListHTML(response);
        $("#"+targetElement).html(html);
      });
    }
    $("#"+targetElement).show();
  });
  $( "#searchbox" ).submit(function(event) {
    //val searchText = $("input[name=q]").val();
    let searchText = $("input[name=q]").val();
    if (searchText != "") {
      let thepanel = $(".cd-panel-content");
      searchDictionary(searchText, thepanel);
      $("#searchTitle").html("Searching for: '"+searchText+"'");
      $('.cd-panel').addClass('is-visible');
    }
    event.preventDefault();
  });
  //close the search panel
  $('.cd-panel').on('click', function(event) {
    if ($(event.target).is('.cd-panel') || $(event.target).is('.cd-panel-close')) {
      $('.cd-panel').removeClass('is-visible');
      event.preventDefault();
    }
  });
});
