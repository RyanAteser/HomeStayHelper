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
<HomeScreen>:
    Button:
        id: next_page
        text: "Next Page"
        md_bg_color: "#3D5A80"
        
        width: dp(150)
        height: dp(48)
       
        opacity: 0  # Button is initially invisible
        disabled: True  # Button is initially disabled
        on_release: app.fetch_next_page()
    BoxLayout:
        orientation: "vertical"
        
        MDTopAppBar:
            title: "Artemis"
            md_bg_color: app.theme_cls.primary_color
            specific_text_color: 1, 1, 1, 1
            elevation: 10
            right_action_items: [['sort', lambda x: app.cycle_sort_methods()]]
            left_action_items: [['dots-vertical', lambda x: app.open_menu()]]



        MDTextField:
            id: search_input
            hint_text: "Enter destination..."
            helper_text: "Type and press enter"
            helper_text_mode: "on_focus"
            icon_right: "magnify"
            icon_right_color: app.theme_cls.primary_color
            pos_hint: {'center_x': 0.5}
            size_hint_x: None
            width: "300dp"
            theme_text_color: "Custom"
            line_color_focus: app.theme_cls.primary_color
            on_text_validate: app.update_search_url(self.text) if self.text.strip() else None
            multiline: False
        

        ScrollView:
            id: scroll
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
            icon: "shuffle"
            on_release: app.cycle_sort_methods()


<ImageViewerTile>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(300)  # Adjusted height for images
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1  # White border color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]  # Rounded corner radius

    AsyncImage:
        source: root.source
        size_hint_x: 0.7  # Set the image width to 70% of the tile width
        allow_stretch: True
        keep_ratio: True

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.3  # Set the labels width to 30% of the tile width
        padding: dp(10)
        spacing: dp(5)

        MDLabel:
            text: root.price
            size_hint_y: None
            height: self.texture_size[1]  # Adjust the height of the label to fit the text
            halign: 'center'  # Center the text horizontally

        MDLabel:
            text: root.beds
            size_hint_y: None
            height: self.texture_size[1]  # Adjust the height of the label to fit the text
            halign: 'center'  # Center the text horizontally

        MDLabel:
            text: root.ratings
            size_hint_y: None
            height: self.texture_size[1]  # Adjust the height of the label to fit the text
            halign: 'center'  # Center the text horizontally

"""

class ImageViewerTile(BoxLayout):
    source = StringProperty()
    price = StringProperty()
    beds = StringProperty()
    ratings = StringProperty()

    def __init__(self, source='', **kwargs):
        super(ImageViewerTile, self).__init__(**kwargs)
        image = AsyncImage(source=source, allow_stretch=True, keep_ratio=False)
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

    def build(self):
        self.root = HomeScreen()
        return self.root

    def update_search_url(self, search_text):
        self.search_url = f"https://www.vrbo.com/search?adults=2&destination={search_text}+%28and+vicinity%29%2C+Washington%2C+United+States+of+America"
        # Simulate a scrape or use the actual scraping function
        Clock.schedule_once(self.start_scraping)

    def start_scraping(self, dt):
        # Example data fetching, replace with actual scrape data fetching
        scraped_data = Search_Vrbo.scrape_vrbo(self.search_url)
        self.update_ui(scraped_data, 'Vrbo.com')

    def update_ui(self, data, source):
        if data:
            # Extract the image file paths
            image_urls = [item['image_sources'][0] for item in data if item['image_sources']]
            print(f"Image URLs to display: {image_urls}")
            self.root.add_images(image_urls)
        else:
            print(f"No data fetched from {source}")


if __name__ == "__main__":
    Builder.load_string(kv)
    app = MyApp()
    app.run()
