# Aegis-Fi Backend — Claude Instructions

## Project Overview
FastAPI backend for the Aegis-Fi Autonomous CFO Platform. Handles SaaS spend management, transaction monitoring, AI risk analysis, policy enforcement, and approval workflows.

## Tech Stack
- **Framework**: FastAPI
- **DB**: PostgreSQL via SQLAlchemy (async)
- **AI**: OpenAI API (CFO Agent)
- **Auth**: JWT (Bearer token)
- **Container**: Docker

## Project Structure
```
app/
├── api/v1/endpoints/   # Route handlers (one file per domain)
├── core/               # Config, DB session, security
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic request/response schemas
└── services/           # Business logic layer
main.py                 # App entrypoint
```

## Development Commands
```bash
# Install deps
pip install -r requirements.txt

# Run dev server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Docker
docker build -t aegis-fi-backend .
docker run -p 8000:8000 --env-file .env aegis-fi-backend
```

## API Domains
- `GET /api/v1/dashboard` — spending summary
- `GET/POST /api/v1/saas` — SaaS subscriptions
- `GET/POST /api/v1/transactions` — transactions
- `GET /api/v1/recommendations` — AI recommendations
- `GET/POST /api/v1/policies` — spend policies
- `POST /api/v1/approvals` — approval workflow

## Conventions
- Services own all business logic; endpoints only parse/validate and delegate
- Use async SQLAlchemy sessions (`AsyncSession`) throughout
- Pydantic schemas live in `app/schemas/`, never inline in endpoints
- Environment config via `app/core/config.py` (pydantic-settings); never hardcode secrets
- Keep endpoints thin — no raw SQL, no OpenAI calls directly in route handlers

## 데이터베이스 테이블 구조

### Department (부서)
department_id (PK, INT), department_name (VARCHAR), 
monthly_budget_limit (DECIMAL 15,2), current_spending (DECIMAL 15,2)

### Employee (직원)
employee_id (PK, INT), employee_name (VARCHAR), position (VARCHAR), 
department_id (FK → Department)

### SaaS_Subscription (SaaS 구독)
subscription_id (PK, INT), subscription_name (VARCHAR), provider (VARCHAR),
monthly_fee (DECIMAL 15,2), total_seats (INT), used_seats (INT),
wasted_amount (DECIMAL 15,2), risk_level (VARCHAR: LOW/MEDIUM/HIGH),
renewal_date (DATE), department_id (FK → Department)

### SaaS_Usage (사용 여부)
usage_id (PK, INT), employee_id (FK → Employee), 
subscription_id (FK → SaaS_Subscription), last_login_date (DATE),
monthly_usage_count (INT), is_ghost_account (BOOLEAN)

### Transaction (거래 내역)
transaction_id (PK, INT), employee_id (FK → Employee),
merchant_name (VARCHAR), amount (DECIMAL 15,2), category (VARCHAR),
user_input_reason (VARCHAR), ai_predicted_reason (VARCHAR),
is_approved (BOOLEAN), ai_risk_score (DECIMAL 5,2),
ai_risk_reason (TEXT), payment_time (DATETIME)

### AI_Payment_Policy (결제 정책)
policy_id (PK, INT), employee_id (FK → Employee),
department_id (FK → Department), restricted_category (VARCHAR),
single_payment_limit (DECIMAL 15,2), is_blocked (BOOLEAN)

### Approval_Log (승인 기록)
approval_id (PK, INT), transaction_id (FK → Transaction),
approver_employee_id (FK → Employee), approval_result (BOOLEAN),
approval_reason (VARCHAR), approval_time (DATETIME)

## 비즈니스 규칙
- 결제 요청 시 AI_Payment_Policy에서 해당 직원/부서 정책을 조회하여 판단
- is_ghost_account: last_login_date가 45일 이상 지난 계정 자동 판정
- wasted_amount = monthly_fee × (total_seats - used_seats) / total_seats
- risk_level: wasted_amount/monthly_fee > 30% → HIGH, > 10% → MEDIUM, 나머지 → LOW