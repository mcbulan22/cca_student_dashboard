import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

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

if auth_status:
    st.sidebar.image("maap_logo.png", width=120)
    st.sidebar.title(f"Welcome, {name}")
    authenticator.logout("Logout", "sidebar")

    df = pd.read_excel("students.xlsx")

    st.title("📊 MAAP Student Performance Dashboard")
    tab1, tab2 = st.tabs(["👤 Individual View", "👥 Group View"])

    # === INDIVIDUAL STUDENT VIEW ===
    with tab1:
        st.subheader("Individual Student Analysis")
        student = st.selectbox("Select a student", sorted(df["Student Name"].unique()))
        student_df = df[df["Student Name"] == student]
        st.dataframe(student_df)

        if not student_df.empty:
            student_df["Assessment Year"] = student_df["Assessment Year"].astype(int)
            student_df = student_df.sort_values(["Course Name", "Assessment Year"])

            # Line Chart
            fig1, ax1 = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=student_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax1)
            ax1.set_title(f"Score Trend by Course: {student}", fontsize=14)
            ax1.set_ylabel("Score (%)")
            ax1.set_xlabel("Assessment Year")
            ax1.legend(title="Course Name", bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.set_xticks(sorted(student_df["Assessment Year"].unique()))
            plt.tight_layout()
            st.pyplot(fig1)

            # Radar Chart: Student vs Class Avg
            st.subheader("🕸️ Student vs Class Average Profile (Radar)")
            year = st.selectbox("Select Year", sorted(student_df["Assessment Year"].unique()))
            year_student = student_df[student_df["Assessment Year"] == year]

            if not year_student.empty:
                program_name = year_student["Program"].iloc[0]
                year_program = df[(df["Assessment Year"] == year) & (df["Program"] == program_name)]

                # Build clean dataset of shared courses
                shared_courses = year_student["Course Name"].unique()
                student_scores = year_student.set_index("Course Name").reindex(shared_courses)["Score"]
                class_avg_scores = year_program.groupby("Course Name")["Score"].mean().reindex(shared_courses)

                # Drop any courses with NaN (missing from either)
                combined = pd.DataFrame({
                    "Student": student_scores,
                    "ClassAvg": class_avg_scores
                }).dropna()

                if not combined.empty:
                    categories = combined.index.tolist()
                    N = len(categories)

                    # Scores
                    values_student = combined["Student"].tolist()
                    values_class = combined["ClassAvg"].tolist()

                    # Close the loop
                    values_student += values_student[:1]
                    values_class += values_class[:1]

                    # Angles
                    angles = [n / float(N) * 2 * np.pi for n in range(N)]
                    angles += angles[:1]

                    # Plot radar
                    fig_radar, ax_radar = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                    ax_radar.plot(angles, values_student, linewidth=2, label="Student")
                    ax_radar.fill(angles, values_student, alpha=0.25)
                    ax_radar.plot(angles, values_class, linewidth=2, linestyle='dashed', label="Class Avg")
                    ax_radar.set_thetagrids(np.degrees(angles[:-1]), categories)
                    ax_radar.set_title(f"{student}'s Score Profile - {year}", y=1.1)
                    ax_radar.set_ylim(0, 100)
                    ax_radar.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
                    st.pyplot(fig_radar)
                else:
                    st.warning("No comparable data between student and group for that year.")

    # === GROUP VIEW ===
    with tab2:
        st.subheader("Group Performance Analysis")
        program = st.selectbox("Select Program", sorted(df["Program"].unique()))
        group_df = df[df["Program"] == program]
        avg_df = group_df.groupby(["Assessment Year", "Course Name"]).mean(numeric_only=True).reset_index()
        st.dataframe(avg_df)

        if not avg_df.empty:
            avg_df["Assessment Year"] = avg_df["Assessment Year"].astype(int)
            avg_df = avg_df.sort_values(["Course Name", "Assessment Year"])

            # Line Chart
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=avg_df, x="Assessment Year", y="Score", hue="Course Name", marker="o", ax=ax2)
            ax2.set_title(f"Average Scores by Course - {program}", fontsize=14)
            ax2.set_ylabel("Average Score (%)")
            ax2.set_xlabel("Assessment Year")
            ax2.legend(title="Course Name", bbox_to_anchor=(1.05, 1), loc='upper left')
            ax2.set_xticks(sorted(avg_df["Assessment Year"].unique()))
            plt.tight_layout()
            st.pyplot(fig2)

            # Heatmap
            st.subheader("🔥 Heatmap of Average Scores")
            pivoted = avg_df.pivot(index="Course Name", columns="Assessment Year", values="Score").fillna(0)

            if not pivoted.empty:
                fig_hm, ax_hm = plt.subplots(figsize=(10, len(pivoted) * 0.5))
                sns.heatmap(pivoted, annot=True, cmap="YlGnBu", fmt=".0f", linewidths=0.5, ax=ax_hm, cbar_kws={'label': 'Score'})
                ax_hm.set_title(f"Heatmap - {program}", fontsize=14)
                st.pyplot(fig_hm)
            else:
                st.warning("No data available to generate heatmap for this program.")

# --- AUTHENTICATION RESPONSES ---
elif auth_status is False:
    st.error("Incorrect username or password.")
elif auth_status is None:
    st.warning("Please enter your credentials.")
