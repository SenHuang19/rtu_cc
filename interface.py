''' Generic Interface '''

import json, time, datetime

import pandas as pd

import requests

import ast

def work(url):
	''' Run the model in its directory. '''
	# Delete output file every run if it exists

	u={}
    
	with open('./input') as f: 
         data = f.read() 

	u = json.loads(data)    
    
    
	json_object = json.dumps(u, indent = 4,default=str)
    
              
	result = requests.post('{0}/run'.format(url),headers={"Content-type":"application/json"}, data=json_object).json()
        
	result = pd.DataFrame.from_dict(result)
    
	result.to_csv('result.csv')
    
    
	return result

work('http://127.0.0.1:5000')