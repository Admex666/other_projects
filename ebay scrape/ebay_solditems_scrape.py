#%% Imports, ebay functions
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import numpy as np
from rapidfuzz import process, fuzz
import re
# and activate VPN for English&USD !!!
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from io import StringIO

#%% Import fbref big5 dataframe
"""
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

"""
#%% import previously stored files
folder = 'other_projects/ebay scrape/'
path_big5 = folder+ 'big5_youngsters.xlsx'
if 'df_big5_filter' in locals(): 
    # save
    df_big5_filter.to_excel(path_big5, index=False)
else: 
    # load
    df_big5_filter = pd.read_excel(path_big5)

path_tm = folder+'transfermarkt.xlsx'
if 'df_tm' in locals():
    pass
else:
    df_tm = pd.read_excel(path_tm)

path_tcdb = folder+'df_tcdb.xlsx'
if 'df_tcdb' in locals():
    pass
else:
    df_tcdb = pd.read_excel(path_tcdb)

path_rookiecards = folder+'rookie_cards_df.csv'
if 'rookie_cards_df' in locals():
    pass
else:
    rookie_cards_df = pd.read_csv(path_rookiecards)
    
path_sets = folder+'tcdb_sets.csv'
if 'df_tcdb_sets' in locals():
    pass
else:
    df_tcdb_sets = pd.read_csv(path_sets) 
    
path_ebay = folder+'df_ebay.csv'
if 'df_ebay' in locals():
    pass
else:
    df_ebay = pd.read_csv(path_ebay)

#%% Functions: Search players on tcdb
def find_tcdb_player_url(player_name):
    searchterm_player = player_name.replace(' ', '+')
    url_tcdb = f'https://www.tcdb.com/Search.cfm?SearchCategory=Soccer&cx=partner-pub-2387250451295121%3Ahes0ib-44xp&cof=FORID%3A10&ie=ISO-8859-1&q={searchterm_player}'
    
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url_tcdb)
    a_elements = driver.find_elements(By.TAG_NAME, "a")
    # Find urls
    for a in a_elements:
        href = a.get_attribute("href")
        if pd.isna(href) == False:
            if ('Person.cfm' in href): # first one = right one for us
                url_tcdb_player = href
                print(f'Player tcdb url: {url_tcdb_player}')
                break
    driver.quit()
    return url_tcdb_player

def rookie_pages_number(tcdb_id, player_tcdb, season_short):
    from urllib.parse import urlparse, parse_qs
    url_rookie = f'https://www.tcdb.com/Person.cfm/pid/{tcdb_id}/col/1/yea/{season_short}/{player_tcdb}?sTeam=&sCardNum=&sNote=&sSetName=&sBrand='
    
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url_rookie)
    time.sleep(5)
    try:
        pagination_links = driver.find_elements(By.CSS_SELECTOR, 'a.page-link')
        last_page_elem = next((el for el in pagination_links if el.text.strip() == '»'), None)

        if last_page_elem:
            last_page_href = last_page_elem.get_attribute('href')
            parsed_url = urlparse(last_page_href)
            query_params = parse_qs(parsed_url.query)
            max_page = int(query_params.get('PageIndex', [1])[0])
        else:
            max_page = 1
    except Exception as e:
        print(f'Error: {e}')
        max_page = 1

    print(f'Number of pages: {max_page}')
    
    driver.quit()
    return max_page

def find_first_tcdb_season(tcdb_id):
    url_rookie = f'https://www.tcdb.com/Person.cfm/pid/{tcdb_id}/col/1/'
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url_rookie)
    time.sleep(5)
    seasons = []
    try:
        div = driver.find_element(By.CSS_SELECTOR, 'div.d-none.d-md-block')
        anchors = div.find_elements(By.TAG_NAME, 'a')
        
        for a in anchors:
            season_text = a.text.strip()
            if season_text:
                seasons.append(season_text)
    except Exception as e:
        print(f'Error: {e}')

    driver.quit()
    return seasons[0]

def find_tcdb_rookie_cards(tcdb_id, player_tcdb, season_short, page_nr):
    url_rookie = f"https://www.tcdb.com/Person.cfm/pid/{tcdb_id}/col/1/yea/{season_short}/{player_tcdb}?PageIndex={page_nr}&sTeam=&sCardNum=&sNote=&sSetName=&sBrand="
    
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url_rookie)
    time.sleep(5)
    
    td_elements = driver.find_elements(By.CSS_SELECTOR, 'td.vertical')
    # Find urls
    url_df= pd.DataFrame()
    for td in td_elements:
        a_tag = td.find_element(By.TAG_NAME, 'a') if td.find_elements(By.TAG_NAME, 'a') else None
        if a_tag:
            href = a_tag.get_attribute("href")
            if 'ViewCard.cfm' in href:
                card_text = a_tag.text.strip()
                full_td_text = td.text.strip()  # Ebben lehet a ritkaság pl. "Fireworks Red"
                # Próbáld kivenni belőle a ritkaságot, ha van
                extra_info = full_td_text.replace(card_text, '').strip()

                new_row = len(url_df)
                url_df.loc[new_row, 'tcdb_id'] = tcdb_id
                url_df.loc[new_row, 'season'] = first_tcdb_season
                url_df.loc[new_row, 'card_url'] = href
                url_df.loc[new_row, 'card_text'] = card_text
                url_df.loc[new_row, 'extra'] = extra_info
    
    url_df = url_df[url_df.card_text != '']
    print(f'Number of cards found: {len(url_df)}')
    driver.quit()
    return url_df

# Find manufacturer, set_name, card_number, autograph, memo, rarity(SN)
manufacturers = ['Donruss', 'Merlin', 'Topps', 'Panini', 'Futera', 'Score', 'Bowman']
def extract_manufacturer(text):
    for m in manufacturers:
        if m.lower() in text.lower():
            return m
    return 'Unknown' 

def format_card_data(url_df):
    ## tcdb IDs
    url_ends = url_df['card_url'].str.split('sid/').str[-1].str.split('/')
    url_df['set_id'], url_df['card_id'] = url_ends.str[0], url_ends.str[2]
    
    
    ## set_name
    url_df['set_name'] = np.where(url_df['card_text'].str.contains(' - '),
                                  url_df['card_text'].str.split(' - ').str[0],
                                  url_df['card_text'].str.split('#').str[0])
    ## card_number
    url_df['card_nr'] = url_df['card_text'].str.split('#').str[1].str.split(' ').str[0]
    ## autograph
    url_df['auto'] = url_df.extra.str.contains('AU')
    ## memo
    url_df['memo'] = url_df.extra.str.contains('MEM')
    ## SN
    import re
    def extract_sn(text):
        match = re.search(r'\bSN(\d+)\b', str(text))
        if match:
            return int(match.group(1))
        return None
    
    url_df['SN'] = url_df['extra'].apply(extract_sn)

    return url_df

def parse_set_data(text, url):
    text = text.strip()
    url = url.strip()
    manu = extract_manufacturer(text)
    parallel = url.split('---')[1] if '---' in url else 'Base'
    parallel_clean = parallel.replace('-', ' ')
    set_short = text.replace(year, '')
    set_short = set_short.replace(manu, '') if manu != 'Unknown' else set_short
    set_short = set_short.strip()
    
    return manu, set_short, parallel_clean  

#%% create dataframe for players' tcdb data
"""
tcdb_list = []
for i in df_big5_filter[0:40].index:
    player_name = df_big5_filter.loc[i, 'Player']
    url_tcdb_player = find_tcdb_player_url(player_name)
    player_tcdb = url_tcdb_player.split('/')[-1]
    tcdb_id = url_tcdb_player.split('pid/')[-1].split('/')[0]
    
    tcdb_dict_player = {'player_fbref': player_name,
                        'player_tcdb': player_tcdb,
                        'tcdb_id': int(tcdb_id),
                        'url': url_tcdb_player,
                        'first_season': '',
                        'pages_nr': 0
                        }
    tcdb_list.append(tcdb_dict_player)

df_tcdb = pd.DataFrame(tcdb_list)
"""

#%% Get market value from Transfermarkt
def get_market_value(url_transfermarkt):
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url_transfermarkt)
    time.sleep(5)
    
    market_value_element = driver.find_element(By.CLASS_NAME, "data-header__market-value-wrapper")
    full_text = market_value_element.text
    
    if 'Last update:' in full_text:
        market_value, last_update = full_text.split("Last update:")
        market_value, last_update = market_value.strip(), last_update.strip()
        
        market_value_noeur = market_value.replace('€', '')
        if 'k' in market_value:
            market_value_float = float(market_value_noeur.replace('k', ''))
            market_value_mill = market_value_float / 1000
        elif 'm' in market_value:
            market_value_float = float(market_value_noeur.replace('m', ''))
            market_value_mill = market_value_float
        else:
            market_value_mill = None
            
        last_update_dt = pd.to_datetime(last_update).date()
    else:
        market_value_mill, last_update_dt = None, None
    
    driver.quit()
    
    return market_value_mill, last_update_dt

for i, row in df_tm[pd.notna(df_tm.url_tm)].iterrows():
    if row['MV'] == 0:
        print(row['player_fbref'])
        mv, last_upd = get_market_value(row['url_tm'])
        print(f'Market value: {mv}')
        print('')
        df_tm.loc[i,['MV', 'update']] = mv, last_upd

df_tm.to_excel(path_tm, index=False)

#%% execute tcdb: Find player profile site
df_tcdb_slice = df_tcdb[20:30].copy()
for i in df_tcdb_slice.index:
    player_name = df_tcdb_slice.loc[i, 'player_fbref']
    print(player_name)
    row_tcdb = df_tcdb.iloc[i,:]
    player_tcdb, tcdb_id, url_tcdb_player, first_tcdb_season, pages_nr = row_tcdb[1:]
    
    rookie_cards_df_player = pd.DataFrame()
    for page_nr in range(1, pages_nr+1):
        rookie_url_df_page = find_tcdb_rookie_cards(tcdb_id, player_tcdb, first_tcdb_season, page_nr)
        # Fetch the data of these cards
        rookie_cards_df_page = format_card_data(rookie_url_df_page)
        rookie_cards_df_player = pd.concat([rookie_cards_df_player, rookie_cards_df_page], ignore_index=True)
    rookie_cards_df = pd.concat([rookie_cards_df, rookie_cards_df_player], ignore_index=True)
rookie_cards_df[['set_id', 'card_id']] = rookie_cards_df[['set_id', 'card_id']].astype(int)

rookie_cards_df = rookie_cards_df.drop_duplicates(subset=['card_id', 'card_text']).reset_index(drop=True)
rookie_cards_df.to_csv(path_rookiecards, index=False)

#%% Create dataframe of sets on tcdb
sets_list = []
for set_id in rookie_cards_df.set_id.unique():
    if set_id not in df_tcdb_sets.set_id.unique():
        set_name = rookie_cards_df[rookie_cards_df.set_id == set_id]['set_name'].iloc[0].strip()
        year = rookie_cards_df[rookie_cards_df.set_id == set_id]['season'].iloc[0]
        set_dict = {'set_id': set_id, 'set_name': set_name, 'year': year}
        sets_list.append(set_dict)
        
df_tcdb_sets_new = pd.DataFrame(sets_list)
df_tcdb_sets = pd.concat([df_tcdb_sets, df_tcdb_sets_new], ignore_index=True).drop_duplicates(subset='set_id', keep="first")   
print(f'New sets found: {len(df_tcdb_sets_new)}')

print(f'Missing set urls: {len(df_tcdb_sets[pd.isna(df_tcdb_sets.url)])}/{len(df_tcdb_sets)}')
# find base sets for every year
for year_set in range(2020, 2025):
    year_set = str(year_set)
    df_tcdb_sets_year = df_tcdb_sets[df_tcdb_sets.year.str.split('-').str[0] == year_set]
    url_sets_year = f'https://www.tcdb.com/ViewAll.cfm/sp/Soccer/year/{year_set}'
    
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url_sets_year)
    time.sleep(5)
    
    a_elements = driver.find_elements(By.TAG_NAME, "a")
    
    for a in a_elements:
        href = a.get_attribute("href")
        text = a.text
        if pd.notna(href):
            # find urks with 'viewset'
            if 'ViewSet.cfm/' in href:
                set_id_url = int(href.split('sid/')[1].split('/')[0])
                # check if set_id in dataframe
                if (set_id_url in df_tcdb_sets_year.set_id.unique()):
                    # find row and fill in url
                    row_tcdb_set = df_tcdb_sets[df_tcdb_sets.set_id == set_id_url]
                    if pd.isna(row_tcdb_set['url'].iloc[0]):
                        row_index = row_tcdb_set.index[0]
                        df_tcdb_sets.loc[row_index, 'url'] = href
                        print(f'{set_id_url} found.')
                else:
                    continue
                            
    driver.quit()

df_tcdb_sets['base_set'] = np.where(df_tcdb_sets.url.str.contains('---'), False, True)

mask_base = df_tcdb_sets.base_set == True
df_tcdb_sets_base = df_tcdb_sets[mask_base]
for i in df_tcdb_sets_base.index:
    set_name = df_tcdb_sets.loc[i, 'set_name']
    set_id = df_tcdb_sets.loc[i, 'set_id']
    url_set_ins = f'https://www.tcdb.com/Inserts.cfm/sid/{set_id}'
    mask_setname = df_tcdb_sets.set_name == set_name
    df_tcdb_sets_samename = df_tcdb_sets[mask_setname]
    if any(pd.isna(df_tcdb_sets_samename.url)):        
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url_set_ins)
        time.sleep(5)
        
        a_elements = driver.find_elements(By.TAG_NAME, "a")
        
        for a in a_elements:
            href = a.get_attribute("href")
            if pd.notna(href):
                if ('Checklist.cfm/sid/' in href) or ('ViewSet.cfm/sid/' in href):
                    set_id_url = int(href.split('sid/')[1][0:6])
                    # check if set_id in dataframe
                    if (set_id_url in df_tcdb_sets.set_id.unique()):
                        # find row and fill in url
                        row_tcdb_set = df_tcdb_sets[df_tcdb_sets.set_id == set_id_url]
                        if pd.isna(row_tcdb_set['url'].iloc[0]):
                            row_index = row_tcdb_set.index[0]
                            df_tcdb_sets.loc[row_index, 'url'] = href
                            print(f'{set_id_url} found.')
                    else:
                        continue
        
        driver.quit()

# drop if set_id doesn't match url
for i, row in df_tcdb_sets.iterrows():
    if pd.notna(row['url']):
        if str(row['set_id']) not in row['url']:
            df_tcdb_sets.loc[i, 'url'] = None
            
print(f'Still missing: {len(df_tcdb_sets[pd.isna(df_tcdb_sets.url)])}/{len(df_tcdb_sets)}')

# parse data
for i, row in df_tcdb_sets.iterrows():
    if pd.notna(row['url']) and pd.notna(row['set_name']):
        set_name, url = row['set_name'], row['url']
        df_tcdb_sets.loc[i, ['manufacturer', 'set_short', 'parallel']] = parse_set_data(set_name, url)

df_tcdb_sets = df_tcdb_sets.drop_duplicates(subset='set_id').reset_index(drop=True)
df_tcdb_sets.to_csv(path_sets, index=False)

#%% ebay functions: Search each on ebay -> create dataframe
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
        sellerinfo = item.find('span', {'class': 's-item__seller-info'})
        if pd.isna(sellerinfo):
            seller_name, seller_sales_new, seller_rating_nr = None, None, None
        else:
            seller_name, seller_sales, seller_rating = sellerinfo.text.split(' ')
            seller_sales_new = seller_sales.replace('(', '').replace(')', '').replace(' ', '').replace(',', '')
            seller_rating_nr = seller_rating.replace('%', '')
        product = {
            'title': item.find('div', {'class':'s-item__title'}).text,
            'soldprice': item.find('span', {'class': 's-item__price'}).text,
            'solddate': item.find('div', {'class': 's-item__caption'}).text.replace('Sold  ', '').strip(),
            'seller_name': seller_name,
            'seller_sales': seller_sales_new,
            'seller_rating': seller_rating_nr,
            'link': item.find('a', {'class': 's-item__link'})['href']
            }
        productslist.append(product)
    return productslist

def output(productslist):
    productsdf = pd.DataFrame(productslist)
    # Format table
    if any(productsdf['soldprice'].str.contains('$')):
        productsdf['soldprice_fact'] = productsdf['soldprice'].str.split(' to ').str[0].str.replace('$', '').str.replace(',', '').astype(float)
    productsdf['solddate_dt'] = pd.to_datetime(productsdf.solddate, format="%b %d, %Y")
    print(productsdf.title)
    return productsdf

def fetch_sold_items(searchterm, pages_nr=1):
    df_multi = pd.DataFrame()
    for page_num in range(1, pages_nr+1):
        soup = get_data(searchterm, page_num)
        productslist = parse(soup)
        df = output(productslist)
        df = df[df.title != 'Shop on eBay']
        df_multi = pd.concat([df_multi, df], ignore_index=True)
        time.sleep(random.uniform(2, 10))
    return df_multi

#%% ebay: find sold items
for i in df_tcdb_slice.index:
    player_name = df_tcdb_slice.loc[i, 'player_fbref']
    player_name_short = player_name.split(' ')[-1]
    print(f'Player: {player_name}')
    tcdb_id = df_tcdb.loc[i, 'tcdb_id']
    rookie_cards_df_player = rookie_cards_df[rookie_cards_df.tcdb_id == tcdb_id].copy()
    first_tcdb_season = rookie_cards_df_player.season.unique()[0]
    if pd.notna(first_tcdb_season):
        df_ebay_player = pd.DataFrame()
        set_ids = pd.Series(rookie_cards_df_player.set_id).to_list()
        manufacturers_player = df_tcdb_sets[df_tcdb_sets.set_id.isin(set_ids) & pd.notna(df_tcdb_sets.manufacturer)].manufacturer.unique()
        for manufacturer in manufacturers_player:
            searchterm =  f'{first_tcdb_season} {manufacturer} {player_name}'
            pages_nr = 3
            
            df_ebay_set = fetch_sold_items(searchterm, pages_nr)
            df_ebay_player = pd.concat([df_ebay_player, df_ebay_set], ignore_index=True)
        
        if len(df_ebay_player) != 0:
            df_ebay_player.drop_duplicates(subset='title')
            df_ebay_player.dropna(subset='title', inplace=True)
            df_ebay_player = df_ebay_player[df_ebay_player['title'].str.contains(player_name_short)]
            df_ebay_player = df_ebay_player[df_ebay_player['title'].str.contains(first_tcdb_season)]
            df_ebay_player['tcdb_id'] = tcdb_id
        
        df_ebay = pd.concat([df_ebay, df_ebay_player], ignore_index=True)
df_ebay.drop_duplicates(subset=['title', 'solddate', 'seller_name', 'soldprice'], inplace=True)
df_ebay.to_csv(path_ebay, index=False)

#%% Functions: matching cards with ebay sales
def tokenize(title):
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)
    return title.split()

def detect_partial_matches(title_tokens, keywords):
    matches = []
    for kw in keywords:
        if any(kw.lower() in token for token in title_tokens):
            matches.append(kw)
    return matches

def score_row(title, set_short, auto, memo, sn, card_nr, parallel):
    score = 0
    title_lower = title.lower()
    title_tokens = tokenize(title_lower)
    
    # 0) Set short
    if pd.notna(set_short):
        set_tokens = tokenize(set_short)
        matches = detect_partial_matches(title_tokens, set_tokens)
        if matches:
            ratio = len(matches) / len(set_tokens)
            set_score = int(20 * ratio)
            score += set_score
    
    # 1) Autograph
    if auto and any(kw in title_lower for kw in ['auto', 'autograph', 'signatures']):
        score += 10

    # 2) Memorabilia 
    if memo and any(kw in title_lower for kw in ['memo', 'patch', 'jersey']):
        score += 10

    # 3) SN 
    if pd.notna(sn):
        sn_str = str(int(sn))
        if f"sn{sn_str}" in title_lower or f"#{sn_str}" in title_lower or f'/{sn_str}':
            score += 10

    # 4) Card number 
    if pd.notna(card_nr):
        card_nr_str = card_nr
        if f"#{card_nr_str}" in title or f"card #{card_nr_str}" in title_lower:
            score += 10
    
    # 5) Parallel
    if pd.notna(parallel):
       parallel_tokens = tokenize(parallel)
       matches = detect_partial_matches(title_tokens, parallel_tokens)
       
       if matches:
           ratio = len(matches) / len(parallel_tokens)
           parallel_score = int(15 * ratio)
           score += parallel_score

    return score

#%% Execute: matching cards with ebay sales
for i_ebay in df_ebay.index:
    title_lower = str(df_ebay.loc[i_ebay, 'title']).lower()
    best_score = 0
    best_idx = None
    best_cardid = None
    
    searched_player_id = df_ebay.loc[i_ebay, 'tcdb_id']
    rookie_cards_df_player = rookie_cards_df[rookie_cards_df.tcdb_id == searched_player_id]

    for i_rc, row_rc in rookie_cards_df_player.iterrows():
        set_id = row_rc['set_id']
        card_text = str(row_rc['card_text'])
        card_nr, auto, memo, sn = row_rc[['card_nr', 'auto', 'memo', 'SN']]
        if set_id in df_tcdb_sets.set_id.values:
            row_set = df_tcdb_sets[df_tcdb_sets.set_id == set_id]
            set_short = row_set['set_short'].iloc[0]
            parallel = row_set['parallel'].iloc[0]
        else:
            continue

        # Manufacturer filtering
        if not any(manu.lower() in title_lower and manu.lower() in card_text.lower() for manu in manufacturers):
            continue
        
        if (pd.isna(title_lower) or pd.isna(set_short) or pd.isna(auto) or pd.isna(memo) 
            or pd.isna(sn) or pd.isna(card_nr) or pd.isna(parallel)):
            continue
        else:
            score = score_row(title_lower, set_short, auto, memo, sn, card_nr, parallel)

            if score > best_score:
                best_score = score
                best_idx = i_rc
                best_cardid = rookie_cards_df_player.loc[best_idx, 'card_id']

    if best_idx is not None:
        df_ebay.at[i_ebay, 'matched_text']  = rookie_cards_df_player.at[best_idx, 'card_text']
        df_ebay.at[i_ebay, 'match_score']   = best_score
        df_ebay.at[i_ebay, 'card_id'] = best_cardid

print(f'Cards over match score 25: {len(df_ebay[df_ebay.match_score>25])}/{len(df_ebay)}')
print(df_ebay.match_score.describe())

df_ebay.drop_duplicates(subset=['title', 'solddate', 'seller_name', 'soldprice'], inplace=True)
df_ebay.to_csv(path_ebay, index=False)

#%% Build machine learning model: Price Prediction
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Models
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor

# 1. Adatok összefűzése
df = pd.merge(df_ebay, rookie_cards_df, on='card_id', suffixes=('', '_replace'))
df = pd.merge(df, df_tcdb_sets, on='set_id', suffixes=('', '_replace'))
df = pd.merge(df, df_tcdb, on='tcdb_id', suffixes=('', '_replace'))
df = pd.merge(df, df_big5_filter, left_on='player_fbref', right_on='Player', suffixes=('', '_replace'))
df = pd.merge(df, df_tm, on='tcdb_id', suffixes=('', '_replace'))
df.drop(columns=[col for col in df.columns if '_replace' in col], inplace=True)

df = df[(df['soldprice_fact'] > 0) & (df['soldprice_fact'] < 100)]

# 2. Feature engineering
df['SN'] = pd.to_numeric(df['SN'], errors='coerce').fillna(10000)
def categorize_rarity(value):
    if value > 200:
        return 'Common'
    elif 200 >= value > 15:
        return 'Rare'
    elif 15 >= value > 0:
        return 'Legendary'
    else:
        return 'Unknown'
df['SN_cat'] = df['SN'].apply(categorize_rarity)

df['auto'] = df['auto'].map({True: 1, False: 0})
df['memo'] = df['memo'].map({True: 1, False: 0})
df['solddate_dt'] = pd.to_datetime(df['solddate_dt'], format='mixed')
df['sold_year'] = df['solddate_dt'].dt.year
df['sold_month'] = df['solddate_dt'].dt.month
df['seller_sales'] = df['seller_sales'].apply(lambda x: np.log1p(x))
df['MV/SN'] = df.MV / df.SN


y = np.log1p(df['soldprice_fact'].astype(float))

stats = [col for col in df_big5_filter.columns if df_big5_filter[col].dtype == 'float64'][:-3]

which_feature = 'most_important'
if which_feature == 'all':
    features = [
        'Age_float', 'Comp',
        'SN', 'auto', 'memo',
        'seller_sales', 'seller_rating',
        'sold_year', 'sold_month', 'manufacturer',
        'MV', 'MV/SN'
    ] + stats

    cat_features = ['manufacturer', 'Comp']
    num_features = [col for col in features if col not in cat_features]
    
elif which_feature == 'most_important':
    features = ['seller_sales', 'seller_rating', 'SN', 'auto', 'sold_month', 
                'Per 90 Minutes_Ast', 'Expected_npxG+xAG', 'Expected_xAG', 
                'MV', 'MV/SN', 'manufacturer']
    cat_features = ['manufacturer']
    num_features = [col for col in features if col not in cat_features]

X = df[features]

# 3. Preprocessing
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), num_features),
    ('cat', OneHotEncoder(handle_unknown='ignore'), cat_features)
])

# 4. Modellek definiálása
state = 2

best_rf = RandomForestRegressor(
    n_estimators=200,
    max_depth=10,
    max_features='sqrt',
    min_samples_split=2,
    min_samples_leaf=1,
    random_state=state
)

models = {
    "Ridge": Ridge(alpha=1.0),
    "Random Forest": best_rf,
    "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=state),
    "Neural Net": MLPRegressor(hidden_layer_sizes=(200, 100, 50), max_iter=1000, learning_rate_init=0.0005, random_state=state)
}

# 5. Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=state)

# 6. Modell lefuttatás és értékelés
results = []

for name, model in models.items():
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', model)
    ])
    
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    # Inverz transzformáció
    y_pred_exp = np.expm1(y_pred)
    y_test_exp = np.expm1(y_test)
    
    # Értékelés
    mae = mean_absolute_error(y_test_exp, y_pred_exp)
    rmse = np.sqrt(mean_squared_error(y_test_exp, y_pred_exp))
    r2 = r2_score(y_test_exp, y_pred_exp)
    
    results.append({
        "Model": name,
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2
    })

# 7. Eredmények kiírása
results_df = pd.DataFrame(results).sort_values("RMSE")
print(results_df)

#%% Pred vs Actual plot
import seaborn as sns
import matplotlib.pyplot as plt

sns.scatterplot(x=y_test_exp, y=y_pred_exp)
plt.xscale('log')
plt.yscale('log')
plt.xlabel("Actual Price")
plt.ylabel("Predicted Price")
plt.title("Predicted vs Actual (Log scale)")
plt.plot([y_test_exp.min(), y_test_exp.max()], [y_test_exp.min(), y_test_exp.max()], 'r--')
plt.show()

#%% Error histogram
errors = y_test_exp - y_pred_exp
plt.hist(errors, bins=50)
plt.xlabel("Prediction Error")
plt.title("Prediction Error Distribution")
plt.show()

#%% SHAP
import shap

# Preprocessing pipeline külön: előfeldolgozott adat kell
X_transformed = preprocessor.fit_transform(X_train)
model = models["Random Forest"]
model.fit(X_transformed, y_train)

# SHAP TreeExplainer csak tree alapú modellekhez
explainer = shap.Explainer(model)
shap_values = explainer(X_transformed)

# 1. Globális fontosság - Summary plot
shap.summary_plot(shap_values, X_transformed, feature_names=features)

#%% Crossval
from sklearn.model_selection import cross_val_score

for name, model in models.items():
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('regressor', model)
    ])
    scores = cross_val_score(pipeline, X, y, cv=5, scoring='r2')
    print(f"{name}: R2 mean={scores.mean():.4f}, std={scores.std():.4f}")

#%% Feature importance
import matplotlib.pyplot as plt

# Kiválasztott modell: pl. Random Forest
model_name = "Random Forest"
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('regressor', models[model_name])
])
pipeline.fit(X_train, y_train)

# Feature nevek kibontása
ohe = pipeline.named_steps['preprocessor'].named_transformers_['cat']
cat_feature_names = ohe.get_feature_names_out(cat_features)
feature_names = num_features + list(cat_feature_names)

# Feature importance
importances = pipeline.named_steps['regressor'].feature_importances_

# Top 20 fontos változó
indices = np.argsort(importances)[::-1][:5]
plt.figure(figsize=(10, 6))
plt.title(f"{model_name} - Top 5 Feature Importance")
plt.barh(np.array(feature_names)[indices][::-1], importances[indices][::-1])
plt.xlabel("Importance")
plt.tight_layout()
plt.show()

#%% Hyperparam tuning
from sklearn.model_selection import GridSearchCV

# Pipeline újra definiálása
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(random_state=state))
])

# Paraméterrács
param_grid = {
    'regressor__n_estimators': [100, 200, 300],
    'regressor__max_depth': [None, 10, 20],
    'regressor__min_samples_split': [2, 5],
    'regressor__min_samples_leaf': [1, 2],
    'regressor__max_features': ['sqrt', 'log2']
}

# Grid search
grid_search = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,
    scoring='neg_mean_squared_error',
    n_jobs=-1,  # párhuzamosítás, ha van több magod
    verbose=2
)

# Illesztés
grid_search.fit(X_train, y_train)

# Legjobb modell
best_model = grid_search.best_estimator_

# Predikció
y_pred = best_model.predict(X_test)
y_pred_exp = np.expm1(y_pred)
y_test_exp = np.expm1(y_test)

# Kiértékelés
mae = mean_absolute_error(y_test_exp, y_pred_exp)
rmse = np.sqrt(mean_squared_error(y_test_exp, y_pred_exp))
r2 = r2_score(y_test_exp, y_pred_exp)

print(f"Best Params: {grid_search.best_params_}")
print(f"MAE: {mae:.2f}, RMSE: {rmse:.2f}, R2: {r2:.3f}")


#%% ML model: Price to increase or not
import pandas as pd

df['player_sncat'] = df[['player_fbref', 'SN_cat']].astype(str).agg('|'.join, axis=1)
df['solddate_dt'] = pd.to_datetime(df['solddate_dt'])
df = df.sort_values(['player_sncat', 'solddate_dt'])

from tqdm import tqdm

# Feltételezzük, hogy minden sor egy konkrét eladás
future_avg_prices = []

# Ciklus minden sorra
for idx, row in tqdm(df.iterrows(), total=len(df)):
    player = row['player_sncat']
    curr_date = row['solddate_dt']
    
    # Szűrés: ugyanazon játékos eladásai 0-90 nappal később
    future_sales = df[
        (df['player_sncat'] == player) &
        (df['solddate_dt'] > curr_date) &
        (df['solddate_dt'] <= curr_date + pd.Timedelta(days=90))
    ]
    
    # Átlagos jövőbeli ár
    if not future_sales.empty:
        avg_price = future_sales['soldprice_fact'].mean()
    else:
        avg_price = None
    
    future_avg_prices.append(avg_price)

df['future_avg_price_3m'] = future_avg_prices

# Label: emelkedett az ár?
df['price_increase'] = (
    df['future_avg_price_3m'] > df['soldprice_fact']
).astype(int)

print(df.groupby('price_increase').price_increase.count())

features = [
    'SN', 'MV',
    'Performance_Gls', 'Performance_Ast', 'Expected_xG', 'Expected_xAG',
    'Per 90 Minutes_Gls', 'Per 90 Minutes_xG', 
    'manufacturer', 'Pos', 'Age_float'
]

print(df[['soldprice_fact', 'future_avg_price_3m']].corr())

#%% MLclass fitting
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# Szétválasztás
X = df[features]
y = df['price_increase']


# Előfeldolgozás
categorical = ['manufacturer', 'Pos']
numerical = list(set(features) - set(categorical))

preprocessor = ColumnTransformer(transformers=[
    ('num', 'passthrough', numerical),
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical)
])

# Modell pipeline
clf = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=227, max_depth=10,
                                          max_features='log2', min_samples_leaf=4,
                                          min_samples_split=2, random_state=1, 
                                          class_weight='balanced'))
])

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Tanítás
clf.fit(X_train, y_train)

#%% MLclass matrix, report
from sklearn.metrics import classification_report, confusion_matrix

y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))

#%% MLclass feature importance
import numpy as np
import matplotlib.pyplot as plt

# 1. Modell és preprocessor kiszedése a pipeline-ból
model = clf.named_steps['classifier']
preprocessor = clf.named_steps['preprocessor']

# 2. Kódolt feature nevek (numerikus + OHE kategóriák)
num_features = preprocessor.transformers_[0][2]  # 'num' rész
cat_features = preprocessor.transformers_[1][1].get_feature_names_out(preprocessor.transformers_[1][2])  # 'cat' rész

# 3. Összefűzés
all_features = np.concatenate([num_features, cat_features])

# 4. Importance sorrendben
importances = model.feature_importances_
indices = np.argsort(importances)[::-1]

# 5. Kiíratás vagy ábra
for i in range(10):  # top 10
    print(f"{i+1}. {all_features[indices[i]]}: {importances[indices[i]]:.4f}")

# 6. Opcionálisan ábra
plt.figure(figsize=(10, 6))
plt.title("Top 10 Feature Importances")
plt.bar(range(10), importances[indices[:10]])
plt.xticks(range(10), all_features[indices[:10]], rotation=45, ha='right')
plt.tight_layout()
plt.show()

#%% MLclass tuning
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint

# Paraméterrács
param_dist = {
    'classifier__n_estimators': randint(100, 500),
    'classifier__max_depth': [None, 5, 10, 20, 30],
    'classifier__min_samples_split': randint(2, 10),
    'classifier__min_samples_leaf': randint(1, 10),
    'classifier__max_features': ['auto', 'sqrt', 'log2'],
    'classifier__bootstrap': [True, False]
}

# RandomSearch setup
random_search = RandomizedSearchCV(
    clf,                # pipeline
    param_distributions=param_dist,
    n_iter=50,          # próbálkozások száma
    cv=5,               # 5-fold cross-validation
    scoring='f1',       # vagy: 'accuracy', 'roc_auc', stb.
    verbose=2,
    random_state=42,
    n_jobs=-1           # párhuzamos futtatás
)

# Fit
random_search.fit(X_train, y_train)

print("Best parameters:", random_search.best_params_)
print("Best CV score:", random_search.best_score_)

# A legjobb modellt elmented
best_model = random_search.best_estimator_

# Teszten megnézed a teljesítményét
from sklearn.metrics import classification_report, confusion_matrix

y_pred_best = best_model.predict(X_test)
print(classification_report(y_test, y_pred_best))
print(confusion_matrix(y_test, y_pred_best))
