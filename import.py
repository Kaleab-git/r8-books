import os

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import csv


engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def fix_stirng(string):
    new_string = "" 
    for letter in string:
        if letter=="'": new_string += "'" + letter
        else: new_string += letter
    return new_string

with open('books.csv', newline='') as csvfile:
    books = csv.DictReader(csvfile)
    progress = 0
    checkpoint = 1
    for row in books:
        if progress%500==0: print (checkpoint*"######"); checkpoint+=1
        isbn = fix_stirng(row['isbn']); title=fix_stirng(row['title']); author=fix_stirng(row['author']); year=fix_stirng(row['year'])
        db.execute(f"insert into books (isbn,title,author,review_count,average_score,year) values ('{isbn}','{title}','{author}',0,0,'{year}');")
        progress += 1
    db.execute("COMMIT;")


"""
0380795272,Krondor: The Betrayal,Raymond E. Feist,1998
1416949658,The Dark Is Rising,Susan Cooper,1973
1857231082,The Black Unicorn ,Terry Brooks,1987
"""