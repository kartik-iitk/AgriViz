import requests
from bs4 import BeautifulSoup
import csv
import time
import pandas as pd

# URL of the mandi price website
url = "https://agmarknet.gov.in/"

# Fetch the page content
response = requests.get(url)
main = BeautifulSoup(response.text, 'html.parser')

# Find the commodity dropdown
commodity_dropdown = main.find('select', {'id': 'ddlCommodity'})

# Extract the options (commodity values and names)
commodities = []
for option in commodity_dropdown.find_all('option'):
    value = option.get('value')
    name = option.text
    if value != "0":  # Skip the '--Select--' option
        commodities.append((value, name))

# Print the commodities
for commodity in commodities:
    print(f"Commodity ID: {commodity[0]}, Name: {commodity[1]}")
    name = commodity[1].replace(" ", "+").replace("/", "%2f")

    data_url = f"https://agmarknet.gov.in/SearchCmmMkt.aspx?Tx_Commodity={commodity[0]}&Tx_State=0&Tx_District=0&Tx_Market=0&DateFrom=01-Jan-2015&DateTo=15-Oct-2024&Fr_Date=01-Jan-2015&To_Date=15-Oct-2024&Tx_Trend=0&Tx_CommodityHead={name}&Tx_StateHead=--Select--&Tx_DistrictHead=--Select--&Tx_MarketHead=--Select--"

    response = requests.post(data_url)

    # Check if the request was successful
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')  # Adjust if table structure is different
        # print(table)
        # Extract data from the table rows
        if table:
            rows = table.find_all('tr')
            data = []
            for row in rows:
                cells = row.find_all('td')
                row_data = [cell.text.strip() for cell in cells]
                if row_data:
                    data.append(row_data)

            if data:
                df = pd.DataFrame(data)
                df.to_csv(f'{commodity[0]}_prices.csv', index=False)
                # save_to_csv(data)
                print(f"Data for {commodity[0]}: {commodity[1]} saved.")
            else:
                print(f"No data found for {commodity[0]}: {commodity[1]}")
    else:
        print(f"Request failed to get data for {commodity[0]}: {commodity[1]}")
