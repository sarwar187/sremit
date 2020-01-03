import os 
import random 
from sklearn.metrics import confusion_matrix
import time
import json 
from sklearn.metrics import accuracy_score

rel_dir = os.path.join(os.getcwd(), "result", "oracle", "rel")
non_rel_dir = os.path.join(os.getcwd(), "result", "oracle", "non-rel")

rel_list = os.listdir(rel_dir)
non_rel_list = os.listdir(non_rel_dir)

user_graded = []
user = []
truth = []

timestr = time.strftime("%Y%m%d-%H%M%S")
file_to_write = open(timestr, "w")
output_dict = {}
for i in range(5):
    sel = random.randint(1,2)
    if sel == 1:
        file_id = random.randint(1, len(rel_list))
    else:
        file_id = random.randint(1, len(non_rel_list))

    text = open(os.path.join(rel_dir, str(file_id) + ".txt")).read()
    print(text)
    print("please input two integers to answer the two above questions\n")
    print("the first value should be between [0,1]")
    print("the second value should be between [0,4]")
    
    input_binary = input()
    
    user.append(int(input_binary))

    if sel == 1:
        truth.append(1)
    else:
        truth.append(0) 
    
    input_graded = input()

    user_graded.append(int(input_graded))
    output_dict["user"] = user
    output_dict["truth"] = truth
    output_dict["user_graded"] = user_graded

json.dump(output_dict, file_to_write)
print("Your accuracy is {}".format(accuracy_score(truth, user)))   
#print(confusion_matrix(truth, user))

#print(rel_count)
#print(non_rel_count)