import requests
import logging
import json

logger = logging.getLogger("main")

state_abstraction_host = "http://192.168.1.68:8051"
state_abstraction_api_root = "/api/"

def get_state_abstraction(website, raw_html):

    #url = state_abstraction_host + state_abstraction_api_root + "state-abstraction-v2"
    url = state_abstraction_host + state_abstraction_api_root + "state-abstraction"

    _params = {'website': website}

    response = requests.post(url, data=raw_html, 
                  headers={'Content-Type': 'text/html'},
                  params=_params
                 )
    
    if(response.status_code == 404):
        return None
    else:
        return response.text
    
'''
Here we are expecting trajectory_info to be a dictonary containing:

{
    <annotation_id>: [<action_uid>, <action_uid>, ...]
}

'''    
def get_annotated_state_abstraction(website, raw_html, trajectory_info):

    request_body = {
        "website": website,
        "raw_html": raw_html,
        "trajectory_info": trajectory_info
    }

    url = state_abstraction_host + state_abstraction_api_root + "state-abstraction-v3"

    response = requests.post(url, json=request_body)

    return response.text