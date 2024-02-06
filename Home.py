import base64
import io
import logging
import sqlite3
import traceback
import zlib
from io import BytesIO

import requests
from PIL import Image as PilImage
from PIL import Image
from kivy.atlas import CoreImage
from kivy.config import Config
from kivy.core.image import ImageLoader
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty, ListProperty, StringProperty, NumericProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image as KivyImage, AsyncImage
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp

import Search_Vrbo

Config.set('kivy', 'log_level', 'debug')
kv = """
ScreenManager:
    Home:
        name: "home_screen"
    ListingScreen:
        name: "listing_screen"

<ImageItem>:
    orientation: 'vertical'
    spacing: '5dp'
    padding: '5dp'
    size_hint_y: None
    height: '200dp'
    # Create AsyncImage widgets using the image_sources property
    AsyncImage:
        source: root.images_loaded[0]
        allow_stretch: True
    AsyncImage:
        source: root.images_loaded[1]
        allow_stretch: True
    AsyncImage:
        source: root.images_loaded[2]
        allow_stretch: True

<Home>:
    BoxLayout:
        orientation: "vertical"

        # Top Bar
        MDTopAppBar:
            title: "Artemis"
            md_bg_color: "#556b2f"
            elevation: 4

        # Search Bar
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: "60dp"
            padding: "10dp"

            MDTextField:
                id: search_input
                hint_text: "Search"
                size_hint_x: 0.7
                mode: "rectangle"

            MDRectangleFlatButton:
                text: "Search"
                theme_text_color: "Primary"
                size_hint_x: 0.3
                on_release: app.root.get_screen('home_screen').perform_search()
                md_bg_color: "#556b2f"

        # Rest of your content (e.g., ScrollView with GridLayout)
        ScrollView:
            GridLayout:
                id: wall_layout
                cols: 3
                spacing: "10dp"
                size_hint_y: None
                height: self.minimum_height
                padding: "10dp"
"""

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.imagelist import MDSmartTile
from kivy.uix.scrollview import ScrollView


class Home(MDApp):
    def __init__(self, images):
        super().__init__()
        self.images = images
        self.db_connection = sqlite3.connect('data/listing_data.db')
        self.cursor = self.db_connection.cursor()

    def get_image_url(self, image_source):
        try:
            # Assuming image_source is the URL of the image stored in the database
            query = "SELECT image_source FROM vrbo_listings WHERE image_source = ?"
            self.cursor.execute(query, (image_source,))
            result = self.cursor.fetchone()
            if result:

                return zlib.decompress(base64.urlsafe_b64decode(result[0]))  # Decode the byte string using Latin-1 encoding
            else:
                print("Results: ", result)
                print(f"No image found in the database for image source: {image_source}")
        except Exception as e:
            print(f"Error fetching image from database: {e}")
        return None

    def create_image_grid(self):
        # Customize this function based on the desired layout and appearance
        # of the image grid.
        # Here, I'm using a simple GridLayout with fixed columns for demonstration.
        from kivy.uix.gridlayout import GridLayout

        grid_layout = GridLayout(cols=3, spacing=10, size_hint_y=None)
        grid_layout.bind(minimum_height=grid_layout.setter('height'))
        return grid_layout

    def build(self):
        screen = MDScreen()
        scroll_view = ScrollView()

        # Create a GridLayout to display images
        grid_layout = self.create_image_grid()

        # Add MDImage widgets to the GridLayout
        for image_data in self.images:
            image_sources = image_data.get('image_sources', [])

            image_url = self.get_image_url(image_sources)
            if image_url:
                # Create an AsyncImage widget with the URL as the source
                image_widget = AsyncImage(
                    source=image_url,
                    allow_stretch=True
                )
                grid_layout.add_widget(image_widget)
            else:
                # Handle the case where image URL is not available
                print("No image URL found for this listing")

        # Add the GridLayout to the ScrollView
        scroll_view.add_widget(grid_layout)
        screen.add_widget(scroll_view)

        return screen


if __name__ == "__main__":
    vrbo_url = "https://www.vrbo.com/search?adults=2&d1=&d2=&destination=Seattle+%28and+vicinity%29%2C+Washington%2C" \
               "+United+States+of+America&endDate=&regionId=178307&semdtl=&sort=RECOMMENDED&startDate=& "
    scraped_data = Search_Vrbo.scrape_vrbo(vrbo_url)
    Home(scraped_data).run()



