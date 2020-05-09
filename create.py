import duckdb

db = duckdb.connect("presentations_cwi.db")
duck_cursor = db.cursor()

duck_cursor.execute("DROP TABLE IF EXISTS presentations")
duck_cursor.execute("DROP TABLE IF EXISTS scilens_machiens")

duck_cursor.execute("CREATE TABLE IF NOT EXISTS presentations(presentation_date Date NOT NULL UNIQUE, presentation_time TIME NOT NULL, author String, title String NOT NULL, bio String, abtract string, zoom_link String);")
duck_cursor.execute("CREATE TABLE IF NOT EXISTS scilens_machiens(machine_type String);")


duck_cursor.execute("insert into presentations values ('2020-05-04', 'Pedro Holanda', 'Bla bla cracking bla bla', NULL,NULL, 'magic zoom_link');")
