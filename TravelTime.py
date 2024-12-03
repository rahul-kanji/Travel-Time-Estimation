import streamlit as st
import requests
from datetime import datetime
import folium
from streamlit_folium import st_folium
from datetime import datetime, time, date, timedelta
from streamlit_searchbox import st_searchbox
from dotenv import load_dotenv
import os

def get_location_suggestions(query, api_key):
    if not query:
        return []
    url = f"https://api.tomtom.com/search/2/search/{query}.json"
    params = {
        "key": api_key,
        "countrySet" : "NZ",
        "typeahead": "true",
        "limit": 5,  # Limit results to 5 suggestions
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        suggestions = [
            {"label": result["address"]["freeformAddress"], 
             "coords": (result["position"]["lat"], result["position"]["lon"])}
            for result in data.get("results", [])
        ]
        return suggestions
    return []

def get_route_data(origin, destination, api_key,travel_mode, departure_time=None):

    url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin}:{destination}/json"

    # Travel mode to be used in the API request
    travel_mode_map = {
        "Car": "car",
        "Truck": "truck",
        "Taxi": "taxi",
        "Bus": "bus",
        "Van": "van",
        "Motorcycle": "motorcycle",
        "Bicycle": "bicycle",
        "Pedestrian": "pedestrian",
    }
    
    travel_mode = travel_mode_map.get(travel_mode, "car")  # Default to "car" if not found
    
    params = {
        "travelMode": travel_mode,  # Updated to use travelMode
        "traffic": "true",
        "key": api_key,
    }
    
    if departure_time:
        params["departAt"] = departure_time  # Add departure time if specified

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def search_locations(query,api_key):
    suggestions = get_location_suggestions(query, api_key)
    return [s["label"] for s in suggestions]

st.markdown("""
    <style>
            
        /* Change the color of all text content to dark blue */
        body, .stText, .stMarkdown, .stWrite, .stLabel, .stSubheader, .stTitle, .stHeader, .stBlockquote, .stCaption {
            color: #003399 !important;  /* Dark blue color */
        }

        /* Additional styling for input labels and text */
        .stTextInput label, .stTextArea label, .stNumberInput label, .stSelectbox label, .stMultiselect label, .stRadio label {
            color: #003399 !important;  /* Dark blue color */
        }

        /* Style for all buttons */
        .stButton>button {
            background-color: #015482; /* Navy blue background */
            color: white; /* Text color white */
            border: none; /* Remove button border */
        }

        /* Hover effect */
        .stButton>button:hover {
            background-color: #99bbff; /* Lighter blue when hovered */
            color: white;
        }

        /* Pressed effect */
        .stButton>button:active {
            background-color: #99bbff; /* Lighter blue when pressed */
            color: white;
        }
            
        /* Ensure text stays white when button is clicked */
        .stButton>button:focus {
            color: white !important;  /* Text remains white on focus (clicked state) */
            background-color: #4a6e97 !important;  /* Keep the lighter blue background */
        }
        
        /* Customize the appearance of the radio button circle */
        .stRadio > div > label > div > svg circle {
            fill: white !important;  /* White circle for the radio button */
        }
        
            
        
    </style>
    """, unsafe_allow_html=True)


# load_dotenv()  # Load variables from the .env file

# api_key = os.getenv('tomtom_API_KEY')  # Fetches the value from .env
# if not api_key:
#     raise ValueError("API key is not set in .env file")

def main_app():
    api_key=st.session_state.API_KEY
    st.image("./WAL_Logo.png", use_container_width=True)
    st.title('Travel Time Estimator',)

    if "route_data" not in st.session_state:
        st.session_state.route_data = None

    ###################
    ## Travel Mode ##
    ###################

    # Travel mode selectbox
    travel_mode = st.radio(
        "Select Travel Mode:",
        ["Car", "Truck", "Taxi", "Bus", "Van", "Motorcycle", "Bicycle", "Pedestrian"],
        index=0,  # Default to "car"
        horizontal=True
    )

    ################
    ##   Origin   ##
    ################

    # Use st_searchbox for the origin location search box
    origin_selected = st_searchbox(
        search_locations, 
        placeholder="Search for origin location...", 
        key="origin_searchbox"
    )

    # Fetch and display the selected origin coordinates
    if origin_selected:
        # Fetch suggestions again based on the selected value
        suggestions = get_location_suggestions(origin_selected, api_key)
        origin_data = next(
            (s for s in suggestions if s["label"] == origin_selected), None
        )
        if origin_data:
            origin_lat, origin_lon = origin_data["coords"]
        else:
            st.write("Origin location not found. Please try again.")

    #####################
    ##   Destination   ##
    #####################

    # Use st_searchbox for the origin location search box
    destination_selected = st_searchbox(
        search_locations, 
        placeholder="Search for destination location...", 
        key="destination_searchbox"
    )

    # Fetch and display the selected origin coordinates
    if destination_selected:
        # Fetch suggestions again based on the selected value
        suggestions = get_location_suggestions(destination_selected, api_key)
        destination_data = next(
            (s for s in suggestions if s["label"] == destination_selected), None
        )
        if destination_data:
            destination_lat, destination_lon = destination_data["coords"]
        else:
            st.write("Origin location not found. Please try again.")


    ############################
    ###    Departure Time    ###
    ############################


    # Current datetime as default
    now = datetime.now()

    # Date Selector
    st.write("### Select Departure Date & Time")
    selected_date = st.date_input(
        "Choose a departure date:",
        value=now.date(),  # Default to current date
        min_value=now.date()  # Prevent selecting past dates
    )

    # Time Selector
    col1, col2, col3, col4 = st.columns(4)

    # Hour selection (1-12 for AM/PM format)
    with col1:
        # Adjust the index calculation to handle 12 PM correctly
        if now.hour == 12:
            hour_index = 11  # 12 PM should correspond to the 12th hour in the selectbox (index 11)
        else:
            hour_index = (now.hour % 12) - 1  # For AM hours (1-11), this works fine

        hour = st.selectbox("Hour", options=list(range(1, 13)), index=hour_index)
    # Minute selection (0-59)
    with col2:
        minute = st.selectbox("Minute", options=list(range(0, 60)), index=now.minute)

    # AM/PM toggle
    with col3:
        am_pm = st.radio("AM/PM", options=["AM", "PM"], index=0 if now.hour < 12 else 1)

    # Convert time selection to 24-hour format
    if am_pm == "PM" and hour != 12:
        hour += 12
    if am_pm == "AM" and hour == 12:
        hour = 0

    selected_time = time(hour, minute)

    # Combine date and time into a datetime object
    selected_datetime = datetime.combine(selected_date, selected_time)

    # Fallback to now if no selection is made
    if not selected_date or not selected_time:
        selected_datetime = now

    # Convert to ISO format for API call
    departure_time = selected_datetime.isoformat()


    # Simulate API usage (for demonstration)
    with col4:
        confirm_button = st.button("Confirm Departure Time")

    if confirm_button:
        st.success(f"Departure Time (ISO): {selected_datetime.strftime('%Y-%m-%d %I:%M %p')} selected successfully!")


    ###########################
    ###    Finding Route    ###
    ###########################

    # API key (replace with your own TomTom API key)
    api_key = "nAHjNV9G82JXoj7oO4dDsvWjNL7Q87hV"

    if st.button('Find Fastest Route'):
        # Ensure origin and destination are entered
        if not origin_selected or not destination_selected:
            st.error("Please select both an origin and a destination before finding the fastest route.")
        else:
            try:
                # Format origin and destination
                origin = f"{origin_lat},{origin_lon}"
                destination = f"{destination_lat},{destination_lon}"
                
                # Fetch route data
                st.session_state.route_data = get_route_data(origin, destination, api_key, travel_mode, departure_time)
                
                # Check if route data was successfully retrieved
                if st.session_state.route_data:
                    st.success("Route data retrieved successfully!")
                else:
                    st.error("Failed to retrieve route data. Please try again.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

        
    ###########################
    ###     Route Stats     ###
    ###########################


    if st.session_state.route_data:
        route_data = st.session_state.route_data
        st.subheader('Route Details:')

        # Extract route details
        distance = route_data['routes'][0]['summary']['lengthInMeters'] / 1000  # Distance in km
        travel_time_minutes = route_data['routes'][0]['summary']['travelTimeInSeconds'] / 60  # Travel time in minutes

        # Format the values
        distance_formatted = f"{distance:.2f} km"
        travel_time_formatted = f"{travel_time_minutes:.2f} minutes"

        # Create two columns for distance and travel time
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Distance: {distance_formatted}")
        with col2:
            st.write(f"Travel Time: {travel_time_formatted}")

        # Calculate and format the departure and arrival times
        try:
            # Parse departure time
            departure_datetime = datetime.fromisoformat(departure_time)

            # Calculate arrival time
            arrival_datetime = departure_datetime + timedelta(minutes=travel_time_minutes)

            # Format the dates without seconds and add AM/PM
            formatted_departure_time = departure_datetime.strftime("%Y-%m-%d %I:%M %p")
            formatted_arrival_time = arrival_datetime.strftime("%Y-%m-%d %I:%M %p")

            # Create two columns for departure and arrival time
            col3, col4 = st.columns(2)
            with col3:
                st.write(f"Departure Time: {formatted_departure_time}")
            with col4:
                st.write(f"Expected Arrival Time: {formatted_arrival_time}")
            
        except Exception as e:
            st.error(f"An error occurred while calculating arrival time: {e}")


        #############################
        ###     Mapping Route     ###
        #############################

        route = route_data['routes'][0]
        route_coordinates = []
        for i in range(len(route['legs'])):
            route_coordinates.append( [(point['latitude'], point['longitude']) for point in route['legs'][i]['points']])
            

        # Create a folium map centered around the origin
        map_center = [origin_lat, origin_lon]
        route_map = folium.Map(location=map_center, zoom_start=14)

        # Add origin and destination markers
        if origin_selected:
            folium.Marker([origin_lat, origin_lon], popup=f"{origin_data['label']}").add_to(route_map)

        if destination_selected:
            folium.Marker([destination_lat, destination_lon], popup=f"{destination_data['label']}").add_to(route_map)

        # Plot the route on the map
        folium.PolyLine(route_coordinates, color="blue", weight=3, opacity=1).add_to(route_map)

        # Display the map in Streamlit using streamlit_folium
        st_folium(route_map, width=700, height=500)

def validate_api_key(api_key):
    # Replace this with a real API endpoint that requires authentication
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{-36.40000,174.36000}:{-36.3967,174.37000}/json"
    params = {
        "travelMode": 'car',  # Updated to use travelMode
        "traffic": "true",
        "key": api_key,
    }
    
    try:
        response = requests.get(url, params=params)
        
        # Check if the response status code is 200 (OK)
        if response.status_code == 200:
            return True  # Valid API key
        else:
            return False  # Invalid API key

    except requests.exceptions.RequestException as e:
        st.error(f"Error making the API request: {e}")
        return False


def input_api_key():
    st.subheader("Enter Your API Key:")
    api_key = st.text_input("API Key", type="password")

    # If the user presses the submit button
    if st.button("Submit"):
        if api_key:
            # Store the API key in session state
            
            api_key_validity = validate_api_key(api_key)
            if api_key_validity:
                st.session_state.API_KEY = api_key
                st.success("API Key Accepted!")
                st.session_state.api_key_valid = True
                st.rerun()  # Rerun the app to load the main page
            else:
                st.session_state.api_key_valid = False
                st.error("Please enter a valid API key.")
        else:
            st.warning("Please enter your API key.")

def app():
    # Check if API key is already in session state
    if "API_KEY" not in st.session_state:
        st.session_state.API_KEY = None

    # If the API key is not provided, show the API key input screen
    if st.session_state.API_KEY is None:
        input_api_key()
    else:
        # If API key is provided, load the main part of the app
        main_app()

if __name__ == "__main__":
    app()