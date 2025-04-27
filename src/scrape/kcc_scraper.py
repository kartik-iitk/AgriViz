import os
import time
import subprocess
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download data from the API and save it to CSV files."
    )
    parser.add_argument(
        "--api-key",
        type=str,
        required=True,
        help="API key for authentication.",
    )
    args = parser.parse_args()
    api_key = args.api_key
    if not api_key:
        raise ValueError("API key is required.")

    # Define states and years
    states = [
        "A AND N ISLANDS",
        "ANDHRA PRADESH",
        "ARUNACHAL PRADESH",
        "ASSAM",
        "BIHAR",
        "CHANDIGARH",
        "CHHATTISGARH",
        "DADRA AND NAGAR HAVELI",
        "DAMAN AND DIU",
        "DELHI",
        "GOA",
        "GUJARAT",
        "HARYANA",
        "HIMACHAL PRADESH",
        "JAMMU AND KASHMIR",
        "JHARKAND",
        "KARNATAKA",
        "KERALA",
        "LAKSHADWEEP",
        "MADHYA PRADESH",
        "MAHARASHTRA",
        "MANIPUR",
        "MEGHALAYA",
        "MIZORAM",
        "NAGALAND",
        "ODISHA",
        "PUDUCHERRY",
        "PUNJAB",
        "RAJASTHAN",
        "SIKKIM",
        "TAMILNADU",
        "TELANGANA",
        "TRIPURA",
        "UTTAR PRADESH",
        "UTTARAKHAND",
        "WEST BENGAL",
    ]
    years = range(2006, 2026)

    data_dir = "../data"
    os.makedirs(data_dir, exist_ok=True)

    # Iterate through all state-year combinations
    for state in states:
        for year in years:
            state_name = state.replace(" ", "%20")
            year_name = str(year)

            offset = 0
            while True:
                filename = (
                    f"{data_dir}/{state.replace(" ", "_")}-{year_name}-{offset}.csv"
                )
                url = f"https://api.data.gov.in/resource/cef25fe2-9231-4128-8aec-2c948fedd43f?api-key={api_key}&format=csv&offset={offset}&limit=100000&filters%5BStateName.keyword%5D={state_name}&filters%5Byear.keyword%5D={year_name}"
                curl_cmd = f"curl -X 'GET' '{url}' -H 'accept: application/xml' -o '{filename}'"

                try:
                    subprocess.run(curl_cmd, shell=True, check=True)
                    if os.path.getsize(filename) == 0:
                        print(f"No more data for {state}, {year} at offset {offset}.")
                        os.remove(filename)
                        break
                    else:
                        print(f"Saved: {filename} at offset {offset}")
                        offset += 100000
                        filename = (
                            f"{data_dir}/{state.replace(' ', '_')}-{year}-{offset}.csv"
                        )
                except subprocess.CalledProcessError:
                    print(
                        f"Failed to download data for {state}, {year} at offset {offset}."
                    )
                    break

                # Wait for 10 seconds before the next request
                time.sleep(10)

    print("All data fetched successfully.")
