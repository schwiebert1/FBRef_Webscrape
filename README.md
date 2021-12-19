# FBRef_Webscrape
Webscraping FBRef to collect per90 data on all football players in Europe's Top 5 Leagues (Premier League, Bundesliga, Ligue 1, Serie A, La Liga)
I challenged myself to use webscraping techniques as much as possible. 

STATUS: not working :( 

**fbref_srape.py:**
***Functions:***
  - getPlayerInfo: Returns list of player names, club, league, and FBRef player ID by scraping league page (using chrome web driver)
  - getPlayerRoot: Builds player-specific url and returns its parsed html response (root)
  - genAge: returns up-to-date age using birth day and runtime's date (invoked in PlayerRow)
  - PlayerRow: does XPath heavy lifting. Returns list [row, pos] where row is a dict with many variables,values and pos is position
  - getDate: scrapes today's date from https://www.calendardate.com/todays.htm, returns date as tuple
  - genTables: uses pandas to turn rows from PlayerRow into data frames and writes csv files for 
      (1) All positions (players.csv)
      (2) Fullbacks (fullbacks.csv)
      (3) Centerbacks (centerbacks.csv)
      (4) Midfielders (midfielders.csv)
      (5) Forwards (forwards.csv)
    
    

All data collected from: https://fbref.com/en/
