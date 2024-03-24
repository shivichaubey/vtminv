import mysql.connector

conn=mysql.connector.connect(host='localhost',username='root',password='ShiviSia3', database='wtf')
my_cursor=conn.cursor

conn.commit()
conn.close()

print("successful!")