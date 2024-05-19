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
        data = prog_data.get(title, {})

        icon_src = data.get('img', ' ')
        categories = data.get('cat', [' '])
        subtitle = data.get('subt', ' ')

        prog_icon = ET.SubElement(prog, 'icon')
        prog_icon.set('src', icon_src)

        prog_subtitle = ET.SubElement(prog, 'sub-title')
        prog_subtitle.text = subtitle

        for cat in categories:
            prog_categ = ET.SubElement(prog, 'category')
            prog_categ.set('lang', 'hr')
            prog_categ.text = cat

        ET.dump(prog)
    
    output_xml = ET.tostring(tree)
    return Response(output_xml, mimetype='text/xml')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
