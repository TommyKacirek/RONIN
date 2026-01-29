import pandas as pd
from typing import Dict, List

class DataMerger:
    """
    Merges multiple parsed IBKR datasets into one.
    Deduplicates transactional data and keeps the latest snapshot for positions.
    """
    
    TRANSACTION_SECTIONS = {
        'Trades', 'Dividends', 'Withholding Tax', 
        'Deposits & Withdrawals', 'Fees', 'Interest', 'Corporate Actions'
    }

    def merge(self, datasets: List[Dict[str, pd.DataFrame]]) -> Dict[str, pd.DataFrame]:
        if not datasets:
            return {}
        
        merged = {}
        all_sections = set().union(*(d.keys() for d in datasets))

        for section in all_sections:
            dfs = [d[section] for d in datasets if section in d]
            if not dfs: continue

            if section in self.TRANSACTION_SECTIONS:
                # Concat and Deduplicate
                combined = pd.concat(dfs, ignore_index=True)
                # Drop duplicates based on ALL columns
                combined = combined.drop_duplicates()
                
                # Sort by Date if available
                date_col = next((c for c in combined.columns if 'Date' in c or 'Time' in c), None)
                if date_col:
                    combined = combined.sort_values(by=date_col)
                
                merged[section] = combined.reset_index(drop=True)
            else:
                # Snapshot sections (e.g. Open Positions, NAV) -> Take the LAST one (assuming chronological order)
                merged[section] = dfs[-1]
        
        return merged
