# Analyzing Movie Reboots and Remakes
Analysis of movies and their remakes or reboots using data scraped from boxofficemojo.com.  Included is a script which scrapes the requested data and saves it to a pickle file and a Jupyter Notebook which outlines the analysis and conclusions from the data.

## roboot_movies.py
This script takes in a csv file with the format:

```
Remake,id_remake,Original,id_original
About Last Night (2014),aboutlastnight14,About Last Night,aboutlastnight
```

Where the id is the id used in the url by boxofficemojo to identify the film.  It should be noted that because we are looking at pairs of movies (i.e. a movie and its remake/reboot), pairs of movies are required with the first movie listed being the remake and the second being the original.

The script can then by run by:
```python reboot_movies.py scrape```

This runs the script in scraping mode it can also run OLS after the data is scraped by:
```python reboot_movies.py load```

## movie_reboots.ipynb
This notebook file contains the analysis of the data that was scraped using the script provided.  I was investigating the usage of linear regression models to predict the success of a remake of a movie or a reboot of an existing franchise.  Success is defined as Domestic Total Gross.  Additional caveats about the data and analysis are provided at the top of the notebook.
