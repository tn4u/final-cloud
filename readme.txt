# Final Cloud

Final Cloud là project mô phỏng hệ thống cloud mini gồm 9 server chính, triển khai bằng Docker Compose.

## Thành phần hệ thống
- Web Frontend Server
- Application Backend Server
- Relational Database Server
- Authentication Identity Server
- Object Storage Server
- Internal DNS Server
- Monitoring Node Exporter
- Monitoring Prometheus Server
- Monitoring Grafana Dashboard Server
- API Gateway / Reverse Proxy

## Công nghệ sử dụng
- Docker
- Docker Compose
- Nginx
- Flask
- MariaDB
- Keycloak
- MinIO
- Bind9
- Prometheus
- Grafana

## Cách chạy project
```bash
docker compose build --no-cache
docker compose up -d
docker compose ps
Port sử dụng
Web: 8080
App: 8085
Auth: 8081
MinIO: 9000 / 9001
DNS: 1053/udp
Prometheus: 9090
Grafana: 3000
Proxy: 80
Thành viên
Thành viên 1: Web, App, DB, Proxy
Thành viên 2: Auth, Storage, DNS, Monitoring, EC2
