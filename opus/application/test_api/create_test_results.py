if __name__ == "__main__":
    import json
    import requests

    OPUS_IDS = [
        'co-cirs-0408010657-fp3',
        'co-cirs-0408031652-fp1',
        'co-cirs-0408041543-fp3',
        'co-cirs-0408152208-fp3',
        'co-cirs-0408161433-fp4',
        'co-cirs-0408220524-fp4',
        # 'co-iss-n1460961193',
        # 'co-iss-n1461527506',
        # 'co-iss-n1461810160',
        # 'co-iss-n1462660850',
        # 'co-iss-n1463306217',
        # 'co-iss-n1481652288',
        # 'co-iss-n1481663213',
        # 'co-iss-n1481666413',
        # 'co-iss-n1482859953',
        # 'co-iss-w1481834905',
        'co-uvis-euv2001_001_05_59',
        'co-uvis-euv2001_002_12_27',
        'co-uvis-euv2001_010_20_59',
        'co-uvis-fuv2001_013_06_07',
        'co-uvis-hdac2001_022_04_45',
        'co-uvis-hsp2001_087_04_00',
        'co-vims-v1484504730_vis',
        'co-vims-v1484580518_vis',
        'co-vims-v1484860325_ir',
        'co-vims-v1485757341_ir',
        'co-vims-v1485803787_ir',
        'co-vims-v1487262184_ir',
        'co-vims-v1490874999_001_vis',
        'go-ssi-c0347769100',
        'go-ssi-c0349673988',
        'go-ssi-c0349761213',
        'go-ssi-c0359986600',
        'hst-05642-wfpc2-u2fi0c05t',
        'hst-05642-wfpc2-u2fi0o0bt',
        'hst-05642-wfpc2-u2fi1901t',
        'hst-07243-nicmos-n4be03seq',
        'hst-07243-nicmos-n4be05blq',
        'hst-07308-stis-o43b2sxgq',
        'hst-07308-stis-o43ba6bxq',
        'hst-07308-stis-o43bd9bhq',
        'hst-09975-acs-j8n460zvq',
        'hst-11559-wfc3-ib4v22gxq',
        'nh-lorri-lor_0299075349',
        'nh-lorri-lor_0329817268',
        'nh-lorri-lor_0330787458',
        'nh-mvic-mc1_0005261846',
        'nh-mvic-mp1_0012448104',
        'vg-iss-2-s-c4360353',
        'mcd27m-iirar-occ-1989-184-28sgr-i',
        'eso1m-apph-occ-1989-184-28sgr-e',
        'lick1m-ccdc-occ-1989-184-28sgr-i',
        'co-rss-occ-2005-123-k26-i',
        'co-rss-occ-2008-217-s63-i',
        'co-rss-occ-2010-170-x34-e',
        'co-uvis-occ-2005-175-126tau-i',
        'co-uvis-occ-2009-015-gamcas-e',
        'co-vims-occ-2006-204-alpori-i',
        'co-vims-occ-2014-175-l2pup-e'
    ]

    # occ = {'Occultation Constraints': {'occtype': None, 'occdir': None, 'bodyoccflag': None, 'occtimesampling': None, 'occdataquality': None, 'occdepth1': None, 'occdepth2': None, 'occwlband': None, 'occsource': None, 'occreceiverhost': None}}

    session = requests.Session()

    for opus_id in OPUS_IDS:
        clean_opus_id = opus_id.replace('-', '_')
        print(f'    def test__results_contents_{clean_opus_id}(self):')
        print(f'        "[test_results_contents.py] {opus_id}"')
        print(f'        url = "/api/metadata_v2/{opus_id}.json"')
        print(f'        self._run_json_equal_file(url, "results_{clean_opus_id}.json")')
        print()

        # url = f'https://opus.pds-rings.seti.org/api/metadata_v2/{opus_id}.json'
        url = f'http://127.0.0.1:8000/api/metadata_v2/{opus_id}.json'
        r = session.get(url)
        j = json.loads(r.text.replace('"NULL"', 'null'))
        # j.update(occ)
        with open(f'responses/results_{clean_opus_id}.json', 'w') as fp:
            fp.write(json.dumps(j, indent=4))
