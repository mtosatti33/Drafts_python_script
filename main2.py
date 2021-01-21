import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import requests
from bs4 import BeautifulSoup

years = range(1970, 2021)

def extract_player_data(table_rows):
    """
    Extract and return the the desired information from the td elements within
    the table rows.
    """
    # create the empty list to store the player data
    player_data = []

    for row in table_rows:  # for each row do the following

        # Get the text for each table data (td) element in the row
        # Some player names end with ' HOF', if they do, get the text excluding
        # those last 4 characters,
        # otherwise get all the text data from the table data
        player_list = [td.get_text()[:-4] if td.get_text().endswith(" HOF")
                       else td.get_text() for td in row.find_all(["th", "td"])]

        # there are some empty table rows, which are the repeated
        # column headers in the table
        # we skip over those rows and and continue the for loop
        if not player_list:
            continue

        # Extracting the player links
        # Instead of a list we create a dictionary, this way we can easily
        # match the player name with their pfr url
        # For all "a" elements in the row, get the text
        # NOTE: Same " HOF" text issue as the player_list above
        links_dict = {(link.get_text()[:-4]   # exclude the last 4 characters
                       if link.get_text().endswith(" HOF")  # if they are " HOF"
                       # else get all text, set thet as the dictionary key 
                       # and set the url as the value
                       else link.get_text()) : link["href"] 
                       for link in row.find_all("a", href=True)}

        # The data we want from the dictionary can be extracted using the
        # player's name, which returns us their pfr url, and "College Stats"
        # which returns us their college stats page
    
        # add the link associated to the player's pro-football-reference page, 
        # or en empty string if there is no link
        player_list.append(links_dict.get(player_list[3], ""))

        # add the link for the player's college stats or an empty string
        # if ther is no link
        player_list.append(links_dict.get("College Stats", ""))

        # Now append the data to list of data
        player_data.append(player_list)

    return player_data

# Create an empty list that will contain all the dataframes
# (one dataframe for each draft)
draft_dfs_list = []

# a list to store any errors that may come up while scraping
errors_list = []

# The url template that we pass in the draft year inro
url_template = "http://www.pro-football-reference.com/years/{year}/draft.htm"

# for each year from 1970 to (and including) 2016
for year in years:

    # Use try/except block to catch and inspect any urls that cause an error
    try:
        # get the draft url
        url = url_template.format(year=year)

        # get the html
        html = requests.get(url).text

        # create the BeautifulSoup object
        soup = BeautifulSoup(html, "lxml") 

        # get the column headers
        column_headers = [th.getText() for th in 
                          soup.findAll('tr', limit=2)[1].findAll('th')]
        column_headers.extend(["Player_NFL_Link", "Player_NCAA_Link"])

        # select the data from the table using the '#drafts tr' CSS selector
        table_rows = soup.select("#drafts tr")[2:] 

        # extract the player data from the table rows
        player_data = extract_player_data(table_rows)

        # create the dataframe for the current years draft
        year_df = pd.DataFrame(player_data, columns=column_headers)

        # if it is a draft from before 1994 then add a Tkl column at the 
        # 24th position
        if year < 1994:
            year_df.insert(24, "Solo", "")

        # add the year of the draft to the dataframe
        year_df.insert(0, "Draft_Yr", year)

        # append the current dataframe to the list of dataframes
        draft_dfs_list.append(year_df)
    
    except Exception as e:
        # Store the url and the error it causes in a list
        error =[url, e] 
        # then append it to the list of errors
        errors_list.append(error)

# store all drafts in one DataFrame
draft_df = pd.concat(draft_dfs_list, ignore_index=True)

# get the current column headers from the dataframe as a list
column_headers = draft_df.columns.tolist()

# The 5th column header is an empty string, but represesents player names
column_headers[4] = "Player"

# Prepend "Rush_" for the columns that represent rushing stats 
column_headers[19:22] = ["Rush_" + col for col in column_headers[19:22]]

# Prepend "Rec_" for the columns that reperesent receiving stats
column_headers[23:25] = ["Rec_" + col for col in column_headers[23:25]]

# Properly label the defensive int column as "Def_Int"
column_headers[-6] = "Def_Int"

# Just use "College" as the column header represent player's colleger or univ
column_headers[-4] = "College"

# Now assign edited columns to the DataFrame
draft_df.columns = column_headers

draft_df.to_csv("pfr_nfl_draft_data_RAW.csv", index=False)