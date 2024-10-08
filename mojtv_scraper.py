from bs4 import BeautifulSoup
import requests
import re
from datetime import date, datetime, timedelta

mojtv_cat = {'/controlimg/program/k6.gif': 'serija', '/controlimg/program/k5.gif': 'film', '/controlimg/program/k2.gif': 'sport'}

additional_day_urls = []

mojtv_url = "https://mojtv.hr/"

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"
}

def get_channels():

    page = requests.get(mojtv_url + "m2/tv-program/", headers=headers).text
    soup = BeautifulSoup(page, 'html.parser')

    soup_channel_table = soup.find("div", {"class": "ui-body-b"}).find("ul").find_all("li")

    channel_urls = []

    for channel in soup_channel_table:
        channel_urls.append( mojtv_url + "m2/tv-program/" + channel.find("a").get("href") )

    return channel_urls


def get_ssn_ep(url_raw):

    url = mojtv_url + url_raw
    
    page = requests.get(url, headers=headers).text
    soup = BeautifulSoup(page, 'html.parser')

    try:
        raw_ssn_ep = soup.find("div", {"id": "ContentPlaceHolder1_epizoda"}).find("span").text
    except:
        raw_ssn_ep = ""

    return raw_ssn_ep


def get_prog_data(url, cid, ssn_ep_dd_ids):

    page = requests.get(url, headers=headers).text
    soup = BeautifulSoup(page, 'html.parser')

    ##

    if 'datum=' not in url:

        other_dates_urls = []

        soup_dates_table = soup.find("ul", {"id": "btn1_list"}).find_all("li")

        for date_li in soup_dates_table:
            date_url = date_li.find("a").get("href")
            other_dates_urls.append(mojtv_url + "m2/tv-program/" + date_url)

        other_dates_urls.pop(0)

        global additional_day_urls

        additional_day_urls.extend(other_dates_urls)

        url_date = date.today().strftime("%Y%m%d")

    else:
        url_date_raw = url.split("datum=")[1].split("&id=")[0].split(".")
        url_date = "{}{:02d}{:02d}".format(url_date_raw[2], int(url_date_raw[1]), int(url_date_raw[0]))

    ##

    soup_programme_table = soup.find("div", {"class": "ui-body-b"}).find("ul").find_all("li")

    prog_data = {}

    for programme in soup_programme_table:
        title = programme.find("a").find("b").text
        subtitle = programme.find("a").find("em").text
        prog_url = programme.find("a").get("href")
        try:
            category_raw = programme.find("span", {'class': 'show-category'}).find("img").get("src")
        except:
            category_raw = " "
        try:
            img = programme.find("img", {"class": "movieinfoimg"}).get("src")
        except:
            img = " "

        ##

        short_title = " ".join(title.split(" ")[:4])

        ##

        larger_img = img.replace("w=150", "w=491")

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

        prog_hour = int(start_time[:2])

        if not 6 <= prog_hour <= 23:
            next_day_date = datetime.strptime(url_date, "%Y%m%d") + timedelta(days=1)
            prog_date = next_day_date.strftime("%Y%m%d")
        else:
            prog_date = url_date

        ##

        if cid in ssn_ep_dd_ids and "serija" in categories:
            season_episode_search = re.search(r'sez.([0-9]+)  ep.([0-9]+)', get_ssn_ep(prog_url)) 
        else:
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

        prog_data.update({short_title + prog_date + start_time: { 'img': "https:" + larger_img, 'cat': categories, 'subt': subtitle, 'ep_num': [episode_num_system, episode_num] }})

    return prog_data


def scrape(channel_ids=[], ssn_ep_dd=[]):
    urls = get_channels()

    all_prog = {}

    for url in urls:
        channel_id = int(url.split("id=")[1])

        if channel_id in channel_ids or channel_ids == []:
            ch_prog_data = get_prog_data(url, channel_id, ssn_ep_dd)
            
            all_prog.update(ch_prog_data)


    for url in additional_day_urls:
        channel_id = int(url.split("id=")[1])

        if channel_id in channel_ids or channel_ids == []:
            ch_prog_data = get_prog_data(url, channel_id, ssn_ep_dd)
            
            all_prog.update(ch_prog_data)

    return all_prog