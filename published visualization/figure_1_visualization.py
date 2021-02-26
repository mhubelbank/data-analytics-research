#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Last edited on 11/18/2020 by Mara Hubelbank

# PURPOSE: Produce the "Network by discipline, gender, race/ethnicity and type of position" figure.
# INPUT: One CSV file merging the person id, award year, job catgegory, race-ethnicity, gender, and division columns. 
# OUTPUT: A stacked bar graph (the purpose figure).

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import math

df = pd.read_csv('../output/figure_1_data.csv')
N = len(df)

# Create a new dataframe to store the quantities of each subbar.
df_q = pd.DataFrame(columns=['job category', 'asian men', 'asian women', 'urm men', 'urm women', 'white men', 'white women'])

# Get the size of the intersection of the four given parameters.
def get_q(division, job, race, gender):
    return len(df[(df['division'] == division) & (df['job_category'] == job)
                  & (df['race_ethnicity_urm'] == race) & (df['gender'] == gender)])

# Merge a list of divisions into one (replace with third arg)
def merge(dframe, old_divs, new_div):
    dframe.replace(old_divs, new_div, inplace=True)
    
# Filter nan values 
def no_nans(elem):
    return str(elem) != 'nan'

# Merge medicine and others, since those are our two smallest divisions
merge(df, ['medicine', 'other'], 'other')

# NEW: Drop the 'other' division
df = df[df['division'] != 'other']

# Get unique divisions
divs = df['division'].unique() 
divs = list(filter(no_nans, divs))
sum_divs = {div:len(df[df['division']==div]) for div in divs}

# Get unique job categories
jobs = df['job_category'].unique() 
jobs = list(filter(no_nans, jobs))

# Add the quantity of each combination to the quantity dataframe
for div in divs:
    for job in jobs:
        df_q = df_q.append({'division': div, 'job category': job, 
                            'asian men': get_q(div, job, 'asian', 'man'),
                            'asian women': get_q(div, job, 'asian', 'woman'),
                            'urm men': get_q(div, job, 'urms', 'man'),
                            'urm women': get_q(div, job, 'urms', 'woman'),
                            'white men': get_q(div, job, 'white', 'man'),
                            'white women': get_q(div, job, 'white', 'woman')}, ignore_index=True)

# For clearer visualization, set heirarchical index.
df_q_h = df_q.set_index(['division', 'job category'])

# Some constants for the bar chart
STACKED_BAR_CHART_INDIVIDUAL_COLORS = ["#CC79A7","#D55E00","#0072B2","#E69F00","#56B4E9","#009E73"] #to make color blind friendly, previous: ["#243473", "#ee7d2f", "#a5a4a4", "#fcc011", "#5c9ad3", "#70ad46"]
NUM_X = len(divs) * len(jobs)
BAR_WIDTH = 0.6 # width of each bar
GRID_COLOR = '#d9d9d8' # light gray

# Get the bar values for the given division and job category as an array
def get_vals(div, job): 
    asian_men = df_q_h.loc[(div, job)]['asian men']
    asian_women = df_q_h.loc[(div, job)]['asian women']
    urm_men = df_q_h.loc[(div, job)]['urm men']
    urm_women = df_q_h.loc[(div, job)]['urm women']
    white_men = df_q_h.loc[(div, job)]['white men']
    white_women = df_q_h.loc[(div, job)]['white women']
    return np.array([asian_men, asian_women, urm_men, urm_women, white_men, white_women])

# Plot a bar with the given values
def plot_bar(index, values):    
    indices = np.repeat(index,repeats=len(values)) 
    cumsum_bottom_values = np.concatenate([np.zeros(1), np.cumsum(values)[:-1]], axis=0)     
    for ind, value, bottom, color in zip(indices, values, cumsum_bottom_values, STACKED_BAR_CHART_INDIVIDUAL_COLORS):
        plt.bar(ind, value, bottom=bottom, color=color, width=BAR_WIDTH)
    cum_sums.append(np.cumsum(values)[-1]) # get this bar's cumulative sum
    
plt.figure(figsize=((NUM_X + 4)/1.15,9/1.15)) # size of bar chart figure

x = np.arange(0.5, NUM_X * 1.25, 1.25)

cum_sums = []
i = 0.5
for div in divs:
    for job in jobs:
        values = get_vals(div, job)
        plot_bar(i, values)
        i += 1.25        

# Get the axis attribute.
ax = plt.gca()

# Title the graph, calculating the sum of cumulative sums.        
total = str(N)
N_comma = total[:1] + "," + total[1:]
#plt.title('Individuals by Field, Gender, Race/Ethnicity, and Type of Position, 2020 (n=' + N_comma + ')', 
#          fontsize=30, fontweight='demibold', pad=20)

# Label the bars on x-axis with the job category names.
labels = [(job + "\n(n=" + str(cs) + ")") for job, cs in zip(df_q['job category'].str.title(), cum_sums)]
plt.xticks(x, labels, fontsize=15.5)

# Secondary x-axis label level with division.
x_2 = [.225, .5, .78]
def div_label(div):
    n = sum_divs[div]
    t = sum(sum_divs.values())
    div_title = div.title() + ('s' if div[-1] == 'e' else '')
    return "\n" + "\n" + div_title + "\n" + str(round(n*100/t)) + "% (n=" + str(n) + ")"
x_labels_2 = [plt.figtext(x, 0.11, div_label(div), ha='center', fontsize=15.5) for x, div in zip(x_2, divs)]

# Add lines separating the divisions.
x_line = np.arange(7.375, 13*1.25, 6*1.25)
for x in x_line:
    line = Line2D([x, x], [-48, 0], lw=1.5, color=GRID_COLOR)
    line.set_clip_on(False)
    ax.add_line(line)

# Label the y-axis
y_step = 20
y_max = y_step * (math.ceil((max(cum_sums)) / y_step)) + y_step # round up to nearest step
plt.yticks(np.arange(0, y_max, y_step),fontsize=18) # y-ticks (min, max, step)

# Add the horizontal grid lines and remove the top and side borders.
plt.grid(color=GRID_COLOR, which='major', axis='y', linestyle='solid', linewidth=2)
ax.set_axisbelow(True)
ax.spines['bottom'].set_color(GRID_COLOR)
ax.spines['top'].set_color('none')
ax.spines['left'].set_color('none')
ax.spines['right'].set_color('none')

# Make the legend (bottom center).
labels = ['Asian Men', 'Asian Women', 'URM Men', 'URM Women', 'White Men', 'White Women']
custom_lines = [Line2D([0], [0], color=c, marker="s", markersize=10, linewidth=0, label=lab) for c, lab in zip(STACKED_BAR_CHART_INDIVIDUAL_COLORS, labels)]
ax.legend(handles=custom_lines, loc='upper center', bbox_to_anchor=(0.5, -0.23), ncol=len(labels), framealpha=0,prop={'size': 15.5})

plt.tight_layout()
plt.savefig('../figures/figure_1_color_blind_friendly.png')

