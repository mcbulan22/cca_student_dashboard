import streamlit as st
import pandas as pd
import numpy as np
import streamlit_authenticator as stauth
import yaml
import matplotlib.pyplot as plt
import seaborn as sns
from yaml.loader import SafeLoader

st.set_page_config(layout="wide")

# --- AUTHENTICATION ---
credentials = {
    "usernames": {
        "Admin": {
            "email": "marlon.bulan@maap.edu.ph",
            "name": "Sir Marlon",
            "password": "$2b$12$I4J0sbdaLJCl2TzHi.j3JO55W2AFz3M/RxZUpHu9xsa05cn6Ad.bm"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "maap_dashboard_cookie",
    "maap_dashboard_secret",
    1
)

name, auth_status, username = authenticator.login("Login", "main")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    return pd.read_excel("students.xlsx")

if auth_status:
    st.sidebar.image("maap_logo.png", width=120)
    st.sidebar.title(f"Welcome, {name}")
    authenticator.logout("Logout", "sidebar")

    df = load_data()
    df = df.dropna(subset=["Student Name", "Course", "Exam", "Score"])

    st.title("📊 MAAP Student Performance Dashboard")

    tab1, tab2 = st.tabs(["👤 Individual View", "👥 Group View"])

    # -----------------------
    # INDIVIDUAL VIEW
    # -----------------------
    with tab1:
        st.header("Student Profile and Exam Results")

        student_list = sorted(df["Student Name"].unique())
        selected_student = st.selectbox("Select a Student", student_list)

        exam_options = sorted(df["Exam"].unique())
        year_levels = sorted(df["Year Level"].dropna().unique())

        exam_filter = st.multiselect("Select Exam Types", exam_options,
                                     default=[e for e in exam_options if e != "Continuous Assessment"],
                                     key="student_exam")

        year_level_filter = st.multiselect("Select Year Levels", year_levels,
                                           default=year_levels,
                                           key="student_year")

        student_df = df[
            (df["Student Name"] == selected_student) &
            (df["Exam"].isin(exam_filter)) &
            (df["Year Level"].isin(year_level_filter))
        ]

        st.subheader("📋 Selected Exam Records")
        st.dataframe(student_df)

        if not student_df.empty:
            fig1, ax1 = plt.subplots(figsize=(10, 5))
            sns.barplot(data=student_df, x="Course", y="Score", hue="Exam", ax=ax1)
            ax1.set_title(f"{selected_student}'s Exam Scores by Course")
            ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha="right")
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            st.pyplot(fig1)

        # CONTINUOUS ASSESSMENT (line graph per year level)
        ca_df = df[
            (df["Student Name"] == selected_student) &
            (df["Exam"] == "Continuous Assessment")
        ]

        if not ca_df.empty:
            st.subheader("📈 Continuous Assessment Trends by Year Level")

            ca_df["Year Level"] = pd.Categorical(ca_df["Year Level"], categories=["First Year", "Second Year", "Third Year"], ordered=True)

            fig2, ax2 = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=ca_df, x="Year Level", y="Score", hue="Course", marker="o", ax=ax2)
            ax2.set_title(f"{selected_student} - Continuous Assessment Progression")
            ax2.set_ylabel("Score")
            ax2.set_xlabel("Year Level")
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            st.pyplot(fig2)

    # -----------------------
    # GROUP VIEW
    # -----------------------
    with tab2:
        st.header("Group Performance Analysis")

        programs = sorted(df["Program"].dropna().unique())
        class_list = sorted(df["Class"].dropna().unique())

        program_filter = st.selectbox("Select Program", programs, key="group_program")
        class_filter = st.selectbox("Select Class", ["All"] + class_list, key="group_class")
        exam_group = st.multiselect("Exam Types", exam_options,
                                    default=[e for e in exam_options if e != "Continuous Assessment"],
                                    key="group_exam")
        year_level_group = st.multiselect("Year Level", year_levels, default=year_levels, key="group_year")

        group_df = df[
            (df["Program"] == program_filter) &
            (df["Year Level"].isin(year_level_group)) &
            (df["Exam"].isin(exam_group))
        ]

        if class_filter != "All":
            group_df = group_df[group_df["Class"] == class_filter]

        st.subheader("📋 Group Exam Records")
        st.dataframe(group_df)

        if not group_df.empty:
            avg_df = group_df.groupby(["Course", "Exam"]).mean(numeric_only=True).reset_index()
            fig3, ax3 = plt.subplots(figsize=(10, 5))
            sns.barplot(data=avg_df, x="Course", y="Score", hue="Exam", ax=ax3)
            ax3.set_title(f"{program_filter} Group Average Scores by Course")
            ax3.set_xticklabels(ax3.get_xticklabels(), rotation=45, ha="right")
            ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            st.pyplot(fig3)

        # CONTINUOUS ASSESSMENT (Line + Heatmap)
        group_ca_df = df[
            (df["Program"] == program_filter) &
            (df["Exam"] == "Continuous Assessment")
        ]

        if not group_ca_df.empty:
            st.subheader("📈 Continuous Assessment - Group Trend")

            avg_ca = group_ca_df.groupby(["Academic Year", "Course"]).mean(numeric_only=True).reset_index()

            fig4, ax4 = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=avg_ca, x="Academic Year", y="Score", hue="Course", marker="o", ax=ax4)
            ax4.set_title("Average Continuous Assessment Over Time")
            ax4.set_ylabel("Score")
            ax4.set_xlabel("Academic Year")
            ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            st.pyplot(fig4)

            # 📊 Heatmap
            st.subheader("🔍 Heatmap: Continuous Assessment Scores")
            pivot = avg_ca.pivot_table(index="Course", columns="Academic Year", values="Score", aggfunc='mean').fillna(0)

            fig5, ax5 = plt.subplots(figsize=(10, 6))
            sns.heatmap(pivot, annot=True, fmt=".0f", cmap="coolwarm", ax=ax5)
            ax5.set_title("Course Performance Heatmap")
            st.pyplot(fig5)

else:
    st.warning("Please enter your credentials.")
