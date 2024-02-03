import base64
import sqlite3
import traceback
import zlib
from io import BytesIO

import requests
from PIL import Image as PilImage
from kivy.atlas import CoreImage
from kivy.config import Config
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty, ListProperty, StringProperty, NumericProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image as KivyImage, AsyncImage
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp

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

from kivy.uix.boxlayout import BoxLayout


# ... (existing code)

class ImageItem(BoxLayout):
    beds = ObjectProperty(None)
    image_sources = ListProperty([])
    price = StringProperty('')
    ratings = NumericProperty(0)

    def __init__(self, image_sources=None, price='', beds='', ratings=0, **kwargs):
        super(ImageItem, self).__init__(**kwargs)
        self.create_image_widget(image_sources, price, beds, ratings)

    def create_image_widget(self, image_sources, price, beds, ratings):
        try:
            print(f"Creating image widget with sources: {image_sources}")

            if image_sources != "Not Available" and all(image_sources):
                # Decompress the image data
                try:
                    # Decode base64-encoded and zlib-compressed image data
                    decoded_data = zlib.decompress(base64.b64decode(image_sources))

                    # Convert decoded binary data to a list of image sources
                    decompressed_images = decoded_data.decode().split(',')

                    # Initialize the size of the combined image
                    combined_width, combined_height = 0, 0

                    # Fetch each image part and combine them
                    image_parts = []
                    for base64_image in decompressed_images:
                        try:
                            # Decode base64-encoded image
                            image_data = base64.b64decode(base64_image)
                            part_image = PilImage.open(BytesIO(image_data))

                            # Update combined image size based on the dimensions of the part image
                            combined_width = max(combined_width, part_image.width)
                            combined_height += part_image.height

                            image_parts.append(part_image)
                        except Exception as fetch_error:
                            print(f"Error decoding base64 image: {fetch_error}")
                            # Handle the case where decoding fails (e.g., replace with a placeholder image)
                            image_parts.append(PilImage.new('RGB', (100, 100), color='red'))

                    # Create a new combined image with the calculated size
                    combined_image = PilImage.new('RGB', (combined_width, combined_height))

                    # Paste each image part into the combined image
                    y_offset = 0
                    for part_image in image_parts:
                        combined_image.paste(part_image, (0, y_offset))
                        y_offset += part_image.height

                    # Convert combined image to Kivy Image
                    buffer = BytesIO()
                    combined_image.save(buffer, format='png')
                    buffer.seek(0)
                    kivy_image = KivyImage(texture=CoreImage(BytesIO(buffer.getvalue()), ext='png').texture)
                    self.add_widget(kivy_image)

                    # Add Labels for details
                    details_label = Label(text=f"Price: {price}\nBeds: {beds}\nRatings: {ratings}", halign='center')
                    self.add_widget(details_label)

                except zlib.error as zlib_error:
                    print(f"Error during decompression: {zlib_error}")
                except Exception as e:
                    print(f"Error creating image widget: {e}")
                    print(f"Failed image_sources: {image_sources}, price: {price}, beds: {beds}, ratings: {ratings}")

        except Exception as outer_exception:
            print(f"An error occurred in the outer try block: {outer_exception}")


class Home(Screen):
    def __init__(self, **kwargs):
        super(Home, self).__init__(**kwargs)
        self.callback()

    def callback(self):
        print("Grabbing image from the database:")
        scroll_view = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        wall_layout = GridLayout(cols=3, size_hint_y=None)
        wall_layout.bind(minimum_height=wall_layout.setter('height'))

        try:
            image_items = self.load_images_from_db()
            if image_items:
                for item in image_items:
                    wall_layout.add_widget(item)
                scroll_view.add_widget(wall_layout)
                self.add_widget(scroll_view)
            else:
                print("No images found in the database.")
        except Exception as e:
            print("Error in callback:", e)
            traceback.print_exc()

    def load_images_from_db(self):
        image_items = []
        conn = sqlite3.connect('data/listing_data.db')
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT image_source, price, beds, ratings FROM vrbo_listings')
            rows = cursor.fetchall()

            if rows:
                for row in rows:
                    image_source, price, beds, ratings = row
                    print(f"Processing image_source: {image_source}, type: {type(image_source)}")
                    # Check if image_source is not None before processing
                    if image_source is not None:
                        try:
                            # Attempt to convert ratings to float
                            ratings = float(ratings) if ratings.replace('.', '', 1).isdigit() else 0.0

                            # Wrap the ImageItem creation in a try-except block
                            try:
                                item = ImageItem(image_sources=[image_source], price=price, beds=beds, ratings=ratings)
                                image_items.append(item)
                            except Exception as item_creation_error:
                                print(f"Error creating ImageItem for {image_source}: {item_creation_error}")
                        except ValueError as rating_conversion_error:
                            print(f"Attempting to convert ratings to float: {ratings}")
                            print(f"Error processing image source: {image_source}\n{rating_conversion_error}")
                            ratings = 0.0
                        except Exception as e:
                            print(f"Error processing image: {e}")
        except sqlite3.Error as db_error:
            print(f"Error fetching images from the database: {db_error}")
        except Exception as general_error:
            print(f"General error in load_images_from_db: {general_error}")
        finally:
            conn.close()

        return image_items

    def load_images_from_db(self):
        image_items = []
        conn = sqlite3.connect('data/listing_data.db')
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT image_source, price, beds, ratings FROM vrbo_listings')
            rows = cursor.fetchall()

            if rows:
                for row in rows:
                    image_source, price, beds, ratings = row
                    print(f"Processing image_source: {image_source}, type: {type(image_source)}")
                    # Check if image_source is not None before processing
                    if image_source is not None:
                        try:
                            # Decode base64-encoded and zlib-compressed image data
                            decoded_data = zlib.decompress(base64.b64decode(image_source))

                            # Convert decoded binary data to a list of image sources
                            decompressed_images = decoded_data.decode().split(',')

                            # Wrap the ImageItem creation in a try-except block
                            try:
                                item = ImageItem(image_sources=decompressed_images, price=price, beds=beds,
                                                 ratings=ratings)
                                image_items.append(item)
                            except Exception as item_creation_error:
                                print(f"Error creating ImageItem for {image_source}: {item_creation_error}")
                        except Exception as decoding_error:
                            print(f"Error decoding image source: {image_source}\n{decoding_error}")
        except sqlite3.Error as db_error:
            print(f"Error fetching images from the database: {db_error}")
        except Exception as general_error:
            print(f"General error in load_images_from_db: {general_error}")
        finally:
            conn.close()

        return image_items


def update_height(self, img, *args):
    img.height = img.width / img.image_ratio if img.image_ratio else 1


def perform_search(self):
    self.sm.current = 'listing_screen'
    query = self.sm.get_screen('home_screen').ids.search_input.text
    print(f"Performing search for: {query}")


class ListingScreen(Screen):
    pass


class ArtemisApp(MDApp):
    def build(self):
        try:
            self.root = Builder.load_string(kv)
            screen_manager = ScreenManager()
            screen_manager.add_widget(Home(name='home_screen'))
            screen_manager.add_widget(ListingScreen(name='listing_screen'))
            return self.root
        except Exception as e:
            print(f"An error occurred: {e}")

    def on_error(self, *args):
        print(f"Kivy Error: {args}")

    def create_image_list(self, image_source):
        for source in image_source:
            item = ImageItem(text="Image", secondary_text="Secondary text")
            item.image_source = source
            self.root.ids.image_list.add_widget(item)


if __name__ == '__main__':
    ArtemisApp().run()

