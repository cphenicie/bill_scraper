# bill_scraper

A tool to run metadata analysis on legislation introduced to the US Congress.

This takes a list of URLs of bills on www.congress.gov and returns a list of Congresspeople that (co-)sponsored the bills, sorted by how many bills they sponosored. This is output both into the terminal and into the file `results.csv` (which should display nicely if you open it in GitHub.

For the bills in the `urls.txt` currently in this repo, I chose them by searching for 'AI' and 'Artificial Intelligence' on www.congress.gov, and then selected bills from the 118th Congress that had titles that sounded relevant. **Beware** this is a very arbitrary way of selecting these, and the results will be biased becuase of this.

To use this code, you'll need to get an API key here: https://api.congress.gov/sign-up/

And then save the key they send to you into the file `congress_API.txt` located in the folder `../API_keys` (or just modify the code to put the API key directly there, but don't publish it!)

You can then feed in the URLs in the file `urls.txt` with one line per URL.

Documentation for the Congress API can be found here: https://api.congress.gov/
