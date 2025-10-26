import sys, os
import argparse
import json 
import pandas as pd

_MIN_REQUIRED_FIELDS = {
    'specimen:update': [tuple(['sampleid', 'processid'])],
    'specimen:new':['bold_recordset_code_arr', 'sampleid']
}

def read_mapping (file):
    return pd.read_csv(file, sep='\t')

def validate_submission_obj (json_obj, is_update):
    isValid = True
    msgs = []
    bcdm_mapping = read_mapping (args.mapping)
    
    if json_obj['submission_type'] != 'specimen':
        msgs.append ( f"[ERROR] Invalid submission type: Expected specimen, received {json_obj['submission_type']}")
        isValid = False

    # min required field checks
    request_subtype = f"{json_obj['submission_type']}:{ 'update' if is_update else 'new'}"
    if request_subtype in _MIN_REQUIRED_FIELDS:
        for fieldset in _MIN_REQUIRED_FIELDS[request_subtype]:
            if type(fieldset) == str:
                if fieldset not in json_obj['submission_packet'] or json_obj['submission_packet'][fieldset] in ('', None) :
                    msgs.append ( f"[ERROR][Request {json_obj['id']}] Required column {fieldset} is missing or empty.")
                    isValid = False
            elif type(fieldset) == tuple:
                if not set (fieldset) & set (json_obj['submission_packet'].keys()) or \
                all(json_obj['submission_packet'].get(f) in (None, "") for f in fieldset):
                    msgs.append (f"[ERROR][Request {json_obj['id']}] At least 1 of the following columns {','.join (fieldset)} is required.")
                    isValid = False

    # data model validator
    submitted_fields = json_obj['submission_packet'].keys()
    
    invalid_fields = [ field for field in submitted_fields if (bcdm_mapping['bcdm_field'] != field).all() ]

    if len(invalid_fields) > 0:
        print (f"[WARNING][Request {json_obj['id']}] Invalid fields found ", invalid_fields, file = sys.stderr)
        #TODO: confirm with Sujeevan filter out bad fields?  Or throw an error? 

    return isValid, msgs

def main(args):
    error_count = 0

    # Validate params

    # Process Input Data Jsonl
    results = []
    for line in sys.stdin:
        line = line.strip("\n")
        print (line)

    '''
    if error_count > 0:
        print (f"[ABORT] all-or-nothing: {error_count} records invalid. ", file=sys.stderr)
        sys.exit (1)
    elif len(error_count)== 0 and args.all_or_nothing:
        print ("\n".join (results))
    '''

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="""This tool takes a data JSONL in valid submission package format and checks if submitted data conforms to BCDM data types.  If all-or-nothing flag is not set, 
        only the valid submission objects will be written to stdout.  All error messages should be captured in stderr.  

Usage: cat data_bcdm.jsonl | python acceptability_check.py --data-tsv data_records.tsv --server-url 'http://localhost:8000" --username cwei --project CWEI --request-id TICKET#1234"
""")
    #parser.add_argument("--username", type=str, required=True, help="Username")
    parser.add_argument("--update", default=False, action=argparse.BooleanOptionalAction, help="If set, record existence is required to proceed with the update. Otherwise, new record submission is requested.")
    parser.add_argument("--batch-size", type=int, required=False, help="If set, the all-or-nothing applies to each batch.  Alternatively, all records submitted will be validated in single batch.")
    parser.add_argument("--all-or-nothing", action="store_true", help="True indicates all or nothing mode")
    parser.add_argument("--bcdm-def", type=str, required=True, help="Path to the BCDM definition file.")

    args = parser.parse_args()

    # Enforce dependency
    if args.batch_size is not None and not args.all_or_nothing:
        parser.error("--batch-size requires --all-or-nothing")

    main(args)