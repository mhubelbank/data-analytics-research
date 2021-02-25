#!/usr/bin/env python
# coding: utf-8

# Last edited on 12/18/2020 by Mara Hubelbank

# PURPOSE: Produce the "PIs and Co‐PIs Changing Institutions by Position and Gender, Person-Level" figure.
# INPUT: CSV files for individual awards, jobs, and demographics.
# OUTPUT: A bar chart representing the individuals (person-level) who changed jobs at least once after receiving an award,
# categorized by position and gender.

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
df_dems = pd.read_csv(inp + 'individual_demographics.csv')
df_jobs = pd.read_csv(inp + 'individual_jobs.csv')

df_dems = df_dems[['person_id', 'gender']]
df_jobs = df_jobs[['person_id', 'job_start_year', 'employer_id', 'job_category']]

TITLE = 'PIs and Co‐PIs Changing Institutions by Position and Gender,\n' + level.title() + '-Level'
COLORS = ['#648fff', '#fe6100'] # blue (stayed), orange (moved)
GRID_COLOR = '#d9d9d8' # light gray
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

# add the gender column by merging in demographic column (inner join since we can't count unspecified gender ids)
df_master = pd.merge(df_master, df_dems, on = 'person_id')

# Add empty columns for job changes and institution changes
df_master['job'] = np.nan
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
    df_slice_years = df_jobs.loc[(df_jobs['person_id'] == p_id) 
                                 & (df_jobs['job_start_year'] - award_year >= 0)].sort_values(by = 'job_start_year') 
    
    # Only update the row if there is at least one institution change
    if (len(df_slice_years) == 0):
        continue
        
    # Drop duplicate employer ids -- we don't care if they switched back to a previous employer
    df_slice_years = df_slice_years.drop_duplicates(['employer_id'])
    
    # Map the jobs to their ranked values
    df_slice_years['job_category'] = df_slice_years['job_category'].map(job_dict)

    # We dropped duplicates, so if the length of the slice is greater than 1, then they switched institutions
    if (len(df_slice_years) > 1):
        df_master.loc[i, 'changed_inst'] = True  
            
    # Group by the award years and get the corresponding highest job category for the first award
    group_years = df_slice_years.groupby('job_start_year')['job_category'].min()    
    reversed_dict = {value : key for (key, value) in job_dict.items()} # Reverse the job dict
    job = reversed_dict[int(group_years.iloc[0])]
    df_master.loc[i, 'job'] = job     
    
# Drop NaN jobs
df_master = df_master[df_master['job'].notna()]

# VISUALIZATION ----------------------------------------------------------------------------------------------------

# Create a new dataframe to store the quantities of each subbar
df_q = pd.DataFrame(columns=['job_category', 'gender', 'stayed_at_inst', 'changed_inst'])

# Get the size of the intersection of the three given parameters
def get_q(job, gender, changed_inst,):
    return len(df_master[(df_master['job'] == job) 
                         & (df_master['gender'] == gender) 
                         & (df_master['changed_inst'] == changed_inst)])

# Filter nan values 
def no_nans(elem):
    return str(elem) != 'nan'

# Get unique job categories
jobs = df_master['job'].unique() 
jobs = sorted(list(filter(no_nans, jobs)))

# Get unique genders
genders = df_master['gender'].unique() 
genders = sorted(list(filter(no_nans, genders)))

# Add the quantity of each combination to the quantity dataframe
for job in jobs:
    for gender in genders:
        df_q = df_q.append({'job_category': job, 'gender': gender,
                            'stayed_at_inst': get_q(job, gender, False),
                            'changed_inst': get_q(job, gender, True)}, ignore_index=True)

# For clearer visualization, set heirarchical index.
df_q_h = df_q.set_index(['job_category', 'gender'])

# Some constants for the bar chart
NUM_X = len(jobs) * len(genders)
BAR_WIDTH = 0.5 # width of each bar

# Get the bar values for the given job category and gender as an array (percentages, raw)
def get_vals(job, gender): 
    stayed_raw = df_q_h.loc[(job, gender)]['stayed_at_inst']
    changed_raw = df_q_h.loc[(job, gender)]['changed_inst']
    sum_raw = stayed_raw + changed_raw
    cum_sums.append(sum_raw) 
    
    if (sum_raw != 0):
        stayed_at_inst = round(stayed_raw * 100 / sum_raw)
        changed_inst = round(changed_raw * 100 / sum_raw)
        return np.array([stayed_at_inst, changed_inst, stayed_raw, changed_raw])
    return np.array([0, 0, 0, 0])

# Plot a bar with the given values
def plot_bar(index, values):
    values_perc = values[:2]
    values_raw = values[2:]
    indices = np.repeat(index,repeats=len(values)) 
    cumsum_bottom_values = np.concatenate([np.zeros(1), np.cumsum(values)[:-1]], axis=0)     
    for ind, perc, raw, bottom, color in zip(indices, values_perc, values_raw, cumsum_bottom_values, COLORS):
        plt.bar(ind, perc, bottom=bottom, color=color, width=BAR_WIDTH)
        plt.text(ind, bottom+perc/2, raw, ha="center", va="center", fontsize=18)

plt.figure(figsize=(NUM_X * 2, 7.5)) # size of bar chart figure

x = np.arange(0.5, NUM_X * 1.5, 1.5)

cum_sums = []
job_N_dict = {}
i = 0.5
for job in jobs:
    for gender in genders:
        values = get_vals(job, gender)
        plot_bar(i, values)
        i += 1.5     
        
# Get the axis attribute.
ax = plt.gca()

# Title the graph, calculating the sum of cumulative sums.        
total = str(sum(cum_sums))
plt.title(TITLE + ' (n=' + total + ')', fontsize=24, pad=15, color=TEXT_COLOR)

# Label the bars on x-axis with the gender names
gend_dict = {'woman': 'women', 'man': 'men'}
x_labels_1 = [gender for gender in df_q['gender'].map(gend_dict)]
plt.xticks(x, x_labels_1, fontsize=18, color=TEXT_COLOR)

# Second x-axis label level: job category counts
x_2 = [0.22, 0.53, 0.843]
labels = [plt.figtext(x, 0.18, label.title(), ha='center', fontsize=18, color=TEXT_COLOR) for x, label in zip(x_2, jobs)]

# Add vertical lines separating the divisions.
x_line = np.arange(2.75, 6, 3)
for x in x_line:
    line = Line2D([x, x], [-25, 0], lw=1.5, color=GRID_COLOR)
    line.set_clip_on(False)
    ax.add_line(line)

# Label the y-axis with percentages
y_vals = np.arange(0, 110, 10)
y_labels = [(str(y) + '%') for y in y_vals] # min 0%, max 100%, step 10%
plt.yticks(y_vals, y_labels, fontsize=16, color=TEXT_COLOR) # y-ticks (min, max, step)

# Add the horizontal grid lines and remove the top and side borders.
plt.grid(color=GRID_COLOR, which='major', axis='y', linestyle='solid', linewidth=2)
ax.set_axisbelow(True)
ax.spines['bottom'].set_color(GRID_COLOR)
ax.spines['top'].set_color('none')
ax.spines['left'].set_color('none')
ax.spines['right'].set_color('none')

# Make the legend (bottom center).
l_labels = ['stayed', 'moved']
custom_lines = [Line2D([0], [0], color=c, marker="s", markersize=10, linewidth=0, label=lab) for c, lab in zip(COLORS, l_labels)]
leg = ax.legend(handles=custom_lines, loc='upper center', bbox_to_anchor=(0.5, -0.23), ncol=len(l_labels), framealpha=0, prop={'size': 16})
for text in leg.get_texts():
    plt.setp(text, color = TEXT_COLOR, fontsize=18)
    
plt.tight_layout(pad=2)
plt.savefig(outp + 'fig_17_' + level + '.png')