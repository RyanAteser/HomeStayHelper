import re
import sqlite3
import webbrowser

from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp

kv = """#:import hex kivy.utils.get_color_from_hex

<HomeScreen>:
    BoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Explore with Style"
            md_bg_color: app.theme_cls.primary_color
            specific_text_color: 1, 1, 1, 1
            elevation: 10
            right_action_items: [['magnify', lambda x: app.search_popup()]]
            left_action_items: [['menu', lambda x: app.open_menu()]]

        MDTextField:
            id: search_input
            hint_text: "Where to next?"
            helper_text: "Type and press enter"
            helper_text_mode: "on_focus"
            icon_right: "magnify"
            icon_right_color: app.theme_cls.primary_color
            pos_hint: {'center_x': 0.5}
            size_hint_x: None
            width: "280dp"
            theme_text_color: "Custom"
            line_color_focus: app.theme_cls.primary_color
            on_text_validate: app.update_search_url(self.text) if self.text.strip() else None

        BoxLayout:
            size_hint_y: None
            height: "50dp"
            padding: "10dp"

            MDLabel:
                text: "Sort by:"
                size_hint_x: None
                width: "70dp"
                theme_text_color: "Primary"

            MDRaisedButton:
                text: "Price"
                on_release: app.sort_by_price()

        ScrollView:
            id: scroll_view
            do_scroll_x: False
            do_scroll_y: True

            GridLayout:
                id: wall_layout
                cols: 1
                spacing: "10dp"
                size_hint_y: None
                height: self.minimum_height
                padding: "10dp"

                # Add dummy content for testing scrolling
                ImageViewerTile:
                    title: "Beautiful View"
                    beds: "3 Beds"
                    ratings: "5 Stars"
                    price: "$500 per night"
                ImageViewerTile:
                    title: "Oceanfront Condo"
                    beds: "2 Beds"
                    ratings: "4.5 Stars"
                    price: "$300 per night"
                ImageViewerTile:
                    title: "Mountain Retreat"
                    beds: "4 Beds"
                    ratings: "5 Stars"
                    price: "$400 per night"
                ImageViewerTile:
                    title: "City Apartment"
                    beds: "1 Bed"
                    ratings: "4 Stars"
                    price: "$150 per night"
                ImageViewerTile:
                    title: "Countryside Cottage"
                    beds: "3 Beds"
                    ratings: "4.5 Stars"
                    price: "$250 per night"

        MDFloatingActionButton:
            icon: "tune"
            pos_hint: {"center_x": 0.5}
            on_release: app.filter_options()

<ImageViewerTile>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(300)
    padding: "10dp"
    spacing: "10dp"
    canvas.before:
        Color:
            rgba: hex('#F5F5F5')
        RoundedRectangle:
            size: self.size
            pos: self.pos
            radius: [15, 15, 15, 15]

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.4

        Carousel:
            id: carousel
            size_hint: (1, 0.8)
            loop: True

        # Navigation buttons for the carousel
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            Button:
                text: '<'
                size_hint_x: 0.1
                on_press: carousel.load_previous()
            Button:
                text: '>'
                size_hint_x: 0.1
                on_press: carousel.load_next()

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.6

        MDLabel:
            text: root.title
            size_hint_y: None
            height: self.texture_size[1]
            halign: 'center'
            theme_text_color: "Primary"

        MDLabel:
            text: f"{root.beds}, {root.ratings}"
            size_hint_y: None
            height: self.texture_size[1]
            halign: 'center'
            theme_text_color: "Secondary"

        MDLabel:
            text: root.price
            size_hint_y: None
            height: self.texture_size[1]
            halign: 'center'
            theme_text_color: "Hint"

<LoginScreen>:
    id: 'login'
    BoxLayout:
        orientation: 'vertical'
        padding: '10dp'
        spacing: '10dp'

        MDTopAppBar:
            title: "Login"
            md_bg_color: app.theme_cls.primary_color
            specific_text_color: 1, 1, 1, 1
            elevation: 10

        BoxLayout:
            orientation: 'vertical'
            padding: '20dp'
            spacing: '20dp'
            size_hint_y: None
            height: self.minimum_height

            MDTextField:
                id: email
                hint_text: "Email"
                helper_text: "Enter your email"
                helper_text_mode: "on_focus"
                icon_right: "email"
                icon_right_color: app.theme_cls.primary_color
                pos_hint: {'center_x': 0.5}
                size_hint_x: None
                width: "280dp"
                required: True

            MDTextField:
                id: password
                hint_text: "Password"
                helper_text: "Enter your password"
                helper_text_mode: "on_focus"
                icon_right: "key"
                icon_right_color: app.theme_cls.primary_color
                pos_hint: {'center_x': 0.5}
                size_hint_x: None
                width: "280dp"
                password: True
                required: True

            MDRaisedButton:
                text: "Login"
                pos_hint: {'center_x': 0.5}
                size_hint_x: None
                width: "200dp"
                on_release: app.validate_login(email.text, password.text)

            MDLabel:
                id: login_message
                text: ""
                halign: 'center'
                theme_text_color: "Error"
"""


class LoginScreen():
    pass


class ImageViewerTile(BoxLayout):
    title = StringProperty()
    beds = StringProperty()
    ratings = StringProperty()
    price = StringProperty()
    image_urls = ListProperty()
    listing_id = StringProperty()

    def __init__(self, **kwargs):
        super(ImageViewerTile, self).__init__(**kwargs)
        for image_url in self.image_urls:
            image = AsyncImage(source=image_url, allow_stretch=True, keep_ratio=False)
            image.bind(on_touch_down=self.on_image_click)
            self.ids.carousel.add_widget(image)

    def on_image_click(self, instance, touch):
        if instance.collide_point(*touch.pos):
            webbrowser.open(f"https://www.vrbo.com/{self.listing_id}")


class HomeScreen(Screen):
    def add_images(self, image_urls):
        grid_layout = self.ids.wall_layout
        grid_layout.clear_widgets()
        for img_url in image_urls:
            tile = ImageViewerTile(source=img_url)
            grid_layout.add_widget(tile)


class MyApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_page = 1
        self.current_table = ""
        self.scroll_y = 1  # Default scroll position

    def build(self):

        self.root = HomeScreen()
        self.update_ui()
        # Call scraping method after app initialization
        return self.root

    def update_search_url(self, search_text):
        if search_text.strip():
            sanitized_name = self.sanitize_search_text(search_text)
            self.current_table, was_created = self.ensure_table_exists(sanitized_name)
            self.fetch_and_update_ui(self.current_table)

    def fetch_and_update_ui(self, table_name):
        data = self.fetch_from_db(table_name)
        self.update_ui()

    def fetch_from_db(self, table_name):
        try:
            with sqlite3.connect('data/Listings_data.db') as conn:
                c = conn.cursor()
                c.execute(f'SELECT listing_id, image_url, price, title, beds, ratings FROM {table_name}')
                return [{'listing_id': row[0],
                         'image_sources': row[1].split(',') if row[1] else ["WebScraper-main/data/img.png"],
                         'price': row[2] if row[2] else "Price not available",
                         'title': row[3] if row[3] else "Title not available",
                         'beds': row[4] if row[4] else "Bed info not available",
                         'ratings': row[5] if row[5] else "Rating not available"} for row in c.fetchall()]
        except sqlite3.Error as e:
            print(f"An error occurred when accessing {table_name}: {e}")
            return []

    def get_images_by_listing(self, table_name):
        conn = sqlite3.connect('data/Listings_data.db')
        cursor = conn.cursor()

        try:
            query = f"SELECT listing_id, image_url, price, title, beds, ratings FROM {table_name}"
            cursor.execute(query)
            results = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            results = []

        conn.close()

        images_by_listing = {}
        for row in results:
            if len(row) == 6:
                listing_id, image_url, price, title, beds, ratings = row
                if listing_id not in images_by_listing:
                    images_by_listing[listing_id] = {
                        'listing_id': listing_id,
                        'images': [],
                        'price': price,
                        'title': title,
                        'beds': beds,
                        'ratings': ratings
                    }
                images_by_listing[listing_id]['images'].append(image_url)
            else:
                print(f"Unexpected number of columns: {len(row)}")

        return images_by_listing

    def update_ui(self):
        if self.current_table:
            data = self.get_images_by_listing(self.current_table)
            if data:
                scroll_view = self.root.ids.scroll_view
                self.scroll_y = scroll_view.scroll_y  # Save the current scroll position

                self.root.ids.wall_layout.clear_widgets()
                for listing_id, info in data.items():
                    tile = ImageViewerTile(image_urls=info['images'],
                                           price=info.get('price', "Price not available"),
                                           title=info.get('title', "Title not available"),
                                           beds=info.get('beds', "Bed info not available"),
                                           ratings=info.get('ratings', "Rating not available"),
                                           listing_id=listing_id)
                    self.root.ids.wall_layout.add_widget(tile)

                scroll_view.scroll_y = self.scroll_y  # Restore the scroll position
            else:
                print("No data to display")

    def sort_by_price(self):
        if self.current_table:
            data = self.fetch_from_db(self.current_table)
            # Remove currency symbol and commas, then convert to float for sorting
            data.sort(key=lambda x: float(re.sub(r'[^\d.]', '', x['price'].split()[0])) if x[
                                                                                               'price'] != "Price not available" else float(
                'inf'))
            self.root.ids.wall_layout.clear_widgets()
            for info in data:
                tile = ImageViewerTile(image_urls=info['image_sources'],
                                       price=info.get('price', "Price not available"),
                                       title=info.get('title', "Title not available"),
                                       beds=info.get('beds', "Bed info not available"),
                                       ratings=info.get('ratings', "Rating not available"),
                                       listing_id=info['listing_id'])
                self.root.ids.wall_layout.add_widget(tile)

    def insert_into_db(self, table_name, data):
        conn = sqlite3.connect('data/Listings_data.db')
        c = conn.cursor()
        c.execute(
            f"INSERT INTO {table_name} (listing_id, image_url, price, title, beds, ratings) VALUES (?, ?, ?, ?, ?, ?)",
            (data['listing_id'], data['image_url'], data['price'], data['title'], data['beds'], data['ratings']))
        conn.commit()
        conn.close()

    def ensure_table_exists(self, sanitized_name):
        conn = sqlite3.connect('data/Listings_data.db')
        c = conn.cursor()
        table_name = f"{sanitized_name}"
        try:
            c.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id TEXT,
                    image_url TEXT,
                    price TEXT,
                    title TEXT,
                    beds TEXT,
                    ratings TEXT
                )
            """)
            conn.commit()
            was_created = c.rowcount == -1
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            was_created = False
        finally:
            conn.close()
        return table_name, was_created

    def sanitize_search_text(self, text):
        sanitized_name = ''.join(c for c in text if c.isalnum()).lower()
        return sanitized_name

    def validate_login(self, email, password):
        # Dummy validation logic, replace with actual logic
        if email == "" and password == "":
            self.sm.current = 'home'
        else:
            self.root.ids.login_message.text = "Invalid email or password"


if __name__ == "__main__":
    Builder.load_string(kv)
    app = MyApp()
    app.run()
