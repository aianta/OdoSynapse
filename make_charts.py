#import matplotlib as plt
import argparse
import os
import json

global_results = {
    'ground_truth_element_missing': 0,
    'ground_truth_element_missing_%': 0.0,
    'element_acc': 0,
    'element_acc_possible': 0,
    'element_acc_%': 0.0,
    'action_f1': 0.0,
    'action_f1_possible': 0.0,
    'action_f1_%':0.0,
    'step_success': 0,
    'step_success_possible': 0,
    'step_success_%': 0.0,
    'task_success': 0 ,
    'task_success_possible': 0,
    'task_success_%': 0.0
}


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_dir", type=str)
    
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    print("Loading results from: ", args.test_dir)

    # https://stackoverflow.com/questions/10377998/how-can-i-iterate-over-files-in-a-given-directory
    test_dir = os.fsencode(args.test_dir)
    for file in os.listdir(test_dir):
        filename = os.fsdecode(file)

        with open(os.path.join(args.test_dir,filename), 'r') as result_file:
            result_data = json.load(result_file)

            global_results['ground_truth_element_missing'] = global_results['ground_truth_element_missing'] + count_ground_truth_elements_missing(result_data)

            # The results are in the last element of the json array
            result_object = result_data[len(result_data)-1]

            element_acc = result_object['element_acc']
            action_f1 = result_object['action_f1']
            step_success = result_object['step_success']
            task_success = result_object['success']

            # Tally element_acc
            tally('element_acc', element_acc)
            compute_percent('element_acc')

            # Tally action f1
            tally('action_f1', action_f1)
            compute_percent('action_f1')

            # Tally step success
            tally('step_success', step_success)
            compute_percent('step_success')

            # Tally task success
            tally('task_success', task_success)
            compute_percent('task_success')

            

    # Compute % not attempted because of ground truth element missing
    global_results['ground_truth_element_missing_%'] = global_results['ground_truth_element_missing'] / global_results['element_acc_possible']

    print(global_results)

def compute_percent(field_name):
    global_results[field_name + '_%'] = global_results[field_name] / global_results[field_name + '_possible']

def tally(field_name, results):
    for sample in results:
        global_results[field_name] = global_results[field_name] + sample
        global_results[field_name + '_possible'] = global_results[field_name + '_possible'] + 1

def count_ground_truth_elements_missing(results):
    count = 0
    for element in results:
        if element == "The ground truth element is not in cleaned html":
            count = count + 1
    
    return count

if __name__ == "__main__":
    main()




