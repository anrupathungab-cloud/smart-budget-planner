import streamlit as st
import matplotlib.pyplot as plt
import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide")

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- DATABASE ----------------
conn = sqlite3.connect("budget.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS history (
    username TEXT,
    salary REAL,
    spent REAL,
    remaining REAL
)
""")

conn.commit()

# ---------------- UI Styling ----------------
st.title("💰 Smart Salary Budget Planner")
st.markdown("## 📊 Plan Smart. Spend Smart. Save Smart.")
st.divider()

# ---------------- LOGIN SYSTEM ----------------
st.sidebar.title("🔐 Account")
menu = st.sidebar.radio("Menu", ["Login", "Signup"])

if menu == "Signup":
    new_user = st.sidebar.text_input("Username")
    new_pass = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Signup"):
        c.execute("SELECT * FROM users WHERE username=?", (new_user,))
        if c.fetchone():
            st.sidebar.warning("User already exists")
        else:
            c.execute("INSERT INTO users VALUES (?, ?)", (new_user, new_pass))
            conn.commit()
            st.sidebar.success("Account created!")

elif menu == "Login":
    user = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, password))
        if c.fetchone():
            st.session_state.user = user
            st.sidebar.success(f"Welcome {user}")
        else:
            st.sidebar.error("Invalid credentials")

# ---------------- LOGOUT ----------------
if st.session_state.user:
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

# ---------------- MAIN APP ----------------
if st.session_state.user:

    name = st.text_input("Enter your name")
    salary = st.number_input("Enter your monthly salary (₹):", min_value=0)
    goal = st.number_input("Enter your saving goal (₹):", min_value=0)

    st.subheader("📌 Select your expenses")

    use_rent = st.checkbox("🏠 Rent")
    use_groceries = st.checkbox("🍚 Groceries", True)
    use_outings = st.checkbox("🎉 Outings", True)
    use_bills = st.checkbox("📱 Bills", True)
    use_medical = st.checkbox("🏥 Medical", True)
    use_fuel = st.checkbox("⛽ Fuel", True)
    use_vehicle = st.checkbox("🔧 Vehicle Service")
    use_emi = st.checkbox("💳 EMI")
    use_shopping = st.checkbox("🛍️ Shopping")
    use_savings = st.checkbox("💰 Savings", True)
    use_emergency = st.checkbox("🚨 Emergency Fund", True)

    st.divider()

    st.subheader("🎛️ Adjust Budget Percentages")

    rent_pct = st.slider("Rent %", 0, 50, 25)
    groceries_pct = st.slider("Groceries %", 0, 30, 15)
    outings_pct = st.slider("Outings %", 0, 30, 10)
    bills_pct = st.slider("Bills %", 0, 20, 5)
    medical_pct = st.slider("Medical %", 0, 20, 5)
    fuel_pct = st.slider("Fuel %", 0, 20, 10)
    vehicle_pct = st.slider("Vehicle Service %", 0, 20, 5)
    emi_pct = st.slider("EMI %", 0, 40, 10)
    shopping_pct = st.slider("Shopping %", 0, 20, 5)
    savings_pct = st.slider("Savings %", 0, 30, 10)
    emergency_pct = st.slider("Emergency Fund %", 0, 20, 5)

    total_pct = (rent_pct + groceries_pct + outings_pct + bills_pct +
                 medical_pct + fuel_pct + vehicle_pct + emi_pct +
                 shopping_pct + savings_pct + emergency_pct)

    st.write(f"📊 Total Allocation: {total_pct}%")

    if total_pct > 100:
        st.error("❌ Total percentage exceeds 100%!")

    lifestyle = st.selectbox("Lifestyle", ["Normal", "Saver", "Luxury"])

    def calculate_budget():
        budget = {}

        if use_rent: budget["Rent"] = salary * rent_pct / 100
        if use_groceries: budget["Groceries"] = salary * groceries_pct / 100
        if use_outings: budget["Outings"] = salary * outings_pct / 100
        if use_bills: budget["Bills"] = salary * bills_pct / 100
        if use_medical: budget["Medical"] = salary * medical_pct / 100
        if use_fuel: budget["Fuel"] = salary * fuel_pct / 100
        if use_vehicle: budget["Vehicle Service"] = salary * vehicle_pct / 100
        if use_emi: budget["EMI"] = salary * emi_pct / 100
        if use_shopping: budget["Shopping"] = salary * shopping_pct / 100
        if use_savings: budget["Savings"] = salary * savings_pct / 100
        if use_emergency: budget["Emergency Fund"] = salary * emergency_pct / 100

        if lifestyle == "Saver" and "Savings" in budget:
            budget["Savings"] += salary * 0.05
        elif lifestyle == "Luxury" and "Outings" in budget:
            budget["Outings"] += salary * 0.05

        total = sum(budget.values())
        remaining = salary - total

        return budget, remaining

    if st.button("🚀 Calculate Budget"):

        st.write(f"👋 Hello {name}")
        budget, remaining = calculate_budget()

        col1, col2, col3 = st.columns(3)
        col1.metric("Salary", f"₹{salary}")
        col2.metric("Spent", f"₹{sum(budget.values()):.0f}")
        col3.metric("Remaining", f"₹{remaining:.0f}")

        # SAVE HISTORY
        c.execute("INSERT INTO history VALUES (?, ?, ?, ?)",
                  (st.session_state.user, salary, sum(budget.values()), remaining))
        conn.commit()

        st.subheader("📊 Breakdown")
        for k, v in budget.items():
            st.write(f"{k}: ₹{v:.2f}")

        # PIE CHART
        if budget:
            fig, ax = plt.subplots()
            ax.pie(budget.values(), labels=budget.keys(), autopct='%1.1f%%')
            ax.axis('equal')
            st.pyplot(fig)

        # HISTORY
        st.subheader("📜 History")
        c.execute("SELECT salary, spent, remaining FROM history WHERE username=?",
                  (st.session_state.user,))
        data = c.fetchall()

        if data:
            df = pd.DataFrame(data, columns=["Salary", "Spent", "Remaining"])
            st.dataframe(df)

            # PREDICTION
            if len(df) >= 3:
                df["Month"] = range(1, len(df) + 1)
                model = LinearRegression()
                model.fit(df[["Month"]], df["Remaining"])
                pred = model.predict([[len(df)+1]])
                st.info(f"📈 Next month prediction: ₹{pred[0]:.2f}")