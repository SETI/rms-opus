/* Cool Javascript Find on this Page
Ver 5.3
Written by Jeff Baker on September, 8, 2007.
Copyright 2014 by Jeff Baker -
Version 5.0 created 7/16/2014
Updated 7/2/2019 ver 5.4b
http://www.seabreezecomputers.com/tips/find.htm
Paste the following javascript call in your HTML web page where
you want a button called "Find on this Page...":

<script type="text/javascript" language="JavaScript"
src="find5.js">
</script>

When you click on the button a floating DIV will pop up
that will have a text box for users to enter in the text they
want to find on the page.

WARNING: If you want to place a second "Find on this page..."
button somewhere on the same page then use the code below for
the second button, otherwise firefox and netscape will not
display the text that users type in and it will not find
text correctly because there will be two different text input
boxes with the same name:

<input type="button" value="Find on this page..."
onclick="show();">

*/

/* You may edit the following variables */
var enable_site_search = 1; // 0 = Don't enable; 1 = Enable site search along with page search
var find_window_background = "white"; // the color of the pop-up window
var find_window_border = "blue"; // the border color of pop-up window
var find_text_color = "black"; // the color of the text in window
var find_title_color = "white"; // color of window title text
var find_window_width = 245; // width of window
//var find_window_height = 85; // height of window - Version 5.3f - No Longer Using
var find_root_node = null; // Leave as null to search entire doc or put id of div to search (ex: 'content'). Ver 5.0a - 7/18/2014
/* Do not edit the variables below this line */

// Simple drag object to hold all the variables for dragging
var drag = {mousex:0,mousey:0,tempx:'',tempy:'',isdrag:false, drag_obj:null, drag_obj_x:0, drag_obj_y:0};

var find_timer = 0;  // used for timer to move window in IE when scrolling

// Create highlights array to hold each new span element
var highlights = [];

// Which find are we currently highlighting
var find_pointer = -1;

var find_text = ''; // Global variable of searched for text

var found_highlight_rule = 0; // whether there is a highlight css rule
var found_selected_rule = 0; // whether there is a selected css rule

document.onmousedown = MouseDown;
document.onmousemove = MouseMove;
document.onmouseup = MouseUp;

document.ontouchstart = MouseDown;
document.ontouchmove = MouseMove;
document.ontouchend = MouseUp;


function highlight(word, node)
{
	if (!node)
		node = document.body;

	//var re = new RegExp(word, "i"); // regular expression of the search term // Ver 5.3c - Not using regular expressions search now

	for (node=node.firstChild; node; node=node.nextSibling)
	{
		//console.log(node.nodeName);
		if (node.nodeType == 3) // text node
		{
			var n = node;
			//console.log(n.nodeValue);
			var match_pos = 0;
			//for (match_pos; match_pos > -1; n=after)
			{
				//match_pos = n.nodeValue.search(re); // Ver 5.3b - Now NOT using regular expression because couldn't search for $ or ^
				match_pos = n.nodeValue.toLowerCase().indexOf(word.toLowerCase()); // Ver 5.3b - Using toLowerCase().indexOf instead

				if (match_pos > -1) // if we found a match
				{
					var before = n.nodeValue.substr(0, match_pos); // split into a part before the match
					var middle = n.nodeValue.substr(match_pos, word.length); // the matched word to preserve case
					//var after = n.splitText(match_pos+word.length);
					var after = document.createTextNode(n.nodeValue.substr(match_pos+word.length)); // and the part after the match
					var highlight_span = document.createElement("span"); // create a span in the middle
			        if (found_highlight_rule == 1)
						highlight_span.className = "highlight";
					else
						highlight_span.style.backgroundColor = "yellow";

					highlight_span.appendChild(document.createTextNode(middle)); // insert word as textNode in new span
					n.nodeValue = before; // Turn node data into before
					n.parentNode.insertBefore(after, n.nextSibling); // insert after
		            n.parentNode.insertBefore(highlight_span, n.nextSibling); // insert new span
		           	highlights.push(highlight_span); // add new span to highlights array
		           	highlight_span.id = "highlight_span"+highlights.length;
					node=node.nextSibling; // Advance to next node or we get stuck in a loop because we created a span (child)
				}
			}
		}
		else // if not text node then it must be another element
		{
			// nodeType 1 = element
			if (node.nodeType == 1 && node.nodeName.match(/textarea|input/i) && node.type.match(/textarea|text|number|search|email|url|tel/i) && !getStyle(node, "display").match(/none/i))
				textarea2pre(node);
			else
			{
			if (node.nodeType == 1 && !getStyle(node, "visibility").match(/hidden/i)) // Dont search in hidden elements
			if (node.nodeType == 1 && !getStyle(node, "display").match(/none/i)) // Dont search in display:none elements
			highlight(word, node);
			}
		}
	}


} // end function highlight(word, node)


function unhighlight()
{
	for (var i = 0; i < highlights.length; i++)
	{

		var the_text_node = highlights[i].firstChild; // firstChild is the textnode in the highlighted span

		var parent_node = highlights[i].parentNode; // the parent element of the highlighted span

		// First replace each span with its text node nodeValue
		if (highlights[i].parentNode)
		{
			highlights[i].parentNode.replaceChild(the_text_node, highlights[i]);
			if (i == find_pointer) selectElementContents(the_text_node); // ver 5.1 - 10/17/2014 - select current find
			parent_node.normalize(); // The normalize() method removes empty Text nodes, and joins adjacent Text nodes in an element
			normalize(parent_node);	// Ver 5.2 - 3/10/2015 - normalize() is incorrect in IE. It will combine text nodes but may leave empty text nodes. So added normalize(node) function below
		}
	}
	// Now reset highlights array
	highlights = [];
	find_pointer = -1; // ver 5.1 - 10/17/2014
} // end function unhighlight()


function normalize(node) {
//http://stackoverflow.com/questions/22337498/why-does-ie11-handle-node-normalize-incorrectly-for-the-minus-symbol
  if (!node) { return; }
  if (node.nodeType == 3) {
    while (node.nextSibling && node.nextSibling.nodeType == 3) {
      node.nodeValue += node.nextSibling.nodeValue;
      node.parentNode.removeChild(node.nextSibling);
    }
  } else {
    normalize(node.firstChild);
  }
  normalize(node.nextSibling);
}


function findit()
{
	// put the value of the textbox in string
	var string = document.getElementById('fwtext').value;

	// Version 5.4 - Site search
	if (enable_site_search && document.getElementById("find_site_search").checked) {
		var website = window.location.hostname; // Or replace with your website. Ex: example.com
		var url = "https://www.google.com/search?q=site%3A"+website+"+"+string;
		window.open(url, "coolfind");
		return;
	}

	// 8-9-2010 Turn DIV to hidden just while searching so doesn't find the text in the window
	findwindow.style.visibility = 'hidden';
	//findwindow.style.display = 'none';

	// if the text has not been changed and we have previous finds
	if (find_text.toLowerCase() == document.getElementById('fwtext').value.toLowerCase() &&
		find_pointer >= 0)
	{
		findnext(); // Find the next occurrence
	}
	else
	{
		unhighlight(); // Remove highlights of any previous finds

		if (string == '') // if empty string
		{
			find_msg.innerHTML = "";
			findwindow.style.visibility = 'visible';
			return;
		}

		find_text = string;

		// Ver 5.0a - 7/18/2014. Next four lines because find_root_node won't exist until doc loads
		if (find_root_node != null)
			var node = document.getElementById(find_root_node);
		else
			var node = null;

		highlight(string, node); // highlight all occurrences of search string

		if (highlights.length > 0) // if we found occurences
		{
			find_pointer = -1;
			findnext(); // Find first occurrence
		}
		else
		{
			find_msg.innerHTML = "&nbsp;<b>0 of 0</b>"; // ver 5.1 - 10/17/2014 - changed from "Not Found"
			find_pointer = -1;
		}
	}
	findwindow.style.visibility = 'visible';
	//findwindow.style.display = 'block';

}  // end function findit()


function findnext()
{
	var current_find;

	if (find_pointer != -1) // if not first find
	{
		current_find = highlights[find_pointer];

		// Turn current find back to yellow
		if (found_highlight_rule == 1)
			current_find.className = "highlight";
		else
			current_find.style.backgroundColor = "yellow";
	}

	find_pointer++;

	if (find_pointer >= highlights.length) // if we reached the end
			find_pointer = 0; // go back to first find

	var display_find = find_pointer+1;

	find_msg.innerHTML = display_find+" of "+highlights.length;

	current_find = highlights[find_pointer];

	// Turn selected find orange or add .find_selected css class to it
	if (found_selected_rule == 1)
			current_find.className = "find_selected";
		else
			current_find.style.backgroundColor = "orange";

	//highlights[find_pointer].scrollIntoView(); // Scroll to selected element
	scrollToPosition(highlights[find_pointer]);

} // end findnext()



// This function is to find backwards by pressing the Prev button
function findprev()
{
	var current_find;

	if (highlights.length < 1) return;

	if (find_pointer != -1) // if not first find
	{
		current_find = highlights[find_pointer];

		// Turn current find back to yellow
		if (found_highlight_rule == 1)
			current_find.className = "highlight";
		else
			current_find.style.backgroundColor = "yellow";
	}

	find_pointer--;

	if (find_pointer < 0) // if we reached the beginning
			find_pointer = highlights.length-1; // go back to last find

	var display_find = find_pointer+1;

	find_msg.innerHTML = display_find+" of "+highlights.length;

	current_find = highlights[find_pointer];

	// Turn selected find orange or add .find_selected css class to it
	if (found_selected_rule == 1)
			current_find.className = "find_selected";
		else
			current_find.style.backgroundColor = "orange";

	//highlights[find_pointer].scrollIntoView(); // Scroll to selected element
	scrollToPosition(highlights[find_pointer]);

} // end findprev()


// This function looks for the ENTER key (13)
// while the find window is open, so that if the user
// presses ENTER it will do the find next
function checkkey(e)
{
	var keycode;
	if (window.event)  // if ie
		keycode = window.event.keyCode;
	else // if Firefox or Netscape
		keycode = e.which;

	//find_msg.innerHTML = keycode;

	if (keycode == 13) // if ENTER key
	{
		// ver 5.1 - 10/17/2014 - Blur on search so keyboard closes on iphone and android
		if (window.event && event.srcElement.id.match(/fwtext/i)) event.srcElement.blur();
		else if (e && e.target.id.match(/fwtext/i)) e.target.blur();
		findit(); // call findit() function (like pressing NEXT)
	}
	else if (keycode == 27) // ESC key // Ver 5.1 - 10/17/2014
	{
		hide(); // Close find window on escape key pressed
	}
} // end function checkkey()


// This function makes the findwindow DIV visible
// so they can type in what they want to search for
function show()
{
	// Object to hold textbox so we can focus on it
	// so user can just start typing after "find" button
	// is clicked
	var textbox = document.getElementById('fwtext');

	// Make the find window visible
	findwindow.style.visibility = 'visible';
	//fwtext.style.visibility = 'visible';

	// Put cursor focus in the text box
	textbox.focus();
	textbox.select(); // ver 5.1 - 10/17/2014 - Select the text to search for
	textbox.setSelectionRange(0, 9999); // ver. 5.3 - 5/15/2015 - iOS woould not select without this
	// Call timer to move textbox in case they scroll the window
	find_timer = setInterval('move_window();', 500);
	// Setup to look for keypresses while window is open
	document.onkeydown = checkkey;

} // end function show()


// This function makes the findwindow DIV hidden
// for when they click on close
function hide()
{
	unhighlight(); // Remove highlights of any previous finds - ver 5.1 - 10/17/2014
	findwindow.style.visibility = 'hidden';

	// turn off timer to move window on scrolling
	clearTimeout(find_timer);

	// Make document no longer look for enter key
	document.onkeydown = null;

} // end function hide()


// This function resets the txt selection pointer to the
// beginning of the body so that we can search from the
// beginning for the new search string when somebody
// enters new text in the find box
function resettext()
{
	if (find_text.toLowerCase() != document.getElementById('fwtext').value.toLowerCase())
		unhighlight(); // Remove highlights of any previous finds

} // end function resettext()


// This function makes the find window jump back into view
// if they scroll while it is open or if the page automatically
// scrolls when it is hightlighting the next found text
function move_window()
{
	//var findwindow = document.getElementById('findwindow');

	// get current left, top and height of find_window
	var fwtop = parseFloat(findwindow.style.top);
	var fwleft = parseFloat(findwindow.style.left);
	// var fwheight = parseFloat(findwindow.style.height); // Version 5.3f - Was returning NaN in Chrome - changed to below
	var fwheight = parseFloat(findwindow.offsetHeight); // Version 5.3f

	// get current top and bottom position of browser screen
	if (document.documentElement.scrollTop) // Needed if you use doctype loose.htm
		var current_top = document.documentElement.scrollTop;
	else
		var current_top = document.body.scrollTop;

	// ver 2.3c 9/14/2013
	var current_bottom = (window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight) + current_top;

	// get current left and right position of browser
	if (document.documentElement.scrollLeft) // Needed if you use doctype loose.htm
		var current_left = document.documentElement.scrollLeft;
	else
		var current_left = document.body.scrollLeft;

	// ver 2.3c 9/14/2013
	var current_right = (window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth) + current_left;


	//find_msg.innerHTML = current_right + ',' + current_left;

	// Only move window if it is out of the view
	if (fwtop < current_top)
	{
		// move window to current_top
		findwindow.style.top = current_top + 30 +'px';
	}
	else if (fwtop > current_bottom - fwheight)
	{
		// move to current_bottom
		findwindow.style.top = current_bottom - fwheight + 'px';
	}

	// Only move left position if out of view
	if (fwleft < current_left ||
		fwleft > current_right)
	{
		findwindow.style.left = current_left + 'px';
	}

	/* var find_msg = document.getElementById('find_msg');
	find_msg.innerHTML = 'find window: ' + fwtop
		+ ' curr_bottom: ' + current_bottom; */

} // end function move_window()


function MouseDown(event)
{
	drag.tempx = drag.tempy = ''; // For single click on object
	if (!event) event = window.event; // 10/5/2014 - ver 5.0d - for older IE <= 9
	var fobj = event.target || event.srcElement; // The element being clicked on (FF || IE)

	// get current screen scrollTop and ScrollLeft
	var scrollLeft = document.body.scrollLeft || document.documentElement.scrollLeft;
	var scrollTop = document.body.scrollTop || document.documentElement.scrollTop;

	// ver 5.1 - 10/17/2014 - Let users highlight textareas and inputs by not dragging them
	if (typeof fobj.nodeName != "undefined")
	if (fobj.nodeName.toLowerCase() == "input" ||
		fobj.nodeName.toLowerCase() == "textarea")
		return true;

	// If parent or grandparents of obj is a dragme item then make the parent the fobj
	for (fobj; fobj; fobj=fobj.parentNode)
	{
		// 7/30/2014 ver 5.0b
		if (fobj.className)
		if (String(fobj.className).match(/dragme/i))
			break;
	}

	// If parent of obj is a dragme item then make the parent the fobj
	/*if (fobj.parentNode.className)
	if (fobj.parentNode.className.match(/dragme/i))
		fobj = fobj.parentNode;*/
	if (fobj) // 7/30/2014 ver 5.0b
	if (fobj.className.match(/dragme/i)) // Only drag objects that have class="dragme"
	{
		//fobj.style.zIndex = parseInt(getStyle(fobj, "z-index"))+1; // Make sure dragged object is in front
		// ^ ver 5.1 - 10/17/2014 - May have caused IE 8 Invalid Argument


		// If there was a previous object dragged then push it back on the screen
		//if (drag.drag_obj)
		//	drag.drag_obj.style.zIndex = parseInt(getStyle(fobj, "z-index"))-1;
		// ^ ver 5.1 - 10/17/2014 - May have caused IE 8 Invalid Argument
		//if (document.getElementById('find_msg'))
		//	document.getElementById('find_msg').innerHTML = getStyle(fobj, "z-index");

		drag.isdrag = true; // Tell mouseMove we are dragging
		drag.drag_obj = fobj; // Put dragged element into global variable
		drag.drag_obj_x = parseInt(drag.drag_obj.offsetLeft); // get current x of element
		drag.drag_obj_y = parseInt(drag.drag_obj.offsetTop); // get current y of element

		// Add scrollTop and scrollLeft to recorded mouse position
		drag.mousex = event.clientX + scrollLeft;
		drag.mousey = event.clientY + scrollTop;

		/* if touchevents from iphone */
		if (event.type == "touchstart")
		if(event.touches.length == 1)
		{ // Only deal with one finger
		    var touch = event.touches[0]; // Get the information for finger #1
		    var node = touch.target; // Find the node the drag started from (redundant)
		    // node.style.position = "absolute";
		    drag.mousex = touch.pageX; // includes scroll offset
		    drag.mousey = touch.pageY; // includes scroll offset
		}
		return true; // 8/25/2014 version 5.0c (Now all buttons and onclick work on iphone and android)
	}
} // end function MouseDown(event)


function MouseMove(event)
{
	if (drag.isdrag)
	{
		// Use 'event' above because IE only uses event and FF can use anything
		if (!event) event = window.event; // 10/5/2014 - ver 5.0d - for older IE <= 9
		drag.tempx = event.clientX; // record new mouse position x
		drag.tempy = event.clientY; // record new mouse position y

		// get current screen scrollTop and ScrollLeft
		var scrollLeft = document.body.scrollLeft || document.documentElement.scrollLeft;
		var scrollTop = document.body.scrollTop || document.documentElement.scrollTop;


	  	// Add scrollTop and scrollLeft to drag.tempx and drag.tempy
		drag.tempx += scrollLeft;
		drag.tempy += scrollTop;

		drag.drag_obj.style.position = 'absolute';

		/* if touchevents from iphone */
		if (event.type == "touchmove")
		if(event.touches.length == 1)
		{ // Only deal with one finger
		    var touch = event.touches[0]; // Get the information for finger #1
		    var node = touch.target; // Find the node the drag started from
		    // node.style.position = "absolute";
		    drag.tempx = touch.pageX; // includes scroll offset
		    drag.tempy = touch.pageY; // includes scroll offset
		}

		//if (document.getElementById('find_msg'))
		//	document.getElementById('find_msg').innerHTML = drag.tempx+", "+drag.tempy;
		// Dragged element position = old position + new mouse position - old mouse position

		drag.drag_obj.style.left = drag.drag_obj_x + drag.tempx - drag.mousex + "px"; // 7/30/2014 ver 5.0b
		drag.drag_obj.style.top  = drag.drag_obj_y + drag.tempy - drag.mousey + "px"; // 7/30/2014 ver 5.0b
		return false;
	}
} // end function MouseMove(event)



function MouseUp()
{
	if (drag.isdrag == true)
	{
		if (drag.tempx == '' && drag.tempy == '')
		{
			//if (document.getElementById('find_msg'))
			//	document.getElementById('find_msg').innerHTML += " You clicked!";
		}
	}

	drag.isdrag = false;

}


function scrollToPosition(field)
{
   // This function scrolls to the DIV called 'edited'
   // It is called with onload.  'edited' only exists if
   // they just edited a comment or the last comment
   // if they just sent a comment
	var scrollLeft = document.body.scrollLeft || document.documentElement.scrollLeft;
	var scrollTop = document.body.scrollTop || document.documentElement.scrollTop;
	var scrollBottom = (window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight) + scrollTop;
	var scrollRight = (window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth) + scrollLeft;


   if (field)
   {
	   var theElement = field;
	   var elemPosX = theElement.offsetLeft;
	   var elemPosY = theElement.offsetTop;
	   theElement = theElement.offsetParent;
	   	while(theElement != null)
	   	{
			elemPosX += theElement.offsetLeft
			elemPosY += theElement.offsetTop;
			theElement = theElement.offsetParent;
		}
		// Only scroll to element if it is out of the current screen
		if (elemPosX < scrollLeft || elemPosX > scrollRight ||
			elemPosY < scrollTop || elemPosY > scrollBottom)
		//window.scrollTo(elemPosX ,elemPosY);
		field.scrollIntoView();
		//window.scrollTo((field.getBoundingClientRect().left + scrollLeft) - ((scrollRight-scrollLeft)/2), (field.getBoundingClientRect().top + scrollTop) - ((scrollBottom-scrollTop)/2));
	}
}  // end function scrollToPosition()


/* It is not possible to get certain styles set in css such as display using
the normal javascript.  So we have to use this function taken from:
http://www.quirksmode.org/dom/getstyles.html */
function getStyle(el,styleProp)
{
	// if el is a string of the id or the actual object of the element
	var x = (document.getElementById(el)) ? document.getElementById(el) : el;
	if (x.currentStyle) // IE
		var y = x.currentStyle[styleProp];
	else if (window.getComputedStyle)  // FF
		var y = document.defaultView.getComputedStyle(x,null).getPropertyValue(styleProp);
	return y;
}



// Create findwindow DIV but make it invisible
// It will be turned visible when user clicks on
// the "Find on this page..." button
function create_div(dleft, dtop, dwidth, dheight)
{
    if (document.documentElement.scrollTop) // Needed if you use doctype loose.htm
		var current_top = document.documentElement.scrollTop;
	else
		var current_top = document.body.scrollTop;

    if (document.getElementById('findwindow'))
    {
        findwindow = document.getElementById('findwindow');
        //win_iframe = document.getElementById('win_iframe');
    }
    else
    {
	    findwindow.id = "findwindow";
	    findwindow.style.position = 'absolute';
        //document.body.appendChild(findwindow);
        document.body.insertBefore(findwindow, document.body.firstChild);
        findwindow.className = 'findwindow dragme';
		findwindow.style.visibility = 'hidden';
	}

    findwindow.style.backgroundColor = find_window_background;
    findwindow.style.border = '2px solid ' + find_window_border;
    findwindow.style.color = find_text_color;
	findwindow.style.width = find_window_width + 'px';
	//findwindow.style.height = + find_window_height + 'px'; // Version 5.3f - No longer using
    findwindow.style.top = '20px';
	findwindow.style.left = '20px';
	findwindow.style.padding = '0px';
	findwindow.style.zIndex = 2000;
	findwindow.style.fontSize = '14px';
	findwindow.style.overflowX = 'hidden';
	//findwindow.style.display = "block";

	// This part creates the title bar
	var string = '<div style="text-align: center'
	+ ';width: ' + (find_window_width-20) + 'px'
	+ ';cursor: move'  // turn mouse arrow to move icon
	+ ';color: ' + find_title_color
	+ ';border: 1px solid ' + find_text_color
	+ ';background-color: ' + find_window_border
	+ ';float: left'
	+ ';" onmouseover="over=1;" onmouseout="over=0;">'
	+ 'Find Window</div>';
	// This part creates the closing X
	string += '<div onclick="hide();" class="close" style="text-align: center'
	+ ';width: ' + (16) + 'px'
	+ ';cursor: default' // make mouse arrow stay an arrow instead of turning to text arrow
	+ ';font-weight: bold'
	+ ';background-color: red'
	+ ';border: 1px solid ' + find_text_color
	+ ';float: right'
	+ ';">'
	+ 'X' // write the letter X
	+ '</div><br />\n';
// This part creates the instructions and the "find" button
	string += '<div id="window_body" style="padding: 5px;">'
	+ '<form onsubmit="return false;"><input type="search" size="25" maxlength="25" id="fwtext"'
	+ ' onchange="resettext();" placeholder="Enter text to find">'
	+ '<input type="button" value="Find Prev" onclick="findprev();">'
	+ '<input type="button" value="Find Next" onclick="this.blur(); findit();">' // ver 5.3 - 5/15/2015 - added this.blur();
	+ ' <span id="find_msg"><br /></span>';
	if (enable_site_search) { // Version 5.4
		string += '<br /><label><input type="radio" name="search_type" value="page" checked>Page</label>'+
		'<label><input type="radio" name="search_type" value="site" id="find_site_search">Site</label>';
	}
	string += '</form></div>\n';
	// ^ ver 5.1 - 10/17/2014

	findwindow.innerHTML = string;

	// Check to see if css rules exist for hightlight and find_selected.
	var sheets = document.styleSheets;
	for (var i=0; i < sheets.length; i++)
	{
		// IE <= 8 uses rules; FF & Chrome and IE 9+ users cssRules
		var rules = (sheets[i].rules) ? sheets[i].rules : sheets[i].cssRules;
		if (rules != null)
		for (var j=0; j < rules.length; j++)
		{
			if (rules[j].selectorText == '.highlight')
				found_highlight_rule = 1;
			else if (rules[j].selectorText == '.find_selected')
				found_selected_rule = 1;
		}
	}


} // end function create_div()

function textarea2pre(el)
{
	// el is the textarea element

	// If a pre has already been created for this textarea element then use it
	if (el.nextSibling && el.nextSibling.id && el.nextSibling.id.match(/pre_/i))
		var pre = el.nextsibling;
	else
		var pre = document.createElement("pre");

	var the_text = el.value; // All the text in the textarea

	// replace <>" with entities
	the_text = the_text.replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
	//var text_node = document.createTextNode(the_text); // create text node for pre with text in it
	//pre.appendChild(text_node); // add text_node to pre
	pre.innerHTML = the_text;

	// Copy the complete HTML style from the textarea to the pre
	var completeStyle = "";
	if (typeof getComputedStyle !== 'undefined') // webkit
	{
		completeStyle = window.getComputedStyle(el, null).cssText;
		if (completeStyle != "") // Verison 5.3f - Is empty in IE 10 and Firefox
			pre.style.cssText = completeStyle; // Everything copies fine in Chrome
		else { // Version 5.3f - Because cssText is empty in IE 10 and Firefox
			var style = window.getComputedStyle(el, null);
			for (var i = 0; i < style.length; i++) {
    			completeStyle += style[i] + ": " + style.getPropertyValue(style[i]) + "; ";
    		}
    		pre.style.cssText = completeStyle;
		}
	}
	else if (el.currentStyle) // IE
	{
		var elStyle = el.currentStyle;
	    for (var k in elStyle) { completeStyle += k + ":" + elStyle[k] + ";"; }
	    //pre.style.cssText = completeStyle;
	    pre.style.border = "1px solid black"; // border not copying correctly in IE
	}

	el.parentNode.insertBefore(pre, el.nextSibling); // insert pre after textarea

	// If textarea blur then turn pre back on and textarea off
	el.onblur = function() { this.style.display = "none"; pre.style.display = "block"; };
	// If textarea changes then put new value back in pre
	el.onchange = function() { pre.innerHTML = el.value.replace(/>/g,'&gt;').replace(/</g,'&lt;').replace(/"/g,'&quot;'); };

	el.style.display = "none"; // hide textarea
	pre.id = "pre_"+highlights.length; // Add id to pre

	// Set onclick to turn pre off and turn textarea back on and perform a click on the textarea
	// for a possible onclick="this.select()" for the textarea
	pre.onclick = function() {this.style.display = "none"; el.style.display = "block"; el.focus(); el.click()};

	// this.parentNode.removeChild(this); // old remove pre in onclick function above

} // end function textarea2pre(el)

// ver 5.1 - 10/17/2014
function selectElementContents(el)
{
    /* http://stackoverflow.com/questions/8019534/how-can-i-use-javascript-to-select-text-in-a-pre-node-block */
	if (window.getSelection && document.createRange) {
        // IE 9 and non-IE
        var range = document.createRange();
        range.selectNodeContents(el);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    } else if (document.body.createTextRange) {
        // IE < 9
        var textRange = document.body.createTextRange();
        textRange.moveToElementText(el);
        textRange.select();
        //textRange.execCommand("Copy");
    }
} // end function selectElementContents(el)


// This part creates a visible button on the HTML page to
// where the script is pasted in the HTML code
document.write('<input type="button" value="Find on this page..."'
	+ ' onclick="show();">');

// Create the DIV
var findwindow = document.createElement("div");
create_div();




/* 10/5/2015 - To not have a find window that opens but rather to
	have the find box displayed in the page:
	1. Comment out lines 314, 315, 774, 775 and 779
	2. Uncomment all the lines below:
*/
/*var find_content = '<div id="window_body" style="padding: 5px;">'
+ 'Type in text to find: '
+ '<form onsubmit="return false;"><input type="search" size="25" maxlength="25" id="fwtext"'
+ ' onchange="resettext();">'
+ '<input type="button" value="Find Prev" onclick="findprev();">'
+ '<input id="btn" type="button" value="Find Next" onclick="findit();">'
+ '</form></div>'
+ '<div id="find_msg"><br /></div>';
document.write(find_content);
document.getElementById('fwtext').onkeydown = checkkey;
*/

var find_msg = document.getElementById('find_msg');
