import streamlit as st
import pandas as pd
import numpy as np
import os

@st.cache_data
def cal_vehicle_life_economy(nev_or_not=False,fuel_capacity=2000.0,body_weight=9000.0,battery_weight=0,capital_cost=397097.1676709765,fuel_consumption_rate=35,life_fuel_price=pd.Series(8.145,index=range(5)),cold_fuel_rate=1,charge_speed=6000,lca_ef=pd.Series(2.63,index=range(5)),insurance_per_year=5000,maintainance_per_km=0.2,maintainance_per_year=2000,discount_rate=0.06,vehicle_life=5,workday_ratio=0.8,workhour_per_driver=8,number_of_driver=1,driver_salary_per_month=10000,average_speed=60,toll_per_km=2,toll_parameter=1,tier_per_km=0.12,allowed_weight=49,cold_month=2,trip_length=4164.711,freight_or_not=True,average_weight_price=0.202615099,average_income_per_trip=25315,fixed_trips=False,trips_every_day=2,carbon_tax=50,lang_ZH_or_not=True,full_load_rate=1,full_work_rate=1):
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
    if fixed_trips:
        annual_trips = annual_days*trips_every_day
    else:
        annual_trips = annual_days/days_per_trip*full_work_rate
    annual_trip_length = annual_trips*trip_length
    annual_energy_consumption = annual_trip_length/100*differnt_day_fuel_rate
    annual_emissions=annual_energy_consumption.sum()*lca_ef/1000

    annual_income = annual_trips*income_per_trip
    annual_carbon_tax=annual_emissions*carbon_tax
    annual_driver_cost=number_of_driver*driver_salary_per_month*12
    annual_maintaince_insurance=maintainance_per_year+(maintainance_per_km+tier_per_km)*annual_trip_length.sum()+insurance_per_year
    annual_toll=toll_per_km*toll_parameter*annual_trip_length.sum()
    annual_fuel_cost=annual_energy_consumption.sum()*life_fuel_price

    lca_emissions=annual_emissions.sum()

    lca_income = full_load_rate*annual_income.sum()*life_cycle_dr.sum()
    lca_fuel_cost=(annual_fuel_cost*life_cycle_dr).sum()
    lca_toll=annual_toll*life_cycle_dr.sum()
    lca_maintaince_insurance=annual_maintaince_insurance*life_cycle_dr.sum()
    lca_carbon_tax = (annual_carbon_tax*life_cycle_dr).sum()
    lca_driver_cost=annual_driver_cost*life_cycle_dr.sum()

    if driver_salary_per_month>0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','司机工资','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Driver salary','Carbon tax']
        lca_economy_mix=pd.Series([lca_income,-capital_cost,-lca_fuel_cost,-lca_toll,-lca_maintaince_insurance,-lca_driver_cost,-lca_carbon_tax],index=economy_index)
    elif driver_salary_per_month==0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Carbon tax']
        lca_economy_mix=pd.Series([lca_income,-capital_cost,-lca_fuel_cost,-lca_toll,-lca_maintaince_insurance,-lca_carbon_tax],index=economy_index)
    return lca_economy_mix,lca_emissions

@st.cache_data
def cal_cost_percent(lca_economy_mix):
    lca_cost_percentage=-lca_economy_mix.iloc[1:]
    lca_cost_percentage=lca_cost_percentage/lca_cost_percentage.sum()
    return lca_cost_percentage

@st.cache_data
def compare_vehicle_economy(vehicle_type='25吨牵引车',year=2021,carbon_tax=50,compare_fuel=['燃油汽车','电动汽车','燃料电池汽车'],lang_ZH_or_not=True,toll_parameter=1,driver_salary_per_month=0,full_load_rate=1,full_work_rate=1,ef_fuels=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车']),cost_fuels=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车']),charge_speeds=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车'])):
    if year not in np.arange(2021,2031):
        print("Only support calculate year from 2021 to 2030.")
    df_vehicle_om=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name='运营参数',index_col=0)
    df_trip_data=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name='线路',index_col=0)
    vehicle_and_trip=pd.MultiIndex.from_product([compare_fuel,df_trip_data.index],names=['Vehicles','Trips'])
    if driver_salary_per_month>0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','司机工资','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Driver salary','Carbon tax']
    elif driver_salary_per_month==0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Carbon tax']
    economy_result=pd.DataFrame(0,index=vehicle_and_trip,columns=economy_index)
    cost_mix_result=pd.DataFrame(0,index=vehicle_and_trip,columns=economy_index[1:])
    emission_result=pd.DataFrame(0,index=compare_fuel,columns=df_trip_data.index)
    for ft in compare_fuel:
        df_vehicle=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name=ft,index_col=0)
        vehicle_life=int(df_vehicle_om.loc['车辆寿命',year])
        future_fuel_cost=pd.Series(0,index=range(vehicle_life))
        future_fuel_ef=pd.Series(0,index=range(vehicle_life))
        for y in future_fuel_cost.index:
            future_fuel_cost.loc[y]=cost_fuels.loc[ft,year+y]
            future_fuel_ef.loc[y]=ef_fuels.loc[ft,year+y]
        nev=True
        bool_of_zh={'是':True,'否':False}
        if ft == '燃油汽车':
            nev=False
        for trip in df_trip_data.index:
            lca_economy_mix,lca_emissions=cal_vehicle_life_economy(nev_or_not=nev,fuel_capacity=df_vehicle.loc['载能容量',year],body_weight=df_vehicle.loc['车身质量',year],battery_weight=df_vehicle.loc['电池质量',year],capital_cost=df_vehicle.loc['购置成本',year],fuel_consumption_rate=df_vehicle.loc['百公里能耗',year],life_fuel_price=future_fuel_cost,cold_fuel_rate=df_vehicle.loc['低温能耗率',year],charge_speed=charge_speeds.loc[ft,year],lca_ef=future_fuel_ef,insurance_per_year=df_vehicle.loc['单年保险费',year],maintainance_per_km=df_vehicle.loc['保养费用',year],maintainance_per_year=df_vehicle.loc['单年维修费',year],discount_rate=df_vehicle_om.loc['折现率',year],vehicle_life=vehicle_life,workday_ratio=df_vehicle_om.loc['工作日占比',year],workhour_per_driver=df_vehicle_om.loc['单人工作时间',year],number_of_driver=df_vehicle_om.loc['司机人数',year],driver_salary_per_month=driver_salary_per_month,average_speed=df_vehicle_om.loc['平均行驶速度',year],toll_per_km=df_vehicle_om.loc['通行费',year],toll_parameter=toll_parameter,tier_per_km=df_vehicle_om.loc['轮胎损耗',year],allowed_weight=df_vehicle_om.loc['额定总重',year],cold_month=df_trip_data.loc[trip,'寒冷月'],trip_length=df_trip_data.loc[trip,'距离'],freight_or_not=bool_of_zh[df_trip_data.loc[trip,'是否货运']],fixed_trips=bool_of_zh[df_trip_data.loc[trip,'是否固定趟数']],trips_every_day=df_trip_data.loc[trip,'每日固定趟数'],average_weight_price=df_trip_data.loc[trip,'单位运价'],average_income_per_trip=df_trip_data.loc[trip,'整车运价'],carbon_tax=carbon_tax,lang_ZH_or_not=lang_ZH_or_not,full_load_rate=full_load_rate,full_work_rate=full_work_rate)
            economy_result.loc[ft,trip]=lca_economy_mix
            cost_mix_result.loc[ft,trip]=cal_cost_percent(lca_economy_mix)
            emission_result.loc[ft,trip]=lca_emissions
    return economy_result,cost_mix_result,emission_result

@st.cache_data
def economy_trend(vehicle_type='25吨牵引车',carbon_tax=50,compare_fuel=['燃油汽车','电动汽车','燃料电池汽车'],lang_ZH_or_not=True,trip='上海-北京',toll_parameter=1,driver_salary_per_month=0,full_load_rate=1,full_work_rate=1,ef_fuels=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车']),cost_fuels=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车']),charge_speeds=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车'])):
    df_vehicle_om=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name='运营参数',index_col=0)
    df_trip_data=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name='线路',index_col=0)
    all_years=np.arange(2021,2031)

    vehicle_and_year=pd.MultiIndex.from_product([compare_fuel,all_years],names=['Vehicles','Years'])
    if driver_salary_per_month>0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','司机工资','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Driver salary','Carbon tax']
    elif driver_salary_per_month==0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Carbon tax']
    economy_result=pd.DataFrame(0,index=vehicle_and_year,columns=economy_index)
    cost_mix_result=pd.DataFrame(0,index=vehicle_and_year,columns=economy_index[1:])
    emission_result=pd.DataFrame(0,index=compare_fuel,columns=all_years)

    for year in all_years:
        for ft in compare_fuel:
            df_vehicle=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name=ft,index_col=0)
            vehicle_life=int(df_vehicle_om.loc['车辆寿命',year])
            future_fuel_cost=pd.Series(0,index=range(vehicle_life))
            future_fuel_ef=pd.Series(0,index=range(vehicle_life))
            for y in future_fuel_cost.index:
                future_fuel_cost.loc[y]=cost_fuels.loc[ft,year+y]
                future_fuel_ef.loc[y]=ef_fuels.loc[ft,year+y]
            nev=True
            bool_of_zh={'是':True,'否':False}
            if ft == '燃油汽车':
                nev=False
            lca_economy_mix,lca_emissions=cal_vehicle_life_economy(nev_or_not=nev,fuel_capacity=df_vehicle.loc['载能容量',year],body_weight=df_vehicle.loc['车身质量',year],battery_weight=df_vehicle.loc['电池质量',year],capital_cost=df_vehicle.loc['购置成本',year],fuel_consumption_rate=df_vehicle.loc['百公里能耗',year],life_fuel_price=future_fuel_cost,cold_fuel_rate=df_vehicle.loc['低温能耗率',year],charge_speed=charge_speeds.loc[ft,year],lca_ef=future_fuel_ef,insurance_per_year=df_vehicle.loc['单年保险费',year],maintainance_per_km=df_vehicle.loc['保养费用',year],maintainance_per_year=df_vehicle.loc['单年维修费',year],discount_rate=df_vehicle_om.loc['折现率',year],vehicle_life=vehicle_life,workday_ratio=df_vehicle_om.loc['工作日占比',year],workhour_per_driver=df_vehicle_om.loc['单人工作时间',year],number_of_driver=df_vehicle_om.loc['司机人数',year],driver_salary_per_month=driver_salary_per_month,average_speed=df_vehicle_om.loc['平均行驶速度',year],toll_per_km=df_vehicle_om.loc['通行费',year],toll_parameter=toll_parameter,tier_per_km=df_vehicle_om.loc['轮胎损耗',year],allowed_weight=df_vehicle_om.loc['额定总重',year],cold_month=df_trip_data.loc[trip,'寒冷月'],trip_length=df_trip_data.loc[trip,'距离'],freight_or_not=bool_of_zh[df_trip_data.loc[trip,'是否货运']],average_weight_price=df_trip_data.loc[trip,'单位运价'],average_income_per_trip=df_trip_data.loc[trip,'整车运价'],carbon_tax=carbon_tax,lang_ZH_or_not=lang_ZH_or_not,full_load_rate=full_load_rate,full_work_rate=full_work_rate)
            economy_result.loc[ft,year]=lca_economy_mix
            cost_mix_result.loc[ft,year]=cal_cost_percent(lca_economy_mix)
            emission_result.loc[ft,year]=lca_emissions
    return economy_result,cost_mix_result,emission_result

@st.cache_data
def get_economy_sum_dataframe(lca_economy_mix):
    first_index=lca_economy_mix.index.get_level_values(0).unique()
    second_index=lca_economy_mix.index.get_level_values(1).unique()
    df=pd.DataFrame(0,index=first_index,columns=second_index)
    for ft in first_index:
        for st in second_index:
            df.loc[ft,st]=lca_economy_mix.sum(axis=1).loc[ft,st]
    return df

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('gb2312')

@st.cache_data
def hydrogen_consumption_rate_sensetivity_analysis(sa_consumption_rates=[],lang_ZH_or_not=True,vehicle_type='25吨牵引车',carbon_tax=50,year=2021,trip='上海-北京',toll_parameter=1,driver_salary_per_month=0,full_load_rate=1,full_work_rate=1,ef_fuels=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车']),cost_fuels=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车']),charge_speeds=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车'])):
    df_vehicle_om=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name='运营参数',index_col=0)
    df_trip_data=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name='线路',index_col=0)
    bool_of_zh={'是':True,'否':False}
    if driver_salary_per_month>0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','司机工资','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Driver salary','Carbon tax']
    elif driver_salary_per_month==0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Carbon tax']
    compare_fuel=['燃油汽车','电动汽车']
    compare_fuel_economy_result=pd.DataFrame(0,index=compare_fuel,columns=economy_index)
    compare_fuel_cost_mix_result=pd.DataFrame(0,index=compare_fuel,columns=economy_index[1:])
    compare_fuel_emission_result=pd.Series(0,index=compare_fuel)
    for ft in compare_fuel:
        df_vehicle=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name=ft,index_col=0)
        vehicle_life=int(df_vehicle_om.loc['车辆寿命',year])
        future_fuel_cost=pd.Series(0,index=range(vehicle_life))
        future_fuel_ef=pd.Series(0,index=range(vehicle_life))
        for y in future_fuel_cost.index:
            future_fuel_cost.loc[y]=cost_fuels.loc[ft,year+y]
            future_fuel_ef.loc[y]=ef_fuels.loc[ft,year+y]
        nev=True
        if ft == '燃油汽车':
            nev=False
        lca_economy_mix,lca_emissions=cal_vehicle_life_economy(nev_or_not=nev,fuel_capacity=df_vehicle.loc['载能容量',year],body_weight=df_vehicle.loc['车身质量',year],battery_weight=df_vehicle.loc['电池质量',year],capital_cost=df_vehicle.loc['购置成本',year],fuel_consumption_rate=df_vehicle.loc['百公里能耗',year],life_fuel_price=future_fuel_cost,cold_fuel_rate=df_vehicle.loc['低温能耗率',year],charge_speed=charge_speeds.loc[ft,year],lca_ef=future_fuel_ef,insurance_per_year=df_vehicle.loc['单年保险费',year],maintainance_per_km=df_vehicle.loc['保养费用',year],maintainance_per_year=df_vehicle.loc['单年维修费',year],discount_rate=df_vehicle_om.loc['折现率',year],vehicle_life=vehicle_life,workday_ratio=df_vehicle_om.loc['工作日占比',year],workhour_per_driver=df_vehicle_om.loc['单人工作时间',year],number_of_driver=df_vehicle_om.loc['司机人数',year],driver_salary_per_month=driver_salary_per_month,average_speed=df_vehicle_om.loc['平均行驶速度',year],toll_per_km=df_vehicle_om.loc['通行费',year],toll_parameter=toll_parameter,tier_per_km=df_vehicle_om.loc['轮胎损耗',year],allowed_weight=df_vehicle_om.loc['额定总重',year],cold_month=df_trip_data.loc[trip,'寒冷月'],trip_length=df_trip_data.loc[trip,'距离'],freight_or_not=bool_of_zh[df_trip_data.loc[trip,'是否货运']],average_weight_price=df_trip_data.loc[trip,'单位运价'],average_income_per_trip=df_trip_data.loc[trip,'整车运价'],carbon_tax=carbon_tax,lang_ZH_or_not=lang_ZH_or_not,full_load_rate=full_load_rate,full_work_rate=full_work_rate)
        compare_fuel_economy_result.loc[ft]=lca_economy_mix
        compare_fuel_cost_mix_result.loc[ft]=cal_cost_percent(lca_economy_mix)
        compare_fuel_emission_result.loc[ft]=lca_emissions
    if len(sa_consumption_rates)>1:
        ft='燃料电池汽车'
        df_vehicle=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name=ft,index_col=0)
        vehicle_life=int(df_vehicle_om.loc['车辆寿命',year])
        future_fuel_cost=pd.Series(0,index=range(vehicle_life))
        future_fuel_ef=pd.Series(0,index=range(vehicle_life))
        for y in future_fuel_cost.index:
            future_fuel_cost.loc[y]=cost_fuels.loc[ft,year+y]
            future_fuel_ef.loc[y]=ef_fuels.loc[ft,year+y]
        nev=True
        sa_economy_result=pd.DataFrame(0,index=sa_consumption_rates,columns=economy_index)
        sa_cost_mix_result=pd.DataFrame(0,index=sa_consumption_rates,columns=economy_index[1:])
        sa_emission_result=pd.Series(0,index=sa_consumption_rates)
        for scr in sa_consumption_rates:
            lca_economy_mix,lca_emissions=cal_vehicle_life_economy(nev_or_not=nev,fuel_capacity=df_vehicle.loc['载能容量',year],body_weight=df_vehicle.loc['车身质量',year],battery_weight=df_vehicle.loc['电池质量',year],capital_cost=df_vehicle.loc['购置成本',year],fuel_consumption_rate=scr,life_fuel_price=future_fuel_cost,cold_fuel_rate=df_vehicle.loc['低温能耗率',year],charge_speed=charge_speeds.loc[ft,year],lca_ef=future_fuel_ef,insurance_per_year=df_vehicle.loc['单年保险费',year],maintainance_per_km=df_vehicle.loc['保养费用',year],maintainance_per_year=df_vehicle.loc['单年维修费',year],discount_rate=df_vehicle_om.loc['折现率',year],vehicle_life=vehicle_life,workday_ratio=df_vehicle_om.loc['工作日占比',year],workhour_per_driver=df_vehicle_om.loc['单人工作时间',year],number_of_driver=df_vehicle_om.loc['司机人数',year],driver_salary_per_month=driver_salary_per_month,average_speed=df_vehicle_om.loc['平均行驶速度',year],toll_per_km=df_vehicle_om.loc['通行费',year],toll_parameter=toll_parameter,tier_per_km=df_vehicle_om.loc['轮胎损耗',year],allowed_weight=df_vehicle_om.loc['额定总重',year],cold_month=df_trip_data.loc[trip,'寒冷月'],trip_length=df_trip_data.loc[trip,'距离'],freight_or_not=bool_of_zh[df_trip_data.loc[trip,'是否货运']],average_weight_price=df_trip_data.loc[trip,'单位运价'],average_income_per_trip=df_trip_data.loc[trip,'整车运价'],carbon_tax=carbon_tax,lang_ZH_or_not=lang_ZH_or_not,full_load_rate=full_load_rate,full_work_rate=full_work_rate)
            sa_economy_result.loc[scr]=lca_economy_mix
            sa_cost_mix_result.loc[scr]=cal_cost_percent(lca_economy_mix)
            sa_emission_result.loc[scr]=lca_emissions
    return compare_fuel_economy_result,compare_fuel_cost_mix_result,compare_fuel_emission_result,sa_economy_result,sa_cost_mix_result,sa_emission_result

@st.cache_data
def hydrogen_battery_sensetivity_analysis(sa_batteery_capacity=[],lang_ZH_or_not=True,vehicle_type='25吨牵引车',carbon_tax=50,year=2021,trip='上海-北京',toll_parameter=1,driver_salary_per_month=0,full_load_rate=1,full_work_rate=1,ef_fuels=pd.DataFrame(),cost_fuels=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车']),charge_speeds=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车'])):
    df_vehicle_om=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name='运营参数',index_col=0)
    df_trip_data=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name='线路',index_col=0)
    bool_of_zh={'是':True,'否':False}
    if driver_salary_per_month>0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','司机工资','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Driver salary','Carbon tax']
    elif driver_salary_per_month==0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Carbon tax']
    compare_fuel=['燃油汽车','电动汽车']
    compare_fuel_economy_result=pd.DataFrame(0,index=compare_fuel,columns=economy_index)
    compare_fuel_cost_mix_result=pd.DataFrame(0,index=compare_fuel,columns=economy_index[1:])
    compare_fuel_emission_result=pd.Series(0,index=compare_fuel)
    for ft in compare_fuel:
        df_vehicle=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name=ft,index_col=0)
        vehicle_life=int(df_vehicle_om.loc['车辆寿命',year])
        future_fuel_cost=pd.Series(0,index=range(vehicle_life))
        future_fuel_ef=pd.Series(0,index=range(vehicle_life))
        for y in future_fuel_cost.index:
            future_fuel_cost.loc[y]=cost_fuels.loc[ft,year+y]
            future_fuel_ef.loc[y]=ef_fuels.loc[ft,year+y]
        nev=True
        if ft == '燃油汽车':
            nev=False
        lca_economy_mix,lca_emissions=cal_vehicle_life_economy(nev_or_not=nev,fuel_capacity=df_vehicle.loc['载能容量',year],body_weight=df_vehicle.loc['车身质量',year],battery_weight=df_vehicle.loc['电池质量',year],capital_cost=df_vehicle.loc['购置成本',year],fuel_consumption_rate=df_vehicle.loc['百公里能耗',year],life_fuel_price=future_fuel_cost,cold_fuel_rate=df_vehicle.loc['低温能耗率',year],charge_speed=charge_speeds.loc[ft,year],lca_ef=future_fuel_ef,insurance_per_year=df_vehicle.loc['单年保险费',year],maintainance_per_km=df_vehicle.loc['保养费用',year],maintainance_per_year=df_vehicle.loc['单年维修费',year],discount_rate=df_vehicle_om.loc['折现率',year],vehicle_life=vehicle_life,workday_ratio=df_vehicle_om.loc['工作日占比',year],workhour_per_driver=df_vehicle_om.loc['单人工作时间',year],number_of_driver=df_vehicle_om.loc['司机人数',year],driver_salary_per_month=driver_salary_per_month,average_speed=df_vehicle_om.loc['平均行驶速度',year],toll_per_km=df_vehicle_om.loc['通行费',year],toll_parameter=toll_parameter,tier_per_km=df_vehicle_om.loc['轮胎损耗',year],allowed_weight=df_vehicle_om.loc['额定总重',year],cold_month=df_trip_data.loc[trip,'寒冷月'],trip_length=df_trip_data.loc[trip,'距离'],freight_or_not=bool_of_zh[df_trip_data.loc[trip,'是否货运']],average_weight_price=df_trip_data.loc[trip,'单位运价'],average_income_per_trip=df_trip_data.loc[trip,'整车运价'],carbon_tax=carbon_tax,lang_ZH_or_not=lang_ZH_or_not,full_load_rate=full_load_rate,full_work_rate=full_work_rate)
        compare_fuel_economy_result.loc[ft]=lca_economy_mix
        compare_fuel_cost_mix_result.loc[ft]=cal_cost_percent(lca_economy_mix)
        compare_fuel_emission_result.loc[ft]=lca_emissions
    if len(sa_batteery_capacity)>1:
        ft='燃料电池汽车'
        df_vehicle=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name=ft,index_col=0)
        vehicle_life=int(df_vehicle_om.loc['车辆寿命',year])
        future_fuel_cost=pd.Series(0,index=range(vehicle_life))
        future_fuel_ef=pd.Series(0,index=range(vehicle_life))
        for y in future_fuel_cost.index:
            future_fuel_cost.loc[y]=cost_fuels.loc[ft,year+y]
            future_fuel_ef.loc[y]=ef_fuels.loc[ft,year+y]
        nev=True
        sa_economy_result=pd.DataFrame(0,index=sa_batteery_capacity,columns=economy_index)
        sa_cost_mix_result=pd.DataFrame(0,index=sa_batteery_capacity,columns=economy_index[1:])
        sa_emission_result=pd.Series(0,index=sa_batteery_capacity)
        for bat in sa_batteery_capacity:
            lca_economy_mix,lca_emissions=cal_vehicle_life_economy(nev_or_not=nev,fuel_capacity=df_vehicle.loc['载能容量',year],body_weight=df_vehicle.loc['车身质量',year],battery_weight=bat*df_vehicle.loc['动力电池能量密度',year],capital_cost=df_vehicle.loc['购置成本',year],fuel_consumption_rate=df_vehicle.loc['百公里能耗',year],life_fuel_price=future_fuel_cost,cold_fuel_rate=df_vehicle.loc['低温能耗率',year],charge_speed=charge_speeds.loc[ft,year],lca_ef=future_fuel_ef,insurance_per_year=df_vehicle.loc['单年保险费',year],maintainance_per_km=df_vehicle.loc['保养费用',year],maintainance_per_year=df_vehicle.loc['单年维修费',year],discount_rate=df_vehicle_om.loc['折现率',year],vehicle_life=vehicle_life,workday_ratio=df_vehicle_om.loc['工作日占比',year],workhour_per_driver=df_vehicle_om.loc['单人工作时间',year],number_of_driver=df_vehicle_om.loc['司机人数',year],driver_salary_per_month=driver_salary_per_month,average_speed=df_vehicle_om.loc['平均行驶速度',year],toll_per_km=df_vehicle_om.loc['通行费',year],toll_parameter=toll_parameter,tier_per_km=df_vehicle_om.loc['轮胎损耗',year],allowed_weight=df_vehicle_om.loc['额定总重',year],cold_month=df_trip_data.loc[trip,'寒冷月'],trip_length=df_trip_data.loc[trip,'距离'],freight_or_not=bool_of_zh[df_trip_data.loc[trip,'是否货运']],average_weight_price=df_trip_data.loc[trip,'单位运价'],average_income_per_trip=df_trip_data.loc[trip,'整车运价'],carbon_tax=carbon_tax,lang_ZH_or_not=lang_ZH_or_not,full_load_rate=full_load_rate,full_work_rate=full_work_rate)
            sa_economy_result.loc[bat]=lca_economy_mix
            sa_cost_mix_result.loc[bat]=cal_cost_percent(lca_economy_mix)
            sa_emission_result.loc[bat]=lca_emissions
    return compare_fuel_economy_result,compare_fuel_cost_mix_result,compare_fuel_emission_result,sa_economy_result,sa_cost_mix_result,sa_emission_result

def axis_lim(list1,list2,rounds):
    vmin=min(min(list1),min(list2))
    if vmin<0:
        vmin=(int(vmin/rounds)-2)*rounds
    else:
        vmin=(int(vmin/rounds)-1)*rounds
    vmax=max(max(list1),max(list2))
    if vmax<0:
        vmax=(int(vmax/rounds)+1)*rounds
    else:
        vmax=(int(vmax/rounds)+2)*rounds
    return vmin,vmax

@st.cache_data
def get_vehicle_type_data():
    files= os.listdir('./data')
    collected_vehicle_type = []
    for file in files: #遍历文件夹
        if not os.path.isdir(file): #判断是否是文件夹，不是文件夹才打开
            if file[0] not in ['.','~']:
                collected_vehicle_type.append(file[:-5])
    return tuple(collected_vehicle_type)

@st.cache_data
def carbon_tax_sensetivity_analysis(carbon_tax=[],lang_ZH_or_not=True,vehicle_type='25吨牵引车',year=2021,trip='上海-北京',toll_parameter=1,cold_month=0,compare_fuel=['燃油汽车','电动汽车','燃料电池汽车'],driver_salary_per_month=0,full_load_rate=1,full_work_rate=1,ef_fuels=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车']),cost_fuels=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车']),charge_speeds=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车'])):
    if year not in np.arange(2021,2031):
        print("Only support calculate year from 2021 to 2030.")
    df_vehicle_om=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name='运营参数',index_col=0)
    df_trip_data=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name='线路',index_col=0)
    vehicle_and_carbontax=pd.MultiIndex.from_product([compare_fuel,carbon_tax],names=['Vehicles','CarbonTax'])
    if driver_salary_per_month>0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','司机工资','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Driver salary','Carbon tax']
    elif driver_salary_per_month==0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Carbon tax']
    economy_result=pd.DataFrame(0,index=vehicle_and_carbontax,columns=economy_index)
    cost_mix_result=pd.DataFrame(0,index=vehicle_and_carbontax,columns=economy_index[1:])
    emission_result=pd.DataFrame(0,index=compare_fuel,columns=carbon_tax)
    for ft in compare_fuel:
        df_vehicle=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name=ft,index_col=0)
        vehicle_life=int(df_vehicle_om.loc['车辆寿命',year])
        future_fuel_cost=pd.Series(0,index=range(vehicle_life))
        future_fuel_ef=pd.Series(0,index=range(vehicle_life))
        for y in future_fuel_cost.index:
            future_fuel_cost.loc[y]=cost_fuels.loc[ft,year+y]
            future_fuel_ef.loc[y]=ef_fuels.loc[ft,year+y]
        nev=True
        bool_of_zh={'是':True,'否':False}
        if ft == '燃油汽车':
            nev=False
        if len(carbon_tax)>0:
            for ct in carbon_tax:
                lca_economy_mix,lca_emissions=cal_vehicle_life_economy(nev_or_not=nev,fuel_capacity=df_vehicle.loc['载能容量',year],body_weight=df_vehicle.loc['车身质量',year],battery_weight=df_vehicle.loc['电池质量',year],capital_cost=df_vehicle.loc['购置成本',year],fuel_consumption_rate=df_vehicle.loc['百公里能耗',year],life_fuel_price=future_fuel_cost,cold_fuel_rate=df_vehicle.loc['低温能耗率',year],charge_speed=charge_speeds.loc[ft,year],lca_ef=future_fuel_ef,insurance_per_year=df_vehicle.loc['单年保险费',year],maintainance_per_km=df_vehicle.loc['保养费用',year],maintainance_per_year=df_vehicle.loc['单年维修费',year],discount_rate=df_vehicle_om.loc['折现率',year],vehicle_life=vehicle_life,workday_ratio=df_vehicle_om.loc['工作日占比',year],workhour_per_driver=df_vehicle_om.loc['单人工作时间',year],number_of_driver=df_vehicle_om.loc['司机人数',year],driver_salary_per_month=driver_salary_per_month,average_speed=df_vehicle_om.loc['平均行驶速度',year],toll_per_km=df_vehicle_om.loc['通行费',year],toll_parameter=toll_parameter,tier_per_km=df_vehicle_om.loc['轮胎损耗',year],allowed_weight=df_vehicle_om.loc['额定总重',year],cold_month=cold_month,trip_length=df_trip_data.loc[trip,'距离'],freight_or_not=bool_of_zh[df_trip_data.loc[trip,'是否货运']],average_weight_price=df_trip_data.loc[trip,'单位运价'],average_income_per_trip=df_trip_data.loc[trip,'整车运价'],carbon_tax=ct,lang_ZH_or_not=lang_ZH_or_not,full_load_rate=full_load_rate,full_work_rate=full_work_rate)
                economy_result.loc[ft,ct]=lca_economy_mix
                cost_mix_result.loc[ft,ct]=cal_cost_percent(lca_economy_mix)
                emission_result.loc[ft,ct]=lca_emissions
    return economy_result,cost_mix_result,emission_result

def select_fuels():
    with st.expander('选择燃料种类和补能方式', expanded=True):
        ef_oil_fuel=pd.read_excel('./fuel/燃料碳排放强度.xlsx',sheet_name='燃油汽车',index_col=0)
        ef_ev_fuel=pd.read_excel('./fuel/燃料碳排放强度.xlsx',sheet_name='电动汽车',index_col=0)
        ef_fcv_fuel=pd.read_excel('./fuel/燃料碳排放强度.xlsx',sheet_name='燃料电池汽车',index_col=0)

        cost_oil_fuel=pd.read_excel('./fuel/燃料成本.xlsx',sheet_name='燃油汽车',index_col=0)
        cost_ev_fuel=pd.read_excel('./fuel/燃料成本.xlsx',sheet_name='电动汽车',index_col=0)
        cost_fcv_fuel=pd.read_excel('./fuel/燃料成本.xlsx',sheet_name='燃料电池汽车',index_col=0)

        charge_oil_fuel=pd.read_excel('./fuel/补能速度.xlsx',sheet_name='燃油汽车',index_col=0)
        charge_ev_fuel=pd.read_excel('./fuel/补能速度.xlsx',sheet_name='电动汽车',index_col=0)
        charge_fcv_fuel=pd.read_excel('./fuel/补能速度.xlsx',sheet_name='燃料电池汽车',index_col=0)
        oil_col, ev_col, fcf_col = st.columns(3)
        with oil_col:
            oils = st.selectbox('请选择燃油汽车燃料:',ef_oil_fuel.index)
            st.markdown('%s当前碳排放强度为%.2f %s'%(oils,ef_oil_fuel.loc[oils,2021],ef_oil_fuel.loc[oils,'单位']))
            oil_charge=st.selectbox('请选择加油方式:',charge_oil_fuel.index)
        with ev_col:
            powers = st.selectbox('请选择电动汽车燃料',ef_ev_fuel.index)
            st.markdown('%s当前碳排放强度为%.2f %s'%(powers,ef_ev_fuel.loc[powers,2021],ef_ev_fuel.loc[powers,'单位']))
            ev_charge=st.selectbox('请选择充电方式:',charge_ev_fuel.index)
        with fcf_col:
            hydrogens = st.selectbox('请选择燃料电池汽车燃料',ef_fcv_fuel.index)
            st.markdown('%s当前碳排放强度为%.2f %s'%(hydrogens,ef_fcv_fuel.loc[hydrogens,2021],ef_fcv_fuel.loc[hydrogens,'单位']))
            fcv_charge=st.selectbox('请选择加氢方式:',charge_fcv_fuel.index)
        efs=pd.DataFrame([ef_oil_fuel.loc[oils],ef_ev_fuel.loc[powers],ef_fcv_fuel.loc[hydrogens]],index=['燃油汽车','电动汽车','燃料电池汽车'])
        costs=pd.DataFrame([cost_oil_fuel.loc[oils],cost_ev_fuel.loc[powers],cost_fcv_fuel.loc[hydrogens]],index=['燃油汽车','电动汽车','燃料电池汽车'])
        charges=pd.DataFrame([charge_oil_fuel.loc[oil_charge],charge_ev_fuel.loc[ev_charge],charge_fcv_fuel.loc[fcv_charge]],index=['燃油汽车','电动汽车','燃料电池汽车'])
        return efs,costs,charges

@st.cache_data
def capital_cost_sensetivity_analysis(sa_capital_cost=[],lang_ZH_or_not=True,vehicle_type='25吨牵引车',carbon_tax=50,year=2021,trip='上海-北京',toll_parameter=1,driver_salary_per_month=0,full_load_rate=1,full_work_rate=1,ef_fuels=pd.DataFrame(),cost_fuels=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车']),charge_speeds=pd.DataFrame(index=['燃油汽车','电动汽车','燃料电池汽车'])):
    df_vehicle_om=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name='运营参数',index_col=0)
    df_trip_data=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name='线路',index_col=0)
    bool_of_zh={'是':True,'否':False}
    if driver_salary_per_month>0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','司机工资','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Driver salary','Carbon tax']
    elif driver_salary_per_month==0:
        if lang_ZH_or_not:
            economy_index=['收入','购置成本','补能成本','过路费','维修保险费','碳税']
        else:
            economy_index=['Income','Capital cost','Fuel cost','Toll','Maintaince and Insurance','Carbon tax']
    compare_fuel=['燃油汽车','电动汽车']
    compare_fuel_economy_result=pd.DataFrame(0,index=compare_fuel,columns=economy_index)
    compare_fuel_cost_mix_result=pd.DataFrame(0,index=compare_fuel,columns=economy_index[1:])
    compare_fuel_emission_result=pd.Series(0,index=compare_fuel)
    for ft in compare_fuel:
        df_vehicle=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name=ft,index_col=0)
        vehicle_life=int(df_vehicle_om.loc['车辆寿命',year])
        future_fuel_cost=pd.Series(0,index=range(vehicle_life))
        future_fuel_ef=pd.Series(0,index=range(vehicle_life))
        for y in future_fuel_cost.index:
            future_fuel_cost.loc[y]=cost_fuels.loc[ft,year+y]
            future_fuel_ef.loc[y]=ef_fuels.loc[ft,year+y]
        nev=True
        if ft == '燃油汽车':
            nev=False
        lca_economy_mix,lca_emissions=cal_vehicle_life_economy(nev_or_not=nev,fuel_capacity=df_vehicle.loc['载能容量',year],body_weight=df_vehicle.loc['车身质量',year],battery_weight=df_vehicle.loc['电池质量',year],capital_cost=df_vehicle.loc['购置成本',year],fuel_consumption_rate=df_vehicle.loc['百公里能耗',year],life_fuel_price=future_fuel_cost,cold_fuel_rate=df_vehicle.loc['低温能耗率',year],charge_speed=charge_speeds.loc[ft,year],lca_ef=future_fuel_ef,insurance_per_year=df_vehicle.loc['单年保险费',year],maintainance_per_km=df_vehicle.loc['保养费用',year],maintainance_per_year=df_vehicle.loc['单年维修费',year],discount_rate=df_vehicle_om.loc['折现率',year],vehicle_life=vehicle_life,workday_ratio=df_vehicle_om.loc['工作日占比',year],workhour_per_driver=df_vehicle_om.loc['单人工作时间',year],number_of_driver=df_vehicle_om.loc['司机人数',year],driver_salary_per_month=driver_salary_per_month,average_speed=df_vehicle_om.loc['平均行驶速度',year],toll_per_km=df_vehicle_om.loc['通行费',year],toll_parameter=toll_parameter,tier_per_km=df_vehicle_om.loc['轮胎损耗',year],allowed_weight=df_vehicle_om.loc['额定总重',year],cold_month=df_trip_data.loc[trip,'寒冷月'],trip_length=df_trip_data.loc[trip,'距离'],freight_or_not=bool_of_zh[df_trip_data.loc[trip,'是否货运']],average_weight_price=df_trip_data.loc[trip,'单位运价'],average_income_per_trip=df_trip_data.loc[trip,'整车运价'],carbon_tax=carbon_tax,lang_ZH_or_not=lang_ZH_or_not,full_load_rate=full_load_rate,full_work_rate=full_work_rate)
        compare_fuel_economy_result.loc[ft]=lca_economy_mix
        compare_fuel_cost_mix_result.loc[ft]=cal_cost_percent(lca_economy_mix)
        compare_fuel_emission_result.loc[ft]=lca_emissions
    if len(sa_capital_cost)>0:
        ft='燃料电池汽车'
        df_vehicle=pd.read_excel('./data/'+vehicle_type+'.xlsx',sheet_name=ft,index_col=0)
        vehicle_life=int(df_vehicle_om.loc['车辆寿命',year])
        future_fuel_cost=pd.Series(0,index=range(vehicle_life))
        future_fuel_ef=pd.Series(0,index=range(vehicle_life))
        for y in future_fuel_cost.index:
            future_fuel_cost.loc[y]=cost_fuels.loc[ft,year+y]
            future_fuel_ef.loc[y]=ef_fuels.loc[ft,year+y]
        nev=True
        sa_economy_result=pd.DataFrame(0,index=sa_capital_cost,columns=economy_index)
        sa_cost_mix_result=pd.DataFrame(0,index=sa_capital_cost,columns=economy_index[1:])
        sa_emission_result=pd.Series(0,index=sa_capital_cost)
        for cc in sa_capital_cost:
            lca_economy_mix,lca_emissions=cal_vehicle_life_economy(nev_or_not=nev,fuel_capacity=df_vehicle.loc['载能容量',year],body_weight=df_vehicle.loc['车身质量',year],battery_weight=df_vehicle.loc['电池质量',year],capital_cost=cc*10000,fuel_consumption_rate=df_vehicle.loc['百公里能耗',year],life_fuel_price=future_fuel_cost,cold_fuel_rate=df_vehicle.loc['低温能耗率',year],charge_speed=charge_speeds.loc[ft,year],lca_ef=future_fuel_ef,insurance_per_year=df_vehicle.loc['单年保险费',year],maintainance_per_km=df_vehicle.loc['保养费用',year],maintainance_per_year=df_vehicle.loc['单年维修费',year],discount_rate=df_vehicle_om.loc['折现率',year],vehicle_life=vehicle_life,workday_ratio=df_vehicle_om.loc['工作日占比',year],workhour_per_driver=df_vehicle_om.loc['单人工作时间',year],number_of_driver=df_vehicle_om.loc['司机人数',year],driver_salary_per_month=driver_salary_per_month,average_speed=df_vehicle_om.loc['平均行驶速度',year],toll_per_km=df_vehicle_om.loc['通行费',year],toll_parameter=toll_parameter,tier_per_km=df_vehicle_om.loc['轮胎损耗',year],allowed_weight=df_vehicle_om.loc['额定总重',year],cold_month=df_trip_data.loc[trip,'寒冷月'],trip_length=df_trip_data.loc[trip,'距离'],freight_or_not=bool_of_zh[df_trip_data.loc[trip,'是否货运']],average_weight_price=df_trip_data.loc[trip,'单位运价'],average_income_per_trip=df_trip_data.loc[trip,'整车运价'],carbon_tax=carbon_tax,lang_ZH_or_not=lang_ZH_or_not,full_load_rate=full_load_rate,full_work_rate=full_work_rate)
            sa_economy_result.loc[cc]=lca_economy_mix
            sa_cost_mix_result.loc[cc]=cal_cost_percent(lca_economy_mix)
            sa_emission_result.loc[cc]=lca_emissions
    return compare_fuel_economy_result,compare_fuel_cost_mix_result,compare_fuel_emission_result,sa_economy_result,sa_cost_mix_result,sa_emission_result