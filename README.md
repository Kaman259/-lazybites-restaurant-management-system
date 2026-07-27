# LazyBites Restaurant Management System

LazyBites is a full-stack restaurant management application for managing dining tables, reservations, customers, menu items, orders, invoices, payments, restaurant settings, dashboard totals, and reports.

The system supports three roles:

- Admin
- Staff
- Customer

## Technology stack

### Frontend

- React
- Vite
- JavaScript
- Tailwind CSS
- React Router
- Axios
- Firebase JavaScript SDK

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- Firebase Admin SDK

### Database

- SQLite for local development
- SQLAlchemy structure prepared for a future PostgreSQL migration

## Main features

### Authentication

- Firebase Email and Password authentication
- Admin login
- Staff login
- Customer registration and login
- Role-based route protection
- Active and inactive account checks

### Admin

- View dashboard totals
- Manage dining tables
- Manage reservations
- Manage menu categories
- Manage menu items
- Manage orders
- Generate invoices
- Record payments
- Process refunds
- Manage customer records
- View reports
- Update restaurant settings

### Staff

- View dashboard totals
- View dining tables
- Manage reservations
- View menu
- Update menu item availability
- Create and manage orders
- Generate invoices
- Record payments
- Manage customer records

Staff cannot access:

- Reports
- Restaurant settings
- Admin-only configuration

### Customer

- Register with Email and Password
- Log in
- Manage profile
- Search tables by date, time, and guest count
- Create table reservations
- View reservation history
- Cancel eligible reservations

## Database tables

The database contains ten main tables:

1. `users`
2. `restaurant_settings`
3. `dining_tables`
4. `customers`
5. `reservations`
6. `menu_categories`
7. `menu_items`
8. `orders`
9. `order_items`
10. `invoices`

## Project structure

```text
LazyBites/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── migrations/
│   ├── tests/
│   ├── uploads/
│   ├── create_admin.py
│   ├── create_staff.py
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── context/
│   │   ├── layouts/
│   │   ├── pages/
│   │   └── routes/
│   └── package.json
├── .gitignore
├── README.md
└── verify-project.ps1