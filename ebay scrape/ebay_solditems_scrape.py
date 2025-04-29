#%% Imports, ebay functions
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
# and activate VPN for English&USD !!!

def get_data(searchterm, page_num):
   url = (f'https://www.ebay.com/sch/i.html?_nkw={searchterm}&_pgn={page_num}'
          '&_sacat=0&_from=R40&rt=nc&LH_Sold=1&LH_Complete=1&_lang=en-US&_fcid=US&_ipg=60')

   headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.ebay.com/',
        'DNT': '1'
    }
    
    # Add cookies to enforce English
   cookies = {
        'gh_loc': 'US',
        'lang': 'en-US',
        'site': 'eng'
    }
    
   r = requests.get(url, headers=headers, cookies=cookies)
   with open('debug.html', 'w', encoding='utf-8') as f:
       f.write(r.text)
    
   soup = BeautifulSoup(r.text, 'html.parser')
   return soup

def parse(soup):
    productslist = []
    results = soup.find_all('div', {'class': 's-item__info clearfix'})
    for item in results:
        product = {
            'title': item.find('div', {'class':'s-item__title'}).text,
            'soldprice': item.find('span', {'class': 's-item__price'}).text,
            'solddate': item.find('div', {'class': 's-item__caption'}).text.replace('eladva  ', ''),
            'link': item.find('a', {'class': 's-item__link'})['href']
            }
        productslist.append(product)
    return productslist

def output(productslist):
    productsdf = pd.DataFrame(productslist)
    print(productsdf)
    return productsdf

#%% Import fbref big5 dataframe
import TSDP.fbref.fbref_module as fbref
url_big5 = 'https://fbref.com/en/comps/Big5/stats/players/Big-5-European-Leagues-Stats'
df_big5 = fbref.format_column_names(fbref.scrape(url_big5, 'stats_standard'))

#%% Modify fbref dataframe
# Drop header rows
df_big5 = df_big5[df_big5.Rk != 'Rk']
# Convert age to numeric
df_big5['Age_float'] = ((df_big5.Age.str.split('-').str[0]).astype(float)+(df_big5.Age.str.split('-').str[1]).astype(float)/365)
df_big5['Playing Time_90s'] = df_big5['Playing Time_90s'].astype(float)
## Filter: age<23, 90s>5
filter_ = (df_big5['Playing Time_90s'] >= 10) & (df_big5['Age_float'] <= 23)
df_big5_filter = df_big5[filter_].reset_index(drop=True)

#%% Find rookie years on fbref
"""
## Get links to player profiles
response_big5 = requests.get(url_big5)
soup_big5 = BeautifulSoup(response_big5.text, 'html.parser')

for i, row in df_big5_filter[:30].iterrows(): 
    playerrows = soup_big5.find_all('td', {'data-stat': 'player'})
    for playerrow in playerrows:
        if playerrow.find('a').text == row['Player']:
            url_player = 'https://www.fbref.com' + playerrow.find('a')['href']
            break
    ## 'stats_standard_dom_lg' table -> (seasons.unique = only this year)? -> if true add to list
    df_player = fbref.format_column_names(fbref.scrape(url_player, 'stats_standard_dom_lg'))
    first_season = df_player.loc[df_player.Comp.str[:2]=='1.', 'Season'].iloc[0]
    first_big5_season = df_player.loc[df_player.Comp.str.contains('Ligue 1') \
                  | df_player.Comp.str.contains('La Liga') \
                  | df_player.Comp.str.contains('Premier League') \
                  | df_player.Comp.str.contains('Bundesliga') \
                  | df_player.Comp.str.contains('Serie A'), 
                          'Season'].iloc[0]
    # Modify dataframe
    df_big5_filter.loc[i, 'first_season'] = first_season
    df_big5_filter.loc[i, 'first_big5_season'] = first_big5_season
    print(i, row['Player'])

df_big5_filter['season_year'] = df_big5_filter.first_season.str.split('-').str[0].astype(float)
df_big5_filter['big5_season_year'] = df_big5_filter.first_big5_season.str.split('-').str[0].astype(float)
"""
#%% Save big5 database to Excel or load it
path_big5 = 'other_projects/ebay scrape/big5_youngsters.xlsx'
if df_big5_filter: # save
    df_big5_filter.to_excel(path_big5, index=False)
else: # load
    df_big5_filter = pd.read_excel(path_big5)

#%% Search players on tcdb
searchterm_player = df_big5_filter.loc[13, 'Player'].replace(' ', '+')

def find_tcdb_player_url(searchterm_player):
    url_tcdb = f'https://www.tcdb.com/Search.cfm?SearchCategory=Soccer&cx=partner-pub-2387250451295121%3Ahes0ib-44xp&cof=FORID%3A10&ie=ISO-8859-1&q={searchterm_player}'
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from io import StringIO
    
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url_tcdb)
    a_elements = driver.find_elements(By.TAG_NAME, "a")
    # Find urls
    for a in a_elements:
        href = a.get_attribute("href")
        text = a.text
        if pd.isna(href) == False:
            if ('Person.cfm' in href): # first one = right one for us
                url_tcdb_player = href
                break
    driver.quit()
    return url_tcdb_player

url_tcdb_player = find_tcdb_player_url(searchterm_player)
tcdb_id = url_tcdb_player.split('pid/')[-1].split('/')[0] # Player id for later

#%% Search each on ebay -> create dataframe

# Dataframe: searchterm, card_id, playername, fabrique, set name, year, cardnumber, rarity, PSA grade, +ebay data

searchterm = 'Lamine+Yamal+cards'
pages_nr = 1

def fetch_sold_items(searchterm, pages_nr=1)
    df_multi = pd.DataFrame()
    for page_num in range(1, pages_nr+1):
        soup = get_data(searchterm, page_num)
        productslist = parse(soup)
        df = output(productslist)
        df = df[df.title != 'Shop on eBay']
        df_multi = pd.concat([df_multi, df], ignore_index=True)
        time.sleep(random.uniform(2, 10))
    return df_multi

df_ebay = fetch_sold_items(searchterm, pages_nr)

#%% Format, build data table
df['soldprice_fact'] = df['soldprice'].str.split(' to ').str[0].str.replace('$', '').str.replace(',', '').astype(float)
