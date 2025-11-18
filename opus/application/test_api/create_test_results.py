if __name__ == "__main__":
    import json
    import requests

    OPUS_IDS = [
        # 'co-cirs-0408010657-fp3',
        # 'co-cirs-0408031652-fp1',
        # 'co-cirs-0408041543-fp3',
        # 'co-cirs-0408152208-fp3',
        # 'co-cirs-0408161433-fp4',
        # 'co-cirs-0408220524-fp4',
        # 'co-cirs-cube-000ph_fp3daymap001_ci004_609_f1_038e',
        # 'co-cirs-cube-000ia_presoi001____ri____699_f4_038p',
        # 'co-cirs-cube-000rb_comp001______ci005_680_f3_224r',
        # 'co-cirs-cube-127en_icyplu001____uv____699_f1_039e',
        # 'co-cirs-cube-127ic_dscal10066___sp____699_f4_039p',
        # 'co-cirs-cube-128ri_lrlemp001____is____680_f3_039r',
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
        # 'co-uvis-euv2001_001_05_59',
        # 'co-uvis-euv2001_002_12_27',
        # 'co-uvis-euv2001_010_20_59',
        # 'co-uvis-fuv2001_013_06_07',
        # 'co-uvis-hdac2001_022_04_45',
        # 'co-uvis-hsp2001_087_04_00',
        # 'co-vims-v1484504730_vis',
        # 'co-vims-v1484580518_vis',
        # 'co-vims-v1484860325_ir',
        # 'co-vims-v1485757341_ir',
        # 'co-vims-v1485803787_ir',
        # 'co-vims-v1487262184_ir',
        # 'co-vims-v1490874999_001_vis',
        # 'go-ssi-c0347769100',
        # 'go-ssi-c0349673988',
        # 'go-ssi-c0349761213',
        # 'go-ssi-c0359986600',
        # 'go-ssi-c0368977800',
        # 'go-ssi-c0248807000',
        # 'go-ssi-c0202540045',
        # 'hst-05642-wfpc2-u2fi0c05t',
        # 'hst-05642-wfpc2-u2fi0o0bt',
        # 'hst-05642-wfpc2-u2fi1901t',
        # 'hst-07181-nicmos-n4uc01b0q',
        # 'hst-07181-nicmos-n4uc01cjq',
        # 'hst-07316-stis-o57h02joq',
        # 'hst-07316-stis-o57h02010',
        # 'hst-09975-acs-j8n460zvq',
        # 'hst-11085-acs-j9xe05011',
        # 'hst-11559-wfc3-ib4v22gxq',
        # 'hst-13667-wfc3-icok28ihq',
        # 'hst-13667-wfc3-icok11rgq',
        # 'nh-lorri-lor_0299075349',
        # 'nh-lorri-lor_0329817268',
        # 'nh-lorri-lor_0330787458',
        # 'nh-mvic-mc0_0032528036',
        # 'nh-mvic-mc1_0005261846',
        # 'nh-mvic-mp1_0012448104',
        # 'vg-iss-2-s-c4360353',
        # 'mcd2m7-iirar-occ-1989-184-28sgr-i',
        # 'esosil1m04-apph-occ-1989-184-28sgr-e',
        # 'lick1m-ccdc-occ-1989-184-28sgr-i',
        # 'co-rss-occ-2005-123-rev007-k26-i',
        # 'co-rss-occ-2008-217-rev079c-s63-i',
        # 'co-rss-occ-2010-170-rev133-x34-e',
        # 'co-uvis-occ-2005-139-126tau-e',
        # 'co-uvis-occ-2005-175-126tau-i',
        # 'co-uvis-occ-2009-015-gamcas-e',
        # 'co-uvis-occ-2009-062-thehya-e',
        # 'co-vims-occ-2006-204-alpori-i',
        # 'co-vims-occ-2014-175-l2pup-e',
        # 'vg-pps-2-s-occ-1981-238-delsco-e',
        # 'vg-pps-2-u-occ-1986-024-sigsgr-delta-e',
        # 'vg-pps-2-n-occ-1989-236-sigsgr-i',
        # 'vg-uvs-1-s-occ-1980-317-iother-e',
        # 'vg-rss-2-u-occ-1986-024-s43-four-i',
        # 'vg-uvs-2-n-occ-1989-236-sigsgr-i',
        # 'vg-iss-2-s-prof',
        # 'kao0m91-vis-occ-1977-069-u0-ringpl-i',
        # 'kao0m91-vis-occ-1977-069-u0-uranus-e',
        # 'kao0m91-vis-occ-1977-069-u0-eta-e'
    ]

    session = requests.Session()

    for opus_id in OPUS_IDS:
        clean_opus_id = opus_id.replace('-', '_')
        print(f'    def test__results_contents_{clean_opus_id}_metadata(self):')
        print(f'        "[test_results_contents.py] {opus_id} metadata"')
        print(f'        url = "/api/metadata/{opus_id}.json"')
        print(f'        self._run_json_equal_file(url, "results_{clean_opus_id}_metadata.json")')
        print()

        # url = f'https://opus.pds-rings.seti.org/api/metadata/{opus_id}.json'
        url = f'http://127.0.0.1:8000/api/metadata/{opus_id}.json'
        r = session.get(url)
        j = json.loads(r.text.replace('"NULL"', 'null'))
        with open(f'responses/results_{clean_opus_id}_metadata.json', 'w') as fp:
            fp.write(json.dumps(j, indent=4))

        print(f'    def test__results_contents_{clean_opus_id}_files(self):')
        print(f'        "[test_results_contents.py] {opus_id} files"')
        print(f'        url = "/api/files/{opus_id}.json"')
        print(f'        self._run_json_equal_file(url, "results_{clean_opus_id}_files.json")')
        print()

        url = f'http://127.0.0.1:8000/api/files/{opus_id}.json'
        r = session.get(url)
        j = json.loads(r.text.replace('"NULL"', 'null'))
        with open(f'responses/results_{clean_opus_id}_files.json', 'w') as fp:
            fp.write(json.dumps(j, indent=4))

        print(f'    def test__results_contents_{clean_opus_id}_images(self):')
        print(f'        "[test_results_contents.py] {opus_id} images"')
        print(f'        url = "/api/images.json?opusid={opus_id}"')
        print(f'        self._run_json_equal_file(url, "results_{clean_opus_id}_images.json")')
        print()

        url = f'http://127.0.0.1:8000/api/images.json?opusid={opus_id}'
        r = session.get(url)
        j = json.loads(r.text.replace('"NULL"', 'null'))
        with open(f'responses/results_{clean_opus_id}_images.json', 'w') as fp:
            fp.write(json.dumps(j, indent=4))
