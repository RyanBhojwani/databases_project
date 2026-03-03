-- Create Database
CREATE DATABASE IF NOT EXISTS ecommerce;
USE ecommerce;

-- Creating all tables

-- Account
CREATE TABLE Account (
  AccountID      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  Name           VARCHAR(120)  NOT NULL,
  Email          VARCHAR(254)  NOT NULL,
  Phone          VARCHAR(32)   NULL,
  Username       VARCHAR(60)   NOT NULL,

  PRIMARY KEY (AccountID)
);

-- Product
CREATE TABLE Product (
  ProductID      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  Name           VARCHAR(200) NOT NULL,
  Description    TEXT         NULL,
  Price          DECIMAL(10,2) NOT NULL,

  PRIMARY KEY (ProductID)
);

-- ShippingOption
CREATE TABLE ShippingOption (
  ShippingOptionID INT UNSIGNED NOT NULL AUTO_INCREMENT,
  Name             VARCHAR(80) NOT NULL,
  Cost             DECIMAL(10,2) NOT NULL,
  TimeToDelivery   VARCHAR(40) NOT NULL,  -- e.g., "3-5 business days"

  PRIMARY KEY (ShippingOptionID)
);

-- Attribute (Name, Value) catalog of attribute name/value pairs
CREATE TABLE Attribute (
  AttributeID    INT UNSIGNED NOT NULL AUTO_INCREMENT,
  Name           VARCHAR(80)  NOT NULL,  
  Value          VARCHAR(255) NOT NULL, 

  PRIMARY KEY (AttributeID)
);

-- ProductAttribute (junction between Product and Attribute)
CREATE TABLE ProductAttribute (
  ProductAttributeID INT UNSIGNED NOT NULL AUTO_INCREMENT,
  ProductID          INT UNSIGNED NOT NULL,
  AttributeID        INT UNSIGNED NOT NULL,

  PRIMARY KEY (ProductAttributeID),
  CONSTRAINT fk_ProductAttribute_Product
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_ProductAttribute_Attribute
    FOREIGN KEY (AttributeID) REFERENCES Attribute(AttributeID)
    ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Inventory 
CREATE TABLE Inventory (
  ProductID          INT UNSIGNED NOT NULL,
  QuantityAvailable  INT UNSIGNED NOT NULL,
  LastUpdate         DATETIME     NOT NULL,

  PRIMARY KEY (ProductID),
  CONSTRAINT fk_Inventory_Product
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
    ON DELETE CASCADE ON UPDATE CASCADE
);

-- Cart
CREATE TABLE Cart (
  CartID        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  AccountID     INT UNSIGNED NOT NULL,

  Status        ENUM('ACTIVE','ABANDONED','CONVERTED') NOT NULL,
  CreatedTime   DATETIME NOT NULL,
  LastUpdate    DATETIME NOT NULL,

  DeviceType    ENUM('MOBILE','TABLET','LAPTOP','DESKTOP','UNKNOWN') NOT NULL DEFAULT 'UNKNOWN',

  PRIMARY KEY (CartID),
  CONSTRAINT fk_Cart_Account
    FOREIGN KEY (AccountID) REFERENCES Account(AccountID)
    ON DELETE CASCADE ON UPDATE CASCADE
);

-- CartProduct
CREATE TABLE CartProduct (
  CartProductID BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  CartID        BIGINT UNSIGNED NOT NULL,
  ProductID     INT UNSIGNED NOT NULL,
  Quantity      INT UNSIGNED NOT NULL,
  Price         DECIMAL(10,2) NOT NULL,  

  PRIMARY KEY (CartProductID),
  CONSTRAINT fk_CartProduct_Cart
    FOREIGN KEY (CartID) REFERENCES Cart(CartID)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_CartProduct_Product
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
    ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Order
CREATE TABLE `Order` (
  OrderID           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  AccountID         INT UNSIGNED NOT NULL,
  CartID            BIGINT UNSIGNED NOT NULL,

  Status            ENUM('PLACED','PAID','SHIPPED','DELIVERED','CANCELLED','RETURNED') NOT NULL,
  TimePlaced        DATETIME NOT NULL,

  ShippingOptionID  INT UNSIGNED NOT NULL,

  PRIMARY KEY (OrderID),
  CONSTRAINT fk_Order_Account
    FOREIGN KEY (AccountID) REFERENCES Account(AccountID)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_Order_Cart
    FOREIGN KEY (CartID) REFERENCES Cart(CartID)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_Order_ShippingOption
    FOREIGN KEY (ShippingOptionID) REFERENCES ShippingOption(ShippingOptionID)
    ON DELETE RESTRICT ON UPDATE CASCADE
);

-- OrderItem
CREATE TABLE OrderItem (
  OrderItemID   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  OrderID       BIGINT UNSIGNED NOT NULL,
  ProductID     INT UNSIGNED NOT NULL,
  Quantity      INT UNSIGNED NOT NULL,
  Price         DECIMAL(10,2) NOT NULL, 

  PRIMARY KEY (OrderItemID),
  CONSTRAINT fk_OrderItem_Order
    FOREIGN KEY (OrderID) REFERENCES `Order`(OrderID)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_OrderItem_Product
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
    ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Payment
CREATE TABLE Payment (
  PaymentID    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  OrderID      BIGINT UNSIGNED NOT NULL,

  Method       ENUM('CREDIT_CARD','DEBIT_CARD','BANK_TRANSFER') NOT NULL,
  Status       ENUM('PENDING','APPROVED','DECLINED','REFUNDED') NOT NULL,
  PayDate      DATETIME NULL,

  PRIMARY KEY (PaymentID),
  CONSTRAINT fk_Payment_Order
    FOREIGN KEY (OrderID) REFERENCES `Order`(OrderID)
    ON DELETE CASCADE ON UPDATE CASCADE
);

-- Return
CREATE TABLE `Return` (
  ReturnID    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  OrderID     BIGINT UNSIGNED NOT NULL,
  AccountID   INT UNSIGNED NOT NULL,

  Status      ENUM('INITIATED','IN_TRANSIT','RECEIVED','REFUNDED','REJECTED') NOT NULL,

  PRIMARY KEY (ReturnID),
  CONSTRAINT fk_Return_Order
    FOREIGN KEY (OrderID) REFERENCES `Order`(OrderID)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_Return_Account
    FOREIGN KEY (AccountID) REFERENCES Account(AccountID)
    ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ReturnItem
CREATE TABLE ReturnItem (
  ReturnItemID   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  ReturnID       BIGINT UNSIGNED NOT NULL,
  OrderItemID    BIGINT UNSIGNED NOT NULL,
  Quantity       INT UNSIGNED NOT NULL,
  RefundAmount   DECIMAL(10,2) NOT NULL,

  PRIMARY KEY (ReturnItemID),
  CONSTRAINT fk_ReturnItem_Return
    FOREIGN KEY (ReturnID) REFERENCES `Return`(ReturnID)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_ReturnItem_OrderItem
    FOREIGN KEY (OrderItemID) REFERENCES OrderItem(OrderItemID)
    ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Load Data
SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION';
SET SESSION foreign_key_checks = 0;
SET SESSION unique_checks = 0;

LOAD DATA  INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/account.csv'
INTO TABLE Account
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(AccountID, Name, Email, Phone, Username);

LOAD DATA  INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/product.csv'
INTO TABLE Product
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(ProductID, Name, Description, Price);

LOAD DATA  INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/shipping_option.csv'
INTO TABLE ShippingOption
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(ShippingOptionID, Name, Cost, TimeToDelivery);

LOAD DATA  INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/attribute.csv'
INTO TABLE Attribute
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(AttributeID, Name, Value);

LOAD DATA  INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/product_attribute.csv'
INTO TABLE ProductAttribute
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(ProductAttributeID, ProductID, AttributeID);

LOAD DATA  INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/inventory.csv'
INTO TABLE Inventory
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(ProductID, QuantityAvailable, LastUpdate);

LOAD DATA  INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/cart.csv'
INTO TABLE Cart
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(CartID, AccountID, Status, CreatedTime, LastUpdate, DeviceType);

LOAD DATA  INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/cart_product.csv'
INTO TABLE CartProduct
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(CartProductID, CartID, ProductID, Quantity, Price);

-- `Order` is reserved-ish; keep backticks
LOAD DATA  INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/order.csv'
INTO TABLE `Order`
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(OrderID, AccountID, CartID, Status, TimePlaced, ShippingOptionID);

LOAD DATA  INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/order_item.csv'
INTO TABLE OrderItem
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(OrderItemID, OrderID, ProductID, Quantity, Price);

LOAD DATA  INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/payment.csv'
INTO TABLE Payment
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(PaymentID, OrderID, Method, Status, @paydate)
SET PayDate = NULLIF(@paydate, '');

LOAD DATA  INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/return.csv'
INTO TABLE `Return`
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(ReturnID, OrderID, AccountID, Status);

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/return_item.csv'
INTO TABLE ReturnItem
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(ReturnItemID, ReturnID, OrderItemID, Quantity, RefundAmount);

-- Re-enable checks
SET SESSION foreign_key_checks = 1;
SET SESSION unique_checks = 1;