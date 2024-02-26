"""
Usage:
  pyvis-forward <appserver> <network> 

Options:
  -h --help             Show this help message
"""



from pyvis.network import Network
import datetime
import inspect
import requests
import os
import pandas as pd
import pyarrow
from docopt import docopt
import webbrowser


def print_debug(message):
    print(
        f"{datetime.datetime.now()} Debug on line {inspect.currentframe().f_back.f_lineno}: {message}"
    )

def open_in_browser():
    cwd = os.getenv("PWD")
    choice = input("Do you want to open the browser to view the network graph? [y/n]: ").lower()
    if choice == 'y':
        webbrowser.open_new_tab(f'file://{cwd}/nodes.html')
    elif choice == 'n':
        print("Okay, not opening the browser.")
    else:
        print("Invalid input. Please enter 'y' for yes or 'n' for no.")

def callNQE(appserver, username, password, networkId, query):
    url = f"https://{appserver}/api/nqe?networkId={networkId}"
    print_debug(f"Sending Request: {url}")
    auth = (username, password)
    body = {
            "query": query
            # "queryOptions": {"offset": offset, "limit": limit},
        }
    try:
        response = requests.post(url, auth=auth, json=body)
        if response.status_code == 200:
              response_json = response.json()
              if not response_json["items"]:
                raise Exception("Items not found in response")
              else:
                  return response_json["items"]
        else:
            return {"error": "Request failed"}
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    

def main(appserver, networkId):
    username = os.getenv("FWD_USER")
    password = os.getenv("FWD_PASSWORD")
    query= """ 
    getLinks(device) =
foreach interface in device.interfaces
let links =  interface.links
where isPresent(links)
foreach link in links
select  link;

getVertexes = 
foreach device in network.devices
select device.name;
  
foreach device in network.devices
let links = getLinks(device)
let vertexes = getVertexes()
foreach link in links
select {source: device.name, target: link.deviceName}
"""
    result = callNQE(appserver, username, password, networkId, query)
    df = pd.DataFrame(result)
    nodes = pd.unique(df[['source', 'target']].values.ravel('K'))
    net = Network(height="800px", width="100%", bgcolor="#222222", font_color="white")
    nodes_list = nodes.tolist()
    net.add_nodes(nodes_list,  title=nodes_list)
    for _, row in df.iterrows():
        net.add_edge(row['source'], row['target'])
    net.show('nodes.html', notebook=False)
    open_in_browser()



open_in_browser()
              

if __name__ == '__main__':
    arguments = docopt(__doc__)
    appserver = arguments['<appserver>']
    network = arguments['<network>']
    main(appserver, network)