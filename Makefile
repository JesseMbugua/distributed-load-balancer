build:
	docker network create net1 2>/dev/null || true
	docker build -t server-image:latest ./server
	docker build -t lb-image:latest ./load_balancer

up: build
	docker compose up -d --build

down:
	docker compose down --remove-orphans
	-docker rm -f $$(docker ps -aq --filter "name=Server_") 2>/dev/null || true
	docker network rm net1 2>/dev/null || true

clean: down