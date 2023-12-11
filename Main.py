from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen

import Home

screen_helper ="""
ScreenManager:
    HomePage:
    ProfilePage:
    LoginPage:
<HomePage>:    
    MDTextField:

        hint_text:'Search For your next stay' 
        pos_hint:{'center_x': .5, 'center_y': .7}
        size_hint_x: None
        icon_right: "MDRoundFlatIconButton"
        icon_right_color: app.theme_cls.primary_color
        width: 300
<ProfilePage>:
<HomePage>:
    
"""


class LoginScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 20

        self.title_label = Label(text='Login Form', font_size='20sp')
        self.username_input = TextInput(hint_text='Username', height=20)
        self.password_input = TextInput(hint_text='Password', password=True, height=40)
        self.login_button = Button(text='Login', height=20)
        self.register_button = Button(text='No account? register here', height=40)
        self.forgot_button = Button(text='Forgot Password?', height=40)
        self.login_button.bind(on_press=self.do_login, )
        self.error_label = Label(text='', color=(1, 0, 0, 1))

        self.add_widget(self.title_label)
        self.add_widget(self.username_input)
        self.add_widget(self.password_input)
        self.add_widget(self.login_button)
        self.add_widget(self.error_label)
        self.add_widget(self.forgot_button)
        self.add_widget(self.register_button)

    def do_login(self, instance):
        sm = ScreenManager()
        username = self.username_input.text
        password = self.password_input.text

        if username == 'admin' and password == 'password':
            self.error_label.text = ''
            print('Successful login!')
            # send to Home page
        else:
            self.error_label.text = 'Invalid username or password'

    def do_reg(self, instance):
        username = self.username_input.text
        password = self.password_input.text


class LoginApp(App):
    def build(self):
        login_screen = LoginScreen()
        return login_screen


class MainPage(Screen):
    pass


class ProfilePage(Screen):
    pass


if __name__ == '__main__':
    LoginApp().run()
