import os
import json
import argparse
import sqlite3
import re

class Analyzer:

    con = None # sqlite connection
    cur = None # sqlite cursor
    create_table_sql = """
                CREATE TABLE IF NOT EXISTS  "mind2web_results" (
                    "annotation_id"	TEXT,
                    "task"          TEXT,
                    "website"       TEXT,
                    "action_uid"	TEXT,
                    "source_dir"	TEXT,
                    "input"	TEXT,
                    "output"	TEXT,
                    "target"	TEXT,
                    "target_el" INTEGER,
                    "prediction"	TEXT,
                    "prediction_el" INTEGER,
                    "prompt_tokens"	INTEGER,
                    "completion_tokens"	INTEGER,
                    "total_tokens"	INTEGER,
                    "state_abstraction" TEXT,
                    PRIMARY KEY("action_uid","source_dir")); 
                """
    insert_sql = """
        INSERT INTO mind2web_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """

    def __init__(self, db_path):
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()

    def create_table(self):
        self.cur.execute(self.create_table_sql)
        

    def save(self, parameters):
        self.cur.executemany(self.insert_sql, parameters)
        self.con.commit()
        

    
    def get_state_abstraction_from_input(self, input):
        last_input = input[len(input)-1]
        content = re.findall("(?<=`).+(?=`)", last_input['content'])
        
        if len(content) == 0:
            content = "Failed to retrieve state abstraction. Content was: " + str(last_input['content'])
        else:
            content = content[0]

        return content


    def data_to_parameters(self,result,prediction,action,annotation_id, website, task, source_dir):
        
        print(f"prediction: {json.dumps(prediction, indent=2)}")
        # Handle case where prediction is malformed.
        predicted_element = re.findall("(?<=\[)\d+(?=\])", prediction['pred_act'])
        if(len(predicted_element)>0):
            predicted_element = predicted_element[0]
        else:
            predicted_element = -1

        params = (
            annotation_id,
            task,
            website, 
            action['action_uid'], 
            source_dir, 
            json.dumps(result['input'], indent=4),
            result["output"],
            prediction['target_act'],
            re.findall("(?<=\[)\d+(?=\])", prediction['target_act'])[0],
            prediction['pred_act'],
            predicted_element,
            result['token_stats']['prompt_tokens'],
            result['token_stats']['completion_tokens'],
            result['token_stats']['total_tokens'],
            self.get_state_abstraction_from_input(result['input'])
            )

        return params
    
    def finish(self):
        self.con.close()


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result_dir", type=str)
    parser.add_argument("--test_data_dir", type=str)
    parser.add_argument("--db_path", type=str)

    return parser

def load_test_data(test_data_dir):

    _test_data_dir = os.fsencode(test_data_dir)

    test_data_files = [os.fsdecode(x) for x in os.listdir(_test_data_dir) if os.fsdecode(x).endswith(".json")]
    test_data_files.sort()

    test_data = []

    for test_file in test_data_files:
 
        with open(os.path.join(test_data_dir, test_file), 'r') as file:

            print(f"Loading test data from {test_file}")

            partial = json.load(file)

            print(f"partial contains {len(partial)} tasks")

            test_data.extend(partial)

    print(f"Loaded {len(test_data)} tasks!")

    return test_data

def get_task_from_results(results):

    for result in results:
        if "input" in result:

            inputs = result['input']

            task_desc = None

            for input in inputs:
                _temp = re.findall("(?<=Task: ).+(?=\\nTrajectory)", input['content'], re.DOTALL)
                if(len(_temp)>0):
                    task_desc = _temp[0]
                

            return task_desc

def get_task(task_desc, tasks):

    print(f"Looking for task: {task_desc}")
    for task in tasks:
        if task['confirmed_task'].startswith(task_desc):
            return task

def main():
    parser = create_parser()
    args = parser.parse_args()

    # Clear database file if it already exists
    # if os.path.exists(args.db_path):
    #     os.remove(args.db_path)

    analyzer = Analyzer(args.db_path)
    analyzer.create_table() # Set up results table in sqlite

    result_dir = os.fsencode(args.result_dir)
    
    
    test_data = load_test_data(args.test_data_dir)

    for t in test_data:
        print(t['confirmed_task'])

    result_files = [os.fsdecode(x) for x in os.listdir(result_dir) if os.fsdecode(x).endswith(".json")]
    result_files.sort()



    for result_file in result_files:
        
        with open(os.path.join(args.result_dir, result_file), 'r') as file:

            print(f"Processing result file: {result_file}")

            results = json.load(file)

            

            task_description = get_task_from_results(results) # get the test task description corresponding with this results file
            print(f"Task description from results was: {task_description}") 
            
            if task_description == None:
                continue #This can happen if none of the steps worked for a task, for example if all steps did not have the ground truth element in the abstracted state
            
            task_info = get_task(task_description, test_data) # use the task description to find the correct task from the loaded test data
            print(f"task_info is None: {task_info == None}")

            print(f"Task from results: {task_description} Task from test data: {task_info['confirmed_task']}")


            task_actions = task_info['actions']
            print(f"{len(task_actions)} actions for task.")
            _data = []



            _action_index = 0
            _results_index = 0
            while(_results_index < len(results)):
                print(f"_results_index: {_results_index} _action_index: {_action_index}")
                result = results[_results_index]
                print(f"result type: {type(result)}")

                if 'output' in result and result['output'].startswith("FAILED DUE TO THE CONTEXT LIMIT"):
                    # Skip past actions whose contexts were too large to process.
                    _results_index += 1 
                    _action_index += 1
                    pass

                elif 'input' in result:
                    
                    action_info = task_actions[_action_index]
                    prediction = results[_results_index + 1]

                    assert "pred_act" in prediction

                    params = analyzer.data_to_parameters(
                        result, prediction, action_info, task_info['annotation_id'],
                        task_info['website'], task_info['confirmed_task'], args.result_dir 
                    )

                    #print(f"Made params for {action_info['action_uid']}")
                
                    _data.append(params)

                    _results_index += 2
                    _action_index += 1

                    pass
                elif 'pred_act' in result:
                    print("This should never happen")
                    pass
                elif result == "The ground truth element is not in cleaned html":
                    _results_index += 1
                    _action_index += 1
                    pass
                elif "element_acc" in result:
                    _results_index += 1
                    pass
            
            analyzer.save(_data)


        
    analyzer.finish()
    pass
    

if __name__ == "__main__":
    main()
