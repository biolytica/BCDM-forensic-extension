import sys, os
import argparse
import json
import re
import dateparser
from datetime import datetime
import pandas as pd

_ACCEPTED_SUB_TYPES = ['specimen']
_MIN_REQUIRED_FIELDS = {
    'specimen:update': [tuple(['sampleid', 'processid'])],
    'specimen:new':['bold_recordset_code_arr', 'sampleid']
}

PLACEHOLDER_REGEX = {
    "%s": ".+",          # any non-empty string
    "%d": r"\d+",        # integer number
    "%f": r"[-+]?\d*\.?\d+",  # float number
}

def convert_placeholder_to_regex (value, match_empty_string = False):
    regex_str = re.escape(value)  # escape all special characters
    if match_empty_string:
        PLACEHOLDER_REGEX["%s"]=".*"
    for placeholder, replacement in PLACEHOLDER_REGEX.items():
        # replace the escaped placeholder with the regex pattern
        regex_str = regex_str.replace(re.escape(placeholder), replacement)
    return re.compile(regex_str)

def read_mapping (file):
    return pd.read_csv(file, sep='\t') #, index_col="field")

def isvalid_value (value, expected_datatype, expected_dataformat):
    if value == "": return True
    # 1. Type check
    try:
        if expected_datatype == 'string':
            str(value)
        elif expected_datatype in ['int', 'integer']:
            int(value)
        elif expected_datatype in ['float', 'number']:
            float(value)
        elif expected_datatype == ['string:date', 'date']:
            str(value)
            dateparser.parse(value)
        elif expected_datatype == 'char':
            if not isinstance (value, str) or not len(value)==1:
                return False
        elif expected_datatype == 'geopoint':       # TODO: confirm input format
            temp_array = value.split(",")
            if len(temp_array) != 2:
                return False
        elif expected_datatype == 'array':
            value.split(",")
        elif expected_datatype == 'array of string':
            temp_array = value.split(",")
            for val in temp_array:
                str(val)
        elif expected_datatype == 'json':
            json.loads(value)
        
    except Exception as e:
        #print (e, file=sys.stderr)
        return False
        
    # 2. Format check
    
    try: 
        if expected_dataformat != 'default':
            #print (f"Value:{value}; Type:{expected_datatype}; Format:{expected_dataformat} Checking...")
            if expected_datatype =='string:date':
                #blah = dateparser.parse(value, date_formats=[expected_dataformat], settings={'STRICT_PARSING': True})
                parsed_date = datetime.strptime(value, expected_dataformat)
                if parsed_date.strftime(expected_dataformat) != date_str:
                    #print (value, file=sys.stderr)
                    #print (parsed_date, file=sys.stderr)
                    #print (parsed_date.strftime(expected_dataformat), file=sys.stderr)
                    return False

            elif expected_datatype == 'string':
                regex_format = convert_placeholder_to_regex (expected_dataformat)
                if not re.fullmatch(regex_format, value):
                    #print ("WHY", value, expected_dataformat, regex_format)
                    return False
                
    except Exception as e:
        #print (e, file=sys.stderr)
        return False
    return True
            
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
                    msgs.append ( f"[ERROR][Request {json_obj['id']}] Required column {fieldset} is missing or empty")
                    isValid = False
            elif type(fieldset) == tuple:
                if not set (fieldset) & set (json_obj['submission_packet'].keys()) or \
                all(json_obj['submission_packet'].get(f) in (None, "") for f in fieldset):
                    msgs.append (f"[ERROR][Request {json_obj['id']}] At least 1 of the following columns {','.join (fieldset)} is required")
                    isValid = False

    # data model validator
    submitted_fields = json_obj['submission_packet'].keys()
    #print ("[DEBUG] submitted_fields: ", submitted_fields)
    
    invalid_fields = [ field for field in submitted_fields if (bcdm_mapping['field'] != field).all() ]

    if len(invalid_fields) > 0:
        print (f"[WARNING][Request {json_obj['id']}] Invalid fields found ", invalid_fields, file = sys.stderr)
        #TODO: confirm with Sujeevan filter out bad fields?  Or throw an error? 

    # TODO: datatype chexk against mapping
    invalid_fields = []
    for bcdm_field in json_obj['submission_packet']:
        if json_obj['submission_packet'][bcdm_field] and (bcdm_mapping['field'] == bcdm_field).any():    # only if data submitted and also valid fields
            #print (f"[DEBUG] Check type for {bcdm_field}")
            row = bcdm_mapping[bcdm_mapping['field']== bcdm_field].iloc[0]
            if not isvalid_value (json_obj['submission_packet'][bcdm_field], row['data_type'], row['data_format']):
                print (f"[DEBUG] Bad type for {bcdm_field}; value:{json_obj['submission_packet'][bcdm_field]}; type:{row['data_type']}; format:{row['data_format']}", file=sys.stderr)
                invalid_fields.append (bcdm_field)
    if len(invalid_fields)>0:
        isValid = False
        msgs.append (f"[ERROR][Request {json_obj['id']}] Invalid data type/format for {len(invalid_fields)} fields: {','.join (invalid_fields)}")
    return isValid, msgs

def main(args):
    error_count = 0

    # Validate params
    if not os.path.exists(args.bcdm_def):
        print ( f"[ABORT] Mapping file path not found: {args.bcdm_def}", file=sys.stderr)
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