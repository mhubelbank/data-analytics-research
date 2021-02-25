#!/usr/bin/env python
# coding: utf-8

# Last edited on 12/18/2020 by Mara Hubelbank

# PURPOSE: Produce the "PIs and Co-PIs Moving to Another IT Site by Position and Gender, Person-Level" figure.
# INPUT: CSV files for awards and organizations, and Syed's job mobility and pinpointed job CSVs.
# OUTPUT: A bar chart representing the IT award-receiving individuals (person-level) 
# who moved out of one IT institution and into another, categorized by position and gender.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Specify the in- and out- file locations 
inp = '../../data_master/' # master datasets
inp_prc = '../../org_network/output/' # processed datasets
outp = '../figures/'

# Specify whether the level is 'role' or 'person'
level = 'person'

df_awards = pd.read_csv(inp + 'individual_awards.csv')
df_org = pd.read_csv(inp + 'organizations.csv')
df_mobility = pd.read_csv('../../org_network/output/' + '01_02_01_job_mobility_edges_after_advance.csv')
df_jobs = pd.read_csv('../output/' + 'eda_01_03_01_individual_awards_with_pinpointed_job_and_demographic.csv')

TITLE = 'PIs and Co-PIs Moving to Another IT Site by Position and Gender,\n' + level.title() + '-Level'
COLORS = ['#1A85FF', '#D41159'] # blue (men), red (women)
GRID_COLOR = '#d9d9d8' # light gray
TEXT_COLOR = '#404040' # dark gray

# DATASET ---------------------------------------------------------------------------------------------------------

# Filter to keep organizations that received an it award
df_org = df_org[(df_org['org_type_based_on_awards'] == 'it and non-it') 
                | (df_org['org_type_based_on_awards'] == 'it only')]

# Filter award role to keep only "pi", "co-pi", "former pi", and "former co-pi"
df_awards = df_awards[(df_awards['award_role'] == "pi") | (df_awards['award_role'] == "co-pi")
                    | (df_awards['award_role'] == "former pi") | (df_awards['award_role'] == "former co-pi")] 

# Filter to keep individuals (in mobility file) for whom both institutions (to and from) are it award-receiving
df_mobility = df_mobility[['person_or_awards_involved_id', 'from_org_id', 'to_org_id']]
df_mobility.rename(columns={'person_or_awards_involved_id':'person_id'}, inplace=True)
org_strs = df_org['org_id']
def it_org_filt(row):
    return (row['from_org_id'] in org_strs.values) & (row['to_org_id'] in org_strs.values)
df_mobility = df_mobility[df_mobility.apply(it_org_filt, axis=1)]

# Merge to keep only individuals who received an it award
df_awards = df_awards[['person_id', 'award_id', 'award_type']]
df_awards = df_awards[df_awards['award_type'] == "it"] 
df_master = pd.merge(df_mobility, df_awards, on = 'person_id')

# Add in the job category, race, and gender of each person
df_jobs = df_jobs[['person_id', 'job_category', 'race_ethnicity_URM', 'gender']]

job_dict = {"admin": 1, "chair/director": 2, "faculty": 3}
for i, row in df_jobs.iterrows():
    job = str(row['job_category'])
    # drop the trailing director info (ex. "_r")
    if job.startswith("director") or job.startswith("chair"):
        df_jobs.at[i,'job_category'] = "chair/director"
    # if not a valid job, drop this row from the jobs dataframe
    elif (job not in job_dict.keys()): 
        df_jobs = df_jobs.drop([i])

df_master = pd.merge(df_master, df_jobs, on = 'person_id', how='left')

# Drop duplicates based on the given level (person or role) and rows with nan values
level_cols = ['person_id'] if level == 'person' else ['person_id', 'award_id']
df_master = df_master.drop_duplicates(level_cols)
df_master.dropna(how='any', inplace=True)
df_master.reset_index(drop=True, inplace=True)

# VISUALIZATION ----------------------------------------------------------------------------------------------------

# Create a new dataframe to store the quantities of each subbar
df_q = pd.DataFrame(columns=['job_category', 'man', 'woman'])

# Get the size of the intersection of the three given parameters
def get_q(job, gender):
    return len(df_master[(df_master['job_category'] == job) 
                         & (df_master['gender'] == gender)])

# Filter nan values 
def no_nans(elem):
    return str(elem) != 'nan'

# Get unique job categories
jobs = df_master['job_category'].unique() 
jobs = sorted(list(filter(no_nans, jobs)))

# Get unique genders
genders = df_master['gender'].unique() 
genders = sorted(list(filter(no_nans, genders)))

# Add the quantity of each combination to the quantity dataframe
for job in jobs:
    df_q = df_q.append({'job_category': job}, ignore_index=True)
    for gender in genders:
        df_q.loc[df_q['job_category'] == job, [gender]] = get_q(job, gender)

# For clearer visualization, set heirarchical index.
df_q_h = df_q.set_index(['job_category'])

# Some constants for the bar chart
NUM_X = len(jobs) * len(genders)
BAR_WIDTH = 0.5 # width of each bar

# Get the bar values for the given job category and gender as an array (percentages, raw)
def get_vals(job): 
    men_raw = df_q_h.loc[job, 'man']
    women_raw = df_q_h.loc[job, 'woman']
    sum_raw = men_raw + women_raw
    cum_sums.append(sum_raw) 
    
    if (sum_raw != 0):
        men_perc = round(men_raw * 100 / sum_raw)
        women_perc = round(women_raw * 100 / sum_raw)
        return np.array([men_raw, women_raw, men_perc, women_perc])
    return np.array([0, 0, 0, 0])

# Plot a bar with the given values
def plot_bar(index, values):
    values_raw = values[:2]
    values_perc = values[2:]
    indices = [index, index + 0.75]
    for ind, perc, raw, color in zip(indices, values_perc, values_raw, COLORS):
        plt.bar(ind, raw, color=color, width=BAR_WIDTH)
        plt.text(ind, raw, str(perc) + '%', ha="center", va="bottom", fontsize=18)
        
plt.figure(figsize=(NUM_X * 2, 6.5)) # size of bar chart figure

x = np.arange(1.625, 5.5, 1.75)

cum_sums = []
job_N_dict = {}
i = 1.25
for job in jobs:
    values = get_vals(job)
    plot_bar(i, values)
    i += 1.75

# Get the axis attribute.
ax = plt.gca()

# Title the graph, calculating the sum of cumulative sums.        
total = str(sum(cum_sums))
plt.title(TITLE + ' (n=' + total + ')', fontsize=24, pad=25, color=TEXT_COLOR)

jobs = [job.title() for job in jobs]
# Label the bars on x-axis with the gender names
plt.xticks(x, jobs, fontsize=18, color=TEXT_COLOR)

# Label the y-axis with percentages
y_vals = np.arange(0, max(cum_sums)+2, 2)
y_labels = [str(y) for y in y_vals] # min 0%, max 100%, step 10%
plt.yticks(y_vals, y_labels, fontsize=18, color=TEXT_COLOR) # y-ticks (min, max, step)

# Add the horizontal grid lines and remove the top and side borders.
plt.grid(color=GRID_COLOR, which='major', axis='y', linestyle='solid', linewidth=2)
ax.set_axisbelow(True)
ax.spines['bottom'].set_color(GRID_COLOR)
ax.spines['top'].set_color('none')
ax.spines['left'].set_color('none')
ax.spines['right'].set_color('none')

# Make the legend (bottom center).
l_labels = ['men', 'women']
custom_lines = [Line2D([0], [0], color=c, marker="s", markersize=10, linewidth=0, label=lab) for c, lab in zip(COLORS, l_labels)]
leg = ax.legend(handles=custom_lines, loc='upper center', bbox_to_anchor=(0.5, -0.16), ncol=len(l_labels), framealpha=0, prop={'size': 16})
for text in leg.get_texts():
    plt.setp(text, color = TEXT_COLOR, fontsize=18)
    
plt.tight_layout(pad=1.5)
plt.savefig(outp + 'fig_20_' + level + '.png')