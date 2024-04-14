import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

import requests
from bs4 import BeautifulSoup

from datetime import datetime, timedelta

from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import leaguegamefinder, playernextngames, commonallplayers



################################################################################
#### Begin - NBA Class to return the upcoming 5 games for specified teams (by team name)
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
    

#### End - NBA Class
################################################################################
    



################################################################################
#### Begin - Football (soccer) Class to return the upcoming 5 games for specified teams (by team name)
class football:

    def __init__(self, football_teams):
        self.football_teams = football_teams
        self.agent = 'Mozilla/5.0 (Windows NT 10.0; Windows; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'
        football_data_path = r"C:\Users\Owner\Documents\Data Projects\GitHub\Apps\project_w\data\football_data.csv"
        self.df_footie = pd.read_csv(football_data_path)


    def get_games(self, prev_or_next):
        self.display_messages = []
        if prev_or_next not in ['prev','next']:
            print("Please enter 'prev' or 'next' in the prev_or_next argument")
            return

        for team in self.football_teams:
            # Get team url from df, request the url
            team_url = self.df_footie[self.df_footie['team'] == team].url.values[0]
            team_response = requests.get(team_url, headers={'User-Agent': self.agent})

            # Gather data from bs4
            soup = BeautifulSoup(team_response.text, 'html.parser')
            table = soup.find_all('table', class_='matches')
            dates = [row.text for row in table[0].find_all('td', class_="full-date")]
            leagues = [row.text.strip() for row in table[0].find_all('td', class_="competition")]
            homes = [row.text.strip() for row in table[0].find_all('td', class_="team")[::2]]
            aways = [row.text.strip() for row in table[0].find_all('td', class_="team")[1::2]]
            times = [row.text.strip() for row in table[0].find_all('td', class_="score-time")]

            # Create dataframes
            df_fixtures = pd.DataFrame(
                {
                    'Date': dates,
                    'League': leagues,
                    'Home team': homes,
                    'Time': times,
                    'Away team': aways
                }
            )

            df_fixtures['Date'] = df_fixtures['Date'].apply(self.convert_date)

            # Organize
            df_fixtures_prev5 = df_fixtures[:5]
            df_fixtures_prev5 = df_fixtures_prev5.rename(columns={"Time": "Score"})

            df_fixtures_next5 = df_fixtures[-5:]
            df_fixtures_next5['Time'] = df_fixtures_next5['Time'].apply(lambda x: self.subtract_n_hours(x, 8))

            ## Final config
            if prev_or_next == 'next':
                df_fixtures_next5['display_text'] = df_fixtures_next5['Date'] + ': ' + df_fixtures_next5['Away team'] + ' @ ' + df_fixtures_next5['Home team'] + ' (' + df_fixtures_next5['League'] + ')' + ' - ' + df_fixtures_next5['Time']
                df_fixtures_next5 = df_fixtures_next5[['display_text']]
                msg_list = df_fixtures_next5['display_text'].tolist()
                final_msg = ', '.join(msg_list)
                self.display_messages.append(final_msg)
            elif prev_or_next == 'prev':
                df_fixtures_prev5['display_text'] = df_fixtures_prev5['Date'] + ': ' + df_fixtures_prev5['Home team'] + ' ' + df_fixtures_prev5['Score'] + ' ' + df_fixtures_prev5['Away team'] + ' (' + df_fixtures_prev5['League'] + ')'
                df_fixtures_prev5 = df_fixtures_prev5[['display_text']]
                msg_list = df_fixtures_prev5['display_text'].tolist()
                final_msg = ', '.join(msg_list)
                self.display_messages.append(final_msg)

        return self.display_messages


    # Function to subtract two hours from the time string
    def subtract_n_hours(self, time_str, n):

        # Remove empty spaces
        time_str = time_str.replace(' ', '')

        # Convert string to datetime object
        datetime_obj = datetime.strptime(time_str, '%H:%M')
        
        # Subtract n hours
        datetime_obj -= timedelta(hours=n)
        
        # Format the datetime object as a string in '%I:%M %p' format
        return datetime_obj.strftime('%I:%M %p')
    

    # Define the function to convert the date string
    def convert_date(self, date_str):
        # Define the input format of the given date string
        input_format = '%d/%m/%y'
        
        # Define the desired output format for the date
        output_format = '%b %d, %Y'
        
        # Parse the date string using the input format
        date_obj = datetime.strptime(date_str, input_format)
        
        # Format the date object according to the desired output format
        formatted_date = date_obj.strftime(output_format)
        
        # Return the formatted date
        return formatted_date




#### End - Football class by team name
################################################################################