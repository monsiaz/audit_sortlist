import pandas as pd
import logging
from typing import Any

# Helper to write a DataFrame to Excel with column flattening
def write_df(writer, sheet_name, data_df, header_format):
    if data_df is None or not hasattr(data_df, 'columns'):
        logging.warning(f"DataFrame {sheet_name} is None or does not have a columns attribute, it will not be written.")
        return
    # Flatten multi-index columns if necessary
    if isinstance(data_df.columns, pd.MultiIndex):
        data_df.columns = ['_'.join([str(c) for c in col if c not in [None, '']]) for col in data_df.columns.values]
    data_df.columns = [str(c) for c in data_df.columns]
    try:
        data_df.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        columns = data_df.columns
        # Define custom formats
        workbook = writer.book
        fmt_float6 = workbook.add_format({'num_format': '0.000000'})
        fmt_float4 = workbook.add_format({'num_format': '0.0000'})
        fmt_float2 = workbook.add_format({'num_format': '0.00'})
        fmt_int = workbook.add_format({'num_format': '0'})
        # Apply optimal format per column
        for col_num, col_name in enumerate(columns):
            worksheet.write(0, col_num, col_name, header_format)
            # Auto width (max 40)
            max_len = max(
                [len(str(col_name))] + [len(str(val)) for val in data_df[col_name].head(100).values if pd.notnull(val)]
            )
            width = min(max_len + 2, 40)
            # Choose format
            col_lower = col_name.lower()
            if any(x in col_lower for x in ['pagerank', 'score', 'ratio', 'normalized']):
                fmt = fmt_float6
            elif 'ctr' in col_lower:
                fmt = fmt_float4
            elif 'avg_position' in col_lower:
                fmt = fmt_float2
            elif col_lower in ['clicks', 'impressions', 'hits', 'incoming_links', 'outgoing_links', 'crawl_depth']:
                fmt = fmt_int
            elif pd.api.types.is_float_dtype(data_df[col_name]):
                fmt = fmt_float2
            else:
                fmt = None
            if fmt:
                worksheet.set_column(col_num, col_num, width, fmt)
            else:
                worksheet.set_column(col_num, col_num, width)
    except Exception as e:
        logging.error(f"Erreur lors de l'écriture de {sheet_name} : {e}")
        logging.error(f"Colonnes : {data_df.columns}")

def generate_excel_report(df: pd.DataFrame, cat_stats: Any, label_stats: Any, loc_stats: Any, prw_df: pd.DataFrame, cross_metrics: Any, output_file: str, search_engine_analysis: Any = None) -> bool:
    import xlsxwriter
    try:
        logging.info("Starting Excel report generation")
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        # Main tab
        write_df(writer, 'AllData', df, header_format)
        # Stats by category
        if cat_stats is not None and not cat_stats.empty:
            write_df(writer, 'CategoryStats', cat_stats, header_format)
        # Stats by label
        if label_stats is not None and not label_stats.empty:
            write_df(writer, 'LabelStats', label_stats, header_format)
        # Stats by location (optional)
        if loc_stats is not None and not loc_stats.empty:
            write_df(writer, 'LocationStats', loc_stats, header_format)
        # Weighted PageRank
        if prw_df is not None and not prw_df.empty:
            write_df(writer, 'WeightedPR', prw_df, header_format)
        # Cross-metrics and special tabs
        if cross_metrics:
            for key, df_cross in cross_metrics.items():
                if df_cross is not None and not df_cross.empty:
                    write_df(writer, key, df_cross, header_format)
        # Engine logs
        if search_engine_analysis:
            for key, val in search_engine_analysis.items():
                write_df(writer, key, val, header_format)
        writer.close()
        logging.info(f"Excel report generated: {output_file}")
        return True
    except Exception as e:
        logging.error(f"Error generating Excel report: {str(e)}")
        return False 