# Aegis-Fi System Architecture

## Overview

Aegis-Fi is a Generative AI-powered Autonomous CFO platform that helps organizations:

- Optimize SaaS subscriptions
- Monitor employee spending
- Enforce financial policies
- Generate AI-powered recommendations
- Improve financial transparency

---

## High-Level Architecture

```text
┌──────────────────────┐
│      Frontend        │
│       Next.js        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      FastAPI         │
│    Backend API       │
└──────────┬───────────┘
           │
 ┌─────────┼─────────┐
 ▼         ▼         ▼

SaaS   Transaction   AI
Service Service     Agent

           │
           ▼

      PostgreSQL

           │
           ▼

      OpenAI API
```

---

## Core Services

### SaaS Service

- SaaS inventory management
- Ghost account detection
- License utilization analysis
- Waste calculation

### Transaction Service

- Expense monitoring
- Spending analysis
- Budget tracking

### Policy Service

- Payment rules
- Category restrictions
- Budget control

### Approval Service

- Approval workflow
- Approval history

### AI Agent Service

- SaaS recommendations
- Risk analysis
- CFO summaries
