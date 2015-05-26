#!/usr/bin/python

import pycurl
from StringIO import StringIO
from BeautifulSoup import BeautifulSoup
from datetime import datetime, timedelta
import os
import smtplib
from mailer import Mailer
from mailer import Message

cutoff_time = datetime.now() - timedelta(hours=30)

def read_history(userid):
    path = os.path.dirname(__file__)
    filename = 'history/{0}'.format(userid)
    full_path = os.path.join(path, filename)
    sent_links = []
    try:
        with open(full_path) as f:
            sent_links = f.readlines()
        f.close()
    finally:
        for i, item in enumerate(sent_links):
            sent_links[i] = item.replace('\n', '')
        return sent_links


def write_history(links, userid):
    path = os.path.dirname(__file__)
    filename = 'history/{0}'.format(userid)
    full_path = os.path.join(path, filename)
    history_object = open(full_path, 'w')
    for item in links:
        history_object.write('{0}\n'.format(item))
    history_object.close()


def send_listings(listings, address):
    fromAddress = ''
    username = ''
    password = ''
    toAddress = address
    message = Message(From = fromAddress, To = toAddress)
    message.Subject = 'Your Apartment Hunter Listings {0}'.format(datetime.now())
    message.Html = """Here's the new listings Apartment Hunter found!<br>"""

    for item in listings:
        message.Html += '<p>' + item + '</p>'

    try:
        sender = Mailer('smtp.gmail.com', port=587, use_tls=True, usr=username, pwd=password)
        sender.send(message)
        print "Message Sent"
    except:
        print "Message Failed"


def queryCL(url):
    response = StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEFUNCTION, response.write)
    c.perform()
    c.close()

    results = response.getvalue()
    response.close()

    return results


def getListings(maxPrice, terms):
    URL = 'http://philadelphia.craigslist.org/search/apa?maxAsk='+maxPrice+'&query='+terms+''
    soup = BeautifulSoup(queryCL(URL))

    output = soup.find("div", {"class": "content"})
    out_string = output.prettify()
    out_string = out_string.splitlines()
    poops = ''

    for line in out_string:
        if line != '<h4 class="ban nearby">':
            poops = poops + line + '\n'
        else:
            break

    soup = BeautifulSoup(poops)
    links = soup.findAll('p', {'class': 'row'})
    
    timed_links = []
    for link in links:
        link_parts = link.findNext('a', {'class': 'hdrlnk'}).prettify().split('"')
        listing_id = link_parts[1].split('/apa/')[1].split('.')[0]
        listing_url = 'http://philadelphia.craigslist.org' + link_parts[1]
        listing_name = link_parts[6].replace('\n', '').replace('</a>', '')[1:]
        listing_location = link.findNext('span', {'class': 'pnr'}).prettify().split('\n')[2].replace(' (',  '').replace(')', '')
        listing_price = link.findNext('span', {'class': 'price'}).prettify().split('\n')[1].replace('&#x0024;', '$')
        listing_size = link.findNext('span', {'class': 'housing'}).prettify().split('\n')[1].split()[1]
        time_posted = datetime.strptime(link.findNext('time').prettify().split('"')[1], '%Y-%m-%d %H:%M')
        timed_links.append([listing_name, listing_url, time_posted, listing_location, listing_price, listing_size, listing_id])
    return timed_links

userid = '000001'
address = 'tbell+apts@tombellnj.com'
timed_links = getListings('1400', 'carriage')
mailed_links = read_history(userid)

listings_to_send = []
for listing in timed_links:
    if cutoff_time < listing[2] and listing[6] not in mailed_links:
        mailed_links.append(listing[6])
        listings_to_send.append('{0} - {1} {2} {3}\n{4}\n'.format(listing[0], listing[3], listing[5], listing[4], listing[1]))

if len(listings_to_send) > 0:
    send_listings(listings_to_send, address)
    print '{0} new listings sent'.format(len(listings_to_send))
else:
    print 'No new listings'

write_history(mailed_links, userid)
