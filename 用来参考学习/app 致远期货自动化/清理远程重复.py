import pymysql
from datetime import datetime

# 远程配置
MYSQL_CONFIG = {
    'host': '115.159.44.226',
    'port': 3306,
    'user': 'qihuo',
    'password': 'Hejdf3KdfaTt4h3w',
    'database': 'qihuo',
    'charset': 'utf8mb4',
    'autocommit': True
}

def clean_duplicate_records():
    print("🚀 开始清理远程重复数据...")
    
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    
    # 假设表有自增id列
    # 第一步：找出所有重复的datetime
    cursor.execute("""
        SELECT datetime, COUNT(*) as count
        FROM hf_HSI_min1
        GROUP BY datetime
        HAVING count > 1
    """)
    duplicates = cursor.fetchall()
    
    if not duplicates:
        print("✅ 没有发现重复记录！")
        conn.close()
        return
    
    print(f"📊 发现 {len(duplicates)} 个重复的分钟")
    
    for dup in duplicates:
        dup_time = dup[0]
        print(f"🔄 处理 {dup_time} ({dup[1]} 条重复)")
        
        # 保留id最大的那条（最新）
        cursor.execute("""
            SELECT MAX(id) FROM hf_HSI_min1 WHERE datetime = %s
        """, (dup_time,))
        max_id = cursor.fetchone()[0]
        
        # 删除其他重复
        cursor.execute("""
            DELETE FROM hf_HSI_min1 
            WHERE datetime = %s AND id != %s
        """, (dup_time, max_id))
    
    conn.commit()
    print("🎉 清理完成！")
    conn.close()

if __name__ == "__main__":
    clean_duplicate_records()
