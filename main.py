from flask import Flask, request, Response
import requests
import xml.etree.ElementTree as ET
from mojtv_scraper import scrape

app = Flask(__name__)

@app.route('/')
def enrich_endpoint():
    origin_url = request.args.get('origin_url')
    ###

    r = requests.get(origin_url)
    r.encoding = r.apparent_encoding
    origin_data = r.text

    tree = ET.fromstring(origin_data) 

    prog_data = scrape(channel_ids=[1,2,310,3,4,185,186,341,370])
    
    for prog in tree.iter('programme'):
        title = " ".join( prog.find('title').text.split(" ")[:4] )
        start_time_raw = prog.attrib.get('start', '')
        if len(start_time_raw) > 11:
            start_time = start_time_raw[8:12]
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

        ET.dump(prog)
    
    output_xml = ET.tostring(tree)
    return Response(output_xml, mimetype='text/xml')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
