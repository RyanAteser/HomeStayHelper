from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.carousel import MDCarousel
from kivymd.uix.label import MDLabel

import Search_Vrbo

# Assuming you have already defined and imported Search_Vrbo and its functions
from kivy.uix.textinput import TextInput

kv = """
<HomeScreen>:
    BoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Artemis"
            md_bg_color: "#556b2f"
            elevation: 1
            size_hint_y: None

        BoxLayout:
            size_hint_y: None
            height: "48dp"
            padding: "8dp"
            spacing: "8dp"
            orientation: "horizontal"

            TextInput:
                id: search_input
                hint_text: "Enter destination..."
                multiline: False
                on_text_validate: app.update_search_url(self.text) if self.text.strip() else None


        ScrollView:
            GridLayout:
                id: wall_layout
                cols: 1  # Set the number of columns to 7
                spacing: "40dp"
                size_hint_y: None
                height: self.minimum_height
                padding: "40dp"

    
<ImageViewerTile>:
    orientation: 'horizontal'

    AsyncImage:
        source: root.source
        size_hint_x: None  # Disable size hint for width
        width: dp(200)     # Set the width of the image
        size_hint_y: 1 

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.5

        MDLabel:
            text: root.price
            halign: 'center'
            theme_text_color: "Primary"

        MDLabel:
            text: root.beds
            halign: 'center'
            theme_text_color: "Primary"

        MDLabel:
            text: root.ratings
            halign: 'center'
            theme_text_color: "Primary"
<ListingInfo>
    
    text: "Listing info"
    MDButton:
    style: "filled"

    MDButtonText:
        text: "Go to Website"
        
    
"""


class HomeScreen(Screen):
    def __init__(self, images=None, **kwargs):
        super().__init__(**kwargs)
        if images is None:
            images = []
        self.images = images
        self.create_image_grid()

    def create_image_grid(self):
        grid_layout = self.ids.wall_layout
        prices_dict = {}

        for image_data in self.images:
            image_sources = image_data.get('image_sources', [])
            price = image_data.get('price', 'Not available')
            beds = image_data.get('beds', 'Not available')
            ratings = image_data.get('ratings', 'Not available')

            if price not in prices_dict:
                prices_dict[price] = []

            prices_dict[price].append({'image_sources': image_sources, 'beds': beds, 'ratings': ratings})

        for price, images_data in prices_dict.items():
            carousel = MDCarousel(direction='right', loop=True)
            for data in images_data:
                image_sources = data['image_sources']
                beds = data['beds']
                ratings = data['ratings']

                # Create BoxLayout to hold image and additional information
                image_container = MDBoxLayout(orientation='vertical', spacing='5dp', size_hint_y=None)

                for image_source in image_sources:
                    # Create AsyncImage with image source
                    image = AsyncImage(source=str(image_source), size_hint=(None, None), size=(100, 100))

                    # Create labels for beds and ratings
                    beds_label = MDLabel(text=f"Beds: {beds}", size_hint_y=None, height='10dp', halign='center')
                    ratings_label = MDLabel(text=f"Ratings: {ratings}", size_hint_y=None, height='10dp',
                                            halign='center')

                    # Add widgets to image_container
                    image_container.add_widget(image)
                    image_container.add_widget(beds_label)
                    image_container.add_widget(ratings_label)

                carousel.add_widget(image_container)

            scrollview = ScrollView(size_hint_y=None)
            scrollview.add_widget(carousel)
            grid_layout.add_widget(scrollview)


class MyApp(MDApp):
    def __init__(self, images=None, **kwargs):
        super().__init__(**kwargs)
        if images is None:
            images = []
        self.images = images
        self.search_url = "https://www.vrbo.com/search?adults=2&d1=&d2=&destination=Seattle+%28and+vicinity%29%2C+Washington%2C" \
                          "+United+States+of+America&endDate=&regionId=178307&semdtl=&sort=RECOMMENDED&startDate=&"

    def build(self):
        root = HomeScreen()
        root.create_image_grid()  # Call create_image_grid to populate the wall_layout initially
        return root

    def update_search_url(self, search_text):
        if not search_text:
            # Handle empty search text (e.g., display error message or perform default search)
            return

        # Update the URL based on the search input
        self.search_url = f"https://www.vrbo.com/search?&destination={search_text}"
        # Reload the data based on the updated URL
        self.root.ids.wall_layout.clear_widgets()
        scraped_data = Search_Vrbo.scrape_vrbo(self.search_url)
        print(scraped_data)
        self.root.add_widget(HomeScreen(images=scraped_data))
        return self.search_url


if __name__ == "__main__":
    Builder.load_string(kv)
    app = MyApp()
      # Prompt the user to enter search text
      # Call instance method with search_text
 # Pass the updated URL to scrape_vrbo
    app.run()  # Run the app
