# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% Change working directory from the workspace root to the ipynb file location. Turn this addition off with the DataScience.changeDirOnImportExport setting
# ms-python.python added
import os
from DataLoader import DataLoader
import json 
from DataLoader import extract_description_and_narrative
from Annotation import Annotation
# %%
import pandas as pd 
import os 
print(os.getcwd())
data = pd.read_csv("small_data/rob_document_mentions.data", sep="\t")
data_file = open("small_data/rob_document_mentions.data")

qrel = pd.read_csv("small_data/rob_entity_ranking.qrel", sep=" ", header=None)
config = json.load(open("code/config.json"))
data_loader = DataLoader(config)
query2reldocids = data_loader.get_relevant_docids()
print("data loaded")


# %%
qrel.iloc[:,[2]]


# %%
print("printing data columns")
column_str = ""
for col in data.columns: 
    column_str+= col + "\t"
print(column_str) 


# %%
entity2judgement = {}
print(len(list(set(data["dbpedia_entity"][0:]))))
print(len(list(set(qrel.iloc[:,2]))))
data_entities = sorted(list(set(data["dbpedia_entity"][0:])))
qrel_entities = sorted(list(set(qrel.iloc[:,2])))
print(data_entities[0:10])
print(qrel_entities[0:10])

for index, row in qrel.iterrows():
    qid = str(row[0]).strip()
    eid = str(row[2]).strip()
    judgement = str(row[3]).strip()
    entity2judgement.setdefault(qid, {})
    entity2judgement[qid][eid] = float(judgement)


# %%
print(len(entity2judgement))
#print(entity2judgement)
# %%
#rob04_qid	query	dbpedia_entity	entity_frq_ttr	rob04_doc	mention	offset	context_size1 context_size2 context_size3

import json 

query2doc = {} 
query2entity = {}
query2text = {}
print("data length {}".format(data.shape))
next(data_file)
for line in data_file:    
    line_splitted = line.split("\t")
    qid = line_splitted[0].strip()
    query = line_splitted[1].strip()
    entity = line_splitted[2].strip()
    #if qid == "649":
    #    print(row)
    #    print(entity)
    document = line_splitted[4].strip()

    query2text.setdefault(qid, "")
    query2doc.setdefault(qid, {})
    query2doc[qid].setdefault(document, [])
    query2entity.setdefault(qid, [])
    
    query2text[qid] = query
    
    #we will only consider queries for which there is something in the qrel file.
    #entity2judgement should be actually entity2judgement_per_query
        
    if qid in entity2judgement:
        entity_dict = entity2judgement[qid]
        if entity in entity_dict:
            judgement = entity_dict[entity]
            query2entity[qid].append((entity, judgement))
            query2doc[qid][document].append((entity, judgement))
        else:
            query2entity[qid].append((entity, 0.0))
            query2doc[qid][document].append((entity, 0.0))


# %%
# for qid in query2entity:
#     entities = query2entity[qid]
#     entities = sorted(entities, key=lambda x: x[1], reverse=True)
#     query2entity[qid] = entities 

#print("")
print(sorted(query2entity['649'], key=lambda x:x[1], reverse=True))
# pass



# %%
import os
result_dir = "result/oracle"

count_rel = 0
count_non_rel = 0
number_of_documents_to_explain_per_query = 19
number_of_entities_in_explanation = 2
topic_description_dict = json.load(open(os.path.join(config["data"], config["dataset"]["name"], config["files"]["query_description"])))

for qid in query2doc:
    if qid in query2entity:
        if len(query2entity[qid]) > 0:
            documents = query2doc[qid]
            description, _ = extract_description_and_narrative(topic_description_dict[qid])
            judged_entities = query2entity[qid]
            judged_entities = sorted(judged_entities, key=lambda x:x[1], reverse=True)
            reldocids = set(query2reldocids[str(qid)])
            #print(judged_entities)
            for document in list(documents.keys())[0:number_of_documents_to_explain_per_query]:            
                judged_entities_present = []
                judged_entities_absent = []
                entities = documents[document]
                document_entity_set = set([entity[0] for entity in entities])
                judged_entity_set = set()
                for entity in judged_entities:
                    entity_string = entity[0]
                    judged_entity_set.add(entity_string)
                    judgement = entity[1]
                    if entity_string in document_entity_set:
                        judged_entities_present.append((entity_string, judgement))
                    else:
                        judged_entities_absent.append((entity_string, judgement))
                #print(judged_entity_set)
                present_set = set()
                absent_set = set()
                for entity in judged_entities_present:
                    present_set.add(entity[0])
                    if len(present_set) >= number_of_entities_in_explanation:
                        break
                
                for entity in judged_entities_absent:
                    absent_set.add(entity[0])
                    if len(absent_set) >= number_of_entities_in_explanation:
                        break
                relevance = ""
                output_file =""
                if document in reldocids:
                    relevance = "relevant"
                    count_rel+=1
                    output_file = open(os.path.join(result_dir, "rel", str(count_rel) + ".txt"), "w")
                else:
                    relevance = "non-relevant"
                    count_non_rel+=1
                    output_file = open(os.path.join(result_dir, "non-rel", str(count_non_rel) + ".txt"), "w")


                output_file.write("Assume that you have issued the following query to a web search engine\n\n")
                output_file.write ("*** qid: {} Query: {} ***\n\n".format(qid, query2text[qid]))            
                output_file.write ("--- Query Description: {} ---\n\n".format(description))            
                output_file.write("Now assume the search engine retrieved a document. We are showing a few entities that are present in the document and a few entities that absent\n\n")
                #output_file.write("Entity snippet for document {}\n".format(document))
                output_file.write("Entities present: {}\n".format(present_set))
                
                for entity in present_set:
                    annotation = Annotation("")
                    abstract = annotation.get_abstract(entity)
                    print("{} : {}".format(entity, abstract))
                #print(judged_entities_present[0:3])
                output_file.write("Entities missing: {}\n\n".format(absent_set))     

                for entity in absent_set:
                    annotation = Annotation("")
                    abstract = annotation.get_abstract(entity)
                    print("{} : {}".format(entity, abstract))
                
                output_file.write("Would you click this document?\n")
                output_file.write("How likely it is for you to click this document in a scale from 1-5?\n\n")

                #output_file.write("Document is {}\n".format(relevance))
                output_file.close()
                #print(judged_entities_absent[0:3])
                #break
            #output_file.write("--------------------------------------------------\n")
            #break


#output_file.close()


# %%


