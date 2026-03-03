USE tienda;

INSERT INTO productos (sku, nombre, categoria, precio, coste) VALUES
('CAF-001','Café molido 250g','Alimentación', 3.90, 2.10),
('TE-001','Té verde 20 bolsitas','Alimentación', 2.80, 1.40),
('GAL-001','Galletas artesanas','Alimentación', 4.50, 2.60),
('PAN-001','Pan artesanal','Alimentación', 1.60, 0.70),
('AGU-001','Agua 1.5L','Bebidas', 1.10, 0.35),
('REF-001','Refresco cola 2L','Bebidas', 2.10, 0.80),
('LIM-001','Limpiador multiusos','Hogar', 3.20, 1.50),
('PIL-001','Pilas AA (pack 4)','Hogar', 5.90, 3.10);

INSERT INTO inventario (producto_id, stock, stock_min)
SELECT id,
       CASE sku
         WHEN 'PAN-001' THEN 18
         WHEN 'AGU-001' THEN 42
         WHEN 'REF-001' THEN 24
         WHEN 'PIL-001' THEN 9
         ELSE 15
       END,
       CASE sku
         WHEN 'PAN-001' THEN 10
         WHEN 'PIL-001' THEN 8
         ELSE 12
       END
FROM productos;

INSERT INTO clientes (nombre, email) VALUES
('Ana Martín','ana@example.com'),
('Luis Pérez','luis@example.com'),
('Marta García','marta@example.com'),
('Carlos Ruiz','carlos@example.com');

INSERT INTO ventas (fecha, cliente_id, metodo_pago, total) VALUES
(NOW() - INTERVAL 4 DAY, 1, 'TARJETA', 0),
(NOW() - INTERVAL 3 DAY, 2, 'EFECTIVO', 0),
(NOW() - INTERVAL 2 DAY, 3, 'BIZUM', 0),
(NOW() - INTERVAL 1 DAY, NULL, 'TARJETA', 0),
(NOW(), 1, 'TARJETA', 0);

INSERT INTO venta_lineas (venta_id, producto_id, cantidad, precio_unit, subtotal) VALUES
(1, (SELECT id FROM productos WHERE sku='CAF-001'), 2, 3.90, 7.80),
(1, (SELECT id FROM productos WHERE sku='PAN-001'), 3, 1.60, 4.80),
(2, (SELECT id FROM productos WHERE sku='AGU-001'), 4, 1.10, 4.40),
(2, (SELECT id FROM productos WHERE sku='GAL-001'), 1, 4.50, 4.50),
(3, (SELECT id FROM productos WHERE sku='LIM-001'), 1, 3.20, 3.20),
(3, (SELECT id FROM productos WHERE sku='PIL-001'), 1, 5.90, 5.90),
(4, (SELECT id FROM productos WHERE sku='REF-001'), 3, 2.10, 6.30),
(4, (SELECT id FROM productos WHERE sku='TE-001'), 2, 2.80, 5.60),
(5, (SELECT id FROM productos WHERE sku='CAF-001'), 1, 3.90, 3.90),
(5, (SELECT id FROM productos WHERE sku='PAN-001'), 2, 1.60, 3.20);

UPDATE ventas v
JOIN (
  SELECT venta_id, ROUND(SUM(subtotal),2) AS total_calc
  FROM venta_lineas
  GROUP BY venta_id
) x ON x.venta_id = v.id
SET v.total = x.total_calc;
