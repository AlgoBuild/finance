import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    user_id = session["user_id"]

    # Get user's cash
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

    # Get user's stocks (sum of shares grouped by symbol)
    holdings = db.execute("""
        SELECT symbol, SUM(shares) as total_shares
        FROM transactions
        WHERE user_id = ?
        GROUP BY symbol
        HAVING total_shares > 0
    """, user_id)

    total_stock_value = 0
    portfolio = []

    for holding in holdings:
        symbol = holding["symbol"]
        shares = holding["total_shares"]
        stock = lookup(symbol)
        price = stock["price"]
        total = shares * price
        total_stock_value += total

        portfolio.append({
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "total": total
        })

    grand_total = cash + total_stock_value

    return render_template("index.html", portfolio=portfolio, cash=cash, grand_total=grand_total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares_str = request.form.get("shares")

        if not symbol:
            return apology("must provide symbol", 400)

        if not shares_str:
            return apology("must provide shares", 400)

        if not shares_str.isdigit():
            return apology("shares must be a positive integer", 400)

        shares = int(shares_str)
        if shares <= 0:
            return apology("shares must be a positive integer", 400)

        stock = lookup(symbol)
        if stock is None:
            return apology("must provide a valid symbol", 400)

        price = stock["price"]
        total_price = price * shares
        user_id = session["user_id"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

        if cash < total_price:
            return apology("cannot afford", 400)

        db.execute("INSERT INTO transactions(user_id, symbol, shares, price, total_price, date_time) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                   user_id, symbol, shares, price, total_price)
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", total_price, user_id)

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]

    transactions = db.execute(
        "SELECT symbol, shares, price, date_time FROM transactions WHERE user_id = ? ORDER BY date_time DESC",
        user_id
    )

    history_data = []
    for tx in transactions:
        history_data.append({
            "symbol": tx["symbol"],
            "shares": tx["shares"],
            "price": tx["price"],
            "date_time": tx["date_time"],
            "type": "BUY" if tx["shares"] > 0 else "SELL"
        })

    return render_template("history.html", transactions=history_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 400)

        elif not request.form.get("password"):
            return apology("must provide password", 400)

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 400)

        session["user_id"] = rows[0]["id"]

        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("must provide symbol", 400)

        stock = lookup(symbol)
        if stock is None:
            return apology("invalid symbol", 400)

        return render_template("quoted.html", quote_data=stock)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 400)

        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        hashed = generate_password_hash(request.form.get("password"))
        try:
            db.execute("INSERT INTO users(username, hash) VALUES (?, ?);",
                       request.form.get("username"), hashed)
        except ValueError:
            return apology("username already exists", 400)

        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares_str = request.form.get("shares")
        user_id = session["user_id"]

        if not symbol:
            return apology("must provide symbol", 400)

        if not shares_str:
            return apology("must provide shares", 400)

        if not shares_str.isdigit():
            return apology("shares must be a positive integer", 400)

        shares = int(shares_str)
        if shares <= 0:
            return apology("shares must be a positive integer", 400)

        owned_shares = db.execute(
            "SELECT SUM(shares) as total FROM transactions WHERE user_id = ? AND symbol = ?",
            user_id, symbol
        )[0]["total"] or 0

        if owned_shares < shares:
            return apology("not enough shares", 400)

        stock = lookup(symbol)
        if stock is None:
            return apology("must provide a valid symbol", 400)

        price = stock["price"]
        total_price = price * shares

        db.execute("INSERT INTO transactions(user_id, symbol, shares, price, total_price, date_time) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                   user_id, symbol, -shares, price, total_price)
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", total_price, user_id)

        return redirect("/")
    else:
        user_id = session["user_id"]
        portfolio = db.execute(
            "SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0",
            user_id
        )
        return render_template("sell.html", portfolio=portfolio)



@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    """Allow user to change password"""
    user_id = session["user_id"]

    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not current_password or not new_password or not confirm_password:
            return apology("must fill all fields", 400)

        row = db.execute("SELECT hash FROM users WHERE id = ?", user_id)[0]

        if not check_password_hash(row["hash"], current_password):
            return apology("current password incorrect", 400)

        if new_password != confirm_password:
            return apology("passwords do not match", 400)

        hash_new = generate_password_hash(new_password)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", hash_new, user_id)

        flash("Password changed successfully!")
        return redirect("/")
    else:
        return render_template("changepassword.html")
