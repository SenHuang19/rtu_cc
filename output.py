import pandas as pd
import json


def isNaN(num):
    return num!= num

def parse_tab(topic, tab):
    with open(tab) as f:
          lines = f.readlines()
    for line in lines:
        if line.find(topic)!=-1:
#           print line
           size = float(line.split(',')[4].replace('\n',''))
           break
    return size       

def energy_consumption(config, df,Blended_Electricity_Rate,Blended_NaturalGas_Rate):
    output = {}
    for key in config:
        ele_consumption = 0
        for item in config[key]['ele']:
               if item in df:
                  ele_consumption = ele_consumption + df[item].iloc[0]
        output[key] = {}                
        output[key]['ele'] = ele_consumption*0.00000027777*Blended_Electricity_Rate
        output[key]['ele_kW'] = ele_consumption*0.00000027777        
        output[key]['tot_kW'] = ele_consumption*0.00000027777
        gas_consumption = 0
        for item in config[key]['gas']:
               if item in df:
                  gas_consumption = gas_consumption + df[item].iloc[0]
        output[key]['gas'] = gas_consumption/105505500*Blended_NaturalGas_Rate
        output[key]['gas_ccf'] = gas_consumption/105505500         
        output[key]['tot_kW'] = output[key]['tot_kW'] + gas_consumption*0.00000027777
    return output        
        
def size(config, tab):
    output = {}
    for key in config:
        size = 0
        for item in config[key]['topic']:
                  size = size + parse_tab(item, tab)
        output[key] = {}                   
        output[key]['size'] = size
    return output   

def cal_payout(input):
    output = {}
    CoolingCapacity = input['CoolingCapacity']*0.293       
    EPlusCoolingSize = input['EPlusCoolingSize'] 
    SizeRatio = CoolingCapacity/EPlusCoolingSize
    output['SizeRatio'] = SizeRatio
    Lifetime = int(input['Lifetime'])   
    AnnualNaturalGasCost_Baseline = input['AnnualNaturalGasCost_Baseline']*SizeRatio
    AnnualElectricityCost_Baseline = input['AnnualElectricityCost_Baseline']*SizeRatio
    AnnualNaturalGasCost_Upgrade = input['AnnualNaturalGasCost_Upgrade']*SizeRatio
    AnnualElectricityCost_Upgrade = input['AnnualElectricityCost_Upgrade']*SizeRatio
    AnnualCosts_Baseline = AnnualNaturalGasCost_Baseline + AnnualElectricityCost_Baseline
    output['AnnualElectricityConsumption_Baseline'] = round(input['AnnualElectricityConsumption_Baseline']*SizeRatio,0)
    output['AnnualGasConsumption_Baseline'] = round(input['AnnualGasConsumption_Baseline']*SizeRatio,0)     
    output['AnnualNaturalGasCost_Baseline'] = round(AnnualNaturalGasCost_Baseline,0)
    output['AnnualElectricityCost_Baseline'] = round(AnnualElectricityCost_Baseline,0) 
    output['AnnualConsumption_Baseline'] = round(input['AnnualConsumption_Baseline']*SizeRatio,0)     
    output['AnnualCosts_Baseline'] = round(AnnualCosts_Baseline,2)
    AnnualCosts_Upgrade = AnnualNaturalGasCost_Upgrade+AnnualElectricityCost_Upgrade
    output['AnnualElectricityConsumption_Upgrade'] = round(input['AnnualElectricityConsumption_Upgrade']*SizeRatio,0)
    output['AnnualGasConsumption_Upgrade'] = round(input['AnnualGasConsumption_Upgrade']*SizeRatio,0)     
    output['AnnualNaturalGasCost_Upgrade'] = round(AnnualNaturalGasCost_Upgrade,0)
    output['AnnualElectricityCost_Upgrade'] = round(AnnualElectricityCost_Upgrade,0) 
    output['AnnualConsumption_Upgrade'] = round(input['AnnualConsumption_Upgrade']*SizeRatio,0)  
    output['AnnualCosts_Upgrade'] = round(AnnualCosts_Upgrade,0)
    RealDiscountRate = input['RealDiscountRate']
    if RealDiscountRate>1:
       RealDiscountRate = RealDiscountRate/100
    CapitalCost_Baseline = input['CapitalCost_Baseline']
    CapitalCost_Upgrade = input['CapitalCost_Upgrade']
    
    a = (1+RealDiscountRate)**Lifetime
    UPV= (a-1)/(RealDiscountRate*a)
    LCC_baseline=CapitalCost_Baseline+(UPV*AnnualCosts_Baseline)
    output['LCC_baseline'] = LCC_baseline
    LCC_upgrade=CapitalCost_Upgrade+(UPV*AnnualCosts_Upgrade)
    output['LCC_upgrade'] = LCC_upgrade
    AC_baseline=LCC_baseline/UPV
    output['AnnualizedCost_Baseline'] = AC_baseline
    AC_upgrade=LCC_upgrade/UPV
    output['AnnualizedCost_Upgrade'] = AC_upgrade
    NPV=LCC_upgrade-LCC_baseline
    output['NPV'] = NPV
    AnnualCostSavings=AnnualCosts_Baseline-AnnualCosts_Upgrade
    CapitalCostSavings=CapitalCost_Baseline-CapitalCost_Upgrade
    if AnnualCostSavings>0:
         SimplePayback=-CapitalCostSavings/AnnualCostSavings
    else:
         SimplePayback=0    
    output['SimplePayback'] = SimplePayback
    DiscountedCosts_baseline=[0]*(Lifetime+1)
    DiscountedCosts_upgrade=[0]*(Lifetime+1)
    DiscountedCosts_baseline[0]=CapitalCost_Baseline
    DiscountedCosts_upgrade[0]=CapitalCost_Upgrade
    DiscountedCostsCumulative_baseline=[0]*(Lifetime+1)
    DiscountedCostsCumulative_upgrade=[0]*(Lifetime+1)
    DiscountedCostsCumulative_baseline[0]=CapitalCost_Baseline
    DiscountedCostsCumulative_upgrade[0]=CapitalCost_Upgrade
    
    for i in range (1, Lifetime+1):
          DiscountedCosts_baseline[i]= AnnualCosts_Baseline*(1/(1+RealDiscountRate)**i)
          DiscountedCosts_upgrade[i]= AnnualCosts_Upgrade*(1/(1+RealDiscountRate)**i)
          DiscountedCostsCumulative_baseline[i]=DiscountedCostsCumulative_baseline[i-1]+DiscountedCosts_baseline[i]
          DiscountedCostsCumulative_upgrade[i]=DiscountedCostsCumulative_upgrade[i-1]+DiscountedCosts_upgrade[i]
    output['DiscountedCostsCumulative_baseline'] = DiscountedCostsCumulative_baseline
    output['DiscountedCostsCumulative_upgrade'] = DiscountedCostsCumulative_upgrade    
    
    baseline_check = CapitalCost_Baseline

    upgrade_check = CapitalCost_Upgrade

    diff = 1000000000000000

    ss = 0
    for i in range(1, Lifetime+1):
          baseline_check= baseline_check+AnnualCosts_Baseline*(1/(1+RealDiscountRate)**i)
          upgrade_check= upgrade_check+AnnualCosts_Upgrade*(1/(1+RealDiscountRate)**i)
          if abs(baseline_check-upgrade_check)<diff:
               diff = abs(baseline_check-upgrade_check)
               index_record = i
          ss = ss + 1
    output['Payback'] = index_record  
    n=0
    NPV_min=10000
    error = 1000
    RateOfReturn=None
    x=10
    while abs(error)>0.05:
       n=n+1
       a= (1+x/1000)**Lifetime
       UPV= (a-1)/(RealDiscountRate*a)
       LCC_baseline=CapitalCost_Baseline+(UPV*AnnualCosts_Baseline)
       LCC_upgrade=CapitalCost_Upgrade+(UPV*AnnualCosts_Upgrade)
       NPV=LCC_upgrade-LCC_baseline
       error=NPV
       x=x+error/50
       if abs(NPV)<abs(NPV_min):
           NPV_min2=NPV
           RateOfReturn=x/1000
       if n>100:
           error=0          
    output['RateOfReturn'] = RateOfReturn
    if CapitalCost_Upgrade>CapitalCost_Baseline:
         SIR= (AnnualCosts_Baseline-AnnualCosts_Upgrade)/(CapitalCost_Upgrade-CapitalCost_Baseline)
    else:
         SIR= 0    
    output['SIR'] = SIR
    for key in output:
        if isNaN(output[key]):
           output[key] = None        
    return output
    


if __name__ == "__main__":  
  
   with open('./input2') as f: 
       data = f.read() 

   u = json.loads(data)['input'] 

   config_file = 'config/{}'.format(u['BuildingType'])

   with open(config_file) as f: 
       data = f.read() 

   config = json.loads(data)  

   zone = u['Orientation']

   baseline_df = pd.read_csv('smallhotel_base_case2/eplusout.csv')

   result = energy_consumption(config['energ_consumption'],baseline_df,u['Blended_Electricity_Rate'],u['Blended_NaturalGas_Rate'])

   u['AnnualElectricityCost_Baseline'] = result[zone]['ele']

   u['AnnualNaturalGasCost_Baseline'] = result[zone]['gas']

   upgrade_df = pd.read_csv('smallhotel_upgrade_case2/eplusout.csv')

   result = energy_consumption(config['energ_consumption'],baseline_df,u['Blended_Electricity_Rate'],u['Blended_NaturalGas_Rate'])

   u['AnnualElectricityCost_Upgrade'] = result[zone]['ele']

   u['AnnualNaturalGasCost_Upgrade'] = result[zone]['gas']

   tab = 'smallhotel_base_case2/eplustbl.csv'

   result = size(config['size'], tab)

   u['EPlusCoolingSize'] = result[zone]['size']

#   print cal_payout(u)