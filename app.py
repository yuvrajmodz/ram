from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time
import urllib.parse
import os

app = Flask(__name__)

def scrape_proxy_status(proxy):
    with sync_playwright() as p:
        # Launch a headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the proxy checker page
        page.goto("https://proxyscrape.com/online-proxy-checker")

        # Fill the proxy input (normal form, not encoded)
        page.fill('textarea[placeholder="0.0.0.0:1234\\n127.0.0.1:3434\\nlocalhost:8080"]', proxy)

        # Click the "Check proxies" button
        page.click('button.btn-style-lg')

        # Wait for a few seconds to let the results load
        time.sleep(5)

        # Get the page content after the form submission
        content = page.content()

        # Close the browser
        browser.close()

        # Use BeautifulSoup to parse the HTML and extract the required data
        soup = BeautifulSoup(content, 'html.parser')
        table_rows = soup.find_all('tr', class_='table-success')

        # Extract relevant data from the table rows
        proxies_data = []
        for row in table_rows:
            columns = row.find_all('td')
            if len(columns) >= 5:
                status = columns[0].find('span').text
                ip = columns[1].text
                port = columns[2].text
                country_img = columns[3].find('img')['src']
                protocol = columns[4].text
                proxies_data.append({
                    'status': status,
                    'ip': ip,
                    'port': port,
                    'country_img': country_img,
                    'protocol': protocol
                })

        return proxies_data

@app.route('/check', methods=['GET'])
def check_proxy():
    # Get the proxy from the query parameter
    proxy = request.args.get('proxies')

    # Decode the proxy if it's URL-encoded
    decoded_proxy = urllib.parse.unquote(proxy)

    # Scrape the proxy checker page for this proxy
    try:
        proxy_status = scrape_proxy_status(decoded_proxy)
        return jsonify(proxy_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5019))
    app.run(host='0.0.0.0', port=port, debug=True)