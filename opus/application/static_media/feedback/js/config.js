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
		label: "Need Help?",		// default: Need Help?
		color: "#20a8d8",			// default: #0b3d91
		fontColor: "#ffffff",		// default: #ffffff
		fontSize: "5",				// default: 16
		size: {
			width: "150",			// default: 150
			height: "60"			// default: 60
		},
		placement: {
			side: "right",			// default: right
			offset: "50"			// default: 50
		}
	}
};
