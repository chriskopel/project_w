import kivy
from kivy.app import App
from kivy.uix.label import Label
# from kivy.uix.gridlayout import GridLayout

import main_classes as mc


class WhatsUp(App):
    def build(self):
        # layout = GridLayout(cols=1)

        # Var for schedule
        nba_sch = mc.nba(teams_abbr=['DEN']).msg_schedule()

        # Adding a label to display text
        label = Label(text=nba_sch) #, font_size=20, color=(0,0,1,1))
        # layout.add_widget(label)

        # return layout

        return label

if __name__ == '__main__':
    WhatsUp().run()
