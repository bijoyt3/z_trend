import streamlit as st
import sqlite3
import boto3
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Line
from streamlit_echarts import st_pyecharts
import numpy as np
import time
import fredapi


def get_pct_change(df, col_name):
    numerator = df[col_name].tail(1).values[0] - df[col_name].head(1).values[0]
    denominator = df[col_name].head(1).values[0]
    change_ = np.round(((numerator / denominator) * 100), 2)
    return change_


def resample(asset_type: str, abbrev: str):
    filtered = master.query("HomeType == 'APARTMENT'")
    resampled = filtered.resample('W', on='LastUpdated')\
        .agg({'ListedPrice': 'mean', 'zpid': 'nunique'})\
        .astype(int)\
        .reset_index() \
        .rename(columns={'ListedPrice': '{}_price'.format(abbrev), 'zpid': '{}_count'.format(abbrev)})

    # df_ = df.resample('W', on='LastUpdated') \
    #     .agg({'ListedPrice': 'mean', 'zpid': 'nunique'}) \
    #     .astype(int) \
    #     .reset_index() \
    #     .rename(columns={'ListedPrice': '{}_price'.format(name), 'zpid': '{}_count'.format(name)})

    return resampled


def resample_fred(series_id: str, sample: str, start_dt: str):
    df = fred.get_series(series_id=series_id, observation_start=start_dt)
    df_ = pd.DataFrame(df)\
        .reset_index()\
        .rename(columns={'index': 'Date', 0: 'Rate'})\
        .resample(sample, on='Date')\
        .agg({'Rate': 'mean'})\
        .round(2)\
        .reset_index()

    return df_


start = time.time()

s3_client = boto3.client(service_name='s3',
                         region_name=st.secrets['AWS_CREDS']['aws_region'],
                         aws_access_key_id=st.secrets['AWS_CREDS']['aws_access_key_id'],
                         aws_secret_access_key=st.secrets['AWS_CREDS']['aws_secret_access_key'])

s3_client.download_file('listingszillow2022', 'listings_master.db', 'listings_master.db')

db = 'listings_master.db'
conn = sqlite3.connect(db)

master = pd.read_sql('select * from "{}"'.format(db), conn)
master['LastUpdated'] = pd.to_datetime(master['LastUpdated'])
master = master.sort_values(by='LastUpdated')

apt = resample('APARTMENT', 'APT')

# apt = master.query("HomeType == 'APARTMENT'")
cond = master.query("HomeType == 'CONDO'")
th = master.query("HomeType == 'TOWNHOUSE'")
sfh = master.query("HomeType == 'SINGLE_FAMILY'")

# apt_ = resample(apt, 'APT')
cond_ = resample(cond, 'COND')
th_ = resample(th, 'TH')
sfh_ = resample(sfh, 'SFH')

# Streamlit Page Starts Here
st.set_page_config(layout='wide')
st.title("🏠 Zillow Pricing Trends Dashboard (June 2022 - Present) 🏠")
st.caption("Brought to you by BJT Studios")
with st.sidebar:
    st.write("""
    ## About:

    Welcome to the **🏠 Zillow Pricing Trends Dashboard 🏠️**. The intent of this application is to track listing price 
    trends in Loudoun County and Fairfax County. 


    ## Data:
    Housing data comes from Zillow - the underlying dataset is a daily scrape of homes for sale on Zillow in 
    116 zipcodes of Loudoun County and Fairfax County. It's important to note that the key metric that is being
    observed here is **LIST PRICE**. Other listing attributes such as Days on Market and Sales Price were considered.
    
    Rate data comes from the St. Louis Fed: https://fred.stlouisfed.org/
    
    + 30 Year Mortage Rate: https://fred.stlouisfed.org/series/MORTGAGE30US
    + 10 Year Treasury Yield: https://fred.stlouisfed.org/series/DGS10
    + Federal Funds Rate: https://fred.stlouisfed.org/series/FEDFUNDS
    
    This data is refreshed daily but aggregated weekly to illustrate macro trends in the market. Collection of 
    housing data began in mid-June 2022.

    """)
st.info("Data Last Updated: {}".format(max(th.LastUpdated).strftime('%m/%d/%y')), icon="ℹ️")


date_list = [d.strftime('%m/%d/%y') for d in th_.LastUpdated.tolist()]

fred_key = st.secrets['FRED_API_KEY']['key']
fred = fredapi.Fred(api_key=fred_key)

treasury_resample = resample_fred(series_id='DGS10', sample='W', start_dt='2022-06-12')
fixedmortgage_resample = resample_fred(series_id='MORTGAGE30US', sample='W', start_dt='2022-06-12')
fedfunds_resample = resample_fred(series_id='FEDFUNDS', sample='M', start_dt='2022-05-12')


with st.container() as metrics:
    a, b, c, d = st.columns(4)
    with a:
        pct_change = get_pct_change(apt, 'APT_price')
        num = apt.APT_price.iloc[-5] - apt.APT_price.head(1).values[0]
        den = apt.APT_price.head(1).values[0]
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
                .add_yaxis("Apartments", apt.APT_price.tolist(), linestyle_opts=opts.LineStyleOpts(width=2))
                .extend_axis(yaxis=opts.AxisOpts(type_="value", position="right", min_=4))
                .add_yaxis("30Yr Mortgage Rate", fixedmortgage_resample.Rate.tolist(), yaxis_index=1,
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
                .add_yaxis("Apartments", apt.APT_count.tolist(), linestyle_opts=opts.LineStyleOpts(width=2))
                .extend_axis(yaxis=opts.AxisOpts(type_="value", position="right", min_=4))
                .add_yaxis("30Yr Mortgage Rate", fixedmortgage_resample.Rate.tolist(), yaxis_index=1,
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
                .add_yaxis("30Yr Mortgage Rate", fixedmortgage_resample.Rate.tolist(), yaxis_index=1,
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
                .add_yaxis("30Yr Mortgage Rate", fixedmortgage_resample.Rate.tolist(), yaxis_index=1,
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
                .add_yaxis("30Yr Mortgage Rate", fixedmortgage_resample.Rate.tolist(), yaxis_index=1,
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
                .add_yaxis("30Yr Mortgage Rate", fixedmortgage_resample.Rate.tolist(), yaxis_index=1,
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
                .add_yaxis("30Yr Mortgage Rate", fixedmortgage_resample.Rate.tolist(), yaxis_index=1,
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
                .add_yaxis("30Yr Mortgage Rate", fixedmortgage_resample.Rate.tolist(), yaxis_index=1,
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
    rate1, rate2, rate3 = st.columns(3)
    with rate1:
        fed_date = [d.strftime('%b %y') for d in fedfunds_resample.Date.tolist()]
        fed_funds = (
            Line(init_opts=opts.InitOpts())
                .add_xaxis(fed_date)
                .add_yaxis("Federal Funds Rate", fedfunds_resample.Rate.tolist(), linestyle_opts=opts.LineStyleOpts(width=2),
                           color='#367E18')
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title='Federal Fund Rate'),
                toolbox_opts=opts.ToolboxOpts(is_show=False),
                legend_opts=opts.LegendOpts(pos_right=True))
        )

        st_pyecharts(fed_funds, key='fed_funds')

    with rate2:
        treas_date = [d.strftime('%m/%d/%y') for d in treasury_resample.Date.tolist()]
        treasury = (
            Line(init_opts=opts.InitOpts())
                .add_xaxis(treas_date)
                .add_yaxis("10 Year Treasury Yield", treasury_resample.Rate.tolist(), linestyle_opts=opts.LineStyleOpts(width=2),
                           color='#749F82')
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title='10 Year Treasury Yield'),
                toolbox_opts=opts.ToolboxOpts(is_show=False),
                legend_opts=opts.LegendOpts(pos_right=True),
                yaxis_opts=opts.AxisOpts(min_=2))
        )

        st_pyecharts(treasury, key='treasury')

    with rate3:
        mort_date = [d.strftime('%m/%d/%y') for d in fixedmortgage_resample.Date.tolist()]
        thirty_year = (
            Line(init_opts=opts.InitOpts())
                .add_xaxis(mort_date)
                .add_yaxis("30Yr Mortgage Rate", fixedmortgage_resample.Rate.tolist(), linestyle_opts=opts.LineStyleOpts(width=2), color='#425F57')
                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title='30 Yr Fixed Mortage Rate'),
                toolbox_opts=opts.ToolboxOpts(is_show=False),
                legend_opts=opts.LegendOpts(pos_right=True),
                yaxis_opts=opts.AxisOpts(min_=4))
        )

        st_pyecharts(thirty_year, key='30y')

st.info("Page Loaded in {:.2f} seconds".format(time.time() - start))