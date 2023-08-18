from dataclasses import dataclass, field
import numpy as np
import re
import requests

# Define constants
# TODO: some of these should be changeable in the command line
CSV_NAME = 'results.csv'

API_KEY_FILE = '../API_keys/congress_API.txt'
URL_FILE = 'urls.txt'

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

# Define classes

# TODO: Implement more sophisticated name objects
# @dataclass
# class Person_Name:
#     """ Class to hold different representations of Congresspeople's names 
# 
#     For now this is a trivial use case, but in the future we may want to
#     include things like FirstName LastName versions if we want to track
#     the same person through, e.g., the House and Senate, 
#     """
#     full_title: str
#     full_title_no_comma: str
# 
#     @classmethod
#     def from_full_name(cls, full_title: str):
#         full_title_no_comma = full_title.replace(',', ';')
#         return cls(full_title, full_title_no_comma)
# 
# class Person_Name_List:
#     """ A class to make operations on lists of Person_Name more clean """
#     def __init__(self, person_list: list[Person_Name]):
#         self.person_list = person_list
# 
#     def to_full_title_original_list(self):
#         return [person.full_title for person in self.person_list]
# 
#     def to_full_title_no_comma_list(self):
#         return [person.full_title_no_comma for person in self.person_list]

@dataclass
class Bill_Metadata:
    """ Class to hold metadata about a bill """
    shortest_title: str
    titles: list[str]
    sponsors: list[str]
    original_cosponsors: list[str]
    later_cosponsors: list[str]

    @classmethod
    def from_API_GETs(cls, main_json: dict, cosponsors_json: dict, titles_json: dict):
        
        # Retrieve the list[str] from the API calls
        sponsor_list = main_json['bill']['sponsors']
        cosponsor_list = cosponsors_json['cosponsors']
        titles_list = titles_json['titles']
       
        # Convert to appropirate types
        sponsors = [sponsor['fullName'].replace(',', ';') for sponsor in sponsor_list]

        # Split cosponsors into "original" and "later"
        original_cosponsors = [cosponsor['fullName'].replace(',', ';') for cosponsor in cosponsor_list if cosponsor['isOriginalCosponsor']]
        later_cosponsors = [cosponsor['fullName'].replace(',', ';') for cosponsor in cosponsor_list if not cosponsor['isOriginalCosponsor']]

        # Remove commas from titles in case we save as CSV
        # TODO: Maybe refactor this to use the word title less often
        titles = [title['title'].replace(',', '') for title in titles_list] 
        shortest_title = min(titles, key=len)

        return cls(shortest_title, titles, sponsors, original_cosponsors, later_cosponsors)



@dataclass
class Person_Metadata:
    """ Class to hold information about a Congressperson """
    name: str
    num_bills_sponsored: int = 0
    num_bills_original_cosponsored: int = 0
    num_bills_later_cosponsored: int = 0
    title_bills_sponsored: list[str] = field(default_factory=list) # []
    title_bills_original_cosponsored: list[str] = field(default_factory=list) # []
    title_bills_later_cosponsored: list[str] = field(default_factory=list) # []
    
    @classmethod
    def from_bill_metadata_list(cls, name: str, bill_metadata_list: list[Bill_Metadata]):

        new_person_metadata = cls(name)

        for bill_metadata in bill_metadata_list:

            if name in bill_metadata.sponsors:
                new_person_metadata.num_bills_sponsored += 1
                new_person_metadata.title_bills_sponsored.append(bill_metadata.shortest_title)
            if name in bill_metadata.original_cosponsors:
                new_person_metadata.num_bills_original_cosponsored += 1
                new_person_metadata.title_bills_original_cosponsored.append(bill_metadata.shortest_title)
            if name in bill_metadata.later_cosponsors:
                new_person_metadata.num_bills_later_cosponsored += 1
                new_person_metadata.title_bills_later_cosponsored.append(bill_metadata.shortest_title)

        return new_person_metadata

@dataclass
class API_URL_Parts:
    """ Class to hold the different parts of the bill's URL 

    Note that variables that have _num in their name are still 
    of type str since we never need to treat this as a number 
    (e.g. we are never doing arithmetic on it)

    Note also that the parts of the URL are different between the API 
    and the web interface, which is why the BILLTYPE_URL_TO_API dict 
    was made and why parts of the strings need to be stripped 

    This class is holding the information you need to use the API
    """
    congress_session_num: str
    bill_type: str
    bill_num: str

    @classmethod
    def from_web_URL(cls, url: str):
          
        url_parts = url.split('/')
        congress_web_string = url_parts[4]
        billType_web_string = url_parts[5]
        billNumber_web_string = url_parts[6]
        
        congress_session_num = congress_web_string[:3]
        bill_type = BILLTYPE_URL_TO_API[billType_web_string]
        try:
            bill_num = re.findall("^(\d+)\??.*", billNumber_web_string)[0]
        except IndexError:
            print(f'Error with URL {url}, could not find the part of the URL corresponding to the bill number, the part being checked for a number is "{billNumber_web_string}"')
            raise

        # We won't use this as a number, but this can be handy to make sure the regex did its job correctly
        try:
            int(bill_num)
        except ValueError:
            print(f'Error with URL {url}, cannot convert the bill number "{billNumber_web_string}", which was parsed as {bill_num}, to an int')
            raise

        return cls(congress_session_num, bill_type, bill_num)

def get_metadata(web_url: str, api_key: str) -> Bill_Metadata:
    """ Make calls to the congress.gov API and store the data in dataclasses """
        
    api_url_parts = API_URL_Parts.from_web_URL(web_url)

    api_url_base = 'https://api.congress.gov/v3/bill/' + api_url_parts.congress_session_num + '/' + api_url_parts.bill_type + '/' + api_url_parts.bill_num
    api_url_main =  api_url_base + '?api_key=' + api_key
    api_url_cosponsors =  api_url_base + '/cosponsors' + '?api_key=' + api_key
    api_url_titles =  api_url_base + '/titles' + '?api_key=' + api_key

    main_json = requests.get(api_url_main).json()
    cosponsors_json = requests.get(api_url_cosponsors).json()
    titles_json = requests.get(api_url_titles).json()

    return Bill_Metadata.from_API_GETs(main_json, cosponsors_json, titles_json)

def count_metadata(bill_metadata_list: list[Bill_Metadata]) -> list[Person_Metadata]:
    """ Take all the metadata we have for bills and convert it to metadata about people """

    sponsors = np.concatenate([bill_metadata.sponsors for bill_metadata in bill_metadata_list])
    original_cosponsors = np.concatenate([bill_metadata.original_cosponsors for bill_metadata in bill_metadata_list])
    later_cosponsors = np.concatenate([bill_metadata.later_cosponsors for bill_metadata in bill_metadata_list])
    all_names = np.unique(np.concatenate([sponsors, original_cosponsors, later_cosponsors]))
    
    person_metadata_list = []
    for name in all_names:
        person_metadata_list.append(Person_Metadata.from_bill_metadata_list(name, bill_metadata_list))

    return person_metadata_list

def sort_metadata(person_metadata_list: list[Person_Metadata]) -> list[Person_Metadata]:
    """ Sort initally by number of sponsored bills, then tiebreak with number of cosponsored bills """

    sorted_person_metadata = sorted(person_metadata_list, key=lambda x: (x.num_bills_sponsored, x.num_bills_original_cosponsored, x.num_bills_later_cosponsored), reverse=True)
    return sorted_person_metadata

def save_csv(person_metadata_list: list[Person_Metadata]) -> None:

    headings = ['name', 'sponsored', 'cosponsored-original', 'cosponsored-later', 'titles_sponsor', 'titles_original_cosponsor', 'titles_later_cosponsor']
    with open(CSV_NAME, 'w') as f:
        f.write(','.join(headings))
        f.write('\n')

        for person_metadata in person_metadata_list:
            f.write(person_metadata.name)
            f.write(',')
            f.write(str(person_metadata.num_bills_sponsored))
            f.write(',')
            f.write(str(person_metadata.num_bills_original_cosponsored))
            f.write(',')
            f.write(str(person_metadata.num_bills_later_cosponsored))
            f.write(',')
            f.write('; '.join(person_metadata.title_bills_sponsored))
            f.write(',')
            f.write('; '.join(person_metadata.title_bills_original_cosponsored))
            f.write(',')
            f.write('; '.join(person_metadata.title_bills_later_cosponsored))
            f.write('\n')

def run_analysis(api_file: str, url_file: str) -> None:

    with open(api_file) as f:
        api_key = f.read().strip()

    with open(url_file) as f:
        web_urls = f.read().splitlines()

    bill_metadata_list = []

    for web_url in web_urls[:]:
        try:
            bill_metadata_list.append(get_metadata(web_url, api_key))
        except:
            print(f'Skipping URL {web_url}')

    person_metadata_list = count_metadata(bill_metadata_list)
    sorted_person_metadata_list = sort_metadata(person_metadata_list)
    save_csv(sorted_person_metadata_list)

    # Print results
    for person_metadata in sorted_person_metadata_list:
        print(person_metadata)

if __name__ == '__main__':
    run_analysis(api_file=API_KEY_FILE, url_file=URL_FILE)

