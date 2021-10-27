from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
import subprocess
import os
from wrapper import load_template
from shutil import copyfile
import pandas as pd
import os
import flask
import traceback
import psutil
from os.path import exists


app = Flask(__name__)
api = Api(app)


import json

max_number_worker = 2

number_workers = 0

class run(Resource):
    '''Interface to cancel a optimization.'''    
    def post(self):   
        inputs = request.get_json()       
        data = inputs['input']
        os.chdir('/home/developer/idf')
        if 'climate' in data:        
            src = './template/climate/{}'.format(data['climate'])
            dst = 'output/climates'
        else:
            return flask.jsonify({'error': 'missing climate', 'message': None})
        if not 'id' in data:        
            return flask.jsonify({'error': 'missing id', 'message': None})
        try:
            copyfile(src, dst)
        except:
            return flask.jsonify({'error': 'no such climate: {}'.format(data['climate']), 'message': None})
        try:     
            load_template('./template/construction','wall_roof.template','output','wall_roof',data)                     
            load_template('./template/construction','window.template','output','window',data)           
            load_template('./template/{}/construction'.format(data['BuildingType']),'FenestrationSurface.template','output','FenestrationSurface',data)         
            load_template('./template/schedule','HVACOperationSchd.template','output','HVACOperationSchd',data)                   
            load_template('./template/schedule','CLGSETP_SCH_NO_OPTIMUM.template','output','CLGSETP_SCH_NO_OPTIMUM',data)
            load_template('./template/schedule','HTGSETP_SCH_NO_OPTIMUM.template','output','HTGSETP_SCH_NO_OPTIMUM',data)
            load_template('./template/{}/devices'.format(data['BuildingType']),'MinOAFraction.template','output','MinOAFraction',data)
            load_template('./template/{}/devices'.format(data['BuildingType']),'cooling_coil.template','output','cooling_coil',data)
            load_template('./template/{}/devices'.format(data['BuildingType']),'heating_coil.template','output','heating_coil',data)
            load_template('./template/{}/controller'.format(data['BuildingType']),'outdoor_air_control.template','output','outdoor_air_control',data)
            load_template('./template/{}/ems'.format(data['BuildingType']),'ems_pr.template','output','ems_pr',data)
            load_template('./template/{}/curve'.format(data['BuildingType']),'FanPowerCurve.template','output','FanPowerCurve',data)
            load_template('./template/{}/curve'.format(data['BuildingType']),'HPACCOOLEIRFT.template','output','HPACCOOLEIRFT',data)
            load_template(['template/{}/global'.format(data['BuildingType']),'output'],'output.template','output','output1.idf',data)
        except:
            Err = traceback.format_exc()
            return flask.jsonify({'error': Err, 'message': None})        
       
        weatherPath = '/home/developer/idf/wea/{}.epw'.format(data['climate'])
        os.chdir('/home/developer/idf/output')
        cmdStr= "energyplus -w \"%s\" -r \"%s\"" % (weatherPath, 'output1.idf')
        global number_workers
        global max_number_worker
        if number_workers < max_number_worker:
           number_workers = number_workers + 1
           simulation = subprocess.Popen(cmdStr, shell=True)
           with open('{}.pid'.format(data['id']),'w', encoding='utf-8') as pPidFile:        
                pPidFile.write(str(simulation.pid))             
           simulation.wait()
           simulation_result=pd.read_csv('/home/developer/idf/output/eplusout.csv')
           number_workers = number_workers - 1
        else:
            return flask.jsonify({'error': 'no available worker', 'message': None})           

        f=open('/home/developer/idf/output/eplustbl.csv')
        tab1=f.readlines()
        f.close()
        
        result={}
        result['tab1'] = tab1
        if 'output' in inputs: 
           for i in range(len(inputs['output'])):
                  result[inputs['output'][i]] = simulation_result[inputs['output'][i]].tolist()
        os.chdir('/home/developer/idf')  
        try:   
           load_template('./template/{}/devices'.format(data['BuildingType']),'cooling_coil_upgrade.template','output','cooling_coil',data)
           load_template('./template/{}/devices'.format(data['BuildingType']),'heating_coil_upgrade.template','output','heating_coil',data)
           load_template('./template/{}/devices'.format(data['BuildingType']),'MinOAFraction_upgrade.template','output','MinOAFraction',data)
           load_template('./template/{}/controller'.format(data['BuildingType']),'outdoor_air_control_upgrade.template','output','outdoor_air_control',data)
           load_template('./template/{}/ems'.format(data['BuildingType']),'ems_pr_upgrade.template','output','ems_pr',data)
           load_template('./template/{}/curve'.format(data['BuildingType']),'FanPowerCurve_upgrade.template','output','FanPowerCurve',data)
           load_template('./template/{}/curve'.format(data['BuildingType']),'HPACCOOLEIRFT_upgrade.template','output','HPACCOOLEIRFT',data)
           load_template(['template/{}/global'.format(data['BuildingType']),'output'],'output.template','output','output2.idf',data)  
        except:
            Err = traceback.format_exc()
            return flask.jsonify({'error': Err, 'message': None})
        os.chdir('/home/developer/idf/output')
        cmdStr= "energyplus -w \"%s\" -r \"%s\"" % (weatherPath, 'output2.idf')        

        if number_workers < max_number_worker:
           number_workers = number_workers + 1
           simulation = subprocess.Popen(cmdStr, shell=True)
           with open('{}.pid'.format(data['id']),'w', encoding='utf-8') as pPidFile:        
                pPidFile.write(str(simulation.pid))             
           simulation.wait()
           simulation_result=pd.read_csv('/home/developer/idf/output/eplusout.csv')
           number_workers = number_workers - 1
        else:
            return flask.jsonify({'error': 'no available worker', 'message': None})
        if 'output' in inputs:             
            for i in range(len(inputs['output'])):
                  result[inputs['output'][i]+'_upgrade'] = simulation_result[inputs['output'][i]].tolist()       

        f=open('/home/developer/idf/output/eplustbl.csv')
        tab2=f.readlines()
        f.close()
        result['tab2'] = tab2   
        return flask.jsonify({'error': None, 'message': result}) 
        

class cancel(Resource):

    '''Interface to cancel a optimization.''' 
   
    def put(self):
    
        inputs = request.get_json()

        if not ('id' in inputs):

           return {'cancel_status':False}

        file_exists = exists('{}.pid'.format(inputs['id']))

        if not file_exists:

           return {'cancel_status':False}                   
        
        f = open('{}.pid'.format(inputs['id']), "r")
        
        pid = int(f.read())
        
        if not psutil.pid_exists(pid):
           
           return {'cancel_status':False}
        
        parent = psutil.Process(pid)
        
        for child in parent.children(recursive=True):  # or parent.children() for recursive=False
        
                child.kill()
                
        parent.kill()
        
        return {'cancel_status':True} 

api.add_resource(cancel, '/cancel')

api.add_resource(run, '/run')


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=81,debug=True)
