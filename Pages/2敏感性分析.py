import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import matplotlib.font_manager as fm

fpath = Path("./simhei.ttf")
ffp = fm.FontProperties(fname="./simhei.ttf")

#plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
#plt.rcParams["font.family"] = 'Times New Roman' #for mac os
#plt.rcParams['axes.unicode_minus']=False

collected_vehicle_type=('25吨牵引车','18吨货车')

@st.cache_data
def cal_vehicle_life_economy(nev_or_not=False,fuel_capacity=2000.0,body_weight=9000.0,battery_weight=0,capital_cost=397097.1676709765,fuel_consumption_rate=35,life_fuel_price=pd.Series(8.145,index=range(5)),cold_fuel_rate=1,charge_speed=6000,lca_ef=pd.Series(2.63,index=range(5)),insurance_per_year=5000,maintainance_per_km=0.2,maintainance_per_year=2000,discount_rate=0.06,vehicle_life=5,workday_ratio=0.8,workhour_per_driver=8,number_of_driver=1,driver_salary_per_month=10000,average_speed=60,toll_per_km=2,tier_per_km=0.12,allowed_weight=49,cold_month=2,trip_length=4164.711,freight_or_not=True,average_weight_price=0.202615099,average_income_per_trip=25315,carbon_tax=50,lang_ZH_or_not=True):
    day_type=['常温','低温']
    life_cycle_dr=[]
    for i in range(vehicle_life):
        life_cycle_dr.append(1/((discount_rate+1)**i))
    life_cycle_dr=np.array(life_cycle_dr)
    if nev_or_not:
        carbon_tax=0
    hour_per_charge = fuel_capacity/charge_speed
    differnt_day_fuel_rate=pd.Series([fuel_consumption_rate,fuel_consumption_rate*cold_fuel_rate],index=day_type)
    length_per_charge = fuel_capacity/differnt_day_fuel_rate*100
    freight_load = allowed_weight-battery_weight/1000-body_weight/1000
    if freight_or_not:
        income_per_trip=trip_length*average_weight_price*freight_load
    else:
        income_per_trip=average_income_per_trip
    charge_times_per_trip = (trip_length/length_per_charge).astype('int')
    hour_charge_per_trip = charge_times_per_trip*hour_per_charge
    hour_per_trip = trip_length/average_speed+hour_charge_per_trip
    day_work_hour=workhour_per_driver*number_of_driver
    days_per_trip = hour_per_trip/day_work_hour
    annual_days = pd.Series([12-cold_month, cold_month],index=day_type)/12*365*workday_ratio
    annual_trips = annual_days/days_per_trip
    annual_trip_length = annual_trips*trip_length
    annual_energy_consumption = annual_trip_length/100*differnt_day_fuel_rate
    annual_emissions=annual_energy_consumption.sum()*lca_ef/1000

    annual_income = annual_trips*income_per_trip
    annual_carbon_tax=annual_emissions*carbon_tax
    annual_driver_cost=number_of_driver*driver_salary_per_month*12
    annual_maintaince_insurance=maintainance_per_year+(maintainance_per_km+tier_per_km)*annual_trip_length.sum()+insurance_per_year
    annual_toll=toll_per_km*annual_trip_length.sum()
    annual_fuel_cost=annual_energy_consumption.sum()*life_fuel_price

    lca_emissions=annual_emissions.sum()

    lca_income = annual_income.sum()*life_cycle_dr.sum()
    lca_fuel_cost=(annual_fuel_cost*life_cycle_dr).sum()
    lca_toll=annual_toll*life_cycle_dr.sum()
    lca_maintaince_insurance=annual_maintaince_insurance*life_cycle_dr.sum()
    lca_carbon_tax = (annual_carbon_tax*life_cycle_dr).sum()
    lca_driver_cost=annual_driver_cost*life_cycle_dr.sum()

    if lang_ZH_or_not:
        economy_index=['收入','购置成本','补能成本','过路费','维修保险费','司机工资','碳税']
    else:
        economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Driver salary','Carbon tax']

    lca_economy_mix=pd.Series([lca_income,-capital_cost,-lca_fuel_cost,-lca_toll,-lca_maintaince_insurance,-lca_driver_cost,-lca_carbon_tax],index=economy_index)

    return lca_economy_mix,lca_emissions

@st.cache_data
def cal_cost_percent(lca_economy_mix):
    lca_cost_percentage=-lca_economy_mix.iloc[1:]
    lca_cost_percentage=lca_cost_percentage/lca_cost_percentage.sum()
    return lca_cost_percentage

@st.cache_data
def compare_vehicle_economy(vehicle_type='25吨牵引车',year=2021,carbon_tax=50,compare_fuel=['燃油汽车','电动汽车','燃料电池汽车'],lang_ZH_or_not=True):
    if year not in np.arange(2021,2031):
        print("Only support calculate year from 2021 to 2030.")
    df_vehicle_om=pd.read_excel(vehicle_type+'.xlsx',sheet_name='运营参数',index_col=0)
    df_trip_data=pd.read_excel(vehicle_type+'.xlsx',sheet_name='线路',index_col=0)
    vehicle_and_trip=pd.MultiIndex.from_product([compare_fuel,df_trip_data.index],names=['Vehicles','Trips'])
    if lang_ZH_or_not:
        economy_index=['收入','购置成本','补能成本','过路费','维修保险费','司机工资','碳税']
    else:
        economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Driver salary','Carbon tax']
    economy_result=pd.DataFrame(0,index=vehicle_and_trip,columns=economy_index)
    cost_mix_result=pd.DataFrame(0,index=vehicle_and_trip,columns=economy_index[1:])
    emission_result=pd.DataFrame(0,index=compare_fuel,columns=df_trip_data.index)
    for ft in compare_fuel:
        df_vehicle=pd.read_excel(vehicle_type+'.xlsx',sheet_name=ft,index_col=0)
        vehicle_life=int(df_vehicle_om.loc['车辆寿命',year])
        future_fuel_cost=pd.Series(0,index=range(vehicle_life))
        future_fuel_ef=pd.Series(0,index=range(vehicle_life))
        for y in future_fuel_cost.index:
            future_fuel_cost.loc[y]=df_vehicle.loc['燃料价格',year+y]
            future_fuel_ef.loc[y]=df_vehicle.loc['燃料生命周期排放因子',year+y]
        nev=True
        bool_of_zh={'是':True,'否':False}
        if ft == '燃油汽车':
            nev=False
        for trip in df_trip_data.index:
            lca_economy_mix,lca_emissions=cal_vehicle_life_economy(nev_or_not=nev,fuel_capacity=df_vehicle.loc['载能容量',year],body_weight=df_vehicle.loc['车身质量',year],battery_weight=df_vehicle.loc['电池质量',year],capital_cost=df_vehicle.loc['购置成本',year],fuel_consumption_rate=df_vehicle.loc['百公里能耗',year],life_fuel_price=future_fuel_cost,cold_fuel_rate=df_vehicle.loc['低温能耗率',year],charge_speed=df_vehicle.loc['充能速度',year],lca_ef=future_fuel_ef,insurance_per_year=df_vehicle.loc['单年保险费',year],maintainance_per_km=df_vehicle.loc['保养费用',year],maintainance_per_year=df_vehicle.loc['单年维修费',year],discount_rate=df_vehicle_om.loc['折现率',year],vehicle_life=vehicle_life,workday_ratio=df_vehicle_om.loc['工作日占比',year],workhour_per_driver=df_vehicle_om.loc['单人工作时间',year],number_of_driver=df_vehicle_om.loc['司机人数',year],driver_salary_per_month=df_vehicle_om.loc['司机工资',year],average_speed=df_vehicle_om.loc['平均行驶速度',year],toll_per_km=df_vehicle_om.loc['通行费',year],tier_per_km=df_vehicle_om.loc['轮胎损耗',year],allowed_weight=df_vehicle_om.loc['额定总重',year],cold_month=df_trip_data.loc[trip,'寒冷月'],trip_length=df_trip_data.loc[trip,'距离'],freight_or_not=bool_of_zh[df_trip_data.loc[trip,'是否货运']],average_weight_price=df_trip_data.loc[trip,'单位运价'],average_income_per_trip=df_trip_data.loc[trip,'整车运价'],carbon_tax=carbon_tax,lang_ZH_or_not=lang_ZH_or_not)
            economy_result.loc[ft,trip]=lca_economy_mix
            cost_mix_result.loc[ft,trip]=cal_cost_percent(lca_economy_mix)
            emission_result.loc[ft,trip]=lca_emissions
    return economy_result,cost_mix_result,emission_result

@st.cache_data
def economy_trend(vehicle_type='25吨牵引车',carbon_tax=50,compare_fuel=['燃油汽车','电动汽车','燃料电池汽车'],lang_ZH_or_not=True,trip='上海-北京'):
    df_vehicle_om=pd.read_excel(vehicle_type+'.xlsx',sheet_name='运营参数',index_col=0)
    df_trip_data=pd.read_excel(vehicle_type+'.xlsx',sheet_name='线路',index_col=0)
    all_years=np.arange(2021,2031)

    vehicle_and_year=pd.MultiIndex.from_product([compare_fuel,all_years],names=['Vehicles','Years'])
    if lang_ZH_or_not:
        economy_index=['收入','购置成本','补能成本','过路费','维修保险费','司机工资','碳税']
    else:
        economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Driver salary','Carbon tax']
    economy_result=pd.DataFrame(0,index=vehicle_and_year,columns=economy_index)
    cost_mix_result=pd.DataFrame(0,index=vehicle_and_year,columns=economy_index[1:])
    emission_result=pd.DataFrame(0,index=compare_fuel,columns=all_years)

    for year in all_years:
        for ft in compare_fuel:
            df_vehicle=pd.read_excel(vehicle_type+'.xlsx',sheet_name=ft,index_col=0)
            vehicle_life=int(df_vehicle_om.loc['车辆寿命',year])
            future_fuel_cost=pd.Series(0,index=range(vehicle_life))
            future_fuel_ef=pd.Series(0,index=range(vehicle_life))
            for y in future_fuel_cost.index:
                future_fuel_cost.loc[y]=df_vehicle.loc['燃料价格',year+y]
                future_fuel_ef.loc[y]=df_vehicle.loc['燃料生命周期排放因子',year+y]
            nev=True
            bool_of_zh={'是':True,'否':False}
            if ft == '燃油汽车':
                nev=False
            lca_economy_mix,lca_emissions=cal_vehicle_life_economy(nev_or_not=nev,fuel_capacity=df_vehicle.loc['载能容量',year],body_weight=df_vehicle.loc['车身质量',year],battery_weight=df_vehicle.loc['电池质量',year],capital_cost=df_vehicle.loc['购置成本',year],fuel_consumption_rate=df_vehicle.loc['百公里能耗',year],life_fuel_price=future_fuel_cost,cold_fuel_rate=df_vehicle.loc['低温能耗率',year],charge_speed=df_vehicle.loc['充能速度',year],lca_ef=future_fuel_ef,insurance_per_year=df_vehicle.loc['单年保险费',year],maintainance_per_km=df_vehicle.loc['保养费用',year],maintainance_per_year=df_vehicle.loc['单年维修费',year],discount_rate=df_vehicle_om.loc['折现率',year],vehicle_life=vehicle_life,workday_ratio=df_vehicle_om.loc['工作日占比',year],workhour_per_driver=df_vehicle_om.loc['单人工作时间',year],number_of_driver=df_vehicle_om.loc['司机人数',year],driver_salary_per_month=df_vehicle_om.loc['司机工资',year],average_speed=df_vehicle_om.loc['平均行驶速度',year],toll_per_km=df_vehicle_om.loc['通行费',year],tier_per_km=df_vehicle_om.loc['轮胎损耗',year],allowed_weight=df_vehicle_om.loc['额定总重',year],cold_month=df_trip_data.loc[trip,'寒冷月'],trip_length=df_trip_data.loc[trip,'距离'],freight_or_not=bool_of_zh[df_trip_data.loc[trip,'是否货运']],average_weight_price=df_trip_data.loc[trip,'单位运价'],average_income_per_trip=df_trip_data.loc[trip,'整车运价'],carbon_tax=carbon_tax,lang_ZH_or_not=lang_ZH_or_not)
            economy_result.loc[ft,year]=lca_economy_mix
            cost_mix_result.loc[ft,year]=cal_cost_percent(lca_economy_mix)
            emission_result.loc[ft,year]=lca_emissions
    return economy_result,cost_mix_result,emission_result

st.title('车辆生命周期评价-敏感性分析')
st.text('@Copyright Email: wangge@ncepu.edu.cn')
st.text('More data and functions are under construction…')

st.sidebar.markdown('# 可选项')

selected_vehicle_type = st.sidebar.selectbox(
    '请选择要分析的车型',
    collected_vehicle_type)

selected_fuel = st.sidebar.multiselect(
    '要对比哪几种类型？',
    ['燃油汽车','电动汽车','燃料电池汽车'],
    ['燃油汽车','电动汽车','燃料电池汽车'])

selected_carbon_tax = st.sidebar.number_input('设置碳税（元/吨）',0,10000,50,format='%d')

st.markdown('# Under construction')
st.sidebar.markdown('## 1. 不同路线的对比')
selected_year = st.sidebar.slider('请选择要分析的年份', 2021, 2030, 2021)

economy_result,cost_mix_result,emission_result=compare_vehicle_economy(vehicle_type=selected_vehicle_type,year=selected_year,carbon_tax=selected_carbon_tax,compare_fuel=selected_fuel,lang_ZH_or_not=True)

@st.cache_data
def get_economy_sum_dataframe(lca_economy_mix):
    vehicle_index=lca_economy_mix.index.get_level_values(0).unique()
    trip_index=lca_economy_mix.index.get_level_values(1).unique()
    df=pd.DataFrame(0,index=vehicle_index,columns=trip_index)
    for vt in vehicle_index:
        for trip in trip_index:
            df.loc[vt,trip]=lca_economy_mix.sum(axis=1).loc[vt,trip]
    return df

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('gb2312')

