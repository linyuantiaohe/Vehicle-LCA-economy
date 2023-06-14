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

st.title('车辆生命周期评价-实际线路分析')
st.text('@Copyright Email: wangge@ncepu.edu.cn')
st.text('More data and functions are under construction…')

ef_fuels,cost_fuels,charge_speeds=vlm.select_fuels()

st.sidebar.markdown('# 可选项')

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

st.markdown('## 1. 不同路线的对比')
#st.sidebar.markdown('## 1. 不同路线的对比')
selected_year = st.slider('请选择要分析的年份', 2021, 2030, 2021)

##函数使用
economy_result,cost_mix_result,emission_result=vlm.compare_vehicle_economy(vehicle_type=selected_vehicle_type,year=selected_year,carbon_tax=selected_carbon_tax,compare_fuel=selected_fuel,lang_ZH_or_not=True,toll_parameter=toll_parameter,hydrogen_toll=hydrogen_toll,driver_salary_per_month=driver_salary_per_month,full_load_rate=full_load_rate,full_work_rate=full_work_rate,ef_fuels=ef_fuels,cost_fuels=cost_fuels,charge_speeds=charge_speeds)

st.markdown('### 1.1 不同路线下的净收益对比')
fig_net_profit,ax_net_profit=plt.subplots(figsize=(8,4))
df_net_profit=vlm.get_economy_sum_dataframe(economy_result)
(df_net_profit/10000).T.plot.bar(ax=ax_net_profit)
ax_net_profit.set_ylabel('净收益: 万元',font=fpath)
ax_net_profit.set_xlabel('',font=fpath)
ax_net_profit.set_title('%s-%d年-碳税%d'%(selected_vehicle_type,selected_year,selected_carbon_tax),font=fpath)
ax_net_profit.legend(title='',loc='lower center',bbox_to_anchor=(0.5,-0.4),ncol=3,prop=ffp,frameon=False)
ax_net_profit.set_xticklabels(df_net_profit.columns,fontproperties = ffp,rotation=45)
ax_net_profit.plot([-1,100],[0,0],c='black')
csv_net_profit = vlm.convert_df((df_net_profit/10000))

st.pyplot(fig_net_profit)

st.download_button(
    label="下载图中数据为CSV格式(GB2312编码)",
    data=csv_net_profit,
    file_name='净利润-%s-%d年-碳税%d元.csv'%(selected_vehicle_type,selected_year,selected_carbon_tax),
    mime='text/csv')

st.markdown('### 1.2 不同路线下的成本结构')
fig_tco,ax_tco=plt.subplots(figsize=(10,4))
for vt in selected_fuel:
    (cost_mix_result/10000).loc[vt].T.sum().plot(style='-o',ax=ax_tco,label=vt)
ax_tco.set_ylabel('总拥有成本:万元',font=fpath)
ax_tco.set_xlabel('',font=fpath)
ax_tco.set_xticks(range(11))
ax_tco.set_xticklabels((cost_mix_result/10000).loc[vt].T.sum().index,fontproperties = ffp,rotation=45)
ax_tco.legend(loc='lower center',bbox_to_anchor=(0.5,-0.4),ncol=3,prop=ffp,frameon=False)
st.pyplot(fig_tco)


fig_cost_mix,ax_cost_mix=plt.subplots(1,len(selected_fuel),figsize=(4*len(selected_fuel),4),sharey=True)
for vt,i in zip(selected_fuel,range(len(selected_fuel))):
    (cost_mix_result/10000).loc[vt].plot.bar(stacked=True,ax=ax_cost_mix[i],legend=False)
    ax_cost_mix[i].set_title(vt,font=fpath)
    ax_cost_mix[i].set_xlabel('',font=fpath)
    #ax_cost_mix[i].set_ylim(0,1)
    #ax_cost_mix[i].set_yticks([0,0.2,0.4,0.6,0.8,1])
    #ax_cost_mix[i].set_yticklabels(['0','20%','40%','60%','80%','100%'])
    ax_cost_mix[i].set_xticklabels(df_net_profit.columns,fontproperties = ffp)
ax_cost_mix[1].legend(loc='lower center',bbox_to_anchor=(0.5,-0.5),ncol=6,prop=ffp,frameon=False)
ax_cost_mix[0].set_ylabel('成本:万元',font=fpath)
fig_cost_mix.subplots_adjust(wspace=0.05)
fig_cost_mix.suptitle('%s-%d年-碳税%d'%(selected_vehicle_type,selected_year,selected_carbon_tax),font=fpath)

st.pyplot(fig_cost_mix)
csv_economy_result = vlm.convert_df(economy_result)

st.download_button(
    label="下载源数据为CSV格式(GB2312编码)",
    data=csv_economy_result,
    file_name='收益利润源数据-%s-%d年-碳税%d元.csv'%(selected_vehicle_type,selected_year,selected_carbon_tax),
    mime='text/csv')

st.markdown('### 1.3 不同路线下的生命周期碳排放总量')
fig_emission,ax_emission=plt.subplots(figsize=(8,4))
emission_result.T.plot.bar(ax=ax_emission)
ax_emission.set_ylabel('碳排放量:吨',font=fpath)
ax_emission.set_xlabel('',font=fpath)
ax_emission.set_title('%s-%d年-碳税%d'%(selected_vehicle_type,selected_year,selected_carbon_tax),font=fpath)
ax_emission.legend(title='',loc='lower center',bbox_to_anchor=(0.5,-0.4),prop=ffp,frameon=False,ncol=3)
ax_emission.plot([-1,100],[0,0],c='black')
ax_emission.set_xticklabels(df_net_profit.columns,fontproperties = ffp,rotation=45)

st.pyplot(fig_emission)

csv_emission = vlm.convert_df(emission_result)
st.download_button(
    label="下载图中数据为CSV格式(GB2312编码)",
    data=csv_emission,
    file_name='生命周期碳排放-%s-%d年-碳税%d元/吨.csv'%(selected_vehicle_type,selected_year,selected_carbon_tax),
    mime='text/csv')

st.markdown('## 2. 选定路线下的趋势对比')

#st.sidebar.markdown('## 2. 选定路线下的趋势对比')

df_trip_data=pd.read_excel('./data/'+selected_vehicle_type+'.xlsx',sheet_name='线路',index_col=0)
selected_trip = st.selectbox('请选择想分析的线路',df_trip_data.index)

##函数使用
year_economy_result,year_cost_mix_result,year_emission_result=vlm.economy_trend(vehicle_type=selected_vehicle_type,carbon_tax=selected_carbon_tax,compare_fuel=selected_fuel,lang_ZH_or_not=True,trip=selected_trip,toll_parameter=toll_parameter,hydrogen_toll=hydrogen_toll,driver_salary_per_month=driver_salary_per_month,full_load_rate=full_load_rate,full_work_rate=full_work_rate,ef_fuels=ef_fuels,cost_fuels=cost_fuels,charge_speeds=charge_speeds)
st.markdown('### 2.1 选定路线下的净收益趋势对比')

fig_net_profit_trend,ax_net_profit_trend=plt.subplots(figsize=(8,4))
df_net_profit_trend=vlm.get_economy_sum_dataframe(year_economy_result)
(df_net_profit_trend/10000).T.plot(style='-o',ax=ax_net_profit_trend)
ax_net_profit_trend.set_ylabel('净收益：万元',font=fpath)
ax_net_profit_trend.set_xlabel('',font=fpath)
ax_net_profit_trend.set_title('净利润趋势-%s-%s-碳税%d元'%(selected_vehicle_type,selected_trip,selected_carbon_tax),font=fpath)
ax_net_profit_trend.legend(title='',loc='lower center',bbox_to_anchor=(0.5,-0.2),prop=ffp,frameon=False,ncol=3)
ax_net_profit_trend.set_xlim(2021,2030)
ax_net_profit_trend.set_ylim(int((df_net_profit_trend/10000).min().min()/50)*50-50,int((df_net_profit_trend/10000).max().max()/50)*50+50)
ax_net_profit_trend.plot([2000,3000],[0,0],c='black')
csv_net_profit_trend = vlm.convert_df((df_net_profit_trend/10000))

st.pyplot(fig_net_profit_trend)

st.download_button(
    label="下载图中数据为CSV格式(GB2312编码)",
    data=csv_net_profit_trend,
    file_name='净利润趋势-%s-%s-碳税%d元.csv'%(selected_vehicle_type,selected_trip,selected_carbon_tax),
    mime='text/csv')

st.markdown('### 2.2 选定路线下的成本结构趋势')
fig_cost_mix_trend,ax_cost_mix_trend=plt.subplots(1,len(selected_fuel),figsize=(4*len(selected_fuel),4),sharey=True)
for vt,i in zip(selected_fuel,range(len(selected_fuel))):
    ax_cost_mix_trend[i].stackplot(np.arange(2021,2031), (year_cost_mix_result/10000).loc[vt].T.values, labels=year_cost_mix_result.loc[vt].T.index)
    #year_cost_mix_result.loc[vt].stackplot(stacked=True,ax=ax_cost_mix_trend[i],legend=False)
    ax_cost_mix_trend[i].set_title(vt,font=fpath)
    ax_cost_mix_trend[i].set_xlabel('',font=fpath)
    #ax_cost_mix_trend[i].set_ylim(0,1)
    ax_cost_mix_trend[i].set_xlim(2021,2030)
    #ax_cost_mix_trend[i].set_yticks([0,0.2,0.4,0.6,0.8,1])
    #ax_cost_mix_trend[i].set_yticklabels(['0','20%','40%','60%','80%','100%'])
    ax_cost_mix_trend[i].set_xticks(range(2021,2031))
    ax_cost_mix_trend[i].set_xticklabels(range(2021,2031),rotation=90)
ax_cost_mix_trend[1].legend(loc='lower center',bbox_to_anchor=(0.5,-0.3),ncol=6,prop=ffp,frameon=False)
ax_cost_mix_trend[0].set_ylabel('成本:万元',font=fpath)
fig_cost_mix_trend.subplots_adjust(wspace=0.05)
fig_cost_mix_trend.suptitle('%s-%s-碳税%d元'%(selected_vehicle_type,selected_trip,selected_carbon_tax),font=fpath)

st.pyplot(fig_cost_mix_trend)
csv_economy_result_trend = vlm.convert_df(year_economy_result)

st.download_button(
    label="下载源数据为CSV格式(GB2312编码)",
    data=csv_economy_result_trend,
    file_name='收益利润趋势源数据-%s-%s-碳税%d元.csv'%(selected_vehicle_type,selected_trip,selected_carbon_tax),
    mime='text/csv')

st.markdown('### 2.3 选定路线下的生命周期碳排放总量')

selected_electricity = st.multiselect('可选电源？',['电网电','绿电'],['电网电','绿电'])
selected_hydrogen = st.multiselect('可选电源？',['低碳氢','电网电制氢','绿氢','煤制氢','天然气SMR','煤制氢+ccus'],['低碳氢','电网电制氢','绿氢'])

energy=year_emission_result/(ef_fuels.loc[:,range(2021,2031)])

ev_ef=pd.read_excel('fuel\燃料碳排放强度.xlsx',sheet_name='电动汽车',index_col=0).loc[selected_electricity,range(2021,2031)]
hv_ef=pd.read_excel('fuel\燃料碳排放强度.xlsx',sheet_name='燃料电池汽车',index_col=0).loc[selected_hydrogen,range(2021,2031)]

emissions=pd.DataFrame(0,index=['燃油汽车'],columns=range(2021,2031))
emissions.loc['燃油汽车']=year_emission_result.loc['燃油汽车',range(2021,2031)]

for i in selected_electricity:
    emissions.loc['电动汽车-%s'%i]=energy.loc['电动汽车'].T*ev_ef.loc[i]

for i in selected_hydrogen:
    emissions.loc['燃料电池汽车-%s'%i]=energy.loc['燃料电池汽车'].T*hv_ef.loc[i]

fig_emission_trend,ax_emission_trend=plt.subplots(figsize=(8,4))
emissions.T.plot(style='-o',ax=ax_emission_trend)
ax_emission_trend.set_ylabel('碳排放量:吨',font=fpath)
ax_emission_trend.set_xlabel('',font=fpath)
ax_emission_trend.set_title('%s-%s-碳税%d元'%(selected_vehicle_type,selected_trip,selected_carbon_tax),font=fpath)
ax_emission_trend.legend(title='',loc='lower center',bbox_to_anchor=(0.5,-0.35),prop=ffp,ncol=3,frameon=False)
ax_emission_trend.set_xlim(2021,2030)
ax_emission_trend.set_ylim(0,int(year_emission_result.max().max()/100)*100+100)
csv_emission_trend = vlm.convert_df(emissions)

st.pyplot(fig_emission_trend)

st.download_button(
    label="下载图中数据为CSV格式(GB2312编码)",
    data=csv_emission_trend,
    file_name='生命周期碳排放趋势-%s-%s-碳税%d元.csv'%(selected_vehicle_type,selected_trip,selected_carbon_tax),
    mime='text/csv')