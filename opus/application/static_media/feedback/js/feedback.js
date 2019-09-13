/*
    Copyright (c) 2019, California Institute of Technology ("Caltech").
    U.S. Government sponsorship acknowledged.
    All rights reserved.
    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
      * Redistributions must reproduce the above copyright notice, this list of
      conditions and the following disclaimer in the documentation and/or other
      materials provided with the distribution.
      * Neither the name of Caltech nor its operating division, the Jet Propulsion
      Laboratory, nor the names of its contributors may be used to endorse or
      promote products derived from this software without specific prior written
      permission.
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE.
*/

var FeedbackMethods;

document.addEventListener("DOMContentLoaded", function(){
	FeedbackMethods = Feedback(config);
});

(function( window, document, undefined ) {
	if ( window.Feedback !== undefined ) {
		return;
	}

	// log proxy function
	var log = function( msg ) {
		window.console.log( msg );
	},
	// function to remove elements, input as arrays
	removeElements = function( remove ) {
		for (var i = 0, len = remove.length; i < len; i++ ) {
			var item = Array.prototype.pop.call( remove );
			if ( item !== undefined ) {
				if (item.parentNode !== null ) { // check that the item was actually added to DOM
					item.parentNode.removeChild( item );
				}
			}
		}
	},
	loader = function() {
		var div = document.createElement("div"), i = 3;
		div.className = "feedback-loader";

		while (i--) { div.appendChild( document.createElement( "span" )); }
		return div;
	},
	getBounds = function( el ) {
		return el.getBoundingClientRect();
	},
	emptyElements = function( el ) {
		var item;
		while( (( item = el.firstChild ) !== null ? el.removeChild( item ) : false) ) {}
	},
	element = function( name, text ) {
		var el = document.createElement( name );
		el.appendChild( document.createTextNode( text ) );
		return el;
	},
	// script onload function to provide support for IE as well
	scriptLoader = function( script, func ){
		if (script.onload === undefined) {
			// IE lack of support for script onload

			if( script.onreadystatechange !== undefined ) {

				var intervalFunc = function() {
					if (script.readyState !== "loaded" && script.readyState !== "complete") {
						window.setTimeout( intervalFunc, 250 );
					} else {
						// it is loaded
						func();
					}
				};

				window.setTimeout( intervalFunc, 250 );

			} else {
				log("ERROR: We can't track when script is loaded");
			}

		} else {
			return func;
		}

	},
	sendButton,
	captchaUrl = "/feedback/recaptcha-v3-verify.php",
	feedbackUrl = "/email-service/SubmitFeedback",
	modal = document.createElement("div"),
	modalBody = document.createElement("div"),
	modalHeader = document.createElement("div"),
	modalFooter = document.createElement("div"),
	captchaScore = 0;

	// window.captchaCallback = function( response ) {};

	window.Feedback = function( options ) {

		options = options || {};

		// default properties
		options.host = options.host || "";
		options.feedback.header = options.feedback.header || "Help Desk";
		options.page = options.page || new window.Feedback.Form();

		var glass = document.createElement("div"),
			returnMethods = {

			// open send feedback modal window
			open: function() {
				options.page.render();
				document.body.appendChild( glass );
				button.disabled = true;

				// modal close button
                // OPUS uses font-awesome
                var ax = element("i", "");
                ax.setAttribute("class", "far fa-times-circle fa-lg");
				var a = element("a", "");
				a.className =  "feedback-close";
                a.appendChild(ax);
				a.onclick = returnMethods.close;
				a.href = "#";

				// build header element
				modalHeader.appendChild( a );
                h3 = element("h3", options.feedback.header );
                h3.appendChild(a);
				modalHeader.appendChild(h3);
				modalHeader.className =  "feedback-header";

				modalBody.className = "feedback-body";

				emptyElements( modalBody );
				modalBody.appendChild( element("p", "How can we help you? Send us your question or feedback and we will get back to you as soon as possible.") );
				modalBody.appendChild( options.page.dom );
				var links = options.feedback.additionalLinks;
				if ( links !== "" ) {
					var additionalHelp = element("p", "In the meantime, you may find the following links helpful:"),
						additionalLinks = document.createElement("ul");
					additionalHelp.className = "additionalHelp";
					for (var i = 0; i < links.length; i++) {
						additionalLinks.insertAdjacentHTML('beforeend', '<li><a href="' + links[i].url + '">' + links[i].title + '</a></li>');
					}
					additionalHelp.insertAdjacentElement("beforeend", additionalLinks);
					modalBody.insertAdjacentElement("beforeend", additionalHelp);
					window.additionalHelp = additionalHelp;
				}

				// Send button
				sendButton = document.createElement("input");
				sendButton.type = "submit";
				sendButton.value = "Send Feedback";
				// sendButton.setAttribute("class", "feedback-btn g-recaptcha");
                sendButton.setAttribute("class", "feedback-btn");
				// sendButton.setAttribute("data-callback", "captchaCallback");
				// sendButton.setAttribute("id", "recaptcha");
                sendButton.onclick = returnMethods.send;

				// reCAPTCHA branding
				// rcBrand = document.createElement("p");
				// rcBrand.innerHTML = 'This site is protected by reCAPTCHA and the Google <a href="https://policies.google.com/privacy">Privacy Policy</a> and <a href="https://policies.google.com/terms">Terms of Service</a> apply.';
				// rcBrand.className = "reCaptcha-brand";

				modalFooter.className = "feedback-footer";
				// modalFooter.appendChild( rcBrand );
				modalFooter.appendChild( sendButton );

				modal.setAttribute("id", "feedback-form");
				modal.className = "feedback-modal";

				modal.appendChild( modalHeader );
				modal.appendChild( modalBody );
				modal.appendChild( modalFooter );

				document.body.appendChild( modal );

				// window.grecaptcha.render("recaptcha", {sitekey: "6LfLCIgUAAAAAI3xLW5PQijxDyZcaUUlTyPDfYlZ"});
			},


			// close modal window
			close: function() {

				button.disabled = false;

				// window.grecaptcha.reset();

				// remove feedback elements
				emptyElements( modalHeader );
				emptyElements( modalFooter );
				removeElements( [ modal, glass ] );

				return false;
			},

			// send data
			send: function( event /*adapter*/ ) {
				// make sure send adapter is of right prototype
				// if ( !(adapter instanceof window.Feedback.Send) ) {
				// 	throw new Error( "Adapter is not an instance of Feedback.Send" );
				// }

				data = options.page.data();
				emptyElements( modalBody );
				modalBody.appendChild( loader() );

				// send data to adapter for processing
				window.Feedback.XHR.prototype.send( data, function( success ) {

					emptyElements( modalBody );
					sendButton.disabled = false;

					sendButton.value = "Close";

					sendButton.onclick = function() {
						returnMethods.close();
						return false;
					};

					modalBody.setAttribute("class", "feedback-body confirmation");
					var message = document.createElement("p");
					if ( success === true ) {
						message.innerHTML = 'Thank you for making OPUS a better site.<br/>If you provided an email address, a PDS representative will get back to you as soon as possible.';
					} else {
						message.innerHTML = 'There was an error sending your feedback.<br/>If the problem persists, please email <a href="mailto:pds_operator@jpl.nasa.gov">pds_operator@jpl.nasa.gov</a>.';
					}
					modalBody.appendChild( message );

					if ( window.additionalHelp ) {
						modalBody.appendChild( window.additionalHelp );
					}
				});

			},

			onloadCallback: function() {
				if ( new URLSearchParams(window.location.search).get("feedback") === "true" ) {
					returnMethods.open();
				}
			},

			captchaCallback: function( response ) {
				if ( document.getElementById("feedback-comment").reportValidity() ) {
					$.ajax({
						type: "POST",
						url: captchaUrl,
						data: {response: response},
						success: function (data) {
							//console.log(data);
							captchaScore = parseFloat(data.substring(data.indexOf("float") + 6, data.indexOf("float") + 9));
							if (captchaScore > 0.70) {
								options.url = options.url || options.host + feedbackUrl;
								options.adapter = options.adapter || new window.Feedback.XHR(options.url);
								emptyElements(modalBody);
								returnMethods.send(options.adapter);
							} else {
								modalBody.setAttribute("class", "feedback-body suspectedBot");
								document.getElementById("recaptcha").disabled = true;
								modalBody.insertAdjacentElement("afterbegin", element("p", "Are you a bot? Suspicious behavior detected."));
							}
						},
						error: function (XMLHttpRequest, textStatus, errorThrown) {
							modalBody.setAttribute("class", "feedback-body captchaError");
							var message = document.createElement("p");
							message.innerHTML = 'Status: ' + textStatus + '; Error: ' + errorThrown + '<br/>If the problem persists, please email <a href="mailto:pds_operator@jpl.nasa.gov">pds_operator@jpl.nasa.gov</a>.';
							modalBody.insertAdjacentElement("afterbegin", message);
						}
					});
				} else {
					return false;
				}
				window.grecaptcha.reset();
			}

		};

		// window.onloadCallback = returnMethods.onloadCallback;
		// window.captchaCallback = returnMethods.captchaCallback;

		glass.className = "feedback-glass";

		var button = document.createElement("button");

		if ( Modernizr.touchevents && window.screen.width < 1025 ) {
			var $window = $(window),
				docHeight = $(document).height(),
				rafId;
			window.requestAnimationFrame = window.requestAnimationFrame
				|| window.mozRequestAnimationFrame
				|| window.webkitRequestAnimationFrame
				|| window.msRequestAnimationFrame;
			$window.on("scroll", function() {
				if ( $window.scrollTop() + $window.height() > docHeight - 65 ) {
					rafId = window.requestAnimationFrame(function() {
						var offset = ($window.scrollTop() - 65) * ($window.scrollTop() - 65) * 0.00001;
						button.style.webkitTransform = "translateY(-" + offset + "px)";
						button.style.mozTransform = "translateY(-" + offset + "px)";
						button.style.transform = "translateY(-" + offset + "px)";
					});
				} else {
					window.cancelAnimationFrame(rafId);
					button.style.webkitTransform = "initial";
					button.style.mozTransform = "initial";
					button.style.transform = "initial";
				}
			});
		} else {
			// default properties
			options.tab.label = options.tab.label || "Need Help?";
			options.tab.color = options.tab.color || "#0b3d91";
			options.tab.fontColor = options.tab.fontColor || "#ffffff";
			options.tab.fontSize = options.tab.fontSize || "16";
			options.tab.size.width = options.tab.size.width || "150";
			options.tab.size.height = options.tab.size.height || "60";
			options.tab.placement.side = options.tab.placement.side || "right";
			options.tab.placement.offset = options.tab.placement.offset || "50";

			var useConfig = {
				setColors: function(el, color, bgColor) {
                    // OPUS
					// el.style.color = color;
					// el.style.backgroundColor = bgColor;
				},

				setText: function(el, label, fontSize) {
					var p = document.createElement("p");
					p.append( document.createTextNode(label) );
					if ( fontSize !== "16" ) {
						if ( !isNaN(fontSize) ) {
							el.setAttribute("class", "noImage");
							el.style.fontSize = fontSize + "px";
						} else {
							console.log("Invalid value for font size. Please check the configuration file.");
						}
					}
					el.appendChild(p);
				},

				setDimensions: function(el, width, height) {
					if ( !isNaN(width) && !isNaN(height) ) {
						el.style.width = width + "px";
						el.style.height = height + "px";
					} else {
						if ( isNaN(width) ) {
							console.log("Invalid value for tab WIDTH. Please check the configuration file.");
						}
						if ( isNaN(height) ) {
							console.log("Invalid value for tab HEIGHT. Please check the configuration file.");
						}
					}
				},

				calculateAdjustment: function(width, height) {
					return -0.5 * ( Number(width) - Number(height) ) - 5;
				},

				calculateMaxOffset: function(width, height) {
					return [ window.innerHeight - 0.5 * ( Number(width) + Number(height) ), window.innerWidth - Number(width) ];
				},

				setPlacement: function(el, side, offset, maxOffset, adjustment) {
					if ( !isNaN(offset) ) {
						if ( side === "right" || side === "left" ) {
							var os = Number(offset) * window.innerHeight / 100,
								minOffset = -1 * ( Number(adjustment) + 5 ),
								adjust = ( adjustment !== undefined );
							if ( os < minOffset ) {
								el.style.top = minOffset + "px";
							} else if ( os > Number(maxOffset[0]) ) {
								el.style.top = maxOffset[0] + "px";
							} else {
								el.style.top = offset + "vh";
							}
							if ( side === "right" ) {
								el.setAttribute("class", "feedbackTab");
								if ( adjust ) {
									el.style.right = adjustment + "px";
								}
							} else  {
								el.setAttribute("class", "feedbackTab left");
								if ( adjust ) {
									el.style.left = adjustment + "px";
								}
							}
						} else if (side === "top" || side === "bottom" ) {
							if ( Number(offset) < 0 ) {
								el.style.left = "0";
							} else if ( Number(offset) * window.innerWidth / 100 > Number(maxOffset[1]) ) {
								el.style.left = maxOffset[1] + "px";
							} else {
								el.style.left = offset + "vw";
							}
							if ( side === "top" ) {
								el.setAttribute("class", "feedbackTab top");
							} else {
								el.setAttribute("class", "feedbackTab bottom");
							}
						} else {
							console.log("Invalid value for SIDE of screen to place the tab. The valid options " +
								"are LEFT, RIGHT, TOP, or BOTTOM. Please check the configuration file.");
						}
					} else {
						console.log("Invalid value for OFFSET of tab placement. Please check the configuration file.");
					}
				}
			};

			useConfig.setColors(button, options.tab.fontColor, options.tab.color);
			useConfig.setText(button, options.tab.label, options.tab.fontSize);

			var	adjustment,
				width = Math.max( Number(options.tab.size.width), Number(options.tab.size.height) ),
				height = Math.min( Number(options.tab.size.width), Number(options.tab.size.height) ),
				defaultWidth = ( width === 150 ),
				defaultHeight = ( height === 60 );
			if ( !defaultWidth || !defaultHeight ) {
				useConfig.setDimensions(button, width, height);
				adjustment = useConfig.calculateAdjustment(width, height);
			}

			var side = options.tab.placement.side.toLowerCase(),
				offset = options.tab.placement.offset,
				maxOffset = useConfig.calculateMaxOffset(width, height);
			if ( offset !== "50" || side !== "right" || adjustment !== undefined ) {
				useConfig.setPlacement(button, side, offset, maxOffset, adjustment);
			}
		}

		if ( !button.classList.contains("feedbackTab") ) {
			button.className = "feedbackTab";
		}
		button.onclick = returnMethods.open;

		if ( options.appendTo !== null ) {
			((options.appendTo !== undefined) ? options.appendTo : document.body).appendChild( button );
		}

		return returnMethods;
	};

	window.Feedback.Page = function() {};
	window.Feedback.Page.prototype = {

		render: function( dom ) {
			this.dom = dom;
		},
		start: function() {},
		close: function() {},
		data: function() {
			// don't collect data from page by default
			return false;
		},
		end: function() { return true; }

	};
	window.Feedback.Send = function() {};
	window.Feedback.Send.prototype = {

		send: function() {}

	};

	window.Feedback.Form = function( elements ) {

		this.elements = elements || [
			{
				type: "input",
				id: "feedback-name",
				name: "Name",
				label: "Name",
				required: false
			},
			{
				type: "input",
				id: "feedback-email",
				name: "Email",
				label: "Email",
				required: false
			},
			{
				type: "select",
				id: "feedback-type",
				name: "Type",
				label: "Type",
				values: config.feedback.feedbackType,
				required: false
			},
			{
				type: "textarea",
				id: "feedback-comment",
				name: "Comment",
				label: "Comment",
				required: true
			}
		];
		this.dom = document.createElement("div");
		this.dom.className = "feedback-form-container";

	};

	window.Feedback.Form.prototype = new window.Feedback.Page();

	window.Feedback.Form.prototype.render = function() {

		var i = 0, len = this.elements.length, item;
		emptyElements( this.dom );
		for (; i < len; i++) {
			item = this.elements[ i ];
			var div = document.createElement("div");
			div.classList.add("feedback-input");

			var formEl = document.createElement( item.type );
			formEl.name = item.name;
			formEl.id = item.id;

			if ( item.required ) {
				formEl.required = true;
				div.appendChild( element("label", item.label + ": *"));
			} else {
				div.appendChild( element("label", item.label + ":"));
			}

			if (item.type === "select") {
				var options = item.values.split(",");
				for (j = 0; j < options.length; j++) {
					var option = document.createElement("option");
					option.value = option.textContent = options[j];
					formEl.appendChild(option);
				}
			}

			div.appendChild( (item.element = formEl) );
			this.dom.appendChild(div);
		}

		return this;

	};

	window.Feedback.Form.prototype.end = function() {
		// form validation
		var i = 0, len = this.elements.length, item;
		for (; i < len; i++) {
			item = this.elements[ i ];

			// check that all required fields are entered
			if ( item.required === true && item.element.value.length === 0) {
				item.element.className = "feedback-error";
				return false;
			} else {
				item.element.className = "";
			}
		}

		return true;

	};

	window.Feedback.Form.prototype.data = function() {
		var i = 0, len = this.elements.length, item, data = {};

		for (; i < len; i++) {
			item = this.elements[ i ];
			data[ item.name ] = item.element.value;
		}

		// cache and return data
		return ( this._data = data );
	};

	window.Feedback.XHR = function( url ) {

		this.xhr = new XMLHttpRequest();
		this.url = url;

	};

	window.Feedback.XHR.prototype = new window.Feedback.Send();

	window.Feedback.XHR.prototype.send = function( data, callback ) {
		// var xhr = this.xhr;
        var xhr = new XMLHttpRequest();

		xhr.onreadystatechange = function() {
			if( xhr.readyState == 4 ) {
				callback( (xhr.status === 200) );
			}
		};

		var emailData = '';
		emailData = 'subject=Feedback from ' + window.location.hostname;
		emailData += '&content=';

		for (var key in data) {
			emailData += key + ': ';
			emailData += data[key] + '\n';
		}

		emailData += '\nLocation: ' + window.location.href + '\n';

		// xhr.open( "POST", this.url, true);
        xhr.open( "POST", "https://pds.nasa.gov/email-service/SubmitFeedback", true);
		xhr.setRequestHeader('Content-type','application/x-www-form-urlencoded');
		xhr.send(emailData);
	};

})( window, document );
