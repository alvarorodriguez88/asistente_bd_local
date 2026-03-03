USE tienda;

CREATE TABLE IF NOT EXISTS productos (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  sku           VARCHAR(32) NOT NULL UNIQUE,
  nombre        VARCHAR(120) NOT NULL,
  categoria     VARCHAR(60) NOT NULL,
  precio        DECIMAL(10,2) NOT NULL,
  coste         DECIMAL(10,2) NOT NULL,
  activo        TINYINT(1) NOT NULL DEFAULT 1,
  creado_en     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventario (
  producto_id   INT PRIMARY KEY,
  stock         INT NOT NULL,
  stock_min     INT NOT NULL DEFAULT 0,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_inv_prod FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE TABLE IF NOT EXISTS clientes (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  nombre        VARCHAR(120) NOT NULL,
  email         VARCHAR(120) UNIQUE,
  creado_en     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ventas (
  id            BIGINT AUTO_INCREMENT PRIMARY KEY,
  fecha         DATETIME NOT NULL,
  cliente_id    INT NULL,
  metodo_pago   ENUM('EFECTIVO','TARJETA','BIZUM','TRANSFERENCIA') NOT NULL,
  total         DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_venta_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE IF NOT EXISTS venta_lineas (
  id            BIGINT AUTO_INCREMENT PRIMARY KEY,
  venta_id      BIGINT NOT NULL,
  producto_id   INT NOT NULL,
  cantidad      INT NOT NULL,
  precio_unit   DECIMAL(10,2) NOT NULL,
  subtotal      DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_linea_venta FOREIGN KEY (venta_id) REFERENCES ventas(id),
  CONSTRAINT fk_linea_prod  FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE INDEX idx_ventas_fecha ON ventas(fecha);
CREATE INDEX idx_lineas_prod ON venta_lineas(producto_id);
CREATE INDEX idx_prod_categoria ON productos(categoria);
