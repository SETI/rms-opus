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

    def build_api_base(self):
        if self.target == "production":
            return "https://tools.pds-rings.seti.org/opus/api/"
        elif self.target == "dev":
            return "http://dev.pds-rings.seti.org/opus/api/"

    # Getting Data
    # api/data.[fmt]
    def build_api_data_base(self):
        return self.api_base + "data."

    # api/metadata/[opus_id].[fmt]
    def build_api_metadata_base(self, opus_id):
        return self.api_base + "metadata/%s." %(opus_id)

    # api/metadata_v2/[opus_id].[fmt]
    def build_api_metadata_v2_base(self, opus_id):
        return self.api_base + "metadata_v2/%s." %(opus_id)

    # api/images/[size].[fmt]
    def build_api_images_size_base(self):
        return self.api_base + "images/thumb."

    # api/images.[fmt]
    def build_api_images_base(self):
        return self.api_base + "images."

    # api/image/[size]/[opus_id].[fmt]
    def build_api_images_with_opus_id_base(self, opus_id):
        return self.api_base + "image/full/%s." %(opus_id)

    # api/files/[opus_id].[fmt]
    def build_api_files_with_opus_id_base(self, opus_id):
        return self.api_base + "files/%s." %(opus_id)

    # api/files.[fmt]
    def build_api_all_files_base(self):
        return self.api_base + "files."

    # Getting Information about Data
    # api/meta/result_count.[fmt]
    def build_api_result_count_base(self):
        return self.api_base + "meta/result_count."

    # api/meta/mults/[param].[fmt]
    def build_api_mults_base(self):
        return self.api_base + "meta/mults/planet." # use planet

    # api/meta/range/endpoints/[param].[fmt]
    def build_api_endpoints_base(self):
        return self.api_base + "meta/range/endpoints/wavelength1." # use wavelength1

    # api/categories/[opus_id].json
    def build_api_categories_with_opus_id_base(self, opus_id):
        return self.api_base + "categories/%s." %(opus_id)

    # api/categories.json
    def build_api_all_categories_base(self):
        return self.api_base + "categories."

    # api/fields/[field].[fmt]
    def build_api_fields_base(self):
        return self.api_base + "fields/mission." # use mission

    # api/fields.[fmt]
    def build_api_all_fields_base(self):
        return self.api_base + "fields."

    # info for each api
    def build_api_dict(self):
        return {
            self.api_data_base: {
                "api": "api/data.[fmt]",
                "payload": ApiFormats.payload_for_data,
                "support": ["json", "html", "csv"]
            },
            self.api_metadata_base: {
                "api": "api/metadata/[opus_id].[fmt]",
                "payload": ApiFormats.payload_for_metadata,
                "support": ["json", "html", "csv"]
            },
            self.api_metadata_v2_base: {
                "api": "api/metadata_v2/[opus_id].[fmt]",
                "payload": ApiFormats.payload_for_metadata,
                "support": ["json", "html", "csv"]
            },
            self.api_images_size_base: {
                "api": "api/images/[size].[fmt]",
                "payload": ApiFormats.payload_for_images,
                "support": ["json", "html", "csv"]
            },
            self.api_images_base: {
                "api": "api/images.[fmt]",
                "payload": ApiFormats.payload_for_images,
                "support": ["json", "html", "csv"]
            },
            self.api_images_with_opus_id_base: {
                "api": "api/image/[size]/[opus_id].[fmt]",
                "payload": None,
                "support": ["json", "html", "csv"]
            },
            self.api_files_with_opus_id_base: {
                "api": "api/files/[opus_id].[fmt]",
                "payload": None,
                "support": ["json", "html", "csv"]
            },
            self.api_all_files_base: {
                "api": "api/files.[fmt]",
                "payload": ApiFormats.payload_for_files,
                "support": ["json", "html", "csv"]
            },
            self.api_result_count_base: {
                "api": "api/meta/result_count.[fmt]",
                "payload": ApiFormats.payload_for_result_count,
                "support": ["json", "html", "zip"]
            },
            self.api_mults_base: {
                "api": "api/meta/mults/[param].[fmt]",
                "payload": ApiFormats.payload_for_mults,
                "support": ["json", "html", "zip"]
            },
            self.api_endpoints_base: {
                "api": "api/meta/range/endpoints/[param].[fmt]",
                "payload": ApiFormats.payload_for_endpoints,
                "support": ["json", "html", "csv"]
            },
            self.api_categories_with_opus_id_base: {
                "api": "api/categories/[opus_id].json",
                "payload": None,
                "support": ["json"]
            },
            self.api_all_categories_base: {
                "api": "api/categories.json",
                "payload": ApiFormats.payload_for_all_categories,
                "support": ["json"]
            },
            self.api_fields_base: {
                "api": "api/fields/[field].[fmt]",
                "payload": None,
                "support": ["json", "html", "zip"]
            },
            self.api_all_fields_base: {
                "api": "api/fields.[fmt]",
                "payload": None,
                "support": ["json", "html", "zip"]
            },
        }
