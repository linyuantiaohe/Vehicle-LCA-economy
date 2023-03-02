import streamlit as st
import pandas as pd
from PIL import Image


st.set_page_config(
    page_title="车辆生命周期评价工具",
    page_icon="😎",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Work hard!"
    }
)

st.title('车辆生命周期经济-环境评价模型')
st.markdown('模型原理如图所示,考虑了购置、使用、至报废全生命周期内的货运车辆的成本和收益.其中,成本包括购置成本、补能成本、司机成本、过路费、维修保险等.收入则为给定运行强度下所有的运费收入,该时间不考虑装卸时间和等货时间,但包括补能时间.为反应新能源汽车的特性,该模型考虑了电池、储氢罐质量对载货能力的影响,以及气温等外部环境对单位能耗的影响。')
st.image(Image.open('./model_fig.jpg'))
st.sidebar.markdown("@Copyright 华北电力大学 经济与管理学院 王歌课题组")
st.sidebar.markdown("欢迎提出意见和建议!")
st.sidebar.markdown("E-mail: wangge@ncepu.edu.cn")
st.sidebar.map(pd.DataFrame(pd.Series([40.088243727163956,116.30600799534605],index=['lat', 'lon']),columns=['Ncepu']).T)


