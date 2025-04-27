import requests
from bs4 import BeautifulSoup
import pandas as pd

searchterm = 'Lamine+Yamal+cards'

def get_data(searchterm):
   url = (f'https://www.ebay.com/sch/i.html?'
           f'_nkw={searchterm}&_sacat=0&_from=R40&rt=nc&'
           f'LH_Sold=1&LH_Complete=1&'
           f'_lang=en-US&_fcid=US&_ipg=60&_pgn=1')  # fcid=US forces US site
    
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

soup = get_data(searchterm)
productslist = parse(soup)
df = output(productslist)
df = df[df.title != 'Shop on eBay']

#%%
df['soldprice_fact'] = df['soldprice'].str.split(' to ').str[0].str.replace('$', '').str.replace(',', '').astype(float)
