# failures_report
Python scripts to create report from csv/xls files
This contains four Python scripts. These should be placed in a directory together with one other
directory named 'Data'. This contains three other directories which are:
1) Demand (containing a single file taken from SAP WM of demand as at day one);
2. Despatch (containing a singel file shwoing stokc despatched at the end of day one);
3) Stock_LX03 (stockholding file taken from SAP first thing on day two)
Also, directory Data contains files 'exclusions.csv' (containign any stores that are to be excluded
from the report - eg are stock builds for new stoes where stock is not being despatched) and
'email_list.csv' (containing a list of email addresses to be used by the final script)

Process:
Step 1 - Run compare_pandas_4.py
 Read demand file and despatch file, compare,and create list of stock with demand but
 not despatched.
a) read both files
b) compare on line by line basis for matches of delivery AND material number.
   If there is no match, line needs to be recorded as a failure.
   If they match, compare the demand quantity with the despatched quantity:
   i) if they match, line can be ignored;
   ii) if the demand quantity exceeds the despatch quantity, record difference as failure
c) Take file of failures and consolidate by ISBN and qty. Produce separate output file for
   both ZLFA & ZLFA

Step 2 - run analysis_zlfs_2.2.py & analysis_zlfa_2.2.py
 a) Read stock file
 b) Trim out any lines not required (specific storage types that are not relevant)
 c) Read failures file from step 1 and compare failures file with stock file
 d )Apply analysis to consolidated file of failures and stock. Analysis to works in reverse
 order across storage types (ie OPD, open tote, picked to chute end, in location*, in putaway,
 in Goods In, in Prob Res areas)
 e) Create piechart using matplotlib and save as pdf file, plus csv file for background data for
 both zlfa and zlfs streams (four files in total)

Step 3 - run email_final_plus.py
Reads email_list.csv, creates email with attachments from step2(e), request password and send email.
