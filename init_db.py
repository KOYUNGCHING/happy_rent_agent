from database import init_db, seed_sample_data

# 初始化資料庫腳本
if __name__ == "__main__":
    init_db()
    seed_sample_data()
    print("Database initialized successfully!")