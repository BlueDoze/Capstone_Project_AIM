# Fanshawe Navigator

## Project Goal

The main goal of this project is to create the **Fanshawe Navigator**, a web application designed to help students, staff, and visitors navigate the Fanshawe College campus. The application will provide an interactive map, search functionality for classrooms and services, and leverage the Gemini API to offer intelligent, conversational guidance.

## Project Structure

- `main.py`: The main entry point for the Flask application.
- `templates/`: Contains HTML templates for rendering pages.
  - `index.html`: The main page of the application.
- `static/`: Contains static assets like CSS and JavaScript.
  - `style.css`: Basic styling for the application.
  - `script.js`: Basic JavaScript for the application.
- `requirements.txt`: A list of Python dependencies for the project.
- `devserver.sh`: A script used by the development environment to run the Flask server.
- `.env`: A file for storing environment variables and secrets. This file is not committed to version control.
- `README.md`: This file.

## Getting Started

This project is configured to run in a specific development environment. Previews should run automatically when starting the workspace.

To run the server, open a terminal and use the `web` preview task, which executes the `./devserver.sh` script.

### Manual Setup After Cloning

If you clone this repository to a new machine, the `.venv` (virtual environment), `.env` (environment variables), and `__pycache__` directories will not be included. You will need to set them up manually.

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Create and activate the virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create the environment file:**
    Create a `.env` file in the root of the project to store your secret keys, such as your Gemini API key. For example:
    ```
    GEMINI_API_KEY='your_gemini_api_key'
    ```

5.  **Run the application:**
    ```bash
    ./devserver.sh
    ```

### Running with Docker

To run the application using Docker, ensure you have Docker and Docker Compose installed.

1.  **Create the environment file:**
    Create a `.env` file in the root of the project to store your `GEMINI_API_KEY`:
    ```
    GEMINI_API_KEY='your_gemini_api_key'
    ```

2.  **Build and run the container:**
    ```bash
    docker-compose up --build
    ```
    The application will be accessible at `http://localhost:8081`.

## Mobile Access Using ngrok

To access the application on a mobile device, you can use ngrok to create a secure tunnel that exposes your local server to the internet. This is particularly useful when your mobile device is on a different network or you want to test without configuring firewall rules.

### Prerequisites

1. **Install ngrok:**
   - Visit [ngrok.com](https://ngrok.com/) and sign up for a free account
   - Download and install ngrok for your platform
   - Authenticate your installation with your authtoken:
     ```bash
     ngrok config add-authtoken YOUR_AUTH_TOKEN
     ```

### Steps to Access via Mobile

1. **Start the Flask server:**
   ```bash
   ./devserver.sh
   ```
   The server should be running on `http://localhost:8081`.

2. **Start ngrok in a new terminal:**
   ```bash
   ngrok http 8081
   ```

3. **Copy the ngrok URL:**
   - ngrok will display a forwarding URL (e.g., `https://abc123.ngrok.io`)
   - Copy this HTTPS URL from the ngrok terminal output

4. **Access from your mobile device:**
   - Open a web browser on your mobile device
   - Navigate to the ngrok URL (e.g., `https://abc123.ngrok.io`)
   - The application should load and be fully functional

### Notes

- The ngrok URL changes each time you restart ngrok (unless you're using a paid plan with a static domain)
- Keep both the Flask server and ngrok running while testing on mobile
- The ngrok terminal shows request logs, which can be helpful for debugging
- For production use, consider using a paid ngrok plan with a static domain or deploy to a proper hosting service

### Alternative: Local Network Access

If your mobile device is on the same WiFi network as your development machine, you can access the application directly using your local IP address. The `./devserver.sh` script displays your local IP address when it starts. Use `http://[YOUR_LOCAL_IP]:8081` in your mobile browser.

For troubleshooting local network access issues, see `TROUBLESHOOTING_MOBILE.md`.

## Development Environment

- **Python Environment:** The environment uses Python 3 and a virtual environment located at `.venv`.
- **Dependency Management:** Project dependencies are listed in `requirements.txt`.
- **Activation:** Before running any `python` or `pip` commands in the terminal, you must first activate the virtual environment:
  ```bash
  source .venv/bin/activate
  ```
- **Running the Server:** The Flask development server is started using the `web` preview task, which runs the `./devserver.sh` script.

## Best Practices

### Security
- **Secrets Management:** Never hard-code secrets like API keys. Use environment variables loaded from a `.env` file (e.g., using the `python-dotenv` library).
- **Input Validation:** Always validate and sanitize user input to prevent common vulnerabilities.

### Project Structure
- **Blueprints:** For larger applications, use Flask Blueprints to organize your code into smaller, reusable components.
- **Application Factory:** Use the application factory pattern to create application instances, which is useful for testing and managing different configurations.
