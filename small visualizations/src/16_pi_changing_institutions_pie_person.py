#!/usr/bin/env python
# coding: utf-8

# Last edited on 12/18/2020 by Mara Hubelbank

# PURPOSE: Produce the "PIs and Co-PIs: Changing Institutions, Person-Level" figure.
# INPUT: CSV files for individual awards and jobs.
# OUTPUT: A pie chart representing the individuals (person-level) who changed jobs at least once after receiving an award.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Specify the in- and out- file locations 
inp = '../../data_master/'
outp = '../figures/'

# Specify whether the level is 'role' or 'person'
level = 'person'

df_awards = pd.read_csv(inp + 'individual_awards.csv')
df_jobs = pd.read_csv(inp + 'individual_jobs.csv')

df_jobs = df_jobs[['person_id', 'job_start_year', 'employer_id', 'job_category']]

TITLE = 'PIs and Co-PIs: Changing Institutions,\n' + level.title() + '-Level'
COLORS = ['#648fff', '#fe6100'] # blue (stayed), orange (moved)
TEXT_COLOR = '#404040' # dark gray

# DATASET ---------------------------------------------------------------------------------------------------------

# Filter award role to keep only "pi", "co-pi", "former pi", and "former co-pi"
df_awards = df_awards[(df_awards['award_role'] == "pi") | (df_awards['award_role'] == "co-pi")
                    | (df_awards['award_role'] == "former pi") | (df_awards['award_role'] == "former co-pi")] 

# Drop duplicates based on the given level (person or role)
level_cols = ['person_id'] if level == 'person' else ['person_id', 'award_id']
df_awards = df_awards.drop_duplicates(level_cols)

# Initialize the master dataframe
# Add person_id and award_start_year from awards df
df_master = df_awards[['person_id', 'award_start_year', 'award_role']].copy()

# Add empty column for institution changes
df_master['changed_inst'] = False

# A dictionary representing precedence of job titles
# Order: admin > chair/director > faculty
job_dict = {"admin": 1, "chair/director": 2, "faculty": 3}

# Parse the given job_start_year (a string)
# Return: the year as an int, or None if there is no year in the string
def parse_year_cell(year):
    if (len(year) > 3):
        if (year[0:4].isdigit()): # first 4 characters are numeric
            return int(year[0:4])
        elif (year[-4:].isdigit()): # last 4 characters are numeric
            return int(year[-4:])
    return None # no year found -- set year cell val to None

# Iterate over the job df; clean and parse start year column, and delete rows with invalid job titles
# We dropped 1249 rows here
for i, row in df_jobs.iterrows():
    # Start year 
    year_cell = str(row['job_start_year'])
    # parse the job_start_year cell as an int, or represent as None if there's no year here
    row['job_start_year'] = parse_year_cell(year_cell)
    
    # Job category
    job = str(row['job_category'])
    # drop the trailing director info (ex. "_r")
    if job.startswith("director") or job.startswith("chair"):
        df_jobs.at[i,'job_category'] = "chair/director"
    # if not a valid job, drop this row from the jobs dataframe
    elif (job not in job_dict.keys()): 
        df_jobs = df_jobs.drop([i])
                
# Reset the jobs df's indexes, since we dropped some rows
df_jobs.reset_index(drop=True, inplace=True)

# Iterate over each row of the master and update institution changes
for i, row in df_master.iterrows():
    p_id = row['person_id']
    award_year = row['award_start_year']
            
    # Get sorted job dataframe slice for this id where all years are geq the start year 
    df_slice_years = df_jobs.loc[(df_jobs['person_id'] == p_id) & (df_jobs['job_start_year'] - award_year >= 0)]
    
    # Drop duplicate employer ids -- we don't care if they switched back to a previous employer
    df_slice_years = df_slice_years.drop_duplicates(['employer_id'])

    # We dropped duplicates, so if the length of the slice is greater than 1, then they switched institutions
    if (len(df_slice_years) > 1):
        df_master.loc[i, 'changed_inst'] = True  

# VISUALIZATION ----------------------------------------------------------------------------------------------------

# Create a new dataframe to store the quantities of each subbar
df_q = pd.DataFrame(columns=['name', 'total'])

# Add the quantity of each combination to the quantity dataframe
df_q = df_q.append({'name': 'never moved', 'total': sum(df_master['changed_inst'] == False)},ignore_index=True)
df_q = df_q.append({'name': 'moved at least once', 'total': sum(df_master['changed_inst'] == True)},ignore_index=True)

def format_label(pct, data):
    absolute = int(round(pct/100.*np.sum(data)))
    return str(absolute) + " (" + str(int(round(pct))) + "%)"

ax = plt.gca()
plt.rcParams['font.size'] = 14
texts = ax.pie(df_q['total'], autopct=lambda pct: format_label(pct, df_q['total']), colors=COLORS, startangle=90, wedgeprops=dict(linewidth=3, edgecolor='w'))

# Make the title
ax.set_title(TITLE + " (n=" + str(sum(df_q['total'])) + ")", fontsize=20, color=TEXT_COLOR)

# Make the legend
custom_lines = [Line2D([0], [0], color=c, marker="s", markersize=10, linewidth=0, label=lab) for c, lab in zip(COLORS, df_q['name'])]
leg = plt.legend(handles=custom_lines, loc="center", ncol=2, framealpha=0, bbox_to_anchor=(0.55, -0.05))
for text in leg.get_texts():
    plt.setp(text, color = TEXT_COLOR, fontsize=14)
    
plt.tight_layout()
plt.savefig(outp + 'fig_16_' + level + '.png')