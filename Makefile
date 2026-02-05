.PHONY: dev dev-frontend dev-backend install install-frontend install-backend

# Start both frontend and backend concurrently
dev:
	@echo "Starting frontend and backend..."
	@trap 'kill 0' INT TERM; \
	$(MAKE) dev-backend & \
	$(MAKE) dev-frontend & \
	wait

# Start frontend only (Vite dev server on port 5173)
dev-frontend:
	cd frontend && pnpm dev

# Start backend only (FastAPI on port 8000)
dev-backend:
	cd backend && uv run uvicorn main:app --reload

# Install all dependencies
install: install-frontend install-backend

# Install frontend dependencies
install-frontend:
	cd frontend && pnpm install

# Install backend dependencies
install-backend:
	cd backend && uv sync
