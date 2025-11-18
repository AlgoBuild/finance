# CS50 Finance

A Flask web application that simulates a stock trading platform: register/login, get stock quotes, buy/sell shares, view portfolio and transaction history, and change password. Built as part of the CS50 Finance problem set.
Video Demo: https://youtu.be/MEFGApoIBTs


## Features
- User authentication: register, login, logout, change password
- Quote lookup via external API (configured via API key)
- Buy and sell stocks with real-time quote lookups
- Portfolio view with current holdings and cash balance
- Transaction history
- Input validation and user-friendly error handling

## Tech Stack
- Python 3
- Flask, Jinja2 templates
- SQLite database (finance.db)
- Server-side sessions (Flask-Session)
- Bootstrap-based CSS (static/styles.css)

## Project Structure
- app.py — Flask application entry point and route definitions
- helpers.py — utility functions (e.g., apology, login_required, lookup, usd)
- templates/ — Jinja2 HTML templates (layout, index, register, login, quote, buy, sell, history, apology, etc.)
- static/ — static assets (styles.css, favicon)
- finance.db — SQLite database (generated after running/using the app)
- requirements.txt — Python dependencies

## Prerequisites
- Python 3.9+
## Setup
1. Create and activate a virtual environment
   - Windows (cmd):
     - py -3 -m venv .venv
     - .venv\Scripts\activate
   - PowerShell:
     - py -3 -m venv .venv
     - .venv\Scripts\Activate.ps1
2. Install dependencies
   - pip install -r requirements.txt

## Running
- flask run
- Then open the URL printed in the terminal (typically http://127.0.0.1:5000)

## Usage Notes
- Register a new account, then login
- Use Quote to look up a stock symbol, then Buy/Sell to transact
- Portfolio shows your current positions and cash
- History lists all transactions


## Security
- Passwords are hashed before storage
- Login required for trading routes
- Server-side session storage

