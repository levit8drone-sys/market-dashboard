import streamlit as st
import pandas as pd
import requests
from utils import load_config, save_config

st.title("Watchlist Configuration")
st.markdown("Search for global assets and allocate target capital.")

config = load_config()
if 'tickers' not in config:
    config['tickers'] = []

def search_yahoo_finance(query):
    url = f"https://query2.finance.yahoo.com/v1/finance/search"
    params = {'q': query, 'quotesCount': 30, 'newsCount': 0}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json().get('quotes', [])
    except Exception as e:
        pass
    return []

st.header("Search & Add Asset")

col_search, col_filter = st.columns([2, 1])
with col_search:
    search_query = st.text_input("Enter Company Name or Ticker (e.g., Fisher & Paykel, BHP, ETH, TSLA)")
with col_filter:
    exchange_filter = st.selectbox("Filter by Market", [
        "All Exchanges", 
        "US Markets (Hatch/Sharesies)", 
        "Australian Securities Exchange (ASX)", 
        "New Zealand Exchange (NZX)", 
        "Cryptocurrency"
    ])

if st.button("Search"):
    if search_query:
        with st.spinner("Searching global markets..."):
            raw_results = search_yahoo_finance(search_query)
            
            filtered_results = []
            if exchange_filter == "All Exchanges":
                filtered_results = raw_results
            else:
                for res in raw_results:
                    exch = res.get('exchange', '').upper()
                    symbol = res.get('symbol', '').upper()
                    quote_type = res.get('quoteType', '').upper()
                    
                    if exchange_filter == "US Markets (Hatch/Sharesies)":
                        if exch in ['NYQ', 'NMS', 'NGM', 'NCM', 'ASE', 'NASDAQ', 'NYSE', 'AMEX', 'PNK', 'PCX', 'BATS'] and not symbol.endswith('.AX') and not symbol.endswith('.NZ'):
                            filtered_results.append(res)
                    elif exchange_filter == "Australian Securities Exchange (ASX)":
                        if exch == 'ASX' or symbol.endswith('.AX'):
                            filtered_results.append(res)
                    elif exchange_filter == "New Zealand Exchange (NZX)":
                        if exch in ['NZE', 'NZSE'] or symbol.endswith('.NZ'):
                            filtered_results.append(res)
                    elif exchange_filter == "Cryptocurrency":
                        if quote_type == 'CRYPTOCURRENCY' or exch == 'CCY' or symbol.endswith('-USD'):
                            filtered_results.append(res)
            
            if filtered_results:
                st.session_state['search_results'] = filtered_results
            else:
                st.warning("No results found for that specific market. Try 'All Exchanges' or a different term.")
                if 'search_results' in st.session_state:
                    del st.session_state['search_results']

if 'search_results' in st.session_state and st.session_state['search_results']:
    st.markdown("### Search Results")
    for res in st.session_state['search_results']:
        ticker = res.get('symbol', '')
        if not ticker:
            continue
            
        name = res.get('shortname', res.get('longname', 'Unknown Name'))
        exch = res.get('exchDisp', res.get('exchange', 'Unknown Exchange'))
        asset_type = res.get('typeDisp', res.get('quoteType', 'Asset'))
        
        exists = any(t['symbol'] == ticker for t in config['tickers'])
        
        col_info, col_btn = st.columns([4, 1])
        with col_info:
            st.markdown(f"**{ticker}** &mdash; {name}  \n*{exch} | {asset_type}*")
        with col_btn:
            if exists:
                st.button("Added", key=f"add_{ticker}", disabled=True)
            else:
                if st.button("Add to List", key=f"add_{ticker}"):
                    if asset_type.upper() == 'CRYPTOCURRENCY' or '-USD' in ticker:
                        tag = "Crypto"
                    elif asset_type.upper() == 'ETF':
                        tag = "Index"
                    else:
                        tag = "Blue Chip"
                        
                    config['tickers'].append({"symbol": ticker, "capital": 1000, "tag": tag, "custom_target": 0.0})
                    save_config(config)
                    st.success(f"Added {ticker} to watchlist!")
                    st.rerun()
    st.markdown("---")

st.header("Manage Portfolio")
st.markdown("Set your target capital, asset tag, and custom buy target for each asset.")

df = pd.DataFrame(config['tickers'])
if df.empty:
    df = pd.DataFrame(columns=["symbol", "capital", "tag", "custom_target"])
else:
    if 'tag' not in df.columns:
        df['tag'] = "Blue Chip"
    if 'custom_target' not in df.columns:
        df['custom_target'] = 0.0
        
    # Drop legacy profile column if it leaked through
    if 'profile' in df.columns:
        df = df.drop(columns=['profile'])

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    column_config={
        "symbol": st.column_config.TextColumn("Ticker Symbol", required=True),
        "capital": st.column_config.NumberColumn("Target Capital ($)", min_value=0, required=True, step=100),
        "tag": st.column_config.SelectboxColumn("Asset Tag", 
            options=["Index", "Blue Chip", "Growth", "Crypto"], 
            required=True,
            default="Blue Chip"
        ),
        "custom_target": st.column_config.NumberColumn("Custom Buy Target ($)", min_value=0.0, step=0.5, format="%.2f", help="Set to 0 to disable.")
    },
    use_container_width=True
)

if st.button("Save Configuration", type="primary"):
    clean_df = edited_df.dropna(subset=['symbol']).copy()
    clean_df['symbol'] = clean_df['symbol'].astype(str).str.upper().str.strip()
    if 'tag' not in clean_df.columns:
        clean_df['tag'] = "Blue Chip"
    clean_df['tag'] = clean_df['tag'].fillna("Blue Chip")
    if 'custom_target' not in clean_df.columns:
        clean_df['custom_target'] = 0.0
    clean_df['custom_target'] = clean_df['custom_target'].fillna(0.0)
    
    new_tickers = clean_df.to_dict('records')
    config['tickers'] = new_tickers
    save_config(config)
    st.success("Configuration saved! You can now switch back to the Dashboard.")

st.markdown("---")
st.header("Advanced Settings")
with st.expander("Configure Fundamental Health Thresholds"):
    thresh = config.get("global_thresholds", {
        "index_max_er": 0.40, "index_max_pe": 20.0,
        "bluechip_max_pe": 30.0,
        "growth_good_peg": 1.2, "growth_bad_peg": 2.5, "growth_max_pe": 50.0,
        "crypto_good_sma": 5.0, "crypto_bad_sma": -10.0
    })
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Index Funds")
        t_index_max_er = st.number_input("Max Expense Ratio (%) [Red if >]", value=thresh.get("index_max_er", 0.40), step=0.05)
        t_index_max_pe = st.number_input("Max P/E Ratio [Green if <]", value=thresh.get("index_max_pe", 20.0), step=1.0)
        
        st.subheader("Blue Chip")
        t_bluechip_max_pe = st.number_input("Max P/E Ratio [Red if >]", value=thresh.get("bluechip_max_pe", 30.0), step=1.0)
        
        st.subheader("Crypto / Digital")
        t_crypto_good_sma = st.number_input("Price vs 200d SMA (%) [Green if >]", value=thresh.get("crypto_good_sma", 5.0), step=1.0)
        t_crypto_bad_sma = st.number_input("Price vs 200d SMA (%) [Red if <]", value=thresh.get("crypto_bad_sma", -10.0), step=1.0)
        
    with col2:
        st.subheader("Growth Stocks")
        t_growth_good_peg = st.number_input("Max PEG Ratio [Green if <]", value=thresh.get("growth_good_peg", 1.2), step=0.1)
        t_growth_bad_peg = st.number_input("Min PEG Ratio [Red if >]", value=thresh.get("growth_bad_peg", 2.5), step=0.1)
        t_growth_max_pe = st.number_input("Max Forward P/E [Red if >]", value=thresh.get("growth_max_pe", 50.0), step=5.0)
        
    if st.button("Save Thresholds"):
        config["global_thresholds"] = {
            "index_max_er": t_index_max_er,
            "index_max_pe": t_index_max_pe,
            "bluechip_max_pe": t_bluechip_max_pe,
            "growth_good_peg": t_growth_good_peg,
            "growth_bad_peg": t_growth_bad_peg,
            "growth_max_pe": t_growth_max_pe,
            "crypto_good_sma": t_crypto_good_sma,
            "crypto_bad_sma": t_crypto_bad_sma
        }
        save_config(config)
        st.success("Global fundamental thresholds saved!")
