from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
import subprocess
import os
from wrapper import load_template
from shutil import copyfile,rmtree
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

max_number_worker = 10

number_workers = 0

class run(Resource):
    '''Interface to cancel a optimization.'''    
    def post(self):  
        result={} 
        inputs = request.get_json()       
        data = inputs['input']    
        if not 'id' in data:        
            return flask.jsonify({'error': 'missing id', 'message': None})    
        base_dir = '/home/developer/base_{}'.format(data['id'])    
        upgrade_dir = '/home/developer/upgrade_{}'.format(data['id'])        
        if not os.path.exists(base_dir):
                 os.makedirs(base_dir)  
        if not os.path.exists(upgrade_dir):
                 os.makedirs(upgrade_dir)                    

        os.chdir('/home/developer/idf')
        
        if 'climate' in data:        
            src = './template/climate/{}'.format(data['climate'])
            dst1 = '{}/climates'.format(base_dir)
            dst2 = '{}/climates'.format(upgrade_dir)            
        else:
            return flask.jsonify({'error': 'missing climate', 'message': None})

        try:
            copyfile(src, dst1)
            copyfile(src, dst2)            
        except:
            return flask.jsonify({'error': 'no such climate: {}'.format(data['climate']), 'message': None})
        weatherPath = '/home/developer/idf/wea/{}.epw'.format(data['climate'])
            
        try:
            if data['BuildingType'] == 'Warehouse':
                 load_template('./template/{}/construction'.format(data['BuildingType']),'wall_roof.template',base_dir,'wall_roof',data)                     
                 load_template('./template/{}/construction'.format(data['BuildingType']),'window.template',base_dir,'window',data)
                 load_template('./template/{}/construction'.format(data['BuildingType']),'wall_roof.template',upgrade_dir,'wall_roof',data)                     
                 load_template('./template/{}/construction'.format(data['BuildingType']),'window.template',upgrade_dir,'window',data)                  
            else:
                 load_template('./template/construction','wall_roof.template',base_dir,'wall_roof',data)                     
                 load_template('./template/construction','window.template',base_dir,'window',data)
                 load_template('./template/construction','wall_roof.template',upgrade_dir,'wall_roof',data)                     
                 load_template('./template/construction','window.template',upgrade_dir,'window',data)                    
            load_template('./template/{}/construction'.format(data['BuildingType']),'FenestrationSurface.template',base_dir,'FenestrationSurface',data)         
            load_template('./template/schedule','HVACOperationSchd.template',base_dir,'HVACOperationSchd',data)                   
            load_template('./template/schedule','CLGSETP_SCH_NO_OPTIMUM.template',base_dir,'CLGSETP_SCH_NO_OPTIMUM',data)
            load_template('./template/schedule','HTGSETP_SCH_NO_OPTIMUM.template',base_dir,'HTGSETP_SCH_NO_OPTIMUM',data)

            load_template('./template/{}/construction'.format(data['BuildingType']),'FenestrationSurface.template',upgrade_dir,'FenestrationSurface',data)         
            load_template('./template/schedule','HVACOperationSchd.template',upgrade_dir,'HVACOperationSchd',data)                   
            load_template('./template/schedule','CLGSETP_SCH_NO_OPTIMUM.template',upgrade_dir,'CLGSETP_SCH_NO_OPTIMUM',data)
            load_template('./template/schedule','HTGSETP_SCH_NO_OPTIMUM.template',upgrade_dir,'HTGSETP_SCH_NO_OPTIMUM',data)
            
            load_template('./template/{}/devices'.format(data['BuildingType']),'MinOAFraction.template',base_dir,'MinOAFraction',data)
            load_template('./template/{}/devices'.format(data['BuildingType']),'cooling_coil.template',base_dir,'cooling_coil',data)
            load_template('./template/{}/devices'.format(data['BuildingType']),'heating_coil.template',base_dir,'heating_coil',data)
            load_template('./template/{}/controller'.format(data['BuildingType']),'outdoor_air_control.template',base_dir,'outdoor_air_control',data)
            load_template('./template/{}/ems'.format(data['BuildingType']),'ems_pr.template',base_dir,'ems_pr',data)
            load_template('./template/{}/curve'.format(data['BuildingType']),'FanPowerCurve.template',base_dir,'FanPowerCurve',data)
            load_template('./template/{}/curve'.format(data['BuildingType']),'HPACCOOLEIRFT.template',base_dir,'HPACCOOLEIRFT',data)
            load_template(['template/{}/global'.format(data['BuildingType']),base_dir],'output.template',base_dir,'output.idf',data)
        except:
            Err = traceback.format_exc()
            return flask.jsonify({'error': Err, 'message': None})        
       
        
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
           try: 
                number_workers = number_workers - 1           
                baseline_df=pd.read_csv(base_dir+'/eplusout.csv')
           except:
                f=open(base_dir+'/output.idf')
                tab=f.readlines()
                f.close()
                result['base_idf'] = tab
                f=open(base_dir+'/eplusout.err')
                tab=f.readlines()
                f.close()
                result['base_err'] = tab 
                result['upgrade_idf'] = ''
                result['upgrade_err'] = ''                
                return flask.jsonify({'error': 'base simulation fails to run', 'message': result})             
           f=open(base_dir+'/output.idf')
           tab=f.readlines()
           f.close()
           result['base_idf'] = tab
           f=open(base_dir+'/eplusout.err')
           tab=f.readlines()
           f.close()
           result['base_err'] = tab
           
        else:
           return flask.jsonify({'error': 'no available worker', 'message': None})           

        os.chdir('/home/developer/idf')  
        try:   
           load_template('./template/{}/devices'.format(data['BuildingType']),'cooling_coil_upgrade.template',upgrade_dir,'cooling_coil',data)
           load_template('./template/{}/devices'.format(data['BuildingType']),'heating_coil_upgrade.template',upgrade_dir,'heating_coil',data)
           load_template('./template/{}/devices'.format(data['BuildingType']),'MinOAFraction_upgrade.template',upgrade_dir,'MinOAFraction',data)
           load_template('./template/{}/controller'.format(data['BuildingType']),'outdoor_air_control_upgrade.template',upgrade_dir,'outdoor_air_control',data)
           load_template('./template/{}/ems'.format(data['BuildingType']),'ems_pr_upgrade.template',upgrade_dir,'ems_pr',data)
           load_template('./template/{}/curve'.format(data['BuildingType']),'FanPowerCurve_upgrade.template',upgrade_dir,'FanPowerCurve',data)
           load_template('./template/{}/curve'.format(data['BuildingType']),'HPACCOOLEIRFT_upgrade.template',upgrade_dir,'HPACCOOLEIRFT',data)
           load_template(['template/{}/global'.format(data['BuildingType']),upgrade_dir],'output.template',upgrade_dir,'output.idf',data)  
        except:
            Err = traceback.format_exc()
            return flask.jsonify({'error': Err, 'message': None})


        os.chdir(upgrade_dir)
        cmdStr= "energyplus -w \"%s\" -r \"%s\"" % (weatherPath, 'output.idf')        

        if number_workers < max_number_worker:
           number_workers = number_workers + 1

           simulation = subprocess.Popen(cmdStr, shell=True)
           with open('{}.pid'.format(data['id']),'w', encoding='utf-8') as pPidFile:        
                  pPidFile.write(str(simulation.pid))             
           simulation.wait()          
           try:   
                number_workers = number_workers - 1           
                upgrade_df=pd.read_csv(upgrade_dir+'/eplusout.csv')           
           except:
                f=open(upgrade_dir+'/output.idf')
                tab=f.readlines()
                f.close()
                result['upgrade_idf'] = tab
                f=open(upgrade_dir+'/eplusout.err')
                tab=f.readlines()
                f.close()    
                result['upgrade_err'] = tab                
                return flask.jsonify({'error': 'upgrade simulation fails to run', 'message': result})               
           
           f=open(upgrade_dir+'/output.idf')
           tab=f.readlines()
           f.close()
           result['upgrade_idf'] = tab
           f=open(upgrade_dir+'/eplusout.err')
           tab=f.readlines()
           f.close()
           result['upgrade_err'] = tab
           
        else:
           return flask.jsonify({'error': 'no available worker', 'message': None})   
            


        os.chdir('/home/developer/idf')          
        config_file = 'config/{}'.format(data['BuildingType'])
        if not os.path.exists(config_file):
                 return flask.jsonify({'error': 'missing config for {}'.format(data['BuildingType']), 'message': None})  
        with open(config_file) as f:         
            temp = f.read()         
        config = json.loads(temp)
        
        if 'ZoneType' in data:        
            zone = data['ZoneType']
        elif 'Orientation' in data:
            zone = data['Orientation']        
        else:
            return flask.jsonify({'error': 'missing orientation or zone type', 'message': None}) 

        if not 'Blended_Electricity_Rate' in data:        

            return flask.jsonify({'error': 'missing blended electricity rate', 'message': None})  

        if not 'Blended_NaturalGas_Rate' in data:        

            return flask.jsonify({'error': 'missing blended gas rate', 'message': None})            
        
        result_baseline = energy_consumption(config['energ_consumption'],baseline_df,data['Blended_Electricity_Rate'],data['Blended_NaturalGas_Rate'])

        result['AnnualElectricityCost_Baseline'] = result_baseline[zone]['ele']
        
        data['AnnualElectricityConsumption_Baseline'] = result_baseline[zone]['ele_kW']        
        
        data['AnnualElectricityCost_Baseline'] = result['AnnualElectricityCost_Baseline']
        
        data['AnnualGasConsumption_Baseline'] = result_baseline[zone]['gas_ccf']            

        result['AnnualNaturalGasCost_Baseline'] = result_baseline[zone]['gas']
               
        data['AnnualNaturalGasCost_Baseline'] = result['AnnualNaturalGasCost_Baseline']  

        data['AnnualConsumption_Baseline'] = result_baseline[zone]['tot_kW']        

        result_upgrade = energy_consumption(config['energ_consumption'],upgrade_df,data['Blended_Electricity_Rate'],data['Blended_NaturalGas_Rate'])

        result['AnnualElectricityCost_Upgrade'] = result_upgrade[zone]['ele']
        
        data['AnnualElectricityConsumption_Upgrade'] = result_upgrade[zone]['ele_kW']           
        
        data['AnnualElectricityCost_Upgrade'] = result['AnnualElectricityCost_Upgrade']

        data['AnnualGasConsumption_Upgrade'] = result_upgrade[zone]['gas_ccf']          

        result['AnnualNaturalGasCost_Upgrade'] = result_upgrade[zone]['gas']
        
        data['AnnualNaturalGasCost_Upgrade'] = result['AnnualNaturalGasCost_Upgrade']  

        data['AnnualConsumption_Upgrade'] = result_upgrade[zone]['tot_kW']                 

        tab = '{}/eplustbl.csv'.format(upgrade_dir)
        
        try:   

             result_size = size(config['size'], tab)

             result['EPlusCoolingSize'] = result_size[zone]['size'] 
             
        except:           
                return flask.jsonify({'error': traceback.format_exc(), 'message': result})                
        
        data['EPlusCoolingSize'] = result['EPlusCoolingSize']  

        try:   
                result_lc = cal_payout(data)                 
        except:           
                return flask.jsonify({'error': traceback.format_exc(), 'message': result})            
     

        result.update(result_lc) 

        rmtree(upgrade_dir) 

        rmtree(base_dir)        
        
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