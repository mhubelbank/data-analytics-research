#!/usr/bin/env python
# coding: utf-8

# In[4]:


# Last edited on 11/18/2020 by Mara Hubelbank

# PURPOSE: Produce the "Network by discipline, gender, race/ethnicity and type of position" figure dataset.
# INPUT: CSV files for individual awards, individual jobs, and individual demographics.
# OUTPUT: One CSV file merging the person id, award year, job catgegory, race-ethnicity, gender, and division columns. 

import pandas as pd
import numpy as np
import functools

# Read in awards CSV
df_awards = pd.read_csv('../../data_master/individual_awards.csv')

# Filter out internal evaluators and day-to-day from awards df
# We removed 128 IEs and 122 D2Ds here
df_awards = df_awards[df_awards['award_role_cat'] != "internal evaluator"] 
df_awards = df_awards[df_awards['award_role_cat'] != "day-to-day"] 

# Drop duplicates of the same person for the same award
df_awards = df_awards.drop_duplicates(['person_id','award_id'])

# Initialize the master dataframe
# Add person_id and award_start_year from awards df, and empty job column
df_master = df_awards[['person_id', 'award_start_year']].copy()
df_master['job_category'] = np.nan

# Reset the master df's indexes, since we dropped some rows
df_master.reset_index(drop=True, inplace=True)

# Read in jobs and demographics CSVs, and get necessary columns.
df_jobs = pd.read_csv('../../data_master/individual_jobs.csv')
df_jobs = df_jobs[['person_id', 'job_start_year', 'job_category']]

df_dems = pd.read_csv('../../data_master/individual_demographics.csv')
df_dems = df_dems[['person_id', 'race_ethnicity_urm', 'gender', 'division']]

# Filter out divisions to keep only science, social science, and engineering
# We dropped 111 rows here (medicine or other)
df_dems = df_dems[(df_dems['division'] == 'science')
                 | (df_dems['division'] == 'social science')
                 | (df_dems['division'] == 'engineering')]

# A dictionary representing precedence of job titles
# Order: admin > director > staff > chair > faculty > non-uni
job_dict = {"admin": 1, "director": 2, "staff": 3, "chair": 4, "faculty": 5, "non-uni": 6}

# A comparator for job titles
# Return: -1 if job1 < job2, 0 if =, 1 if job1 > job2
def job_comparator(job1, job2):
    if job_dict[job1] < job_dict[job2]:
        return -1
    elif job_dict[job1] > job_dict[job2]:
        return 1
    else:
        return 0

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
for i, row in df_jobs.iterrows():
    # Start year 
    year_cell = str(row['job_start_year'])
    # parse the job_start_year cell as an int, or represent as None if there's no year here
    row['job_start_year'] = parse_year_cell(year_cell)
    
    # Job category
    job = str(row['job_category'])
    # drop the trailing director info (ex. "_r")
    if job.startswith("director"):
        df_jobs.at[i,'job_category'] = "director"
    # if not a valid job, drop this row from the jobs dataframe
    elif (job not in job_dict.keys()): 
        df_jobs = df_jobs.drop([i])
        # we removed 29 rows here
    
# Reset the df indexes, since we dropped some rows
df_jobs.reset_index(drop=True, inplace=True)

# NEW: Keep only the first award for each person.
# We do this after the award years have been parsed to ints.
df_master = df_master.loc[df_master.groupby('person_id')['award_start_year'].idxmin()]

# Given a list of job titles, sort by custom precedence list and return the highest job title
# Return: the highest job title in the given list (a string)
def get_highest_title(job_list):
     # Sort the list using our custom precedence dictionary and job_comparator
    job_list.sort(key=functools.cmp_to_key(job_comparator))
    
    # Sorted in descending order -- return first
    if (len(job_list) > 0):
        return job_list[0] 
    else:
        return None
    
# Slice the job df by the given id and award year
# Return: the job title corresponding to the year closest to the given award year
def get_closest_title_from_year_slice(p_id, year):
    # Get sorted dataframe slice for this id where all years are leq the start year in the award year dictionary
    df_slice_years = df_jobs.loc[(df_jobs['person_id'] == p_id) 
                                 & (df_jobs['job_start_year'] - year <= 0)].sort_values(by = 'job_start_year') 
        
    # If there are no years found, just get the highest corresponding title for this person from the jobs df
    if (len(df_slice_years) == 0):
        all_jobs_list = df_jobs.loc[(df_jobs['person_id'] == p_id)]['job_category'].to_list()
        highest_title = get_highest_title(all_jobs_list)
        return highest_title

    # Else: there are years found, so find the year closest to given year in the sorted-by-year slice
    else:
        # Ascending order --> last row has closest year
        year_closest = df_slice_years['job_start_year'][df_slice_years.index[-1]]

        # Get all rows in the dataframe slice that contain the closest year
        df_slice_last_year = df_slice_years.loc[df_jobs['job_start_year'] == year_closest]
        
        # If there's only one row corresponding to the closest job year, return its job
        if (len(df_slice_last_year) == 1):
            job_closest = df_slice_years['job_category'][df_slice_years.index[-1]]
            return job_closest
        
        # Else, there are multiples of the closest year to the given award year, so get the highest title
        else:
            closest_year_jobs_list = df_slice_last_year['job_category'].drop_duplicates().to_list()
            highest_title = get_highest_title(closest_year_jobs_list)
            return highest_title    

# Iterate over the df to get most pertinent jobs for each award year
for i, row in df_master.iterrows():
    p_id = row['person_id']
    award_year = row['award_start_year']
    
    # Get the closest corresponding job title to this award year and person id
    job_closest = get_closest_title_from_year_slice(p_id, award_year)

    # Update the master df with the most pertinent job found
    df_master.loc[i, 'job_category'] = job_closest
    
# Merge the demographic data into the master dataframe
df_master = pd.merge(df_master, df_dems, on = 'person_id')

# NEW: Drop the rows where the person doesn't have any of these columns filled
df_master.replace('', float("NaN"), inplace=True) 
df_master.dropna(how='any', inplace=True)

# Save our master df to a CSV file
df_master.to_csv('../output/figure_1_data.csv', index=False)

