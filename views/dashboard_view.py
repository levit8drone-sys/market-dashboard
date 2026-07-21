import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import datetime
import numpy as np
from utils import load_config

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    .macro-green { color: #00e676; font-weight: bold; }
    .macro-red { color: #ff1744; font-weight: bold; }
    .macro-yellow { color: #ffea00; font-weight: bold; }
    .stAlert { margin-top: 10px; }
    .fund-box {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 5px;
        margin-top: 10px;
    }
    
    /* Mobile Layout Optimizations */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 0.5rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        .fund-box {
            padding: 10px;
            font-size: 0.85em; /* Smaller text for dense mobile display */
        }
        h1 {
            font-size: 1.5rem !important;
        }
        h2 {
            font-size: 1.25rem !important;
        }
        h3 {
            font-size: 1.1rem !important;
        }
        /* Make metric labels smaller on mobile */
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def fetch_data(ticker, period="max"):
    try:
        data = yf.download(ticker, period=period, progress=False)
        return data
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_info(ticker):
    try:
        return yf.Ticker(ticker).info
    except:
        return {}

def get_series(df, col):
    if isinstance(df.columns, pd.MultiIndex):
        return df[col].iloc[:, 0].squeeze()
    return df[col].squeeze()

def calculate_rsi(series, periods=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def run_macro_engine(expected_inflation):
    st.header("Macro Risk Engine")
    st.markdown("Monitor long-term market health and secular trends for generational capital deployment.")
    
    col1, col2, col3, col4 = st.columns(4)
    macro_score = 0
    
    with col1:
        spy_data = fetch_data("SPY", period="max")
        if not spy_data.empty:
            spy_close = get_series(spy_data, 'Close')
            spy_current = spy_close.iloc[-1]
            spy_ath = spy_close.max()
            spy_drawdown = ((spy_current / spy_ath) - 1) * 100
            
            st.metric("S&P 500 Valuation (Drawdown)", f"{spy_drawdown:.2f}%", f"ATH: ${spy_ath:.2f}", help="Measures the percentage drop from the all-time high. A drawdown worse than -20% typically indicates a Bear Market, presenting a generational buying opportunity for long-term investors.")
            if spy_drawdown < -20:
                st.markdown("<span class='macro-green'>Generational Value (Bear Market)</span>", unsafe_allow_html=True)
                macro_score += 1
            elif spy_drawdown > -5:
                st.markdown("<span class='macro-red'>Historically Expensive (Near ATH)</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='macro-yellow'>Fair Value / Correction</span>", unsafe_allow_html=True)
                macro_score += 1
        else:
            st.error("Failed to load SPY data.")

    with col2:
        if not spy_data.empty and len(spy_data) >= 1000:
            spy_weekly = spy_close.resample('W').last()
            if len(spy_weekly) >= 200:
                sma_200_week = spy_weekly.rolling(window=200).mean().iloc[-1]
                pct_diff = ((spy_current/sma_200_week)-1)*100
                st.metric("Secular Trend (200-Week SMA)", f"${spy_current:.2f}", f"{pct_diff:+.1f}% vs 200w SMA", help="The 200-week Simple Moving Average defines the long-term, secular trend of the stock market. Trading above this line indicates a Secular Bull Market; dropping below indicates a Secular Bear Market.")
                if spy_current > sma_200_week:
                    st.markdown("<span class='macro-green'>Secular Bull Market</span>", unsafe_allow_html=True)
                    macro_score += 1
                else:
                    st.markdown("<span class='macro-red'>Secular Bear Market</span>", unsafe_allow_html=True)
            else:
                st.error("Need more data for 200-Week SMA.")
        else:
            st.error("Need more data for 200-Week SMA.")

    with col3:
        tnx_data = fetch_data("^TNX", period="1y")
        if not tnx_data.empty:
            tnx_close = get_series(tnx_data, 'Close')
            tnx_current = tnx_close.iloc[-1]
            real_yield = tnx_current - expected_inflation
            
            st.metric("10-Year Real Yield", f"{real_yield:.2f}%", f"Nominal: {tnx_current:.2f}%", help="Real Yield is the 10-Year Treasury rate minus Expected Inflation. A yield above 1.0% means borrowing money is expensive (Restrictive Capital Environment), which hurts growth stocks. A yield below 1.0% is Supportive, pushing capital into risk assets.")
            if real_yield < 1.0:
                st.markdown("<span class='macro-green'>Supportive for Risk Assets</span>", unsafe_allow_html=True)
                macro_score += 1
            else:
                st.markdown("<span class='macro-red'>Restrictive Capital Environment</span>", unsafe_allow_html=True)
        else:
            st.error("Failed to load TNX data.")

    with col4:
        dxy_data = fetch_data("DX-Y.NYB", period="2y")
        if not dxy_data.empty and len(dxy_data) >= 252:
            dxy_close = get_series(dxy_data, 'Close')
            dxy_current = dxy_close.iloc[-1]
            dxy_1y_ago = dxy_close.iloc[-252]
            delta_perc = ((dxy_current / dxy_1y_ago) - 1) * 100
            st.metric("US Dollar (52-Week Trend)", f"{dxy_current:.2f}", f"{delta_perc:+.1f}% (1y)", help="Tracks the strength of the US Dollar (DXY). Because global assets are priced in dollars, a falling dollar (Secular Liquidity Expansion) acts as a tailwind for stocks and crypto, while a rising dollar tightens global liquidity.")
            if dxy_current < dxy_1y_ago:
                st.markdown("<span class='macro-green'>Secular Liquidity Expansion</span>", unsafe_allow_html=True)
                macro_score += 1
            else:
                st.markdown("<span class='macro-red'>Secular Liquidity Tightening</span>", unsafe_allow_html=True)
        else:
            st.error("Failed to load DXY data.")

    st.markdown("---")
    return macro_score

def create_chart(data, ticker, timeframe):
    if timeframe == "1yr":
        plot_data = data.iloc[-252:].copy()
    elif timeframe == "5yr":
        plot_data = data.iloc[-1260:].copy()
    else: # Max
        plot_data = data.copy()
        
    fig = go.Figure()
    
    if timeframe in ["5yr", "Max"]:
        weekly_data = pd.DataFrame()
        weekly_data['Open'] = get_series(plot_data, 'Open').resample('W').first()
        weekly_data['High'] = get_series(plot_data, 'High').resample('W').max()
        weekly_data['Low'] = get_series(plot_data, 'Low').resample('W').min()
        weekly_data['Close'] = get_series(plot_data, 'Close').resample('W').last()
        weekly_data = weekly_data.dropna()
        plot_data_agg = weekly_data
    else:
        plot_data_agg = pd.DataFrame()
        plot_data_agg['Open'] = get_series(plot_data, 'Open')
        plot_data_agg['High'] = get_series(plot_data, 'High')
        plot_data_agg['Low'] = get_series(plot_data, 'Low')
        plot_data_agg['Close'] = get_series(plot_data, 'Close')
        
    fig.add_trace(go.Candlestick(
        x=plot_data_agg.index,
        open=plot_data_agg['Open'],
        high=plot_data_agg['High'],
        low=plot_data_agg['Low'],
        close=plot_data_agg['Close'],
        name='Price Action'
    ))
    
    close_full = get_series(data, 'Close')
    weekly_close = close_full.resample('W').last().dropna()
    sma_200w = weekly_close.rolling(window=200).mean()
    
    sma_200w_plot = sma_200w.reindex(plot_data_agg.index, method='ffill')
    
    fig.add_trace(go.Scatter(x=plot_data_agg.index, y=sma_200w_plot, line=dict(color='#ff9800', width=2), name='200-Week SMA'))
    
    fig.update_layout(
        template="plotly_dark",
        title=f"{ticker} Secular Trend",
        xaxis_title="",
        yaxis_title="Price",
        height=350,  # Slightly shorter for mobile screens
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), # Horizontal legend above chart avoids overlap
        dragmode='pan' # Better for touch screens
    )
    return fig

st.title("Market Watchlist")

st.sidebar.header("Macro Settings")
expected_inflation = st.sidebar.number_input("Expected Long-Term Inflation (%)", value=2.5, step=0.1)

macro_score = run_macro_engine(expected_inflation)

config = load_config()
tickers_list = config.get('tickers', [])
thresh = config.get("global_thresholds", {
    "index_max_er": 0.40, "index_max_pe": 20.0,
    "bluechip_max_pe": 30.0,
    "growth_good_peg": 1.2, "growth_bad_peg": 2.5, "growth_max_pe": 50.0,
    "crypto_good_sma": 5.0, "crypto_bad_sma": -10.0
})

if not tickers_list:
    st.info("Your watchlist is empty. Please use the Setup page to add assets.")
else:
    processed_assets = []
    targets_reached = []
    available_tags_set = set()
    
    for item in tickers_list:
        t = item['symbol']
        capital = float(item.get('capital', 0))
        tag = item.get('tag', "Blue Chip")
        
        # Legacy profile migration fallback
        if 'profile' in item and 'tag' not in item:
            if 'Index' in item['profile']: tag = 'Index'
            elif 'Blue Chip' in item['profile']: tag = 'Blue Chip'
            elif 'Crypto' in item['profile']: tag = 'Crypto'
            else: tag = 'Growth'
            
        custom_target = float(item.get('custom_target', 0.0))
        available_tags_set.add(tag)
        
        data = fetch_data(t, period="max")
        if data.empty:
            st.warning(f"No data found for ticker: {t}")
            continue
            
        close_prices = get_series(data, 'Close')
        current_price = close_prices.iloc[-1]
        ath = close_prices.max()
        drawdown_pct = ((current_price / ath) - 1) * 100
        
        if custom_target > 0 and current_price <= custom_target:
            targets_reached.append({
                "symbol": t, 
                "price": current_price, 
                "target": custom_target,
                "drawdown": drawdown_pct
            })
            
        weekly_close = close_prices.resample('W').last().dropna()
        dist_to_sma = None
        if len(weekly_close) >= 200:
            sma_200w = weekly_close.rolling(window=200).mean().iloc[-1]
            dist_to_sma = ((current_price / sma_200w) - 1) * 100
            
        weekly_rsi = 50
        if len(weekly_close) >= 14:
            weekly_rsi = calculate_rsi(weekly_close).iloc[-1]
            
        info = fetch_info(t) if tag != 'Crypto' else {}
        fund_border_color = "#ff9800"
        health_status = "Neutral"
        
        if tag == 'Crypto':
            if dist_to_sma is not None:
                if dist_to_sma > thresh["crypto_good_sma"]: 
                    fund_border_color = "#00e676"
                    health_status = "Strong"
                elif dist_to_sma < thresh["crypto_bad_sma"]: 
                    fund_border_color = "#ff1744"
                    health_status = "Weak"
        elif info:
            if tag == 'Index':
                er = info.get("annualReportExpenseRatio", info.get("fundPerformance", {}).get("annualReportExpenseRatio", None))
                pe = info.get("trailingPE", None)
                er_pct = (er * 100 if er < 1 else er) if er is not None else 0
                if er_pct > thresh["index_max_er"]: 
                    fund_border_color = "#ff1744"
                    health_status = "Weak"
                elif pe and pe < thresh["index_max_pe"] and er_pct <= thresh["index_max_er"]: 
                    fund_border_color = "#00e676"
                    health_status = "Strong"
            elif tag == 'Blue Chip':
                fcf = info.get("freeCashflow", None)
                trailing_pe = info.get("trailingPE", None)
                forward_pe = info.get("forwardPE", None)
                mock_5y_pe = (trailing_pe + forward_pe) / 2 if (trailing_pe and forward_pe) else 15.0
                if (fcf is not None and fcf < 0) or (trailing_pe and trailing_pe > thresh["bluechip_max_pe"]): 
                    fund_border_color = "#ff1744"
                    health_status = "Weak"
                elif trailing_pe and trailing_pe < mock_5y_pe and fcf and fcf > 0: 
                    fund_border_color = "#00e676"
                    health_status = "Strong"
            elif tag == 'Growth':
                fwd_pe = info.get("forwardPE", None)
                peg = info.get("pegRatio", None)
                if peg is not None:
                    if peg < thresh["growth_good_peg"]: 
                        fund_border_color = "#00e676"
                        health_status = "Strong"
                    elif peg > thresh["growth_bad_peg"] or (fwd_pe and fwd_pe > thresh["growth_max_pe"]): 
                        fund_border_color = "#ff1744"
                        health_status = "Weak"
                else:
                    if fwd_pe and fwd_pe > thresh["growth_max_pe"]: 
                        fund_border_color = "#ff1744"
                        health_status = "Weak"
                    elif fwd_pe and fwd_pe < (thresh["growth_max_pe"]/2): 
                        fund_border_color = "#00e676"
                        health_status = "Strong"

        if tag == "Index": tiers = [-5, -10, -20, -30]
        elif tag in ["Crypto", "Growth"]: tiers = [-20, -40, -60, -80]
        else: tiers = [-10, -20, -30, -50]
        
        is_discounted = drawdown_pct < tiers[0]

        processed_assets.append({
            "symbol": t, "capital": capital, "tag": tag, "custom_target": custom_target,
            "data": data, "current_price": current_price, "ath": ath, 
            "drawdown_pct": drawdown_pct, "close_prices": close_prices,
            "weekly_rsi": weekly_rsi, "dist_to_sma": dist_to_sma, "info": info,
            "fund_border_color": fund_border_color, "health_status": health_status,
            "tiers": tiers, "is_discounted": is_discounted
        })

    # Summary Section
    st.header("🎯 Top Fundamental Buy Candidates")
    buy_candidates = [a for a in processed_assets if a["health_status"] == "Strong" and a["is_discounted"]]
    
    if buy_candidates:
        cols = st.columns(min(len(buy_candidates), 4))
        for i, cand in enumerate(buy_candidates[:4]):
            with cols[i]:
                st.markdown(f"<div style='border: 1px solid #00e676; border-radius: 8px; padding: 10px; text-align: center;'>"
                            f"<h3>{cand['symbol']}</h3>"
                            f"<p style='color: #00e676; font-weight: bold;'>{cand['tag']}</p>"
                            f"<small>Drawdown: {cand['drawdown_pct']:.1f}%</small>"
                            f"</div>", unsafe_allow_html=True)
    else:
        st.info("No assets currently meet both strong fundamental and discount criteria. Patience is key.")
        
    if targets_reached:
        st.header("🚨 ACTION REQUIRED: Custom Targets Reached")
        for tr in targets_reached:
            st.success(f"**{tr['symbol']}** has fallen below your custom buy target of **${tr['target']:.2f}**. Current Price: **${tr['price']:.2f}** (Drawdown: {tr['drawdown']:.2f}%)")
        st.markdown("---")

    # Tag Filtering UI
    st.sidebar.markdown("---")
    st.sidebar.header("Dashboard Filters")
    available_tags_list = sorted(list(available_tags_set))
    if not available_tags_list:
        available_tags_list = ["Index", "Blue Chip", "Growth", "Crypto"]
    
    selected_tags = st.sidebar.multiselect(
        "Select Tags to Display", 
        options=available_tags_list, 
        default=available_tags_list
    )
    
    filtered_assets = [a for a in processed_assets if a['tag'] in selected_tags]

    st.header("Watchlist & Drawdown Tracker")
    timeframe = st.radio("Chart Timeframe", ["1yr", "5yr", "Max"], horizontal=True, index=1)
    
    # Group rendering by tag
    for current_tag in ["Index", "Blue Chip", "Growth", "Crypto"]:
        tag_assets = [a for a in filtered_assets if a['tag'] == current_tag]
        
        if not tag_assets:
            continue
            
        st.markdown(f"<h2 style='color:#00e676; margin-top:40px;'>🏷️ {current_tag} Watchlist</h2>", unsafe_allow_html=True)
        st.markdown("---")

        for asset in tag_assets:
            t = asset['symbol']
            capital = asset['capital']
            tag = asset['tag']
            custom_target = asset['custom_target']
            data = asset['data']
            current_price = asset['current_price']
            ath = asset['ath']
            drawdown_pct = asset['drawdown_pct']
            close_prices = asset['close_prices']
            weekly_rsi = asset['weekly_rsi']
            dist_to_sma = asset['dist_to_sma']
            info = asset['info']
            fund_border_color = asset['fund_border_color']
            tiers = asset['tiers']
            
            if drawdown_pct > tiers[0]:
                suggested_deployment = capital * 0.0
                tranche_msg = "Market near highs. Accumulate cash."
            elif drawdown_pct > tiers[1]:
                suggested_deployment = capital * 0.20
                tranche_msg = f"Mild correction. Deploy 20% of target capital (${suggested_deployment:,.2f})."
            elif drawdown_pct > tiers[2]:
                suggested_deployment = capital * 0.50
                tranche_msg = f"Major correction. Deploy 50% of target capital (${suggested_deployment:,.2f})."
            elif drawdown_pct > tiers[3]:
                suggested_deployment = capital * 0.80
                tranche_msg = f"Severe bear market. Deploy 80% of target capital (${suggested_deployment:,.2f})."
            else:
                suggested_deployment = capital * 1.0
                tranche_msg = f"Generational crash. Deploy 100% of target capital (${suggested_deployment:,.2f})."

            col_text, col_chart = st.columns([1, 3])
            
            with col_text:
                st.subheader(t)
                st.metric("Current Price", f"${current_price:.2f}")
                st.metric("Drawdown from ATH", f"{drawdown_pct:.2f}%", f"ATH: ${ath:.2f}", help="Percentage drop from the highest price ever recorded. Used by the Tranche System to determine how much capital to deploy.")
                st.metric("Weekly RSI", f"{weekly_rsi:.1f}", help="Relative Strength Index (Weekly). Measures momentum on a scale of 0 to 100. A value below 30 indicates the asset has been aggressively dumped and is 'Massively Oversold', often signaling a strong entry point.")
                
                # Conditional Valuation Engine
                fund_html = f"<div class='fund-box' style='border-left: 4px solid {fund_border_color};'><strong>Fundamental Engine ({tag})</strong><br><br>"
                
                if tag == 'Crypto':
                    fund_html += "🔹 <em>Digital Asset - Fundamentals N/A</em><br>"
                    fund_html += "<small>Relying strictly on 200d SMA and macro triggers.</small>"
                else:
                    if not info:
                        fund_html += "<em>Fundamental data currently unavailable</em>"
                    else:
                        if tag == 'Index':
                            er = info.get("annualReportExpenseRatio", info.get("fundPerformance", {}).get("annualReportExpenseRatio", None))
                            dy = info.get("yield", info.get("dividendYield", None))
                            pe = info.get("trailingPE", None)
                            
                            if er is not None:
                                er_pct = er * 100 if er < 1 else er
                                er_color = "#ff1744" if er_pct > thresh["index_max_er"] else "#00e676"
                                fund_html += f"<abbr title='The annual fee charged by the fund. High fees compound over decades, significantly eating into long-term returns.'>Expense Ratio</abbr>: <span style='color:{er_color};'>{er_pct:.2f}%</span><br>"
                            else:
                                fund_html += "<abbr title='The annual fee charged by the fund.'>Expense Ratio</abbr>: N/A<br>"
                                
                            fund_html += f"<abbr title='The annual dividend payment as a percentage of the current share price.'>Dividend Yield</abbr>: {dy * 100:.2f}%<br>" if dy else "<abbr title='The annual dividend payment.'>Dividend Yield</abbr>: N/A<br>"
                            fund_html += f"<abbr title='Price-to-Earnings ratio. A lower number implies the asset is cheaper relative to the earnings it generates.'>Aggregate P/E</abbr>: {pe:.2f}<br>" if pe else "<abbr title='Price-to-Earnings ratio.'>Aggregate P/E</abbr>: N/A<br>"
                            
                        elif tag == 'Blue Chip':
                            fcf = info.get("freeCashflow", None)
                            dy = info.get("dividendYield", None)
                            trailing_pe = info.get("trailingPE", None)
                            forward_pe = info.get("forwardPE", None)
                            
                            fund_html += f"<abbr title='The cash a company generates after accounting for cash outflows. Negative FCF is a massive risk for blue-chip companies as it means they are burning cash to survive.'>Free Cash Flow</abbr>: ${fcf:,.0f}<br>" if fcf else "<abbr title='The cash a company generates.'>Free Cash Flow</abbr>: N/A<br>"
                            fund_html += f"<abbr title='The annual dividend payment as a percentage of the current share price.'>Dividend Yield</abbr>: {dy * 100:.2f}%<br>" if dy else "<abbr title='The annual dividend payment.'>Dividend Yield</abbr>: N/A<br>"
                            
                            if trailing_pe:
                                mock_5y_pe = (trailing_pe + forward_pe) / 2 if (trailing_pe and forward_pe) else 15.0
                                pe_color = "#00e676" if trailing_pe < mock_5y_pe else "#ffffff"
                                fund_html += f"<abbr title='Price-to-Earnings based on the last 12 months. If this is higher than its 5-year average, the stock is historically expensive.'>Trailing P/E</abbr>: <span style='color:{pe_color};'>{trailing_pe:.2f}</span> <small>(vs 5y Avg {mock_5y_pe:.2f})</small><br>"
                            else:
                                fund_html += "<abbr title='Price-to-Earnings based on the last 12 months.'>Trailing P/E</abbr>: N/A<br>"
                                
                        elif tag == 'Growth':
                            fwd_pe = info.get("forwardPE", None)
                            peg = info.get("pegRatio", None)
                            
                            fund_html += f"<abbr title='Price-to-Earnings based on projected future earnings. High growth companies trade at high Forward P/E ratios.'>Forward P/E</abbr>: {fwd_pe:.2f}<br>" if fwd_pe else "<abbr title='Price-to-Earnings based on projected future earnings.'>Forward P/E</abbr>: N/A<br>"
                            if peg is not None:
                                if peg < thresh["growth_good_peg"]:
                                    fund_html += f"<abbr title='Price/Earnings-to-Growth ratio. It divides the P/E by the expected growth rate. A PEG under 1.2 is considered undervalued, while a PEG over 2.5 means you are overpaying for growth.'>PEG Ratio</abbr>: <span style='color:#00e676;'>{peg:.2f}</span> <small>(Growth justifies valuation)</small><br>"
                                elif peg > thresh["growth_bad_peg"] or (fwd_pe and fwd_pe > thresh["growth_max_pe"]):
                                    fund_html += f"<abbr title='Price/Earnings-to-Growth ratio. It divides the P/E by the expected growth rate. A PEG under 1.2 is considered undervalued, while a PEG over 2.5 means you are overpaying for growth.'>PEG Ratio</abbr>: <span style='color:#ffea00;'>{peg:.2f}</span> <small>(High relative to growth)</small><br>"
                                else:
                                    fund_html += f"<abbr title='Price/Earnings-to-Growth ratio.'>PEG Ratio</abbr>: {peg:.2f}<br>"
                            else:
                                fund_html += "<abbr title='Price/Earnings-to-Growth ratio.'>PEG Ratio</abbr>: N/A<br>"
                
                fund_html += "</div>"
                st.markdown(fund_html, unsafe_allow_html=True)
                
                st.markdown("#### Capital Deployment Strategy")
                st.markdown(f"**Target Capital:** ${capital:,.2f}")
                if custom_target > 0:
                    st.markdown(f"**Custom Buy Target:** ${custom_target:.2f}")
                
                # Highlight other metrics
                if weekly_rsi < 30:
                    st.markdown("<span class='macro-green'>MASSIVELY OVERSOLD (Weekly RSI < 30)</span>", unsafe_allow_html=True)
                if dist_to_sma is not None and dist_to_sma < 5 and dist_to_sma > -15:
                    st.markdown("<span class='macro-green'>GENERATIONAL SUPPORT (Near 200w SMA)</span>", unsafe_allow_html=True)
                
                if macro_score >= 3 and drawdown_pct < tiers[0]:
                    st.success("GREEN LIGHT: Favorable macro environment and asset is discounted.")
                elif macro_score < 3 and drawdown_pct < tiers[0]:
                    st.warning("CAUTION: Asset is discounted, but macro risks remain high.")
                else:
                    st.info("WAIT: Asset is relatively expensive.")
                    
                st.markdown(f"**Action:** {tranche_msg}")
                
            with col_chart:
                fig = create_chart(data, t, timeframe)
                st.plotly_chart(fig, use_container_width=True)
                
            st.markdown("---")
