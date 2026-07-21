import streamlit as st
import extra_streamlit_components as stx

st.set_page_config(page_title="Institutional Market Dashboard", layout="wide", initial_sidebar_state="auto")

cookie_manager = stx.CookieManager(key="auth_cookie_manager")

# Inject PWA Meta Tags
st.markdown("""
<head>
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#0e1117">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Market Dash">
</head>
""", unsafe_allow_html=True)

# Authentication Check
if cookie_manager.get("auth_token") == "authenticated":
    st.session_state["authenticated"] = True
elif "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state.get("authenticated", False):
        return True
        
    st.title("🔐 Authentication Required")
    st.markdown("Please enter your access password to unlock the dashboard.")
    
    pwd_input = st.text_input("Password", type="password")
    if st.button("Unlock Dashboard", type="primary"):
        correct_password = "invest2026"
        try:
            if "APP_PASSWORD" in st.secrets:
                correct_password = st.secrets["APP_PASSWORD"]
        except:
            pass
            
        if pwd_input == correct_password:
            st.session_state["authenticated"] = True
            cookie_manager.set("auth_token", "authenticated", expires_at=None) # Persist indefinitely
            st.success("Access Granted!")
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

if check_password():
    dashboard_page = st.Page("views/dashboard_view.py", title="Dashboard", default=True)
    setup_page = st.Page("views/setup_view.py", title="Setup")

    pg = st.navigation([dashboard_page, setup_page])
    pg.run()
