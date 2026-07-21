import json
import os
import streamlit as st
try:
    from supabase import create_client, Client
except ImportError:
    pass

CONFIG_FILE = 'watchlist.json'

DEFAULT_CONFIG = {
    "tickers": [
        {"symbol": "SPY", "capital": 10000, "tag": "Index", "custom_target": 0.0}, 
        {"symbol": "BTC-USD", "capital": 5000, "tag": "Crypto", "custom_target": 0.0}, 
        {"symbol": "RKLB", "capital": 2000, "tag": "Growth", "custom_target": 0.0},
        {"symbol": "AAPL", "capital": 3000, "tag": "Blue Chip", "custom_target": 0.0}
    ],
    "global_thresholds": {
        "index_max_er": 0.40,
        "index_max_pe": 20.0,
        "bluechip_max_pe": 30.0,
        "growth_good_peg": 1.2,
        "growth_bad_peg": 2.5,
        "growth_max_pe": 50.0,
        "crypto_good_sma": 5.0,
        "crypto_bad_sma": -10.0
    }
}

def get_supabase_client():
    try:
        if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
            return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        pass
    return None

def load_config():
    # 1. Try Supabase First (Cloud Persistence)
    try:
        supabase = get_supabase_client()
        if supabase:
            response = supabase.table('app_state').select('config_data').eq('id', 1).execute()
            if response.data and len(response.data) > 0:
                data = response.data[0]['config_data']
                if not data:
                    return DEFAULT_CONFIG
                return data
    except Exception as e:
        print("Supabase load error:", e)

    # 2. Try Local File (Local Development Fallback)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data
        except:
            pass
            
    return DEFAULT_CONFIG

def save_config(config):
    # 1. Try Supabase First
    try:
        supabase = get_supabase_client()
        if supabase:
            supabase.table('app_state').upsert({'id': 1, 'config_data': config}).execute()
            return
    except Exception as e:
        print("Supabase save error:", e)

    # 2. Try Local File
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        pass
