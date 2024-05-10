import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

import requests
from bs4 import BeautifulSoup

from datetime import datetime, timedelta
import pytz

import geonamescache

import os



################################################################################
#### Begin - SportsBaseClass
class SportsBaseClass:

    # Get the directory of the current script
    script_dir = os.path.dirname(__file__)

    # Define the relative path to the CSV file
    footy_relative_path = os.path.join("..", "..", "project_w", "data", "football_data.csv")
    nba_relative_path = os.path.join("..", "..", "project_w", "data", "nba_team_abbr.csv")
    nhl_relative_path = os.path.join("..", "..", "project_w", "data", "nhl_team_abbr.csv")

    # Construct the absolute path for the lookup files
    football_data_path = os.path.abspath(os.path.join(script_dir, footy_relative_path))
    nba_team_abbr_lkp_path = os.path.abspath(os.path.join(script_dir, nba_relative_path))
    nhl_team_abbr_lkp_path = os.path.abspath(os.path.join(script_dir, nhl_relative_path))



    # Define a function to apply the condition
    def get_game_time_status(self, date):
        if date.date() >= self.today:
            return 'Upcoming'
        else:
            return 'Past'
        
    # Define a function to apply the condition
    def get_season(self, row_number):
        if row_number >= 82:
            return 'playoffs'
        else:
            return 'regular season'



#### End - SportsBaseClass
################################################################################



################################################################################
#### Begin - NBA Class to return the upcoming 5 games for specified teams (by team abbr - nba ref)

class nba(SportsBaseClass):

    def __init__(self, teams_abbr, n_upcoming_games=None):

        self.teams_abbr = teams_abbr
        self.n_upc_games = n_upcoming_games

        self.df_nba = pd.read_csv(self.nba_team_abbr_lkp_path)
        # Get today's date
        self.today = datetime.now().date()
    

    # Build a message with the upcoming schedule
    def msg_schedule(self):

        for team in self.teams_abbr:
            df = self.retrieve_schedule(team)
            user_team = df['user_team'].iloc[0]

            # Construct the message header
            message = f"Upcoming schedule for the {user_team}:\n"

            # Iterate over the rows and construct the message body
            for index, row in df.iterrows():
                game_date = row['Date']
                start_time = row['Start (ET)']
                home_away = row['Home/Away']
                opponent = row['Opponent']
                
                message += f"{game_date} at {start_time}(ET) {home_away} the {opponent}.\n"

            print(message)

    
    # Get the schedule from nba ref
    def retrieve_schedule(self, team_abbr):
        # URL of the website
        url = f"https://www.basketball-reference.com/teams/{team_abbr}/2024_games.html#games"

        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            dfs_list = pd.read_html(url)

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
            df['user_team'] = self.df_nba['team'][self.df_nba['abbr'] == team_abbr].iloc[0]
            
            # Create new cols from fns
            df['GameTimeStatus'] = df['computer_date'].apply(lambda x: self.get_game_time_status(x))
            df['game_type'] = df.index.to_series().apply(lambda x: self.get_season(x))

            # new slim table for upcoming games
            df_upcoming_slim = df[df['GameTimeStatus'] == 'Upcoming'][['Date','Start (ET)','Home/Away','Opponent','user_team']].reset_index(drop=True).head(self.n_upc_games)

            return df_upcoming_slim
        
        else:
            print("Error retrieving data")

 

    

#### End - NBA Class (nba ref)
################################################################################
    


################################################################################
#### Begin - NHL Class to return the upcoming 5 games for specified teams (by team abbr - nhl ref)

class nhl(SportsBaseClass):

    def __init__(self, teams_abbr, n_upcoming_games=None):

        self.teams_abbr = teams_abbr
        self.n_upc_games = n_upcoming_games

        self.df_nhl = pd.read_csv(self.nhl_team_abbr_lkp_path)
        # Get today's date
        self.today = datetime.now().date()
    

    # Build a message with the upcoming schedule
    def msg_schedule(self):

        for team in self.teams_abbr:
            df = self.retrieve_schedule(team)
            user_team = df['user_team'].iloc[0]

            # Construct the message header
            message = f"Upcoming schedule for the {user_team}:\n"

            # Iterate over the rows and construct the message body
            for index, row in df.iterrows():
                game_date = row['Date']
                start_time = row['Time']
                home_away = row['Home/Away']
                opponent = row['Opponent']
                
                message += f"{game_date} at {start_time}(ET) {home_away} the {opponent}.\n"

            print(message)

    
    # Get the schedule from nba ref
    def retrieve_schedule(self, team_abbr):
        # URL of the website
        url = f"https://www.hockey-reference.com/teams/{team_abbr}/2024_games.html"

        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            dfs_list = pd.read_html(url)

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
            df['user_team'] = self.df_nhl['team'][self.df_nhl['abbr'] == team_abbr].iloc[0]
            
            # Apply the function to create the new column
            df['GameTimeStatus'] = df['computer_date'].apply(lambda x: self.get_game_time_status(x))
            df['game_type'] = df.index.to_series().apply(lambda x: self.get_season(x))

            # new slim table for upcoming games
            df_upcoming_slim = df[df['GameTimeStatus'] == 'Upcoming'][['Date','Time','Home/Away','Opponent','user_team']].reset_index(drop=True).head(self.n_upc_games)

            return df_upcoming_slim
        
        else:
            print("Error retrieving data")

 

    

#### End - NHL Class (nhl ref)
################################################################################









################################################################################
#### Begin - Football (soccer) Class to return the upcoming 5 games for specified teams (by team name)
class football(SportsBaseClass):

    def __init__(self, football_teams):
        self.football_teams = football_teams
        self.agent = 'Mozilla/5.0 (Windows NT 10.0; Windows; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'
        self.df_footie = pd.read_csv(self.football_data_path)


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









################################################################################
#### Begin - Weather Class to return current and forecasted weather by city name
class weather:

    def __init__(self, city_names=['Denver']):

        self.weather_data_dict = self.get_weather_data(city_names)

        
    ## Get the lat lon of the city 
    def get_weather_data(self, city_names):

        # Create an instance of the GeoNamesCache
        gc = geonamescache.GeonamesCache()

        # Retrieve cities data
        cities = gc.get_cities()

        dict_city_lat_lon = {}
        for city_name in city_names:
            # Search for the city in the cities data
            for city_code, city_data in cities.items():
                if city_data['name'] == city_name:
                    # Extract latitude and longitude
                    latitude = city_data['latitude']
                    longitude = city_data['longitude']

                    dict_city_lat_lon[city_name] = [latitude, longitude]
                    break
            else:
                print(f"Could not find city name: {city_name}")



        # Define a custom User-Agent header
        headers = {
            "User-Agent": "YourAppName/1.0 (your-email@example.com) _ 11298370iahdjhiaosfdi8y98 y9801"
        }


        weather_data_dict = {}
        for city, lat_lon in dict_city_lat_lon.items():
            
            lat, lon = lat_lon

            # Specify the MET API URL with the retrieved latitude and longitude
            url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"

            # Make an API request to the MET API with the custom User-Agent header
            response = requests.get(url, headers=headers)

            # Parse the JSON response
            weather_data_dict[city] = response.json()

        
        return weather_data_dict


    ### Parse weather data
    # Function to parse the forecasted weather data
    def parse_weather_data(self):

        for city, data in self.weather_data_dict.items():

            print("_______________________________________________________")
            print(f"Weather for {city}:\n")
            
            timeseries = data['properties']['timeseries']
            
            # Iterate through each time series entry
            for entry in timeseries:
                time = self.convert_to_mountain_time(entry['time'])
                instant_data = entry['data']['instant']['details']
                
                # Current instant data
                current_temp_celsius = instant_data['air_temperature']
                current_temp_fahrenheit = self.celsius_to_fahrenheit(current_temp_celsius)
                current_wind_speed_ms = instant_data['wind_speed']
                current_wind_speed_mph = self.ms_to_mph(current_wind_speed_ms)
                current_wind_direction = instant_data['wind_from_direction']
                # Convert wind direction in degrees to compass direction
                compass_direction = self.wind_direction_to_compass(current_wind_direction)

                # Get symbol code for instant data from the next 1-hour forecast data
                if 'next_1_hours' in entry['data']:
                    next_1_hour = entry['data']['next_1_hours']
                    symbol_code_instant = next_1_hour['summary']['symbol_code']
                else:
                    symbol_code_instant = 'N/A'  # If next 1-hour forecast data is unavailable

                # Retrieve precipitation data for the next 1, 6, and 12 hours
                precip_next_1_hour = next_1_hour['details']['precipitation_amount'] if 'next_1_hours' in entry['data'] and 'details' in entry['data']['next_1_hours'] else 0.0
                precip_next_6_hour = entry['data']['next_6_hours']['details']['precipitation_amount'] if 'next_6_hours' in entry['data'] and 'details' in entry['data']['next_6_hours'] else 0.0
                

                # Print
                prnt_str_time = f"Time: {time} - {symbol_code_instant}\n"
                prnt_str_weather_0 = f"Temperature: {current_temp_fahrenheit:.2f}°F, Wind speed: {current_wind_speed_mph:.2f} mph, Wind direction: {compass_direction}\n"
                prnt_str_weather_1 = f"Precip next 1 hour: {precip_next_1_hour} mm, Precip next 6 hours: {precip_next_6_hour} mm\n"

                final_msg =  prnt_str_time + prnt_str_weather_0 + prnt_str_weather_1

                print(final_msg)

    


    ##### Helper functions
    # Helper function to convert Celsius to Fahrenheit
    def celsius_to_fahrenheit(self, celsius):
        return celsius * 9 / 5 + 32


    # Helper function to convert meters per second to miles per hour
    def ms_to_mph(self, meters_per_second):
        return meters_per_second * 2.237


    # Helper function to convert wind direction in degrees to compass direction
    def wind_direction_to_compass(self, degrees):
        compass_points = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]
        # Calculate the index in the compass_points list based on the degrees
        index = int((degrees + 11.25) / 22.5) % 16
        return compass_points[index]


    # Function to convert UTC timestamp to Mountain Time (Denver, CO)
    def convert_to_mountain_time(self, utc_timestamp, format="%Y-%m-%d %H:%M"):

        # Define the UTC and Mountain Time (Denver, CO) time zones
        utc_timezone = pytz.utc
        mountain_timezone = pytz.timezone('America/Denver')


        # Parse the UTC timestamp to a datetime object
        utc_time = datetime.fromisoformat(utc_timestamp.rstrip('Z'))
        
        # Make the datetime object timezone aware (UTC timezone)
        utc_time = utc_timezone.localize(utc_time)
        
        # Convert the UTC time to Mountain Time (Denver, CO)
        mountain_time = utc_time.astimezone(mountain_timezone)
        
        # Return the Mountain Time in the specified format
        return mountain_time.strftime(format)
    
    ##### End helper functions



#### End - Weather Class by city name
################################################################################















#######################################################################################################################
#######################################################################################################################
### Dev notes
# Updates to make:
# - Class: weather
# - - Autoformat tz to selected city
# - - only show n forward hours (current (0),1,3,5,12,24,48,72?)
# - - find a better way to display (chart?)
# - - pick out the min max and avg 
#
#
# - CHANGE FOOTBALL (SOCCER) CLASS TO THE FBREF? https://fbref.com/en/squads/b8fd03ef/Manchester-City-Stats#all_matchlogs
# - - would be the "same" source for all data then (pros and cons, but we know it's easy to pull from)
# 
#
#
# - Change filepath lookup for csvs to hide the full directory
#
# 
#
#
### End Dev notes
#######################################################################################################################
#######################################################################################################################