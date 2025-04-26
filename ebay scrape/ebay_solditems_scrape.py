import requests
from bs4 import BeautifulSoup
import pandas as pd

searchterm = 'Lamine+Yamal+cards'

def get_data(searchterm):
    url = f'https://www.ebay.com/sch/i.html?_nkw={searchterm}&_sacat=0&_from=R40&rt=nc&LH_Sold=1&LH_Complete=1'
    r = requests.get(url)
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
    return productsdf

soup = get_data(searchterm)
productslist = parse(soup)
df = output(productslist)