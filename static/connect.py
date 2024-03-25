import mysql.connector

#conn=mysql.connector.connect(host='localhost',username='root',password='ShiviSia3', database='wtf')
conn = mysql.connector.connect(user="vtmotorsports", password="FormulaSAE123", host="vtmotorsportsinv.mysql.database.azure.com", port=3306, database="vtm", ssl_ca="/home/DigiCertGlobalRootG2.crt.pem", ssl_disabled=False)
# conn = mysql.connector.connect(user="udugeqkkup", password="7QJYY876G6BB8125$", host="vtmotorsportsinv-server.mysql.database.azure.com", port=3306, database="vtmotorsportsinv-database", ssl_ca="/home/DigiCertGlobalRootG2.crt.pem", ssl_disabled=False)
my_cursor=conn.cursor()

# conn.commit()
# conn.close()

print("successful!")