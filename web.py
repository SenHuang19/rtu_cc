from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
import subprocess
import os
from wrapper import load_template
from shutil import copyfile
import pandas as pd
import os



app = Flask(__name__)
api = Api(app)


import json


class run(Resource):
    '''Interface to cancel a optimization.'''    
    def post(self):   
        inputs = request.get_json(force=True)       
        data = inputs['input']
        os.chdir('/home/developer/idf')  
        src = './template/climate/{}'.format(data['climate'])
        dst = 'output/climates'
        copyfile(src, dst)
        load_template('./template/construction','wall_roof.template','output','wall_roof',data)
        load_template('./template/construction','window.template','output','window',data)
        load_template('./template/construction','FenestrationSurface.template','output','FenestrationSurface',data)
        load_template('./template/schedule','HVACOperationSchd.template','output','HVACOperationSchd',data)
        load_template('./template/schedule','CLGSETP_SCH_NO_OPTIMUM.template','output','CLGSETP_SCH_NO_OPTIMUM',data)
        load_template('./template/schedule','HTGSETP_SCH_NO_OPTIMUM.template','output','HTGSETP_SCH_NO_OPTIMUM',data)
        load_template('./template/devices','MinOAFraction.template','output','MinOAFraction',data)
        load_template('./template/devices','cooling_coil.template','output','cooling_coil',data)
        load_template('./template/devices','heating_coil.template','output','heating_coil',data)
        load_template('./template/controller','outdoor_air_control.template','output','outdoor_air_control',data)
        load_template('./template/ems','ems_pr.template','output','ems_pr',data)
        load_template('./template/curve','FanPowerCurve.template','output','FanPowerCurve',data)
        load_template('./template/curve','HPACCOOLEIRFT.template','output','HPACCOOLEIRFT',data)
        load_template(['template/global','output'],'output.template','output','output.idf',data)
        weatherPath = '/home/developer/idf/wea/{}.epw'.format(data['climate'])
        os.chdir('/home/developer/idf/output')
        cmdStr= "energyplus -w \"%s\" -r \"%s\"" % (weatherPath, 'output.idf')
        simulation = subprocess.Popen(cmdStr, shell=True)
        simulation.wait()
       
        simulation_result=pd.read_csv('/home/developer/idf/output/eplusout.csv')
        
        f=open('/home/developer/idf/output/eplustbl.csv')
        tab1=f.readlines()
        f.close()
        
        result={}
        result['tab1'] = tab1
        for i in range(len(inputs['output'])):
             result[inputs['output'][i]] = simulation_result[inputs['output'][i]].tolist()
        os.chdir('/home/developer/idf')  
        load_template('./template/devices','cooling_coil_upgrade.template','output','cooling_coil',data)
        load_template('./template/devices','heating_coil_upgrade.template','output','heating_coil',data)
        load_template('./template/controller','outdoor_air_control_upgrade.template','output','outdoor_air_control',data)
        load_template('./template/ems','ems_pr_upgrade.template','output','ems_pr',data)
        load_template('./template/curve','FanPowerCurve_upgrade.template','output','FanPowerCurve',data)
        load_template('./template/curve','HPACCOOLEIRFT_upgrade.template','output','HPACCOOLEIRFT',data)
        load_template(['template/global','output'],'output.template','output','output.idf',data)  
        os.chdir('/home/developer/idf/output')
        simulation = subprocess.Popen(cmdStr, shell=True)
        simulation.wait()
       
        simulation_result=pd.read_csv('/home/developer/idf/output/eplusout.csv')
        for i in range(len(inputs['output'])):
             result[inputs['output'][i]+'_upgrade'] = simulation_result[inputs['output'][i]].tolist()       

        f=open('/home/developer/idf/output/eplustbl.csv')
        tab2=f.readlines()
        f.close()
        result['tab2'] = tab2   
        return result 
        

api.add_resource(run, '/run')


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
