import sys
from kivy.config import Config
from kivy_reloader import App

if len(sys.argv) > 1:
    args = sys.argv
    if args[1] == "no-window":
        Config.set('graphics', 'window_state', 'hidden')


class MainApp(App):
    def build_and_reload(self):
        from screens.main_screen import MainScreen
        return MainScreen(name="Main Screen")


MainApp()
