import streamlit as st
from streamlit_option_menu import option_menu

import cohorts, courses, students, uploads

st.set_page_config(
    page_title="Instructor Dashboard",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="auto",
)

with st.sidebar:
    selected = option_menu(
        menu_title='Instructor Dash',
        menu_icon='activity',
        options=['Courses', 'Cohorts', 'Students'],
         icons=['star', 'bullseye', 'person','image','play-circle'],
        default_index=0,
        styles={
            "container": {"padding": "5!important"},
            #"icon": {"color": "#fafafa", "font-size": "23px"}, 
            #"nav-link": {"color":"#fafafa","font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": ""},
            "nav-link-selected": {"background-color": "#005EC2"}
            }
    )

if selected == 'Courses':
    courses.app()
if selected == 'Cohorts':
    cohorts.app()
if selected == 'Students':
    students.app()


