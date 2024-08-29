from flask import Flask, request, Response
import requests
import xml.etree.ElementTree as ET
import re
from mojtv_scraper import scrape
import pickle
import os, os.path, time

app = Flask(__name__)

def get_prog_data(channel_ids, ssn_ep_dd, max_age=864000*3):
    filename = 'prog_data.pkl'
    
    if os.path.isfile(filename):
        file_creation_ts = os.stat(filename).st_mtime
        now_ts = time.time()
        diff = now_ts - file_creation_ts

        print(diff)

        if diff < max_age:
            
            with open(filename, 'rb') as f:
                loaded_prog = pickle.load(f)
                return loaded_prog
    
    scraped_prog = scrape(channel_ids, ssn_ep_dd)

    with open(filename, 'wb') as f:
        pickle.dump(scraped_prog, f)

    return scraped_prog
        

@app.route('/')
def enrich_endpoint():
    origin_url = request.args.get('origin_url')
    channel_id_list = [int(x) for x in request.args.get('cids').split(',')]
    ssn_ep_dd_ids_list = [int(x) for x in request.args.get('dd').split(',')]
    max_age = int(request.args.get('max_age')) if request.args.get('max_age') else 864000*3
    ###

    r = requests.get(origin_url)
    r.encoding = r.apparent_encoding
    origin_data = r.text

    tree = ET.fromstring(origin_data) 

    prog_data = get_prog_data(channel_ids=channel_id_list, ssn_ep_dd=ssn_ep_dd_ids_list, max_age=max_age) # [1,2,310,3,4,185,186,341,370]

    # import json
    
    # with open('file.txt', 'w') as file:
    #     file.write(json.dumps(prog_data))
    # return None
    
    for prog in tree.iter('programme'):
        long_title = prog.find('title').text
        title = " ".join( long_title.split(" ")[:4] )
        
        start_time_raw = prog.attrib.get('start', '')
        if len(start_time_raw) > 11:
            start_time = start_time_raw[0:12]
        else:
            start_time = ''
        
        data = prog_data.get(title + start_time, {})

        icon_src = data.get('img', ' ')
        categories = data.get('cat', [' '])
        subtitle = data.get('subt', ' ')
        episode_num = data.get('ep_num', {})

        ##

        if icon_src and icon_src != ' ':
            prog_icon = ET.SubElement(prog, 'icon')
            prog_icon.set('src', icon_src)

        ##

        empty_subtitle = prog.find('sub-title')
        prog.remove(empty_subtitle)

        #if not (subtitle and subtitle != ' '):
        subtitle_in_title = prog.find('title').text.split(', ')
        if len(subtitle_in_title) > 1:
            subtitle = subtitle_in_title[1]
            categories.extend( subtitle.split(" ") )
            categories = list(set(filter(None, categories)))
        
        if subtitle and subtitle != ' ':
            prog_subtitle = ET.SubElement(prog, 'sub-title')
            prog_subtitle.text = subtitle

        ##
            
        for cat in categories:
            if cat and cat != ' ':
                prog_categ = ET.SubElement(prog, 'category')
                prog_categ.set('lang', 'hr')
                prog_categ.text = cat

        ##

        if episode_num and episode_num[0] != ' ':
            prog_episode_num = ET.SubElement(prog, 'episode-num')
            prog_episode_num.set('system', episode_num[0])
            prog_episode_num.text = episode_num[1]

        ##

        l_long_title = long_title.lower()
        l_subtitle = subtitle.lower()

        if ("nove epizode" in l_long_title or "nove epizode" in l_subtitle) or \
            ("nova sezona" in l_long_title or "nova sezona" in l_subtitle) or \
            ("nova serija" in l_long_title or "nova serija" in l_subtitle):
            prog_new = ET.SubElement(prog, 'new')

        if ("prijenos" in l_long_title or "prijenos" in l_subtitle) or \
            ("uživo" in l_long_title or "uživo" in l_subtitle):
            prog_live = ET.SubElement(prog, 'live')

        if ("(R)" in long_title or "(R)" in subtitle) or \
            (re.search(r'R$', long_title) or re.search(r'R$', subtitle)):
            prog_repeat = ET.SubElement(prog, 'previously-shown')

        if "premijera" in l_long_title or "premijera" in l_subtitle:
            prog_premiere = ET.SubElement(prog, 'premiere')

        ##

        ET.dump(prog)

    output_xml = ET.tostring(tree)
    return Response(output_xml, mimetype='text/xml')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
