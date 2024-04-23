from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivy.properties import StringProperty
import sqlite3
import Search_Vrbo

kv = """
#:import hex kivy.utils.get_color_from_hex
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

        ScrollView:
            do_scroll_x: False
            do_scroll_y: True

            GridLayout:
                id: wall_layout
                cols: 1
                spacing: "10dp"
                size_hint_y: None
                adaptive_height: True
                padding: "10dp"

        MDFloatingActionButton:
            icon: "tune"
            pos_hint: {"center_x": 0.5}
            on_release: app.filter_options()

<ImageViewerTile>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(300)
    padding: dp(8)
    canvas.before:
        Color:
            rgba: 0, 0, 0, 1  # Black border
        Line:
            rectangle: self.x + 1, self.y + 1, self.width - 2, self.height - 2
            width: 1.2

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.3
        padding: dp(10)
        spacing: dp(5)

        MDLabel:
            text: root.price
            size_hint_y: None
            height: self.texture_size[1]
            halign: 'center'
            theme_text_color: "Primary"

        MDLabel:
            text: root.beds
            size_hint_y: None
            height: self.texture_size[1]
            halign: 'center'
            theme_text_color: "Secondary"

        MDLabel:
            text: root.ratings
            size_hint_y: None
            height: self.texture_size[1]
            halign: 'center'
            theme_text_color: "Hint"

    AsyncImage:
        source: root.source
        size_hint_x: 0.8
        allow_stretch: True
        keep_ratio: True
        halign:'left'


"""


class ImageViewerTile(BoxLayout):
    source = StringProperty()
    price = StringProperty()
    beds = StringProperty()
    ratings = StringProperty()

    def __init__(self, source='', price=None, beds=None, ratings=None, **kwargs):
        super(ImageViewerTile, self).__init__(**kwargs)
        self.price = price if price is not None else 'Unknown'
        self.beds = beds if beds is not None else 'Unknown'
        self.ratings = ratings if ratings is not None else 'Unknown'
        image = AsyncImage(source=source or 'default.png', allow_stretch=True, keep_ratio=False)
        self.add_widget(image)


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

    def build(self):
        self.root = HomeScreen()
        self.update_ui()
        Clock.schedule_once(self.start_scraping, 0)  # Call scraping method after app initialization
        return self.root

    def update_search_url(self, search_text):
        if search_text.strip():
            sanitized_name = self.sanitize_search_text(search_text)
            self.current_table, was_created = self.ensure_table_exists(sanitized_name)
            self.fetch_and_update_ui(self.current_table)

    def start_scraping(self, dt):
        if self.current_table:
            # Perform scraping here, possibly using a method like `scrape_vrbo` shown earlier
            scraped_data = Search_Vrbo.scrape_vrbo("https://www.vrbo.com/search?query=" + self.current_table,
                                                   self.current_table)
            # Assuming scraped_data is a list of dictionaries with expected keys
            for data in scraped_data:
                self.insert_into_db(self.current_table, data)
            self.fetch_and_update_ui(self.current_table)

    def fetch_and_update_ui(self, table_name):
        data = self.fetch_from_db(table_name)
        self.update_ui()

    def fetch_from_db(self, table_name):
        try:
            with sqlite3.connect('data/listing_data.db') as conn:
                c = conn.cursor()
                c.execute(f'SELECT image_url, price, beds, ratings FROM {table_name}')
                return [{'image_sources': [row[0] if row[0] else "WebScraper-main/data/img.png"],
                         'price': row[1] if row[1] else "Price not available",
                         'beds': row[2] if row[2] else "Bed info not available",
                         'ratings': row[3] if row[3] else "Rating not available"} for row in c.fetchall()]
        except sqlite3.Error as e:
            print(f"An error occurred when accessing {table_name}: {e}")
            return []

    def get_images_by_listing(self, table_name):
        conn = sqlite3.connect('data/listing_data.db')
        cursor = conn.cursor()

    # Ensure the query is correct and the table name is sanitized
        query = f"SELECT listing_id, image_url, price, beds, ratings FROM {table_name}"
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        images_by_listing = {}
        for listing_id, image_url, price, beds, ratings in results:
            if listing_id not in images_by_listing:
                images_by_listing[listing_id] = {
                'images': [],
                'price': price,
                'beds': beds,
                'ratings': ratings
            }
            images_by_listing[listing_id]['images'].append(image_url)
        return images_by_listing

    def update_ui(self):
        if self.current_table:
            data = self.get_images_by_listing(self.current_table)
            if data:
                self.root.ids.wall_layout.clear_widgets()
                for listing_id, info in data.items():
                    for image_url in info['images']:
                        tile = ImageViewerTile(source=image_url,
                                               price=info['price'],
                                               beds=info['beds'],
                                               ratings=info['ratings'])
                        self.root.ids.wall_layout.add_widget(tile)
            else:
                print("No data to display")

    def insert_into_db(self, table_name, data):
        conn = sqlite3.connect('data/listing_data.db')
        c = conn.cursor()
        # Example insert, adjust according to your data structure
        c.execute(f"INSERT INTO {table_name} (listing_id, image_url, price, beds, ratings) VALUES (?, ?, ?, ?, ?)",
                  (data['listing_id'], data['image_url'], data['price'], data['beds'], data['ratings']))
        conn.commit()
        conn.close()




    def ensure_table_exists(self, sanitized_name):
        conn = sqlite3.connect('data/listing_data.db')
        c = conn.cursor()
        table_name = f"{sanitized_name}"
        try:
            # This SQL statement ensures that the table will only be created if it does not exist.
            c.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT,
            image_url TEXT,
            price TEXT,
            beds TEXT,
            ratings TEXT
        )
        """)
            conn.commit()
            # Determine if the table was just created or already existed
            was_created = c.rowcount == -1  # If rowcount is -1, no new table was created
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            was_created = False  # Assume the table wasn't created if there's an error
        finally:
            conn.close()
        return table_name, was_created

    def sanitize_search_text(self, text):
        # Basic sanitization to remove special characters and spaces
        sanitized_name = ''.join(c for c in text if c.isalnum()).lower()  # Lowercase to ensure consistency
        return sanitized_name


if __name__ == "__main__":
    Builder.load_string(kv)
    app = MyApp()
    app.run()