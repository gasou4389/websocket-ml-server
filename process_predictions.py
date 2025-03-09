import os
import pandas as pd
import json

# ✅ Define a relative path for JSON output
json_file_path = "C:/NBA/predictions.json"  # ✅ Save outside OneDrive

# ✅ Use a relative path to load Excel
file_path = os.path.join(os.path.dirname(__file__), "Live Summary.xlsx")

def generate_predictions_json():
    """Extract predictions from Excel, print them, and save as JSON."""
    try:
        xls = pd.ExcelFile(file_path)
        sheet_names = [f"Game {i}" for i in range(1, 16)]
        structured_predictions = []

        for sheet in sheet_names:
            try:
                # ✅ Read the game name from column V (row 9)
                game_name = pd.read_excel(xls, sheet_name=sheet, usecols="V", skiprows=8, nrows=1).iloc[0, 0]

                # ✅ Read headers from B1:J1
                headers_BJ = pd.read_excel(xls, sheet_name=sheet, usecols="B:J", skiprows=0, nrows=1, header=None).iloc[0].astype(str).tolist()

                # ✅ Read data from B2:J2
                data_BJ = pd.read_excel(xls, sheet_name=sheet, usecols="B:J", skiprows=1, nrows=1, header=None).iloc[0].tolist()

                # ✅ Convert B2:J2 data into a dictionary using headers_BJ as keys
                extra_game_data = dict(zip(headers_BJ, data_BJ))

                # ✅ Read main headers from A1:U1 (row 9)
                headers_main = pd.read_excel(xls, sheet_name=sheet, usecols="A:U", skiprows=8, nrows=1, header=None).iloc[0].astype(str).tolist()

                # ✅ Read main table data from A2:U52 (rows 10-61)
                df = pd.read_excel(xls, sheet_name=sheet, usecols="A:U", skiprows=9, nrows=52, header=None)
                df.columns = headers_main

                # ✅ Add game_ID
                df.insert(0, "game_ID", game_name)

                # ✅ Create a unique Row_ID by combining game_ID and Row column
                if "Row" in df.columns:
                    df["Row_ID"] = df.apply(lambda row: f"{row['game_ID']}_{row['Row']}" if pd.notna(row["Row"]) else None, axis=1)
                else:
                    print(f"⚠️ Warning: 'Row' column missing in {sheet}, skipping Row_ID generation.")

                # ✅ Merge extra game data (B2:J2) into each row
                for key, value in extra_game_data.items():
                    df[key] = value  # Assign same value to all rows

                # ✅ Replace NaN and empty strings with None (null in JSON)
                df = df.map(lambda x: None if pd.isna(x) or x == "" else x)

                # ✅ Convert to dictionary format
                game_predictions = df.to_dict(orient="records")
                structured_predictions.extend(game_predictions)

                # ✅ Print predictions for this game
                print(f"\n📊 Predictions for {game_name}:\n")
                for i, row in enumerate(game_predictions[:5]):  # Print first 5 rows
                    print(f"{i+1}. {row}")
                if len(game_predictions) > 5:
                    print(f"... ({len(game_predictions) - 5} more rows hidden)\n")

            except Exception as e:
                print(f"❌ Error processing {sheet}: {e}")

        # ✅ Save the structured predictions as a JSON file
        with open(json_file_path, "w") as f:
            json.dump(structured_predictions, f, indent=4)

        print(f"\n✅ Predictions saved to {json_file_path}")

    except FileNotFoundError:
        print("❌ Excel file not found. Ensure 'Live Summary.xlsx' is in the correct location.")

# Run this script manually to generate the JSON
if __name__ == "__main__":
    generate_predictions_json()





