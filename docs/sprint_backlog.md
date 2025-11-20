# Sprint Backlog

This document outlines the development sprints for creating the Fanshawe College Navigation Chatbot.

## Sprint 1: Foundational Setup & Core Chat Logic

- **Goal:** Establish the Flask project, create a chat interface, and implement core chatbot logic for handling messages and simple responses.
- **User Stories:**
    - As a developer, I want to set up the Flask project with Blueprints and an application factory.
    - As a user, I want to see a webpage with a chat window and a text input field to type messages.
    - As a user, I want to type a message, send it to the chatbot, and see my message and a reply in the chat window.
- **Tasks:**
    - Create a `run.py` file and a `project` folder.
    - Implement the application factory in `project/__init__.py`.
    - Create a `chatbot` blueprint in `project/chatbot.py`.
    - Create a `base.html` and an `index.html` template.
    - Design a simple chat interface in `index.html`.
    - Create a route in the `chatbot` blueprint to render the `index.html` template.
    - Add basic CSS for styling.
    - Create a new route in the `chatbot` blueprint to handle incoming messages (e.g., `/ask`).
    - Use JavaScript to send the user's message from the `index.html` page to the `/ask` endpoint.
    - Implement a basic function that receives the message and returns a hardcoded or simple rule-based response.
    - Update the frontend JavaScript to display the chatbot's response in the chat window.

## Sprint 2: Chat Interface & Logic Enhancement

- **Goal:** Enhance the chat interface and the chatbot's conversational abilities.
- **User Stories:**
    - As a user, I want the chat interface to be more visually appealing and user-friendly.
    - As a user, I want the chatbot to understand a wider range of greetings and basic questions.
- **Tasks:**
    - Improve the CSS and layout of the chat window.
    - Implement message timestamps.
    - Add a "typing" indicator to show when the bot is preparing a response.
    - Expand the rule-based logic to handle more conversational phrases (e.g., "how are you?", "thanks").
    - Refactor the backend to make it easier to add new response types.

## Sprint 3: Navigation & Interactive Map Integration

- **Goal:** Enable the chatbot to provide navigation instructions and display an interactive map with the route.
- **User Stories:**
    - As a user, I want to ask for directions to a specific place (e.g., "the library") and get step-by-step instructions.
    - As a user, when I receive directions, I want to see a map with the route visually highlighted.
- **Tasks:**
    - Create a simple data structure (e.g., a Python dictionary) to store directions for key locations.
    - Enhance the chatbot's logic to recognize keywords in the user's query.
    - When a keyword is matched, retrieve the corresponding directions and return them.
    - Choose and integrate a JavaScript mapping library (e.g., Leaflet.js).
    - Add a map container to the `index.html` template.
    - Create a route or a static JSON file to serve map data (e.g., a GeoJSON file).
    - Load the map in the browser.
    - Modify the chatbot's response to include the coordinates for a route.
    - Write JavaScript to draw a line on the map based on the route coordinates.

## Sprint 4: User Accounts & Personalization

- **Goal:** Allow users to create accounts to save and quickly access their important locations.
- **User Stories:**
    - As a user, I want to create an account and log in.
    - As a user, I want to be able to save a location as a "favorite" (e.g., "my classroom").
- **Tasks:**
    - Set up a database and a `User` model.
    - Implement registration and login functionality.
    - Create a `SavedLocation` model, linked to the `User` model.
    - Add a button or command in the chat (e.g., "save this as...") to allow logged-in users to save a location.
    - Create a profile page or a section in the UI where users can see and click on their saved locations for quick navigation.

## EXTRA: Admin & Data Management

- **Goal:** Build a basic admin interface for managing location and map data.
- **User Stories:**
    - As an admin, I want a dashboard to add, edit, or delete navigable locations.
- **Tasks:**
    - Create a secure admin area.
    - Build a simple web-based interface for CRUD (Create, Read, Update, Delete) operations on the location data.
    - Ensure that the chatbot uses this database as its source of truth for navigation, rather than hardcoded data.
