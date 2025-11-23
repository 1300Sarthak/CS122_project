from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric, Boolean, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(20), nullable=False)
    balance = Column(Numeric(10, 2), nullable=False, default=0.00)

    __table_args__ = (
        CheckConstraint(
            "type IN ('Checking', 'Savings', 'Cash', 'Credit')", name='check_account_type'),
    )

    transactions = relationship("Transaction", back_populates="account")


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(20), nullable=False)
    description = Column(String(500))

    __table_args__ = (
        CheckConstraint("type IN ('Income', 'Expense')",
                        name='check_category_type'),
    )

    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    payee = Column(String(200))
    amount = Column(Numeric(10, 2), nullable=False)
    note = Column(String(500))
    planned = Column(Boolean, nullable=False, default=False)

    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")


class Budget(Base):
    __tablename__ = 'budgets'

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    target_amount = Column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("month >= 1 AND month <= 12", name='check_month'),
        UniqueConstraint('category_id', 'month', 'year', name='unique_budget'),
    )

    category = relationship("Category", back_populates="budgets")
