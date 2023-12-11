#!/usr/bin/env python
import sqlite3

from kivy.config import Config
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage, Image
from kivy.uix.screenmanager import Screen
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.list import TwoLineAvatarListItem

import Search

Config.set('kivy', 'log_level', 'debug')

from kivy.lang import Builder

kv = """
ScreenManager:
    Home:
        name: "home_screen"
    ListingScreen:
        name: "listing_screen"

<Home>:
    MDBoxLayout:
        orientation: "vertical"
        padding: "10dp"
        
        MDTextField:
            id: search_input
            hint_text: "Search"
            size_hint_x: None
            width: 300
            mode: "rectangle"
        
        MDRectangleFlatButton:
            text: "Search"
            theme_text_color: "Primary"
            size_hint_x: None
            width: 100
            on_release: app.root.load_homestays()  # Adjust this based on your logic
            md_bg_color: "#556b2f"
    
    ScrollView:
        GridLayout:
            id: wall_layout
            cols: 3
            size_hint_y: None
            height: self.minimum_height  # Adjust the height based on content
            padding: "10dp"

<ListingScreen>:
    # Your listing screen content goes here
"""


# ... Your remaining Python code remains unchanged


class Home(Screen):
    def __init__(self, **kwargs):
        if 'name' in kwargs:
            kwargs.pop('name')
        super(Home, self).__init__(**kwargs)
        self.callback()

    def callback(self):
        print("Grabbing image from database:")
        scroll_view = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        wall_layout = GridLayout(cols=3, size_hint_y=None)
        wall_layout.bind(minimum_height=wall_layout.setter('height'))

        def update_height(img, *args):
            img.height = img.width / img.image_ratio

        images_loaded = self.load_images_from_db(wall_layout, update_height)
        if images_loaded:
            scroll_view.add_widget(wall_layout)  # Adding the GridLayout to ScrollView
            self.add_widget(scroll_view)
        else:
            print("Cannot Find Images")

    def load_images_from_db(self, wall_layout, update_height):
        conn = sqlite3.connect('data/listing_data.db')  # Replace with your database path
        cursor = conn.cursor()
        images_found = False

        try:
            cursor.execute('SELECT image_source FROM vrbo_listings')
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    image_source = row[0]

                    if image_source is not None:
                        try:
                            image = Image(source=image_source,
                                               size_hint=(1, None),
                                               keep_ratio=True,
                                               allow_stretch=True)
                            image.bind(width=update_height, image_ratio=update_height)
                            wall_layout.add_widget(image)
                            images_found = True
                        except FileNotFoundError as e:
                            print(f"Image not found: {e}")
                    # You can handle missing images here, e.g., replace with a default image or show an error
                    # placeholder

        except sqlite3.Error as e:
            print(f"Error fetching images: {e}")

        finally:
            conn.close()

        return images_found

    def perform_search(self):
        self.sm.current = 'listing_screen'
        query = self.sm.get_screen('home_screen').ids.search_input.text
        # Add your search logic here
        print(f"Performing search for: {query}")
        #search_results = Search.scrape_airbnb(BASE_URL5)  # Replace with your actual search logic
        # self.update_homestays(search_results)
        #print(search_results)


class ListingScreen(Screen):
    pass


class ImageItem(TwoLineAvatarListItem):
    image_source = StringProperty()


class ArtemisApp(MDApp):
    def build(self):
        Builder.load_string(kv)
        screen_manager = ScreenManager()
        screen_manager.add_widget(Home(name='home_screen'))
        screen_manager.add_widget(ListingScreen(name='listing_screen'))

        return self.root
        pass

    def create_image_list(self, image_sources):
        for source in image_sources:
            item = ImageItem(text="Image", secondary_text="Secondary text")
            item.image_source = source
            self.root.ids.image_list.add_widget(item)


if __name__ == '__main__':
    BASE_URL5 = "https://www.airbnb.com/s/Seattle/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&monthly_start_date=2024-01-01&monthly_length=3&price_filter_input_type=0&channel=EXPLORE&date_picker_type=calendar&source=structured_search_input_header&search_type=filter_change"
    ArtemisApp().run()
