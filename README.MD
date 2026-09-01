# ICS 4104: Customizable Distributed Load Balancer

## Overview
A containerized distributed load balancer implementing consistent hashing with virtual nodes ($K = \log_2(512) = 9$) and linear probing collision resolution deployed within an isolated Docker network (`net1`).

---

## System Architecture & Endpoints
- `GET /home`: Proxies the request clockwise across the ring to an active backend replica.
- `GET /rep`: Returns current replica count ($N$) and hostname listing.
- `POST /add`: Dynamically provisions $n$ new container replicas and assigns them to the ring.
- `DELETE /rm`: Removes $n$ container replicas from the ring and deletes their containers.
- `GET /heartbeat`: Internal health check invoked by the failure detector every 500ms.

---

## Analysis & Benchmarking (Task 4)

### A-1: Request Distribution ($N = 3$)
- **Requests**: 10,000 asynchronous HTTP calls.
- **Result Plot**: `analysis/a1_distribution.png`
- **Observation**: Requests map clockwise to the nearest virtual server slot. Due to polynomial quadratic residue distributions, slots cluster around certain segments of the 512-slot ring.

### A-2: Scalability ($N = 2$ to $N = 6$)
- **Result Plot**: `analysis/a2_scalability.png`
- **Observation**: Average request load decreases inversely proportional to $N$ ($Load = \frac{10000}{N}$), confirming horizontal scalability.

### A-3: Fault Recovery
- Terminating a server container triggers the background heartbeat detector within 500ms, removing the failed instance and spawning a replacement container seamlessly.

### A-4: Hash Function Comparison
- Replacing $H(i) = i^2 + 2i + 17$ and $\Phi(i, j) = i^2 + j^2 + 2j + 25$ with a multiplicative distribution significantly reduces clustering and produces uniform load balance across replicas.

---

## Deployment
```bash
make build
make up
make clean