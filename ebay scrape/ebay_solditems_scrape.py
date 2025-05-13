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
#%% Save big5 database to Excel or load it
folder = 'other_projects/ebay scrape/'
path_big5 = folder+ 'big5_youngsters.xlsx'
if 'df_big5_filter' in locals(): 
    # save
    df_big5_filter.to_excel(path_big5, index=False)
else: 
    # load
    df_big5_filter = pd.read_excel(path_big5)

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
#%% execute tcdb: Find player profile site
path_tcdb = folder+'df_tcdb.csv'
if 'df_tcdb' in locals():
    pass
else:
    df_tcdb = pd.read_csv(path_tcdb)

path_rookiecards = folder+'rookie_cards_df.csv'
if 'rookie_cards_df' in locals():
    pass
else:
    rookie_cards_df = pd.read_csv(path_rookiecards)

for i in df_big5_filter[6:12].index:
    player_name = df_big5_filter.loc[i, 'Player']
    print(player_name)
    if player_name not in df_tcdb.player_fbref.values:
        url_tcdb_player = find_tcdb_player_url(player_name)
        player_tcdb = url_tcdb_player.split('/')[-1]
        tcdb_id = url_tcdb_player.split('pid/')[-1].split('/')[0] # Player id
        # Find first season
        first_tcdb_season = find_first_tcdb_season(tcdb_id)
        # Find rookie card URLs
        pages_nr = rookie_pages_number(tcdb_id, player_tcdb, first_tcdb_season)
    else:
        row_tcdb = df_tcdb[df_tcdb.player_fbref == player_name]
        player_tcdb, tcdb_id, url_tcdb_player, first_tcdb_season, pages_nr = row_tcdb.iloc[0][1:]
        
    rookie_cards_df_player = pd.DataFrame()
    for page_nr in range(1, pages_nr+1):
        rookie_url_df_page = find_tcdb_rookie_cards(tcdb_id, player_tcdb, first_tcdb_season, page_nr)
        # Fetch the data of these cards
        rookie_cards_df_page = format_card_data(rookie_url_df_page)
        rookie_cards_df_player = pd.concat([rookie_cards_df_player, rookie_cards_df_page], ignore_index=True)
    rookie_cards_df = pd.concat([rookie_cards_df, rookie_cards_df_player], ignore_index=True)
rookie_cards_df[['set_id', 'card_id']] = rookie_cards_df[['set_id', 'card_id']].astype(int)

#%% Create dataframe of sets on tcdb
path_sets = folder+'tcdb_sets.csv'
if 'df_tcdb_sets' in locals():
    pass
else:
    df_tcdb_sets = pd.read_csv(path_sets) 

sets_list = []
for set_id in rookie_cards_df.set_id.unique():
    if set_id not in df_tcdb_sets.set_id.unique():
        set_name = rookie_cards_df[rookie_cards_df.set_id == set_id]['set_name'].iloc[0].strip()
        year = rookie_cards_df[rookie_cards_df.set_id == set_id]['season'].iloc[0]
        set_dict = {'set_id': set_id, 'set_name': set_name, 'year': year}
        sets_list.append(set_dict)
df_tcdb_sets_new = pd.DataFrame(sets_list)
df_tcdb_sets = pd.concat([df_tcdb_sets, df_tcdb_sets_new], ignore_index=True).drop_duplicates(subset='set_id', keep="first")   

print(f'Missing set urls: {len(df_tcdb_sets[pd.isna(df_tcdb_sets.url)])}/{len(df_tcdb_sets)}')
base_set_list = []
for year_set in range(2020, 2025):
    year_set = str(year_set)
    url_sets_year = f'https://www.tcdb.com/ViewAll.cfm/sp/Soccer/year/{year_set}'
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url_sets_year)
    time.sleep(5)
    a_elements = driver.find_elements(By.TAG_NAME, "a")
    
    for i in df_tcdb_sets[df_tcdb_sets.year.str.split('-').str[0] == year_set].index:
        # only fetch if there is no url
        if pd.notna(df_tcdb_sets.loc[i, 'set_name']) and pd.isna(df_tcdb_sets.loc[i, 'url']):
            # Find urls
            for a in a_elements:
                href = a.get_attribute("href")
                text = a.text
                if pd.notna(href):
                    if 'ViewSet.cfm/' in href:
                        set_id_url = int(href.split('sid/')[1].split('/')[0])
                        base_set_list.append({'set_id':set_id_url, 'year_set': year_set, 'url':href})
                                
    driver.quit()
    
print(f'Still missing: {len(df_tcdb_sets[pd.isna(df_tcdb_sets.url)])}/{len(df_tcdb_sets)}')

for i_i, r_i in df_tcdb_sets[df_tcdb_sets.set_id.isin(set_id_url_dict.keys())].iterrows():
    set_id_insert = r_i['set_id']
    if f'{set_id_insert}/' in href:
        print(f'set found: {set_id_insert}')
        df_tcdb_sets.loc[i_i, 'url'] = href

# parse data
for i, row in df_tcdb_sets.iterrows():
    if pd.notna(row['url']) and pd.notna(row['set_name']):
        set_name, url = row['set_name'], row['url']
        df_tcdb_sets.loc[i, ['manufacturer', 'set_short', 'parallel']] = parse_set_data(set_name, url)

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
path_ebay = folder+'df_ebay.csv'
if 'df_ebay' in locals():
    pass
else:
    df_ebay = pd.read_csv(path_ebay)

df_ebay = pd.DataFrame()
for i in df_big5_filter[6:12].index:
    player_name = df_big5_filter.loc[i, 'Player']
    print(f'Player: {player_name}')
    tcdb_id = df_tcdb[df_tcdb.player_fbref == player_name]['tcdb_id'].unique()[0]
    rookie_cards_df_player = rookie_cards_df[rookie_cards_df.tcdb_id == tcdb_id].copy()
    first_tcdb_season = rookie_cards_df_player.season.unique()[0]
    if pd.notna(first_tcdb_season):
        df_ebay_player = pd.DataFrame({'player_fbref': []})
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
            df_ebay_player = df_ebay_player[df_ebay_player['title'].str.contains(player_name)]
            df_ebay_player = df_ebay_player[df_ebay_player['title'].str.contains(first_tcdb_season)]
            df_ebay_player['tcdb_id'] = tcdb_id
        
        df_ebay = pd.concat([df_ebay, df_ebay_player], ignore_index=True)
df_ebay.drop_duplicates(subset=['title', 'solddate', 'seller_name', 'soldprice'], inplace=True)

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

    if best_idx is not None:
        df_ebay.at[i_ebay, 'matched_text']  = rookie_cards_df_player.at[best_idx, 'card_text']
        df_ebay.at[i_ebay, 'match_score']   = best_score
        df_ebay.at[i_ebay, 'rookie_row_id'] = best_idx

print(f'Cards over match score 25: {len(df_ebay[df_ebay.match_score>25])}/{len(df_ebay)}')
print(df_ebay.match_score.describe())
        
# Dataframe: searchterm, card_id, playername, manufacturer, set name, year, 
# cardnumber, SN, PSA grade, +ebay data

#%% Save tables to xlsx
# read previous
prev_ebay = pd.read_csv(path_ebay)
prev_rookiecards = pd.read_csv(path_rookiecards)
prev_tcdb = pd.read_csv(path_tcdb)
prev_tcdb_sets = pd.read_csv(path_sets)
# merge
new_ebay = pd.concat([prev_ebay, df_ebay], ignore_index=True).drop_duplicates(subset=['title', 'seller_name', 'solddate_dt'])
new_rookiecards = pd.concat([prev_rookiecards, rookie_cards_df], ignore_index=True).drop_duplicates(subset=['card_text', 'card_url'])
if 'df_tcdb' in locals():
    new_tcdb = pd.concat([prev_tcdb, df_tcdb], ignore_index=True).drop_duplicates()
    new_tcdb.to_csv(path_tcdb, index=False)
    print(f"New rows (players): {len(df_tcdb)}")
new_tcdb_sets = pd.concat([prev_tcdb_sets, df_tcdb_sets], ignore_index=True).drop_duplicates

# save
new_ebay.to_csv(path_ebay, index=False)
new_rookiecards.to_csv(path_rookiecards, index=False)
new_tcdb_sets.to_csv(path_sets, index=False)
print(f"New rows (ebay): {len(df_ebay)}")
print(f"New rows (rookie cards): {len(rookie_cards_df)}")
print(f"New rows (sets): {len(df_tcdb_sets)}")
