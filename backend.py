import requests
import pandas as pd
from bs4 import BeautifulSoup
from collections import deque
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.parse import urlparse, parse_qs

def fetch_sitemap_urls(sitemap_url):
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        exclude_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.css', '.js', '.pdf', '.zip']
        sitemap_urls = []
        sitemap_tags = soup.find_all('sitemap')
        if sitemap_tags:
            for sitemap in sitemap_tags:
                loc_tag = sitemap.find('loc')
                if loc_tag:
                    url = loc_tag.text.strip()
                    if not any(url.endswith(ext) for ext in exclude_extensions):
                        sitemap_urls.append(url)
        else:
            for url_tag in soup.find_all('url'):
                loc_tag = url_tag.find('loc')
                if loc_tag:
                    url = loc_tag.text.strip()
                    if not any(url.endswith(ext) for ext in exclude_extensions):
                        sitemap_urls.append(url)
        return sitemap_urls
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sitemap URLs: {e}")
        return []
    
def fetch_page_urls(sitemap_url):
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        return [url.text for url in soup.find_all('loc')]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page URLs from {sitemap_url}: {e}")
        return []
    
def extract_meta_data(page_url):
    try:
        response = requests.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string if soup.title else 'N/A'
        description_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = description_tag['content'] if description_tag and 'content' in description_tag.attrs else 'N/A'
        html_tag = soup.find('html')
        lang = html_tag.get('lang', 'N/A') if html_tag else 'N/A'
        return title, meta_description, lang
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return 'N/A', 'N/A', 'N/A'
    except Exception as e:
        print(f"Error processing the page: {e}")
        return 'N/A', 'N/A', 'N/A'
    
def extract_headers(page_url):
    response = requests.get(page_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    headers_summary = {
        'H1': [],  
        'H2': []  
    }
    headers_summary['H1'] = [h1.get_text(strip=True) for h1 in soup.find_all('h1') if h1.get_text(strip=True)]
    headers_summary['H2'] = [h2.get_text(strip=True) for h2 in soup.find_all('h2') if h2.get_text(strip=True)]
    if not headers_summary['H1']:
        headers_summary['H1'] = ["Missing"]
    if not headers_summary['H2']:
        headers_summary['H2'] = ["Missing"]
    return headers_summary

def normalize_text(text):
    return ' '.join(str(text).strip().lower().split())

def check_duplicates(headers, text_column):
    headers_df = pd.DataFrame(headers)
    headers_df['Normalized Text'] = headers_df[text_column].apply(normalize_text)
    headers_df['Duplicate Key'] = headers_df['Normalized Text'] + headers_df['Page URL']
    duplicate_counts = headers_df['Duplicate Key'].value_counts()
    headers_df['Duplicate Status'] = headers_df['Duplicate Key'].apply(
        lambda x: "Duplicate Found" if duplicate_counts[x] > 1 else "No Duplicate"
    )
    headers_df.drop(columns=['Normalized Text', 'Duplicate Key'], inplace=True)    
    return headers_df

def fetch_tag_pages(sitemap_url):
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        tag_page_urls = []
        for sitemap_tag in soup.find_all('sitemap'):
            loc_tag = sitemap_tag.find('loc')
            if loc_tag:
                nested_sitemap_url = loc_tag.text.strip()
                tag_page_urls.extend(fetch_tag_pages(nested_sitemap_url))
        for url_tag in soup.find_all('url'):
            loc_tag = url_tag.find('loc')
            if loc_tag:
                url = loc_tag.text.strip()
                if any(tag in url for tag in ['/tag/', '/product-tag/', '/category-tag/']):
                    tag_page_urls.append(url)
        if not tag_page_urls:
            print("No tag pages found in this sitemap.")
        return tag_page_urls
    except Exception as e:
        print(f"Error fetching tag pages: {e}")
        return []

def extract_images(page_url):
    response = requests.get(page_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    images = soup.find_all('img')
    images_missing_alt = []
    images_over_100kb = []
    for img in images:
        img_url = img.get('src')
        alt_text = img.get('alt', None)
        if alt_text is None or len(alt_text) == 0:
            images_missing_alt.append((page_url, img_url))
        if img_url.startswith("http"):
            try:
                img_response = requests.head(img_url)
                img_size = int(img_response.headers.get('content-length', 0))
                if img_size > 100 * 1024:
                    images_over_100kb.append((page_url, img_url, img_size))
            except requests.exceptions.RequestException:
                continue
    return images_missing_alt, images_over_100kb

def is_valid_url(url):
    invalid_extensions = (
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',  
        '.mp4', '.avi', '.mov', '.mkv',                           
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip',         
        '.rar', '.7z', '.exe'
    )
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        if 'cart' in path:
            return True
        if any(path.endswith(ext) for ext in invalid_extensions):
            return False
        query_params = parse_qs(parsed.query)
        if 'add-to-cart' in query_params or any(key == 'action' for key in query_params.keys()):
            return False
        return True
    except Exception:
        return False
    
def crawl_website(root_url):
    visited_urls = set()
    urls_to_visit = deque([normalize_url(root_url)])  
    all_urls = []
    while urls_to_visit:
        current_url = urls_to_visit.popleft()
        normalized_current_url = normalize_url(current_url)
        if normalized_current_url in visited_urls:
            continue
        try:
            response = requests.get(current_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            visited_urls.add(normalized_current_url)
            all_urls.append(normalized_current_url)
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = normalize_url(urljoin(current_url, href)) 
                if full_url.startswith(root_url) and full_url not in visited_urls:
                    urls_to_visit.append(full_url)
        except requests.exceptions.RequestException:
            continue
    return all_urls

def normalize_url(url, add_trailing_slash=False):
    parsed = urlparse(url)
    normalized_path = parsed.path.rstrip('/')
    if add_trailing_slash:
        normalized_path += '/' if not normalized_path.endswith('/') else ''
    else:
        normalized_path = normalized_path.rstrip('/')
    return urlunparse(parsed._replace(fragment='', path=normalized_path))

link_status_cache = {}

def check_link_status(link):
    normalized_link = normalize_url(link, add_trailing_slash=False)
    if normalized_link in link_status_cache:
        return link_status_cache[normalized_link]
    try:
        response = requests.get(normalized_link, allow_redirects=False, timeout=5)
        status_code = response.status_code
        redirect_url = response.headers.get('Location', '').strip()
        if status_code in [301, 302]:
            if normalize_url(redirect_url, add_trailing_slash=False) == normalized_link or \
               normalize_url(redirect_url, add_trailing_slash=True) == normalized_link:
                link_status_cache[normalized_link] = '200_ok'
                return '200_ok'
            link_status_cache[normalized_link] = f'redirect_{status_code}'
            return f'redirect_{status_code}'
        elif status_code == 200:
            link_status_cache[normalized_link] = '200_ok'
            return '200_ok'
        elif status_code == 404:
            link_status_cache[normalized_link] = '404'
            return '404'
        link_status_cache[normalized_link] = 'broken'
        return 'broken'
    except requests.exceptions.RequestException:
        link_status_cache[normalized_link] = 'broken'
        return 'broken'
    
def process_url(input_url, input_type="Website URL"):
    meta_data = []
    headers_h1 = []
    headers_h2 = []
    images_missing_alt = []
    images_over_100kb = []
    page_status_combined = [] 
    all_titles = []
    all_descriptions = []
    titles_missing = []
    descriptions_missing = []
    titles_below_30 = []
    descriptions_below_50 = []
    tag_pages = []
    meta_titles_dict = {}
    meta_descriptions_dict = {}
    processed_urls = set()  
    def convert_to_list_of_dicts(duplicate_data, page_type):
        result = []
        for meta_data, pages in duplicate_data.items():
            for page in pages:
                result.append({page_type: meta_data, "Page URL": page})
        return result
    try:
        if input_type == "Sitemap URL":
            page_urls = []
            tag_pages = fetch_tag_pages(input_url)
            sitemap_urls = fetch_sitemap_urls(input_url)
            for sitemap_url in sitemap_urls:
                page_urls.extend(fetch_page_urls(sitemap_url))
        else:
            page_urls = crawl_website(input_url)
            tag_pages = [url for url in page_urls if any(tag in url for tag in ['/tag/', '/product-tag/', '/category-tag/'])]
        page_urls = [normalize_url(url) for url in page_urls if is_valid_url(url)]
        tag_pages = [normalize_url(url) for url in tag_pages if is_valid_url(url)]
        combined_urls = list(set(page_urls + tag_pages))
        for page_url in combined_urls:
            if page_url in processed_urls:
                continue  
            page_status = check_link_status(page_url)
            processed_urls.add(page_url) 
            page_status_combined.append({'Page URL': page_url, 'Status': page_status})
            if page_status in ['404', 'broken', 'redirect_301', 'redirect_302']:
                continue
            title, description, lang = extract_meta_data(page_url)
            if not title or title.strip() == '' or title.strip() == 'N/A':
                title = 'N/A'
                titles_missing.append({'Page URL': page_url, 'Meta Title': title})
            else:
                if len(title) < 30:
                    titles_below_30.append({'Page URL': page_url, 'Meta Title': title})
                meta_titles_dict.setdefault(title, []).append(page_url)
            if not description or description.strip() == '' or description.strip() == 'N/A':
                description = 'N/A'
                descriptions_missing.append({'Page URL': page_url, 'Meta Description': description})
            else:
                if len(description) < 50:
                    descriptions_below_50.append({'Page URL': page_url, 'Meta Description': description})
                meta_descriptions_dict.setdefault(description, []).append(page_url)
            if title != 'N/A':
                all_titles.append({'Page URL': page_url, 'Meta Title': title})
            if description != 'N/A':
                all_descriptions.append({'Page URL': page_url, 'Meta Description': description})
            meta_data.append({
                'Input URL': input_url,
                'Page URL': page_url,
                'Meta Title': title,
                'Meta Description': description,
                'Language': lang
            })
            headers = extract_headers(page_url)
            headers_h1.extend([{'Page URL': page_url, 'H1 Text': h} for h in headers.get('H1', ["Missing"])])
            headers_h2.extend([{'Page URL': page_url, 'H2 Text': h} for h in headers.get('H2', ["Missing"])])
            images_alt_missing, images_over_100kb_list = extract_images(page_url)
            images_missing_alt.extend(images_alt_missing)
            images_over_100kb.extend(images_over_100kb_list)
    except Exception as e:
        return {"error": str(e)}
    duplicate_titles = {title: urls for title, urls in meta_titles_dict.items() if len(urls) > 1 and title != 'N/A'}
    duplicate_descriptions = {desc: urls for desc, urls in meta_descriptions_dict.items() if len(urls) > 1 and desc != 'N/A'}
    duplicate_titles_list = convert_to_list_of_dicts(duplicate_titles, "Meta Title")
    duplicate_descriptions_list = convert_to_list_of_dicts(duplicate_descriptions, "Meta Description")
    return {
        "meta_data": meta_data,
        "headers_h1": headers_h1,
        "headers_h2": headers_h2,
        "images_missing_alt": images_missing_alt,
        "images_over_100kb": images_over_100kb,
        "page_status": page_status_combined,
        "meta_titles_all": all_titles,
        "meta_titles_missing": titles_missing,
        "meta_titles_below_30": titles_below_30,
        "meta_descriptions_all": all_descriptions,
        "meta_descriptions_missing": descriptions_missing,
        "meta_descriptions_below_50": descriptions_below_50,
        "tag_pages": tag_pages,
        "meta_titles_duplicate": duplicate_titles_list,
        "meta_descriptions_duplicate": duplicate_descriptions_list
    }