#####
#####
# This version successfully returns the schedules for the selcted teams (and returns appr. msg if no upcoming games)
# Next, have another selection for soccer and group them all together.
# We want the final output to be a schedule of all events, not just by team, but aggregated by day, so we'll need to combine all the data 
#  and then config as one schedule
#####
#####
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.properties import StringProperty, ListProperty
from kivy.uix.screenmanager import ScreenManager, Screen
import pandas as pd

import main_classes as mc

class MyLayout(BoxLayout):
    selected_options = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dropdown = DropDown()
        
        # Get list of NBA Abbr teams
        nba_path = mc.SportsBaseClass.nba_team_abbr_lkp_path
        nba_abbr_list = pd.read_csv(nba_path).abbr.tolist()

        for nba_team in nba_abbr_list:
            btn = Button(text=nba_team, size_hint_y=None, height=44)
            btn.bind(on_release=self.toggle_selection)
            self.dropdown.add_widget(btn)

        self.main_button = self.ids.main_button
        self.main_button.bind(on_release=self.dropdown.open)

    def toggle_selection(self, btn):
        if btn.text in self.selected_options:
            self.selected_options.remove(btn.text)
            btn.background_color = (1, 1, 1, 1)  # Default color
        else:
            self.selected_options.append(btn.text)
            btn.background_color = (0.5, 0.5, 1, 1)  # Highlight color

        self.main_button.text = ', '.join(self.selected_options)

    def go_to_second_screen(self):
        app = App.get_running_app()
        selected_teams = ', '.join(self.selected_options)
        app.root.get_screen('second').selected_teams = selected_teams

        # Pull the schedules for the selected teams
        schedules = [mc.nba(teams_abbr=[team]).msg_schedule() for team in self.selected_options]
        app.root.get_screen('second').slct_team_sch = '\n'.join(schedules)

        app.root.current = 'second'


class SecondScreen(Screen):
    selected_teams = StringProperty('')
    slct_team_sch = StringProperty('')


class WhatsUpApp(App):
    def build(self):
        sm = ScreenManager()
        
        screen = Screen(name='main')
        layout = MyLayout()
        screen.add_widget(layout)
        sm.add_widget(screen)
        
        second_screen = SecondScreen(name='second')
        sm.add_widget(second_screen)
        
        return sm

if __name__ == '__main__':
    WhatsUpApp().run()

