#!/usr/bin/env python3
"""
Test script to demonstrate the get_last_row function from real_last_row.py
"""

import os
from real_last_row import get_last_row

def main():
    # Path to the Excel file
    file_path = os.path.join(os.path.dirname(__file__), 'Real_DIBELS.xlsx')
    
    # Test with sheet name
    print("Testing with sheet name:")
    sheet_name = 'Year 1'
    column = 'Z'
    
    try:
        last_row = get_last_row(file_path, sheet_name, column)
        if last_row is not None:
            print(f"The last row with data in column {column} of sheet '{sheet_name}' is: {last_row}")
        else:
            print(f"No data found in column {column} in sheet '{sheet_name}'")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with sheet index
    print("\nTesting with sheet index:")
    sheet_index = 1  # Assuming 'Year 1' is the second sheet (index 1)
    try:
        last_row = get_last_row(file_path, sheet_index, column)
        if last_row is not None:
            print(f"The last row with data in column {column} of sheet index {sheet_index} is: {last_row}")
        else:
            print(f"No data found in column {column} in sheet index {sheet_index}")
    except Exception as e:
        print(f"Error: {e}")



if __name__ == "__main__":
    main()