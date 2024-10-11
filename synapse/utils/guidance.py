import requests
import logging
import json

logger = logging.getLogger("main")

guidance_host = "http://192.168.1.68:8051"
guidance_api_root = "/api/"

def get_guidance_with_id(guidance_id):

    url = guidance_host + guidance_api_root + "guidance"
    request={
        "id": guidance_id
    }

    response = requests.post(url, json=request)
    response = response.json()

    return parse_guidance_response(response)

def get_guidance(request):

    url = guidance_host + guidance_api_root + "guidance"

    response = requests.post(url=url, json=request)
    response = response.json()

    return parse_guidance_response(response)


def parse_guidance_response(response):
     
     if "error" in response:
         print("Guidance request returned an error, likely there are no steps left.")
         guidance_id = None
         step = None
         actions = []
     else:
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
Strips 'task' and 'id' keys from exemplar elements
'''
def strip_exemplars(exemplars):
    result = []

    for exemplar in exemplars:
        stripped_trajectory = []
        for element in exemplar:
            stripped_trajectory.append({
                'role': element['role'],
                'content': element['content']
            })
        result.append(stripped_trajectory)

    return result

'''
Given a master list of exemplars/trajectories, and a set of action ids.
Create a new pruned exemplar list, where the only actions that appear are those whose ids appear in the action id list
'''
def prune_exemplars(exemplars, actions, step=None):
     pruned_exemplars = []
     for trajectory in exemplars:
        pruned_trajectory = []
        for element in trajectory:
            annotation_id, action_id, sample_type = parse_exemplar_id(element['id'])

            if action_id in actions:
                
                '''
                In the original implementation, only the first step of a task included the task description. This made sense, since all steps were given at once.
                But with single steps being given, we still want the LLM to have information about what kind of tasks the steps correspond to. So the task description
                needs to be injected even if we are only feeding it step 7 for example. 

                So, in the original dataset if the exemplar content started with 'Task:' we know it's the first step in a trajectory. 
                If the content starts with 'Action:' then it's the action following an observation. 

                If it starts with neither, then we know its an observation for a subsequent (non-first) step in a trajectory and we should insert the task description. 
                '''

                if element['content'].startswith("Task:") or element['content'].startswith("Action:"):
                    pruned_trajectory.append({
                            "role": element['role'],
                            'content': element['content']
                    })
                else:
                    
                    if step is not None:
                        pruned_trajectory.append({
                            "role": element['role'],
                            'content': 'Task: ' + element['task'] + "\nExample observation and action for step "+str(step)+":\n" + element['content']
                        })
                    else:
                        pruned_trajectory.append({
                            "role": element['role'],
                            'content': 'Task: ' + element['task'] + "\nExample observation and action for current step:\n" + element['content']
                        })
        pruned_exemplars.append(pruned_trajectory)
    
     return pruned_exemplars
    
        



