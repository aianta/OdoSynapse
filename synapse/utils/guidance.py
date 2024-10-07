import requests
import logging
import json

logger = logging.getLogger("main")

guidance_host = "http://192.168.1.68:8051"
guidance_api_root = "/api/"


def get_guidance(request):

    url = guidance_host + guidance_api_root + "guidance"

    response = requests.post(url=url, json=request)
    response = response.json()

    return parse_guidance_response(response)


def parse_guidance_response(response):
     guidance_id = response['id']
     step = response['step']
     actions = response['actions']

     return guidance_id, step, actions


def parse_exemplar_id(id):
    split = id.split("_")
    annotation_id = split[0]
    action_id = split[1]
    sample_type = split[2]

    return annotation_id, action_id, sample_type

'''
Create a correctly formatted guidance request from a list of exemplars/trajectories.
'''
def make_guidance_request_from_exemplars(exemplars):
    guidance_request_body = {}

    for trajectory in exemplars:
            
            for element in trajectory:
                
                annotation_id, action_id, sample_type = parse_exemplar_id(element["id"])

                if annotation_id not in guidance_request_body:
                    guidance_request_body[annotation_id] = []
                    
                if action_id not in guidance_request_body[annotation_id]:
                    guidance_request_body[annotation_id].append(action_id)
                
    print("Guidance request body: ", guidance_request_body)
    return guidance_request_body

'''
Given a master list of exemplars/trajectories, and a set of action ids.
Create a new pruned exemplar list, where the only actions that appear are those whose ids appear in the action id list
'''
def prune_exemplars(exemplars, actions):
     pruned_exemplars = []
     for trajectory in exemplars:
        pruned_trajectory = []
        for element in trajectory:
            annotation_id, action_id, sample_type = parse_exemplar_id(element['id'])

            if action_id in actions:
                pruned_trajectory.append({
                        "role": element['role'],
                        'content': element['content']
                })
        pruned_exemplars.append(pruned_trajectory)
    
     return pruned_exemplars
    
        



