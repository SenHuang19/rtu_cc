from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
import subprocess
import os
from wrapper import load_template
from shutil import copyfile
import pandas as pd
import os
import flask
from flask import jsonify, make_response
import traceback
from output import size, energy_consumption, cal_payout
import psutil
from os.path import exists

from flask.json import JSONEncoder

 

class StrictEncoder(JSONEncoder):
    def __init__(self, *args, allow_nan=False, **kwargs):
        kwargs["allow_nan"] = allow_nan
        super().__init__(*args, **kwargs)


app = Flask(__name__)
app.json_encoder = StrictEncoder
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
            if data['BuildingType'] == 'Warehouse':
                 load_template('./template/{}/construction'.format(data['BuildingType']),'wall_roof.template','output','wall_roof',data)                     
                 load_template('./template/{}/construction'.format(data['BuildingType']),'window.template','output','window',data)                
            else:
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
            load_template(['template/{}/global'.format(data['BuildingType']),'output'],'output.template','output','output.idf',data)
        except:
            Err = traceback.format_exc()
            return flask.jsonify({'error': Err, 'message': None})        
       
        weatherPath = '/home/developer/idf/wea/{}.epw'.format(data['climate'])
        base_dir = '/home/developer/base_{}'.format(data['id'])
        if not os.path.exists(base_dir):
                 os.makedirs(base_dir)   

        copyfile('/home/developer/idf/output/output.idf', base_dir+'/output.idf')         
        
        os.chdir(base_dir)
        cmdStr= "energyplus -w \"%s\" -r \"%s\"" % (weatherPath, 'output.idf')
        global number_workers
        global max_number_worker
        if number_workers < max_number_worker:
           number_workers = number_workers + 1
           simulation = subprocess.Popen(cmdStr, shell=True)
           with open('{}.pid'.format(data['id']),'w', encoding='utf-8') as pPidFile:        
                pPidFile.write(str(simulation.pid))             
           simulation.wait()
           baseline_df=pd.read_csv('eplusout.csv')
           number_workers = number_workers - 1
        else:
            return flask.jsonify({'error': 'no available worker', 'message': None})           

        os.chdir('/home/developer/idf')  
        try:   
           load_template('./template/{}/devices'.format(data['BuildingType']),'cooling_coil_upgrade.template','output','cooling_coil',data)
           load_template('./template/{}/devices'.format(data['BuildingType']),'heating_coil_upgrade.template','output','heating_coil',data)
           load_template('./template/{}/devices'.format(data['BuildingType']),'MinOAFraction_upgrade.template','output','MinOAFraction',data)
           load_template('./template/{}/controller'.format(data['BuildingType']),'outdoor_air_control_upgrade.template','output','outdoor_air_control',data)
           load_template('./template/{}/ems'.format(data['BuildingType']),'ems_pr_upgrade.template','output','ems_pr',data)
           load_template('./template/{}/curve'.format(data['BuildingType']),'FanPowerCurve_upgrade.template','output','FanPowerCurve',data)
           load_template('./template/{}/curve'.format(data['BuildingType']),'HPACCOOLEIRFT_upgrade.template','output','HPACCOOLEIRFT',data)
           load_template(['template/{}/global'.format(data['BuildingType']),'output'],'output.template','output','output.idf',data)  
        except:
            Err = traceback.format_exc()
            return flask.jsonify({'error': Err, 'message': None})
        upgrade_dir = '/home/developer/upgrade_{}'.format(data['id'])
        if not os.path.exists(upgrade_dir):
                 os.makedirs(upgrade_dir)   

        copyfile('/home/developer/idf/output/output.idf', upgrade_dir+'/output.idf')          
        
        os.chdir(upgrade_dir)
        cmdStr= "energyplus -w \"%s\" -r \"%s\"" % (weatherPath, 'output.idf')        

        if number_workers < max_number_worker:
           number_workers = number_workers + 1
           simulation = subprocess.Popen(cmdStr, shell=True)
           with open('{}.pid'.format(data['id']),'w', encoding='utf-8') as pPidFile:        
                pPidFile.write(str(simulation.pid))             
           simulation.wait()
           upgrade_df=pd.read_csv('eplusout.csv')           
           number_workers = number_workers - 1
        else:
            return flask.jsonify({'error': 'no available worker', 'message': None})   
            
        result={} 

        os.chdir('/home/developer/idf')          
        config_file = 'config/{}'.format(data['BuildingType'])
        if not os.path.exists(config_file):
                 return flask.jsonify({'error': 'missing config for {}'.format(data['BuildingType']), 'message': None})  
        with open(config_file) as f:         
            temp = f.read()         
        config = json.loads(temp)
        
        if 'Orientation' in data:        
            zone = data['Orientation']
        elif 'ZoneType' in data:
            zone = data['ZoneType']        
        else:
            return flask.jsonify({'error': 'missing orientation or zone type', 'message': None}) 

        if not 'Blended_Electricity_Rate' in data:        

            return flask.jsonify({'error': 'missing blended electricity rate', 'message': None})  

        if not 'Blended_NaturalGas_Rate' in data:        

            return flask.jsonify({'error': 'missing blended gas rate', 'message': None})            
        
        result_baseline = energy_consumption(config['energ_consumption'],baseline_df,data['Blended_Electricity_Rate'],data['Blended_NaturalGas_Rate'])

        result['AnnualElectricityCost_Baseline'] = result_baseline[zone]['ele']
        
        data['AnnualElectricityCost_Baseline'] = result['AnnualElectricityCost_Baseline']

        result['AnnualNaturalGasCost_Baseline'] = result_baseline[zone]['gas']
               
        data['AnnualNaturalGasCost_Baseline'] = result['AnnualNaturalGasCost_Baseline']  

        result['AnnualConsumption_Baseline'] = result_baseline[zone]['tot_kW']         

        result_upgrade = energy_consumption(config['energ_consumption'],baseline_df,data['Blended_Electricity_Rate'],data['Blended_NaturalGas_Rate'])

        result['AnnualElectricityCost_Upgrade'] = result_upgrade[zone]['ele']
        
        data['AnnualElectricityCost_Upgrade'] = result['AnnualElectricityCost_Upgrade']         

        result['AnnualNaturalGasCost_Upgrade'] = result_upgrade[zone]['gas']
        
        data['AnnualNaturalGasCost_Upgrade'] = result['AnnualNaturalGasCost_Upgrade']  

        result['AnnualConsumption_Upgrade'] = result_upgrade[zone]['tot_kW']                 

        tab = '{}/eplustbl.csv'.format(upgrade_dir)

        result_size = size(config['size'], tab)

        result['EPlusCoolingSize'] = result_size[zone]['size'] 
        
        data['EPlusCoolingSize'] = result['EPlusCoolingSize']        

        result_lc = cal_payout(data)  

        result.update(result_lc)        
        
        return make_response(jsonify({'error': None, 'message': result}), 200) 
        

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
        global number_workers       
        number_workers = number_workers - 1       
        return {'cancel_status':True} 

api.add_resource(cancel, '/cancel')

api.add_resource(run, '/run')


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=81,debug=True)
