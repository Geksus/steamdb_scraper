import csv
import json
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
import lxml

headers = ['steam_appid', 'Name', 'Type', 'url', 'User score', 'Description', 'Supported languages', 'website', 'minimum_pc_requirements', 'recommended_pc_requirements', 'minimum_mac_requirements', 'recommended_mac_requirements', 'minimum_linux_requirements', 'recommended_linux_requirements', 'Developers', 'Publishers', 'Price', 'Currently playing']
all_games = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
all_games_response = requests.get(all_games)
if all_games_response.status_code == 200:
    game_ids = [game_id['appid'] for game_id in all_games_response.json()['applist']['apps']]

with open('all_game_ids.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for game_id in game_ids:
        writer.writerow([game_id])

with open('all_game_ids.csv', 'r') as f:
    reader = csv.reader(f)
    game_ids = sorted([i[0] for i in reader if i != []])

with open('used_ids.csv', 'r') as f:
    reader = csv.reader(f)
    used_ids = sorted([i[0] for i in reader if i != []])
steam_game_urls = [f'https://store.steampowered.com/app/{id}' for id in game_ids if id not in used_ids]


def parse_steam_data(url):
    with open('used_ids.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([url.split("/")[-1]])
    temp = {
        'steam_appid': '',
        'Name': '',
        'Type': '',
        'url': '',
        'User score': 0.0,
        'Description': '',
        'Supported languages': '',
        'website': '',
        'minimum_pc_requirements': '',
        'recommended_pc_requirements': '',
        'minimum_mac_requirements': '',
        'recommended_mac_requirements': '',
        'minimum_linux_requirements': '',
        'recommended_linux_requirements': '',
        'Developers': '',
        'Publishers': '',
        'Price': '',
        'Currently playing': 0
    }
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    try:
        temp['steam_appid'] = url.split("/")[-1]
    except:
        temp['steam_appid'] = ''
    try:
        temp['Name'] = soup.find('div', {'class': 'apphub_AppName'}).text
    except:
        temp['Name'] = ''
    # temp['Type'] = soup.find('div', {'class': 'apphub_AppName'}).find_next('b').text
    try:
        temp['url'] = url
    except:
        temp['url'] = ''

    try:
        all_reviews = soup.select('#review_summary_num_reviews')
        int_all_reviews = int(str(all_reviews).split('value=')[-1].split('"')[1])
        positive_reviews = soup.select('#review_summary_num_positive_reviews')
        int_positive_reviews = int(str(positive_reviews).split('value=')[-1].split('"')[1])
        temp['User score'] = round((int_positive_reviews / int_all_reviews) * 100, 2)
    except:
        temp['User score'] = 0.0
    try:
        description = soup.find('div', {'class': 'game_description_snippet'}).text
        temp['Description'] = description.replace('\t', '').replace('\r', '').replace('\n', '')
    except:
        temp['Description'] = ''
    try:
        supported_languages = soup.find('table', {'class': 'game_language_options'}).find_all('td', class_='ellipsis')
        temp['Supported languages'] = ', '.join([i.text.replace('\r', '').replace('\n', '').replace('\t', '') for i in supported_languages])
    except:
        temp['Supported languages'] = ''
    try:
        temp['website'] = soup.find('a', {'class': 'linkbar'}).get('href')
    except:
        temp['website'] = ''

    try:
        pc_requirements = soup.select('[data-os="win"]')
        for i in pc_requirements:
            temp['minimum_pc_requirements'] = i.text.strip().replace('\t', '').replace('\r', '').replace('\n', '').split('Recommended:')[0]
            temp['recommended_pc_requirements'] = i.text.strip().replace('\t', '').replace('\r', '').replace('\n', '').split('Recommended:')[-1]
    except:
        temp['minimum_pc_requirements'] = ''
        temp['recommended_pc_requirements'] = ''
    try:
        mac_requirements = soup.select('[data-os="mac"]')
        for i in mac_requirements:
            temp['minimum_mac_requirements'] = i.text.strip().replace('\t', '').replace('\r', '').replace('\n', '').split('Recommended:')[0]
            temp['recommended_mac_requirements'] = i.text.strip().replace('\t', '').replace('\r', '').replace('\n', '').split('Recommended:')[-1]
    except:
        temp['minimum_mac_requirements'] = ''
        temp['recommended_mac_requirements'] = ''
    try:
        linux_requirements = soup.select('[data-os="linux"]')
        for i in linux_requirements:
            temp['minimum_linux_requirements'] = i.text.strip().replace('\t', '').replace('\r', '').replace('\n', '').split('Recommended:')[0]
            temp['recommended_linux_requirements'] = i.text.strip().replace('\t', '').replace('\r', '').replace('\n', '').split('Recommended:')[-1]
    except:
        temp['minimum_linux_requirements'] = ''
        temp['recommended_linux_requirements'] = ''
    try:
        developers = soup.find('div', {'id': 'developers_list'}).find_all('a')
        temp['Developers'] = ', '.join([i.text for i in developers])
    except:
        temp['Developers'] = ''
    try:
        publishers = soup.find('div', class_='glance_ctn_responsive_left').find_all('a')
        temp['Publishers'] = ', '.join([i.text for i in publishers if 'publisher' in i['href']])
    except:
        temp['Publishers'] = ''

    try:
        price = soup.find('div', {'class': 'game_purchase_price price'}).text
        temp['Price'] = price.replace('\t', '').replace('\r', '').replace('\n', '')
    except:
        temp['Price'] = ''

    if 'English' in temp['Supported languages'] or 'Polish' in temp['Supported languages']:
        with open('steam_data.csv', 'a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writerow(temp)

    print(f'Parsed {url}')
    print(f'Items left: {len(steam_game_urls) - steam_game_urls.index(url)}')


def scraper():
    with ThreadPoolExecutor(max_workers=16) as executor:
        executor.map(parse_steam_data, steam_game_urls)


scraper()
