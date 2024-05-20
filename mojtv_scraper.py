from bs4 import BeautifulSoup
import requests
import re

mojtv_cat = {'/controlimg/program/k6.gif': 'serija', '/controlimg/program/k5.gif': 'film', '/controlimg/program/k2.gif': 'sport'}

additional_day_urls = []

mojtv_url = "https://mojtv.hr/m2/tv-program/"

def get_channels():

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"
    }

    page = requests.get(mojtv_url, headers=headers).text
    soup = BeautifulSoup(page, 'html.parser')

    soup_channel_table = soup.find("div", {"class": "ui-body-b"}).find("ul").find_all("li")

    channel_urls = []

    for channel in soup_channel_table:
        channel_urls.append( mojtv_url + channel.find("a").get("href") )

    return channel_urls


def get_prog_data(url):

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"
    }

    page = requests.get(url, headers=headers).text
    soup = BeautifulSoup(page, 'html.parser')

    ##

    if 'datum=' not in url:

        other_dates_urls = []

        soup_dates_table = soup.find("ul", {"id": "btn1_list"}).find_all("li")

        for date_li in soup_dates_table:
            date_url = date_li.find("a").get("href")
            other_dates_urls.append(mojtv_url + date_url)

        other_dates_urls.pop(0)

        global additional_day_urls

        additional_day_urls.extend(other_dates_urls)

    ##

    soup_programme_table = soup.find("div", {"class": "ui-body-b"}).find("ul").find_all("li")

    prog_data = {}

    for programme in soup_programme_table:
        title = programme.find("a").find("b").text
        subtitle = programme.find("a").find("em").text
        try:
            category_raw = programme.find("span", {'class': 'show-category'}).find("img").get("src")
        except:
            category_raw = " "
        try:
            img = programme.find("a").find("img").get("src")
        except:
            img = " "

        ##

        short_title = " ".join(title.split(" ")[:4])

        ##

        larger_img = img.replace("w=150", "w=360")

        ##

        categories = [mojtv_cat.get(category_raw)]
        if any(x in title.lower() for x in ['vijesti', 'dnevnik', 'rtl danas', 'vrijeme']):
            categories.append('informativni')
        categories.extend( subtitle.split(" ") )
        categories = list(set(filter(None, categories)))

        ##

        start_time_raw = programme.find("span", {"class": "show-time"}).find("b").text
        start_time = start_time_raw.replace(":", "")

        ##

        season_episode_search = re.search(r'S([0-9]+) E([0-9]+)', subtitle)
        # season_episode_search_2 = re.search(r'\(([0-9]+)\/([0-9]+)\)', subtitle)

        if season_episode_search:
            se_num = season_episode_search.group(1)
            ep_num = season_episode_search.group(2)
            
            episode_num = "S{s}E{e}".format(s=se_num, e=ep_num)
            episode_num_system = "SxxExx"
        
        # elif season_episode_search_2:
        #     ep_num = int(season_episode_search_2.group(1)) - 1
        #     ep_left = int(season_episode_search_2.group(2)) - 1
            
        #     episode_num = ".{en}/{el}.".format(en=ep_num, el=ep_left)
        #     episode_num_system = "xmltv_ns"
        
        else:
            episode_num = " "
            episode_num_system = " "

        ##

        prog_data.update({short_title + start_time: { 'img': "https:" + larger_img, 'cat': categories, 'subt': subtitle, 'ep_num': [episode_num_system, episode_num] }})

    return prog_data


def scrape(channel_ids=[]):
    urls = get_channels()

    all_prog = {}

    for url in urls:
        channel_id = int(url.split("id=")[1])

        if channel_id in channel_ids or channel_ids == []:
            ch_prog_data = get_prog_data(url)
            
            all_prog.update(ch_prog_data)


    for url in additional_day_urls:
        channel_id = int(url.split("id=")[1])

        if channel_id in channel_ids or channel_ids == []:
            ch_prog_data = get_prog_data(url)
            
            all_prog.update(ch_prog_data)

    return all_prog