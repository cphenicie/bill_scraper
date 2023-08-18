# bill_scraper

A tool to aggregate information between a series of bills.

For now, the main use is figuring out which Congresspeople sponsor, or co-sponsor the bills in the list the most.

To use this code, you'll need to get an API key here: https://api.congress.gov/sign-up/

And then put this into the file `congress_API.txt` located in the folder `../API_keys` (or just modify the code to put the API key directly there)

For now, you can feed in the URLs in the file `urls.txt` with one line per URL. (Ideally, this would be a Google Sheet, or similar)

Documentation for the Congresse API can be found here: https://api.congress.gov/
