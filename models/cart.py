# models/cart.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float, Boolean, func
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base


class Cart(Base):
    __tablename__ = 'carts'

    id = Column(Integer, primary_key=True, index=True)
    clover_merchant_id = Column(String(64), nullable=False)
    session_id = Column(String(128), nullable=True)

    # Basic cart info
    status = Column(String(20), default="active")  # active, converted, abandoned
    subtotal = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="cart")


class CartItem(Base):
    __tablename__ = 'cart_items'

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey('carts.id'), nullable=False)

    # Clover item details
    clover_item_id = Column(String(64), nullable=False)

    # Item details
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)  # Unit price
    quantity = Column(Integer, default=1)

    # Calculated totals
    line_total = Column(Float, nullable=False)  # price * quantity

    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    cart = relationship("Cart", back_populates="items")
    modifiers = relationship("CartItemModifier", back_populates="cart_item", cascade="all, delete-orphan")


class CartItemModifier(Base):
    __tablename__ = 'cart_item_modifiers'

    id = Column(Integer, primary_key=True, index=True)
    cart_item_id = Column(Integer, ForeignKey('cart_items.id'), nullable=False)

    # Clover modifier details
    clover_modifier_id = Column(String(64), nullable=False)
    clover_modifier_group_id = Column(String(64), nullable=False)

    # Modifier details
    name = Column(String(255), nullable=False)
    price = Column(Float, default=0.0)  # Additional cost

    # Metadata
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    cart_item = relationship("CartItem", back_populates="modifiers")


# Order Management Models
class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey('carts.id'), nullable=False)
    clover_merchant_id = Column(String(64), nullable=False)
    clover_order_id = Column(String(64), nullable=True)

    # Customer Information
    customer_id = Column(String(64), nullable=True)
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    customer_email = Column(String(255), nullable=True)

    # Order Details
    order_type = Column(String(50), default="delivery")  # delivery, pickup, dine_in
    delivery_address = Column(Text, nullable=True)
    pickup_time = Column(DateTime, nullable=True)
    delivery_time = Column(DateTime, nullable=True)
    table_number = Column(String(20), nullable=True)

    # Financial Details
    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.0)
    service_charge = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)

    # Payment
    payment_method = Column(String(50), nullable=True)
    payment_status = Column(String(20), default="pending")
    transaction_id = Column(String(128), nullable=True)

    # Status & Tracking
    status = Column(String(20), default="pending")  # pending, confirmed, preparing, ready, delivered, cancelled
    source = Column(String(50), default="web")
    employee_id = Column(String(64), nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    confirmed_at = Column(DateTime, nullable=True)
    synced_at = Column(DateTime, nullable=True)

    # Relationships
    cart = relationship("Cart", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    clover_item_id = Column(String(64), nullable=False)
    clover_line_item_id = Column(String(64), nullable=True)

    # Item details
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    line_total = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    order = relationship("Order", back_populates="items")
    modifiers = relationship("OrderItemModifier", back_populates="order_item", cascade="all, delete-orphan")


class OrderItemModifier(Base):
    __tablename__ = 'order_item_modifiers'

    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey('order_items.id'), nullable=False)

    # Modifier details
    clover_modifier_id = Column(String(64), nullable=False)
    clover_modifier_group_id = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False)
    price = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    order_item = relationship("OrderItem", back_populates="modifiers")
