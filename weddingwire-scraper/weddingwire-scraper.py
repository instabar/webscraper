from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import datetime
import requests
import re
import json
from lxml.html import fromstring
from itertools import cycle
import traceback

def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

def getSearchUrl(page):
    return ("https://www.weddingwire.com/shared/search?group_id=2&page=" + str(page)
    + "&userSearch=1&faqs[]=300500469&faqs[]=300500410&sector_id[]=5&currentPickedMonth=201908")

proxies = get_proxies()
proxy_pool = cycle(proxies)

def getBeautifulSoupFromUrl(url):
    # Trying to use proxies to get around fb bot security
    #proxy = next(proxy_pool)
    #page = requests.get(url, proxies={"http":proxy, "https":proxy}).content

    page = requests.get(url).content
    return BeautifulSoup(page, 'html.parser')

def getBusinessPages():
    links = []

    page = 0
    while True:
        page += 1
        searchUrl = getSearchUrl(page)

        bs = getBeautifulSoupFromUrl(searchUrl)

        searchFilters = json.loads(bs.find("div", {"id":"app-vendors-search-filters"}).get("data-filters"))

        # There are 20 results per page. When page * 20 exceeds the number of results, the webpage redirects to
        # a search for all caterers (instead of just bar services). This checks if there are no search filters set.
        if "faqs" not in searchFilters:
            break

        anchors = bs.findAll("a", {"class":"item-title"})

        for a in anchors:
            links.append(a.get("href"))  
    
    return links

def getTitle(bs):
    return bs.find("h1").get_text()

def getPhone(bs):
    phoneTag = bs.find("span", {"class":"app-phone-replace"})
    if phoneTag is None:
        return ""

    return re.sub("\D", "", phoneTag.get_text())

def getAddress(bs):
    addressTag = bs.find("div", {"class":"storefrontHeaderOnepage__address"})
    for child in addressTag.findChildren():
        child.decompose() # isolate address text from sibling elements

    # pick out address from whitespace and reconstruct the string
    addressTag = re.sub("·", "", addressTag.get_text())
    addressTag = re.findall("[\S]+", addressTag)
    address = ""
    for idx, val in enumerate(addressTag):
        address += (val + " ") if idx < (len(addressTag) - 1) else val

    return address

def getRating(bs):
    ratingTag = bs.find("div", {"class":"storefrontSummary__text"})
    if ratingTag is None:
        return ""

    return re.findall("\d.\d", ratingTag.get_text())[0]

def getWebsite(bs):
    websiteTag = bs.findAll("a", {"class":"storefrontHeaderOnepage__infoItem"})[-1].get("onclick")
    return re.sub("'", "", re.findall("'[\S]+'", websiteTag)[0])

def getSocial(bs):
    socialTags = bs.findAll("a", {"class":"storefrontInfo__socialIcon"})
    social = {}
    for tag in socialTags:
        name = re.sub("-", "", re.findall("--[\S]+", tag.get("class")[-1])[0])
        social[name] = tag.get("href")

    return social


def getEmailFromFb(originalFbLink):
    
    suffix = re.findall(".com\S+", originalFbLink)

    if len(suffix) == 0:
        print("Regex returned 0", originalFbLink)
        return "";
        
    fb = "https://facebook" + suffix[0]
    bs = getBeautifulSoupFromUrl(fb);
    aboutDiv = bs.find("div", {"data-key":"tab_about"})

    if (aboutDiv == None):
        print('No "About" div -- Scraper probably denied\t', fb)
        return ""

    aboutUrl = aboutDiv.find("a").get("href");
    bs = getBeautifulSoupFromUrl("https://facebook.com" +  aboutUrl)
    mailtoAnchors = bs.find_all("a", href=re.compile(r"^mailto:"))

    if len(mailtoAnchors) > 0:
        email = mailtoAnchors[0].find('div').get_text()
        return email
    else:
        print('No link beginning with "mailto:"')

    return ""
            
        
def scrapeBusinessPage(url):
    bs = getBeautifulSoupFromUrl(url)

    business = {}
    business["title"]   = getTitle(bs)
    business["website"] = getWebsite(bs)    
    business["phone"]   = getPhone(bs)
    business["address"] = getAddress(bs)
    business["rating"]  = getRating(bs)
    business["social"]  = getSocial(bs)
    business["email"]   = ""

    if "facebook" in business["social"].keys():
        try:
            business["email"] = getEmailFromFb(business["social"]["facebook"])
        except Exception as e:
            print(str(e))

    # TODO If facebook doesn't work, try finding "mailto" anchors on their website
    #if business["email"] == "" and business["website"] != "":
    
    return business

def loadJsonData():
    with open('.\save\weddingwire-output-usa.json') as json_file:
        data = json.load(json_file);
        print(len(data), " businesses loaded")
        return data

def scrapeFacebookEmails(data):
    businesses = 0
    businessesWithEmail = 0
    count = 0;
    for business in data:
        businesses += 1
        if business["email"] == "" and "facebook" in business["social"].keys():
            try:
                business["email"] = getEmailFromFb(business["social"]["facebook"])
                count += 1;
                if (business["email"] != ""):
                    print(count, ' / ', businesses, business["email"])
            except Exception as e:
                print(str(e))
        if (business["email"] != ""):
            businessesWithEmail += 1
    print (businessesWithEmail, " business with emails")
    return data;

def scrapeWeddingWire():
    print("Getting businesses... (this may take a while)")
    links = getBusinessPages()

    print(str(len(links)) + " businesses retrieved")
    print("Scraping each business page... (this will take much longer)")
    data = []
    for link in links:
        business = scrapeBusinessPage(link)
        data.append(business)

    return data;

def writeJSON(data):
    filename = "./json/weddingwire-output-usa-" + datetime.datetime.now().strftime("%Y-%m-%d_%H%M") + ".json"
    print("Writing data to " + filename)
    with open(filename, 'w') as outfile:
        json.dump(data, outfile)
        print(filename + " written")

def main():
    try:
        data = loadJsonData()
        data = scrapeFacebookEmails(data)
        writeJSON(data)
    except Exception as e:
        print(str(e))
        data = scrapeWeddingWire()
        writeJSON(data)
    

if __name__ == "__main__":
    main()
    
