
import streamlit as st
import pandas as pd
import json
import hashlib
from pathlib import Path
from datetime import datetime

# ---------------- PAGE SETTINGS ----------------
st.set_page_config(
    page_title="Mangrove Atlas",
    page_icon="🌿",
    layout="wide"
)

USERS_FILE = Path("mangrove_users.json")
HISTORY_FILE = Path("mangrove_history.json")


# ---------------- FILE HELPERS ----------------
def read_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def write_json(path, data):
    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ---------------- DESIGN ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #e0f7fa, #f1f8e9);
}
.main-title {
    text-align: center;
    color: #00695c;
    font-size: 42px;
    font-weight: bold;
}
.subtitle {
    text-align: center;
    color: #336b63;
    font-size: 18px;
}
div.stButton > button {
    background-color: #00796b;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 8px 20px;
}
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "Home"


# ---------------- HEADER ----------------
st.markdown(
    '<div class="main-title">🌿 Mangrove Atlas</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">Explore • Understand • Protect Mangroves</div>',
    unsafe_allow_html=True
)
st.divider()


# ---------------- LOGIN AND REGISTRATION ----------------
if st.session_state.user is None:
    left, center, right = st.columns([1, 1.5, 1])

    with center:
        st.subheader("Welcome to Mangrove Atlas")
        st.write(
            "Explore mangrove ecosystem data through "
            "interactive tables and visualizations."
        )

        action = st.radio(
            "Choose an option",
            ["Login", "Register"],
            horizontal=True
        )

        with st.form("account_form"):
            username = st.text_input("Username")
            password = st.text_input(
                "Password",
                type="password"
            )

            if action == "Register":
                confirm = st.text_input(
                    "Confirm password",
                    type="password"
                )
            else:
                confirm = password

            submitted = st.form_submit_button(
                action,
                use_container_width=True
            )

        if submitted:
            username = username.strip()

            if not username or not password:
                st.error("Please enter both username and password.")

            elif action == "Register":
                users = read_json(USERS_FILE)

                if username in users:
                    st.error("This username already exists.")

                elif password != confirm:
                    st.error("The passwords do not match.")

                elif len(password) < 6:
                    st.error("Use a password with at least 6 characters.")

                else:
                    users[username] = hash_password(password)
                    write_json(USERS_FILE, users)
                    st.success("Registration successful! Please log in.")

            else:
                users = read_json(USERS_FILE)

                if users.get(username) == hash_password(password):
                    st.session_state.user = username
                    st.session_state.page = "Home"
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

    st.stop()


# ---------------- LOGGED-IN USER ----------------
username = st.session_state.user

with st.sidebar:
    st.title("🌿 Mangrove Atlas")
    st.write(f"Welcome, **{username}**!")

    page = st.radio(
        "Navigation",
        ["Home", "Explore Data", "Search History"],
        key="navigation"
    )

    st.divider()

    if st.button("Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.page = "Home"
        st.rerun()


# ---------------- HOME PAGE ----------------
if page == "Home":
    st.header("Welcome to your Mangrove Atlas!")

    st.write("""
    Discover and analyse mangrove ecosystem information
    using simple data-analysis tools.

    Upload a CSV file to explore your dataset, view summaries,
    and create charts.
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("🌱 **Explore**\n\nExamine mangrove data.")

    with col2:
        st.info("📊 **Visualise**\n\nCreate interactive charts.")

    with col3:
        st.info("🔎 **Analyse**\n\nUnderstand data patterns.")

    st.subheader("Getting Started")
    st.write("1. Open **Explore Data** in the sidebar.")
    st.write("2. Upload a CSV file.")
    st.write("3. Select a column and explore the charts.")


# ---------------- EXPLORE DATA ----------------
elif page == "Explore Data":
    st.header("📊 Explore Mangrove Data")

    uploaded = st.file_uploader(
        "Upload your CSV dataset",
        type=["csv"]
    )

    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)

            st.subheader("Dataset Preview")
            st.dataframe(df, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Rows", len(df))
            col2.metric("Columns", len(df.columns))
            col3.metric("Missing Values", int(df.isna().sum().sum()))

            st.subheader("Data Summary")
            st.dataframe(
                df.describe(include="all").transpose(),
                use_container_width=True
            )

            numeric_columns = df.select_dtypes(
                include="number"
            ).columns.tolist()

            if numeric_columns:
                selected_column = st.selectbox(
                    "Choose a numeric column for a chart",
                    numeric_columns
                )

                st.subheader(f"Chart: {selected_column}")
                st.bar_chart(df[selected_column])

                if len(numeric_columns) >= 2:
                    x_column = st.selectbox(
                        "Choose the first column for comparison",
                        numeric_columns
                    )

                    y_options = [
                        c for c in numeric_columns
                        if c != x_column
                    ]

                    y_column = st.selectbox(
                        "Choose the second column",
                        y_options
                    )

                    st.scatter_chart(
                        df,
                        x=x_column,
                        y=y_column
                    )
            else:
                st.info(
                    "No numeric columns were found in this dataset."
                )

            # Save this upload in the signed-in user's history
            history = read_json(HISTORY_FILE)
            user_history = history.get(username, [])

            entry = {
                "file": uploaded.name,
                "time": datetime.now().strftime(
                    "%d-%m-%Y %H:%M"
                ),
                "rows": len(df),
                "columns": len(df.columns)
            }

            if not user_history or user_history[-1] != entry:
                user_history.append(entry)

            history[username] = user_history[-50:]
            write_json(HISTORY_FILE, history)

            st.success("Dataset loaded successfully!")

        except Exception as error:
            st.error(f"Could not read this CSV file: {error}")


# ---------------- SEARCH HISTORY ----------------
elif page == "Search History":
    st.header("🕘 Your Search History")

    history = read_json(HISTORY_FILE)
    user_history = history.get(username, [])

    if user_history:
        st.dataframe(
            pd.DataFrame(user_history),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(
            "No datasets explored yet. Upload a CSV file "
            "in Explore Data to start your history."
        )

    if user_history and st.button("Clear My History"):
        history[username] = []
        write_json(HISTORY_FILE, history)
        st.success("Your history has been cleared.")
        st.rerun()


# ---------------- FOOTER ----------------
st.divider()
st.caption(
    "Mangrove Atlas | MCA Mini Project | "
    "Mangrove Ecosystem Data Analysis and Visualization"
)       