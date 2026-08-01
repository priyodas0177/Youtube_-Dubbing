import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="my_ai_project",
    )


# Test connection
# try:
#     conn = get_connection()

#     if conn.is_connected():
#         print("✅ MySQL connected successfully")

#     conn.close()

# except mysql.connector.Error as e:
#     print("❌ MySQL connection failed:", e)

def crate_table():
    conn=get_connection()
    cursor=conn.cursor()

    sql="""
        CREATE TABLE processing_logs (

    id INT AUTO_INCREMENT PRIMARY KEY,

    video_id INT,

    stage VARCHAR(100),

    message TEXT,

    progress INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(video_id)
        REFERENCES videos(id)

);
"""
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Table 'segments' created successfully")
crate_table()