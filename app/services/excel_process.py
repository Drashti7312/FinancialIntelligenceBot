import pandas as pd
from io import BytesIO
from typing import Literal, Dict, Any
from logger import logger, log_exception

class ExcelFileProcess:
    async def _read_excel_files(
            self,
            file_type: Literal["csv", "xlsx", "xls"],
            file_data: bytes
    ) -> pd.DataFrame:
        try:
            if file_type == "csv":
                return pd.read_csv(BytesIO(file_data))
            return pd.read_excel(BytesIO(file_data))
        except Exception as e:
            return log_exception(e, logger)
        
    async def _data_cleaning(
            self, 
            df: pd.DataFrame
    ) -> pd.DataFrame:
        try:
            # Step1: Convert column names to lowercase
            df.columns = [col.strip().lower() for col in df.columns]

            # Step2: Convert all string values in object columns to lowercase
            for col in df.select_dtypes(include=["object"]).columns:
                df[col] = df[col].str.strip().str.lower()
            return df
        except Exception as e:
            return log_exception(e, logger)

    async def _fetch_df_info(
            self,
            df: pd.DataFrame
    ) -> Dict[str, Any]:
        try:
            # Step1: Columns and their data types
            column_details = []
            for col in df.columns:
                column_details.append({
                    "column_name": col,
                    "pandas_dtype": str(df[col].dtype)
                })

            # Step2: Separate Columns based on their dtypes
            numeric_columns = df.select_dtypes(
                include=["number"]
            ).columns.to_list()
            object_columns = df.select_dtypes(
                include=["object"]
            ).columns.to_list()
            object_cols_data = []

            # Step3: Fetch Column wise information
            for col in object_columns:
                value_counts = df[col].dropna().value_counts().head(50)
                object_cols_data.append({
                    "column_name": col,
                    "total_unique_values": int(df[col].nunique(dropna=True)),
                    "top_50_unique_values": list(value_counts.to_dict().keys())
                })

            numerical_cols_data = []
            for col in numeric_columns:
                numerical_cols_data.append({
                    "min_value": float(df[col].min()),
                    "max_value": float(df[col].max())
                })

            # Step4: Return DF Information
            df_info = {
                    "column_details": column_details,
                    "object_columns": object_columns,
                    "object_cols_data": object_cols_data,
                    "numeric_columns": numeric_columns,
                    "numeric_cols_data": numerical_cols_data,
                    "row_count": len(df),
                    "first_5_row": df.head(5).to_dict()
                }
            return df_info
        except Exception as e:
            return log_exception(e, logger)
