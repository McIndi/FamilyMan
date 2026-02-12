
# FamilyMan Project

**FamilyMan** is a fully featured Django-based family management platform. It helps families organize their lives with collaborative tools for events, shopping, communication, child rewards, and finances—all in one place.

## Features

### 🗓️ Calendar App
- Create, update, and delete events for the whole family
- Day, week, and month views
- Recurring events with customizable intervals
- Invite family members as attendees

### 🛒 Shopping List App
- Add, update, and delete shopping list items
- Categorize items as "Need" or "Want"
- Mark items as obtained
- Track current and past items

### ⭐ Merits & Demerits (Child Rewards)
- Parents can award **merits** (positive points) and **demerits** (negative points) to children
- Track each child’s score and history
- Dashboard view for all children in the family
- Customizable descriptions and weights for each merit/demerit

### ✉️ Messaging (Mail)
- Send messages to one or more family members
- Inbox, message detail, reply, edit, and delete
- Mark messages as read
- Pagination for large inboxes

### 💵 Cash (Income & Expense Tracking)
- Add funds (e.g., payday) and record expenses
- Categorize expenses (with per-family categories)
- Attach receipt photos to expenses
- View and search transactions by week, month, or year
- See running family cash total
- Edit or delete funds and expenses if needed

### 👨‍👩‍👧‍👦 Family Management
- Support for multiple families per user
- Switch between families
- Assign parent/child roles
- Family dashboard overview

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```bash
   cd familyman
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Apply migrations:
   ```bash
   python manage.py migrate
   ```
5. Copy the example environment file and set your own secret key:
   ```bash
   cp .env.example .env
   # Edit .env to set your SECRET_KEY and other settings
   ```
6. Create a superuser to access the admin interface:
   ```bash
   python manage.py createsuperuser
   ```
7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

- Access the calendar at `/calendar/`
- Access the shopping list at `/shoppinglist/`
- Access the merits dashboard at `/merits/dashboard/`
- Access the inbox at `/mail/inbox/`
- Access cash tracking at `/cash/transactions/`

## API Endpoints

### Calendar
- `POST /calendar/create/` — Create event
- `POST /calendar/<int:pk>/update/` — Update event
- `POST /calendar/<int:pk>/delete/` — Delete event
- `GET /calendar/day/<int:year>/<int:month>/<int:day>/` — Day view
- `GET /calendar/week/<int:year>/<int:month>/<int:day>/` — Week view
- `GET /calendar/month/<int:year>/<int:month>/` — Month view

### Shopping List
- `POST /shoppinglist/create/` — Create item
- `POST /shoppinglist/<int:pk>/update/` — Update item
- `POST /shoppinglist/<int:pk>/delete/` — Delete item
- `GET /shoppinglist/items/` — List items
- `GET /shoppinglist/past-items/` — Past items

### Merits/Demerits
- `GET /merits/dashboard/` — View merit dashboard
- `POST /merits/add_merit/` — Add merit
- `POST /merits/add_demerit/` — Add demerit

### Messaging
- `GET /mail/inbox/` — View inbox
- `GET /mail/message/<int:pk>/` — View message
- `GET/POST /mail/compose/` — Compose message
- `POST /mail/message/<int:pk>/delete/` — Delete message
- `POST /mail/message/<int:pk>/edit/` — Edit message
- `POST /mail/message/<int:pk>/reply/` — Reply to message

### Cash
- `GET /cash/transactions/` — View/search transactions
- `POST /cash/add_fund/` — Add funds
- `POST /cash/add_expense/` — Add expense
- `POST /cash/expense/<int:expense_id>/edit/` — Edit expense
- `POST /cash/expense/<int:expense_id>/delete/` — Delete expense
- `POST /cash/fund/<int:fund_id>/edit/` — Edit fund
- `POST /cash/fund/<int:fund_id>/delete/` — Delete fund

## Contributing

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes and push to your branch.
4. Submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.