# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 13:59:06 2018

@author: r: lucas.xu
"""


import json
import time
import pandas as pd
import os
from bs4 import BeautifulSoup  
from pyecharts import Bar,Line,Overlap
from selenium import webdriver 
os.chdir('D:/爬虫/电视剧')

## 爬取剧集列表，并输出成为excel表格
driver = webdriver.Chrome()
driver.maximize_window()    
driver.close() 
driver.switch_to_window(driver.window_handles[0])  
url = 'https://movie.douban.com/tag/#/?sort=U&range=2,10&tags=%E7%94%B5%E8%A7%86%E5%89%A7,%E4%B8%AD%E5%9B%BD%E5%A4%A7%E9%99%86'
js='window.open("'+url+'")'
driver.execute_script(js)
driver.close() 
driver.switch_to_window(driver.window_handles[0])
while True:
   try: 
     js="var q=document.documentElement.scrollTop=10000000"  
     driver.execute_script(js)
     driver.find_element_by_class_name('more').click()
     time.sleep(2)
   except:
     break 

name = [k.text for k in driver.find_elements_by_class_name('title')]   
score = [k.text for k in driver.find_elements_by_class_name('rate')]   
url = [k.get_attribute('href') for k in driver.find_elements_by_class_name('item')]  
pd.DataFrame({'name':name,'score':score,'url':url}).to_excel('电视剧名称.xlsx')


## 通过剧集列表循环爬取剧集信息，以及演员评分
drama_list = pd.read_excel('电视剧名称.xlsx')
driver = webdriver.Chrome()
driver.maximize_window()    
driver.close() 
driver.switch_to_window(driver.window_handles[0])   
drama_info = pd.DataFrame(columns=['id','name','score','count','year','content','short','genre',
                                   'director','author'])
actor_info = pd.DataFrame(columns=['name','url','drama_id','score','drama','rank','count'])

  
for i in range(drama_list.shape[0]):
    try:
        url = drama_list['url'][i]
        js='window.open("'+url+'")'
        driver.execute_script(js)
        driver.close() 
        driver.switch_to_window(driver.window_handles[0])
        bsObj=BeautifulSoup(driver.page_source,"html.parser")
        time.sleep(2)
        data =  json.loads(bsObj.find('script',attrs={'type':'application/ld+json'}).contents[0].replace('\n','').replace(' ',''))
        actor_name = [k['name'] for k in data['actor']]
        actor_url = [k['url'] for k in data['actor']]       
        drama_director = [k['name'] for k in data['director']]
        drama_author = [k['name'] for k in data['author']]
        drama_score = data['aggregateRating']['ratingValue']
        drama_count = data['aggregateRating']['ratingCount']
        drama_name = data['name']
        drama_genre = data['genre']
        drama_year = bsObj.find('span',attrs={"class":"year"}).text[1:5]
        drama_content =  bsObj.find('span',attrs={"property":"v:summary"}).text.replace('\n','')
        drama_short =[k.text for k in  bsObj.find_all('span',attrs={"class":"short"})]
        drama_info = drama_info.append({'id':drama_list['url'][i],'name':drama_name,'score':drama_score,'count':drama_count,
                                        'year':drama_year,'content':drama_content,
                                        'short':drama_short,'genre':drama_genre,
                                        'director':drama_director,'author':drama_author},
                                        ignore_index=True)
        this_actors=pd.DataFrame({'name':actor_name,'url':actor_url,'drama_id':drama_list['url'][i],'score':drama_score,
                                  'drama':drama_name,'rank':list(range(len(actor_name))),'count':drama_count})
        actor_info = pd.concat([actor_info,this_actors])
        print(str(i))
    except:
        print(drama_list['name'][i])
        continue
        
drama_info.to_excel('电视剧统计.xlsx')
actor_info.to_excel('演员统计.xlsx')  

## 整理演员评分信息 包含主角 重要角色 次要角色数据
actor_all = pd.read_excel('演员统计.xlsx')   
actor_all['rank'] = actor_all['rank']+1
actor_all['main'] = [1 if k<=2 else 0 for k in actor_all['rank']]
actor_all['important'] = [1 if k<=5&k>=3 else 0 for k in actor_all['rank']]
actor_all['other'] = [1 if k<=10&k>=6 else 0 for k in actor_all['rank']]
actor_all['count_reg'] = [k if k<2000 else 2000 for k in actor_all['count']]
actor_all['count_stat'] = actor_all['main']*1*actor_all['count_reg']+actor_all['important']*0.5*actor_all['count_reg']+actor_all['other']*0.1*actor_all['count_reg']
actor_all['count_score'] = actor_all['count_stat']*actor_all['score']
actor_grouped = actor_all.groupby(['name','url'])
actor_stat = actor_grouped.agg({'count_score': ['sum'],
                          'count_stat':['sum'],
                          'main':['sum'],
                          'important':['sum'],
                          'other':['sum'],
                          'rank':['count']}).reset_index()
actor_stat.columns = ['name', 'url', 'count_score','count_stat', 'main_num', 'important_num','ohter_num','total_num']
actor_stat['score']=actor_stat['count_score']/actor_stat['count_stat']

## 筛选出需要进行对比的主要演员名单
actor_main = actor_stat[(actor_stat['main_num']>=2) & (actor_stat['count_stat']>=3000)].reset_index()
actor_more = pd.DataFrame(columns=['name','url','sex','xingzuo','birth_year','birth_date','hometown'])

## 循环爬取演员信息
for i in range(actor_main.shape[0]):
    try:
        url = 'https://movie.douban.com'+actor_main['url'][i]
        js='window.open("'+url+'")'
        driver.execute_script(js)
        driver.close() 
        driver.switch_to_window(driver.window_handles[0])
        bsObj=BeautifulSoup(driver.page_source,"html.parser")
        actor_info = bsObj.find('div',attrs={"class":"info"}).text.split()
        sex = actor_info[1]
        xingzuo = actor_info[3]
        birth_year = actor_info[5][0:4]
        birth_date = actor_info[5][5:11]
        hometown = actor_info[7].split(',')[-1]
        actor_more = actor_more.append({'name':actor_main['name'][i],'url':actor_main['url'][i],
                           'sex':sex,'xingzuo':xingzuo,
                           'birth_year':birth_year,'birth_date':birth_date,
                           'hometown':hometown},ignore_index=True)
        print(str(i))
    except:
        print(actor_main['name'][i])    
        continue
actor_data = pd.merge(actor_main,actor_more,how='left',on=['name','url'])    



## 剧集排名可视化
drama_all = pd.read_excel('电视剧统计.xlsx')  
drama_main = drama_all[drama_all['count']>=1000]
bottom_15_drama = drama_main.sort_values('score')[0:15]
top_15_drama = drama_main.sort_values('score',ascending=False)[0:15]


attr = top_15_drama['name']
v1=top_15_drama['year']
v2=top_15_drama['score']
line = Line("TOP15电视剧评分/拍摄年份")
line.add("评分", attr, v2, is_stack=True,xaxis_rotate=30,
         xaxis_interval=0,line_color='purple',
         line_width=4,is_splitline_show=False,yaxis_min=8,is_label_show=True)
  
bar = Bar("TOP15电视剧评分/拍摄年份")
bar.add("拍摄年份", attr, v1, is_stack=False,xaxis_rotate=30,is_yaxis_show=False,
         xaxis_interval =0,is_splitline_show=False,yaxis_min=1975,yaxis_max=2050,
         is_label_show=True,bar_col='green')
overlap = Overlap()

overlap.add(line)
overlap.add(bar, yaxis_index=1, is_add_yaxis=True)
overlap.render('TOP15电视剧评分_拍摄年份.html')

attr = bottom_15_drama['name']
v1=bottom_15_drama['year']
v2=bottom_15_drama['score']
line = Line("BOTTOM15电视剧评分/拍摄年份")
line.add("评分", attr, v2, is_stack=True,xaxis_rotate=30,
         xaxis_interval=0,line_color='purple',
         line_width=4,is_splitline_show=False,yaxis_min=1,is_label_show=True)
  
bar = Bar("BOTTOM15电视剧评分/拍摄年份")
bar.add("拍摄年份", attr, v1, is_stack=False,xaxis_rotate=45,is_yaxis_show=False,
         xaxis_interval =0,is_splitline_show=False,yaxis_min=1975,yaxis_max=2050,
         is_label_show=True,bar_col='green')
overlap = Overlap()
overlap.add(line)
overlap.add(bar, yaxis_index=1, is_add_yaxis=True)
overlap.render('BOTTOM15电视剧评分_拍摄年份.html')


## 演员排名可视化
actor_data['name']=[k.split(' ')[0] for k in actor_data['name']]
actor_data['score'] = round(actor_data['score'],2)
actor_data['birth_year'] = round(actor_data['birth_year'],0)

bottom_20_actor = actor_data.sort_values('score')[0:20]
top_20_actor = actor_data.sort_values('score',ascending=False)[0:20]
attr = bottom_20_actor['name']
v1=bottom_20_actor['birth_year']
v2=bottom_20_actor['score']
line = Line("BOTTOM20演员评分/出生年份")
line.add("评分", attr, v2, is_stack=True,xaxis_rotate=30,
         xaxis_interval=0,line_color='purple',
         line_width=4,is_splitline_show=False,yaxis_min=1,is_label_show=True)
  
bar = Bar("BOTTOM20演员评分/出生年份")
bar.add("出生年份", attr, v1, is_stack=False,xaxis_rotate=45,is_yaxis_show=False,
         xaxis_interval =0,is_splitline_show=False,yaxis_min=1930,yaxis_max=2080,
         is_label_show=True,bar_col='green')
overlap = Overlap()
overlap.add(line)
overlap.add(bar, yaxis_index=1, is_add_yaxis=True)
overlap.render('BOTTOM20演员评分_出生年份.html')

top_20_80_actor = actor_data[(actor_data['birth_year']>=1980)&(actor_data['birth_year']<=1989)].sort_values('score',ascending=False)[0:20]
attr = top_20_80_actor['name']
v1=top_20_80_actor['birth_year']
v2=top_20_80_actor['score']
line = Line("TOP20 80后演员评分/出生年份")
line.add("评分", attr, v2, is_stack=True,xaxis_rotate=30,
         xaxis_interval=0,line_color='purple',
         line_width=4,is_splitline_show=False,yaxis_min=5,is_label_show=True)
  
bar = Bar("TOP20 80后演员评分/出生年份")
bar.add("出生年份", attr, v1, is_stack=False,xaxis_rotate=45,is_yaxis_show=False,
         xaxis_interval =0,is_splitline_show=False,yaxis_min=1930,yaxis_max=2080,
         is_label_show=True,bar_col='green')
overlap = Overlap()
# 默认不新增 x y 轴，并且 x y 轴的索引都为 0
overlap.add(line)
overlap.add(bar, yaxis_index=1, is_add_yaxis=True)
overlap.render('TOP20 80后演员评分_出生年份.html')

top_20_90_actor = actor_data[(actor_data['birth_year']>=1990)].sort_values('score',ascending=False)[0:20]
attr = top_20_90_actor['name']
v1=top_20_90_actor['birth_year']
v2=top_20_90_actor['score']
line = Line("TOP20 90后演员评分/出生年份")
line.add("评分", attr, v2, is_stack=True,xaxis_rotate=30,
         xaxis_interval=0,line_color='purple',
         line_width=4,is_splitline_show=False,yaxis_min=4,is_label_show=True)
  
bar = Bar("TOP20 90后演员评分/出生年份")
bar.add("出生年份", attr, v1, is_stack=False,xaxis_rotate=45,is_yaxis_show=False,
         xaxis_interval =0,is_splitline_show=False,yaxis_min=1930,yaxis_max=2080,
         is_label_show=True,bar_col='green')
overlap = Overlap()
overlap.add(line)
overlap.add(bar, yaxis_index=1, is_add_yaxis=True)
overlap.render('TOP20 90后演员评分_出生年份.html')

attr = top_20_actor['name']
v1=top_20_actor['birth_year']
v2=top_20_actor['score']
line = Line("TOP20 80后演员评分/出生年份")
line.add("评分", attr, v2, is_stack=True,xaxis_rotate=30,
         xaxis_interval=0,line_color='purple',
         line_width=4,is_splitline_show=False,yaxis_min=7,is_label_show=True)
  
bar = Bar("TOP20 80后演员评分/出生年份")
bar.add("出生年份", attr, v1, is_stack=False,xaxis_rotate=45,is_yaxis_show=False,
         xaxis_interval =0,is_splitline_show=False,yaxis_min=1930,yaxis_max=2080,
         is_label_show=True,bar_col='green')
overlap = Overlap()
# 默认不新增 x y 轴，并且 x y 轴的索引都为 0
overlap.add(line)
overlap.add(bar, yaxis_index=1, is_add_yaxis=True)
overlap.render('TOP20 80后演员评分_出生年份.html')


bottom_20_fm_actor = actor_data[actor_data['sex']=='女'].sort_values('score')[0:20]
top_20_fm_actor = actor_data[actor_data['sex']=='女'].sort_values('score',ascending=False)[0:20]
attr = bottom_20_fm_actor['name']
v1=bottom_20_fm_actor['birth_year']
v2=bottom_20_fm_actor['score']
line = Line("BOTTOM20女演员评分/出生年份")
line.add("评分", attr, v2, is_stack=True,xaxis_rotate=30,
         xaxis_interval=0,line_color='purple',
         line_width=4,is_splitline_show=False,yaxis_min=1,is_label_show=True)
  
bar = Bar("BOTTOM20女演员评分/出生年份")
bar.add("出生年份", attr, v1, is_stack=False,xaxis_rotate=45,is_yaxis_show=False,
         xaxis_interval =0,is_splitline_show=False,yaxis_min=1930,yaxis_max=2080,
         is_label_show=True,bar_col='green')
overlap = Overlap()
# 默认不新增 x y 轴，并且 x y 轴的索引都为 0
overlap.add(line)
overlap.add(bar, yaxis_index=1, is_add_yaxis=True)
overlap.render('BOTTOM20女演员评分_出生年份.html')



bottom_20_ma_actor = actor_data[actor_data['sex']=='男'].sort_values('score')[0:20]
top_20_ma_actor = actor_data[actor_data['sex']=='男'].sort_values('score',ascending=False)[0:20]
attr = bottom_20_ma_actor['name']
v1=bottom_20_ma_actor['birth_year']
v2=bottom_20_ma_actor['score']
line = Line("BOTTOM20男演员评分/出生年份")
line.add("评分", attr, v2, is_stack=True,xaxis_rotate=30,
         xaxis_interval=0,line_color='purple',
         line_width=4,is_splitline_show=False,yaxis_min=1,is_label_show=True)
  
bar = Bar("BOTTOM20男演员评分/出生年份")
bar.add("出生年份", attr, v1, is_stack=False,xaxis_rotate=45,is_yaxis_show=False,
         xaxis_interval =0,is_splitline_show=False,yaxis_min=1930,yaxis_max=2080,
         is_label_show=True,bar_col='green')
overlap = Overlap()
# 默认不新增 x y 轴，并且 x y 轴的索引都为 0
overlap.add(line)
overlap.add(bar, yaxis_index=1, is_add_yaxis=True)
overlap.render('BOTTOM20男演员评分_出生年份.html')





bottom_20_fm_actor = actor_data[actor_data['sex']=='女'].sort_values('score')[0:20]
top_20_fm_actor = actor_data[actor_data['sex']=='女'].sort_values('score',ascending=False)[0:20]
attr = bottom_20_fm_actor['name']
v1=bottom_20_fm_actor['birth_year']
v2=bottom_20_fm_actor['score']
line = Line("BOTTOM20女演员评分/出生年份")
line.add("评分", attr, v2, is_stack=True,xaxis_rotate=30,
         xaxis_interval=0,line_color='purple',
         line_width=4,is_splitline_show=False,yaxis_min=1,is_label_show=True)
  
bar = Bar("BOTTOM20女演员评分/出生年份")
bar.add("出生年份", attr, v1, is_stack=False,xaxis_rotate=45,is_yaxis_show=False,
         xaxis_interval =0,is_splitline_show=False,yaxis_min=1930,yaxis_max=2080,
         is_label_show=True,bar_col='green')
overlap = Overlap()
# 默认不新增 x y 轴，并且 x y 轴的索引都为 0
overlap.add(line)
overlap.add(bar, yaxis_index=1, is_add_yaxis=True)
overlap.render('BOTTOM20女演员评分_出生年份.html')



bottom_20_ma_actor = actor_data[actor_data['sex']=='男'].sort_values('score')[0:20]
top_20_ma_actor = actor_data[actor_data['sex']=='男'].sort_values('score',ascending=False)[0:20]
attr = top_20_ma_actor['name']
v1=top_20_ma_actor['birth_year']
v2=top_20_ma_actor['score']
line = Line("TOP20男演员评分/出生年份")
line.add("评分", attr, v2, is_stack=True,xaxis_rotate=30,
         xaxis_interval=0,line_color='purple',
         line_width=4,is_splitline_show=False,yaxis_min=7,is_label_show=True)
  
bar = Bar("TOP20男演员评分/出生年份")
bar.add("出生年份", attr, v1, is_stack=False,xaxis_rotate=45,is_yaxis_show=False,
         xaxis_interval =0,is_splitline_show=False,yaxis_min=1930,yaxis_max=2080,
         is_label_show=True,bar_col='green')
overlap = Overlap()

overlap.add(line)
overlap.add(bar, yaxis_index=1, is_add_yaxis=True)
overlap.render('TOP20男演员评分_出生年份.html')


attr = top_20_fm_actor['name']
v1=top_20_fm_actor['birth_year']
v2=top_20_fm_actor['score']
line = Line("TOP20女演员评分/出生年份")
line.add("评分", attr, v2, is_stack=True,xaxis_rotate=30,
         xaxis_interval=0,line_color='purple',
         line_width=4,is_splitline_show=False,yaxis_min=7,is_label_show=True)
  
bar = Bar("TOP20女演员评分/出生年份")
bar.add("出生年份", attr, v1, is_stack=False,xaxis_rotate=45,is_yaxis_show=False,
         xaxis_interval =0,is_splitline_show=False,yaxis_min=1930,yaxis_max=2080,
         is_label_show=True,bar_col='green')
overlap = Overlap()
# 默认不新增 x y 轴，并且 x y 轴的索引都为 0
overlap.add(line)
overlap.add(bar, yaxis_index=1, is_add_yaxis=True)
overlap.render('TOP20女演员评分_出生年份.html')

## 星座分布图
from pyecharts import TreeMap,WordCloud
star_stat = actor_data.groupby('xingzuo').agg({'name':'count'}).reset_index().sort_values('name'
                              ,ascending=False)[0:12].reset_index()



data = [{'value':star_stat['name'][i],
         'name':star_stat['xingzuo'][i]+' '+str(star_stat['name'][i])} for i in range(star_stat.shape[0])]

treemap = TreeMap("星座分布图", width=1200, height=600)
treemap.add("星座分布", data, is_label_show=True, label_pos='inside')
treemap.render('星座分布.html')

## 城市分布图
city_stat = actor_data.groupby('hometown').agg({'name':'count'}).reset_index()
city_stat = city_stat[~city_stat['hometown'].isin(['香港','台湾'])].sort_values('name',ascending=False)[0:30].reset_index()
data = [{'value':city_stat['name'][i],
         'name':city_stat['hometown'][i]+' '+str(city_stat['name'][i])} for i in range(city_stat.shape[0])]

treemap = TreeMap("TOP30城市分布图", width=1500, height=900)
treemap.add("TOP30城市分布", data, is_label_show=True, label_pos='inside')
treemap.render('城市分布.html')

name = actor_data[actor_data['hometown']=='青岛']['name']
value = [1 for k in range(len(name))]
wordcloud = WordCloud(width=1300, height=620)
wordcloud.add("", name, value, word_size_range=[10,40])
wordcloud.render('青岛演员名单.html')


## 各个城市演员词云
name = actor_data[actor_data['hometown']=='北京']['name']
value = [1 for k in range(len(name))]
wordcloud = WordCloud(width=1300, height=620)
wordcloud.add("", name, value, word_size_range=[10,40])
wordcloud.render('北京演员名单.html')

name = actor_data[actor_data['hometown']=='上海']['name']
value = [1 for k in range(len(name))]
wordcloud = WordCloud(width=1300, height=620)
wordcloud.add("", name, value, word_size_range=[10,40])
wordcloud.render('上海演员名单.html')


name = actor_data[actor_data['hometown']=='哈尔滨']['name']
value = [1 for k in range(len(name))]
wordcloud = WordCloud(width=1300, height=620)
wordcloud.add("", name, value, word_size_range=[10,40])
wordcloud.render('哈尔滨演员名单.html')

name = actor_data[actor_data['hometown']=='西安']['name']
value = [1 for k in range(len(name))]
wordcloud = WordCloud(width=1300, height=620)
wordcloud.add("", name, value, word_size_range=[10,40])
wordcloud.render('西安演员名单.html')

name = actor_data[actor_data['hometown']=='天津']['name']
value = [1 for k in range(len(name))]
wordcloud = WordCloud(width=1300, height=620)
wordcloud.add("", name, value, word_size_range=[10,40])
wordcloud.render('天津演员名单.html')




