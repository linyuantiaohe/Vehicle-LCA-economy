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

st.sidebar.markdown('# 选择敏感性分析基准值')

selected_vehicle_type = st.sidebar.selectbox(
    '请选择要分析的车型',
    collected_vehicle_type)

toll_parameter=1
if selected_vehicle_type=='4.5吨冷链车':
    cold_truck_toll = st.sidebar.checkbox('是否绿色通道?')
    st.sidebar.markdown('注:绿色通道车辆免征过路费')
    if cold_truck_toll:
        toll_parameter=0

selected_year = st.sidebar.slider('选择基准年份', 2021, 2030, 2021)

df_trip_data=pd.read_excel('./data/'+selected_vehicle_type+'.xlsx',sheet_name='线路',index_col=0)
selected_trip = st.sidebar.selectbox('请选一条基准线路',df_trip_data.index)

selected_carbon_tax = st.sidebar.number_input('设置碳税（元/吨）,默认为50',0,10000,50,format='%d')

df_hydrogen=pd.read_excel('./data/'+selected_vehicle_type+'.xlsx',sheet_name='燃料电池汽车',index_col=0)

sa_rates=np.array([0+i*0.05 for i in range(23)])

st.markdown('## 1.针对氢耗水平的敏感性分析')
st.markdown('基准氢耗:百公里%.2fkg'%df_hydrogen.loc['百公里能耗',selected_year])
sa_hydrogen_consum_rates=sa_rates*df_hydrogen.loc['百公里能耗',selected_year]

compare_fuel_economy_result,compare_fuel_cost_mix_result,compare_fuel_emission_result,sa_economy_result,sa_cost_mix_result,sa_emission_result=vlm.hydrogen_consumption_rate_sensetivity_analysis(sa_consumption_rates=sa_hydrogen_consum_rates,lang_ZH_or_not=True,carbon_tax=selected_carbon_tax,vehicle_type=selected_vehicle_type,year=selected_year,trip=selected_trip)

fig_sa_hydrogen_consumption_rate,ax_sa_hydrogen_consumption_rate=plt.subplots(figsize=(6,4))
(sa_economy_result.sum(axis=1)/10000).plot(style='-o',ax=ax_sa_hydrogen_consumption_rate,label='燃料电池汽车')

for ft in compare_fuel_economy_result.index:
    ax_sa_hydrogen_consumption_rate.plot([0,10000],[compare_fuel_economy_result.loc[ft].sum()/10000,compare_fuel_economy_result.loc[ft].sum()/10000],'-',label=ft)
ax_sa_hydrogen_consumption_rate.set_xlim(sa_hydrogen_consum_rates.min(),sa_hydrogen_consum_rates.max())
ax_sa_hydrogen_consumption_rate.set_ylim(vlm.axis_lim(compare_fuel_economy_result.sum(axis=1)/10000,sa_economy_result.sum(axis=1)/10000,100))
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
print(sa_hydrogen_battery_capacity)

compare_fuel_economy_result,compare_fuel_cost_mix_result,compare_fuel_emission_result,sa_economy_result,sa_cost_mix_result,sa_emission_result=vlm.hydrogen_battery_sensetivity_analysis(sa_batteery_capacity=sa_hydrogen_battery_capacity,lang_ZH_or_not=True,carbon_tax=selected_carbon_tax,vehicle_type=selected_vehicle_type,year=selected_year,trip=selected_trip)

fig_sa_hydrogen_battery_capacity,ax_sa_battery_capacity=plt.subplots(figsize=(6,4))
(sa_economy_result.sum(axis=1)/10000).plot(style='-o',ax=ax_sa_battery_capacity,label='燃料电池汽车')

for ft in compare_fuel_economy_result.index:
    ax_sa_battery_capacity.plot([0,10000],[compare_fuel_economy_result.loc[ft].sum()/10000,compare_fuel_economy_result.loc[ft].sum()/10000],'-',label=ft)
ax_sa_battery_capacity.set_xlim(sa_hydrogen_battery_capacity.min(),sa_hydrogen_battery_capacity.max())
ax_sa_battery_capacity.set_ylim(vlm.axis_lim(compare_fuel_economy_result.sum(axis=1)/10000,sa_economy_result.sum(axis=1)/10000,100))
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