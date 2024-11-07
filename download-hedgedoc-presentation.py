import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse

def download_resource(session, url, base_dir, level=0):
    try:
        response = session.get(url, stream=True)
        response.raise_for_status()

        # Check the content type to ensure it's not an HTML error page
        content_type = response.headers.get('Content-Type', '')
        content_is_code = content_type.split("; ")[0] in ['application/javascript', 'text/javascript', 'text/css']
        
        if 'text/html' in content_type and not url.endswith(".html"):
            print(f"!! Skipped downloading {url}: MIME type is text/html (likely a 404 page)")
            return

        parsed_url = urlparse(url)
        resource_path = os.path.join(base_dir, parsed_url.path.lstrip('/'))
        resource_dir = os.path.dirname(resource_path)
        
        os.makedirs(resource_dir, exist_ok=True)
        
        print(f'{"    "*level}Saving {parsed_url.path} to {resource_path}')
        
        with open(resource_path, 'wb') as f:
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                
                # Monkey-patch the javascript
                if resource_path.endswith('slide-pack.9fe42901cee029fba75d.js'):
                    chunk_str = chunk.decode('utf-8')
                    chunk_str = chunk_str.replace('src:serverurl+"/build/', 'src:"build/')
                    chunk = chunk_str.encode('utf-8')
                    
                content += chunk
                f.write(chunk)

        # If the downloaded file is JavaScript or CSS, check for more URLs
        if content_is_code:
            content_str = content.decode('utf-8')
            matches = re.findall(r'https://pad\.gwdg\.de/[^\'"\s\)\]]+', content_str)
            matches += ['https://pad.gwdg.de/' + p for p in re.findall(r'/(build|css|js)/[^\'"\s\)\]]+', content_str)]
            for match in matches:
                if not match.endswith("/"):
                    download_resource(session, match, base_dir, level+1)
                
    except Exception as e:
        print(f"{"    "*level}Failed to download {url}: {e}")

def remove_csp(soup):
    for meta in soup.find_all("meta"):
        if 'http-equiv' in meta.attrs and meta.attrs['http-equiv'] == 'Content-Security-Policy':
            meta.decompose()

def replace_and_download_resources(session, soup, base_url, base_dir):
    for tag in soup.find_all(['img', 'link', 'script']):
        if tag.name == 'img' and tag.get('src'):
            resource_url = urljoin(base_url, tag['src'])
            download_resource(session, resource_url, base_dir)
        elif tag.name == 'link' and tag.get('href'):
            resource_url = urljoin(base_url, tag['href'])
            download_resource(session, resource_url, base_dir)
        elif tag.name == 'script' and tag.get('src'):
            resource_url = urljoin(base_url, tag['src'])
            download_resource(session, resource_url, base_dir)

    # Handle dynamically generated URLs in script content
    for script in soup.find_all('script'):
        if script.string:
            updated_script = script.string
            matches = re.findall(r'https://pad\.gwdg\.de/([^\'"\s]+)', updated_script)
            for match in matches:
                resource_url = urljoin(base_url, match)
                download_resource(session, resource_url, base_dir)
                updated_script = updated_script.replace(resource_url, match)
            script.string.replace_with(updated_script)

def download_uploads_resources(session, html_str, base_dir):
    matches = re.findall(r'https://pad\.gwdg\.de/uploads/[^\s\'\"\)\]\&>\/]+', html_str)
    for match in matches:
        resource_url = match
        download_resource(session, resource_url, base_dir)

def download_additional_resources(session, base_url, base_dir, additional_paths):
    for path in additional_paths:
        resource_url = urljoin(base_url, path)
        download_resource(session, resource_url, base_dir)

def download_html_and_resources(slide_id, output_html, base_dir, additional_paths):
    base_url = "https://pad.gwdg.de"
    page_url = f"{base_url}/p/{slide_id}"
    
    session = requests.Session()
    response = session.get(page_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    remove_csp(soup)  # Remove CSP settings

    # Replace occurrences of the base URL with the local paths and download resources
    replace_and_download_resources(session, soup, base_url, base_dir)
    
    # Convert the soup object to string to find and download uploads resources
    html_str = str(soup)
    download_uploads_resources(session, html_str, base_dir)
    
    # Download additional specified resources
    download_additional_resources(session, base_url, base_dir, additional_paths)
    
    # Convert all occurrences of the base URL to local paths
    html_str = html_str.replace(base_url + '/', './')
    
    # Ensure the base directory exists
    os.makedirs(base_dir, exist_ok=True)

    # Save the modified HTML
    with open(os.path.join(base_dir, output_html), 'w', encoding='utf-8') as f:
        f.write(html_str)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and save HTML and resources from pad.gwdg.de")
    parser.add_argument('-i', '--id', required=True, help="The slide ID from pad.gwdg.de")
    parser.add_argument('-d', '--dir', required=True, help="The directory where the resources will be saved")

    args = parser.parse_args()

    slide_id = args.id
    base_dir = args.dir
    output_html = "index.html"
    # this is a manual collection of resources that were not discovered by the script, probably incomplete
    additional_paths = [
        "build/85934a8a31bd9b8b75e68eeb57b6859810055d48742953766c4a5c2b5a0d5266.woff",
        "build/8810ba3440bf482ced33d2f74b7803bba711f689d8e4caa7da5c6ae6844a1b49.woff2",
        "build/006708d6691753cfc46eec2dae88fbdafa22823a89194149d9f223050dc78998.woff",
        "build/4f319287827e35f841069eb471c092eccf97d2f7830aa4d8bd7301ded418bf49.ttf",
        "build/ae93165204442cdb2d226a4fb7a64b05ab3902cb223fff920a0ec86393e1a54e.woff",
        "build/MathJax/jax/input/TeX/config.js?V=2.7.9",
        "build/MathJax/jax/input/MathML/config.js?V=2.7.9",
        "build/MathJax/jax/output/HTML-CSS/config.js?V=2.7.9",
        "build/MathJax/jax/output/NativeMML/config.js?V=2.7.9",
        "build/MathJax/jax/output/PreviewHTML/config.js?V=2.7.9", 
        "build/MathJax/extensions/tex2jax.js?V=2.7.9",
        "build/MathJax/extensions/mml2jax.js?V=2.7.9",
        "build/MathJax/extensions/MathEvents.js?V=2.7.9",
        "build/MathJax/extensions/MathZoom.js?V=2.7.9",
        "build/MathJax/extensions/MathMenu.js?V=2.7.9",
        "build/MathJax/extensions/toMathML.js?V=2.7.9",
        "build/MathJax/extensions/TeX/noErrors.js?V=2.7.9",
        "build/MathJax/extensions/TeX/noUndefined.js?V=2.7.9",
        "build/MathJax/extensions/TeX/AMSmath.js?V=2.7.9",
        "build/MathJax/extensions/TeX/AMSsymbols.js?V=2.7.9",
        "build/MathJax/extensions/fast-preview.js?V=2.7.9",
        "build/MathJax/extensions/AssistiveMML.js?V=2.7.9",
        "build/MathJax/extensions/a11y/accessibility-menu.js?V=2.7.9",
        "build/MathJax/extensions/Safe.js?V=2.7.9",
        "build/29.5f5bdb9120d6b9c39930.js",
        "build/27.fbb6b5bbda6765f0a1f1.js",
        "build/slide-pack.2622cb29189cb5164611.js",
        "build/24.2fb0d01138de2df6de0a.css",
        "build/slide-styles.f28b3cbe43b1ce05a8b8.css",
        "build/slide.3a42b21a3dd6674f6952.css",
        "build/reveal.js/plugin/notes/notes.js",
        "build/reveal.js/css/theme/white.css",
        "build/reveal.js/lib/font/source-sans-pro/source-sans-pro.css",
        "build/reveal.js/css/print/paper.css",
        "build/reveal.js/lib/font/source-sans-pro/source-sans-pro-regular.ttf",
        "build/reveal.js/lib/font/source-sans-pro/source-sans-pro-regular.woff"
    ]
    download_html_and_resources(slide_id, output_html, base_dir, additional_paths)
