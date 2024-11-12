import os

import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

import numpy as np

import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup

from datetime import datetime, time
import time
import pytz

import requests

import gspread




class scrape_w:

    def __init__(self):

        # # Find OS
        # ## (*was using for filepaths and saving, but the methodology used below should be platform agnostic (at least for mac, windows)*)
        # self.os_var = "windows" if os.name == "nt" else "mac" if os.name == "posix" else None


        # Define the project directories
        project_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.data_base_dir = os.path.join(project_base_dir, "data")
        self.metadata_base_dir = os.path.join(self.data_base_dir, "metadata")

        ## Create the full path to the metadata files
        self.fb_md_fp = os.path.join(self.metadata_base_dir, "football_data.csv")
        self.nba_md_fp = os.path.join(self.metadata_base_dir, "nba_team_abbr.csv")
        self.nhl_md_fp = os.path.join(self.metadata_base_dir, "nhl_team_abbr.csv")
        self.nfl_md_fp = os.path.join(self.metadata_base_dir, "nfl_espn_team_abbr.csv")

        ## FPs for each destination folder
        self.fb_folder_path = os.path.join(self.data_base_dir, "fb")  # Create the path to the fb folder within data_base_dir
        self.nba_folder_path = os.path.join(self.data_base_dir, "nba")  # Create the path to the nba folder within data_base_dir
        self.nhl_folder_path = os.path.join(self.data_base_dir, "nhl")  # Create the path to the nhl folder within data_base_dir
        self.nfl_folder_path = os.path.join(self.data_base_dir, "nfl")  # Create the path to the nfl folder within data_base_dir
        self.master_future_folder_path = os.path.join(self.data_base_dir, "master_future")


        ## misc. vars
        self.chrome_driver_path = os.getenv('chrome_driver_path') # # Get the ChromeDriver path from your environment variable
        self.today_str = datetime.now().strftime("%Y_%m_%d") # # Get today's date in the desired format
        self.today = pd.Timestamp.today().date()



    ##############################################################################################################
    # Begin scrapers

    #######################################################
    # Begin master scraper
    ## General scraper to be invoked in user code
    def scrape(self, subject: list):

        # Define allowed values
        allowed_subjects = {"fb", "nba", "nhl", "nfl"}
        
        # Check if all items in subject are in the allowed subjects
        if not all(item in allowed_subjects for item in subject):
            raise ValueError(f"Subject list can only contain: {', '.join(allowed_subjects)}")

        # Perform scraping based on the contents of subject
        for item in subject:
            if item == "fb":
                self.scrape_fb()
            elif item == "nba":
                self.scrape_nba()
            elif item == "nhl":
                self.scrape_nhl()
            elif item == "nfl":
                self.scrape_nfl()


    
    # End master scraper
    #######################################################



    ## Method for each speciifc subject (to be invoked by the general scraper)

    #######################################################
    # Begin FB
    def scrape_fb(self):
        fb_md = pd.read_csv(self.fb_md_fp)

        # Convert metadata to dictionary
        team_url_dict = fb_md.set_index('team')['url'].to_dict()
        team_url_dict = {team: url + 'matches/' for team, url in team_url_dict.items()} # Amend each URL by adding 'matches/' at the end


        for fb_team, fb_url in team_url_dict.items():

            df_team_fixtures = self.retrieve_fb_schedule(fb_team, fb_url)

            ## Add to master df
            if 'df_fb_master' in locals():
                df_fb_master = pd.concat([df_fb_master, df_team_fixtures], ignore_index=True)
            else:
                df_fb_master = df_team_fixtures.copy()

        ## Save the df
        # Create the full path for the CSV file
        fb_file_name = f"df_fb_scrape_{self.today_str}.csv"
        fb_file_path = os.path.join(self.fb_folder_path, fb_file_name)

        # Save the DataFrame
        df_fb_master.to_csv(fb_file_path, index=False)


    # Get the schedule via selenium
    def retrieve_fb_schedule(self, fb_team, fb_url):
        try:

            # Setup WebDriver
            service = Service(self.chrome_driver_path)  # Use the path from environment variable
            driver = webdriver.Chrome(service=service)

            # Open the page
            driver.get(fb_url)
            
            # Wait until the cookie popup is present and clickable
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Reject All']"))
            ).click()

            # Now proceed with your scraping task
            ## Use BeautifulSoup to parse the page source once the page is fully loaded
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Find the table and extract data as before
            table = soup.find_all('table', class_='matches')
            dates = [row.text for row in table[0].find_all('td', class_="full-date")]
            leagues = [row.text.strip() for row in table[0].find_all('td', class_="competition")]
            homes = [row.text.strip() for row in table[0].find_all('td', class_="team")[::2]]
            aways = [row.text.strip() for row in table[0].find_all('td', class_="team")[1::2]]
            times = [row.text.strip() for row in table[0].find_all('td', class_="score-time")]

            # Create dataframes
            df_team_fixtures = pd.DataFrame(
                {
                    'Team': fb_team,
                    'Date': dates,
                    'League': leagues,
                    'Home Team': homes,
                    'Time': times,
                    'Away Team': aways
                }
            )

            return df_team_fixtures


        except TimeoutException:
            driver.quit()
            print(f"Timed out waiting for cookie pop-up or other elements for {fb_team} at {fb_url}")
            
        finally:
            # Close the browser
            driver.quit()

    # End FB
    #######################################################



    #######################################################
    # Begin NBA
    def scrape_nba(self):

        self.nba_md = pd.read_csv(self.nba_md_fp)

        for nba_team in self.nba_md['abbr']:
            
            # Scrape
            nba_team_sch = self.retrieve_nba_schedule(nba_team)

            # Check for dataframe
            if 'df_nba_master' in locals():
                df_nba_master = pd.concat([df_nba_master, nba_team_sch], ignore_index=True)
            else:
                df_nba_master = nba_team_sch.copy()

            # Pause for n seconds to address HTTPError: HTTP Error 429: Too Many Requests
            time.sleep(4)


        ## Save the df
        # Create the full path for the CSV file
        nba_file_name = f"df_nba_scrape_{self.today_str}.csv"
        nba_file_path = os.path.join(self.nba_folder_path, nba_file_name)

        # Save the DataFrame
        df_nba_master.to_csv(nba_file_path, index=False)



    # Get the schedule from nba ref
    def retrieve_nba_schedule(self, nba_team_abbr):

        self.nba_url = f"https://www.basketball-reference.com/teams/{nba_team_abbr}/2025_games.html"

        headers = {
            "User-Agent": "YourAppName/1.0 (https://yourwebsite.com; contact@yourwebsite.com)"
        }

        # Send a GET request to the URL
        response = requests.get(self.nba_url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            time.sleep(4) # if successful, wait n secs before reading in the html
            dfs_list = pd.read_html(self.nba_url)

            # Prep data
            drop_cols = ['Unnamed: 3','Unnamed: 4']
            col_mapping = {
                'Unnamed: 5': 'Home/Away',
                'Unnamed: 7': 'Result',
                'Unnamed: 8': 'OT'
            }

            # Organize
            df = pd.concat(dfs_list, ignore_index=True).drop(columns=drop_cols).rename(columns=col_mapping)
            df['Home/Away'] = df['Home/Away'].fillna("vs.")
            df = df[df['Date'] != 'Date'].reset_index(drop=True)
            df['computer_date'] = pd.to_datetime(df['Date'], format='%a, %b %d, %Y')
            df['user_team'] = self.nba_md['team'][self.nba_md['abbr'] == nba_team_abbr].iloc[0]
            
            # Create new cols from fns
            df['game_type'] = np.where(df['Notes'] == 'In-Season Tournament', 'In-Season Tournament', 'Regular Season') # Apply conditional update to game_type column

            return df
        
        else:
            print(f"Error retrieving data for {nba_team_abbr}")

    # End NBA
    #######################################################




    #######################################################
    # Begin NHL
    def scrape_nhl(self):

        self.nhl_md = pd.read_csv(self.nhl_md_fp)

        for nhl_team in self.nhl_md['abbr']:
            
            # Scrape
            nhl_team_sch = self.retrieve_nhl_schedule(nhl_team)

            # Check for dataframe
            if 'df_nhl_master' in locals():
                df_nhl_master = pd.concat([df_nhl_master, nhl_team_sch], ignore_index=True)
            else:
                df_nhl_master = nhl_team_sch.copy()

            # Pause for n seconds to address HTTPError: HTTP Error 429: Too Many Requests
            time.sleep(4)


        ## Save the df
        # Create the full path for the CSV file
        nhl_file_name = f"df_nhl_scrape_{self.today_str}.csv"
        nhl_file_path = os.path.join(self.nhl_folder_path, nhl_file_name)

        # Save the DataFrame
        df_nhl_master.to_csv(nhl_file_path, index=False)


    # Get the schedule from nhl ref
    def retrieve_nhl_schedule(self, nhl_team_abbr):

        self.nhl_url = f"https://www.hockey-reference.com/teams/{nhl_team_abbr}/2025_games.html"

        headers = {
            "User-Agent": "YourAppName/1.0 (https://yourwebsite.com; contact@yourwebsite.com)"
        }

        # Send a GET request to the URL
        response = requests.get(self.nhl_url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            time.sleep(4) # if successful, wait n secs before reading in the html
            dfs_list = pd.read_html(self.nhl_url)

            # Prep data
            col_mapping = {
                'Unnamed: 3': 'Home/Away',
                'Unnamed: 7': 'Result',
                'Unnamed: 8': 'OT'
            }

            # Organize
            df = pd.concat(dfs_list, ignore_index=True).rename(columns=col_mapping)
            df['Home/Away'] = df['Home/Away'].fillna("vs.")
            df = df[df['Date'] != 'Date'].reset_index(drop=True)
            df['computer_date'] = pd.to_datetime(df['Date'])
            df['Date'] = df['computer_date'].dt.strftime('%a, %b %d, %Y')
            df['user_team'] = self.nhl_md['team'][self.nhl_md['abbr'] == nhl_team_abbr].iloc[0]
            df['game_type'] = 'Regular Season'
            
            return df
        
        else:
            print(f"Error retrieving data for {nhl_team_abbr}")

    # End NHL
    #######################################################




    #######################################################
    # Begin NFL
    def scrape_nfl(self):

        self.nfl_md = pd.read_csv(self.nfl_md_fp)

        for nfl_team in self.nfl_md['abbr']:
            
            # Scrape
            nfl_team_sch = self.retrieve_nfl_schedule(nfl_team)

            # Check for dataframe
            if 'df_nfl_master' in locals():
                df_nfl_master = pd.concat([df_nfl_master, nfl_team_sch], ignore_index=True)
            else:
                df_nfl_master = nfl_team_sch.copy()

            # Pause for n seconds to address HTTPError: HTTP Error 429: Too Many Requests
            time.sleep(4)


        ## Save the df
        # Create the full path for the CSV file
        nfl_file_name = f"df_nfl_scrape_{self.today_str}.csv"
        nfl_file_path = os.path.join(self.nfl_folder_path, nfl_file_name)

        # Save the DataFrame
        df_nfl_master.to_csv(nfl_file_path, index=False)


    # Get the schedule from nfl ref
    def retrieve_nfl_schedule(self, nfl_team_abbr):

        # URL of the website
        nfl_url = f"https://www.espn.com/nfl/team/schedule/_/name/{nfl_team_abbr}"

        headers = {
            "User-Agent": "YourAppName/1.0 (https://yourwebsite.com; contact@yourwebsite.com)"
        }

        # Send a GET request to the URL
        response = requests.get(nfl_url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            time.sleep(4) # if successful, wait n secs before reading in the html
            df = pd.read_html(nfl_url)[0]

            # Find the index of the row that starts with "WK", "DATE", etc.
            start_row = df[(df[0] == "WK") & (df[1] == "DATE") & (df[2] == "OPPONENT") & (df[3] == "TIME")].index[0]

            # Find the index of the row that starts with "Preseason"
            end_row = df[df[0] == "Preseason"].index[0]

            # Select rows between the start and end rows, and set the start_row as the header
            df = df.iloc[(start_row-1) + 1:end_row].reset_index(drop=True)  # +1 to exclude the header row from the data
            df.columns = df.iloc[0]  # Set the first row of the selection as column headers
            df = df[1:]  # Drop the header row itself

            # Filter out rows where any cell has "BYE WEEK"
            df = df[~df.eq("BYE WEEK").any(axis=1)]

            # Drop the first column and the last two columns
            df = df.iloc[:, :-2].reset_index(drop=True)

            # Extract "vs" or "@" into a new column "Home/Away"
            df['Home/Away'] = df['OPPONENT'].str.extract(r'(vs|@)')
            df['Home/Away'] = df['Home/Away'].replace('vs', 'vs.')

            # Remove "vs" or "@" from the "OPPONENT" column and strip whitespace
            df['OPPONENT'] = df['OPPONENT'].str.replace(r'vs |@ ', '', regex=True).str.strip()

            ## Organize
            df['user_team'] = self.nfl_md['team'][self.nfl_md['abbr'] == nfl_team_abbr].iloc[0]
            df['game_type'] = "regular season"
            df = df.drop(columns=df.filter(regex="^tickets$").columns)
            df['TIME'] = df['TIME'].replace("TBD", pd.NA)

            # Replace "TBD" with NaN using loc
            df.loc[df['DATE'].str.contains('TBD'), 'DATE'] = np.nan

            return df
        
        else:
            print(f"Error retrieving data for {nfl_team_abbr}")


    # End NFL
    #######################################################

    # End Scrapers
    ##############################################################################################################






    ##############################################################################################################
    # Begin organizing the data

    def organize_data(self, save, fb_master_filename, nba_master_filename, nhl_master_filename, nfl_master_filename):

        # Define allowed save options
        allowed_save_options = {"both", "master", "future"}
        
        # Validate the save argument
        if save not in allowed_save_options:
            raise ValueError(f"Invalid save option. Choose from: {', '.join(allowed_save_options)}")
    

        #  Get the current year
        current_year = datetime.now().year
        next_year = current_year + 1

        # Define a custom date parser for the corresponding formats
        fb_date_parser = lambda x: pd.to_datetime(x, format="%d/%m/%y").date()
        nba_nhl_date_parser = lambda x: pd.to_datetime(x, format="%a, %b %d, %Y").date()
        nfl_date_parser = lambda x: pd.to_datetime(f"{x}, {next_year}" if "Jan" in x else f"{x}, {current_year}", format="%a, %b %d, %Y").date() if pd.notna(x) else np.nan

        # Master data files for each subject
        fb_master_fp = os.path.join(self.fb_folder_path, fb_master_filename)
        nba_master_fp = os.path.join(self.nba_folder_path, nba_master_filename)
        nhl_master_fp = os.path.join(self.nhl_folder_path, nhl_master_filename)
        nfl_master_fp = os.path.join(self.nfl_folder_path, nfl_master_filename)


        # Read in files with their dates
        ## football/soccer
        df_fb = pd.read_csv(
            fb_master_fp,
            parse_dates=['Date'], 
            date_parser=fb_date_parser
        )
        ### Create/convert cols as necessary
        df_fb['Date'] = pd.to_datetime(df_fb['Date']).dt.date
        df_fb = df_fb[df_fb['Date'] >= self.today]
        df_fb['Time'] = df_fb['Time'].astype(str).str.replace(r'\s+', '', regex=True)
        df_fb['Time'] = df_fb['Time'].replace('-', pd.NA).replace('SUSP', pd.NA)
        df_fb['Time'] = pd.to_datetime(df_fb['Time'], format='%H:%M').dt.time


        ## nba
        df_nba = pd.read_csv(
            nba_master_fp,
            parse_dates=['Date'], 
            date_parser=nba_nhl_date_parser
        )
        ### Create/convert cols as necessary
        df_nba['Date'] = pd.to_datetime(df_nba['Date']).dt.date
        df_nba = self.org_assign_teams(df_nba, 'Home/Away', 'user_team', 'Opponent')
        df_nba['Start (ET)'] = pd.to_datetime(df_nba['Start (ET)'], infer_datetime_format=True).dt.time
        df_nba = df_nba.rename(columns={'Start (ET)': 'Time'})
        df_nba['Time'] = pd.to_datetime(df_nba['Time'].astype(str)) - pd.to_timedelta(2, unit='hours')
        df_nba['Time'] = df_nba['Time'].dt.time


        ## nhl
        df_nhl = pd.read_csv(
            nhl_master_fp,
            parse_dates=['Date'], 
            date_parser=nba_nhl_date_parser
        )
        ### Create/convert cols as necessary
        df_nhl['Date'] = pd.to_datetime(df_nhl['Date']).dt.date
        df_nhl = self.org_assign_teams(df_nhl, 'Home/Away', 'user_team', 'Opponent')
        df_nhl['Time'] = pd.to_datetime(df_nhl['Time'], infer_datetime_format=True).dt.time
        df_nhl['Time'] = pd.to_datetime(df_nhl['Time'].astype(str)) - pd.to_timedelta(2, unit='hours')
        df_nhl['Time'] = df_nhl['Time'].dt.time


        ## nfl
        df_nfl = pd.read_csv(
            nfl_master_fp,
            parse_dates=['DATE'], 
            date_parser=nfl_date_parser
        )
        df_nfl['DATE'] = pd.to_datetime(df_nfl['DATE']).dt.date
        df_nfl = self.org_assign_teams(df_nfl, 'Home/Away', 'user_team', 'OPPONENT')
        df_nfl['TIME'] = pd.to_datetime(df_nfl['TIME'], infer_datetime_format=True).dt.time
        df_nfl['TIME'] = pd.to_datetime(df_nfl['TIME'].astype(str)) - pd.to_timedelta(2, unit='hours')
        df_nfl['TIME'] = df_nfl['TIME'].dt.time


        ## Combine data
        # First, rename and reorder columns in df_fb
        df_fb_fin = df_fb.rename(columns={'Team': 'user_team', 'League': 'game_type'})
        df_fb_fin = df_fb_fin[['user_team', 'Date', 'game_type', 'Home Team', 'Away Team', 'Time']].copy()
        df_fb_fin['Sport'] = 'Soccer'

        # Select and reorder columns in df_nba and df_nhl
        fin_cols_list = ['user_team', 'Date', 'game_type', 'Home Team', 'Away Team', 'Time']
        df_nba_fin = df_nba[fin_cols_list].copy()
        df_nba_fin['Sport'] = 'NBA'

        df_nhl_fin = df_nhl[fin_cols_list].copy()
        df_nhl_fin['Sport'] = 'NHL'

        # Select and reorder columns in df_nfl
        df_nfl_fin = df_nfl[['user_team','DATE','game_type','Home Team','Away Team', 'TIME']].copy()
        df_nfl_fin.columns = fin_cols_list
        df_nfl_fin['Sport'] = 'NFL'


        # Stack all dataframes and Sort the combined dataframe by Date and then by Time, both in ascending order
        df_fin_all = (
            pd.concat([df_fb_fin, df_nba_fin, df_nhl_fin, df_nfl_fin], ignore_index=True)
            .sort_values(by=['Date', 'Time', 'Home Team'], ascending=[True, True, True])
            .reset_index(drop=True)
        )

        df_fin_future = df_fin_all[df_fin_all['Date'] >= self.today]


        ## Save dfs
        # Define the file name
        master_filename = f"df_master_{self.today_str}.csv"
        master_fut_filename = f"df_master_future_{self.today_str}.csv"

        master_folder_path = os.path.join(self.data_base_dir, "master")
        master_fut_folder_path = os.path.join(self.data_base_dir, "master_future")

        master_fp = os.path.join(master_folder_path, master_filename)
        master_fut_fp = os.path.join(master_fut_folder_path, master_fut_filename)


        # Save DataFrames based on the save option
        if save == "both":
            df_fin_all.to_csv(master_fp, index=False)
            df_fin_future.to_csv(master_fut_fp, index=False)
        elif save == "master":
            df_fin_all.to_csv(master_fp, index=False)
        elif save == "future":
            df_fin_future.to_csv(master_fut_fp, index=False)
        



    # Function for home/away cols for nba/nhl/nfl
    def org_assign_teams(self, df, home_away_col, user_team_col, opponent_col):
        df['Home Team'] = np.where(df[home_away_col] == 'vs.', df[user_team_col], df[opponent_col])
        df['Away Team'] = np.where(df[home_away_col] == '@', df[user_team_col], df[opponent_col])
        return df
    


    # End organizing the data
    ##############################################################################################################




    ##############################################################################################################
    # Begin Uploading the data to GSheets

    def upload_to_gsheet(self, csv):
        ### Send to GSheet
        ## Config details
        sa_path_windows = r"C:\Users\Owner\AppData\Local\Programs\Python\Python310\Lib\site-packages\gspread\service_account.json"
        sa_path_mac = "/Users/ckopel/Documents/keys/service_account.json"
        sa_path = sa_path_windows if os.name == "nt" else sa_path_mac if os.name == "posix" else None

        gc = gspread.service_account(filename=sa_path)


        ## Read in the csv
        master_future_fp = os.path.join(self.master_future_folder_path, csv)
        df = pd.read_csv(master_future_fp)

        # Replace NaN and infinite values
        df = df.replace([float('inf'), -float('inf')], None)  # Replace infinite values with None
        df = df.fillna('')  # Replace NaN with an empty string


        ## Open the sheet
        sh = gc.open("project_w_landing")
        worksheet = sh.worksheet("Data")  # Access the "Data" sheet
        worksheet.clear() # Clear the sheet


        # Upload CSV data to Google Sheets
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        


    # End uploading the data to GSheets
    ##############################################################################################################