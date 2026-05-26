import argparse
import re
import sys
from urllib.parse import urlparse

import markdownify
import requests
from bs4 import BeautifulSoup


class GoogleCloudDocsConverter(markdownify.MarkdownConverter):
    def convert_pre(self, el, text, parent_tags):
        # Find syntax language if present
        # In Google Cloud docs, it's often on devsite-code or pre
        syntax = el.get('syntax', '')
        if not syntax and el.parent:
            syntax = el.parent.get('syntax', '')
            if not syntax and el.parent.parent:
                syntax = el.parent.parent.get('syntax', '')
        
        if not syntax:
            # Check class names like 'lang-py' or similar
            classes = el.get('class', [])
            for c in classes:
                if c.startswith('lang-'):
                    syntax = c.split('-')[1]
                    break
        
        # Clean up syntax string
        syntax = syntax.lower().strip() if syntax else ''
        if syntax == 'bash':
            syntax = 'sh'
        
        # Preformatted text often contains extra leading/trailing whitespace
        cleaned_text = text.strip()
        return f'\n```{syntax}\n{cleaned_text}\n```\n'

    def convert_a(self, el, text, parent_tags):
        href = el.get('href', '')
        # Convert relative URLs to absolute Google Cloud docs URLs
        if href.startswith('/') and not href.startswith('//'):
            href = f'https://cloud.google.com{href}'
        
        # Avoid empty link text or redundant links
        if not text:
            text = href
        
        title = el.get('title', '')
        title_part = f' "{title}"' if title else ''
        return f'[{text}]({href}{title_part})'

    def convert_img(self, el, text, parent_tags):
        src = el.get('src', '')
        if src.startswith('/') and not src.startswith('//'):
            src = f'https://cloud.google.com{src}'
        
        alt = el.get('alt', '') or ''
        return f'![{alt}]({src})'

def convert_url_to_markdown(url, output_path):
    print(f"Fetching URL: {url} ...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    print("Parsing HTML with BeautifulSoup...")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Locate the main article body
    # Standard Google Cloud Docs uses devsite-article-body
    article_body = soup.select_one('div.devsite-article-body')
    if not article_body:
        # Fallback to general main or article tags
        article_body = soup.select_one('article') or soup.select_one('main')
    
    if not article_body:
        print("Error: Could not find article body in HTML.")
        sys.exit(1)
        
    # Decompose unwanted elements (surveys, custom buttons, feedback widgets, etc.)
    unwanted_selectors = [
        'devsite-hats-survey',
        'button.devsite-button-copy',
        '.devsite-content-footer',
        '.devsite-article-meta',
        '.devsite-feedback',
        'div.devsite-rating-stars'
    ]
    for selector in unwanted_selectors:
        for item in article_body.select(selector):
            item.decompose()
            
    # Normalize relative links and images within the article body directly
    for a in article_body.find_all('a'):
        href = a.get('href', '')
        if href.startswith('/') and not href.startswith('//'):
            a['href'] = f'https://cloud.google.com{href}'
            
    for img in article_body.find_all('img'):
        src = img.get('src', '')
        if src.startswith('/') and not src.startswith('//'):
            img['src'] = f'https://cloud.google.com{src}'

    print("Converting HTML to Markdown...")
    converter = GoogleCloudDocsConverter(
        heading_style=markdownify.ATX,
        bullets='-',
        strip=['script', 'style']
    )
    
    markdown_content = converter.convert(str(article_body))
    
    # Post-processing: clean up excessive blank lines and formatting artifacts
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
    
    # Prepend a metadata header to make it extremely premium
    title_el = soup.find('h1')
    if title_el:
        # Clean up nested tooltips or actions inside h1
        for tag in title_el.find_all(['devsite-feature-tooltip', 'devsite-actions', 'button']):
            tag.decompose()
        title_text = title_el.get_text().strip()
    else:
        title_text = "Vertex AI SDK Deprecations"
    
    
    metadata = f"""# {title_text}

> **Source**: [{url}]({url})
> **Converted on**: 2026-05-22

---

"""
    
    # If the markdown content already starts with the H1, we remove it to avoid duplicates
    first_heading_match = re.match(r'^\s*#\s+(.+)\n', markdown_content)
    if first_heading_match:
        markdown_content = markdown_content[first_heading_match.end():].lstrip()
        
    final_output = metadata + markdown_content
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_output)
        
    print(f"Successfully converted and saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Google Cloud doc page to Markdown.")
    parser.add_argument("url", help="The URL of the Google Cloud documentation page to convert.")
    parser.add_argument("-o", "--output", help="The output file path. Defaults to <last-part-of-url>.md")
    
    args = parser.parse_args()
    
    url = args.url
    if args.output:
        output_path = args.output
    else:
        parsed_url = urlparse(url)
        path_part = parsed_url.path.rstrip('/')
        if path_part:
            last_part = path_part.split('/')[-1]
        else:
            last_part = parsed_url.netloc or "output"
        output_path = f"{last_part}.md"
        
    convert_url_to_markdown(url, output_path)
