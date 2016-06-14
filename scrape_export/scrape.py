__author__ = 'jasper'
from bs4 import BeautifulSoup
import math
import collections
import re
import sys
import pprint

dividerStyle = "border: black 1px solid; left:18px"
regex_operation = "(.*voer.*|.*breng.*) van (.*) naar (.*)"
soup = BeautifulSoup(open('test.html', 'rb'))

def styleToDict(style):
    if style is None:
        return None
    x = [ a.strip() for a in re.split(';|:', style)]
    x = x[0:len(x) - (len(x) % 2)] # ensure even length
    return dict(x[i:i+2] for i in range(0, len(x), 2))

def stripCssUnit(string, unit):
    m = re.match("([0-9]*)\s*%s" % (unit), string)
    if m:
        return float(m.group(1))
    raise Exception("Couldn't strip unit %s from %s" % (unit, string))

def pxToInt(px):
    return int(stripCssUnit(px, "px"))

def findColumnPositionByItemRegex(regex):
    tags=soup.findAll("div", text=re.compile(regex))
    left = set([y['left'] for y in [styleToDict(x['style']) for x in tags]])
    if len(left) != 1:
        raise Exception("Failed to find unique position for column with regex %s" % regex)
    return pxToInt(left.pop())

def scrape():
    columns = {
                'VolgNr'                 : { 'align' : 'l' },
                'ML Categorie'           : { 'align' : 'l' },
                'Omschrijving'           : { 'align' : 'l' },
                'Land van eindgebruik'   : { 'align' : 'l' },
                'Bestemmeling'           : { 'align' : 'l' },
                'Eindgebruiker'          : { 'align' : 'l' },
                'Bedrag'                 : { 'align' : 'r' },
                }

    for col, defi in columns.items():
        headers = soup.findAll("div", text=re.compile(col))
        if len(headers) == 0:
            raise Exception("Column %s not found" % ( col ))
        for headerTag in headers:
            styles = styleToDict(headerTag['style'])
            if defi['align'] == 'l':
                position = pxToInt(styles['left'])
            elif defi['align'] == 'r':
                left = pxToInt(styles['left'])
                width = pxToInt(styles['width'])
                position = left + width
            else:
                raise Exception("Illegal column definition for column %s" % col)
            if 'position' in defi:
                if defi['position'] != position:
                    raise Exception("Mismatch of column header: found column %s at %s, expecting %s" % (col, position, columnPositions[col]))
            else:
                defi['position'] = position

    print("Column offsets found:")
    for c, d in columns.items():
        print("Column %s at %s" % (c, d['position']))

    columns['ML Categorie']['position'] = findColumnPositionByItemRegex("^ML[0-9]{2}$")
    columns['ML Subcategorie'] = {
        'align' : 'l',
        'position' : findColumnPositionByItemRegex("^ML[0-9]{2}[a-z]$")
    }
    print("Correcting ML tag position at %d px" % columns['ML Categorie']['position'])
    print("Found ML subcat tag position at %d px" % columns['ML Subcategorie']['position'])

    print("finding column contents")
    # have to iterate over all divs and check position
    # one by one to support right-aligned items
    for tag in soup.findAll("div"):
        styles = styleToDict(tag['style'])
        if styles is None:
            continue
        if not 'left' in styles:
            continue
        if not 'top' in styles:
            continue
        left = pxToInt(styles['left'])
        width = pxToInt(styles['width'])
        right = left + width
        top = pxToInt(styles['top'])
        # match against all column positions
        for c, d in columns.items():
            if not 'lines' in d:
                d['lines'] = dict()
            if ((d['align'] == 'l' and left == d['position']) or
                (d['align'] == 'r' and right == d['position'])):
                if re.match("%s\n" % c, tag.text):
                    break
                d['lines'][top] = tag.text.strip()
                break

    print("Column stats:")
    for c, d in columns.items():
        print("Column %s at %s got %d items" % (c, d['position'], len(d['lines'])))

    # Divide lines among sections
    sectionDividers = soup.findAll("span", style=re.compile(dividerStyle))
    sectionHeaders = soup.findAll("div", text=re.compile(regex_operation))
    sections = [{'name':x.text.strip(),'top':pxToInt(styleToDict(x['style'])['top'])} for x in sectionHeaders]
    #Sort sections by positions'top
    sections = sorted(sections, key=lambda s: s['top'])
    # Add bottom coordinate
    sections[len(sections)-1]['bottom'] = sys.maxsize
    for i in range(len(sections)-1):
        sections[i]['bottom'] = sections[i+1]['top']

    for s in sections:
        sectionTop = s['top']
        sectionBottom = s['bottom']
        for c, d in columns.items():
            s[c] = dict()
            for top, line in d['lines'].items():
                if top >= sectionTop and top <= sectionBottom:
                    if not 'lines' in s[c]:
                        s[c]['lines'] = dict()
                    s[c]['lines'][top] = line

    # Per section, iterate over the gathered data and put it
    # into records
    for s in sections:
        # The amount of records equals the amount of items in the
        # 'VolgNr' column. Generate top/bottom info for that col
        recordTops = sorted([x for x in s['VolgNr']['lines'].keys()])
        recordBottom = list()
        if(len(recordTops) > 1):
            recordBottom = recordTops[1:]
        recordBottom.append(s['bottom'])
        if not 'records' in s:
            s['records'] = dict()
        for i in range(len(recordTops)):
            top = recordTops[i]
            bottom = recordBottom[i]
            recNr = s['VolgNr']['lines'][top]
            if not recNr in s['records']:
                s['records'][recNr] = dict()
            for col in columns:
                if not 'lines' in s[col]:
                    continue
                for linetop, text in s[col]['lines'].items():
                    if linetop >= top and linetop < bottom:
                        if not col in s['records'][recNr]:
                            s['records'][recNr][col] = list()
                            #print("[%s : %s] Column %s already populated" % (s['name'], recNr, col))
                        s['records'][recNr][col].append(text)
    return sections

sections = scrape()
pprint.pprint([x['records'] for x in sections])