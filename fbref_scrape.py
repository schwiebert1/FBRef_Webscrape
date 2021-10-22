import os
import json
import io
import requests
from lxml import etree
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from tqdm import tqdm

def getPlayerInfo(url, path="/Users/turnerschwiebert/Desktop/chromedriver"):
    
    s=Service(path)
    driver = webdriver.Chrome(service=s)
    driver.get(url)
    source_bytes = driver.page_source.encode()
    driver.quit()
    
    obj = io.BytesIO(source_bytes)
    htmltree = etree.parse(obj, parser=etree.HTMLParser())
    htmlroot = htmltree.getroot()
    
    names = htmlroot.xpath("""//*[@id="stats_standard"]/tbody/tr/td[1]/a/text()""")
    clubs = htmlroot.xpath("""//*[@id="stats_standard"]/tbody/tr/td[4]/a/text()""")
    
    player_names = []
    club_list = []
    for i in names:
        player_names.append(i.replace(" ", "-"))
    for i in clubs:
        club_list.append(i)
    assert len(player_names) == len(club_list)

    player_ids = []
    for element in htmlroot.xpath("""//*[@id="stats_standard"]/tbody/tr/td[1]/a"""):
        string = etree.tostring(element).decode()
        ID = string.split("""<a href="/en/players/""")[1][0:8]
        player_ids.append(ID)

    assert len(player_names) == len(player_ids)
    
    league = url.split("stats/")[1][:-6]
    if league.find("-") != -1:
        league = league.replace("-", " ")
    
    IDs = []
    for i in range(len(player_ids)):
        IDs.append((player_names[i], player_ids[i], league, club_list[i]))
        
    return IDs

def getPlayerRoot(info):
    if info[0].find("%") != -1:
        return "Error"
    url = f"https://fbref.com/en/players/{info[1]}/scout/365_euro/{info[0]}-Scouting-Report"
    
    response = requests.get(url)
    
    obj = io.BytesIO(response.content)
    htmltree = etree.parse(obj, parser=etree.HTMLParser())
    htmlroot = htmltree.getroot()
    return htmlroot

def genAge(date, birth):
    date_obj1 = date[0]*365
    date_obj2 = date[1]*30
    date_obj3 = date[2]
    days_current = date_obj1 + date_obj2 + date_obj3
    
    months = {
        'January': 1,
        'February': 2,
        'March': 3,
        'April': 4,
        'May': 5,
        'June': 6,
        'July': 7,
        'August': 8,
        'September': 9,
        'October': 10,
        'November': 11,
        'December': 12
    }
    birth_obj1 = int(birth[0])*365
    birth_obj2 = months[birth[1]]*30
    birth_obj3 = int(birth[2])
    days_at_birth = birth_obj1 + birth_obj2 + birth_obj3
    
    age_days = days_current - days_at_birth
    age = age_days/365

    return age

def PlayerRow(root, info, date):
    
    if root == "Error":
        return "Error"
    
    row={}
    
    rootSTR = etree.tostring(root).decode()
  
    try:
        row['player_id'] = info[1]
        
        name = info[0].replace("-"," ")
        row ['name'] = name
        
        heightSTR = rootSTR.split("""itemprop="height">""")[1]
        row['height_cm'] = int(heightSTR[:heightSTR.find("c")])
        
        weightSTR = rootSTR.split("""itemprop="weight">""")[1]
        row['weight_kg'] = int(weightSTR[:weightSTR.find("k")])
        
        posSTR = rootSTR.split("vs. ")[1][:15]
        row['position'] = posSTR[:posSTR.find("s")]
        
        footSTR = rootSTR.split("""Footed:</strong>""")[1][:20].split("% ")[1]
        row['foot'] = footSTR[:footSTR.find("<")]
        
        club = info[3]
        row['club'] = club
        
        row['league'] = info[2]
        
        countrySTR = rootSTR.split("""National Team:</strong>""")[1].split(">")[1]
        row['country'] = countrySTR[:countrySTR.find("<")]
        
        ageSTR = rootSTR.split("""itemprop="birthDate""")[1].split(">")[1]
        raw_age = ageSTR[:ageSTR.find("<")]
        birth = (raw_age.split(" ")[6][:4], raw_age.split(" ")[4], raw_age.split(" ")[5][:-1])
        age = round(genAge(date, birth), 2)
        row['age'] = age
    except:
        return "Error"
    
    row['PD_Info'] = f"{name} - {age} - {club}"
    
    pos = posSTR[:posSTR.find("s")]
    attrib = ""
    if pos == "Goalkeeper":
        return "Error"
    if pos == "Fullback":
        attrib = "FB"
    if pos == "Center Back":
        attrib = "CB"
    if pos == "Midfielder":
        attrib = "MF"
    if pos == "Forward":
        attrib = "FW"
    if pos == "Att Mid / Wing":
        attrib = "AM"
        
    varibs = root.xpath(f"""//*[@id="scout_full_{attrib}"]/tbody/tr/th/text()""")
    
    remove = [
        "Shooting",
        "Statistic",
        "Passing",
        "Pass Types",
        "Goal and Shot Creation",
        "Defense",
        "Possession",
        "Miscellaneous Stats",
        "Per 90",
        "Percentile"
    ]
    var_list = [i for i in varibs if i not in remove]
    
    vals = root.xpath(f"""//*[@id="scout_full_{attrib}"]/tbody/tr/td[1]/text()""")
    values = []
    for i in vals:
        if i.find("%") != -1:
            values.append(i[:-1])
        else:
            values.append(i)
    
    try:
        assert len(values) == len(var_list)
    except:
        return "Error"
    
    if len(values) == 0:
        return "Error"
    
    tuples = []
    for i in range(len(values)):
        obj = (var_list[i], float(values[i]))
        tuples.append(obj)
    
    for i in tuples:
        row[i[0]] = i[1]
    
    return [row, pos]

def getDate():
    response = requests.get("https://www.calendardate.com/todays.htm")
    date = response.text.split("""<td id="tprg"> """)[5].split("-")
    date_tuple = (int(date[0]), int(date[1]), int(date[2][:4]))
    return date_tuple

def genTables(date,
    url_list = [
    "https://fbref.com/en/comps/9/stats/Premier-League-Stats",
    "https://fbref.com/en/comps/13/stats/Ligue-1-Stats",
    "https://fbref.com/en/comps/20/stats/Bundesliga-Stats",
    "https://fbref.com/en/comps/11/stats/Serie-A-Stats",
    "https://fbref.com/en/comps/12/stats/La-Liga-Stats"], 
    ):
    
    prem_list = getPlayerInfo(url_list[0])
    ligue_list = getPlayerInfo(url_list[1])
    bundes_list = getPlayerInfo(url_list[2])
    serie_list = getPlayerInfo(url_list[3])
    liga_list = getPlayerInfo(url_list[4])
    
    info_list = prem_list + ligue_list + bundes_list + serie_list + liga_list
    
    player_list = []
    found = set()
    for i in info_list:
        if i[1] not in found:
            player_list.append(i)
        found.add(i[1])
    
    FB_LoD = []
    CB_LoD = []
    MF_LoD = []
    FW_LoD = []
    for i in tqdm(player_list):
        result = PlayerRow(getPlayerRoot(i), i, date)
        if result == 'Error':
            pass
        if result[1] == "Fullback":
            FB_LoD.append(result[0])
        if result[1] == "Center Back":
            CB_LoD.append(result[0])
        if result[1] == "Midfielder":
            MF_LoD.append(result[0])
        if result[1] == "Forward" or result[1] == "Att Mid / Wing":
            FW_LoD.append(result[0])
            
    FB_df = pd.DataFrame(FB_LoD)
    CB_df = pd.DataFrame(CB_LoD)
    MF_df = pd.DataFrame(MF_LoD)
    FW_df = pd.DataFrame(FW_LoD)
    
    FB_df.to_csv("/Users/turnerschwiebert/Desktop/GitHub/FBRef_Webscrape/Data/fullbacks.csv")
    CB_df.to_csv("/Users/turnerschwiebert/Desktop/GitHub/FBRef_Webscrape/Data/centerbacks.csv")
    MF_df.to_csv("/Users/turnerschwiebert/Desktop/GitHub/FBRef_Webscrape/Data/midfielders.csv")
    FW_df.to_csv("/Users/turnerschwiebert/Desktop/GitHub/FBRef_Webscrape/Data/forwards.csv")

    FULL_df = pd.concat([FB_df, CB_df, MF_df, FW_df])
    FULL_df.to_csv("/Users/turnerschwiebert/Desktop/GitHub/FBRef_Webscrape/Data/players.csv")

genTables(date = getDate())