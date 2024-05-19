from bs4 import BeautifulSoup
import requests

mojtv_cat = {'/controlimg/program/k6.gif': 'serija', '/controlimg/program/k5.gif': 'film', '/controlimg/program/k2.gif': 'sport'}

def get_channels():

    url = "https://mojtv.hr/m2/tv-program/"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"
    }

    page = requests.get(url, headers=headers).text
    soup = BeautifulSoup(page, 'html.parser')

    soup_channel_table = soup.find("div", {"class": "ui-body-b"}).find("ul").find_all("li")

    channel_urls = []

    for channel in soup_channel_table:
        channel_urls.append( url + channel.find("a").get("href") )

    return channel_urls


def get_prog_data(url):

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"
    }

    page = requests.get(url, headers=headers).text
    soup = BeautifulSoup(page, 'html.parser')

    soup_programme_table = soup.find("div", {"class": "ui-body-b"}).find("ul").find_all("li")

    prog_data = {}

    for programme in soup_programme_table:
        title = programme.find("a").find("b").text
        subtitle = programme.find("a").find("em").text
        try:
            category_raw = programme.find("span", {'class': 'show-category'}).find("img").get("src")
        except:
            category_raw = ""
        try:
            img = programme.find("a").find("img").get("src")
        except:
            img = ""

        short_title = " ".join(title.split(" ")[:4])
        larger_img = img.replace("w=150", "w=360")
        categories = [mojtv_cat.get(category_raw)]
        categories.extend( subtitle.split(" ") )

        prog_data.update({short_title: { 'img': "https:" + larger_img, 'cat': list(set( categories )) }})

    return prog_data


def scrape(channel_ids=[]):
    urls = get_channels()

    all_prog = {}

    for url in urls:
        channel_id = int(url.split("?id=")[1])

        if channel_id in channel_ids or channel_ids == []:
            ch_prog_data = get_prog_data(url)
            
            all_prog.update(ch_prog_data)

    return all_prog