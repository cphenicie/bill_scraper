import numpy as np
import re
import requests

CSV_NAME = 'results.csv'

API_KEY_FILE = '../API_keys/congress_API.txt'

BILLTYPE_URL_TO_API = {
        'house-bill': 'hr', 
        'senate-bill': 's', 
        'house-joint-resolution': 'hjres', 
        'senate-joint-resolution': 'sjres', 
        'house-concurrent-resolution': 'hconres', 
        'senate-concurrent-resolution': 'sconres', 
        'house-resolution': 'hres',
        'senate-resolution': 'sres'
        }

with open(API_KEY_FILE) as f:
    api_key = f.read().strip()

with open('urls.txt') as f:
    bill_urls = f.read().splitlines()


# Make lists for different types of authorship, and add names from the urls.txt
sponsors = []
original_cosponsors = []
later_cosponsors = []

for bill_url in bill_urls[:2]:
    url_parts = bill_url.split('/')
    congress_string = url_parts[4]
    billType_string = url_parts[5]
    billNumber_string = url_parts[6]


    congress_API_string = congress_string[:3]
    billType_API_string = BILLTYPE_URL_TO_API[billType_string]
    try:
        billNumber_API_string = re.findall("^(\d+)\??.*", billNumber_string)[0]
    except IndexError:
        print(f'Skipping the URL {bill_url} because I could not find the part of the URL corresponding to the bill number, that section is just "{billNumber_string}"')
        continue

    try:
        int(billNumber_API_string)
    except ValueError:
        print(f'Skipping the URL {bill_url} because I cannot convert the bill number "{billNumber_string}", which I parsed to {billNumber_API_string}, to an int')
        continue

    api_url_base = 'https://api.congress.gov/v3/bill/' + congress_API_string + '/' + billType_API_string + '/' + billNumber_API_string
    api_url_main =  api_url_base + '?api_key=' + api_key
    api_url_cosponsors =  api_url_base + '/cosponsors' + '?api_key=' + api_key

    response_main = requests.get(api_url_main).json()
    response_cosponsors = requests.get(api_url_cosponsors).json()
    # print(response_cosponsors)
    # print(response_main)

    sponsor_list = response_main['bill']['sponsors']
    for sponsor in sponsor_list:
        sponsors.append(sponsor['fullName'])
    # print(sponsor_names)

    cosponsor_list = response_cosponsors['cosponsors']
    # print(cosponsor_names)
    for cosponsor in cosponsor_list:
        if cosponsor['isOriginalCosponsor']:
            original_cosponsors.append(cosponsor['fullName'])
        else:
            later_cosponsors.append(cosponsor['fullName'])

# Count the number of each type of authorship, and sort by most in sponsorship
# Tiebroken by most in sponsorship (first orginal-, then later-sponsorship)
all_names = np.unique(np.concatenate([sponsors, original_cosponsors, later_cosponsors]))

counts_dict = {name: {'sponsor': sponsors.count(name), 
                      'original_cosponsor': original_cosponsors.count(name),
                      'later_cosponsor': later_cosponsors.count(name)} 
               for name in all_names}

sorted_counts_dict_items = sorted(counts_dict.items(), key=lambda x: (x[1]['sponsor'], x[1]['original_cosponsor'], x[1]['later_cosponsor']), reverse=True) 

# Save to CSV
headings = ['name', 'sponsored', 'cosponsored-original', 'cosponsored-later']
with open(CSV_NAME, 'w') as f:
    f.write(','.join(headings))
    f.write('\n')

    for counts in sorted_counts_dict_items:
        f.write(counts[0].replace(',', ';'))
        f.write(',')
        f.write(str(counts[1]['sponsor']))
        f.write(',')
        f.write(str(counts[1]['original_cosponsor']))
        f.write(',')
        f.write(str(counts[1]['later_cosponsor']))
        f.write('\n')

# Print results
for counts in sorted_counts_dict_items:
    print(counts)


