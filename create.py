import duckdb

db = duckdb.connect("presentations_cwi.db")
duck_cursor = db.cursor()

# be sure to not delete your little database
duck_cursor.execute("DROP TABLE IF EXISTS presentations;")
duck_cursor.execute("DROP TABLE IF EXISTS members;")

duck_cursor.execute("CREATE TABLE IF NOT EXISTS presentations(presentation_date Date NOT NULL UNIQUE, "
                    "presentation_time TIME, author String, title String , bio String, "
                    "abstract string, zoom_link String);")

duck_cursor.execute("CREATE TABLE IF NOT EXISTS members(name String NOT NULL UNIQUE, last_madam DATE NOT NULL, "
                    "last_fatal Date NOT NULL);")


duck_cursor.execute("insert into presentations values ('2020-05-04','13:00:00', 'Pedro Holanda', 'Bla bla cracking bla "
                    "bla', NULL,NULL, 'magic zoom_link');")

a = duck_cursor.execute("select * from presentations;").fetchall()
duck_cursor.execute("insert into members values ('Hannes Mühleisen', '2020-01-20' ,'2019-01-01');")
duck_cursor.execute("insert into members values ('Tim Gubner', '2020-01-27' ,'2020-03-09');")
duck_cursor.execute("insert into members values ('Nantia Makrynioti', '2020-05-11', '2020-03-27');")
duck_cursor.execute("insert into members values ('Peter Boncz', '2020-03-20', '2020-04-10');")
duck_cursor.execute("insert into members values ('Long Tran', '2019-01-01','2019-01-01');")
duck_cursor.execute("insert into members values ('Pedro Holanda', '2020-04-28', '2020-03-23');")
duck_cursor.execute("insert into members values ('Iulian Birlica', '2019-01-01', '2019-01-01');")
duck_cursor.execute("insert into members values ('Mark Raasveldt', '2020-04-06' ,'2020-01-09');")
duck_cursor.execute("insert into members values ('Benno Kruit', '2019-01-01', '2020-02-07');")
duck_cursor.execute("insert into members values ('Matheus Nerone', '2020-04-20', '2020-02-24');")
duck_cursor.execute("insert into members values ('Stefan Manegold', '2019-01-01', '2020-03-02');")
duck_cursor.execute("insert into members values ('Martin Kersten', '2019-01-01' ,'2019-01-01');")
duck_cursor.execute("insert into members values ('Sam Anmink', '2019-01-01' ,'2019-01-01');")
duck_cursor.execute("insert into members values ('Azim', '2019-01-01', '2019-01-01');")
duck_cursor.execute("insert into members values ('Diego Tome', '2020-03-30' ,'2020-05-15');")
duck_cursor.execute("insert into members values ('Dean De Leo', '2019-01-01', '2020-04-03');")
