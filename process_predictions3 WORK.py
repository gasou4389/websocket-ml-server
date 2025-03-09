import os
import pandas as pd
import json

# ✅ Define a relative path for JSON output
json_file_path = "C:/NBA/predictions.json"  # ✅ Save outside OneDrive

# ✅ Use a relative path to load Excel
file_path = os.path.join(os.path.dirname(__file__), "Live Summary.xlsx")

def generate_predictions_json():
    """Extract predictions from Excel and save them as a JSON file."""
    try:
        xls = pd.ExcelFile(file_path)
        sheet_names = [f"Game {i}" for i in range(1, 16)]
        structured_predictions = []

        for sheet in sheet_names:
            try:
                game_name = pd.read_excel(xls, sheet_name=sheet, usecols="V", skiprows=8, nrows=1).iloc[0, 0]
                headers = pd.read_excel(xls, sheet_name=sheet, usecols="A:U", skiprows=8, nrows=1, header=None).iloc[0].astype(str).tolist()
                df = pd.read_excel(xls, sheet_name=sheet, usecols="A:U", skiprows=9, nrows=52, header=None)
                df.columns = headers

                # ✅ Add game_ID
                df.insert(0, "game_ID", game_name)

                # ✅ Create a unique Row_ID by combining game_ID and Row column
                if "Row" in df.columns:
                    df["Row_ID"] = df.apply(lambda row: f"{row['game_ID']}_{row['Row']}" if pd.notna(row["Row"]) else None, axis=1)
                else:
                    print(f"⚠️ Warning: 'Row' column missing in {sheet}, skipping Row_ID generation.")

                # ✅ Replace NaN and empty strings with None (null in JSON)
                df = df.map(lambda x: None if pd.isna(x) or x == "" else x)

                structured_predictions.extend(df.to_dict(orient="records"))
            except Exception as e:
                print(f"❌ Error processing {sheet}: {e}")

        # ✅ Save the structured predictions as a JSON file
        with open(json_file_path, "w") as f:
            json.dump(structured_predictions, f, indent=4)

        print(f"✅ Predictions saved to {json_file_path}")

    except FileNotFoundError:
        print("❌ Excel file not found. Ensure 'Live Summary.xlsx' is in the correct location.")

# Run this script manually to generate the JSON
if __name__ == "__main__":
    generate_predictions_json()




