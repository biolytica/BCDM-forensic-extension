import argparse
import json, sys, os, csv

import pandas as pd

########## Helper Functions ##########

def get_verbatim_mapping (mapping_verbatim_to_bold):
    return pd.read_csv(mapping_verbatim_to_bold, sep="\t")  # columns: bcdm_field, bold_field
    
def get_verbatim_mapping_OLD (mapping_verbatim_to_bold, mapping_bcdm_to_bold):
    df1 = pd.read_csv(mapping_verbatim_to_bold, sep="\t")  # columns: bcdm_field, bold_field
    df2 = pd.read_csv(mapping_bcdm_to_bold, sep="\t")  # columns: bold_field, verbatim_field

    merged_df = pd.merge(df1, df2, on="bold_field", how="left")
    return merged_df

def modify_update_obj (update_json, mapping_DF, mode = "add"):
    verbatim_db_mapping = {}
    for bcdm_field in update_json.keys():
        #print (f"In function modify_update_obj for field {bcdm_field}")
        live_db_table_name = update_json[bcdm_field][0]['db_table'].split("__")[0]
        live_db_field_name = update_json[bcdm_field][0]['db_field'].split("__")[0]
        
        lookup_bold_field = live_db_table_name+'.'+live_db_field_name
        if (mapping_DF['bold_field'] == lookup_bold_field).any():
            #print (f"\t\tFound bold_field in mapping{lookup_bold_field}")
            row = mapping_DF.loc[mapping_DF['bold_field']== lookup_bold_field].iloc[0].to_dict()
            verbatim_table = row['verbatim_field'].split(".")[0]
            verbatim_field = row['verbatim_field'].split(".")[1]
        
            if mode == 'add':
                update_json[bcdm_field].append ({'db_table': verbatim_table, 'db_field': verbatim_field, 'value': update_json[bcdm_field][0]['value']})
            else: #Replace 
                update_json[bcdm_field][0]['db_table']=verbatim_table
                update_json[bcdm_field][0]['db_field']=verbatim_field

                
def main(args):

    if not os.path.exists(args.mapping_verbatim):
        print ( f"[ABORT] Mapping file path not found: {args.mapping_verbatim}", file=sys.stderr)
        sys.exit (1)

    # Input Submission Processing (ALL or NOTHING)
    excluded_fields = ['record_id']
    vebatim_to_bold_mapping_DF = get_verbatim_mapping (args.mapping_verbatim) #get_verbatim_mapping (args.mapping_verbatim, args.mapping)

    results =[]
    for line in sys.stdin:
        update_obj = json.loads(line.strip("\n"))
        try:
            modify_update_obj (update_obj, vebatim_to_bold_mapping_DF, args.mode)
            
            if args.all_or_nothing:
                results.append (json.dumps(update_obj))
            else:
                print (json.dumps(update_obj))
            
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
    parser.add_argument("--mapping-verbatim", type=str, required=True, help="File path for the verbatim to BOLD DB field mapping")
    parser.add_argument("--mode", type = str, required=False, choices = ["add", "replace"], default="add")
    parser.add_argument("--all-or-nothing", action="store_true", help="True indicates all or nothing mode")
    args = parser.parse_args()
 
    main(args)
