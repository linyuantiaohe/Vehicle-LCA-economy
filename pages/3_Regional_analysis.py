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

st.title('车辆生命周期评价-区域分析')
st.text('@Copyright Email: wangge@ncepu.edu.cn')
st.text('More data and functions are under construction…')

ef_fuels,cost_fuels,charge_speeds=vlm.select_fuels()

st.sidebar.markdown('# 选择敏感性分析基准值')

selected_vehicle_type = st.sidebar.selectbox(
    '请选择要分析的车型',collected_vehicle_type)

df_ini_vehicle=pd.read_excel('./data/'+selected_vehicle_type+'.xlsx',sheet_name='运营参数',index_col=0)
full_load_rate = st.sidebar.slider('选择平均负载率(100%为全部满载,0%为全部空载)', 0,100, int(df_ini_vehicle.loc['平均负载率',2021]))/100
full_work_rate = st.sidebar.slider('选择行驶时间占比(扣除装卸货和接不到单时间)', 0,100, int(df_ini_vehicle.loc['行驶时间占比',2021]))/100

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

selected_year = st.sidebar.slider('选择基准年份', 2021, 2030, 2021)

df_trip_data=pd.read_excel('./data/'+selected_vehicle_type+'.xlsx',sheet_name='线路',index_col=0)
selected_trip = st.sidebar.selectbox('请选一条基准线路',df_trip_data.index)
st.sidebar.markdown('该路线长度%dkm,整车运价%d元.'%(df_trip_data.loc[selected_trip,'距离'],df_trip_data.loc[selected_trip,'整车运价']))

weather=pd.read_excel('region/各省气温.xlsx',sheet_name='平均气温',index_col=0)
coldmonths=pd.DataFrame(0,index=['0度以下','0-10度'],columns=weather.index)
coldmonths.loc['0度以下']=weather[weather.le(0)].T.describe().loc['count']
coldmonths.loc['0-10度']=weather[weather>0][weather[weather>0]<=10].T.describe().loc['count']
coldmonths=(coldmonths.T*np.array([1,0.5])).sum(axis=1)


st.markdown('注1:低温月份计算方式为,平均气温0度以下记为1个月,平均气温0-10度记为0.5个月.')

st.markdown('## 1.地区对氢-电竞争的影响')
df_nt_h2ev=pd.Series(0,index=coldmonths.index)
df_c_h2ev=pd.Series(0,index=coldmonths.index)
for r in coldmonths.index:
    ##函数使用
    economy_result,cost_mix_result,emission_result=vlm.carbon_tax_sensetivity_analysis(carbon_tax=[0],vehicle_type=selected_vehicle_type,year=selected_year,trip=selected_trip,toll_parameter=toll_parameter,cold_month=coldmonths.loc[r],driver_salary_per_month=driver_salary_per_month,full_load_rate=full_load_rate,full_work_rate=full_work_rate,ef_fuels=ef_fuels,cost_fuels=cost_fuels,charge_speeds=charge_speeds)
    df_nt_h2ev.loc[r]=(economy_result.sum(axis=1)).loc['燃料电池汽车',0]-(economy_result.sum(axis=1)).loc['电动汽车',0]

st.markdown('氢-电生命周期利润差')
st.bar_chart(df_nt_h2ev/10000)


st.markdown('## 2.碳税对氢-油竞争的影响')
sa_carbon_tax=[50*i for i in range(21)]
df_nt_h2oil=pd.DataFrame(0,index=coldmonths.index,columns=sa_carbon_tax)

df_c_h2oil=pd.DataFrame(0,index=coldmonths.index,columns=sa_carbon_tax)

for r in coldmonths.index:
    ##函数使用
    economy_result,cost_mix_result,emission_result=vlm.carbon_tax_sensetivity_analysis(carbon_tax=sa_carbon_tax,vehicle_type=selected_vehicle_type,year=selected_year,trip=selected_trip,toll_parameter=toll_parameter,cold_month=coldmonths.loc[r],driver_salary_per_month=driver_salary_per_month,full_load_rate=full_load_rate,full_work_rate=full_work_rate,ef_fuels=ef_fuels,cost_fuels=cost_fuels,charge_speeds=charge_speeds)
    df_nt_h2ev.loc[r]=(economy_result.sum(axis=1)).loc['燃料电池汽车']-(economy_result.sum(axis=1)).loc['电动汽车']
    df_nt_h2oil.loc[r]=(economy_result.sum(axis=1)).loc['燃料电池汽车']-(economy_result.sum(axis=1)).loc['燃油汽车']

oil_col1, oil_col2 = st.columns(2)

with oil_col1:
    target_carbon_tax = st.selectbox('请选择碳税水平',sa_carbon_tax)
    st.bar_chart(df_nt_h2oil.loc[:,target_carbon_tax]/10000)

with oil_col2:
    target_region = st.selectbox('请选择地区',coldmonths.index)
    st.bar_chart(df_nt_h2oil.loc[target_region]/10000)