import argparse
import json, sys, os, csv

import urllib.parse

__ACCEPTED_RECORDID_FIELDS = ['processid', 'sampleid']
__EXCLUDED_FIELDS = ['record_id']


########## Helper Functions ##########

def convert_upload_single_package (json_obj, bcdm_to_bold_mapping):
    data_json = json_obj['submission_packet']
    
    record_identifier = None
    for field in __ACCEPTED_RECORDID_FIELDS:
        if field in data_json and data_json[field]:
            record_identifier = data_json[field]
    if record_identifier is None:
        raise Exception (f"[ERROR][Request {json_obj['id']}] {' or '.join (__ACCEPTED_RECORDID_FIELDS)} is required.")

    converted_obj = {}
    for bcdm_field in bcdm_to_bold_mapping:
        if bcdm_field in data_json:
            converted_obj [bcdm_field]= [{
                'db_table':bcdm_to_bold_mapping[bcdm_field]['table'], 
                'db_field':bcdm_to_bold_mapping[bcdm_field]['field'], 
                'value':data_json[bcdm_field], 
            }]

            if data_json[bcdm_field] == '':  
                converted_obj [bcdm_field][0]['value']= None   # This translate to null in DB
    return converted_obj #{record_identifier:converted_obj}

def get_bcdm_to_bold_mapping (excluded_fields=None):   
    """
    This function returned a dictionary of db_field mapping where the keys are the universal fields.  If the optional param excluded_fields 
    is provided, the fields matching to ones in this list will NOT be returned.
    """
    delimiter = '__'
    filepath = args.mapping
    db_mapping = {}

    with open (filepath ) as mapping_file:
        rows = csv.DictReader(mapping_file, delimiter="\t")
        for row in rows:
            if len(row)==0: continue
            if not excluded_fields or row['bcdm_field'] not in excluded_fields:        # Remove this after testing. 
                info = row['bold_field'].split('.')
                if len(info) >2: # foreign key
                    #print (info, file=sys.stderr)
                    table = info[0].split(delimiter)[0] + delimiter + info[1]
                    field = info[0].split(delimiter)[1] + delimiter + info[2]
                else: 
                    table = info[0]
                    field = info [1]
                db_mapping [row['bcdm_field']]= {'db': 'newdb12','table': table, 'field': field}

    return db_mapping


def main(args):

    # Param processing
    if not os.path.exists(args.mapping):
        print ( f"[ABORT] Mapping file path not found: {args.mapping}", file=sys.stderr)
        sys.exit (1)

    count_rows = 0 #len(list(reader))
    error_records = []

    # Input Submission Processing (ALL or NOTHING)
    bcdm_to_bold_mapping = get_bcdm_to_bold_mapping(__EXCLUDED_FIELDS)

    results = []        # Only use if all_or_nothing
    for line in sys.stdin:
        sub_obj = json.loads(line.strip("\n"))
        try:
            converted_obj = convert_upload_single_package (sub_obj, bcdm_to_bold_mapping) 
            if not converted_obj: 
                raise Exception (f"[ERROR][Request {sub_obj['id']}]Error converting bcdm record to upload json object")
            else:  
                if not args.all_or_nothing:
                    print (json.dumps(converted_obj))
                else:
                    results.append (json.dumps(converted_obj))
        except Exception as e: 
            print (e, file=sys.stderr)
            if args.all_or_nothing:
                print (f"[ABORT] all-or-nothing: detected invalid record. ", file=sys.stderr)
                break
                
    if len(results) > 0:
        print ("\n".join (results))
        
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="""This tool takes a data TSV in BCDM format and submits the specimen record to the BOLD Database via the Submission API.  
This tool can run any machine with access to internet.

Usage: python orchestrator_submission.py --data-tsv data_records.tsv --server-url 'http://localhost:8000" --username cwei --project CWEI --request-id TICKET#1234"
""")
    #parser.add_argument("--data", type=str, required=True, help="Path to the JSONL data file. All data will be url encoded")
    #parser.add_argument("--username", type=str, required=True, help="Username")
    #parser.add_argument("--update", default=False, action=argparse.BooleanOptionalAction, help="If set, record existence is required to proceed with the update. Otherwise, new record submission is requested.")
    parser.add_argument("--mapping", type=str, required=True, help="File path for the BCDM field to BOLD DB field mapping")
    parser.add_argument("--all-or-nothing", action="store_true", help="True indicates all or nothing mode")

    args = parser.parse_args()
 
    main(args)
