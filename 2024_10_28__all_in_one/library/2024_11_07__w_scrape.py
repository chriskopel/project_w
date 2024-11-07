import os

import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup

from datetime import datetime




class scrape_w:

    def __init__(self):

        # Find OS
        self.os_var = "windows" if os.name == "nt" else "mac" if os.name == "posix" else None


        # Define the project directories
        project_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.data_base_dir = os.path.join(project_base_dir, "data")

        ## Create the full path to the metadata files
        self.fb_md_fp = os.path.join(data_base_dir, "football_data.csv")
        self.nba_md_fp = os.path.join(data_base_dir, "nba_team_abbr.csv")
        self.nhl_md_fp = os.path.join(data_base_dir, "nhl_team_abbr.csv")
        self.nfl_md_fp = os.path.join(data_base_dir, "nfl_espn_team_abbr.csv")

        ## misc. vars
        self.chrome_driver_path = os.getenv('chrome_driver_path') # # Get the ChromeDriver path from your environment variable     
        self.today_str = datetime.now().strftime("%Y_%m_%d") # # Get today's date in the desired format



        ##### ONLY LOAD THE DATA IF IT IS TO BE DECLARED AS NEEEDED FOR THE SCRAPE IN THE METHOD CALL
        ## Define metadata needed for scraping
        
        nba_md = pd.read_csv(nba_md_fp)
        nhl_md = pd.read_csv(nhl_md_fp)
        nfl_md = pd.read_csv(nfl_md_fp)


    ## General scraper to be invoked in user code
    def scrape(self, subject: list):
        pass

    ## Method for each speciifc subject (to be invoked by the general scraper)
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
        file_name = f"df_fb_scrape_{self.today_str}.csv"
        file_path = os.path.join(self.data_base_dir, file_name)

        # Save the DataFrame
        df_fb_master.to_csv(file_path, index=False)