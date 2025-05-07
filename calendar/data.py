import pandas as pd
from pytz import timezone

def load_event_data(csv_path="casino_events.csv"):
    PDT = timezone('America/Los_Angeles')
    df = pd.read_csv(csv_path)
    
    for col in ["StartDate", "EndDate"]:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        if df[col].dt.tz is None:
            df[col] = df[col].dt.tz_localize(PDT)
        else:
            df[col] = df[col].dt.tz_convert(PDT)
            
    return df
    