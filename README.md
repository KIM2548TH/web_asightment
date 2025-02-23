# web_asightment

This project provides a web application to compare the cost of living in various provinces of Thailand. Users can view and compare living expenses, and administrators can add new data.

## Features

- View cost of living data for different provinces
- Compare cost of living between two provinces
- Add new provinces and cost of living data (admin only)
- About Us page

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/KIM2548TH/thailand-cost-of-living.git
    cd thailand-cost-of-living
    ```

2. Install Poetry:

    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

3. Install dependencies using Poetry:

    ```bash
    poetry install
    ```

4. Run the application:

    ```bash
    poetry run python web/main.py
    ```

5. Initialize the database:

    ```bash
    poetry run python web/init_database.py
    ```

    This script will create the necessary tables and populate initial data, including roles and provinces.

6. Open your web browser and go to `http://127.0.0.1:5000`.

## Usage

### Viewing Cost of Living Data

- Navigate to the home page to view the latest cost of living data for Thailand.
- Use the "View Province" page to see detailed data for a specific province.
- Use the "View Compare Cost" page to compare the cost of living between two provinces.

### Adding Data (Admin Only)

- Log in as an admin user.
- Use the "Create Province" page to add a new province.
- Use the "Create Cost of Living" page to add cost of living data for a province.

### Contact Us

- Use the "Contact" page to send feedback or questions.
- Other contact methods:
  - Facebook: [จิตรกร จันทร์สังข์](https://www.facebook.com/jitkhon.jansang)
  - Instagram: [@jitkhon_.2548](https://www.instagram.com/jitkhon_.2548)
  - GitHub: [KIM2548TH](https://github.com/KIM2548TH)

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.