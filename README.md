# FamilyMan Project

FamilyMan is a Django-based project that includes a calendar application and a shopping list application. It helps users manage their events and shopping needs efficiently.

## Features

### Calendar App
- Create, update, and delete events.
- View events in day, week, and month views.
- Recurring events with customizable intervals.

### Shopping List App
- Add, update, and delete shopping list items.
- Categorize items as "Need" or "Want."
- Mark items as obtained.

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
5. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

- Access the calendar at `/calendar/`.
- Access the shopping list at `/shoppinglist/`.

## API Documentation

### Calendar API
- **Create Event**: `POST /calendar/create/`
- **Update Event**: `POST /calendar/<int:pk>/update/`
- **Delete Event**: `POST /calendar/<int:pk>/delete/`
- **Day View**: `GET /calendar/day/<int:year>/<int:month>/<int:day>/`
- **Week View**: `GET /calendar/week/<int:year>/<int:month>/<int:day>/`
- **Month View**: `GET /calendar/month/<int:year>/<int:month>/`

### Shopping List API
- **Create Item**: `POST /shoppinglist/create/`
- **Update Item**: `POST /shoppinglist/<int:pk>/update/`
- **Delete Item**: `POST /shoppinglist/<int:pk>/delete/`
- **List Items**: `GET /shoppinglist/items/`
- **Past Items**: `GET /shoppinglist/past-items/`

## Contributing

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes and push to your branch.
4. Submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.