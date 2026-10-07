# How to use and understand the levels system, and how we got there

## How to use:
first: 

`from game.waves import load_level`

then: 

`level = load_level(current_city)`

and then for example:

`level["outbreak_strength"]`


Spell city names correctly and capitalized:

Leiden, Tallinn, Istanbul, Sparta, Wloclawek, Dusseldorf, Avignon

The keys to use:
- city
- country 
- year
- disease
- cases (for the whole country)
- vaccine_coverage (goes from 0 to 1)
- outbreak_strength (rank of the countries we have, 0 for weakest 1 for strongest)

The game only uses these numbers to scale the levels (cure rate, how many enemies, which enemy types).
Players never see the years or case counts: every city has its own themed look (for example ancient Sparta).

outbreak strength pretty much evens out the jumps between levels
sorted the cities by cases, smallest to biggest
Each city's place (0 to 6) is divided by 6 
(why? so that if we add more cities we can always find the correct levels even 
if we add more cities or something like that. Easiest is always 0, hardest is 1). 
That gives 0, 0.17, 0.33, 0.5, 0.67, 0.83, 1.0.

That is so that the jumps between levels are normal. 
Otherwise we would get very big or small jumps. 
We can choose how we implement the difficulty jumps. 

Don't edit levels/*.json by hand, rebuild it


## How we got it

Two excel files from the WHO Immunization Data portal (in data/raw)
https://immunizationdata.who.int/

for each city the country's biggest single year outbreak of 
MEASLES, RUBELLA, PERTUSSIS, DIPHTHERIA that also has 
vaccination info. from that we get disease, year, cases, coverage. 


## if you wish to rebuild the data (you really don't need to)

(better to keep the database off gh as we would be adding 50 Mb
to the repo every time we rebuild as git keeps every copy i think)

python -m pip install -r requirements-dev.txt

From the main folder, run python data_pipeline/load_database.py 
(takes a bit of time), then python data_pipeline/build_levels.py. 
Script creates the database.

load_database.py prints a junk report (how many rows each filter throws away):

    coverage: 396,212 rows -> WUENIC only 89,767 -> countries only 78,013 -> with a year and a value 58,291
    cases: 90,400 rows -> countries only 87,322 -> with a year and a count 66,741 -> diseases we use 28,577

build_levels.py prints a summary table of the 7 levels.
Running it twice gives exactly the same files.


## Tests

From the main folder: python -m pytest

- tests/test_levels.py checks the level files (7 cities, sane numbers, strength is a rank, the game turns
  them into sane gameplay numbers). No database needed.
- tests/test_pipeline.py checks the database against known numbers (Ghana MCV1 1980 = 16%, Netherlands
  measles 2013 = 2,632 cases, ...) and fails if levels/*.json are out of date. Skipped if
  data/who_data.db doesn't exist yet.


## Issues 

Strength compares countries based on total cases so big countries score higher. 

4 of 7 have measles (we can use other data sources 
to get variety)



