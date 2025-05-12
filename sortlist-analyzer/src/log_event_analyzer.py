import pandas as pd
import matplotlib.pyplot as plt
import os

def analyze_log_file(log_file_path, output_reports_dir):
    """
    Analyzes a log CSV file to generate a pie chart of status codes
    and an Excel file detailing 403 and 410 errors for Sortlist URLs.
    """
    try:
        # Create output directories if they don't exist
        charts_output_dir = os.path.join(output_reports_dir, 'charts')
        os.makedirs(output_reports_dir, exist_ok=True)
        os.makedirs(charts_output_dir, exist_ok=True)
        print(f"Ensured output directories exist: {output_reports_dir} and {charts_output_dir}")

        # Load the data
        print(f"Loading log file: {log_file_path}")
        df = pd.read_csv(log_file_path)
        print(f"Successfully loaded {len(df)} rows from {log_file_path}.")

        # Ensure 'event_url' is string type for filtering
        df['event_url'] = df['event_url'].astype(str)
        # Convert status codes to numeric, coercing errors to NaN (which can then be handled or dropped if necessary)
        df['event_status_code'] = pd.to_numeric(df['event_status_code'], errors='coerce')


        # Filter for Sortlist URLs
        df_sortlist = df[df['event_url'].str.contains('https://www.sortlist.com/', na=False)].copy()
        print(f"Found {len(df_sortlist)} rows for Sortlist URLs.")

        if df_sortlist.empty:
            print("No data found for https://www.sortlist.com/ URLs. Exiting.")
            return

        # --- 1. Generate Pie Chart for event_status_code distribution ---
        # Drop rows where status code could not be converted to numeric for reliable analysis
        df_sortlist_valid_codes = df_sortlist.dropna(subset=['event_status_code']).copy()
        # Convert numeric status codes to integer for cleaner representation
        df_sortlist_valid_codes.loc[:, 'event_status_code_int'] = df_sortlist_valid_codes['event_status_code'].astype(int)
        
        status_counts = df_sortlist_valid_codes['event_status_code_int'].value_counts()
        
        print("\nStatus Code Counts for Sortlist URLs:")
        print(status_counts)

        if not status_counts.empty:
            plt.figure(figsize=(12, 10))
            patches, texts, autotexts = plt.pie(status_counts, 
                                                labels=status_counts.index, 
                                                autopct='%1.1f%%', 
                                                startangle=140, 
                                                pctdistance=0.85)
            for text in texts:
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_fontsize(9)
                autotext.set_color('white')
                
            plt.title('Distribution of Event Status Codes for sortlist.com URLs', fontsize=16)
            plt.axis('equal') 
            
            if len(status_counts) > 6:
                 plt.legend(title="Status Codes", loc="center left", bbox_to_anchor=(1.05, 0.5), fontsize=9)

            pie_chart_path = os.path.join(charts_output_dir, 'sortlist_status_code_distribution.png')
            plt.savefig(pie_chart_path, bbox_inches='tight')
            plt.close()
            print(f"\nPie chart saved to: {pie_chart_path}")
        else:
            print("No valid status codes to plot for Sortlist URLs.")

        # --- 2. Generate Excel file with 403 and 410 error details ---
        # Use the df_sortlist_valid_codes for error filtering as it has integer status codes
        df_403 = df_sortlist_valid_codes[df_sortlist_valid_codes['event_status_code_int'] == 403]
        df_410 = df_sortlist_valid_codes[df_sortlist_valid_codes['event_status_code_int'] == 410]
        
        print(f"\nFound {len(df_403)} rows with status 403 for Sortlist URLs.")
        print(f"Found {len(df_410)} rows with status 410 for Sortlist URLs.")

        excel_file_path = os.path.join(output_reports_dir, 'sortlist_http_error_details.xlsx')
        with pd.ExcelWriter(excel_file_path, engine='xlsxwriter') as writer:
            if not df_403.empty:
                df_403.drop(columns=['event_status_code_int']).to_excel(writer, sheet_name='403_Errors', index=False)
                print("403 errors sheet created.")
            else:
                print("No 403 errors found for Sortlist URLs to write to Excel.")
            
            if not df_410.empty:
                df_410.drop(columns=['event_status_code_int']).to_excel(writer, sheet_name='410_Errors', index=False)
                print("410 errors sheet created.")
            else:
                print("No 410 errors found for Sortlist URLs to write to Excel.")
        
        if not df_403.empty or not df_410.empty:
            print(f"\nExcel file with error details saved to: {excel_file_path}")
        else:
            # Remove the excel file if it was created but no sheets were written (though ExcelWriter might not create it)
            if os.path.exists(excel_file_path) and (df_403.empty and df_410.empty):
                 try:
                     os.remove(excel_file_path)
                     print(f"Empty Excel file {excel_file_path} removed.")
                 except OSError as e:
                     print(f"Error removing empty excel file: {e}")
            print(f"\nExcel file not saved or removed as no 403 or 410 errors were found for Sortlist URLs.")

    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file_path}")
    except pd.errors.EmptyDataError:
        print(f"Error: The log file at {log_file_path} is empty.")
    except KeyError as e:
        print(f"Error: A required column is missing in the log file: {e}. Please check the CSV format.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    # This script is intended to be in sortlist-analyzer/src/
    # Get the directory where the script is located
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    # Assume the 'sortlist-analyzer' directory is one level up from 'src'
    PROJECT_ANALYZER_DIR = os.path.dirname(SCRIPT_DIR)

    # Construct paths relative to the 'sortlist-analyzer' directory
    DEFAULT_LOG_FILE = os.path.join(PROJECT_ANALYZER_DIR, 'data', 'COM_ALL_2025-05-05_581c699d451c950526bcfa28_logs_events.csv')
    DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ANALYZER_DIR, 'reports')

    # You can change these paths if needed
    input_log_file_path = DEFAULT_LOG_FILE
    output_reports_directory = DEFAULT_OUTPUT_DIR
    
    print(f"Script directory: {SCRIPT_DIR}")
    print(f"Project analyzer directory: {PROJECT_ANALYZER_DIR}")
    print(f"Input log file: {input_log_file_path}")
    print(f"Output reports directory: {output_reports_directory}")

    analyze_log_file(input_log_file_path, output_reports_directory)
    print("\nLog analysis script finished.") 