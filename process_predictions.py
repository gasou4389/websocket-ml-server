import pandas as pd

# ✅ Define a function to return structured predictions
def get_structured_predictions():
    """ Extracts structured predictions from an Excel file and returns them as JSON-friendly data. """

    # Path to your Excel file
    file_path = r"C:\Users\Brandon Moyer\OneDrive - BEC\Desktop\NBA\Live Summary.xlsx"

    # Load all sheets
    xls = pd.ExcelFile(file_path)

    # Define the sheets to extract data from
    sheet_names = [f"Game {i}" for i in range(1, 16)]

    # Create an empty list to store structured data
    structured_predictions = []

    # Loop through each sheet and extract the relevant data
    for sheet in sheet_names:
        try:
            # Read game name from column V
            game_name = pd.read_excel(xls, sheet_name=sheet, usecols="V", skiprows=8, nrows=1).iloc[0, 0]

            # Read headers from A9:U9 (22 columns)
            headers = pd.read_excel(xls, sheet_name=sheet, usecols="A:U", skiprows=8, nrows=1, header=None).iloc[0].astype(str).tolist()

            # Read the main data range (A10:U61) - 52 rows per game
            df = pd.read_excel(xls, sheet_name=sheet, usecols="A:U", skiprows=9, nrows=52, header=None)

            # Assign the extracted headers to the DataFrame
            df.columns = headers

            # Insert game_ID as the first column
            df.insert(0, "game_ID", game_name)

            # Convert entire DataFrame to list of dictionaries
            structured_predictions.extend(df.to_dict(orient="records"))

        except Exception as e:
            print(f"❌ Error processing {sheet}: {e}")

    return structured_predictions  # ✅ Now returns the predictions instead of just printing

