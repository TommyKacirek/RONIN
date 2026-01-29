import csv
import pandas as pd
from typing import Dict, List, Optional
import io

class IBKRParser:
    """
    Parses Interactive Brokers Activity Statements (CSV).
    Handles 'nested CSV' rows where data is wrapped in quotes.
    """

    def parse_csv(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Parses the CSV file and returns a dict of DataFrames (Key = Section Name).
        """
        raw_rows = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row: continue
                    # Handle nested quoting (row[0] contains the actual CSV line)
                    # Relaxed check: Section names never contain commas. If row[0] has comma, it's nested.
                    # This handles cases like: "Trades,...",LI,
                    if len(row) > 0 and ',' in row[0]:
                         try:
                             # Attempt to parse the first column as a CSV line
                             nested_reader = csv.reader([row[0]])
                             nested_row = next(nested_reader)
                             if len(nested_row) > 1:
                                 raw_rows.append(nested_row)
                                 continue
                         except:
                             pass
                    
                    raw_rows.append(row)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return {}

        return self._build_sections(raw_rows)

    def _build_sections(self, rows: List[List[str]]) -> Dict[str, pd.DataFrame]:
        # We need to handle cases where a Section has multiple sets of Headers (e.g. Trades for Stocks vs Options)
        # Strategy: Collect batches of (Header, DataRows). Then concat DFs per section.
        
        # Current active header for each section
        current_headers: Dict[str, List[str]] = {}
        
        # Store batches: { section: [ (header_row, [data_rows...]), ... ] }
        batches: Dict[str, List[Dict]] = {} 

        for row in rows:
            if len(row) < 2: continue
            section = row[0]
            type_ = row[1]

            if type_ == 'Header':
                current_headers[section] = row
                
                # Initialize section in batches if new
                if section not in batches:
                    batches[section] = []
                
                # Start a new batch for this header
                # Note: We append a new batch even if header is same as before? 
                # Ideally yes, to keep order or just robustness.
                # Only if data comes.
                # Actually, let's just create the bucket when we see Data, based on current header.
                
            elif type_ == 'Data':
                if section not in current_headers:
                    # Data without header? Skip or infer?
                    continue
                
                header = current_headers[section]
                
                if section not in batches:
                    batches[section] = []
                
                # Check if the last batch for this section uses the SAME header
                last_batch = batches[section][-1] if batches[section] else None
                
                if last_batch and last_batch['header'] == header:
                    last_batch['rows'].append(row)
                else:
                    # Create new batch
                    batches[section].append({
                        'header': header,
                        'rows': [row]
                    })

        # Now build DataFrames
        sections = {}
        
        for section, batch_list in batches.items():
            dfs = []
            for batch in batch_list:
                cols = batch['header']
                data = batch['rows']
                
                # Deduplicate columns (helper)
                dedup_cols = self._dedup_cols(cols)
                
                # Clean data length
                cleaned_data = []
                for r in data:
                    if len(r) == len(dedup_cols):
                        cleaned_data.append(r)
                    elif len(r) < len(dedup_cols):
                        cleaned_data.append(r + [''] * (len(dedup_cols) - len(r)))
                    else:
                        cleaned_data.append(r[:len(dedup_cols)])
                        
                df = pd.DataFrame(cleaned_data, columns=dedup_cols)
                df = self._clean_df(df)
                dfs.append(df)
            
            if dfs:
                # Concat all batches for this section
                # pandas concat aligns columns. e.g. 'Comm/Fee' (Stocks) vs 'Comm in USD' (Options)
                # They will be separate columns in the result, most likely.
                combined = pd.concat(dfs, ignore_index=True)
                sections[section] = combined
                
        return sections

    def _dedup_cols(self, cols: List[str]) -> List[str]:
        seen = {}
        dedup_cols = []
        for c in cols:
            if c not in seen:
                seen[c] = 1
                dedup_cols.append(c)
            else:
                seen[c] += 1
                dedup_cols.append(f"{c}_{seen[c]}")
        return dedup_cols

    def _clean_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts numeric columns and dates.
        """
        for col in df.columns:
            if df[col].dtype == object:
                # Try numeric
                try:
                    # Remove commas
                    cleaned = df[col].astype(str).str.replace(',', '', regex=False)
                    # Convert to numeric, errors='ignore' (keep as object if mixed) or 'coerce' (NaN)
                    # We prefer keeping data if it's text, so we check first or use to_numeric with 'ignore' is deprecated behavior for errors?
                    # pd.to_numeric(errors='ignore') returns input if fail.
                    df[col] = pd.to_numeric(cleaned)
                except:
                    pass
                
                # Try datetime (if not numeric)
                if df[col].dtype == object:
                     try:
                         # Simple check to avoid aggressive date parsing of simple strings
                         sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else ""
                         if isinstance(sample, str) and (sample.startswith('20') or sample.startswith('19')):
                             df[col] = pd.to_datetime(df[col], errors='ignore')
                     except:
                         pass
        return df
