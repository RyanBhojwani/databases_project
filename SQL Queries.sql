-- 1
SELECT p.ProductID, p.Name, p.Description, p.Price, 
	   GROUP_CONCAT(CONCAT(a.Name, '=', a.Value) ORDER BY a.Name SEPARATOR ', ') AS Attributes
FROM Product p
JOIN ProductAttribute pa ON pa.ProductID = p.ProductID
JOIN Attribute a ON a.AttributeID = pa.AttributeID
WHERE EXISTS (
  SELECT *
  FROM ProductAttribute pa2
  JOIN Attribute a2 ON a2.AttributeID = pa2.AttributeID
  WHERE pa2.ProductID = p.ProductID
    AND a2.Name = 'Category'
    AND a2.Value = 'FASHION'
) AND a.Name IN ('Size', 'Color', 'Material')
GROUP BY p.ProductID, p.Name, p.Description, p.Price;


-- 2
-- MongoDB

-- 3
SELECT p.ProductID, p.Name, i.QuantityAvailable
FROM Inventory i
JOIN Product p ON p.ProductID = i.ProductID
WHERE i.QuantityAvailable < 5;


-- 4
SELECT p.ProductID, p.Name, p.Price, i.QuantityAvailable
FROM Product p
JOIN Inventory i ON i.ProductID = p.ProductID
WHERE i.QuantityAvailable > 0
  AND EXISTS (
    SELECT *
    FROM ProductAttribute pa
    JOIN Attribute a ON a.AttributeID = pa.AttributeID
    WHERE pa.ProductID = p.ProductID AND a.Name = 'Category' AND a.Value = 'FASHION'
  )
  AND (
    EXISTS (
      SELECT *
      FROM ProductAttribute pa2
      JOIN Attribute a2 ON a2.AttributeID = pa2.AttributeID
      WHERE pa2.ProductID = p.ProductID AND a2.Name = 'Color' AND a2.Value = 'Blue'
    )
    OR EXISTS (
      SELECT *
      FROM ProductAttribute pa3
      JOIN Attribute a3 ON a3.AttributeID = pa3.AttributeID
      WHERE pa3.ProductID = p.ProductID AND a3.Name = 'Size' AND a3.Value = 'L'
    )
  );

-- 5
-- MongoDB

-- 6
-- MongoDB

-- 7
SELECT c.CartID, c.AccountID, c.DeviceType, 
  SUM(cp.Quantity) AS total_items, SUM(cp.Quantity * cp.Price) AS total_amount
FROM cart c
LEFT JOIN cartproduct cp ON cp.CartID = c.CartID
GROUP BY c.CartID;


-- 8
SELECT o.OrderID, p.ProductID, p.Name AS product_name, p.description as product_description, oi.Price, pay.Method AS payment_method, 
	so.Name AS shipping_option, o.Status
FROM `order` o
JOIN account a ON a.AccountID = o.AccountID
JOIN orderitem oi ON oi.OrderID  = o.OrderID
JOIN product p ON p.ProductID = oi.ProductID
LEFT JOIN payment pay ON pay.OrderID = o.OrderID
LEFT JOIN shippingoption so ON so.ShippingOptionID = o.ShippingOptionID
WHERE a.Username = 'sarah'
ORDER BY o.OrderID;

-- 9
SELECT r.ReturnID, r.Status AS refund_status, ri.RefundAmount, 0 AS restocking_fee
FROM `return` r
JOIN account a ON a.AccountID = r.AccountID
JOIN returnitem ri ON ri.ReturnID = r.ReturnID
WHERE a.Username = 'sarah';


-- 10
SELECT AVG(DATEDIFF(o2.TimePlaced, o1.TimePlaced)) AS avg_days_between_purchases
FROM `Order` o1
JOIN `Order` o2 ON o1.AccountID = o2.AccountID
JOIN Account a ON o1.AccountID = a.AccountID
WHERE a.Username = 'sarah' AND o2.TimePlaced = (
	SELECT MIN(o3.TimePlaced)
    FROM `Order` o3
    WHERE o3.AccountID = o1.AccountID AND o3.TimePlaced > o1.TimePlaced
  );
  






-- 11
SELECT 100 * SUM(CASE WHEN Status = 'CONVERTED' THEN 0 ELSE 1 END) / COUNT(*) AS pct_carts_not_converted from cart
where CreatedTime >= NOW() - INTERVAL 30 DAY;




-- 12
SELECT p2.ProductID, p2.Name, COUNT(*) AS times_bought_with_headphones
FROM OrderItem oi1
JOIN Product p1 ON p1.ProductID = oi1.ProductID
JOIN OrderItem oi2 ON oi2.OrderID = oi1.OrderID
JOIN Product p2 ON p2.ProductID = oi2.ProductID
WHERE p1.Name LIKE '%headphones%' AND oi2.ProductID != oi1.ProductID
GROUP BY p2.ProductID
ORDER BY times_bought_with_headphones DESC
LIMIT 3;




-- 13
SELECT a.AccountID, a.Username, DATEDIFF(CURDATE(), MAX(o.TimePlaced)) AS days_since_last_purchase, COUNT(o.OrderID) AS total_orders
FROM account a
LEFT JOIN `order` o ON o.AccountID = a.AccountID
GROUP BY a.AccountID, a.Username;





