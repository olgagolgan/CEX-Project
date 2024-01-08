# -IMPORTS-------------------------------------------------------------------------------------------------------------
import time
import json
import os
from elasticsearch import Elasticsearch as ES

# ---------------------------------------------------------------------------------------------------------------------
# -GLOBAL OBJECTS------------------------------------------------------------------------------------------------------
_index = 'olga_docs'
_scroll_size = 15  # how many input docs to retrieve at a time from the index
_max_extract_time = 0.5  # minutes
_max_scroll_tries = 2  # how often to retry when queries failed
_output_dir = 'outcite_sources'
_doc_id_test_sample = ['ENG_51', 'AGR-BIO-SCI_1']

_scr_body = {
    "query": {
        "bool": {
            "must": [
                {
                    "term": {
                        "has_fulltext": True
                    }
                },
                {
                    "exists": {
                        "field": "grobid_references_from_grobid_xml"
                    }
                }
            ]
        }
    }
}  # which documents to select for processing

# ---------------------------------------------------------------------------------------------------------------------
# -FUNCTIONS-----------------------------------------------------------------------------------------------------------


def check_dir(dir_name):
    try:
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
    except Exception as e:
        print(e)
        print('\n[!]-----> Failed to create a folder ', dir_name, '\n')


def get_canonical_refs():
    client = ES(['svko-vadis.gesis.intra'], scheme='http', port=9200, timeout=60)
    page = client.search(index=_index, scroll=str(int(_max_extract_time * _scroll_size)) + 'm', size=_scroll_size, body=_scr_body)
    sid = page['_scroll_id']
    returned = len(page['hits']['hits'])
    page_num = 0
    i = 1
    while returned > 0:
        for doc in page['hits']['hits']:

            try:
                print(doc['_id'], ' count: '+str(i))
                i += 1
                canonical_refs = doc['_source']
                # canonical_refs = doc['_source']['grobid_references_from_grobid_xml']
                # Serializing json
                json_list = json.dumps(canonical_refs, indent=4)
                # Writing to json
                check_dir(_output_dir)
                with open("./"+_output_dir+"/Grobid_refs_"+doc['_id']+".json", "w") as outfile:
                    outfile.write(json_list)
            except Exception as e:
                print(e)
                print('\n[!]-----> Some problem occurred while processing document', doc['_id'])
        scroll_tries = 0
        while scroll_tries < _max_scroll_tries:
            try:
                page = client.scroll(scroll_id=sid, scroll=str(int(_max_extract_time * _scroll_size)) + 'm')
                returned = len(page['hits']['hits'])
                page_num += 1
            except Exception as e:
                print(e)
                print('\n[!]-----> Some problem occurred while scrolling. Sleeping for 3s and retrying...')
                returned = 0
                scroll_tries += 1
                time.sleep(3)
                continue
            break
        # break  # uncomment to break after first page e.g. after 1st _scroll_size
    client.clear_scroll(scroll_id=sid)

# ---------------------------------------------------------------------------------------------------------------------
# -Calling Function----------------------------------------------------------------------------------------------------


get_canonical_refs()




