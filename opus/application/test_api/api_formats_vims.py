from api_formats import ApiFormats
# This class is to build up testing APIs for VIMS products to verify multiple downlinks
class ApiForVimsDownlinks(ApiFormats):
    opus_id_all = {
        "v1490874598": [
            "co-vims-v1490874598_001_ir",
            "co-vims-v1490874598_001_vis",
            "co-vims-v1490874598_002_ir",
            "co-vims-v1490874598_002_vis",
        ],
        "v1490874654": [
            "co-vims-v1490874654_001_ir",
            "co-vims-v1490874654_001_vis",
            "co-vims-v1490874654_002_ir",
            "co-vims-v1490874654_002_vis",
        ],
        "v1490874707": [
            "co-vims-v1490874707_001_ir",
            "co-vims-v1490874707_001_vis",
            "co-vims-v1490874707_002_ir",
            "co-vims-v1490874707_002_vis",
        ],
        "v1490874775": [
            "co-vims-v1490874775_001_ir",
            "co-vims-v1490874775_001_vis",
            "co-vims-v1490874775_002_ir",
            "co-vims-v1490874775_002_vis",
        ],
        "v1490874823": [
            "co-vims-v1490874823_001_ir",
            "co-vims-v1490874823_001_vis",
            "co-vims-v1490874823_002_ir",
            "co-vims-v1490874823_002_vis",
        ],
        "v1490874878": [
            "co-vims-v1490874878_001_ir",
            "co-vims-v1490874878_001_vis",
            "co-vims-v1490874878_002_ir",
            "co-vims-v1490874878_002_vis",
        ],
        "v1490874946": [
            "co-vims-v1490874946_001_ir",
            "co-vims-v1490874946_001_vis",
            "co-vims-v1490874946_002_ir",
            "co-vims-v1490874946_002_vis",
        ],
        "v1490874999": [
            "co-vims-v1490874999_001_ir",
            "co-vims-v1490874999_001_vis",
            "co-vims-v1490874999_002_ir",
            "co-vims-v1490874999_002_vis",
        ],
        "v1490875052": [
            "co-vims-v1490875052_001_ir",
            "co-vims-v1490875052_001_vis",
            "co-vims-v1490875052_002_ir",
            "co-vims-v1490875052_002_vis",
        ],
    }

    def __init__(self, target):
        super().__init__(target)

    def build_all_testing_api(self):
        self.api_dict = self.build_api_dict()

    # info for api calls with vims product
    def build_api_dict(self):
        res = {}
        url = self.build_api_all_files_base()
        for primary_filespec in ApiForVimsDownlinks.opus_id_all:
            res[primary_filespec] = {
                "api": "api/files.[fmt]",
                "payload": {"primaryfilespec": primary_filespec},
                "images_with_opus_id": ApiForVimsDownlinks.opus_id_all[primary_filespec],
                "url": url
            }
        return res
