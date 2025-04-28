#%% Imports, functions
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

# Fetch sold items data from ebay
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
filter_ = (df_big5['Playing Time_90s'] >= 5) & (df_big5['Age_int'] <= 23)
df_big5_filter = df_fbref[filter_].reset_index(drop=True)
## Get links to profile
response_big5 = requests.get(url_fbref)
soup_big5 = BeautifulSoup(response_big5.text, 'html.parser')

for i, row in df_big5_filter[:10].iterrows(): 
    playerrows = soup_big5.find_all('td', {'data-stat': 'player'})
    for playerrow in playerrows:
        if playerrow.find('a').text == row['Player']:
            url_player = 'https://www.fbref.com' + playerrow.find('a')['href']
            break
    ## 'stats_standard_dom_lg' table -> (seasons.unique = only this year)? -> if true add to list
    df_player = fbref.format_column_names(fbref.scrape(url_player, 'stats_standard_dom_lg'))
    first_pro_season = df_player.loc[df_player.Comp.str[:2]=='1.', 'Season'].iloc[0]
    # Modify dataframe
    df_big5_filter.loc[i, 'first_pro_season'] = first_pro_season
    
#%% Search on tcdb


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

df = fetch_sold_items(searchterm, pages_nr)

#%% Format, build data table
df['soldprice_fact'] = df['soldprice'].str.split(' to ').str[0].str.replace('$', '').str.replace(',', '').astype(float)
