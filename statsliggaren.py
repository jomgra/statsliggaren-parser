#!/usr/bin/python3

from bs4 import BeautifulSoup
import requests as req
import sqlite3
import os


f = 'esv.db'  # Databasens namn
url = "https://www.esv.se/statsliggaren/"


def create_connection(db_file):
	conn = None
	try:
		conn = sqlite3.connect(db_file)
	except Error as e:
		print(e)
	
	return conn


def create_table():
	conn = create_connection(f)
	cursor = conn.cursor()
	sql = '''
	CREATE TABLE "esv" (
		"myndighetsid"	INTEGER,
		"myndighetsnamn"	TEXT,
		PRIMARY KEY("myndighetsid")
		)
	'''
	cursor.execute(sql)
	conn.close()

	
def writetodb(sql):
	try:
		conn = create_connection(f)
		cursor = conn.cursor()
		cursor.execute(sql)
		conn.commit()
		conn.close()
		r = True
	except:
		r = False
		
	return r
	
	
def getYears():
	r = []
	t = req.get(url)
	soup = BeautifulSoup(t.text, "html.parser")
	nav = soup.find("nav", {"aria-label": "period"})
	y_link = nav.find_all("a")
	for y in y_link:
		r.append(str(y.text).strip())
		
	return r


def getAuthorities(year):

	r = []
	t = req.get(url + "?PeriodId=" + year)
	soup = BeautifulSoup(t.text, "html.parser")
	nav = soup.find("nav", {"id": "Myndigheter"})
	auth = nav.find_all("a")
	
	for a in auth:
		md = {}
		md["href"] = a["href"]
		md["id"] = int(a["href"][a["href"].find("myndighetId=") + 12: a["href"].find("&")])
		md["name"] = str(a.text).strip()
		r.append(md)
	
	return r


def getRBnode(authId, year):
	
	u = f"{url}SenasteRegleringsbrev/?myndighetId={authId}&periodId={year}"
	t = req.get(u)
	soup = BeautifulSoup(t.text, "html.parser")
	r = soup.find("section", {"id": "letter"})
	
	return r


if not os.path.isfile(f):  # Skapa databas
	create_table()

years = getYears()  # Hämta tillgängliga åt

for year in years:

	sql = f"ALTER TABLE esv ADD '{year}' INTEGER"
	writetodb(sql)  # Skapa kolumn för året

	print(f"\n{year}")
	
	auth = getAuthorities(year)  # Hämta myndigheter

	for a in auth:
		
		print("\n" + "-"*30 + "\n\n" + a["name"])
		
		sql = f"INSERT INTO esv (myndighetsid, myndighetsnamn) VALUES ({a['id']},{a['name']})"
		
		if writetodb(sql):
			print("  Tillagd till databasen")
			
		else:
			print("  Finns redan i databasen")
		
		rb = getRBnode(a["id"], year)  # Hämta regleringsbrev
		
		# Räkna orden i regleringsbrevet
		rbWords = rb.get_text(separator=" ")
		num = len(rbWords.split())
		print(" ", num, "ord")
		
		sql = f"UPDATE esv SET '{year}'={num} WHERE myndighetsid={a['id']}"

		writetodb(sql)  # Lägg till antal ord (eller något annat)
			
