import pandas as pd
import streamlit as st
from io import BytesIO
import base64
import re
from backend import process_url
from urllib.robotparser import RobotFileParser
from backend import check_duplicates
from urllib.parse import urlparse
import time


logo_path = "images/Involvz-Logo.png"
st.set_page_config(page_title="SEO Web Crawler Data", page_icon="🕸️", layout="wide")
def add_multiple_status_based_on_url(df, section_name):
    url_counts = df['Page URL'].value_counts()
    df[f'{section_name} Multiple'] = df['Page URL'].map(lambda url: 'Multiple' if url_counts[url] > 1 else 'Not Multiple')
    return df

def is_crawl_allowed(url, user_agent="*"):
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    robot_parser = RobotFileParser()
    robot_parser.set_url(robots_url)
    robot_parser.read()
    return robot_parser.can_fetch(user_agent, url)

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_base64 = get_base64_image(logo_path)

st.markdown(f"""
    <style>
        .st-emotion-cache-1r4qj8v {{
            background: rgb(212 228 233);
        }}

        .toolbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 20px;
            margin: 20px;
        }}
        .toolbar .links {{
            display: flex;
            justify-content: center;
            margin-left: -60px;
        }}
        .toolbar a {{
            margin: 0 15px;
            padding: 10px 15px;
            font-weight: bold;
            color: black;
            text-decoration: none;
            transition: background-color 0.3s;
        }}
        .toolbar a:hover {{
            background-color: rgba(236, 0, 140, 0.1);
        }}
    </style>
    <div class="toolbar">
        <img src="data:image/png;base64,{logo_base64}" alt="Logo" style="height:40px; margin-right: 20px;">
        <div class="links">
            <a href="# seo-analysis-tool">Home</a>
            <a href="#features">Features</a>
            <a href="#clients-that-have-trusted-us">Clients</a>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>SEO Analysis Tool</h1>", unsafe_allow_html=True)

selection = st.radio("Choose Input Type", ["Sitemap URL", "Website URL"], horizontal=True)

with st.form(key="input_form"):
    if selection == "Sitemap URL":
        st.subheader("Enter your Sitemap URL")
        url = st.text_input("Sitemap URL", placeholder="https://example.com/sitemap.xml")
    else:
        st.subheader("Enter your Website URL")
        url = st.text_input("Website URL", placeholder="https://example.com")
    submit_button = st.form_submit_button(label="Analyze Now")
    st.markdown("""
    <style>
        .stFormSubmitButton {
            background-color: #2A4880; 
            color: black; 
            font-size: 16px; 
            font-weight: bold; 
            padding: 12px 20px;
            border-radius: 8px; 
            border: none; 
            cursor: pointer; 
            transition: background-color 0.3s ease, transform 0.3s ease; 
        }
        .stFormSubmitButton:hover {
            background-color: #0056B3; 
            transform: scale(1.05); 
        }
        .stFormSubmitButton:focus {
            outline: none; 
            box-shadow: 0 0 10px rgba(0, 86, 179, 0.5);
        }
        .stFormSubmitButton:active {
            background-color: #0056B3; 
            transform: scale(1); 
        }
    </style>
    """, unsafe_allow_html=True)

empty_meta_titles_df = pd.DataFrame(columns=["Page URL", "Meta Title"])
empty_meta_descriptions_df = pd.DataFrame(columns=["Page URL", "Meta Description"])
empty_headers_df = pd.DataFrame(columns=["Page URL", "H1", "H2", "Header Issues"])
empty_images_df = pd.DataFrame(columns=["Page URL", "Image URL"])
empty_broken_links_df = pd.DataFrame(columns=["Page URL", "Broken Link"])

if submit_button:
    if selection == "Sitemap URL":
        if not re.match(r"https?://.*\.(xml)$", url.strip()):
            st.error("Please enter a valid Sitemap URL ending in '.xml'.")
        else:
                if is_crawl_allowed(url):  
                    placeholder = st.empty() 
                    placeholder.success("Crawling is allowed. Processing the website, please wait...")
                    time.sleep(3)  
                    placeholder.empty()  
                    with st.spinner('Crawling the website, please wait...'):
                        data = process_url(url, input_type=selection)
                        st.session_state['data'] = data
                        st.success("Sitemap analysis complete!")
                else:
                    st.error("Crawling is disallowed for this Sitemap URL. Check the site's robots.txt.")
    else:  
        if not re.match(r"https?://.*", url.strip()):
            st.error("Please enter a valid Website URL starting with 'http://' or 'https://'.")
        else:
                if is_crawl_allowed(url):  
                    placeholder = st.empty() 
                    placeholder.success("Crawling is allowed. Processing the website, please wait...")
                    time.sleep(3) 
                    placeholder.empty()  
                    with st.spinner('Crawling the website, please wait...'):
                        data = process_url(url, input_type=selection)
                        st.session_state['data'] = data
                        st.success("Website analysis complete!")
                else:
                    st.error("Crawling is disallowed for this Website URL. Check the site's robots.txt.")
      
if 'data' in st.session_state and st.session_state['data']:
    data = st.session_state['data']
    st.subheader("SEO Data Overview")

def get_box_type(count):
    if count < 10:
        return 'success'
    elif 10 <= count < 30:
        return 'warning'
    else:
        return 'danger'

if st.session_state.get('data'):
    data = st.session_state['data']

    missing_titles_count = len(data.get("meta_titles_missing", []))
    duplicate_titles_count = len(data.get("meta_titles_duplicate", []))
    images_missing_alt_count = len(data.get("images_missing_alt", []))
    meta_description_count = len(data.get("meta_descriptions_all", []))
    meta_descriptions_missing_count = len(data.get("meta_descriptions_missing", []))

    st.markdown("""
    <style>
        @media (min-width: 576px) {
       .st-emotion-cache-1jicfl2 {
            padding-left: 5rem;
            padding-right: 5rem;
            background: whitesmoke;
    }
}
        .result-box {
            padding: 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            max-width: 30%;
            float: left;
            margin: 20px;
            height: 250px;
            text-align: center;
            align-content: center;
            font-size: 25px;
            padding: 50px;        
            background: #2A4880;        
            background: #ffffff;
            text-decoration: none;
        }
        .result-box.success {
            background-color: #2A4880;
        }
        .result-box.warning {
            background-color: #2A4880;
        }
        .result-box.danger {
            background-color: #2A4880;
        }
        .st-emotion-cache-1rsyhoq a {
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)
    if 'expander_open' not in st.session_state:
        st.session_state.expander_open = True
    if 'expander_open_duplicate' not in st.session_state:
        st.session_state.expander_open_duplicate = True
    if 'expander_open_images_missing_alt' not in st.session_state:
        st.session_state.expander_open_images_missing_alt = True
    if 'expander_open_meta_descriptions_all' not in st.session_state:
        st.session_state.expander_open_meta_descriptions_all = True 

    query_params = st.query_params
    if 'open_meta_titles' in query_params:
        st.session_state.expander_open = True
    if 'open_duplicate_meta_titles' in query_params:
       st.session_state.expander_open_duplicate = True
    if 'open_images_missing_alt' in query_params:
        st.session_state.expander_open_images_missing_alt = True
    if 'open_meta_descriptions' in query_params:
        st.session_state.expander_open_meta_descriptions_all = True

    st.markdown(f"""
        <a href="#missing-meta-titles" class="result-box success" onclick="window.location.hash = 'missing-meta-titles';">
            <div>
                {missing_titles_count} Missing Meta Titles
            </div>
        </a>
        <a href="#duplicate-meta-titles" class="result-box {get_box_type(duplicate_titles_count)}" onclick="window.location.hash = 'duplicate-meta-titles';">
            <div>
                {duplicate_titles_count} Duplicate Meta Titles
            </div>
        </a>
        <a href="#images-missing-alt" class="result-box {get_box_type(images_missing_alt_count)}" onclick="window.location.hash = 'images-missing-alt';">
            <div>
                {images_missing_alt_count} Images Missing Alt Text
            </div>
        </a>
        <a href="#meta-descriptions" class="result-box {get_box_type(meta_description_count)}" onclick="window.location.hash = 'meta-descriptions';">
            <div>
                {meta_description_count} Meta Descriptions
            </div>
        </a>
    """, unsafe_allow_html=True)
   
   
    st.markdown("""
    <style>
        .st-expanderHeader {
            word-break: break-word;
            margin-bottom: 0px;
            font-size: 32px;
            font-weight: 600;
            font-family: monospace;
            color: #333;  
        }
        
        .st-expanderHeader div {
            padding: 10px;
        }
        
        .st-expanderHeader[aria-expanded="true"] {
            background-color: #f0f0f0;  
            color: #0056b3;  
        }

        .st-expander {
            background-color: #f7f7f7;  
            border-radius: 8px;
            margin-bottom: 10px;
        }
                
        .st-emotion-cache-jkfxgf p {
            word-break: break-word;
            margin-bottom: 0px;
            font-size: 32px;
            font-weight: 600;
            font-family: monospace;
        }

        .st-expanderHeader .icon {
            color: #007BFF;
        }
    </style>
""", unsafe_allow_html=True)


    if data.get("meta_titles_all"):
        with st.expander("Meta Titles - All", expanded=True):
            st.dataframe(pd.DataFrame(data["meta_titles_all"], columns=["Page URL", "Meta Title"]))

    if data.get("meta_titles_below_30"):
        with st.expander("Meta Titles Below 30 Characters", expanded=True):
            st.dataframe(pd.DataFrame(data["meta_titles_below_30"], columns=["Page URL", "Meta Title"]))
    else:
        with st.expander("Meta Titles Below 30 Characters", expanded=True):
            st.markdown("No meta titles below 30 characters found.")
            st.dataframe(empty_meta_titles_df)
    
    if data.get("meta_titles_missing") and len(data["meta_titles_missing"]) > 0:
        with st.expander("Meta Titles Missing", expanded=st.session_state.expander_open):
            st.markdown('<a id="missing-meta-titles"></a>', unsafe_allow_html=True)  
            st.dataframe(pd.DataFrame(data["meta_titles_missing"], columns=["Page URL", "Meta Title"]))
    else:
        with st.expander("Meta Titles Missing", expanded=st.session_state.expander_open):
            st.markdown('<a id="missing-meta-titles"></a>', unsafe_allow_html=True) 
            st.markdown("No missing meta titles found.")
            st.dataframe(pd.DataFrame([], columns=["Page URL", "Meta Title"]))

    if data.get("meta_titles_duplicate") and len(data["meta_titles_duplicate"]) > 0:
        with st.expander("Meta Titles Duplicate", expanded=st.session_state.expander_open_duplicate):
            st.markdown('<a id="duplicate-meta-titles"></a>', unsafe_allow_html=True)  
            st.dataframe(pd.DataFrame(data["meta_titles_duplicate"], columns=["Page URL", "Meta Title"]))
    else:
        with st.expander("Meta Titles Duplicate", expanded=st.session_state.expander_open_duplicate):
            st.markdown('<a id="duplicate-meta-titles"></a>', unsafe_allow_html=True)  
            st.markdown("No duplicate meta titles found.")
            st.dataframe(pd.DataFrame([], columns=["Page URL", "Meta Title"]))

    if data.get("meta_descriptions_all"):
        with st.expander("Meta Descriptions - All", expanded=st.session_state.expander_open_meta_descriptions_all):
            st.markdown('<a id="meta-descriptions"></a>', unsafe_allow_html=True)  
            st.dataframe(pd.DataFrame(data["meta_descriptions_all"], columns=["Page URL", "Meta Description"]))

    if data.get("meta_descriptions_below_50") and len(data["meta_descriptions_below_50"]) > 0:
        with st.expander("Meta Descriptions Below 50 Characters", expanded=True):
            st.dataframe(pd.DataFrame(data["meta_descriptions_below_50"], columns=["Page URL", "Meta Description"]))
    else:
        with st.expander("Meta Descriptions Below 50 Characters", expanded=True):
            st.markdown("No meta descriptions below 50 characters found.")
            st.dataframe(empty_meta_descriptions_df)

    if data.get("meta_descriptions_missing") and len(data["meta_descriptions_missing"]) > 0:
        with st.expander("Meta Descriptions Missing", expanded=True):
            st.dataframe(pd.DataFrame(data["meta_descriptions_missing"], columns=["Page URL", "Meta Description"]))
    else:
        with st.expander("Meta Descriptions Missing", expanded=True):
            st.markdown("No missing meta descriptions found.")
            st.dataframe(empty_meta_descriptions_df)

    if data.get("meta_descriptions_duplicate") and len(data["meta_descriptions_duplicate"]) > 0:
        with st.expander("Meta Descriptions Duplicate", expanded=True):
            st.dataframe(pd.DataFrame(data["meta_descriptions_duplicate"], columns=["Page URL", "Meta Description"]))
    else:
        with st.expander("Meta Descriptions Duplicate", expanded=True):
            st.markdown("No duplicate meta descriptions found.")
            st.dataframe(empty_meta_descriptions_df)

    if data.get("headers_h1") and len(data["headers_h1"]) > 0:
        h1_headers_df = check_duplicates(data["headers_h1"], text_column="H1 Text")
        h1_headers_df = add_multiple_status_based_on_url(h1_headers_df, section_name="H1")
        with st.expander("H1 Headers", expanded=True):
            st.dataframe(h1_headers_df)
    else:
        with st.expander("H1 Headers", expanded=True):
            st.markdown("No H1 headers found.")
            st.dataframe(pd.DataFrame(columns=["Page URL", "H1 Text", "H1 Content", "Duplicate Status", "H1 Multiple"]))

    if data.get("headers_h2") and len(data["headers_h2"]) > 0:
        h2_headers_df = check_duplicates(data["headers_h2"], text_column="H2 Text")
        h2_headers_df = add_multiple_status_based_on_url(h2_headers_df, section_name="H2")
        with st.expander("H2 Headers", expanded=True):
            st.dataframe(h2_headers_df)
    else:
        with st.expander("H2 Headers", expanded=True):
            st.markdown("No H2 headers found.")
            st.dataframe(pd.DataFrame(columns=["Page URL", "H2 Text", "H2 Content", "Duplicate Status", "H2 Multiple"]))

    if data.get("tag_pages") and len(data["tag_pages"]) > 0:
        tag_pages_df = pd.DataFrame(data["tag_pages"], columns=["Page URL"])
        with st.expander("Tag Pages", expanded=True):
            st.dataframe(tag_pages_df)
    else:
        with st.expander("Tag Pages", expanded=True):
            st.markdown("No tag pages found.")
            st.dataframe(pd.DataFrame(columns=["Page URL"])) 


    if data.get("images_missing_alt") and len(data["images_missing_alt"]) > 0:
        with st.expander("Images Missing Alt Text", expanded=st.session_state.expander_open_images_missing_alt):
            st.markdown('<a id="images-missing-alt"></a>', unsafe_allow_html=True)  
            st.dataframe(pd.DataFrame(data["images_missing_alt"], columns=["Page URL", "Image URL"]))
    else:
        with st.expander("Images Missing Alt Text", expanded=st.session_state.expander_open_images_missing_alt):
            st.markdown('<a id="images-missing-alt"></a>', unsafe_allow_html=True)  
            st.markdown("No images missing alt text found.")
            st.dataframe(pd.DataFrame([], columns=["Page URL", "Image URL"]))

    if data.get("images_over_100kb") and len(data["images_over_100kb"]) > 0:
        with st.expander("Images Over 100KB", expanded=True):
            st.dataframe(pd.DataFrame(data["images_over_100kb"], columns=["Page URL", "Image URL", "Image Size (bytes)"]))
    else:
        with st.expander("Images Over 100KB", expanded=True):
            st.markdown("No images over 100kb found.")
            st.dataframe(empty_images_df)
 
    
    if data.get("page_status"):
        with st.expander("Page Status List", expanded=True):
            st.dataframe(pd.DataFrame(data["page_status"], columns=["Page URL", "Status"]))
    else:
        with st.expander("Page Status List", expanded=True):
            st.markdown("No page status data found.")
            st.dataframe(pd.DataFrame(columns=["Page URL", "Status"]))


    def convert_df_to_excel(data_dict):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet_name, data in data_dict.items():
                if len(data) > 0:  
                    df = pd.DataFrame(data)
                    df.to_excel(writer, index=False, sheet_name=sheet_name)
            
        return output.getvalue()

    data_dict = {}

    if data.get("meta_titles_all"):
        data_dict["Meta Titles - All"] = data["meta_titles_all"]

    if data.get("meta_titles_below_30"):
        data_dict["Meta Titles Below 30"] = data["meta_titles_below_30"]

    if data.get("meta_titles_missing"):
        data_dict["Meta Titles Missing"] = data["meta_titles_missing"]

    if data.get("meta_titles_duplicate"):
        data_dict["Meta Titles Duplicate"] = data["meta_titles_duplicate"]

    if data.get("meta_descriptions_all"):
        data_dict["Meta Descriptions-All"] = data["meta_descriptions_all"]

    if data.get("meta_descriptions_below_50"):
        data_dict["Meta Descriptions Below 50"] = data["meta_descriptions_below_50"]

    if data.get("meta_descriptions_missing"):
        data_dict["Meta Descriptions Missing"] = data["meta_descriptions_missing"]

    if data.get("meta_descriptions_duplicate"):
        data_dict["Meta Descriptions Duplicate"] = data["meta_descriptions_duplicate"]

    if data.get("headers_h1"):
        data_dict["H1 Headers"] = data["headers_h1"]

    if data.get("headers_h2"):
        data_dict["H2 Headers"] = data["headers_h2"]

    if data.get("tag_pages"):
        data_dict["Tag Pages"] = data["tag_pages"]

    if data.get("page_status"):
        data_dict["Page status"] = data["tag_pages"]

    if data.get("images_missing_alt"):
        data_dict["Images Missing Alt Text"] = data["images_missing_alt"]

    if data.get("images_over_100kb"):
        data_dict["Images Over 100KB"] = data["images_over_100kb"]
    st.markdown("""
    <style>
        .stDownloadButton {
            background-color: #2A4880; 
            color: black; 
            font-size: 16px;
            font-weight: bold; 
            padding: 12px 20px; 
            border-radius: 8px; 
            border: none; 
            cursor: pointer; 
            transition: background-color 0.3s ease, transform 0.3s ease; 
        }

        .stDownloadButton:hover {
            background-color: #0056B3; 
            transform: scale(1.05); 
        }

        .stDownloadButton:focus {
            outline: none; 
            box-shadow: 0 0 10px rgba(0, 86, 179, 0.5);
        }

        .stDownloadButton:active {
            background-color: #0056B3; 
            transform: scale(1); 
        }
    </style>
    """, unsafe_allow_html=True)
    if data_dict:
        excel_file = convert_df_to_excel(data_dict)
        st.download_button(
            label="Download All Crawled Data as Excel",
            data=excel_file,
             file_name="seo_analysis_data.xlsx",
            mime="application/vnd.ms-excel"
        )
    else:
        st.subheader("No data available to download.")