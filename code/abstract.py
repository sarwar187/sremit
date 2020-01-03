import tagme
import spotlight
import re, string, random
import requests



def get_abstract(title):
        
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


print(get_abstract('Union_of_South_Africa'))