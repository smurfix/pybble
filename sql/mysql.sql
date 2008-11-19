CREATE TABLE obj (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	discriminator INTEGER, 
	owner_id INTEGER, 
	parent_id INTEGER, 
	superparent_id INTEGER, 
	PRIMARY KEY (id), 
	 FOREIGN KEY(superparent_id) REFERENCES obj (id), 
	 FOREIGN KEY(owner_id) REFERENCES obj (id), 
	 FOREIGN KEY(parent_id) REFERENCES obj (id)
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

