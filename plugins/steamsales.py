import time
import json
import os
from util import hook, http, text, web
from collections import OrderedDict

debug = False


def log_sales_data(sales, filename):
    # Create dr to log sales for debug purposes
    if not os.path.exists('persist/steamsales_history'):
        os.makedirs('persist/steamsales_history')

    # Log specified data
    with open('persist/steamsales_history/' +
            time.strftime('%Y%m%d%H%M', time.localtime()) +
            '-' + filename + '.json', 'w+') as f:
        json.dump(sales, f, sort_keys=True, indent=2)


def get_featured():
    sales_url = "http://store.steampowered.com/api/featured/?l=english"
    try:
        sales = http.get_json(sales_url)
    except:
        sales = {}

    if debug:
        log_sales_data(sales, "featured")

    return sales


def get_featuredcategories():
    sales_url = "http://store.steampowered.com/api/featuredcategories/?l=english"
    try:
        sales = http.get_json(sales_url)
    except:
        sales = {}

    if debug:
        log_sales_data(sales, "featuredcategories")

    return sales


def get_sales(mask):
    # Fetch data
    data = get_featuredcategories()
    flash_data = get_featured()

    # Break if either return empty - might be unnecessary
    if not data or not flash_data:
        return {}

    # Aggregate data
    fetchtime = int(time.time())
    data["flash"] = {}
    data["flash"]["name"] = "Flash Sales"
    data["flash"]["items"] = []
    data["featured"] = {}
    data["featured"]["name"] = "Featured Sales"
    data["featured"]["items"] = []
    for item in flash_data["large_capsules"]:
        if "discount_expiration" not in item.keys():
            item["discount_expiration"] = 9999999999
        if item["discount_expiration"] - fetchtime <= 43200:
            data["flash"]["items"].append(item)
        else:
            data["featured"]["items"].append(item)

    # Check for no data
    if sum([len(c_data.get('items', {})) for category, c_data in
            data.iteritems() if isinstance(c_data, dict)]) == 0:
        return {}, False

    # Mask Data
    data = {k: v for k, v in data.items() if isinstance(v, dict)
        and k not in mask}

    if debug:
        log_sales_data(data, "data")

    # Format data
    sales = {}
    for category in data:
        if "items" not in data[category].keys():
            data[category]["items"] = []
        for item in data[category]["items"]:
            # Prepare item data
            try:
                # Bundles
                if set(["id", "url"]).issubset(set(item.keys())):
                    if not item["final_price"] and not item["discounted"]:
                        item["final_price"] = web.try_googl(item["url"])
                        item["discounted"] = True
                else:
                    # Midweek Madness, etc
                    if "url" in item.keys() and "id" not in item.keys():
                        data[category]["name"] = item["name"] or data[category]["name"]
                        item["id"] = str(item["url"])[34:-1]
                        appdata = http.get_json("http://store.steampowered.com/api/"
                            "appdetails/?appids={}".format(item["id"]))[str(item["id"])]["data"]
                        item["name"] = appdata["name"]
                        if "Free to Play" in appdata["genres"]:
                            item["final_price"] = 'Free to Play'
                            item["discount_percent"] = '100'
                        else:
                            item["final_price"] = appdata[
                                "price_overview"]["final"]
                            item["discount_percent"] = appdata[
                                "price_overview"]["discount_percent"]
                    item["discounted"] = True if int(item["discount_percent"]) > 0 \
                        else False
            except:
                # Unusuable Catagory e.g. Banner Announcments
                continue
            # Add appropriate item data to sales
            if item["discounted"]:
                item["name"] = item["name"].replace(" Advertising App", "")
                item = {k: u"{}".format(v) for k, v in item.items() if k in
                    ["name", "final_price", "discount_percent"]}
                if data[category]["name"] not in sales.keys():
                    sales[data[category]["name"]] = []
                sales[data[category]["name"]].append(item)

    # Filter and sort items
    sales = {category: sorted([item for item in items if item["name"] != "Uninitialized"],
        key=lambda x: x["name"]) for category, items in sales.items()}

    if debug:
        log_sales_data(sales, "sales")

    # Return usable data
    return sales, True


def format_sale_item(item):
    if not str(item["final_price"]).isdigit():
        return u"\x02{}\x0F: {}".format(item["name"],
            item["final_price"])
    else:
        return u"\x02{}\x0F: ${}.{}({}% off)".format(item["name"],
            item["final_price"][:-2],
            item["final_price"][-2:],
            item["discount_percent"])


@hook.command()
def steamsales(inp, say='', chan=''):
    "steamsales <space seperated options> - Check Steam for specified sales; " \
    "Displays special event deals on top of chosen deals. " \
    "Options: daily flash featured specials top_sellers all"

    options = {"Flash Sales": "flash",
               "Featured Sales": "featured",
               "Specials": "specials",
               "Top Sellers": "top_sellers",
               "Daily Deal": "daily",
               "All": "all"}
    mask = ["coming_soon", "new_releases", "genres",
            "trailerslideshow", "status"]

    # Clean input data
    categories = [line.strip(', ') for line in inp.lower().split()
        if line in options.values()]
    if 'all' in inp:
        categories = [item for item in options.values() if item != 'all']

    # Check for bad input
    if not categories:
        return steamsales.__doc__

    # Get Sales
    mask += [option for option in options.values() if option not in categories]
    sales, flag = get_sales(mask)

    # If sales not returned
    if not sales and not flag:
        return "Steam Store API error, please try again in a few minutes."
    elif not sales and flag:
        return "No sales found."

    # Prepare sales
    for k, v in options.items():
        if v in categories and k not in sales:
            sales[k] = []
    sales = OrderedDict(sorted(sales.items()))

    # Output appropriate data
    for category in sales:
        items = [format_sale_item(item) for item in sales[category]]
        if len(items):
            for out in text.chunk_str(u"\x02New {}\x0F: {}".format(category, u"; ".join(items))):
                say(out)
        else:
            if 'all' not in inp.lower():
                say(u"\x02{}\x0F: {}".format(category, u"None found"))

