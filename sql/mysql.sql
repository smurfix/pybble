CREATE TABLE obj (
	discriminator INTEGER, 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	PRIMARY KEY (id)
);
CREATE TABLE urls (
	added DATETIME, 
	uid VARCHAR(140), 
	public BOOL, 
	id INTEGER NOT NULL, 
	target VARCHAR(500), 
	PRIMARY KEY (id), 
	 FOREIGN KEY(id) REFERENCES obj (id)
);

