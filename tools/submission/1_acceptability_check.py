import sys, os
import argparse
import json 
import pandas as pd

_ACCEPTED_SUB_TYPES = ['specimen']
_MIN_REQUIRED_FIELDS = {
    'specimen:update': [tuple(['sampleid', 'processid'])],
    'specimen:new':['bold_recordset_code_arr', 'sampleid']
}

def read_mapping (file):
    return pd.read_csv(file, sep='\t')

def validate_submission_obj (json_obj, is_update):
    isValid = True
    msgs = []
    bcdm_mapping = read_mapping (args.bcdm_def)
    
    if json_obj['submission_type'] not in _ACCEPTED_SUB_TYPES:
        msgs.append ( f"[ERROR] Invalid submission type: Expected {','.join (_ACCEPTED_SUB_TYPES)}, received {json_obj['submission_type']}")
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
    
    invalid_fields = [ field for field in submitted_fields if (bcdm_mapping['field'] != field).all() ]

    if len(invalid_fields) > 0:
        print (f"[WARNING][Request {json_obj['id']}] Invalid fields found ", invalid_fields, file = sys.stderr)
        #TODO: confirm with Sujeevan filter out bad fields?  Or throw an error? 

    return isValid, msgs

def main(args):
    error_count = 0

    # Validate params
    if not os.path.exists(args.bcdm_def):
        print ( f"Mapping file path not found: {args.bcdm_def}", file=sys.stderr)
        sys.exit (1)

    # Process Input Data Jsonl
    results = []
    for line in sys.stdin:
        line = line.strip("\n")
        isValid, msgs = validate_submission_obj (json.loads(line), args.update)
        if not isValid: 
            print ( "\n".join (msgs), file=sys.stderr)
            error_count+=1
        else:
            if not args.all_or_nothing: 
                print (line)
            else:
                results.append (line)

    if error_count > 0 and args.all_or_nothing:
        print (f"[ABORT] all-or-nothing: {error_count} records invalid. ", file=sys.stderr)
        sys.exit (1)
    elif error_count== 0 and args.all_or_nothing:
        print ("\n".join (results))

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="""This tool takes a data JSONL in BCDM format and checks whether submission objects are in valid format.  If all-or-nothing flag is not set, 
        only the valid submission objects will be written to stdout.  All error messages should be captured in stderr.  

Usage: cat data_bcdm.jsonl | python acceptability_check.py  --bcdm_def /file/path/field_definitions.tsv --update --all-or-nothing > /file/path/filtered.jsonl 2> /file/path/err.log;
""")
    #parser.add_argument("--username", type=str, required=True, help="Username")
    parser.add_argument("--update", default=False, action=argparse.BooleanOptionalAction, help="If set, record existence is required to proceed with the update. Otherwise, new record submission is requested.")
    parser.add_argument("--bcdm-def", type=str, required=True, help="Path to the BCDM definition file.")
    parser.add_argument("--all-or-nothing", action="store_true", help="True indicates all or nothing mode")
    args = parser.parse_args()
    main(args)