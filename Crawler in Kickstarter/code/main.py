import os
import sys
from bs4 import BeautifulSoup
import requests
import io
import json
import datetime
from time import sleep
import calendar
import time


# define some constants
PAGES = 300
URL = "https://www.kickstarter.com/discover/advanced?category_id=16&woe_id=0&sort=magic&seed=2727134&page="
SLEEP = 1
ERR_MSG = "Couldn't load page number "
SUCCEEDED_STATUS = 200
OUTPUT_FILE = "output.json"

crawler_results = []
counter, page_num = 0, 0


def get_story(address):
    sleep(SLEEP)
    slug = address
    s = requests.Session()
    r = s.get(address)
    soup = BeautifulSoup(r.text, 'html.parser')
    xcsrf = soup.find("meta", {"name": "csrf-token"})["content"]

    query = """
    query Campaign($slug: String!) {
      project(slug: $slug) {
        story(assetWidth: 680)
      }
    }"""

    r = s.post("https://www.kickstarter.com/graph",
               headers={
                   "x-csrf-token": xcsrf
               },
               json={
                   "operationName": "Campaign",
                   "variables": {
                       "slug": slug
                   },
                   "query": query
               })

    result = r.json()
    story_html = result["data"]["project"]["story"]
    soup = BeautifulSoup(story_html, 'html.parser')
    story = ''.join(s.get_text() for s in soup.find_all('p'))
    return story


print("Starting crawling process.\nPlease wait :)")
while counter < PAGES:
    # define the page's URL
    page_num += 1
    page_url = URL + str(page_num)

    # download the curr page
    page_data = requests.get(page_url)
    if page_data.status_code != SUCCEEDED_STATUS:
        print(ERR_MSG + str(page_num))
        break

    # parse the curr page
    page_parsed = BeautifulSoup(page_data.content, 'html.parser')

    for article in page_parsed.find_all('div'):
        if counter >= PAGES:
            break
        if article.get("data-project"):
            # lets load the json
            project = {}
            page_json = json.loads(article.attrs["data-project"])
            project["Creator"] = page_json['creator']['name']
            project["Title"] = page_json['name']
            project["Text"] = get_story(page_json['urls']['web']['project'])
            project["DollarsPledged"] = page_json['usd_pledged']
            project["DollarsGoal"] = page_json['goal']
            project["NumBackers"] = page_json['backers_count']
            togo = datetime.timedelta(seconds=(page_json['deadline'] - calendar.timegm(time.gmtime())))
            togo_str = "{:0>8}".format(str(togo)).split(':')
            project["DaysToGo"] = f"{togo_str[0]} hours {togo_str[1]} minutes and {togo_str[2]} seconds"
            project["AllOrNothing"] = str(datetime.datetime.now() + togo)
            crawler_results.append(project)
            counter += 1
            sys.stdout.write(f"\rPage number {counter} out of {PAGES} pages.")
            sys.stdout.flush()
    sleep(SLEEP)


results_path = os.path.join(os.path.curdir, 'output', OUTPUT_FILE)
with io.open(results_path, "w", encoding="utf-8") as f:
    json.dump({"records": {"record ": crawler_results}}, f, ensure_ascii=False, indent=4)
f.close()















