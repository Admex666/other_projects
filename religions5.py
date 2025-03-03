from bs4 import BeautifulSoup
from selenium import webdriver 
import random
from other_projects import email_alert 
from datetime import datetime
import calendar

def get_soup(url):
    driver = webdriver.Chrome()
    driver.get(url)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    driver.close()
    
    return soup

#%% Get all soups
url_bible = 'https://www.bible.com/verse-of-the-day'
soup_bible = get_soup(url_bible)

url_quran = 'https://ayahaday.com/'
soup_quran = get_soup(url_quran)

url_buddh = 'https://www.brainyquote.com/authors/buddha-quotes'
soup_buddh = get_soup(url_buddh)

url_hind = 'https://www.beliefnet.com/faiths/hinduism/daily-hindu-quote.aspx'
soup_hind = get_soup(url_hind)

url_torah = 'https://www.chabad.org/dailystudy/default_cdo/jewish/Daily-Study.htm'
soup_torah = get_soup(url_torah)

end_of_link = soup_torah.find('div', class_='clearfix f-14 large_bottom_margin').find('a','href'==True).get('href')
url_torah_daily = f'https://www.chabad.org{end_of_link}' 
soup_torah_daily = get_soup(url_torah_daily)

#%% Bible
text = soup_bible.find('a', class_="w-full no-underline dark:text-text-dark text-text-light")
author = soup_bible.find('p', class_="dark:text-text-dark text-15 font-aktiv-grotesk uppercase font-bold mbs-2 text-gray-25")

verse_bible = f'{text.string} \n \n{author.string}'

out_bible = '\n \nBible \n---------------------------------------------------------------- \n' + verse_bible

#%% Quran
p_all = soup_quran.find_all('p')
for p in p_all:
    if p.get('class') != None:    
        if 'translation' in p.get('class')[0]:
            text_quran = p.string
h3_all = soup_quran.find_all('h3')
for h3 in h3_all:
    if h3.get('class') != None:    
        if 'surahEnglish' in h3.get('class')[0]:
            title_quran = h3.string

verse_quran = f'{title_quran} \n \n{text_quran}'

out_quran = '\n \nQuran \n---------------------------------------------------------------- \n' + verse_quran

#%% Buddhism
div_all = soup_buddh.find_all('div')
div_indices = []
for i, div in enumerate(div_all):
    if div.get('style') != None:
        if 'display: flex;justify-content: space-between' in div.get('style'):
            div_indices.append(i) # create a list of quote indices

# choose a random one
random_quote_index = div_indices[random.randint(0,len(div_indices)-1)]
text_buddh = div_all[random_quote_index].text

out_buddhism= '\n \nBuddhism \n---------------------------------------------------------------- \n' + text_buddh

#%% Hindu 
section = soup_hind.find('section', class_='daily-content box-border-decoration add-more-padding text-center')
text_hind = section.find('p').text
source_hind = section.find('div', class_='quote-source').text

verse_hind = f'{text_hind} \n{source_hind}'

out_hinduism = '\n \nHinduism \n---------------------------------------------------------------- \n' + verse_hind

#%% Torah
out_torah = '\n \nTorah \n---------------------------------------------------------------- \n'
table = soup_torah_daily.find('table', class_='Co_TanachTable lt-both')
verses = table.find_all('tr', class_='Co_Verse')

for v in verses:
    tds = v.find_all('td')
    for td in tds:
        if 'hebrew' not in str(td.get('class')):
            versetext = td.find_all('span', class_='co_VerseText')
            for v in versetext:
                out_torah += f'{v.text} \n'
                
#%% Send email
output = ''
for religion in ['bible', 'quran', 'buddhism', 'hinduism', 'torah']:
    output += globals()[f'out_{religion}']

today = datetime.today()
date_str = f'{today.day} {calendar.month_name[today.month]} {today.year}'

if __name__ == '__main__':
    email_alert.email_alert(f'Daily teachings, {date_str}', output, ['adam.jakus99@gmail.com', 'szatimi11@gmail.com'])
    print('E-mails were sent.')
