"""
Streamlit dashboard for Music Charts Tracking API.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from typing import Optional
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_V1 = f"{API_URL}/api/v1"

st.set_page_config(
    page_title="Music Charts Tracking Dashboard",
    page_icon="music",
    layout="wide"
)

if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "username" not in st.session_state:
    st.session_state.username = None


def register(username: str, email: str, password: str, role: str = "viewer") -> bool:
    """Register a new user."""
    try:
        response = requests.post(
            f"{API_V1}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "role": role
            }
        )
        if response.status_code == 201:
            st.success(f"User {username} registered successfully! Please login.")
            return True
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            if isinstance(error_detail, list):
                error_detail = error_detail[0].get('msg', 'Unknown error')
            st.error(f"Registration failed: {error_detail}")
            return False
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return False


def login(username: str, password: str) -> bool:
    """Login and get access token."""
    try:
        response = requests.post(
            f"{API_V1}/auth/token",
            data={
                "username": username,
                "password": password,
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.access_token = data["access_token"]
            st.session_state.username = username
            return True
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
                if isinstance(error_detail, list):
                    error_detail = error_detail[0].get('msg', 'Unknown error')
                st.error(f"Login failed: {error_detail}")
            except:
                st.error(f"Login failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return False


def get_headers() -> dict:
    """Get headers with authentication token."""
    if st.session_state.access_token:
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}


def fetch_charts(date_filter: Optional[date] = None, date_from: Optional[date] = None, 
                 date_to: Optional[date] = None, source: Optional[str] = None,
                 country: Optional[str] = None, artist: Optional[str] = None, limit: int = 100) -> list:
    """Fetch charts from API."""
    try:
        params = {"limit": limit}
        if date_filter:
            params["date"] = date_filter.isoformat()
        elif date_from or date_to:
            if date_from:
                params["date_from"] = date_from.isoformat()
            if date_to:
                params["date_to"] = date_to.isoformat()
        if source:
            params["source"] = source
        if country:
            params["country"] = country
        if artist:
            params["artist"] = artist
        
        response = requests.get(f"{API_V1}/charts", params=params, headers=get_headers(), timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', 'Unknown error')
                if isinstance(error_detail, list):
                    error_detail = error_detail[0].get('msg', 'Unknown error') if error_detail else 'Unknown error'
                st.error(f"Error fetching charts: {error_detail}")
            except (ValueError, KeyError):
                st.error(f"Error fetching charts: HTTP {response.status_code} - {response.text[:200] if response.text else 'No response body'}")
            return []
    except requests.exceptions.Timeout:
        st.error("Request timed out. Try again.")
        return []
    except requests.exceptions.ConnectionError:
        st.error("Connection error. Check if API is running.")
        return []
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return []


def fetch_top_charts(selected_date: date, source: Optional[str] = None,
                    country: Optional[str] = None, limit: int = 10) -> list:
    """Fetch top charts for a specific date."""
    try:
        params = {"date": selected_date.isoformat(), "limit": limit}
        if source:
            params["source"] = source
        if country and country.strip() and country.lower() != "global":
            params["country"] = country.strip()
        
        response = requests.get(f"{API_V1}/charts/top", params=params, headers=get_headers(), timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else []
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
                if isinstance(error_detail, list):
                    error_detail = error_detail[0].get('msg', 'Unknown error') if error_detail else 'Unknown error'
                st.error(f"Error fetching top charts: {error_detail}")
            except:
                st.error(f"Error fetching top charts: HTTP {response.status_code}")
            return []
    except requests.exceptions.Timeout:
        st.error("Request timed out. Try again.")
        return []
    except requests.exceptions.ConnectionError:
        st.error("Connection error. Check if API is running.")
        return []
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return []


def fetch_trends(days: int = 30, source: Optional[str] = None) -> list:
    """Fetch trend analysis."""
    try:
        params = {"days": days, "min_appearances": 1}
        if source:
            params["source"] = source
        
        response = requests.get(f"{API_V1}/trends/top-artists", params=params, headers=get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            if isinstance(error_detail, list):
                error_detail = error_detail[0].get('msg', 'Unknown error') if error_detail else 'Unknown error'
            st.error(f"Error fetching trends: {error_detail}")
            return []
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return []


def main():
    """Main dashboard application."""
    st.title("Music Charts Tracking Dashboard")
    
    if not st.session_state.access_token:
        st.sidebar.header("Authentication")
        
        auth_tab = st.sidebar.radio("Choose option", ["Login", "Register"], horizontal=True)
        
        if auth_tab == "Login":
            st.sidebar.subheader("Login")
            username = st.sidebar.text_input("Username", key="login_username")
            password = st.sidebar.text_input("Password", type="password", key="login_password")
            
            if st.sidebar.button("Login", type="primary", use_container_width=True):
                if username and password:
                    if login(username, password):
                        st.rerun()
                else:
                    st.sidebar.warning("Please enter both username and password")
        
        else:
            st.sidebar.subheader("Register New User")
            reg_username = st.sidebar.text_input("Username", key="reg_username", help="3-50 characters, alphanumeric")
            reg_email = st.sidebar.text_input("Email", key="reg_email", help="Valid email address")
            reg_password = st.sidebar.text_input("Password", type="password", key="reg_password", help="Minimum 8 characters")
            reg_role = st.sidebar.selectbox("Role", ["viewer", "editor", "admin"], index=0, key="reg_role", 
                                          help="Viewer: Read-only, Editor: Can create/edit, Admin: Full access")
            
            if st.sidebar.button("Register", type="primary", use_container_width=True):
                if reg_username and reg_email and reg_password:
                    if len(reg_password) < 8:
                        st.sidebar.warning("Password must be at least 8 characters")
                    else:
                        if register(reg_username, reg_email, reg_password, reg_role):
                            st.sidebar.info("Registration successful! Switch to Login tab to sign in.")
                else:
                    st.sidebar.warning("Please fill in all fields")
    else:
        st.sidebar.success(f"Logged in as: {st.session_state.username}")
        if st.sidebar.button("Logout"):
            st.session_state.access_token = None
            st.session_state.username = None
            st.rerun()
        
        page = st.sidebar.selectbox("Select Page", ["Top Charts", "Chart History", "Trend Analysis", "Data Export"])
        
        if page == "Top Charts":
            show_top_charts()
        elif page == "Chart History":
            show_chart_history()
        elif page == "Trend Analysis":
            show_trend_analysis()
        elif page == "Data Export":
            show_data_export()


def fetch_itunes_data(country: str = "us", limit: int = 50, days_back: int = 0):
    """Fetch chart data from iTunes."""
    try:
        params = {"country": country, "limit": limit}
        if days_back > 0:
            params["days_back"] = days_back
        
        response = requests.post(
            f"{API_V1}/sync/fetch/itunes",
            params=params,
            headers=get_headers(),
            timeout=60
        )
        if response.status_code == 201:
            result = response.json()
            return True, result.get("imported", 0), result.get("skipped", 0), result.get("fetched", 0), None, result.get("days_created", 1)
        else:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = f"HTTP {response.status_code}"
            return False, 0, 0, 0, error_detail, 0
    except Exception as e:
        return False, 0, 0, 0, str(e), 0


def show_top_charts():
    """Display top charts page."""
    st.header("Top Charts")
    
    with st.expander("Need data? Fetch iTunes charts first", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            fetch_country = st.selectbox("Country Code", ["us", "gb", "ca", "au", "de", "fr"], key="fetch_country")
        with col2:
            fetch_limit = st.slider("Songs per day", 10, 200, 50, key="fetch_limit")
        with col3:
            days_back = st.selectbox("Days of History", [0, 7, 14, 30], index=1, 
                                    help="0 = today only, 7 = last week, 14 = last 2 weeks, 30 = last month",
                                    key="days_back")
        
        if st.button("Fetch iTunes charts", type="primary", use_container_width=True):
            with st.spinner(f"Fetching charts from iTunes for {days_back + 1} days..."):
                success, imported, skipped, fetched, error, days_created = fetch_itunes_data(fetch_country, fetch_limit, days_back)
                if success:
                    if days_back > 0:
                        st.success(f"Imported {imported} entries across {days_created} days (fetched: {fetched}, skipped: {skipped})")
                        st.info(f"Data created for today and last {days_back} days. Use Chart History and Trend Analysis.")
                    else:
                        st.success(f"Imported {imported} new entries (fetched: {fetched}, skipped: {skipped})")
                        st.info("Try fetching top charts below with date set to today.")
                else:
                    st.error(f"Fetch failed: {error}")
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_date = st.date_input("Select Date", value=date.today())
    with col2:
        source = st.selectbox("Platform", [None, "Apple Music"], help="Select a platform to filter results")
    with col3:
        country = st.text_input("Country", value="US", help="Country code (e.g., US, GB, CA)")
    
    limit = st.slider("Number of entries", 10, 100, 20)
    
    if st.button("Fetch top charts", type="primary", use_container_width=True):
        with st.spinner(f"Fetching top charts for {selected_date}" + (f" from {source}" if source else "") + "..."):
            charts = fetch_top_charts(selected_date, source, country if country else None, limit)
            
        if charts and len(charts) > 0:
            df = pd.DataFrame(charts)
            
            st.success(f"Found {len(charts)} chart entries")
            
            display_cols = ["rank", "song", "artist", "source", "country"]
            if "streams" in df.columns:
                display_cols.append("streams")
            
            st.dataframe(df[display_cols], use_container_width=True)
            
            if len(df) > 0:
                fig = px.bar(
                    df.head(20),
                    x="song",
                    y="rank",
                    color="artist",
                    title=f"Top {min(20, len(df))} Songs by Rank" + (f" - {source}" if source else ""),
                    labels={"rank": "Chart Position", "song": "Song"},
                    orientation="h"
                )
                fig.update_layout(yaxis=dict(autorange="reversed"), height=600, xaxis_title="Song", yaxis_title="Rank")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No chart data found for {selected_date}" + (f" from {source}" if source else "") + (f" in {country}" if country else ""))
            st.info("Tip: use the data fetch above, or pick a different date.")


def show_chart_history():
    """Display chart history page."""
    st.header("Chart History")
    
    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("From Date", value=date.today() - timedelta(days=30))
    with col2:
        date_to = st.date_input("To Date", value=date.today())
    
    source = st.selectbox("Platform", [None, "Apple Music"])
    artist = st.text_input("Filter by Artist (optional)")
    
    limit = st.slider("Number of entries", 50, 500, 100)
    
    if st.button("Fetch Chart History"):
        with st.spinner(f"Fetching chart history from {date_from} to {date_to}..."):
            charts = fetch_charts(date_filter=None, date_from=date_from, date_to=date_to, 
                                 source=source, country=None, artist=artist, limit=limit)
        
        if charts and len(charts) > 0:
            df = pd.DataFrame(charts)
            
            if artist:
                df = df[df["artist"].str.contains(artist, case=False, na=False)]
            
            st.dataframe(df[["date", "rank", "song", "artist", "source", "streams"]])
            
            if len(df) > 0:
                df["date"] = pd.to_datetime(df["date"])
                fig = px.line(
                    df.sort_values("date"),
                    x="date",
                    y="rank",
                    color="song",
                    title="Chart Position Over Time",
                    labels={"rank": "Chart Position", "date": "Date"}
                )
                fig.update_layout(yaxis=dict(autorange="reversed"), height=500)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No chart data found for the selected date range" + (f" from {source}" if source else "") + (f" by {artist}" if artist else ""))
            st.info("Tip: fetch iTunes data first on Top Charts page, or pick a different range.")


def show_trend_analysis():
    """Display trend analysis page."""
    st.header("Trend Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        days = st.slider("Analysis Period (days)", 7, 365, 30)
    with col2:
        source = st.selectbox("Platform", [None, "Apple Music"])
    
    if st.button("Fetch Trend Analysis"):
        trends = fetch_trends(days, source)
        if trends:
            df = pd.DataFrame(trends)
            
            st.dataframe(df[["artist", "total_appearances", "average_rank", "best_rank", "trending_score"]])
            
            fig = px.bar(
                df.head(20),
                x="artist",
                y="trending_score",
                title="Top 20 Artists by Trending Score",
                labels={"trending_score": "Trending Score", "artist": "Artist"}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            fig2 = px.scatter(
                df.head(20),
                x="total_appearances",
                y="average_rank",
                size="trending_score",
                hover_data=["artist"],
                title="Artist Performance: Appearances vs Average Rank",
                labels={"total_appearances": "Total Appearances", "average_rank": "Average Rank"}
            )
            fig2.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig2, use_container_width=True)


def show_data_export():
    """Display data export page."""
    st.header("Data Export")
    
    st.info("Export chart data for analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        date_filter = st.date_input("Filter by Date", value=date.today())
    with col2:
        source = st.selectbox("Platform", [None, "Apple Music"])
    
    if st.button("Export Data"):
        charts = fetch_charts(date_filter, source, limit=1000)
        if charts:
            df = pd.DataFrame(charts)
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"charts_{date_filter}_{source or 'all'}.csv",
                mime="text/csv"
            )
            
            st.subheader("Data Preview")
            st.dataframe(df.head(100))


if __name__ == "__main__":
    main()

