import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import re, sys, requests, dateutil.parser
from matplotlib import pyplot as plt
from pprint import pprint
from patsy import dmatrices
from patsy import dmatrix
import statsmodels.api as sm

def get_movie_value(soup, field_name):
	'''Grab a value from boxofficemojo HTML
	
	Takes a string attribute of a movie on the page and
	returns the string in the next sibling object
	(the value for that attribute)
	or None if nothing is found.
	'''
	obj = soup.find(text=re.compile(field_name))
	if not obj:
		return None
	# this works for most of the values
	next_sibling = obj.findNextSibling()
	if next_sibling:
		return next_sibling.text 
	else:
		return None

def to_date(datestring):
	'''Parses date string into a datetime object
	'''

	date = dateutil.parser.parse(datestring)
	return date

def money_to_int(moneystring):
	'''converts money string into an integer value

	Takes a string which is of the format $XXX,XXX,XXX
	and removes the $ sign and commas, converts the string to an int
	and returns the int
	'''
	moneystring = moneystring.replace('$', '').replace(',', '')
	return int(moneystring)

def runtime_to_minutes(runtimestring):
	'''converts our runtimestring into an integer

	Takes a string which is formatted X hrs. XX mins. and then
	splits the string and finally tries to convert it to an integer
	which represents total minutes and returns None if it can't.
	'''
	runtime = runtimestring.split()
	try:
		minutes = int(runtime[0])*60 + int(runtime[2])
		return minutes
	except:
		return None

def get_budget(soup):
	'''gets the budget of a movie and returns it as an integer

	Takes in a soup object and then finds the value corresponding to budget.
	If the budget is N/A, then it returns 0, otherwise it removes the $ sign
	and splits the string and finally returns it as an integer formatted in
	terms of millions of dollars.
	'''
	raw_budget = get_movie_value(soup, 'Production Budget')
	if raw_budget == 'N/A':
		return 0
	else:
		raw_budget = raw_budget.replace('$', '').split()
		return int(float(raw_budget[0]) * 1000000)

def get_movie_information(soup):
	'''Returns all of the information for a given movie

	Takes a soup object and then finds the title, release date,
	domestic total gross, genre, and rating and returns them all
	'''
	title_string = soup.find('title').text
	title = title_string.split('(')[0]
	
	raw_release_date = get_movie_value(soup,'Release Date')
	release_date = to_date(raw_release_date)
	
	raw_domestic_total_gross = get_movie_value(soup,'Domestic Total')
	domestic_total_gross = money_to_int(raw_domestic_total_gross)

	genre = get_movie_value(soup,'Genre:')

	rating = get_movie_value(soup,'Rating')
	
	return title, release_date, domestic_total_gross, genre, rating

def scrape_data(movies):
	'''Scrapes all of the data for the given movies and returns a DataFrame

	Takes in a DataFrame with information about the movies to scrape,
	including the identifier for each movies's url.  Zips the ids together
	and then loops through and scrapes the pages for each remake and original movie
	together.  It then creates a dict for each of these pairs and adds it to a list,
	and finally the list of dicts is returned as a DataFrame.
	'''
	remakes = movies['id_remake'].tolist()
	originals = movies['id_original'].tolist()

	headers = ['title', 'originaltitle','domestictotalgross', 'domestictotalgrossoriginal',
		   'releasedate', 'releasedateoriginal', 'ratingremake', 'ratingoriginal', 'genreremake', 'genreoriginal', 'budget']
	movie_data = []

	for r, o in zip(remakes, originals):
		url_original = 'http://www.boxofficemojo.com/movies/?id='+o+'.htm&adjust_yr=2015&p=.htm'
		url_remake = 'http://www.boxofficemojo.com/movies/?id='+r+'.htm&adjust_yr=2015&p=.htm'
		
		response_original = requests.get(url_original)
		response_remake = requests.get(url_remake)

		page_original = response_original.text
		page_remake = response_remake.text

		soup_original = BeautifulSoup(page_original)
		soup_remake = BeautifulSoup(page_remake)

		budget = get_budget(soup_remake)

		title_original, release_date_original, domestic_gross_original, genre_original, rating_original = get_movie_information(soup_original)
		title_remake, release_date_remake, domestic_gross_remake, genre_remake, rating_remake = get_movie_information(soup_remake)
		movie_dict = dict(zip(headers, [title_remake, title_original, domestic_gross_remake, domestic_gross_original,
										release_date_remake, release_date_original, rating_remake,
										rating_original, genre_remake, genre_original, budget]))
		movie_data.append(movie_dict)

	return pd.DataFrame(movie_data)

def rearrange(movies_df):
	'''
	Rearanges the DataFrame so that the titles come first for easier reading
	'''
	return movies_df[['title', 'originaltitle','domestictotalgross', 'domestictotalgrossoriginal', 'budget', 'releasedate', 'releasedateoriginal', 'genreremake', 'genreoriginal', 'ratingremake', 'ratingoriginal']]

def time_diff(movies_df):
	'''Creates the time difference feature

	Takes in a DataFrame and then subtracts release dates for each pair.
	The time delta is then converted to an integer in terms of days and
	the series is returned
	'''
	return (movies_df['releasedate'] - movies_df['releasedateoriginal']).dt.days

def same_rating(movies_df):
	'''Creates the time difference feature

	Takes in a DataFrame and then compares the two ratings columns together, 
	sets it to true if they are and then the series is returned
	'''
	return (movies_df['ratingoriginal'] == movies_df['ratingremake'])

def bin_genres(movies_df):
	'''Converts the genreremake field into new features for each genre

	Takes in a DataFrame and then for each of the new features looks to see
	if the genreremake string contains the feature name and sets it to true
	if it does.  This allows movies to have multiple different generes.
	Finally the DataFrame is returned
	'''
	movies_df['comedy'] = movies_df['genreremake'].str.contains('Comedy')
	movies_df['action'] = movies_df['genreremake'].str.contains('Action')
	movies_df['adventure'] = movies_df['genreremake'].str.contains('Adventure')
	movies_df['horror'] = movies_df['genreremake'].str.contains('Horror')
	movies_df['romance'] = movies_df['genreremake'].str.contains('Roman')
	movies_df['music'] = movies_df['genreremake'].str.contains('Music')
	movies_df['fantasy'] = movies_df['genreremake'].str.contains('Fantasy')
	movies_df['drama'] = movies_df['genreremake'].str.contains('Drama')
	movies_df['thriller'] = movies_df['genreremake'].str.contains('Comedy')
	movies_df['scifi'] = movies_df['genreremake'].str.contains('Sci-Fi')

	return movies_df

def scrape_mode():
	'''Scrapes the movie data and dumps it to a pickle file

	Reads a csv file with the movie id information for Box Office Mojo.
	Scrapes all of the data into a DataFrame and then processes it to
	add new features it and dumps it to a pickle file.
	'''
	movies = pd.read_csv('movie-list.csv')
	movies_df = scrape_data(movies)

	movies_df = rearrange(movies_df)
	movies_df['time_diff'] = time_diff(movies_df)

	movies_df['samerating'] = same_rating(movies_df)

	movies_df = bin_genres(movies_df)
	movies_df.to_pickle('movie-data.pkl')

def main(argv):
	if argv[0] == 'scrape':
		scrape_mode()
	elif argv[0] == 'load':
		movies_df = pd.read_pickle('movie-data.pkl')
		movies_df = movies_df[movies_df['budget'] > 0]

		
		y, X = dmatrices('domestictotalgross ~ budget + adventure + fantasy', data=movies_df, return_type='dataframe')

		model = sm.OLS(y, X)
		res = model.fit()
		pprint(res.summary())

if __name__ == "__main__":
   main(sys.argv[1:])

