# This class is to build up testing APIs for either production or dev sites
class ApiFormats:
    formats = ["json", "html", "csv"]
    # slugs for testing
    payload_for_result_count = {"planet": "Saturn", "target": "Pan", "limit": 2}
    payload_for_mults = {"planet": "Jupiter", "target": "Jupiter", "limit": 2}
    payload_for_endpoints = {"planet": "Jupiter", "target": "Callisto", "limit": 2}
    payload_for_all_categories = {"planet": "Jupiter", "target": "Callisto", "mission": "Galileo", "limit": 2}
    payload_for_data = {"planet": "Saturn", "target": "Pan", "instrument": "Cassini ISS", "limit": 2}
    payload_for_metadata = {"cats": "PDS Constraints"}
    payload_for_images = {"planet": "Jupiter", "limit": 2}
    payload_for_files = {"planet": "Jupiter", "limit": 2}

    def __init__(self, target="production"):
        self.target = target
        self.api_base = self.build_api_base()
        self.api_data_base = self.build_api_data_base()
        self.api_images_size_base = self.build_api_images_size_base()
        self.api_images_base = self.build_api_images_base()
        self.api_all_files_base = self.build_api_all_files_base()
        self.api_result_count_base = self.build_api_result_count_base()
        self.api_mults_base = self.build_api_mults_base()
        self.api_endpoints_base = self.build_api_endpoints_base()
        self.api_all_categories_base = self.build_api_all_categories_base()
        self.api_fields_base = self.build_api_fields_base()
        self.api_all_fields_base = self.build_api_all_fields_base()

        self.api_metadata_base = self.build_api_metadata_base("co-iss-n1867600335")
        self.api_metadata_v2_base = self.build_api_metadata_v2_base("vg-iss-2-s-c4362550")
        self.api_images_with_opus_id_base = self.build_api_images_with_opus_id_base("go-ssi-c0349542178")
        self.api_files_with_opus_id_base = self.build_api_files_with_opus_id_base("vg-iss-2-n-c0898429")
        self.api_categories_with_opus_id_base = self.build_api_categories_with_opus_id_base("vg-iss-2-s-c4360511")

        self.api_dict = self.build_api_dict()

    #################
    ### Build API ###
    #################
    def build_api_base(self):
        """build up base api depending on target site: dev/production
        """
        if self.target == "production":
            return "https://tools.pds-rings.seti.org/opus/api/"
        elif self.target == "dev":
            return "http://dev.pds-rings.seti.org/opus/api/"

    def build_api_data_base(self):
        """api/data.[fmt]
        """
        return self.api_base + "data."

    def build_api_metadata_base(self, opus_id):
        """api/metadata/[opus_id].[fmt]
        """
        return self.api_base + "metadata/%s." %(opus_id)

    def build_api_metadata_v2_base(self, opus_id):
        """api/metadata_v2/[opus_id].[fmt]
        """
        return self.api_base + "metadata_v2/%s." %(opus_id)

    def build_api_images_size_base(self):
        """api/images/[size].[fmt]
        """
        return self.api_base + "images/thumb."

    def build_api_images_base(self):
        """api/images.[fmt]
        """
        return self.api_base + "images."

    def build_api_images_with_opus_id_base(self, opus_id):
        """api/image/[size]/[opus_id].[fmt]
        """
        return self.api_base + "image/full/%s." %(opus_id)

    def build_api_files_with_opus_id_base(self, opus_id):
        """api/files/[opus_id].[fmt]
        """
        return self.api_base + "files/%s." %(opus_id)

    def build_api_all_files_base(self):
        """api/files.[fmt]
        """
        return self.api_base + "files."

    def build_api_result_count_base(self):
        """api/meta/result_count.[fmt]
        """
        return self.api_base + "meta/result_count."

    def build_api_mults_base(self):
        """api/meta/mults/[param].[fmt]
        """
        return self.api_base + "meta/mults/planet." # use planet

    def build_api_endpoints_base(self):
        """api/meta/range/endpoints/[param].[fmt]
        """
        return self.api_base + "meta/range/endpoints/wavelength1." # use wavelength1

    def build_api_categories_with_opus_id_base(self, opus_id):
        """api/categories/[opus_id].json
        """
        return self.api_base + "categories/%s." %(opus_id)

    def build_api_all_categories_base(self):
        """api/categories.json
        """
        return self.api_base + "categories."

    def build_api_fields_base(self):
        """api/fields/[field].[fmt]
        """
        return self.api_base + "fields/mission." # use mission

    def build_api_all_fields_base(self):
        """api/fields.[fmt]
        """
        return self.api_base + "fields."

    def build_api_dict(self):
        """Test info for each api.
           ex:
           {'api': 'api/data.[fmt]',
            'payload': {'planet': 'Saturn',
                        'target': 'Pan',
                        'instrument': 'Cassini ISS',
                        'limit': 2},
            'support_format': ['json', 'html', 'csv']
           }
        """
        return {
            self.api_data_base: {
                "api": "api/data.[fmt]",
                "payload": ApiFormats.payload_for_data,
                "support_format": ["json", "html", "csv"]
            },
            self.api_metadata_base: {
                "api": "api/metadata/[opus_id].[fmt]",
                "payload": ApiFormats.payload_for_metadata,
                "support_format": ["json", "html"]
            },
            self.api_metadata_v2_base: {
                "api": "api/metadata_v2/[opus_id].[fmt]",
                "payload": ApiFormats.payload_for_metadata,
                "support_format": ["json", "html"]
            },
            self.api_images_size_base: {
                "api": "api/images/[size].[fmt]",
                "payload": ApiFormats.payload_for_images,
                "support_format": ["json", "html"]
            },
            self.api_images_base: {
                "api": "api/images.[fmt]",
                "payload": ApiFormats.payload_for_images,
                "support_format": ["json", "html"]
            },
            self.api_images_with_opus_id_base: {
                "api": "api/image/[size]/[opus_id].[fmt]",
                "payload": None,
                "support_format": ["json", "html"]
            },
            self.api_files_with_opus_id_base: {
                "api": "api/files/[opus_id].[fmt]",
                "payload": None,
                "support_format": ["json"]
            },
            self.api_all_files_base: {
                "api": "api/files.[fmt]",
                "payload": ApiFormats.payload_for_files,
                "support_format": ["json"]
            },
            self.api_result_count_base: {
                "api": "api/meta/result_count.[fmt]",
                "payload": ApiFormats.payload_for_result_count,
                "support_format": ["json", "html"]
            },
            self.api_mults_base: {
                "api": "api/meta/mults/[param].[fmt]",
                "payload": ApiFormats.payload_for_mults,
                "support_format": ["json", "html"]
            },
            self.api_endpoints_base: {
                "api": "api/meta/range/endpoints/[param].[fmt]",
                "payload": ApiFormats.payload_for_endpoints,
                "support_format": ["json", "html"]
            },
            self.api_categories_with_opus_id_base: {
                "api": "api/categories/[opus_id].json",
                "payload": None,
                "support_format": ["json"]
            },
            self.api_all_categories_base: {
                "api": "api/categories.json",
                "payload": ApiFormats.payload_for_all_categories,
                "support_format": ["json"]
            },
            self.api_fields_base: {
                "api": "api/fields/[field].[fmt]",
                "payload": None,
                "support_format": ["json", "html"]
            },
            self.api_all_fields_base: {
                "api": "api/fields.[fmt]",
                "payload": None,
                "support_format": ["json", "html"]
            },
        }
