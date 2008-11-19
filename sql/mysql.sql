CREATE TABLE obj (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	discriminator INTEGER, 
	owner INTEGER, 
	superowner INTEGER, 
	site INTEGER, 
	PRIMARY KEY (id), 
	 FOREIGN KEY(owner) REFERENCES obj (id), 
	 FOREIGN KEY(superowner) REFERENCES obj (id), 
	 FOREIGN KEY(site) REFERENCES obj (id)
);
CREATE TABLE urls (
	id INTEGER NOT NULL, 
	uid VARCHAR(140), 
	target VARCHAR(500), 
	added DATETIME, 
	public BOOL, 
	PRIMARY KEY (id), 
	 FOREIGN KEY(id) REFERENCES obj (id)
);

