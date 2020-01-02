import tagme
import spotlight
import re, string, random
import requests

class Annotator: 
    def __init__(self, config):
        self.annotator_name = config["annotator"]["name"]
        self.token = config["annotator"]["token"]
        self.threshold = config["annotator"]["threshold"]
        self.query_description = ""
        
    def annotate(self, query, document):
        if self.annotator_name == "tagme":             
            tagme_annotations = tagme.annotate(document)
            processed_annotations = []
            for tagme_annotation in tagme_annotations.get_annotations(self.threshold): 
                annotation = Annotation(query)
                annotation.mention = tagme_annotation.mention
                annotation.annotation_score = tagme_annotation.score 
                annotation.entity_id = tagme_annotation.entity_id
                #annotation.process_tagme_annotation()
                processed_annotations.append(annotation)
            return processed_annotations 

        elif self.annotator_name == "spotlight":
            spotlight_annotations = spotlight.annotate('http://model.dbpedia-spotlight.org/en/annotate', document, confidence=0., support=20)
            processed_annotations = []
            for spotlight_annotation in spotlight_annotations: 
                annotation = Annotation(query)
                annotation.mention = spotlight_annotation['surfaceForm']
                annotation.annotation_score = spotlight_annotation['similarityScore']
                annotation.URI = spotlight_annotation['URI']
                annotation.process_spotlight_annotation()
                processed_annotations.append(annotation)
            return processed_annotations 

        else:
            print("no annotator selected")
            return None


class Annotation: 
    def __init__(self, query):
        self.mention = ""
        self.annotation_score = -1
        self.entity_id = -1
        self.abstract = ""
        self.similarity_score = 1
        self.query = query 
        self.URI = ""
    
    def clean_text(self, text):
        """  Remove everything but whitespace, the alphabet. Separate apostrophes for stopwords  """
        st = re.sub(r"[^a-z\s']", '', text.lower())
        st = re.sub(r"[']+", ' ', st)
        return st

    def get_jaccard_sim(self, query, abstract): 
        query = self.clean_text(query)
        abstract = self.clean_text(abstract)
        a = set(query.split()) 
        b = set(abstract.split())
        c = a.intersection(b)
        return float(len(c)) / (len(a) + len(b) - len(c))

    def get_abstract(self, title):
        
        response = requests.get('http://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&explaintext=1&titles=' + title)

        d = response.json()["query"]["pages"]

        abstract = ""
        for key in d.keys():
            if 'extract' in d[key].keys():
                result = d[key]["extract"]
                paragraphs = result.split("\n")

                for paragraph in paragraphs:
                    if paragraph.startswith("=="):
                        break
                    abstract += paragraph
                
        return abstract

    def process_spotlight_annotation(self):
        dbpedia_link = self.URI
        title = dbpedia_link.split("/")[-1]
        abstract = self.get_abstract(title) 
        self.similarity_score = self.get_jaccard_sim(self.query, abstract)


    # def process_tagme_annotation(self):
    #     return self 





    
    