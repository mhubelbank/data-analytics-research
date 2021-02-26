#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Get the year and job of the given person when they first entered the ADVANCE network (via the first grant they worked on)
# Input: an individual's id, the year of the person's first grant they worked on, and the institution of their first grant
# Return the first job and first year in the network of the given person
def get_first_job(p_id, year, e_id):
    # Get the jobs for this p_id at the given e_id where all job years are leq the award start year
    jobs_slice = ind_jobs.loc[(ind_jobs['person_id'] == p_id)
                              & (ind_jobs['job_start_year'] - year <= 0)
                              & (ind_jobs['job_end_year'] - year >= 0)
                              & (ind_jobs['employer_id'] == e_id)].sort_values(by = 'job_start_year') 
    ind = -1
    # We're getting the job they had when they entered the network (start of grant)
    # So we want the closest job they had to the start year of the grant
    
    # If there are no jobs found which started on or before the grant start year, get the first job at the institution    
    if len(jobs_slice) == 0:                
        jobs_slice = ind_jobs.loc[(ind_jobs['person_id'] == p_id)
                                  & (ind_jobs['employer_id'] == e_id)].sort_values(by = 'job_start_year')
        ind = 0 # First job
       
        # If there are no jobs at the first award institution, find the closest (<=) job to the first award's start year
        if len(jobs_slice) == 0:
            jobs_slice = ind_jobs.loc[(ind_jobs['person_id'] == p_id)
                                      & (ind_jobs['job_start_year'] - year <= 0)
                                      & (ind_jobs['job_end_year'] - year >= 0)].sort_values(by = 'job_start_year') 
            ind = -1 # Last row has closest job 
                    # If still no jobs, return NaN
    
            # If there are no jobs <= the award start year, just get the highest job for this person
            if len(jobs_slice) == 0:
                jobs_slice = get_jobs(p_id)
                                
                # If there are still no jobs, return NaN
                if (len(jobs_slice) == 0):
                    return (np.nan, np.nan)
                
                else: # This person has at least one job; get the highest one
                    jobs_list = jobs_slice['job_category'].drop_duplicates().to_list()
                    jobs_list = [x for x in jobs_list if str(x) != 'nan']
                    highest_title = get_highest_title(jobs_list)
                    # We assume that they entered the ADVANCE network in the grant start year
                    return (highest_title, year)
       
    # Ascending order --> take either the jobs in the first year or the last one (if need leq closest to award year)
    first_year_in_ADVANCE = jobs_slice['job_start_year'][jobs_slice.index[ind]]

    # Get all rows in the dataframe slice that contain the first year
    jobs_first_year_slice = jobs_slice.loc[ind_jobs['job_start_year'] == first_year_in_ADVANCE]

    # Find the highest position of all the first-year jobs
    jobs_list = jobs_first_year_slice['job_category'].drop_duplicates().to_list()
    jobs_list = [x for x in jobs_list if str(x) != 'nan']
    highest_title = get_highest_title(jobs_list)
    return (highest_title, first_year_in_ADVANCE)

# Get the job of the given person after they entered the ADVANCE network (via the first grant they worked on)
# Input: an individual's id, the year of the person's first grant they worked on, and (optionally) an employer id to filter by
def get_highest_job(p_id, e_id=True):
  
    first_year_in_advance = log_individual_jobs.loc[log_individual_jobs['person_id'] == p_id, 
                                                    'first_year_in_advance'].iloc[0]
    
    # First, get the jobs they had at their award institutions after entering the ADVANCE network
    if e_id: # If e_id=True then no filtering by employer id
        inst = get_awards(p_id)['award_org_id'].unique()
        jobs = ind_jobs[(ind_jobs['person_id'] == p_id) 
                        & (ind_jobs['job_start_year'] >= first_year_in_advance)
                        & (ind_jobs['employer_id'].isin(inst))]
    else:
        jobs = ind_jobs[(ind_jobs['person_id'] == p_id) & (ind_jobs['employer_id'] == e_id)]
    
    # If there are none, then just get the jobs they had after they entered the ADVANCE network 
    if len(jobs) == 0:
        jobs = ind_jobs[(ind_jobs['person_id'] == p_id) & (ind_jobs['job_start_year'] >= first_year_in_advance)]
        
        # If they have no jobs after entering the network, then just get the highest job that this person ever had
        if len(jobs) == 0:
            jobs = ind_jobs[ind_jobs['person_id'] == p_id]
            
            # If still no jobs, return NaN
            if len(jobs) == 0: 
                return np.nan
    
    jobs_list = jobs['job_category'].drop_duplicates().to_list()
    jobs_list = [x for x in jobs_list if str(x) != 'nan']
    return get_highest_title(jobs_list)

# Get the most recent job of the given individual, or the highest most recent in the case of ties
# Input: an individual's id, and (optionally) a max year to filter by
def get_last_job(p_id, year=3000):
    jobs_slice = get_jobs(p_id)
    if len(jobs_slice) == 0:
        return np.nan
    jobs_slice_leq = jobs_slice[jobs_slice['job_start_year'] <= year].copy()
    if len(jobs_slice_leq) > 0:
        jobs_slice = jobs_slice_leq
    last_start_year = jobs_slice['job_start_year'][jobs_slice.index[-1]]
    jobs_last_start_year = jobs_slice.loc[ind_jobs['job_start_year'] == last_start_year].sort_values('job_end_year')
    jobs_list = jobs_last_start_year['job_category'].drop_duplicates().to_list()
    jobs_list = [x for x in jobs_list if str(x) != 'nan']
    return get_highest_title(jobs_list)   

ties = 0
doc_tie = ''

# Determine the most relevant positions for each category.
for i, row in log_individual_jobs.iterrows():
    p_id = row['person_id']
    awards_slice = get_awards(p_id)
    
    # Ascending order --> first row has year and institution of the first award this person worked on
    ind_first = awards_slice.index[0]
    year_first = awards_slice['award_start_year'][ind_first]
    
    # If individuals started at two different grants in the same years, pick the one where they had the highest role
    awards_year_first = awards_slice.loc[awards_slice['award_start_year'] == year_first].copy()
    awards_year_first.drop_duplicates('award_org_id', inplace=True)
    if len(awards_year_first) > 1:
        awards_year_first['award_role_cat'] = awards_year_first['award_role_cat'].map(role_dict).argsort()
        e_id_first = awards_year_first['award_org_id'][awards_year_first.index[-1]]
        # doc_tie += 'Person ' + str(p_id) + '\'s highest role was at org ' + str(e_id_first) + '\n'
        ties += 1
    else: 
        e_id_first = awards_slice['award_org_id'][ind_first]
    
    # Get the highest first position at the first institution, and the first year in the network
    tup_first = get_first_job(p_id, int(year_first), e_id_first)
        
    log_individual_jobs.loc[i, 'first_year_in_advance'] = tup_first[1]
    log_individual_jobs.loc[i, 'first_job'] = tup_first[0]
    log_individual_jobs.loc[i, 'highest_job'] = get_highest_job(p_id, year_first)
    log_individual_jobs.loc[i, 'last_job'] = get_last_job(p_id)

