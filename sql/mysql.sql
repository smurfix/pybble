CREATE TABLE site_users (
	site_id INTEGER, 
	user_id INTEGER, 
	 FOREIGN KEY(site_id) REFERENCES obj (id), 
	 FOREIGN KEY(user_id) REFERENCES obj (id)
);
CREATE TABLE obj (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	discriminator INTEGER, 
	owner_id INTEGER, 
	parent_id INTEGER, 
	superparent_id INTEGER, 
	PRIMARY KEY (id), 
	 FOREIGN KEY(owner_id) REFERENCES obj (id), 
	 FOREIGN KEY(superparent_id) REFERENCES obj (id), 
	 FOREIGN KEY(parent_id) REFERENCES obj (id)
);
CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(30), 
	first_name VARCHAR(30), 
	last_name VARCHAR(30), 
	email VARCHAR(100), 
	password VARCHAR(30), 
	verified BOOL, 
	first_login DATETIME, 
	last_login DATETIME, 
	user_id INTEGER, 
	obj_id INTEGER, 
	`right` INTEGER, 
	PRIMARY KEY (id), 
	 FOREIGN KEY(id) REFERENCES obj (id), 
	 FOREIGN KEY(obj_id) REFERENCES obj (id), 
	 FOREIGN KEY(user_id) REFERENCES obj (id)
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
CREATE TABLE sites (
	id INTEGER NOT NULL, 
	domain VARCHAR(100), 
	name VARCHAR(50), 
	PRIMARY KEY (id), 
	 FOREIGN KEY(id) REFERENCES obj (id)
);

