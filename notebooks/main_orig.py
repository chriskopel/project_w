import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.gridlayout import GridLayout

import main_classes as mc

import pandas as pd


class WhatsUp(App):
    def build(self):
        # layout = GridLayout(cols=1)

        ### Dropdown
        # Get list of NBA Abbr teams
        nba_path = mc.SportsBaseClass.nba_team_abbr_lkp_path
        nba_abbr_list = pd.read_csv(nba_path).abbr.tolist()

        # Create a button to trigger the dropdown
        main_button = Button(text='Select NBA Team', size_hint=(None, None))
        main_button.bind(on_release=self.show_dropdown)

        # Create a dropdown
        dropdown = DropDown()
        for team in nba_abbr_list:
            btn = Button(text=team, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(btn)


        # Bind the dropdown to the button selection
        dropdown.bind(on_select=lambda instance, x: setattr(main_button, 'text', x))

        main_button_dropdown = main_button
        main_button_dropdown.dropdown = dropdown


        # Create a BoxLayout to center the button vertically and horizontally
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(BoxLayout())
        layout.add_widget(main_button_dropdown)


        return layout
    

    def show_dropdown(self, button):
        # Open the dropdown when the button is clicked
        button.dropdown.open(button)


        # # Var for schedule
        # nba_sch = mc.nba(teams_abbr=['DEN']).msg_schedule()

        # # Adding a label to display text
        # label = Label(text=nba_sch) #, font_size=20, color=(0,0,1,1))
        # # layout.add_widget(label)

        # # return layout

        # return label

if __name__ == '__main__':
    WhatsUp().run()
