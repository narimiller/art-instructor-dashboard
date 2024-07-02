import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit_shadcn_ui as ui
import plotly.io as pio
from datetime import datetime
from datetime import timedelta
from streamlit import session_state as ss
from utils import load_card_css, create_metric_card, read_query_from_file, TERM_END_BUFFER
import os
import glob
from PIL import Image

def app():

    #######################
    # Queries

    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    query_file_path = 'queries.sql'
    
    # posts with image count
    q = read_query_from_file(query_file_path, 'posts_images')
    images = pd.read_sql_query(q, conn, params=(TERM_END_BUFFER,))

    # all assignment posts, including "between terms" category
    q = read_query_from_file(query_file_path, 'posts_all')
    posts = pd.read_sql_query(q, conn, params=(TERM_END_BUFFER, TERM_END_BUFFER))

    conn.close()
    
    #######################
    # Theme

    primaryColor = st.get_option('theme.primaryColor')
    backgroundColor = st.get_option('theme.backgroundColor')
    secondaryBackgroundColor = st.get_option('theme.secondaryBackgroundColor')
    textColor = st.get_option('theme.textColor')

    #######################
    # Plots

    # takes in df containing one user and analysis type
    def make_heatmap(df, x_name):
        filtered_df = df.copy()
        if x_name == 'module':
            filtered_df = filtered_df.groupby(['cohort_id', 'module']).sum().reset_index()
        
        custom_colorscale = [
                [0.0, backgroundColor],
                [0.4, '#1499FF'],
                [1.0, '#B8E0FF']
        ]
        
        # Reshape df for heatmap
        heatmap_data = filtered_df.pivot_table(index='cohort_id', columns=x_name, values='num_posts')
        heatmap_data.fillna(0, inplace=True)

        fig = px.imshow(heatmap_data, aspect='auto', color_continuous_scale=custom_colorscale, zmin=0)
        
        fig.update_traces(
            hovertemplate=f'{x_name.capitalize()}: %{{x}}<br>Cohort ID: %{{y}}<br>Posts: %{{z}}<extra></extra>',
            xgap=3,
            ygap=3,
        )
        
        tickangle = 45 if x_name == 'assignment' else 0
        num_terms = filtered_df['cohort_id'].nunique()
        height = 300 + (num_terms - 5) * 50 if num_terms > 5 else 200 + num_terms * 20

        fig.update_layout(
            xaxis_title=x_name.capitalize(),
            yaxis_title="Cohort ID",
            yaxis_nticks=len(filtered_df),
            xaxis_nticks=len(filtered_df[x_name].unique()),
            xaxis=dict(
                tickmode='linear',
                tick0=1,
                dtick=1,
                tickangle=tickangle,
            ),
            height=height,
            xaxis_showgrid=False,
            yaxis_showgrid=False,
            margin=dict(t=10)
        )

        return fig
    
    #######################
    # Main Panel

    st.title("Students")
    
    # Username filter
    username_options = [""] + sorted(posts['username'].unique(), reverse=False)
    selected_username = st.selectbox('Choose Username', username_options)

    filtered = pd.DataFrame()
    if selected_username:
        filtered = posts[posts['username'] == selected_username]
        st.markdown(f'## {selected_username}')

        # Calculate completion metrics
        total_modules = filtered['module'].nunique()
        modules_completed = filtered[filtered['num_posts'] > 0]['module'].nunique()
        completion_percentage = (modules_completed / total_modules) * 100

        # Metric cards
        st.markdown(f"#### Overall")
        stats = st.columns(4)  
        load_card_css(secondaryBackgroundColor)
        
        with stats[0]:
            create_metric_card(title='Terms', 
                           value=filtered['cohort_id'].nunique()
                           ) 
        with stats[1]:
            create_metric_card(title='Total Posts', 
                           value=filtered['num_posts'].sum()
                           ) 
        with stats[2]:
            create_metric_card(title='Total Images', 
                           value=images[images['username']==selected_username]['num_images'].sum()
                           ) 
        with stats[3]:
            create_metric_card(title='Completion', 
                           value=f"{completion_percentage:.0f}%"
                            )

        # Heatmap
        st.markdown('#### Post Activity')
        heatmap_tabs = ui.tabs(
            options=['Modules', 'Assignments'],
            default_value='Modules',
            key="heatmap_tabs",
            )
        if heatmap_tabs == 'Modules':
            x_val = 'module'
        else:
            x_val = 'assignment'
        st.plotly_chart(make_heatmap(filtered, x_val))

    else:
        st.warning("Please select a username.")

    #######################
    # Display Images
    
    def find_images(username, directory):
        pattern = f"{directory}/*{username}*.jpg"
        images = sorted(glob.glob(pattern))
        return images

    # Directory containing images
    DIR = "../data_processing/data/source/images/TSC-raw"

    # Search and display images if a username is selected
    if selected_username:
        image_paths = find_images(selected_username, DIR)
        if image_paths:
            st.markdown(f"#### Images for {selected_username}")
            
            # Radio buttons to control the number of columns
            size_option = st.radio("", ["Small", "Medium", "Large"], index=1, horizontal=True, label_visibility="collapsed")
            
            st.markdown("<style>div[role='radiogroup']{margin-bottom: 0px;}</style>", unsafe_allow_html=True)
            
            if size_option == "Small":
                cols_count = 6
                show_captions = False
            elif size_option == "Medium":
                cols_count = 3
                show_captions = True
            elif size_option == "Large":
                cols_count = 1
                show_captions = True
            
            # Create rows with the selected number of columns
            rows = [st.columns(cols_count) for _ in range((len(image_paths) // cols_count) + 1)]
            
            for i, image_path in enumerate(image_paths):
                image = Image.open(image_path)
                # Display images in the calculated columns
                if show_captions:
                    rows[i // cols_count][i % cols_count].image(image, caption=os.path.basename(image_path), use_column_width=True)
                else:
                    rows[i // cols_count][i % cols_count].image(image, use_column_width=True)
        else:
            st.info(f"No images found for {selected_username}.")

if __name__ == "__main__":
    app()