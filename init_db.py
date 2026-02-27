import sqlite3
import os

def init_db():
    
    db_path = os.path.join('data', 'database.db')
    
 
    connection = sqlite3.connect(db_path)
   
    with open('schema.sql') as f:
        connection.executescript(f.read())
    
    
    with open('app/seed.sql') as f:
        connection.executescript(f.read())
    
    connection.commit()
    connection.close()
    print("Дерекқор сәтті құрылды және мәліметтер енгізілді!")

if __name__ == '__main__':
    init_db()