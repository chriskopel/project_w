import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

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