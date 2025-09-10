# 🩺 Medical Backend Project (FastAPI)

## 🔮 Planned Features (Future Updates)

- Full test coverage (unit + integration)
- Second database for chat module
- Celery for token cleanup and auto-unban
- Microservices architecture
- Advanced protection against attacks (including DDoS)
- Extended functionality for doctors and patients
- Performance boost with async optimizations
- Additional Redis layers and smarter caching
- Rate limiting, request tracing, and abuse detection

---

## ⏭️ Next Update Preview
  - Token expiration cleanup
- Expand doctor/patient endpoints
- Harden security layers (anti-flood, role abuse prevention)
- Add Redis-based throttling and fallback logic

---

## ⚙️ Core Features (Current)

- **Real-time chat system**:  
  - WebSocket-powered communication  
  - Room-based architecture  
  - Redis for pub/sub and caching  
  - PostgreSQL for persistence  
  📌 Designed for scalability and low-latency messaging

- **JWT tokens**: access, refresh, and email — encrypted with RS256 + AES
- **Token validation**: full lifecycle checks with pollution protection
- **Authentication**: bcrypt, secure cookies, async email verification
- **Role system**: `Admin`, `Patient`, `Doctor` — isolated endpoints and permissions
- **Redis (async)**: smart caching with conditional bypass and fallback to DB
- **ORM**: SQLAlchemy with clean model separation
- **Email dispatching**: fully asynchronous
- **Logging**: structured and layered
- **Docker**: ready for containerized deployment
- **Nginx**: reverse proxy setup

---

## 🧠 Role Breakdown

- **Admin**
  - Create/delete users
  - Ban/unban (with reason and duration)
  - View full user info

- **Patient**
  - Submit requests
  - Rate doctors
  - View sorted doctor lists

- **Doctor**
  - Accept requests
  - Diagnose patients
  - View incoming requests

🔐 Role logic enforced via `Role_checker` in `core/app_logic/rights_check.py`

---

## 🧩 Shared Endpoints

- Get user by role (for frontend rendering)
- Average rating calculation
- `joinload` optimization for related entities

---

## 🧬 Redis Logic

- If Redis has entry → compare → return  
- If not → query DB → fill Redis → return  
- If mismatch → raise error  
📌 Designed for minimal pollution and fast access.

---

## 🧾 Tech Stack

| Layer        | Tool / Library            |
|--------------|---------------------------|
| Backend      | FastAPI (async)           |
| Auth         | JWT (RS256 + AES), bcrypt |
| DB           | PostgreSQL + SQLAlchemy   |
| Cache        | Redis (async)             |
| Mail         | Async SMTP                |
| Realtime     | WebSocket + Redis         |
| Container    | Docker                    |
| Proxy        | Nginx                     |

---

## 📣 Final Notes

This project is evolving fast. Every update brings more performance, security, and features.  
If you're curious — clone it, run it, and explore the logic.  
Next update will be even bigger.
