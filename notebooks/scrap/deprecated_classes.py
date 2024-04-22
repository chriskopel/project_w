######################################################
######################################################
### This file is for referencing classes that used to be in the main_classes.py file


################################################################################
#### Begin - NBA Class to return the upcoming 5 games for specified teams (by team name) (nba_api)

from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import playernextngames, commonallplayers

class nba:

    def __init__(self, nba_teams):
        self.nba_teams = nba_teams

        # Team IDs
        self.team_ids = []
        for team in nba_teams:
            team_id = self.get_team_id(team)
            self.team_ids.append(team_id)

        # Players 
        self.team_players = []
        for id in self.team_ids:
            player = self.get_team_player(id)
            self.team_players.append(player)

        # Team Schedules
        self.dict_of_dfs = {}
        for player in self.team_players:
            df = self.get_team_schedule(player)
            self.dict_of_dfs[player] = df



    ## Final function to return schedule
    def return_sch_msg(self, dict_of_dfs):
        # Display messages
        self.display_messages = []
        for key, df in dict_of_dfs.items():
            # Filter original df
            df = df[['GAME_DATE','HOME_TEAM_ABBREVIATION','VISITOR_TEAM_ABBREVIATION','GAME_TIME']]
            df['game_time_mountain'] = df['GAME_TIME'].apply(self.subtract_two_hours)
            df = df.drop(columns='GAME_TIME')

            # Create message from the columns
            df['display_text'] = df['GAME_DATE'] + ': ' + df['VISITOR_TEAM_ABBREVIATION'] + ' @ ' + df['HOME_TEAM_ABBREVIATION'] + ' - ' + df['game_time_mountain']
            df = df[['display_text']]
            final_msg = df.display_text.to_string(index=False)
            self.display_messages.append(final_msg)

        return self.display_messages


    ## Function to get the team ID by team name
    def get_team_id(self, team_name):
        nba_teams = teams.get_teams()
        for team in nba_teams:
            if team['full_name'] == team_name:
                return team['id']
        return None


    ## Function to get a player of a specific team (need a player to lookup the schedule)
    def get_team_player(self, team_id):
        # Get all players who were active in the current season
        all_players = commonallplayers.CommonAllPlayers(is_only_current_season=1)
        all_players_df = all_players.get_data_frames()[0]
        
        # Filter the players to get those who are currently on the specified team
        team_roster = all_players_df[all_players_df['TEAM_ID'] == team_id]
        player = team_roster.DISPLAY_FIRST_LAST.iloc[0]

        return player
    

    ## Function to get the team's schedule 
    def get_team_schedule(self, team_player):
        # Load all players, get player id for input player
        all_players = players.get_players()
        player_stats = [player for player in all_players if player['full_name'] == team_player]
        player_id = player_stats[0]['id']

        # Grab the schedule
        player_next_n_games = playernextngames.PlayerNextNGames(player_id=player_id)
        df_player_next_n_games = player_next_n_games.get_data_frames()[0]
        next_n_games = df_player_next_n_games.head()

        return next_n_games
    

    # Function to subtract two hours from the time string
    def subtract_two_hours(self, time_str):
        # Convert string to datetime object
        datetime_obj = datetime.strptime(time_str, '%I:%M %p')
        
        # Subtract two hours
        datetime_obj -= timedelta(hours=2)
        
        # Format the datetime object as a string in '%I:%M %p' format
        return datetime_obj.strftime('%I:%M %p')
    

####
'''
# Example calling this class:
nba_config = mc.nba(nba_teams = ["Denver Nuggets", "Atlanta Hawks"])
final_dict = nba_config.dict_of_dfs
nba_config.return_sch_msg(final_dict)
'''
####
    

#### End - NBA Class (nba_api)
################################################################################



















################################################################################
#### Begin - NBA Class to return the upcoming 5 games for specified teams (by team name) (foxsports.com)

class nba:

    def __init__(self, nba_city=["denver"], nba_team=["nuggets"]):
        driver_path = os.getenv('chrome_driver_path')
        # Set up the WebDriver
        self.service = Service(driver_path)
        self.options = Options()
        self.options.add_argument('--headless')

        # Clean, combine lists
        nba_city = [element.replace(' ', '-') for element in nba_city]
        self.nba_tuple = zip(nba_city, nba_team)
        

    def return_sch_msg(self):
        self.display_messages = []
        # Loop through each team and get the display messages
        for ele1, ele2 in self.nba_tuple:
            city, team = ele1, ele2
            url = f'https://www.foxsports.com/nba/{city}-{team}-team-schedule'

            # Get raw df, then clean it
            df = self.get_raw_df(url)
            df_clean = self.build_clean_df(df, team)

            # Return final msg
            df_final = df_clean[['display_text']]
            final_msg = df_final.display_text.to_string(index=False)

            # Add to the message list
            self.display_messages.append(final_msg)

            return self.display_messages



    

    def build_clean_df(self, df, team):
        # Build and clean
        col_names = ['date','opponent','time','arena']
        df = df.iloc[1:]
        df.columns = col_names
        df['game_type'] = df['opponent'].apply(lambda x: 'Away' if '@' in x else 'Home')
        df['opponent'] = df['opponent'].str.replace('@', '').str.split().str[-1]
        df['TV'] = df['time'].apply(lambda x: x.split('\n')[1] if '\n' in x else '')
        df['time'] = df['time'].apply(lambda x: x.split('\n')[0] if '\n' in x else x)
        df['location'] = df['arena'].apply(lambda x: x.split('\n')[1])
        df['arena'] = df['arena'].apply(lambda x: x.split('\n')[0]).str.replace(',','')
        df['display_text'] = df.apply(lambda row: f"{row['date']} @ {row['time']}: {row['opponent']} @ {team.title()} at {row['arena']} in {row['location']}" if row['game_type'] == 'Home' else f"{row['date']} @ {row['time']}: {team.title()} @ {row['opponent']} at {row['arena']} in {row['location']}",
            axis=1)
        
        return df



    ## Get a raw df from the url
    def get_raw_df(self, url):
        # Load driver         
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        # Load the website
        self.driver.get(url)

        # Locate the <div class="table"> element
        table_div = self.driver.find_element(By.CLASS_NAME, 'table')

        # Locate the <table id="table-0" class="data-table"> within the table div
        table = table_div.find_element(By.ID, 'table-0')

        df = self.construct_table(table)
        # Quit the driver
        self.driver.quit()

        return df

    
    ## Construct a table from table elements passed in
    def construct_table(self, table):
        # Initialize a list to hold the rows of the table
        rows = []

        # Iterate through each row in the table
        for row in table.find_elements(By.TAG_NAME, 'tr'):
            # Initialize a list to hold the cells in the row
            cells = []
            
            # Iterate through each cell in the row
            for cell in row.find_elements(By.TAG_NAME, 'td'):
                # Append the cell's text to the list of cells
                cells.append(cell.text)
            
            # Append the list of cells (row) to the list of rows
            rows.append(cells)

        # Convert the list of rows into a Pandas DataFrame
        df = pd.DataFrame(rows)

        return df



####
'''
# Example calling this class:
# nba_config = mc.nba()
nba_config = mc.nba(
    nba_city=['oklahoma city','los angeles'],
    nba_team=['thunder','clippers']
)

nba_msg = nba_config.return_sch_msg()
print(nba_msg)
'''
####


    

#### End - NBA Class (foxsports.com)
################################################################################