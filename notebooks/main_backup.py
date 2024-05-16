from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
import pandas as pd

import main_classes as mc

class MyLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dropdown = DropDown()

        # Get list of NBA Abbr teams
        nba_path = mc.SportsBaseClass.nba_team_abbr_lkp_path
        nba_abbr_list = pd.read_csv(nba_path).abbr.tolist()

        for nba_team in nba_abbr_list:
            btn = Button(text=nba_team, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: self.dropdown.select(btn.text))
            self.dropdown.add_widget(btn)

        self.main_button = self.ids.main_button
        self.main_button.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(self.main_button, 'text', x))


    def on_select_team(self, team):
        self.selected_team = team  # Store the selected team in the variable

class SecondScreen(Screen):
    # nba_selection_output = mc.nba(teams_abbr = ['DEN'])
    test_var = 'test'
    selected_team = StringProperty(test_var)  # Define a StringProperty
        

class WhatsUpApp(App):
    def build(self):
        sm = ScreenManager()
        screen = Screen(name='main')
        screen.add_widget(MyLayout())
        sm.add_widget(screen)
        second_screen = SecondScreen(name='second')
        sm.add_widget(second_screen)
        return sm
    
if __name__ == '__main__':
    WhatsUpApp().run()