from shiny import App, ui, render
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import io
import requests
import tempfile
import altair as alt

# Function to load and prepare data
def load_and_prepare_data():
    # Load data
    file_path = '/Users/hyeyoonsmacbook/Desktop/Github/final-project/data/merged_data.csv'
    data = pd.read_csv(file_path)

    # Clean company names
    data['company_name'] = data['company_name'].str.strip().str.upper()

    # Map companies to countries (simplified example

    company_to_country = {
   
    "JPMORGAN CHASE": "United States",
    "BERKSHIRE HATHAWAY": "United States",
    "APPLE": "United States",
    "MICROSOFT": "United States",
    "AMAZON": "United States",
    "TESLA": "United States",
    "GOOGLE": "United States",
    "META": "United States",
    "WALMART": "United States",
    "BANK OF AMERICA": "United States",
    "CITIGROUP": "United States",
    "WELLS FARGO": "United States",
    "VERIZON COMMUNICATIONS": "United States",

   
    "ICBC": "China",
    "CHINA CONSTRUCTION BANK": "China",
    "PING AN INSURANCE GROUP": "China",
    "AGRICULTURAL BANK OF CHINA": "China",
    "BANK OF CHINA": "China",
    "TENCENT HOLDINGS": "China",
    "ALIBABA GROUP": "China",
    "SINOPEC": "China",
    "CHINA MOBILE": "China",
    "CHINA MERCHANTS BANK": "China",
    "PETROCHINA": "China",
    "INDUSTRIAL BANK": "China",

 
    "SAUDI ARABIAN OIL COMPANY (SAUDI ARAMCO)": "Saudi Arabia",

   
    "TOYOTA MOTOR": "Japan",
    "SONY": "Japan",
    "HONDA MOTOR": "Japan",
    "MITSUBISHI UFJ FINANCIAL": "Japan",
    "NIPPON TELEGRAPH & TEL": "Japan",

    
    "SAMSUNG ELECTRONICS": "South Korea",
    "HYUNDAI MOTOR": "South Korea",


    "VOLKSWAGEN GROUP": "Germany",
    "BMW GROUP": "Germany",
    "DAIMLER": "Germany",
    "SIEMENS": "Germany",
    "ALLIANZ": "Germany",


    "HSBC HOLDINGS": "United Kingdom",
    "BP": "United Kingdom",
    "SHELL": "United Kingdom",
    "BARCLAYS": "United Kingdom",

   
    "RELIANCE INDUSTRIES": "India",
    "STATE BANK OF INDIA": "India",
    "HDFC BANK": "India",

    
    "BNP PARIBAS": "France",
    "AXA GROUP": "France",
    "TOTALENERGIES": "France",

 
    "NESTLÉ": "Switzerland",
    "ROCHE HOLDING": "Switzerland",
    "NOVARTIS": "Switzerland",

 
    "GAZPROM": "Russia",
    "SBERBANK": "Russia",
    "ROSNEFT": "Russia",

  
    "RBC": "Canada",
    "TD BANK GROUP": "Canada",
    "BANK OF MONTREAL": "Canada",

   
    "PETROBRAS": "Brazil",
    "ITAÚ UNIBANCO HOLDING": "Brazil",

    
    "BHP GROUP": "Australia",
    "COMMONWEALTH BANK": "Australia",

 
    "PHILIPS": "Netherlands",
    "HEINEKEN": "Netherlands",
}

    

    # Map country names
    data['country'] = data['company_name'].map(company_to_country).fillna('UNKNOWN')

    # Calculate total profit and total emissions
    profit_columns = ['profit_2020', '2021_profit_(million_usd)_2021', '2022_profit_(millions_usd)_2022']
    emission_columns = [
        'scope_1_ghg_emissions_tons_co₂e_2020', 'scope_2_emissions__tons_co₂e_2020',
        '2021_scope_1_emissions_tons_co₂e_2021', '2021_scope_2_emissions_tons_co₂e_2021',
        '2022_scope_1_emissions_tons_co₂e_2022', '2022_scope_2_emissions_tons_co₂e_2022'
    ]
    data[profit_columns + emission_columns] = data[profit_columns + emission_columns].fillna(0).apply(pd.to_numeric, errors='coerce')
    data['total_profit'] = data[profit_columns].sum(axis=1)
    data['total_emissions'] = data[emission_columns].sum(axis=1)

    # Group data by country
    country_data = data.groupby('country', as_index=False).agg({'total_profit': 'sum', 'total_emissions': 'sum'})

    # Download world map data
    url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
    response = requests.get(url)
    geojson_data = io.StringIO(response.text)
    world = gpd.read_file(geojson_data)

    # Standardize and fix country names
    world['NAME'] = world['NAME'].str.strip().str.upper().replace({
        'UNITED STATES OF AMERICA': 'UNITED STATES'
    })
    country_data['country'] = country_data['country'].str.strip().str.upper()

    # Merge world map with data
    world = world.merge(country_data, how='left', left_on='NAME', right_on='country')

    # Fill missing values
    world['total_profit'] = world['total_profit'].fillna(0)
    world['total_emissions'] = world['total_emissions'].fillna(0)

    # Log-transform data
    world['log_total_profit'] = world['total_profit'].apply(lambda x: np.log1p(x))
    world['log_total_emissions'] = world['total_emissions'].apply(lambda x: np.log1p(x))

    return data, world

# Load data
data, world_data = load_and_prepare_data()

# Define the Shiny app UI
app_ui = ui.page_fluid(
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_radio_buttons(
                "map_type", "Select Map Type:",
                choices=["Profit", "Emissions"], selected="Profit"
            )
        ),
        ui.output_image("world_map"),
        ui.output_table("filtered_table")
    )
)

# Define the Shiny app server logic
def server(input, output, session):
    @output
    @render.image
    def world_map():
        # Generate map based on user selection
        fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
        if input.map_type() == "Profit":
            world_data.plot(column='log_total_profit', cmap='Blues', legend=True, ax=ax)
            ax.set_title('Log-Transformed Total Profit by Country', fontsize=16)
        else:
            world_data.plot(column='log_total_emissions', cmap='Reds', legend=True, ax=ax)
            ax.set_title('Log-Transformed Total Carbon Emissions by Country', fontsize=16)

        # Save as temporary image
        image_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
        plt.tight_layout()
        plt.savefig(image_path, dpi=150)
        plt.close(fig)
        return {"src": image_path, "width": 800, "height": 600}

    @output
    @render.table
    def filtered_table():
        return data[['company_name', 'country', 'total_profit', 'total_emissions']]

# Create Shiny app
app = App(app_ui, server)
