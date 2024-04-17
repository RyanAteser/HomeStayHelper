from kivy.clock import Clock
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
import Search_Bnb
import Search_book

# Assuming you have already defined and imported Search_Vrbo and its functions
from kivy.uix.textinput import TextInput

kv = """
<HomeScreen>:
    Button:
        text: "Next Page"
        md_bg_color: "#3D5A80"
        size_hint_y: None
        height: "48dp"
        on_press: app.fetch_next_page()
        
    BoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Artemis"
            md_bg_color: "#3D5A80"
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
                cols: 1  # Adjusted for better visual spacing
                spacing: "20dp"
                size_hint_y: None
                height: self.minimum_height
                padding: "20dp"

<ImageViewerTile>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(300)  # Adjust height for better display

    MDCarousel:
        size_hint_y: 1
        AsyncImage:
            source: root.source
            size_hint_y: 1
            keep_ratio: True
            allow_stretch: True

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: 0.5
        padding: "10dp"

        MDLabel:
            text: root.price
            size_hint_y: None
            height: "30dp"
            theme_text_color: "Primary"


        MDLabel:
            text: root.beds
            size_hint_y: None
            height: "30dp"
            theme_text_color: "Primary"

        MDLabel:
            text: root.ratings
            size_hint_y: None
            height: "30dp"
            theme_text_color: "Primary"
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
        grid_layout.clear_widgets()  # Clear existing widgets
        if not self.images:
            no_data_label = MDLabel(text="No data available", halign="center")
            grid_layout.add_widget(no_data_label)
            return

        prices_dict = {}
        print("getting data....")
        for image_data in self.images:

            image_sources = image_data.get('image_sources', [])
            if not image_sources:  # Skip if there are no images
                continue
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
                image_container = MDBoxLayout(orientation='vertical', spacing='5dp')

                for image_source in image_sources:
                    image = AsyncImage(source=str(image_source), size_hint=(None, None), size=(300, 300))
                    price_label = MDLabel(text=f"price: {price}", size_hint_y=None, height='10dp', halign='right')
                    beds_label = MDLabel(text=f"Beds: {beds}", size_hint_y=None, height='10dp', halign='right')
                    ratings_label = MDLabel(text=f"Ratings: {ratings}", size_hint_y=None, height='10dp', halign='right')
                    image_container.add_widget(image)
                    image_container.add_widget(price_label)
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
        self.current_page = 1

    def fetch_next_page(self):
        self.current_page += 1

        print("Fetching next page:", self.current_page)
        # Assume scraping functions can take a 'page' argument
        scraped_data = Search_Vrbo.scrape_vrbo(self.search_url, self.current_page)
        scrape_bnb = Search_Bnb.scrape_bnb(self.search_url2)
        scrape_book = Search_book.scrape_booking(self.search_url3, self.current_page)

        # Schedule UI updates after fetching data
        Clock.schedule_once(lambda dt: self.update_ui(scraped_data, 'Vrbo.com'))
        Clock.schedule_once(lambda dt: self.update_ui(scrape_bnb, 'Airbnb.com'))
        Clock.schedule_once(lambda dt: self.update_ui(scrape_book, 'Booking.com'))

    def build(self):
        root = HomeScreen()
        root.create_image_grid()
        # Call create_image_grid to populate the wall_layout initially
        return root

    def update_search_url(self, search_text):
        if not search_text:
            # Handle empty search text (e.g., display error message or perform default search)
            return
        checkOut = "2024-05-08"
        checkIn = "2024-05-05"
        # Update the URL based on the search input
        self.search_url = f"https://www.vrbo.com/search?&destination={search_text}"
        self.search_url2 = f"https://www.airbnb.com/s/{search_text}"
        self.search_url3 = (
            f"https://www.booking.com/searchresults.html?ss={search_text}&efdco=1&label=gen173nr-1FCAEoggI46AdIM1gEaLQCiAEBmAExuAEXyAEM2AEB6AEB-AECiAIBqAIDuAKW6fawBsACAdICJGRjYWUxNTU5LThmOGQtNGZlOS05NWIyLTgwMDc3MGUyMDQyN9gCBeACAQ&aid=304142&lang=en-us&sb=1&src_elem=sb&src=searchresults&dest_id=20144883&dest_type=city&checkin="
            f"{checkIn}&checkout={checkOut}&group_adults=2&no_rooms=1&group_children=0")
        # Reload the data based on the updated URL
        self.root.ids.wall_layout.clear_widgets()
        print("Scraping Vrbo.com")
        scraped_data = Search_Vrbo.scrape_vrbo(self.search_url)
        print("Scraping AirBnB.com")
        scrape_bnb = Search_Bnb.scrape_bnb(self.search_url2)

        Clock.schedule_once(lambda dt: self.update_ui(scraped_data, 'Vrbo.com'))

        Clock.schedule_once(lambda dt: self.update_ui(scrape_bnb, 'Airbnb.com'))
        print("Scraping Booking.com")
        scrape_book = Search_book.scrape_booking(self.search_url3)

        Clock.schedule_once(lambda dt: self.update_ui(scrape_book, 'Booking.com'))
        return self.search_url, self.search_url2, self.search_url3

    def update_ui(self, data, source):
        if data:
            print(f"Data fetched from {source}: {data}")
            print("Updating UI")
            new_screen = HomeScreen(images=data)
            self.root.clear_widgets()  # Clear the previous screen
            self.root.add_widget(new_screen)
        else:
            print(f"No data fetched from {source}")


if __name__ == "__main__":
    Builder.load_string(kv)
    app = MyApp()
    # Prompt the user to enter search text
    # Call instance method with search_text
    # Pass the updated URL to scrape_vrbo
    app.run()  # Run the app
