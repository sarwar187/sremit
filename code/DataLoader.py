import os 
import glob 
import tagme
import glob 
import ast 
import json 
import spotlight 
from Annotation import Annotator

class DataLoader:
    
    def __init__(self, config):
        self.config = config
        self.dataset = config["dataset"]
        self.annotator = config["annotator"]
        self.topk = int(config["topk"])
        self.concepts_per_document = int(config["concepts_per_document"])

    def annotate_documents(self, annotated_docs_dir, query_to_relevant_docids, topic_description_dict, config):
        config = self.config
        query_to_keywords_list = {}
        if os.path.exists(os.path.join(annotated_docs_dir, config["files"]["document_to_entities"])):
            query_to_keywords_list = json.load(open(os.path.join(annotated_docs_dir, config["files"]["document_to_entities"])))
        else: 
            annotator = Annotator(config)
            query_to_doc_dir = os.path.join(config["data"], config["dataset"]["name"], config["directories"]["query_to_docs"]) 
            query_files = query_to_doc_dir + "/*.json" 
            files = glob.glob(query_files)
            for file in files: 
                query_id = file.split("/")[-1].split(".")[0]
                description, _ = extract_description_and_narrative(topic_description_dict[query_id])
                print(query_id)
                print(description)
                query_dict = json.load(open(file))
                keyword_set_documents = []
                    
                if query_id in query_to_relevant_docids.keys():
                    for i in range(self.topk):
                        print("annotation begins")
                        annotated_list = []
                        text_annotations = annotator.annotate(description, query_dict['docs'][i]['doc_text'])
                        doc_id = query_dict['docs'][i]['doc_id']
                        rel = 0
                        if doc_id in query_to_relevant_docids[query_id]:
                            rel = 1 
                        else:
                            rel = 0
                        for annotation in text_annotations:
                            annotated_list.append((annotation.mention, annotation.annotation_score * annotation.similarity_score, annotation.annotation_score, annotation.entity_id, annotation.similarity_score, annotation.query, annotation.URI, annotation.abstract))
                        sorted(annotated_list,key=lambda x: x[1], reverse=True)
                        keyword_set_documents.append((annotated_list[0:self.concepts_per_document], query_dict['docs'][i]['score'], rel))
                        print("annotation ends")
                    query_to_keywords_list[query_id] = keyword_set_documents
                else: 
                    print("relevant document missing for query id {}".format(query_id))
                    query_to_keywords_list[query_id] = keyword_set_documents
                #break
            with open(os.path.join(annotated_docs_dir, config["files"]["document_to_entities"]), 'w') as f:
                json.dump(query_to_keywords_list, f)
        return query_to_keywords_list
        
    def get_relevant_docids(self):
        config = self.config
        relevant_docs_directory = os.path.join(config["data"], config["dataset"]["name"], config["directories"]["query_to_rel_docids"]) 
        print("directory of all the relevant docs {}".format(relevant_docs_directory))
        relevant_doc_files = glob.glob(relevant_docs_directory + "/*")
        query_to_relevant_docids = {}

        for relevant_doc_file in relevant_doc_files:
            query_id = relevant_doc_file.split("/")[-1].split("_")[0].strip()
            document_ids = set()
            for line in open(relevant_doc_file):
                document_ids.add(line.strip())
            query_to_relevant_docids[query_id] = document_ids
        
        return query_to_relevant_docids

    def get_query_performance(self):
        config = self.config 
        hard_query_list = ast.literal_eval(open(os.path.join(config["data"], config["dataset"]["name"], config["files"]["query_performance"])).readline())
        hard_query_dict = {}
            
        for hard_query in hard_query_list:
            hard_query_dict.setdefault(hard_query[0], {})
            hard_query_dict[hard_query[0]]["performance"] = hard_query[1]
        
        #print(hard_query_dict)
        query_to_doc_dir = os.path.join(config["data"], config["dataset"]["name"], config["directories"]["query_to_docs"]) 
        query_files = query_to_doc_dir + "/*.json" 
        files = glob.glob(query_files)
        for file in files: 
            query_id = file.split("/")[-1].split(".")[0]
            query_dict = json.load(open(file))
            if int(query_id) in hard_query_dict:
                hard_query_dict[int(query_id)]["query_text"] = query_dict["query_text"]
        return hard_query_dict

    def get_annotated_documents(self, topic_description_dict, config):
        """
        This function will find or create annotated or linked documents using a linker like tagme. 
        """
        config = self.config
        annotated_docs_dir = os.path.join(config["data"], config["dataset"]["name"], config["directories"]["query_to_annotated_docs"], config["annotator"]["name"]) 
        print("annotated documents are in {}".format(annotated_docs_dir))
        return self.annotate_documents(annotated_docs_dir, self.get_relevant_docids(), topic_description_dict, config)
        


def get_valid_queries(query_to_linked_documents):
    """
    returns 
    valid queries: queries for #documents >=3 for QL
    query_to_linked_entities: ranked list of linkable entities against a document
    """
    valid_queries = []
    query_to_linked_entities = {}
    for query in query_to_linked_documents.keys():
        documents = query_to_linked_documents[query]
        query_to_linked_entities.setdefault(query,[])
        for document in documents: 
            entity_list = document[0]
            entity_list = sorted(entity_list, key=lambda x: x[2], reverse=True)
            
            for entity in entity_list[0:config["concepts_per_document"]]:
                entity_string = entity[0]
                linking_score = entity[1]
                query_to_linked_entities[query].append((entity_string, linking_score))
        
        query_to_linked_entities[query] = sorted(query_to_linked_entities[query], key=lambda x: x[1], reverse=True)
        
        #TODO: convert list to set of entities 

        num_relevant_documents = 0
        for document in documents: 
            if document[2] == 1:
                num_relevant_documents+=1    

        if num_relevant_documents < 5:
            valid_queries.append(query)

    return valid_queries, query_to_linked_entities

def extract_description_and_narrative(text):
    text_splitted = text.split("\n")
    desc = 0
    narr = 0
    description = ""
    narrative = ""
    for line in text_splitted: 
        if line.startswith("[<desc>"): 
            desc = 1
        if line.startswith("<narr>"):
            narr = 1
            desc = 0

        if desc == 1 and line.startswith("[<desc>") == False: 
            description+= line.strip() + " " 
        if narr == 1 and line.startswith("<narr>") == False: 
            narrative+= line.strip() + " " 
    return description.strip(), narrative.strip()


def main(config):
    tagme.GCUBE_TOKEN = config["annotator"]["token"]
    data_loader = DataLoader(config)
    topic_description_dict = json.load(open(os.path.join(config["data"], config["dataset"]["name"], config["files"]["query_description"])))
    
    query_to_linked_documents = data_loader.get_annotated_documents(topic_description_dict, config)
    query_performance = data_loader.get_query_performance()
    #the above dictionary contains topic descriptions and narratives 
    valid_queries, query_to_linked_entities = get_valid_queries(query_to_linked_documents)
    print(valid_queries)
    for query in valid_queries:    
        if int(query) in query_performance:
            print(query_performance[int(query)])
            description, _ = extract_description_and_narrative(topic_description_dict[query])
            print(description)
            documents = query_to_linked_documents[query]
            
            
            for document in documents[0: self.topk]:   
                positives = []
                negatives = []

                #if document[2] == 0:  
                print(document[1], document[2])
                concepts_list = document[0]
                concepts_list = sorted(concepts_list, key=lambda x: x[2], reverse=True)
                concepts_set = set()
                for concept in concepts_list:
                    concepts_set.add(concept[0])
                for concept in concepts_list[0:10]:
                    #print(concept[0], concept[1]) 
                    positives.append(concept[0])
                    #query_to_linked_entities.append((keyword[0], keyword[1]))
                
                count = 0
                for item in query_to_linked_entities[query]:
                    if item[0] not in concepts_set:
                        #print(item[0])
                        negatives.append(item[0])
                        count+=1
                    if count == 10:
                        break
                
                print(positives)
                print(negatives)

if __name__ == "__main__":
    config = json.load(open("code/config.json"))
    #print(config)
    print(config["directories"]["query_to_rel_docids"])
    main(config)
        
        