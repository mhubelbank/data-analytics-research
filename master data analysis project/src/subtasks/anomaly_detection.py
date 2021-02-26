#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Determine whether the given employer id corresponds to a university based on a multileveled categorical definition.
def is_uni(emp_id):
    if pd.isna(emp_id):
        out('NaN employer')
        return False
        
    # If the employer is not in our list of organizations, return false.
    if not emp_id in orgs['org_id'].unique():
        out(str(emp_id) + ' is not in the organizations CSV')
        return False
    
    # Get the row corresponding to the given id in the organizations df
    org = orgs[orgs['org_id'] == emp_id].iloc[0]
    name = org['org_name'].lower() 
    
    # If the org has a Carnegie ID, then it is a US university 
    if not pd.isna(org['carnegie_id']):
        # out(name + ' has a Carnegie ID, so it\'s a US uni')
        return True
    
    # For non-US universities, we have keywords that we look for in the org's name
    keys = ['university', 'college', 'school', 'universitat', 'universidad', 'ecole']
            
    # We also have keys for non-unis that contain our uni keys, so we check for these first
    # Ex. "Cambridge Public Schools"
    antikeys = ['colleges', 'schools', 'association']    
    if any(x in name for x in antikeys):
        # out(name + ' contains an antikey, so it is not a uni')
        return False
    
    if any(x in name for x in keys):
        # out(name + ' contains a uni key, so it\'s a non-US uni')
        return True
    
    # The most tricky term seems to be "institute", as it can be either a non-uni or a uni term.
    # From manual review, we can see three institutes which are universities; these are marked here.
    if 'institute' in name and ('india' in name or 'stockholm' in name):
        # out(name + ' contains \'institute\' so it may or may not be a uni')
        return True
    
    # Else the org is not a US or non-US uni; return False
    # out(name + ' is not a uni')
    return False

us_unis = 0 # Count of US universities
for i, row in orgs.iterrows():
    orgs.loc[i, 'is_uni'] = is_uni(row['org_id'])
    us_unis += 1 if not pd.isna(row['carnegie_id']) else 0
    
print('\nThe employers for the below positions are not presently marked as universities, so their categories will be set to non-uni.')

# We add to the report each non-university which has at least one employee with a university-labeled position.
def mark_non_uni_jobs():
    body_uni = ''
    # If a job position is NOT marked as non-uni AND the corresponding employer is NOT a uni (by our definition)
    # Then there is an error -- the job should be marked as non-uni, since the employer is not a university.
    for i, row in orgs.iterrows():
        if row['is_uni'] == False:
            employees = ind_jobs[(ind_jobs['employer_id'] == row['org_id']) 
                                & (ind_jobs['job_category'] != 'non-uni')]
            if (len(employees) != 0):
                body_uni += '\n' + str(int(row['org_id'])) + ': ' + row['org_name']
                for i, row in employees.iterrows():
                    body_uni += '\n - ' + str(int(row['person_id'])) + ' had uni position: ' + row['job_category']
                    ind_jobs.loc[(ind_jobs['person_id']==row['person_id'])
                                 & (ind_jobs['job_title']==row['job_title'])
                                 & (ind_jobs['employer_id'] == row['employer_id']), 'job_category'] = 'non-uni'
    return body_uni

before = len(ind_jobs[ind_jobs['job_category']=='non-uni'])
body_uni = mark_non_uni_jobs()
after = len(ind_jobs[ind_jobs['job_category']=='non-uni'])
print('Number of jobs newly set to non-uni: ' + str(after-before))
print(body_uni)

# Look for date issues (Title at institution prior to their recorded employment start year, etc.).
for i, row_job in ind_jobs.iterrows():
    # row_job['job_category'] == 'director_d'
    job_start = row_job['job_start_year']
    if job_start == 0:
        continue
    title = row_job['job_title'].lower()
    if (title.endswith('advance') or 'advance ' in title) and 'director' in title:
        valid_director_job = False
        awards_slice = get_awards(row_job['person_id'])
        for i, row_award in awards_slice.iterrows():
            if job_start >= row_award['award_start_year']:
                valid_director_job = True
        if not valid_director_job:
            award_year = awards_slice['award_start_year'][awards_slice.index[0]]
            award_org = str(int(awards_slice['award_org_id'][awards_slice.index[0]]))
            title = title[:60] + '...' if len(title) > 60 else title
            out('Person ' + str(row_job['person_id'])
                  + ' has a job as \"' + title
                  + '\" which starts in year ' + str(int(job_start)) + '.')
            out('> Their first award started in ' + str(int(award_year)) + ' at org ' + award_org + '.')

# Use k-most-freq algorithm defined in nlp_frequency script
freq_dict = {cat: k_most_freq(ind_jobs, 'job_category', 'job_title', cat, 15) for cat in job_cats_task}
keys_dict = {'admin': ['chief', 'ceo'],
             'director_a': [],
             'chair': ['chairman'],
             'director_c': [],
             'director_r': [],
             'director_d': [],
             'faculty': ['lecturer', 'scientist', 'instructor'],
             'staff': ['research', 'researcher', 'advisor'],
             'postdoc': ['postdoc']}

antikeys_dict = {'admin': ['advisor', 'liaison'],
             'director_a': ['advisor', 'liaison'],
             'chair': [],
             'director_c': [],
             'director_r': [],
             'director_d': [],
             'faculty': [],
             'staff': [],
             'postdoc': []}

# For each category, we output the job titles which contain neither the 15 most frequent terms in their assigned category 
# nor any of the manually defined category keys. This also points to some misspelled job titles, such as "profesor".
for cat in job_cats_task:
    keys = [tup[0] for tup in freq_dict[cat]]
    keys = keys + keys_dict[cat]
    antikeys = antikeys_dict[cat]
    cat_slice = ind_jobs.loc[ind_jobs['job_category'] == cat]
    
    out('\nJob titles which may not fit in category ' + cat + ': ')
    for i, row in cat_slice.iterrows():
        terms = re.split(',|, |_|-| |:|/', row['job_title']) 
        if (not any(term in keys for term in terms)) or any(term in antikeys for term in terms):
            out('Person ' + str(int(row['person_id'])) + ': ' + row['job_title'])

