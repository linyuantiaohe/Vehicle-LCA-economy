import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import matplotlib.font_manager as fm
import sys
sys.path.append('./header')
import vehiclelcamodel as vlm

collected_vehicle_type = vlm.get_vehicle_type_data()

fpath = Path("./font/simhei.ttf")
ffp = fm.FontProperties(fname="./font/simhei.ttf")

#plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
#plt.rcParams["font.family"] = 'Times New Roman' #for mac os
#plt.rcParams['axes.unicode_minus']=False

st.title('燃料电池汽车-参数敏感性分析')
st.text('@Copyright Email: wangge@ncepu.edu.cn')
st.text('More data and functions are under construction…')

ef_fuels,cost_fuels,charge_speeds=vlm.select_fuels()

st.sidebar.markdown('# 选择敏感性分析基准值')

st.sidebar.markdown('## 1.车型和工作量')

selected_vehicle_type = st.sidebar.selectbox(
    '请选择要分析的车型',
    collected_vehicle_type)

df_ini_vehicle=pd.read_excel('./data/'+selected_vehicle_type+'.xlsx',sheet_name='运营参数',index_col=0)
full_load_rate = st.sidebar.slider('选择平均负载率(100%为全部满载,0%为全部空载)', 0,100, int(df_ini_vehicle.loc['平均负载率',2021]))/100
full_work_rate = st.sidebar.slider('选择行驶时间占比(扣除装卸货和接不到单时间)', 0,100, int(df_ini_vehicle.loc['行驶时间占比',2021]))/100

st.sidebar.markdown('## 2.燃料电池汽车购置成本')

cost_ini_vehicle=pd.read_excel('./data/'+selected_vehicle_type+'.xlsx',sheet_name='燃料电池汽车',index_col=0).loc['购置成本',range(2021,2031)]/10000

st.sidebar.markdown('购置成本将从2021年的%.2f万元降至2030年的%.2f万元。'%(cost_ini_vehicle.iloc[0],cost_ini_vehicle.iloc[-1]))
fc_subs_perc = st.sidebar.slider('可选择购置成本补贴比例(100%为全额补贴,0%为不补贴)', 0,100, 0)/100

if fc_subs_perc>0:
    st.sidebar.markdown('补贴后，购置成本将从2021年的%.2f万元降至2030年的%.2f万元。'%(cost_ini_vehicle.iloc[0]*(1-fc_subs_perc),cost_ini_vehicle.iloc[-1]*(1-fc_subs_perc)))

st.sidebar.markdown('## 3.氢价格')

hydrogen_price=pd.read_excel('fuel/燃料成本.xlsx',sheet_name='燃料电池汽车',index_col=0).loc['低碳氢',range(2021,2031)].values
st.sidebar.markdown('终端氢价将从2021年的%.2f元/kg降至2030年的%.2f元/kg。'%(hydrogen_price[0],hydrogen_price[-1]))

mod_hp = st.sidebar.checkbox('是否修改氢价?')
if mod_hp:
    hp21=st.sidebar.number_input('设置2021年氢价（元/kg）',0,hydrogen_price[0],hydrogen_price[0],format='%d')
    if hp21>0:
        hp30=st.sidebar.number_input('设置2030年氢价（元/kg）',0,hp21,min(hydrogen_price[-1],hp21),format='%d')
    else:
        hp30=0
    hydrogen_price=np.linspace(hp21,hp30,10)

cost_fuels.loc['燃料电池汽车',range(2021,2031)]=hydrogen_price
cost_fuels.loc['燃料电池汽车',range(2031,2035)]=hydrogen_price[-1]

st.markdown('**燃料价格**')
st.write(cost_fuels)

st.sidebar.markdown('## 4.工资、过路费、碳价格等外生因素')

driver_salary_per_month = st.sidebar.checkbox('是否考虑司机工资?')
if driver_salary_per_month:
    driver_salary_per_month = st.sidebar.number_input('选择司机平均月工资', 2000, 15000, 10000,format='%d')
else:
    driver_salary_per_month=0

toll_parameter=1
if selected_vehicle_type=='4.5吨冷链车':
    cold_truck_toll = st.sidebar.checkbox('是否绿色通道?',value=True)
    st.sidebar.markdown('注:绿色通道车辆免征过路费')
    if cold_truck_toll:
        toll_parameter=0

if toll_parameter:
    hydrogen_toll=st.sidebar.slider('选择燃料电池车的高速通行费:元/km', 0, int(df_ini_vehicle.loc['通行费',2021]), int(df_ini_vehicle.loc['通行费',2021]))

selected_carbon_tax = st.sidebar.number_input('设置碳税（元/吨）',0,10000,50,format='%d')

st.sidebar.markdown('## 5.其它软件功能')

selected_fuel = st.sidebar.multiselect('要对比哪几种类型？',['燃油汽车','电动汽车','燃料电池汽车'],['燃油汽车','电动汽车','燃料电池汽车'])

st.sidebar.markdown('## 6.敏感性分析专用')

selected_year = st.sidebar.slider('选择基准年份', 2021, 2030, 2021)

df_trip_data=pd.read_excel('./data/'+selected_vehicle_type+'.xlsx',sheet_name='线路',index_col=0)
selected_trip = st.sidebar.selectbox('请选一条基准线路',df_trip_data.index)

df_hydrogen=pd.read_excel('./data/'+selected_vehicle_type+'.xlsx',sheet_name='燃料电池汽车',index_col=0)

sa_rates=np.array([0+i*0.05 for i in range(23)])

st.markdown('## 1.针对氢耗水平的敏感性分析')
st.markdown('基准氢耗:百公里%.2fkg'%df_hydrogen.loc['百公里能耗',selected_year])
sa_hydrogen_consum_rates=sa_rates*df_hydrogen.loc['百公里能耗',selected_year]

##函数使用
compare_fuel_economy_result,compare_fuel_cost_mix_result,compare_fuel_emission_result,sa_economy_result,sa_cost_mix_result,sa_emission_result=vlm.hydrogen_consumption_rate_sensetivity_analysis(sa_consumption_rates=sa_hydrogen_consum_rates,lang_ZH_or_not=True,carbon_tax=selected_carbon_tax,vehicle_type=selected_vehicle_type,year=selected_year,trip=selected_trip,toll_parameter=toll_parameter,hydrogen_toll=hydrogen_toll,driver_salary_per_month=driver_salary_per_month,full_load_rate=full_load_rate,full_work_rate=full_work_rate,ef_fuels=ef_fuels,cost_fuels=cost_fuels,charge_speeds=charge_speeds)

fig_sa_hydrogen_consumption_rate,ax_sa_hydrogen_consumption_rate=plt.subplots(figsize=(6,4))
(sa_economy_result.sum(axis=1)/10000).plot(style='-o',ax=ax_sa_hydrogen_consumption_rate,label='燃料电池汽车')

for ft in compare_fuel_economy_result.index:
    ax_sa_hydrogen_consumption_rate.plot([0,10000],[compare_fuel_economy_result.loc[ft].sum()/10000,compare_fuel_economy_result.loc[ft].sum()/10000],'-',label=ft)
ax_sa_hydrogen_consumption_rate.set_xlim(sa_hydrogen_consum_rates.min(),sa_hydrogen_consum_rates.max())
ax_sa_hydrogen_consumption_rate.set_ylim(vlm.axis_lim(compare_fuel_economy_result.sum(axis=1)/10000,sa_economy_result.sum(axis=1)/10000,20))
ax_sa_hydrogen_consumption_rate.plot([df_hydrogen.loc['百公里能耗',selected_year],df_hydrogen.loc['百公里能耗',selected_year]],[-10000,10000],'--',label='当前氢耗水平')
ax_sa_hydrogen_consumption_rate.legend(loc='right',bbox_to_anchor=(1.32,0.5),prop=ffp)
ax_sa_hydrogen_consumption_rate.set_ylabel('净利润:万元',font=fpath)
ax_sa_hydrogen_consumption_rate.set_xlabel('氢耗水平:kg/百公里',font=fpath)
ax_sa_hydrogen_consumption_rate.set_title('%s-%s-碳税%d元-氢耗敏感性'%(selected_vehicle_type,selected_trip,selected_carbon_tax),font=fpath)
ax_sa_hydrogen_consumption_rate.grid()
st.pyplot(fig_sa_hydrogen_consumption_rate)

st.markdown('## 2.针对轻量化的敏感性分析')
st.markdown('随着燃料电池效率的提升,对于配套动力电池容量的需求降低.')
st.markdown('注:轻量化仅针对货运车辆,对客车影响较小.')
st.markdown('基准动力电池容量:%.2fkWh'%(df_hydrogen.loc['动力电池容量',selected_year]))
sa_hydrogen_battery_capacity=sa_rates*(df_hydrogen.loc['动力电池容量',selected_year])

##函数使用
compare_fuel_economy_result,compare_fuel_cost_mix_result,compare_fuel_emission_result,sa_economy_result,sa_cost_mix_result,sa_emission_result=vlm.hydrogen_battery_sensetivity_analysis(sa_batteery_capacity=sa_hydrogen_battery_capacity,lang_ZH_or_not=True,carbon_tax=selected_carbon_tax,vehicle_type=selected_vehicle_type,year=selected_year,trip=selected_trip,toll_parameter=toll_parameter,hydrogen_toll=hydrogen_toll,driver_salary_per_month=driver_salary_per_month,full_load_rate=full_load_rate,full_work_rate=full_work_rate,ef_fuels=ef_fuels,cost_fuels=cost_fuels,charge_speeds=charge_speeds)

fig_sa_hydrogen_battery_capacity,ax_sa_battery_capacity=plt.subplots(figsize=(6,4))
(sa_economy_result.sum(axis=1)/10000).plot(style='-o',ax=ax_sa_battery_capacity,label='燃料电池汽车')

for ft in compare_fuel_economy_result.index:
    ax_sa_battery_capacity.plot([0,10000],[compare_fuel_economy_result.loc[ft].sum()/10000,compare_fuel_economy_result.loc[ft].sum()/10000],'-',label=ft)
ax_sa_battery_capacity.set_xlim(sa_hydrogen_battery_capacity.min(),sa_hydrogen_battery_capacity.max())
ax_sa_battery_capacity.set_ylim(vlm.axis_lim(compare_fuel_economy_result.sum(axis=1)/10000,sa_economy_result.sum(axis=1)/10000,20))
ax_sa_battery_capacity.plot([df_hydrogen.loc['动力电池容量',selected_year],df_hydrogen.loc['动力电池容量',selected_year]],[-10000,10000],'--',label='当前配套容量')
ax_sa_battery_capacity.legend(loc='right',bbox_to_anchor=(1.32,0.5),prop=ffp)
ax_sa_battery_capacity.set_ylabel('净利润:万元',font=fpath)
ax_sa_battery_capacity.set_xlabel('燃料电池汽车配套动力电池容量:kWh',font=fpath)
ax_sa_battery_capacity.set_title('%s-%s-碳税%d元-配套动力电池容量敏感性'%(selected_vehicle_type,selected_trip,selected_carbon_tax),font=fpath)
ax_sa_battery_capacity.grid()
st.pyplot(fig_sa_hydrogen_battery_capacity)

fig_only_hydrogen,ax_only_hydrogen=plt.subplots()
(sa_economy_result.sum(axis=1)/10000).plot(style='-o',ax=ax_only_hydrogen,label='燃料电池汽车')
ax_only_hydrogen.set_ylabel('净利润:万元',font=fpath)
ax_only_hydrogen.set_xlabel('燃料电池汽车配套动力电池容量:kWh',font=fpath)
ax_only_hydrogen.set_title('%s-%s-碳税%d元-配套动力电池容量敏感性(仅燃料电池车)'%(selected_vehicle_type,selected_trip,selected_carbon_tax),font=fpath)
ax_only_hydrogen.grid()
st.pyplot(fig_only_hydrogen)

st.markdown('## 3.针对燃料电池汽车购置成本的敏感性分析')
st.markdown('用于检验燃料电池汽车购置成本补贴的政策效果.')
st.markdown('基准购置成本:%.1f万元'%(df_hydrogen.loc['购置成本',selected_year]/10000))
base_capital_cost=df_hydrogen.loc['购置成本',selected_year]/10000
for step in range(11):
    if 20*step>base_capital_cost:
        break
    else:
        continue
sa_hydrogen_capital_cost=np.array([step*i for i in range(23)])

#print(sa_hydrogen_capital_cost)

##函数使用
cc_compare_fuel_economy_result,cc_compare_fuel_cost_mix_result,cc_compare_fuel_emission_result,cc_sa_economy_result,cc_sa_cost_mix_result,cc_sa_emission_result=vlm.capital_cost_sensetivity_analysis(sa_capital_cost=sa_hydrogen_capital_cost,lang_ZH_or_not=True,carbon_tax=selected_carbon_tax,vehicle_type=selected_vehicle_type,year=selected_year,trip=selected_trip,toll_parameter=toll_parameter,hydrogen_toll=hydrogen_toll,driver_salary_per_month=driver_salary_per_month,full_load_rate=full_load_rate,full_work_rate=full_work_rate,ef_fuels=ef_fuels,cost_fuels=cost_fuels,charge_speeds=charge_speeds)

fig_sa_hydrogen_capital_cost,ax_sa_hydrogen_capital_cost=plt.subplots(figsize=(6,4))
(cc_sa_economy_result.sum(axis=1)/10000).plot(style='-o',ax=ax_sa_hydrogen_capital_cost,label='燃料电池汽车')

for ft in cc_compare_fuel_economy_result.index:
    ax_sa_hydrogen_capital_cost.plot([0,10000],[cc_compare_fuel_economy_result.loc[ft].sum()/10000,cc_compare_fuel_economy_result.loc[ft].sum()/10000],'-',label=ft)
ax_sa_hydrogen_capital_cost.set_xlim(sa_hydrogen_capital_cost.min(),sa_hydrogen_capital_cost.max())
ax_sa_hydrogen_capital_cost.set_ylim(vlm.axis_lim(cc_compare_fuel_economy_result.sum(axis=1)/10000,cc_sa_economy_result.sum(axis=1)/10000,20))
ax_sa_hydrogen_capital_cost.plot([df_hydrogen.loc['购置成本',selected_year]/10000,df_hydrogen.loc['购置成本',selected_year]/10000],[-10000,10000],'--',label='当前购置成本')
ax_sa_hydrogen_capital_cost.legend(loc='right',bbox_to_anchor=(1.32,0.5),prop=ffp)
ax_sa_hydrogen_capital_cost.set_ylabel('净利润:万元',font=fpath)
ax_sa_hydrogen_capital_cost.set_xlabel('燃料电池汽车购置成本:万元',font=fpath)
ax_sa_hydrogen_capital_cost.set_title('%s-%s-碳税%d元-燃料电池汽车购置成本敏感性'%(selected_vehicle_type,selected_trip,selected_carbon_tax),font=fpath)
ax_sa_hydrogen_capital_cost.grid()
st.pyplot(fig_sa_hydrogen_capital_cost)