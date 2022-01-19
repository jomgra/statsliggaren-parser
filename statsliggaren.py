#!/usr/bin/python3

from bs4 import BeautifulSoup
import requests as req
import sqlite3
import os

f = 'esv.db' # Databasens namn


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


# Skapa databas om den inte finns
if not os.path.isfile(f):
	create_table()

# Läs in statsliggaren
url = "https://www.esv.se"
r = req.get(url + "/statsliggaren/")
soup = BeautifulSoup(r.text, "html.parser")

# Hitta företeckningen över årtal
nav = soup.find("nav", {"aria-label": "period"})
years = nav.find_all("a")

# Gå igenom varje år
for y in years:
	year = str(y.text).strip()
	
	# Ladda in statsliggseren för resp år
	r = req.get(url + "/statsliggaren/?PeriodId=" + year)
	soup = BeautifulSoup(r.text, "html.parser")

	try:  # Lägg till kolumn för året
		conn = create_connection(f)
		cursor = conn.cursor()
		sql = f"ALTER TABLE esv ADD '{year}' INTEGER"
		cursor.execute(sql)
		conn.commit()
		conn.close()
	except:
		pass

	print(f"\n{year}")

	# Hitta förtecknkngen över myndigheter
	nav = soup.find("nav", {"id": "Myndigheter"})
	myndigheter = nav.find_all("a")

	# Gå igenom alla myndigheter
	for m in myndigheter:
		mdata = []
		mdata.append(int(m["href"][m["href"].find("myndighetId=") + 12: m["href"].find("&")]))  # MyndighetsID
		mdata.append(str(m.text).strip())  # Myndighetsnamn
		
		print("\n" + "-"*30 + "\n\n" + mdata[1])
		
		try:  # Lägg till myndigheten
			conn = create_connection(f)
			cursor = conn.cursor()
			sql = "INSERT INTO esv (myndighetsid, myndighetsnamn) VALUES (?,?)"
			cursor.execute(sql, mdata)
			conn.commit()
			conn.close()
			print("  Tillagd till databasen")
		except:
			print("  Finns redan i databasen")
		
		# Ladda in regleringsbrevet
		r = req.get(url + m["href"])
		soup = BeautifulSoup(r.text, "html.parser")
		rb = soup.find("section", {"id": "letter"})
		
		# Räkna orden i regleringsbrevet
		rbWords = rb.get_text(separator=" ")
		num = len(rbWords.split())
		print(" ", num, "ord")
			
		try:  # Lägg till antal ord (eller något annat)
			conn = create_connection(f)
			cursor = conn.cursor()
			sql = f"UPDATE esv SET '{year}'={num} WHERE myndighetsid={mdata[0]}"
			cursor.execute(sql)
			conn.commit()
			conn.close()
		except:
			pass
