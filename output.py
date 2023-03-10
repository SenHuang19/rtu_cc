import pandas as pd
import json
import math

def isNaN(num):
    return num!= num

def parse_tab(topic, tab):
    with open(tab) as f:
          lines = f.readlines()
    for line in lines:
        if line.find(topic)!=-1:
           size = float(line.split(',')[4].replace('\n',''))
           break
    return size       

def energy_consumption(config, df,Blended_Electricity_Rate,Blended_NaturalGas_Rate):
    output = {}
    for key in config:
        ele_consumption = 0
        for item in config[key]['ele']:
               if item in df :
                  ele_consumption = ele_consumption + df[item].iloc[0]
               elif item+' ' in df:
                  ele_consumption = ele_consumption + df[item+' '].iloc[0]               
        output[key] = {}                
        output[key]['ele'] = ele_consumption*0.00000027777*Blended_Electricity_Rate
        output[key]['ele_kW'] = ele_consumption*0.00000027777        
        output[key]['tot_kW'] = ele_consumption*0.00000027777
        gas_consumption = 0
        for item in config[key]['gas']:
               if item in df:
                  gas_consumption = gas_consumption + df[item].iloc[0]
               elif item+' ' in df:
                  gas_consumption = gas_consumption + df[item+' '].iloc[0]                              
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
    output['AnnualCosts_Baseline'] = round(AnnualCosts_Baseline,0)
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
    output['LCC_baseline'] = round(LCC_baseline,0)
    LCC_upgrade=CapitalCost_Upgrade+(UPV*AnnualCosts_Upgrade)
    output['LCC_upgrade'] = round(LCC_upgrade,0)
    AC_baseline=LCC_baseline/UPV
    output['AnnualizedCost_Baseline'] = round(AC_baseline,0)
    AC_upgrade=LCC_upgrade/UPV
    output['AnnualizedCost_Upgrade'] = round(AC_upgrade,0)
    NPV=LCC_baseline-LCC_upgrade
    output['NPV'] = round(NPV,0)
    SIR= max((AnnualCosts_Baseline-AnnualCosts_Upgrade)*UPV/(CapitalCost_Upgrade-CapitalCost_Baseline),0.0)
    if math.isinf(SIR):
        output['SIR'] = 'Infinity'
    elif isNaN(SIR):
        output['SIR'] = None
    else:       
        output['SIR'] = round(SIR,2)
    AnnualCostSavings=AnnualCosts_Baseline-AnnualCosts_Upgrade
    CapitalCostSavings=CapitalCost_Baseline-CapitalCost_Upgrade
    if AnnualCostSavings>0:
         SimplePayback=-CapitalCostSavings/AnnualCostSavings
    else:
         SimplePayback=0    
    output['SimplePayback']=round(SimplePayback,1)
    DiscountedCosts_baseline=[0]*(Lifetime+1)*10
    DiscountedCosts_upgrade=[0]*(Lifetime+1)*10
    DiscountedCosts_baseline[0]=CapitalCost_Baseline
    DiscountedCosts_upgrade[0]=CapitalCost_Upgrade
    DiscountedCostsCumulative_baseline=[0]*(Lifetime+1)*10
    DiscountedCostsCumulative_upgrade=[0]*(Lifetime+1)*10
    DiscountedCostsCumulative_baseline[0]=CapitalCost_Baseline
    DiscountedCostsCumulative_upgrade[0]=CapitalCost_Upgrade
    years = [0]
    s=1
    for i in range (1, (Lifetime+1)*10, 1):
          i=i/10.
          years.append(i)
          DiscountedCosts_baseline[s]=AnnualCosts_Baseline*(1/(1+RealDiscountRate)**i)*0.1
          DiscountedCosts_upgrade[s]=AnnualCosts_Upgrade*(1/(1+RealDiscountRate)**i)*0.1
          DiscountedCostsCumulative_baseline[s]=DiscountedCostsCumulative_baseline[s-1]+DiscountedCosts_baseline[s]
          DiscountedCostsCumulative_upgrade[s]=DiscountedCostsCumulative_upgrade[s-1]+DiscountedCosts_upgrade[s]
          s=s+1
    output['DiscountedCostsCumulative_baseline']=DiscountedCostsCumulative_baseline
    output['DiscountedCostsCumulative_upgrade']=DiscountedCostsCumulative_upgrade 
    output['DiscountedCostsCumulative_year']=years
    output['DiscountedCostsCumulative_interval']=0.1
    baseline_check = CapitalCost_Baseline
    upgrade_check = CapitalCost_Upgrade
    diff = 1000000000000000
    abs_diff_min = diff
    abs_diff_max = -10000000000
    for i in range(1, (Lifetime+1)*10,1):
          i = i/10.
          baseline_check= baseline_check+AnnualCosts_Baseline*(1/(1+RealDiscountRate)**i)*0.1
          upgrade_check= upgrade_check+AnnualCosts_Upgrade*(1/(1+RealDiscountRate)**i)*0.1
          abs_diff = baseline_check-upgrade_check
#          print(diff)
          if abs(baseline_check-upgrade_check)<diff:
               diff = abs(baseline_check-upgrade_check)
               index_record = i
          if abs_diff_min>abs_diff:
               abs_diff_min = abs_diff
          if abs_diff_max<abs_diff:
               abs_diff_max = abs_diff 
#    print(abs_diff_min)  
#    print(abs_diff_max)    
    if abs_diff_min>0:
           index_record = 0
    elif abs_diff_max<0:
           index_record = None
    if index_record is not None:           
         output['Payback'] = round(index_record,1)
    else:
         output['Payback'] = 'Infinity'  
    NPV_min=100000000 
    for i in range(1,100):
       x = i/100.
       a = (1+x)**Lifetime
       UPV= (a-1)/(x*a)
       LCC_baseline=CapitalCost_Baseline+(UPV*AnnualCosts_Baseline)
       LCC_upgrade=CapitalCost_Upgrade+(UPV*AnnualCosts_Upgrade)
       NPV=LCC_upgrade-LCC_baseline
       if abs(NPV)<abs(NPV_min):
           NPV_min=NPV
           RateOfReturn=x*100
               
    if output['Payback'] is None:
           RateOfReturn = None
    elif output['Payback']==0:
           RateOfReturn = 'Infinity'  
    elif output['Payback']=='Infinity':
           RateOfReturn = 0.0
         
    if RateOfReturn is not None and RateOfReturn != 'Infinity':           
         output['RateOfReturn'] = round(RateOfReturn,1)
    else:
         output['RateOfReturn'] = None            

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