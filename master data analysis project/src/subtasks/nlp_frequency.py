#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Find the k most frequent terms occuring in the given column of the given dataframe
# Input: df, column with category names, column with category terms (ex. job titles), name of category, k
def k_most_freq(df, col_cat, col_terms, cat, k):
    # Get the cells in the given category (with duplicates)
    cat_vals = df.loc[df[col_cat] == cat][col_terms]
    
    # Split each title and add each word to a list if it's not a stop word
    terms = []
    for title in cat_vals:
        for term in title.split():
            term_alnum = ''.join(c for c in term if c.isalnum() or c=='-') # Remove non-alnum characters (spaces, etc.)
            if (not term_alnum in stopwords.words('english')) and term_alnum: # If non-stopword and non-empty
                terms.append(term_alnum)
                
    # Count the k most frequent terms in the job terms list             
    c = Counter(terms)
    return c.most_common(k)

# Input: df, column with category names, column with category terms, list of sorted column values, 
# name of cat col as string, name of term col as string, k (number of terms/bars per category), whether to display
def viz_kmf(df, col_cat, col_terms, cat_vals, k):
        
    n = len(cat_vals) # number of categories
    b = 3 if n < 10 else 4  # number of columns
    a = int(math.ceil(n / b))  # number of rows
    c = 1  # initialize plot counter

    colors = sns.color_palette("hls", n) # get a distinct color for each category

    fig = plt.figure(figsize=(22,16))
    
    # Create title strings from column names 
    cat_str = col_cat.replace('_', " ")
    term_str = col_terms.replace('_', " ")
    if not 'category' in cat_str:
        cat_str = cat_str.replace('cat', "category")

    # We'll also build a string doc representing the numerical data 
    doc = '\nThe ' + str(k) + ' most frequent ' + term_str + ' terms in each ' + cat_str.lower() + ' are:'

    for cat in cat_vals:
        freq = k_most_freq(df, col_cat, col_terms, cat, k)
        n = len(df.loc[df[col_cat] == cat])
        lab = cat + ' (n=' + str(n) + ')'

        # Add this category's k-most frequent terms to the growing doc
        doc += '\n' + lab
        for val in freq:
            doc += ('\n  - ' + val[0] + ': ' + str(val[1]))
            
        # Graph this category as a subplot
        ax = plt.subplot(a, b, c)
        plt.title(lab, fontsize=25)
        ax.tick_params(axis='x', which='major', labelsize=15)
        plt.xlabel('frequency', fontsize=20)

        # If this category doesn't have k values, add in some blank pads
        padded = (freq + [('', 0)] * k)[:k]

        plt.barh(range(k), [val[1] for val in padded], align='center', color=colors[c - 1])
        plt.yticks(range(k), [val[0] for val in padded], fontsize=15 if k < 16 else 12)
        ax.invert_yaxis()  # labels read top-to-bottom

        c = c + 1

    fig.suptitle(str(k) + ' Most Frequent ' + term_str.title() + ' Terms Per ' + cat_str.title(), fontsize=35)
    plt.tight_layout(rect=(0, 0, 1, 0.92), w_pad=1.5, h_pad=2.5)
    plt.savefig('viz_' + col_cat + '_freq.png')
    plt.show()
    return doc

