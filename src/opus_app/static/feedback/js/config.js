var config = {
	host: "https://pds.nasa.gov",	// Email Server Host
	feedback: {
		header: "OPUS Feedback and Support",
		feedbackType: "Comment,Question,Problem/Bug,Kudos,Other",
		additionalLinks: [
			{
				title: "PDS Ring-Moon Systems Node Home Page",
				url: "https://pds-rings.seti.org/"
			},
            {
				title: "OPUS Blog and Recent Announcements",
				url: "https://ringsnodesearchtool.blogspot.com/"
			},
			{
				title: "PDS-Wide Search",
				url: "https://pds.nasa.gov/datasearch/data-search/"
			},
			{
				title: "ROSES Proposal Support",
				url: "https://pds-rings.seti.org/roses/"
			},
			{
				title: "Cassini Information",
				url: "https://pds-rings.seti.org/cassini/"
			},
            {
				title: "Galileo Information",
				url: "https://pds-rings.seti.org/galileo/"
			},
			{
				title: "New Horizons Information",
				url: "https://pds-rings.seti.org/newhorizons/"
			},
            {
				title: "Hubble Space Telescope Information",
				url: "https://pds-rings.seti.org/hst/"
			}
		]
	},
	tab: {
		label: "Questions / Feedback",		// default: Need Help?
        // OPUS - moved directly into feedback.css
        // color: "#000000",
		// fontColor: "#ffffffc0",		// default: #ffffff
		fontSize: "13",				// default: 16
		size: {
			width: "185",			// default: 150
			height: "35"			// default: 60
		},
		placement: {
			side: "right",			// default: right
			offset: "50"			// default: 50
		}
	}
};
