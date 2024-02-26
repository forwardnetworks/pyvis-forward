"""
Usage:
  pyvis-forward <appserver> <network> 

Options:
  -h --help             Show this help message
"""

# const options = {
#   "physics": {
#     "barnesHut": {
#       "gravitationalConstant": -3400,
#       "centralGravity": 0,
#       "damping": 0.32
#     },
#     "minVelocity": 0.75
#   }
# }


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

def open_in_browser(file):
    cwd = os.getenv("PWD")
    choice = input("Do you want to open the browser to view the network graph? [y/n]: ").lower()
    if choice == 'y':
        webbrowser.open_new_tab(f'file://{cwd}/{file}')
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
            print_debug(response_json)
            raise Exception("Request failed")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    

def main(appserver, networkId):
    username = os.getenv("FWD_USER")
    password = os.getenv("FWD_PASSWORD")
    if not username or not password:
        print("Please set FWD_USER and FWD_PASSWORD")
        exit(1)
    query= """ 
foreach device in network.devices
foreach interface in device.interfaces
foreach link in interface.links
select {
  source: device.name,
  sourceInterface: interface.name,
  target: link.deviceName,
  targetInterface: link.ifaceName
}
"""
    result = callNQE(appserver, username, password, networkId, query)
    df = pd.DataFrame(result)
    nodes = pd.unique(df[['source', 'target']].values.ravel('K'))
    net = Network(height="800px", width="100%", bgcolor="#222222", font_color="white", filter_menu=True)
    nodes_list = nodes.tolist()
    net.add_nodes(nodes_list,  title=nodes_list)
    for _, row in df.iterrows():
        net.add_edge(row['source'], row['target'], title = f"{row['source'] + '-' + row['sourceInterface'] + '<->' + row['target'] + '-' +row['targetInterface']   }")
    output = f"nodes-{networkId}.html"
    # net.show_buttons(filter_=['physics'])
   
    net.show(output, notebook=False)
    open_in_browser(output)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    appserver = arguments['<appserver>']
    network = arguments['<network>']
    main(appserver, network)