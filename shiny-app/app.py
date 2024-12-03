from shiny import App, ui, render
import pandas as pd
import altair as alt

# Load the data
file_path = '/Users/joying/Documents/GitHub/Final Project /Data Base for FP/merged_cleaned_data.csv'
data = pd.read_csv(file_path)

# Ensure all necessary columns exist
required_columns = [
    'profit_2020', '2021_profit_(million_usd)_2021', '2022_profit_(millions_usd)_2022',
    'scope_1_ghg_emissions_tons_co₂e_2020', 'scope_2_emissions__tons_co₂e_2020',
    '2021_scope_1_emissions_tons_co₂e_2021', '2021_scope_2_emissions_tons_co₂e_2021',
    '2022_scope_1_emissions_tons_co₂e_2022', '2022_scope_2_emissions_tons_co₂e_2022'
]

# Fill missing columns with 0 if they don't exist
for col in required_columns:
    if col not in data.columns:
        data[col] = 0

# Ensure numeric data for profit and emissions
profit_columns = ['profit_2020', '2021_profit_(million_usd)_2021', '2022_profit_(millions_usd)_2022']
data[profit_columns] = data[profit_columns].apply(pd.to_numeric, errors='coerce')

emission_columns = [
    'scope_1_ghg_emissions_tons_co₂e_2020', 'scope_2_emissions__tons_co₂e_2020',
    '2021_scope_1_emissions_tons_co₂e_2021', '2021_scope_2_emissions_tons_co₂e_2021',
    '2022_scope_1_emissions_tons_co₂e_2022', '2022_scope_2_emissions_tons_co₂e_2022'
]
data[emission_columns] = data[emission_columns].apply(pd.to_numeric, errors='coerce')

# Calculate total emissions and profit
data['total_emissions'] = data[emission_columns].sum(axis=1)
data['profit_total'] = data[profit_columns].sum(axis=1)

# Calculate emission intensity
data['emission_intensity'] = data['total_emissions'] / data['profit_total']
data['emission_intensity'] = data['emission_intensity'].replace([float('inf'), -float('inf')], 0).fillna(0)

# Define the UI
app_ui = ui.page_fluid(
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select(
                "industry", "Select Industry:",
                choices=["All"] + sorted(data['industry'].dropna().unique().tolist()),
                selected="All"
            ),
            ui.input_select(
                "company", "Select Company:",
                choices=["All"] + sorted(data['company_name'].dropna().unique().tolist()),
                selected="All"
            )
        ),
        ui.output_image("emission_plot"),
        ui.output_table("emission_table")
    )
)

# Define the server
def server(input, output, session):
    # Filter data based on user input
    def filter_data():
        filtered = data.copy()
        if input.industry() != "All":
            filtered = filtered[filtered['industry'] == input.industry()]
        if input.company() != "All":
            filtered = filtered[filtered['company_name'] == input.company()]
        return filtered

    # Generate the plot
    @output
    @render.image
    def emission_plot():
        filtered = filter_data()
        chart = alt.Chart(filtered).mark_circle(size=60).encode(
            x=alt.X('total_emissions:Q', title='Total Emissions (tons)'),
            y=alt.Y('profit_total:Q', title='Total Profit (USD)'),
            color=alt.Color('industry:N', title='Industry'),
            tooltip=['company_name', 'total_emissions', 'profit_total', 'emission_intensity']
        ).properties(
            title="Profit vs Emissions",
            width=800,
            height=400
        )
        # Save the chart as an image
        chart_path = "/tmp/emission_plot.png"
        chart.save(chart_path, format="png")
        return {"src": chart_path, "width": 800, "height": 400}

    # Render the filtered table
    @output
    @render.table
    def emission_table():
        filtered = filter_data()
        required_columns = ['company_name', 'industry', 'total_emissions', 'profit_total', 'emission_intensity']
        for col in required_columns:
            if col not in filtered.columns:
                filtered[col] = 0
        return filtered[required_columns]

