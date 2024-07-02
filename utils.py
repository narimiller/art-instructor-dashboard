import streamlit as st

#################
# Constants
TERM_END_BUFFER = '+14 days'

#################
# Functions

# Read a specific query from the SQL file using markers
def read_query_from_file(file_path, query_name):
    with open(file_path, 'r') as file:
        in_query = False
        query_lines = []
        for line in file:
            line = line.strip()
            if line.startswith('-- START_QUERY:'):
                if line[15:].strip() == query_name:
                    in_query = True
                    continue
            if line.startswith('-- END_QUERY:'):
                if line[13:].strip() == query_name:
                    break
            if in_query:
                query_lines.append(line)
        return ' '.join(query_lines)

def load_card_css(background_color):
    custom_css = f"""
    <style>
    .custom-metric-card-wrapper {{
        padding: 4px 6px 20px 6px; /* Padding around card */
    }}
    .custom-metric-card {{
        background-color: {background_color};
        color: white; /* Text color */
        padding: 25px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Shadow */
        text-align: left; 
    }}
    .custom-title {{
        font-size: 16px;
        font-weight: normal;
        margin-bottom: 5px;
    }}
    .custom-value {{
        font-size: 28px;
        font-weight: 600; /* Medium font weight */
        margin-bottom: -2px
    }}
    .custom-subtext {{
        font-size: 14px;
        color: lightgray; /* Subtext color */
        margin-top: 0px;
    }}
    </style>
    """

    st.markdown(custom_css, unsafe_allow_html=True)

def create_metric_card(title, value, subtext=None):
    """
    Create a metric card with an optional subtext.

    Parameters:
    - title (str): The title of the metric.
    - value (str): The value of the metric.
    - subtext (str, optional): Additional subtext for the metric. Default is None.
    """
    card_html = f"""
        <div class="custom-metric-card-wrapper">
            <div class="custom-metric-card">
                <div class="custom-title">{title}</div>
                <div class="custom-value">{value}</div>
    """
    if subtext is not None:
        card_html += f'<div class="custom-subtext">{subtext}</div>'
    
    card_html += "</div></div>"

    st.markdown(card_html, unsafe_allow_html=True)