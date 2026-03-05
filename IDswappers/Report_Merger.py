import os
import sys

# Add project root to path so Helpers can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from Helpers.dog_box import select_work_files
from water_logged.the_logger import THElogger


class ReportMerger:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logging.ini")
        self.logger = THElogger(script_name="Report_Merger", config_file=config_path)

    def run(self):
        """Execute the report merge process."""
        # Select multiple Excel files
        files = select_work_files([".xlsx"])

        if not files:
            self.logger.error("No files selected. Exiting.")
            return

        # Directory to save the merged report (same as the first file's directory)
        output_dir = os.path.dirname(files[0])
        output_path = os.path.join(output_dir, "FULL_Report.xlsx")

        # Lists to collect data
        summary_dfs = []
        full_list_dfs = []

        for file in files:
            try:
                # Read Summary sheet
                summary_df = pd.read_excel(file, sheet_name='Summary')
                summary_dfs.append(summary_df)

                # Read Full List sheet
                full_list_df = pd.read_excel(file, sheet_name='Full List')
                full_list_dfs.append(full_list_df)
            except Exception as e:
                self.logger.error(f"Error reading {file}: {e}")
                continue

        if not summary_dfs:
            self.logger.error("No valid Summary sheets found. Exiting.")
            self.logger.finalize_report()
            return

        # Merge Summary: place side by side
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # For Summary tab
            start_col = 0
            for i, df in enumerate(summary_dfs):
                df.to_excel(writer, sheet_name='Summary', startcol=start_col, index=False)
                start_col += df.shape[1] + 1  # Add a gap column

            # For Full List tab: concatenate all
            if full_list_dfs:
                full_list_combined = pd.concat(full_list_dfs, ignore_index=True)
                full_list_combined.to_excel(writer, sheet_name='Full List', index=False)

        self.logger.info(f"Merged report saved to {output_path}")
        self.logger.finalize_report()


def main():
    merger = ReportMerger()
    merger.run()


if __name__ == "__main__":
    main()
