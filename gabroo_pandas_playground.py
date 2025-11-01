import pandas as pd
import numpy as np



link = "gabroo_videos_full.csv"
df = pd.read_csv(link)


df["title"] = df["title"].str.lower().str.strip()

mask_first = df["title"].str.contains("first place", case=False, na=False) 
mask_second = df["title"].str.contains("second place", case=False, na=False)
mask_third = df["title"].str.contains("third place", case=False, na=False)

## np.select(condlist, choicelist, default=0)
df["placings"] = np.select(condlist=[mask_first,mask_second,mask_third], choicelist=["1", "2", "3"],default="None")


# Clean up YT duration using Regex


# Case 1: Seconds only (PT47S → 47)
df.loc[df["duration"].str.contains(r"^PT\d+S$", regex=True, na=False), "duration"] = (
    df["duration"].str.replace(r"PT(\d+)S", r"\1", regex=True)
)

# Case 2: Minutes + Seconds (PT8M47S → 527, PT5M30S → 330)
mask = df["duration"].str.contains(r"^PT\d+M\d+S$", regex=True, na=False)
df.loc[mask, "duration"] = (
    df.loc[mask, "duration"]
      .str.extract(r"PT(\d+)M(\d+)S")     # get minutes + seconds
      .fillna(0)                          # replace NaN with 0
      .astype(int)                        # convert to ints
      .apply(lambda x: x[0] * 60 + x[1], axis=1)  # compute total seconds
)

# Case 3: Minutes only (PT2M → 120)
df.loc[df["duration"].str.contains(r"^PT\d+M$", regex=True, na=False), "duration"] = (
    df["duration"].str.replace(
        r"PT(\d+)M",
        lambda m: str(int(m.group(1)) * 60),
        regex=True
    )
)

# Case 4: Hours + Minutes + Seconds (PT1H2M3S)
mask = df["duration"].str.contains(r"^PT\d+H\d+M\d+S$", regex=True, na=False)
df.loc[mask, "duration"] = (
    df.loc[mask, "duration"]
      .str.extract(r"PT(\d+)H(\d+)M(\d+)S")
      .fillna(0)
      .astype(int)
      .apply(lambda x: x[0]*3600 + x[1]*60 + x[2], axis=1)
)

# Case 5: Hours + Minutes (PT3H50M)
mask = df["duration"].str.contains(r"^PT\d+H\d+M$", regex=True, na=False)
df.loc[mask, "duration"] = (
    df.loc[mask, "duration"]
      .str.extract(r"PT(\d+)H(\d+)M")
      .fillna(0)
      .astype(int)
      .apply(lambda x: x[0]*3600 + x[1]*60, axis=1)
)

# Case 6: Hours only (PT2H)
mask = df["duration"].str.contains(r"^PT\d+H$", regex=True, na=False)
df.loc[mask, "duration"] = (
    df.loc[mask, "duration"]
      .str.replace(r"PT(\d+)H", lambda m: str(int(m.group(1))*3600), regex=True)
)

df["duration"] = df["duration"].astype(int) ## convert everything to integers

## Filter out exhibition performances
delete_exh_title = df["title"].str.contains("exhibition", case=False, na=False)
delete_exh_description = df["description"].str.contains("Exhibition", case=False, na=False)
delete_giddha = df["title"].str.contains("giddha", case=False, na=False)

delete_exh = delete_exh_title | delete_exh_description | delete_giddha ## Use | instead of 'or'
df = df[~delete_exh]

## Filter videos with during <120 seconds
delete_sec = df["duration"] > 120
df = df[delete_sec]


## Extract Competition Names 
def get_competition_name(title):
    if " at " in title:
        return title.split(" at " , 1)[1].strip() ## maxsplit = 1
    elif " @ " in title:
        return title.split("@" , 1)[1].strip()
    elif "-" in title:
        return title.split("-" , 1)[1].strip()
    else:
        return None


df["competition_name"] = df["title"].apply(get_competition_name)
df["competition_name"] = df["competition_name"].str.replace(r"(\b\d{4}\b)", "", regex=True).str.strip()


## Extract Team Names
def get_team_name(title):
    idx_at = title.find(" at ") if " at " in title else float("inf")
    idx_dash = title.find("-") if "-" in title else float("inf")
    idx_at_symbol = title.find(" @ ") if " @ " in title else float("inf")
    
    # find which delimiter appears first
    first_idx = min(idx_at, idx_dash, idx_at_symbol)

    if first_idx == float("inf"):
        return None  # no delimiter found
    
    return title[:first_idx].strip()

df["team_name"] = df["title"].apply(get_team_name)


# check for blanks in comp name
blank = df["competition_name"] == ""
nas = df["competition_name"].isna()
maskit = blank | nas 
df = df[~maskit]



# Year Competition
df["comp_year"] = df["title"].str.extract(r"(\b\d{4}\b)") 

## Manual Fixes for comp_year
df.loc[df["video_id"] == "snYwCBWewY4", "comp_year"] = "2014" ## Burgh Video
df.loc[df["video_id"] == "k_HlF40BjtA", "comp_year"] = "2024" ## GTV spelling error
df.loc[df["video_id"] == "mMiiWLM7bZ4", "comp_year"] = "2016" ## Bhangra Blowout 23
df.loc[df["title"].str.contains("bhangra fever 4") , "comp_year"] = "2013" ## Bhangra Fever 4
df.loc[df["title"].str.contains("bhangra fever 5") , "comp_year"] = "2014" ## Bhangra Fever 5
df.loc[df["title"].str.contains("bhangra fever 6") , "comp_year"] = "2015" ## Bhangra Fever 6
df.loc[df["title"].str.contains("dhol di awaz 13") , "comp_year"] = "2010" ## Dhol Di Awaz


# Double-check for videos under 400 seconds
df = df[df["video_id"] != "a2zdadcBDUw"] # random vid
df = df[df["video_id"] != "QtXtpBeRPGg"] # award ceremony
df = df[df["video_id"] != "MQf2NjkXc8s"] # SPD Exhibition
df = df[df["video_id"] != "qscV-WWHMtY"] # Random Danceoff

# DCMA's exhibitions
df = df[df["video_id"] != "5fOWygmy4d8"] 
df = df[df["video_id"] != "m87S7RNlLTI"]
df = df[df["video_id"] != "WfbZhgy8bzk"] 
df = df[df["video_id"] != "TRSSikm32ng"] 
df = df[df["video_id"] != "4uBj882moJA"] 
df = df[df["video_id"] != "vtoi7234V1c"]
df = df[df["video_id"] != "PfvbSKFtDTE"] 
df = df[df["video_id"] != "a07QZuChn6c"] 


df = df[df["video_id"] != "Ft187itSZro"] 


df = df[df["video_id"] != "3rHRENS_Kpk"] # random vid
df = df[df["video_id"] != "pU8SjN2U6_o"] # mixer games
df = df[df["video_id"] != "DdD1nT60rOw"] # random vid
df = df[df["video_id"] != "4aMLteI9jAk"] # random vid
df = df[df["video_id"] != "3sZJ7iul6fM"] # random vid
df = df[df["video_id"] != "O4vLMYDt9x4"] # random vid
df = df[df["video_id"] != "-517TVVq7VU"] # random vid
df = df[df["video_id"] != "i3SnSzANYXI"] # random vid
df = df[df["video_id"] != "QxlWwyDq9b8"] # random vid
df = df[df["video_id"] != "Da1bgoUBpck"] # random vid
df = df[df["video_id"] != "YLHdYt0Dsmo"] # behind the scenes
df = df[df["video_id"] != "nlygqWsE3Q0"] # random vid
df = df[df["video_id"] != "DzxmqV3yrXs"] # random vid
df = df[df["video_id"] != "2KadPrj1BMY"] # random vid
df = df[df["video_id"] != "DlrTz9_8cDQ"] # random vid
df = df[df["video_id"] != "ymNt9iwa-Xk"] # random vid
df = df[df["video_id"] != "4NHpbgxpAHQ"] # random vid
df = df[df["video_id"] != "XJC4QMl7ZhI"] # random vid
df = df[df["video_id"] != "ZbPStFC0Fv8"] # random vid
df = df[df["video_id"] != "cno0aQLLJGk"] # random vid
df = df[df["video_id"] != "wTrExK0IxLU"] # random vid
df = df[df["video_id"] != "D98-KEiPA_Q"] # random vid
df = df[df["video_id"] != "QEgMSMHsuPM"] # random vid
df = df[df["video_id"] != "rPfY_FxRVxg"] # random vid
df = df[df["video_id"] != "pAh6aXpVlKs"] # random vid
df = df[df["video_id"] != "eyzpPuLr-hg"] # random vid
df = df[df["video_id"] != "0M8tLMSlgNc"] # random vid
df = df[df["video_id"] != "CO4XWwGq8Yk"] # random vid
df = df[df["video_id"] != "bKtQDphMaLE"] # random vid
df = df[df["video_id"] != "bKtQDphMaLE"] # random vid
df = df[df["video_id"] != "HGyfMqNLFk0"] # random vid

# check for blanks in comp year
blank = df["comp_year"] == ""
nas = df["comp_year"].isna()
maskitt = blank | nas 
df = df[~maskitt]


# Restrict to post 2008 data
discard2006 = df["comp_year"].str.contains("2006")
discard2007 = df["comp_year"].str.contains("2007")
discard2008 = df["comp_year"].str.contains("2008")
discard2009 = df["comp_year"].str.contains("2009")

discardboth = discard2006 | discard2007 | discard2008 | discard2009
df = df[~discardboth]



# Ensure consistent naming conventions for competitions
df.loc[df["competition_name"].str.contains("burgh"), "competition_name"] = "bhangra at the burgh"
df.loc[df["competition_name"].str.contains("bruin"), "competition_name"] = "bruin bhangra"
df.loc[df["competition_name"].str.contains("richmond"), "competition_name"] = "richmond mela"
df.loc[df["competition_name"].str.contains("cup"), "competition_name"] = "6ix city bhangra"
df.loc[df["competition_name"].str.contains("back to the"), "competition_name"] = "back to the roots"
df.loc[df["competition_name"].str.contains("dhamak"), "competition_name"] = "dhamak bhangra"
df.loc[df["competition_name"].str.contains("fever"), "competition_name"] = "bhangra fever"
df.loc[df["competition_name"].str.contains("alamo"), "competition_name"] = "bhangra at the alamo"
df.loc[df["competition_name"].str.contains("city"), "competition_name"] = "bhangra city"
df.loc[df["competition_name"].str.contains("blowout"), "competition_name"] = "bhangra blowout"
df.loc[df["competition_name"].str.contains("arena"), "competition_name"] = "bhangra arena"
df.loc[df["competition_name"].str.contains("pioneer"), "competition_name"] = "pioneer bhangra"
df.loc[df["competition_name"].str.contains("warrior"), "competition_name"] = "warrior bhangra"
df.loc[df["competition_name"].str.contains("dcmpaa"), "competition_name"] = "dcmpaa competition"
df.loc[df["competition_name"].str.contains("tor punjaban"), "competition_name"] = "tor punjaban"
df.loc[df["competition_name"].str.contains("dhol di"), "competition_name"] = "dhol di awaz"
df.loc[df["competition_name"].str.contains("elite"), "competition_name"] = "elite 8"
df.loc[df["competition_name"].str.contains("best in the"), "competition_name"] = "bhangra idols"
df.loc[df["competition_name"].str.contains("best of the"), "competition_name"] = "bhangra idols"
df.loc[df["competition_name"].str.contains("idols"), "competition_name"] = "bhangra idols"
df.loc[df["competition_name"].str.contains("bell"), "competition_name"] = "bhangra at the bell"
df.loc[df["competition_name"].str.contains("santa"), "competition_name"] = "uc santa barbara's nachle deewane"
df.loc[df["competition_name"].str.contains("notorious"), "competition_name"] = "notorious bhangra"


# Ensure consistent naming conventions for teams
df.loc[df["team_name"].str.contains("kohinoor"), "team_name"] = "kohinoor bhangra"
df.loc[df["team_name"].str.contains("got bhangra"), "team_name"] = "got bhangra"
df.loc[df["team_name"].str.contains("apna bhangra"), "team_name"] = "apna bhangra crew"
df.loc[df["team_name"].str.contains("shan e"), "team_name"] = "shan e punjab"
df.loc[df["team_name"].str.contains("punjab arts club"), "team_name"] = "punjab arts club"
df.loc[df["team_name"].str.contains("nachdi jawani"), "team_name"] = "nachdi jawani"
df.loc[df["team_name"].str.contains("royal academy"), "team_name"] = "royal academy "
df.loc[df["team_name"].str.contains("mission"), "team_name"] = "mission punj-aab culture club "
df.loc[df["team_name"].str.contains("folk stars"), "team_name"] = "folk stars "
df.loc[df["team_name"].str.contains("punjabi heritage"), "team_name"] = "phf edmenton"
df.loc[df["team_name"].str.contains("phf"), "team_name"] = "phf edmenton"
df.loc[df["team_name"].str.contains("rvd"), "team_name"] = "rvd joshiley"
df.loc[df["team_name"].str.contains("raakhe"), "team_name"] = "rvd joshiley"
df.loc[df["team_name"].str.contains("nachde punjabi"), "team_name"] = "nachde punjabi"
df.loc[df["team_name"].str.contains("furteelay"), "team_name"] = "furteelay"
df.loc[df["team_name"].str.contains("bu bhangra"), "team_name"] = "bull bhangra"
df.loc[df["team_name"].str.contains("bhams blazin", case=False), "team_name"] = "bhams blazin bhangra"
df.loc[df["team_name"].str.contains("bhams blazin"), "team_name"] = "bhams blazin bhangra"
df.loc[df["team_name"].str.contains("anakh"), "team_name"] = "anakh e gabroo"
df.loc[df["team_name"].str.contains("rangla punjab arts academy"), "team_name"] = "rangla punjab arts academy"
df.loc[df["team_name"].str.contains("royal bhangra"), "team_name"] = "royal bhangra"
df.loc[df["team_name"].str.contains("virsa.*tradition"), "team_name"] = "virsa our tradition"
df.loc[df["team_name"].str.contains("nachda punjab bhangra academy"), "team_name"] = "nachda punjab bhangra academy"
df.loc[df["team_name"].str.contains("dc metro punjabi arts academy"), "team_name"] = "dc metro punjabi arts academy"
df.loc[df["team_name"].str.contains("dcmpaa"), "team_name"] = "dc metro punjabi arts academy"
df.loc[df["team_name"].str.contains("bhangra knight"), "team_name"] = "bhangra knightz"
df.loc[df["team_name"].str.contains("cornell bhangra"), "team_name"] = "cornell bhangra"
df.loc[df["team_name"].str.contains("michigan bhangra team"), "team_name"] = "michigan bhangra team"
df.loc[df["team_name"].str.contains("the michigan bhangra team"), "team_name"] = "michigan bhangra team"
df.loc[df["team_name"].str.contains("maryland bhangra"), "team_name"] = "maryland bhangra"
df.loc[df["team_name"].str.contains("umd"), "team_name"] = "maryland bhangra"
df.loc[df["team_name"].str.contains("wash u bhangra"), "team_name"] = "wash u bhangra"
df.loc[df["team_name"].str.contains("washu bhangra"), "team_name"] = "wash u bhangra"
df.loc[df["team_name"].str.contains("uva"), "team_name"] = "uva bhangra"
df.loc[df["team_name"].str.contains("virginia school of bhangra"), "team_name"] = "virginia school of bhangra"
df.loc[df["team_name"].str.contains("royal folk nation"), "team_name"] = "royal folk nation"
df.loc[df["team_name"].str.contains("sada virsa sada gaurav"), "team_name"] = "sada virsa sada gaurav"
df.loc[df["team_name"].str.contains("apna virsa academy"), "team_name"] = "apna virsa academy"
df.loc[df["team_name"].str.contains("punjab folk academy"), "team_name"] = "punjab folk academy"
df.loc[df["team_name"].str.contains("duniya allstar"), "team_name"] = "duniya allstars"
df.loc[df["team_name"].str.contains("vsb"), "team_name"] = "virgina school of bhangra"
df.loc[df["team_name"].str.contains("virginia school"), "team_name"] = "virgina school of bhangra"
df.loc[df["team_name"].str.contains("naach di clevelend"), "team_name"] = "naach di cleveland"
df.loc[df["team_name"].str.contains("naach di cleveland"), "team_name"] = "naach di cleveland"
df.loc[df["competition_name"].str.contains("naach di clevelend"), "competition_name"] = "naach di cleveland"
df.loc[df["competition_name"].str.contains("naach di cleveland"), "competition_name"] = "naach di cleveland"

# drop tags
mask = df["title"].str.contains("bhangra idols 10th anniversary | musical | banquet | skit | singh")
df = df[~mask]


# drop musical chairs + mixers
mixers = df["title"].str.contains("mixer")
musicalchairs = df["title"].str.contains("musical")
df = df[~mixers]
df = df[~musicalchairs]




## Extract all unique list of teams 

# 1. Total comps per team (denominator)
df["total_comps"] = df.groupby("team_name")["team_name"].transform("count")

# 2. Placing score (numerator weight)
def comp_score(x):
    if x == "1":
        return 1
    if x == "2":
        return 0.75
    if x == "3":
        return 0.50
    else:
        return 0.10

df["placing_score"] = df["placings"].apply(comp_score)


team_scores = df.groupby("team_name")["placing_score"].sum()
df["sum_placing_score"] = df["team_name"].map(team_scores)
df["finalscore"] = df["sum_placing_score"] / df["total_comps"]


# 1. # of teams in a competition
df["number_of_teams_in_comp"] = df.groupby("competition_name")["team_name"].transform("count")



# Get the sums of hte teams for the comps 
sumforcomps = df.groupby("competition_name")["finalscore"].sum()
df["comp_numerator"] = df["competition_name"].map(sumforcomps)
df["comp_score"] = df["comp_numerator"] / df["number_of_teams_in_comp"]
df["team_score"] = df["avg_score"] * np.log1p(df["total_comps"])


df = df.sort_values("comp_score", ascending=False)





print(df["placings"].info())




df.to_csv("filtered_GTVVideos.csv", index=False)


