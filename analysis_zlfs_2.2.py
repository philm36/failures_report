#!/usr/bin/python3
# Script to read from SAP output csv file using pandas.read_csv 
# This version reads single LX03 file and is for ZLFS demand
# Uses pd.read_csv to check and read only a single file in directory 'Stock_LX03'
# Read only columns Material, SLoc, Typ, StorageBin, Avail_st, & Lst_plcmnt by name
# Tidies Headers, removes line for zero avail stock and drops NaN
# Removes line for storage type TIN, TIO, MPB & TCR. 
# Excludes storage bins (Inbound & 50 for ZLFS; 1-24 & CELL 201 to 228 for ZLFA)
# Applies dictionary to group storage types as Mezz, OpenTote etc
# Reads failures file produced by 'compare' script and merges files. Applies custom
# sort (916,OPD,Open_tote,Chute-end,Mezz,MPR,PBS,FM,FP,Putaway,Inbound,999,923,HP,
# NoStock). Analyses merged data to identify failures against stock 
# Outputs a stock summary file then applies plotly to produce graphical html output
#
# NOTE - it initially failed on straight SAP files but is OK on a file opened and
# saved as a Unicode csv file. Corrupt data was cause - title contained single "
# V 2.2 uses matplotlib rather than plotly and writes output as pdf

import pandas as pd
import os
import matplotlib.pyplot as plt

csv_files = os.listdir('Data/Stock_LX03')
if len(csv_files) != 1:
    print("There should be one and only one file in Stock_LX03 directory")
    exit()

stock=pd.DataFrame()
for filename in csv_files:
    print('Stock file name: ',filename)
    with open('Data/Stock_LX03/'+filename, encoding='utf-16') as f:
        stock=pd.read_csv(
            f,sep='\t',skip_blank_lines=True,skipinitialspace=True,
            usecols=['Material','SLoc','Typ','StorageBin','Avail.st','Lst.plcmnt'],
            skiprows=[0,1,2,3,5],index_col=None,thousands=',',
            quoting=3,engine='python')

print('Reading of stock file complete')
print("File has ", stock.shape[0]," lines")

# Replace the '.' in column names in demand file with '_'
stock.columns=stock.columns.str.replace('.','_')
#stock.columns=stock.columns.str.replace(' ','')
# Remove any lines containing 'NaN'
stock.dropna(inplace=True)

stock=stock.query('Avail_st != 0')
print("Zero quantities removed. File has ",len(stock)," rows")
#stock.to_csv('Output/output_zlfs_2.1-0.csv', encoding='utf-8')

# Change data type to numeric for Avail.st
stock["Avail_st"]=pd.to_numeric(stock.Avail_st,errors='coerce')
print("Header names cleaned. Avail Stk values numeric")
print("File has ",len(stock)," rows")

# Code to remove unwanted storage types and bins
remove_type=['TIN','TCR','TIO','MPB']
stock=stock[stock['Typ'].isin(remove_type)==False]
print('Unwanted storage types removed')

# Remove unwanted Storage Bins depending on order type
# Remove 1-24 and CELL* for ZLFA
# Remove bin 50 and Inbound for ZLFS
excludes=['INBOUND','50']
stock=stock.query('StorageBin not in @excludes')
print('Inbound and bin 50 removed')
#stock.to_csv('Output/output_zlfs_2.1-1.csv', encoding='utf-8')
print("File has ",len(stock)," rows")

# Reduce storage types to groups 
# Define a dictionary to group storage types
storage={
    '916':'916','OPD':'OPD',
    '201':'Open_tote','202':'Open_tote','203':'Open_tote','204':'Open_tote',
    '205':'Open_tote','206':'Open_tote','207':'Open_tote','208':'Open_tote',
    '209':'Open_tote','210':'Open_tote','211':'Open_tote','212':'Open_tote',
    '213':'Open_tote','214':'Open_tote','215':'Open_tote','216':'Open_tote',
    '217':'Open_tote','218':'Open_tote','219':'Open_tote','220':'Open_tote',
    '221':'Open_tote','222':'Open_tote','223':'Open_tote','224':'Open_tote',
    '225':'Open_tote','226':'Open_tote','227':'Open_tote','228':'Open_tote',
    '1':'Chute-end','MS':'Mezz','MSX':'Mezz','MIX':'Mezz','MP':'Mezz','MPR':'MPR',
    'PB1':'PBS','PB2':'PBS','PB3':'PBS','PB4':'PBS','FM':'FM','FP':'FP',
    'P&D':'Putaway','BPD':'Putaway',
    '600':'Inbound','601':'Inbound','603':'Inbound','604':'Inbound','609':'Inbound',
    '999':'999','923':'923'}

# Insert extra column and fill with value from dict based on str type
stock['Str_Area']=stock['Typ'].map(storage)
print('Creating summary file and writing output')
summary=stock.groupby(['Material','Str_Area'],as_index=False)['Avail_st'].agg('sum')

# Open and read the failures_summary file
print('Reading failures files')
try:
    with open('Output/failures_zlfs_by_ISBN.csv') as f2:
        failures_zlfs=pd.read_csv(f2,usecols=[1,2],engine='python')
except:
    FileNotFoundError
    print('No Failures file found. Run "compare" script to create one')
    exit()
print("File read complete")
print("ZLFS file has ", failures_zlfs.shape[0]," lines")

print("Merge starting")
# Try to merge the stock summary above with the failures file
dtype={'Material':str}
analysis=failures_zlfs.astype(dtype).merge(summary.astype(dtype),how='left',indicator=True) 

# Define custom sort order
sort_order=['916','OPD','Open_tote','Chute-end',
    'Mezz', 'MPR','PBS','FM','FP',
    'Putaway','Inbound','999','923','HP','NoStock']

# Perform custom sort
analysis['Str_Area']=pd.Categorical(analysis['Str_Area'],sort_order)
analysis=analysis.sort_values(['_merge','Material','Str_Area'])
analysis=analysis.reset_index(drop=True)

# Create additional column for net outstanding quantity
analysis["Net"] = ""
for n in range(0,len(analysis)):
    if analysis.iat[n,4] == 'both':
        if analysis.iat[n,0]==analysis.iat[n-1,0]:
            analysis.iat[n,1]=analysis.iat[n-1,1]-analysis.iat[n-1,5]
        if analysis.iat[n,1] > analysis.iat[n,3]:
            analysis.iat[n,5] = analysis.iat[n,3]
            if analysis.iat[n,0]!=analysis.iat[n+1,0]:
                add=[analysis.iat[n,0],analysis.iat[n,1]-analysis.iat[n,5],'NoStock',
                    '','left_only',analysis.iat[n,1]-analysis.iat[n,5]]
                s=pd.Series(add,index=analysis.columns)
                analysis=analysis.append(s,ignore_index=True)
                print('Line appended for line ',n,' : ',analysis.iat[n,0])
        else:
            analysis.iat[n,5] = analysis.iat[n,1]
    else:
        analysis.iat[n,5]=analysis.iat[n,1]
        analysis.iat[n,2]='NoStock'

print('Full output file being produced')
# Remove lines where 'Diff' has been reduced to zero
analysis.query('Diff != 0').to_csv('Output/full_analysis_output_zlfs_2.2.csv', encoding='utf-8')

# Create file for graphical outpuut
summary=analysis.groupby(['Str_Area'])['Net'].sum().reset_index()

#print('Data ouput file used by matlplotlib tests being produced')
#summary.reset_index()[['Str_Area','Net']].to_csv('Output/analysis_zlfs_out_final_2.2.csv', encoding='utf-8')

print('Cleaning data for graphical output')
#summary=summary.query('Net != 0')
summary=summary.query('Net > 0')
summary['Str_Area']=pd.Categorical(summary['Str_Area'],sort_order)
summary=summary.sort_values(['Str_Area'])
summary=summary.reset_index(drop=True)

# Add new column to use as label concatenating Str_Area and Qty
summary['label'] = ''
for n in range(0,len(summary)):
    summary.iat[n,2]=summary.iat[n,0]+str(" : ")+str(int(summary.iat[n,1]))

# Create lists for labels and values in pie chart
labels=summary['Str_Area'].tolist()
legend_tags=summary['label'].tolist()
values=summary['Net'].tolist()

print('Producing pie chart')
# Create plot with matplotlib
fig, ax = plt.subplots(figsize=(8,12), subplot_kw=dict(aspect='equal'))

wedges, texts, autotexts = ax.pie(values, autopct="%1.1f%%", startangle=90,
    counterclock=False, labels=labels, rotatelabels=False,
    pctdistance=0.9, labeldistance=1.05)
    #, textprops=dict(color="k"))

# Create legend and set title
ax.legend(wedges, legend_tags, title="Failures by Area & Qty",
    loc='upper center', bbox_to_anchor=(0.5,0,0,0))
ax.set_title("Failures for ZLFS by Area")

plt.setp(autotexts, size=8)
plt.savefig('Output/piechart_zlfs.pdf')#,bbox_inches='tight')
print('Output produced at "Output/piechart_zlfs.pdf"')
plt.close(fig)
