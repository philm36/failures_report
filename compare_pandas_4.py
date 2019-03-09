#!/usr/bin/python3
# Script to read from SAP output csv file using pandas module. Reads five specified
# columns for demand (delivery, del type, ship-to, ISBN, Qty) & three for despatched.
# Skips blank line after headers (1st 3 are skipped by default). Should skip any
# blank lines and also final line (totals).
# Converts the Delivery and ISBN to int64 values from float64, & ship-to to int32
# Performs merge between two files to identify lines not delivered. Adds Diff column
# which contans difference between demand and delivered or, if nothing delivered,
# uses demand qty. Removes any lines delivered where difference is zero.
# V.2  Includes store (ship-to) in demand dataframe. Replaces col name 'Dlv.qty' with
# 'Dlv_qty' & 'Ship-to' with 'Ship_to'. Removes any spaces found in columns names due
# to mis-formed SAP files. Hard-coded lines to exclude by store(s)
# Creates summary file grouping by material and outputs additional summary file
# V.3 Reads csv file (SAP ID should be in column 1) with stores to be excluded which
# needs to be named 'exclusions.csv'
# V.4 Reads files from separate directories. Checks that there is only a single file
# in each directory and then reads that file irrespective of its name. Path to
# directory is hard-coded though. Reads columns by name rather then number

import pandas as pd
import numpy as np
import csv
import os

demand_files=os.listdir('Data/Demand')
despatch_files=os.listdir('Data/Despatch')
#print("Demand files: ",len(demand_files))
#print("Despatch files: ",len(despatch_files))
if len(demand_files) != 1:
    print("There should be one and only one file in Demand directory")
    exit()
elif len(despatch_files) != 1:
    print("There should be one and only one file in Despatch directory")
    exit()

for filename in demand_files:
    print('Demand file: ',filename)
    with open('Data/Demand/'+filename, encoding='utf-16')as f1:
        demand=pd.read_csv(f1,sep='\t',skiprows=[0,1,2,4],skip_blank_lines=True,skipinitialspace=True,usecols=['Delivery','DlvTy','Ship-to','Material','Dlv.qty'],engine='python')

for filename in despatch_files:
    print('Despatch file: ',filename)
    with open('Data/Despatch/'+filename, encoding='utf-16') as f2:
        despatch=pd.read_csv(f2, sep='\t',skiprows=[0,1,2,4],skipfooter=2,skip_blank_lines=True,skipinitialspace=True,usecols=['Reference','Material','Quantity'],engine='python')

print("Demand file has ",demand.shape[0]," lines")
print("Despatch file has ",despatch.shape[0]," lines")

# Replace the '.' and '-' in column names in demand file with '_'
demand.columns=demand.columns.str.replace('-','_')
demand.columns=demand.columns.str.replace('.','_')
#demand.columns=demand.columns.str.replace(' ','')      # Not required with
#despatch.columns=despatch.columns.str.replace(' ','')  # 'skipinitalspace=True'

# Remove any stores that are to be excluded. Needs to be list for multiple stores
# Data read from simple external csv file. If no stores to be excluded or file 
# not found, sets exludes to empty list
excludes=[]
try:
    with open('Data/exclusions.csv') as f3:
        reader=csv.reader(f3, delimiter=',')
        for row in reader:
            excludes.append(row[0])
    print('Exclusion file processed')
except:
    FileNotFoundError
    print('No Exclusions file found.No stores excluded. Filename should be "exclusions.csv"')
demand=demand.query('Ship_to not in @excludes') 

# Remove any lines containing 'NaN' (catch page break at 60k lines)
demand.dropna(inplace=True)
despatch.dropna(inplace=True)
# Change data type from float to int64 but not for ISBN; might not be numeric
demand=demand.astype({'Delivery': np.int64, 'Ship_to': np.int32,'Dlv_qty':np.int32})
despatch=despatch.astype({'Reference': np.int64,'Quantity': np.int32}) 

failures = demand.merge(despatch.drop_duplicates(),how='left',left_on=['Delivery','Material'],right_on=['Reference','Material'],indicator=True)
print('Merge complete. Calculating differences')
# Add extra column to contain difference between demand and delivered qty.
# If there is no delivered qty, populate with demand qty
failures['Diff']=failures.apply(lambda row: row['Dlv_qty'] + row['Quantity'] if row['_merge'] == 'both' else row['Dlv_qty'], axis=1)
# Remove any lines where difference = 0
failures=failures.query('Diff != 0')  ## Comment this line out for full picture in output files

# Write list of failures to external csv file
header=["Delivery","DlvTy","Ship_to","Material","Dlv_qty","Quantity","Diff","_merge"]
#print('Writing full output files')
#failures.to_csv('Output/failures_output_v4.csv', encoding='utf-8', columns=header)
#summary=failures.groupby(['DlvTy','Material'])['Diff'].sum()
#summary.reset_index()[['DlvTy','Material', 'Diff']].to_csv('Output/failures_summary_by_ISBN.csv', encoding='utf-8', index=False)
#print('Writing output files split by Delivery Type')  # Uncomment for full details
#failures.query('DlvTy == "ZLFA"').to_csv('Output/failures_zlfa_output.csv', encoding='utf-8', columns=header)
#failures.query('DlvTy == "ZLFS"').to_csv('Output/failures_zlfs_output.csv', encoding='utf-8', columns=header)

# Create and write output files to be used by analysis scripts
print('Writing output files by ISBN to be used by analysis scripts')
summary1=failures.query('DlvTy == "ZLFA"').groupby(['DlvTy','Material'])['Diff'].sum()
summary1.reset_index()[['DlvTy','Material', 'Diff']].to_csv('Output/failures_zlfa_by_ISBN.csv', encoding='utf-8', index=False)
summary2=failures.query('DlvTy == "ZLFS"').groupby(['DlvTy','Material'])['Diff'].sum()
summary2.reset_index()[['DlvTy','Material', 'Diff']].to_csv('Output/failures_zlfs_by_ISBN.csv', encoding='utf-8', index=False)
