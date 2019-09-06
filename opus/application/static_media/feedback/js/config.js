var config = {
	host: "https://pds.nasa.gov",	// Email Server Host
	feedback: {
		header: "OPUS Feedback and Support",
		feedbackType: "Comment,Question,Problem/Bug,Kudos,Other",
		additionalLinks: [
			{
				title: "PDS Ring-Moon Systems Node",
				url: "https://pds-rings.seti.org/"
			},
			{
				title: "PDS-wide Search",
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
		label: "Questions?",		// default: Need Help?
        color: "#000000",
		fontColor: "#ffffffc0",		// default: #ffffff
		fontSize: "15",				// default: 16
		size: {
			width: "130",			// default: 150
			height: "35"			// default: 60
		},
		placement: {
			side: "right",			// default: right
			offset: "85"			// default: 50
		}
	}
};
