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

from datetime import datetime
import time

import requests



class scrape_w:

    def __init__(self):

        # # Find OS
        # ## (*was using for filepaths and saving, but the methodology used below should be platform agnostic (at least for mac, windows)*)
        # self.os_var = "windows" if os.name == "nt" else "mac" if os.name == "posix" else None


        # Define the project directories
        project_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.data_base_dir = os.path.join(project_base_dir, "data")

        ## Create the full path to the metadata files
        self.fb_md_fp = os.path.join(self.data_base_dir, "football_data.csv")
        self.nba_md_fp = os.path.join(self.data_base_dir, "nba_team_abbr.csv")
        self.nhl_md_fp = os.path.join(self.data_base_dir, "nhl_team_abbr.csv")
        self.nfl_md_fp = os.path.join(self.data_base_dir, "nfl_espn_team_abbr.csv")


        ## misc. vars
        self.chrome_driver_path = os.getenv('chrome_driver_path') # # Get the ChromeDriver path from your environment variable
        self.today_str = datetime.now().strftime("%Y_%m_%d") # # Get today's date in the desired format



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



    ## Method for each speciifc subject (to be invoked by the general scraper)

    #######################################################
    # Begin FB
    def scrape_fb(self):
        fb_md = pd.read_csv(self.fb_md_fp)

        # Convert metadata to dictionary
        team_url_dict = fb_md.set_index('team')['url'].to_dict()
        team_url_dict = {team: url + 'matches/' for team, url in team_url_dict.items()} # Amend each URL by adding 'matches/' at the end


        for team, url in team_url_dict.items():

            try:

                # Setup WebDriver
                service = Service(self.chrome_driver_path)  # Use the path from environment variable
                driver = webdriver.Chrome(service=service)

                # Open the page
                driver.get(url)
                
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
                        'Team': team,
                        'Date': dates,
                        'League': leagues,
                        'Home Team': homes,
                        'Time': times,
                        'Away Team': aways
                    }
                )

                ## Add to master df
                if 'df_fb_master' in locals():
                    df_fb_master = pd.concat([df_fb_master, df_team_fixtures], ignore_index=True)
                else:
                    df_fb_master = df_team_fixtures.copy()


            except TimeoutException:
                print("Timed out waiting for cookie pop-up or other elements")
                
            finally:
                # Close the browser
                driver.quit()


        ## Save the df
        # Create the full path for the CSV file
        fb_file_name = f"df_fb_scrape_{self.today_str}.csv"
        fb_folder_path = os.path.join(self.data_base_dir, "fb")  # Create the path to the fb folder within data_base_dir
        fb_file_path = os.path.join(fb_folder_path, fb_file_name)

        # Save the DataFrame
        df_fb_master.to_csv(fb_file_path, index=False)

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
        nba_folder_path = os.path.join(self.data_base_dir, "nba")  # Create the path to the nba folder within data_base_dir
        nba_file_path = os.path.join(nba_folder_path, nba_file_name)

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
            df['game_type'] = np.where(df['Notes'] == 'In-Season Tournament', 'In-Season Tournament', df['game_type']) # Apply conditional update to game_type column

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
        nhl_folder_path = os.path.join(self.data_base_dir, "nhl")  # Create the path to the nhl folder within data_base_dir
        nhl_file_path = os.path.join(nhl_folder_path, nhl_file_name)

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
            
            return df
        
        else:
            print(f"Error retrieving data for {nhl_team_abbr}")

    # End NHL
    #######################################################




    #######################################################
    # Begin NFL
    def scrape_nfl(self):

        nfl_md = pd.read_csv(self.nfl_md_fp)

        for nfl_team in nfl_md['abbr']:
            
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
        nfl_folder_path = os.path.join(self.data_base_dir, "nfl")  # Create the path to the nfl folder within data_base_dir
        nfl_file_path = os.path.join(nfl_folder_path, nfl_file_name)

        # Save the DataFrame
        df_nfl_master.to_csv(nfl_file_path, index=False)


    # Get the schedule from nfl ref
    def retrieve_nfl_schedule(self, nfl_team_abbr):

        # URL of the website
        nfl_url = f"https://www.pro-football-reference.com/teams/{nfl_team_abbr}/2024/gamelog/"

        headers = {
            "User-Agent": "YourAppName/1.0 (https://yourwebsite.com; contact@yourwebsite.com)"
        }

        # Send a GET request to the URL
        response = requests.get(nfl_url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            time.sleep(4) # if successful, wait n secs before reading in the html
            dfs_list = pd.read_html(nfl_url)

            # Concatenate all DataFrames in dfs_list
            df = pd.concat(dfs_list, ignore_index=True)

            # Flatten the multi-level columns, ignoring 'Unnamed' and removing '_level_'
            df.columns = [
                re.sub(r'\d+\s', '', ' '.join(col).strip().replace("Unnamed: ", "").replace("_level_", "")).replace("0", "").replace("1", "").replace("6","Home/Away").replace("4","Result")
                for col in df.columns
            ]

            df = df.drop(columns='3')

            # Organize
            df['Home/Away'] = df['Home/Away'].fillna("vs.")
            df['user_team'] = self.nfl_md['team'][self.nfl_md['abbr'] == nfl_team_abbr].iloc[0]
            df['game_type'] = "regular season"

            return df
        
        else:
            print(f"Error retrieving data for {nfl_team_abbr}")


    # End NFL
    #######################################################