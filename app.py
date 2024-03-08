import csv
import requests
import re
import time
import concurrent.futures
from bs4 import BeautifulSoup
from algoliasearch.search_client import SearchClient

# Regular expressions for matching phone numbers and Facebook profile links.
phone_regex = r'\(\d{3}\)\s?\d{3}[-\s]?\d{4}|\d{3}-\d{3}-\d{4}|\d{3}\.\d{3}\.\d{4}'
facebook_regex = r'https?://www\.facebook\.com/[^\s"]+'

# A string of state abbreviations used in the regular expression to match addresses.
states = "AL|AK|AZ|AR|AS|CA|CO|CT|DE|D.C.|FL|GA|GU|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|MP|OH|OK|OR|PA|PR|RI|SC|SD|TN|TX|TT|UT|VT|VA|VI|WA|WV|WI|WY"
state_zip_regex = fr'(.{{1,36}})?\b({states})\s(\d{{5}})\b'

# Constants for company information fields.
comercial_comp_name = 'Company Commercial Name'
legal_comp_name = 'Company Legal Name'
all_available_comp_name = 'Company All Available Names'

# Headers to be sent with HTTP requests to mimic a real browser request.
request_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Accept': '*/*'
}

# Reads company information from a CSV file into a dictionary.
def read_company_info(file_path):
    company_info = {}
    with open(file_path, mode='r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            domain = row['domain']
            company_info[domain] = {
                comercial_comp_name: row['company_commercial_name'],
                legal_comp_name: row['company_legal_name'],
                all_available_comp_name: row['company_all_available_names']
            }
    return company_info

# Removes duplicate words from an address.
def deduplicate_address(address):
    words = address.split()
    seen = set()
    unique_words = []

    for word in words:
        stripped_word = re.sub(r'\W+', '', word)
        if stripped_word not in seen:
            seen.add(stripped_word)
            unique_words.append(word)

    return ' '.join(unique_words)

# Makes requests to the provided domain and its subpages to find contact information.
def make_request_and_search(domain):
    subpages = ['', 'about', 'about-us', 'contact', 'contact-us']
    info = {'phone_numbers': set(), 'facebook_links': set(), 'addresses': set(), 'main_page_success': False}
    for subpage in subpages:
        url = f'http://{domain}/{subpage}'
        try:
            response = requests.get(url, headers=request_headers, timeout=3)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text(" ", strip=True)
                info['phone_numbers'].update(re.findall(phone_regex, text))
                facebook_links = re.findall(facebook_regex, response.text)
                info['facebook_links'].update(facebook_links)
                matches = re.findall(state_zip_regex, text)
                for pre_text, state, zip_code in matches:
                    full_address = f"{pre_text.strip() if pre_text else ''} {state} {zip_code}".strip()
                    unique_address = deduplicate_address(full_address)
                    info['addresses'].add(unique_address)
                if subpage == '':
                    info['main_page_success'] = True
        except requests.RequestException as e:
            if subpage == '':
                print(f"Error accessing {url}: {e}")
            break
    return domain, info

# Reads the list of domains from a CSV file.
def read_domains_from_csv(file_path):
    domains = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        next(csv_reader, None)  # Skip the header
        for row in csv_reader:
            domains.append(row[0])
    return domains

# The main function orchestrates the reading, processing, and saving of data.
def main():
    start_time = time.time()
    file_path = 'sample-websites.csv'
    additional_info_path = 'sample-websites-company-names.csv'
    output_file_path = 'PhoneNumber_FacebookLink_Addresses_CompanyNames.csv'

    domains = read_domains_from_csv(file_path)
    company_info = read_company_info(additional_info_path)
    domain_info = {domain: None for domain in domains}
    successful_accesses = 0
    unsuccessful_accesses = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(make_request_and_search, domain) for domain in domains]
        for future in concurrent.futures.as_completed(futures):
            domain, info = future.result()
            domain_info[domain] = info
            if info and info['main_page_success']:
                successful_accesses += 1
            else:
                unsuccessful_accesses += 1

    client = SearchClient.create('FOEOURC6HS', '881d1efc2a907d9f5b57faf1a347e9c3') # Public API key, the private API key will be delivered by email
    index = client.init_index('ScrapperPhoneNumberFacebookLinksAddresses')

    records = []
    for domain, info in domain_info.items():
        if info:
            record = {
                "objectID": domain,
                "domain": domain,
                "phone_numbers": ', '.join(info.get('phone_numbers', [])),
                "facebook_links": ', '.join(info.get('facebook_links', [])),
                "addresses": ', '.join(info.get('addresses', [])),
                **company_info.get(domain, {})
            }
            records.append(record)

    # Save the records to Algolia for search indexing.
    if records:
        try:
            index.save_objects(records)
            print(f"Indexed {len(records)} records to Algolia.")
        except Exception as e:
            print(f"Algolia indexing failed: {e}")

    # Write the collected data into a CSV file.
    with open(output_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        headers = ['Domain', 'Phone Numbers', 'Facebook Links', 'Addresses', 'Company Commercial Name',
                   'Company Legal Name', 'Company All Available Names']
        writer.writerow(headers)
        for domain in domains:
            info = domain_info.get(domain, {})
            unique_addresses = [deduplicate_address(addr) for addr in info.get('addresses', ['N/A'])]
            row = [
                domain,
                ', '.join(info.get('phone_numbers', ['N/A'])),
                ', '.join(info.get('facebook_links', ['N/A'])),
                ', '.join(unique_addresses),
                company_info.get(domain, {}).get(comercial_comp_name, 'N/A'),
                company_info.get(domain, {}).get(legal_comp_name, 'N/A'),
                company_info.get(domain, {}).get(all_available_comp_name, 'N/A')
            ]
            writer.writerow(row)

    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    print(f"Data has been written to {output_file_path}")
    print(f"Successfully accessed {successful_accesses} websites.")
    print(f"Failed to access {unsuccessful_accesses} websites.")
    print(f"Time taken: {int(minutes)} minutes and {int(seconds)} seconds.")

# The entry point of the script.
if __name__ == "__main__":
    main()