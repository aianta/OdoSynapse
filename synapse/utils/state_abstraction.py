import requests
import logging
import json

from .guidance import parse_exemplar_id

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

    dump_to_file(request_body)
    response = requests.post(url, json=request_body)

    return response.text

def dump_to_file(data):
    with open('annotated_state_abstraction_request.json', 'w') as f:
        json.dump(data, f, indent=4)

'''
Create a correctly formatted annotated state abstraction request from a list of exemplars/trajectories.
'''
def make_trajectory_info_from_exemplars(exemplars):
    guidance_request_body = {}
    symbol_mapping = {}
    symbol_index = 1

    for trajectory in exemplars:
            
            for element in trajectory:
                
                annotation_id, action_id, sample_type = parse_exemplar_id(element["id"])

                if annotation_id not in guidance_request_body:
                    guidance_request_body[annotation_id] = []

                if annotation_id not in symbol_mapping:
                    symbol_mapping[annotation_id] = "trajectory-" + str(symbol_index)
                    symbol_index = symbol_index + 1
                    
                if action_id not in guidance_request_body[annotation_id]:
                    guidance_request_body[annotation_id].append(action_id)

    result = {
        "symbolMapping": symbol_mapping,
        "trajectories": guidance_request_body
    }

    print("Trajectory Info:\n", result)

    return result