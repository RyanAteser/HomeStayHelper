import base64
import zlib

from kivy.lang import Builder
from kivy.uix.carousel import Carousel
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.imagelist import MDSmartTile
import Search_Vrbo

kv = """
<HomeScreen>:
    BoxLayout:
        orientation: "vertical"
        ScrollView:
            GridLayout:
                id: wall_layout
                cols: 3
                spacing: "10dp"
                size_hint_y: None
                height: self.minimum_height
                padding: "10dp"
    
    MDTopAppBar:
        title: "Artemis"
        md_bg_color: "#556b2f"
        elevation: 4
        size_hint_y: '.07'
"""


class HomeScreen(Screen):
    def __init__(self, images=None, **kwargs):
        super().__init__(**kwargs)
        if images is None:
            images = []
        self.images = images
        self.create_image_carousel()

    def create_image_carousel(self):
        carousel = Carousel(direction='right', loop=True)
        for image_data in self.images:
            image_sources = image_data.get('image_sources', [])
            for image_source in image_sources:
                # Create AsyncImage with image source
                image = AsyncImage(source=str(image_source), size_hint=(None, None), size=(400, 400))
                carousel.add_widget(image)
        self.add_widget(carousel)


class MyApp(MDApp):
    def __init__(self, images=None, **kwargs):
        super().__init__(**kwargs)

        if images is None:
            images = []
        self.images = images

    def build(self):
        return HomeScreen(images=self.images)


if __name__ == "__main__":
    # Load the kv file after defining the HomeScreen class
    Builder.load_string(kv)

    vrbo_url = "https://www.vrbo.com/search?adults=2&d1=&d2=&destination=Seattle+%28and+vicinity%29%2C+Washington%2C" \
               "+United+States+of+America&endDate=&regionId=178307&semdtl=&sort=RECOMMENDED&startDate=& "
    scraped_data = Search_Vrbo.scrape_vrbo(vrbo_url)
    MyApp(scraped_data).run()
