.PHONY: install-backend install-frontend dev-backend dev-backend seed run-all clean

# 安装后端依赖
install-backend:
	cd backend && pip install -r requirements.txt

# 安装前端依赖
install-frontend:
	cd frontend && npm install

# 启动后端开发服务器
dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

# 启动前端开发服务器
dev-frontend:
	cd frontend && npm run dev

# 生成种子数据
seed:
	cd backend && python app/seed_data.py

# 同时启动前后端
run-all:
	@echo "启动后端..."
	cd backend && uvicorn app.main:app --port 8000 &
	@echo "启动前端..."
	cd frontend && npm run dev

# 清理数据库
clean:
	rm -f backend/coal_transport.db
