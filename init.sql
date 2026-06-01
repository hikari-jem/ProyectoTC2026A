CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(50) NOT NULL,
    rol ENUM('Administrador', 'Cajero') NOT NULL
);

CREATE TABLE IF NOT EXISTS productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    precio DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL,
    categoria VARCHAR(50) NOT NULL
);

INSERT INTO usuarios (nombre_completo, username, password, rol) VALUES
('Arturo García López', 'arturo', '12345', 'Administrador'),
('Vanessa Jacobo', 'vann', '54321', 'Cajero')
ON DUPLICATE KEY UPDATE id=id;

INSERT INTO productos (nombre, precio, stock, categoria) VALUES
('Chetos', 34.00, 13, 'Botanas'),
('Jamon', 34.00, 10, 'Lácteos'),
('Queso', 45.00, 5, 'Lácteos'),
('Flan', 25.00, 11, 'Lácteos'),
('Rancheritos', 45.00, 5, 'Botanas'),
('Ruffles', 25.00, 17, 'Botanas'),
('Leche Lala 1L', 28.00, 22, 'Lácteos'),
('Sabritas', 20.00, 26, 'Botanas'),
('Coca Cola 600ml', 18.00, 26, 'Bebidas');