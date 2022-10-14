import streamlit as st
import boto3
import sqlite3
import pandas as pd
import os
from pyecharts import options as opts
from pyecharts.charts import Line
from streamlit_echarts import st_pyecharts
import numpy as np


def get_pct_change(df, col_name):
    numerator = df[col_name].tail(1).values[0] - df[col_name].head(1).values[0]
    denominator = df[col_name].head(1).values[0]
    change_ = np.round(((numerator / denominator) * 100), 2)
    return change_


db = 'listings_master.db'
fp = os.path.join('db', db)
conn = sqlite3.connect(fp)

master = pd.read_sql('select * from "{}"'.format(db), conn)
master['LastUpdated'] = pd.to_datetime(master['LastUpdated'])
master = master.sort_values(by='LastUpdated')

apt = master.query("HomeType == 'APARTMENT'")
cond = master.query("HomeType == 'CONDO'")
th = master.query("HomeType == 'TOWNHOUSE'")
sfh = master.query("HomeType == 'SINGLE_FAMILY'")

apt_ = apt.resample('W', on='LastUpdated')\
    .agg({'ListedPrice': 'mean', 'zpid': 'nunique'})\
    .astype(int)\
    .reset_index()

th_ = th.resample('W', on='LastUpdated')\
    .agg({'ListedPrice': 'mean', 'zpid': 'nunique'})\
    .astype(int)\
    .reset_index()

sfh_ = sfh.resample('W', on='LastUpdated')\
    .agg({'ListedPrice': 'mean', 'zpid': 'nunique'})\
    .astype(int)\
    .reset_index()

cond_ = cond.resample('W', on='LastUpdated')\
    .agg({'ListedPrice': 'mean', 'zpid': 'nunique'})\
    .astype(int)\
    .reset_index()

apt_ = apt_.rename(columns={'ListedPrice': 'APT_price', 'zpid': 'APT_count'})
th_ = th_.rename(columns={'ListedPrice': 'TH_price', 'zpid': 'TH_count'})
cond_ = cond_.rename(columns={'ListedPrice': 'COND_price', 'zpid': 'COND_count'})
sfh_ = sfh_.rename(columns={'ListedPrice': 'SFH_price', 'zpid': 'SFH_count'})

# Streamlit Page Starts Here
st.set_page_config(layout='wide')
st.title("🏠 Zillow Pricing Trends Dashboard (June 2022 - Present) 🏠")
st.caption("Brought to you by BJT Studios")
os.chdir('/z_stream_home')

date_list = [d.strftime('%m/%d/%y') for d in apt_.LastUpdated.tolist()]
nat_mort_rate = [5.78, 5.81, 5.70, 5.30, 5.51, 5.54, 5.30, 4.99, 5.22, 5.13, 5.55,
                 5.66, 5.89, 6.02, 6.29, 6.70, 6.66, 6.92]

ten_yr = pd.read_excel('../10yr_rates.xlsx', parse_dates=['Date'])
ten_yr_ = ten_yr.resample('W', on='Date')\
    .agg({'Rate': 'mean'})\
    .reset_index()

ff = pd.read_excel('../FF.xlsx', parse_dates=['Date'])
ff_ = ff.resample('W', on='Date').agg({'Fed_Rate': 'mean'}).reset_index()


with st.container() as metrics:
    a, b, c, d = st.columns(4)
    with a:
        pct_change = get_pct_change(apt_, 'APT_price')
        num = apt_.APT_price.iloc[-5] - apt_.APT_price.head(1).values[0]
        den = apt_.APT_price.head(1).values[0]
        mom = np.round(((num / den) * 100), 2)

        st.metric(label='Apartment Price Change (%)', value="{:.2f}%".format(pct_change),
                  delta='{:.2f} % Points MoM'.format(pct_change - mom))
    with b:
        pct_change = get_pct_change(cond_, 'COND_price')
        num = cond_.COND_price.iloc[-5] - cond_.COND_price.head(1).values[0]
        den = cond_.COND_price.head(1).values[0]
        mom = np.round(((num / den) * 100), 2)
        st.metric(label='Condo Price Change (%)', value="{:.2f}%".format(pct_change),
                  delta='{:.2f} % Points MoM'.format(pct_change - mom))
    with c:
        pct_change = get_pct_change(th_, 'TH_price')
        num = th_.TH_price.iloc[-5] - th_.TH_price.head(1).values[0]
        den = th_.TH_price.head(1).values[0]
        mom = np.round(((num / den) * 100), 2)
        st.metric(label='Townhouse Price Change (%)', value="{:.2f}%".format(pct_change),
                  delta='{:.2f} % Points MoM'.format(pct_change - mom))
    with d:
        pct_change = get_pct_change(sfh_, 'SFH_price')
        num = sfh_.SFH_price.iloc[-5] - sfh_.SFH_price.head(1).values[0]
        den = sfh_.SFH_price.head(1).values[0]
        mom = np.round(((num / den) * 100), 2)
        st.metric(label='Single Family Home Price Change (%)', value="{:.2f}%".format(pct_change),
                  delta='{:.2f} % Points MoM'.format(pct_change - mom))

with st.container() as charts:
    a, b = st.columns(2)
    with a:
        apt_price = (
            Line(init_opts=opts.InitOpts())
                .add_xaxis(date_list)
                .add_yaxis("Apartments", apt_.APT_price.tolist(), linestyle_opts=opts.LineStyleOpts(width=2))
                .extend_axis(yaxis=opts.AxisOpts(type_="value", position="right", min_=4))
                .add_yaxis("30Yr Mortgage Rate", nat_mort_rate, yaxis_index=1,
                           linestyle_opts=opts.LineStyleOpts(type_='dotted'))
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(title_opts=opts.TitleOpts(title='Average List Price of Apartments'),
                                 toolbox_opts=opts.ToolboxOpts(is_show=False),
                                 legend_opts=opts.LegendOpts(pos_right=True))
        )
        st_pyecharts(apt_price, key='avgLine')

    with b:
        apt_count = (
            Line(init_opts=opts.InitOpts())
                .add_xaxis(date_list)
                .add_yaxis("Apartments", apt_.APT_count.tolist(), linestyle_opts=opts.LineStyleOpts(width=2))
                .extend_axis(yaxis=opts.AxisOpts(type_="value", position="right", min_=4))
                .add_yaxis("30Yr Mortgage Rate", nat_mort_rate, yaxis_index=1,
                           linestyle_opts=opts.LineStyleOpts(type_='dotted'))
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(title_opts=opts.TitleOpts(title='Count of Apartments'),
                                 toolbox_opts=opts.ToolboxOpts(is_show=False),
                                 legend_opts=opts.LegendOpts(pos_right=True))
        )
        st_pyecharts(apt_count, key='countLine')

    c, d = st.columns(2)
    with c:
        cond_price = (
            Line(init_opts=opts.InitOpts())
                .add_xaxis(date_list)
                .add_yaxis("Condos", cond_.COND_price.tolist(), linestyle_opts=opts.LineStyleOpts(width=2))
                .extend_axis(yaxis=opts.AxisOpts(type_="value", position="right", min_=4))
                .add_yaxis("30Yr Mortgage Rate", nat_mort_rate, yaxis_index=1,
                           linestyle_opts=opts.LineStyleOpts(type_='dotted'))
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title='Average List Price of Condos'),
                toolbox_opts=opts.ToolboxOpts(is_show=False),
                legend_opts=opts.LegendOpts(pos_right=True),
                yaxis_opts=opts.AxisOpts(min_=200000))
        )
        st_pyecharts(cond_price, key='condPriceLine')

    with d:
        cond_count = (
            Line(init_opts=opts.InitOpts())
                .add_xaxis(date_list)
                .add_yaxis("Condos", cond_.COND_count.tolist(), linestyle_opts=opts.LineStyleOpts(width=2))
                .extend_axis(yaxis=opts.AxisOpts(type_="value", position="right", min_=4))
                .add_yaxis("30Yr Mortgage Rate", nat_mort_rate, yaxis_index=1,
                           linestyle_opts=opts.LineStyleOpts(type_='dotted'))
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title='Count of Condos'),
                toolbox_opts=opts.ToolboxOpts(is_show=False),
                legend_opts=opts.LegendOpts(pos_right=True))
        )
        st_pyecharts(cond_count, key='condCountLine')

    e, f = st.columns(2)
    with e:
        th_price = (
            Line(init_opts=opts.InitOpts())
                .add_xaxis(date_list)
                .add_yaxis("Townhouses", th_.TH_price.tolist(), linestyle_opts=opts.LineStyleOpts(width=2))
                .extend_axis(yaxis=opts.AxisOpts(type_="value", position="right", min_=4))
                .add_yaxis("30Yr Mortgage Rate", nat_mort_rate, yaxis_index=1,
                           linestyle_opts=opts.LineStyleOpts(type_='dotted'))
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title='Average List Price of Townhouses'),
                toolbox_opts=opts.ToolboxOpts(is_show=False),
                legend_opts=opts.LegendOpts(pos_right=True),
                yaxis_opts=opts.AxisOpts(min_=500000))
        )
        st_pyecharts(th_price, key='thPriceLine')

    with f:
        th_count = (
            Line(init_opts=opts.InitOpts())
                .add_xaxis(date_list)
                .add_yaxis("Townhouses", th_.TH_count.tolist(), linestyle_opts=opts.LineStyleOpts(width=2))
                .extend_axis(yaxis=opts.AxisOpts(type_="value", position="right", min_=4))
                .add_yaxis("30Yr Mortgage Rate", nat_mort_rate, yaxis_index=1,
                           linestyle_opts=opts.LineStyleOpts(type_='dotted'))
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title='Count of Townhouses'),
                toolbox_opts=opts.ToolboxOpts(is_show=False),
                legend_opts=opts.LegendOpts(pos_right=True),
                yaxis_opts=opts.AxisOpts(min_=300))
        )
        st_pyecharts(th_count, key='thCountLine')

    g, h = st.columns(2)
    with g:
        sfh_price = (
            Line(init_opts=opts.InitOpts())
                .add_xaxis(date_list)
                .add_yaxis("Single Family", sfh_.SFH_price.tolist(), linestyle_opts=opts.LineStyleOpts(width=2))
                .extend_axis(yaxis=opts.AxisOpts(type_="value", position="right", min_=4))
                .add_yaxis("30Yr Mortgage Rate", nat_mort_rate, yaxis_index=1,
                           linestyle_opts=opts.LineStyleOpts(type_='dotted'))
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title='Average List Price of SFHs'),
                toolbox_opts=opts.ToolboxOpts(is_show=False),
                legend_opts=opts.LegendOpts(pos_right=True),
                yaxis_opts=opts.AxisOpts(min_=1000000))
        )
        st_pyecharts(sfh_price, key='sfhLine')

    with h:
        sfh_count = (
            Line(init_opts=opts.InitOpts())
                .add_xaxis(date_list)
                .add_yaxis("Single Family", sfh_.SFH_count.tolist(), linestyle_opts=opts.LineStyleOpts(width=2))
                .extend_axis(yaxis=opts.AxisOpts(type_="value", position="right", min_=4))
                .add_yaxis("30Yr Mortgage Rate", nat_mort_rate, yaxis_index=1,
                           linestyle_opts=opts.LineStyleOpts(type_='dotted'))
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title='Count of SFH Listings'),
                toolbox_opts=opts.ToolboxOpts(is_show=False),
                legend_opts=opts.LegendOpts(pos_right=True),
                yaxis_opts=opts.AxisOpts(min_=700))
        )
        st_pyecharts(sfh_count, key='sfhCountLine')

with st.container() as rate_container:

    rates_ = (
        Line(init_opts=opts.InitOpts())
            .add_xaxis(date_list)
            .add_yaxis("10 Year Treasury Yield", ten_yr_.Rate.tolist(), linestyle_opts=opts.LineStyleOpts(width=2))
            .add_yaxis("Federal Funds Rate", ff_.Fed_Rate.tolist(), linestyle_opts=opts.LineStyleOpts(width=2))
            .add_yaxis("30Yr Mortgage Rate", nat_mort_rate, linestyle_opts=opts.LineStyleOpts(width=2))
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(
            title_opts=opts.TitleOpts(title='Federal Fund Rate vs. 10 Year Treasury Yield vs. 30 Yr Fixed Mortgage Rate'),
            toolbox_opts=opts.ToolboxOpts(is_show=False),
            legend_opts=opts.LegendOpts(pos_right=True))
    )
    st_pyecharts(rates_, key='rates')


