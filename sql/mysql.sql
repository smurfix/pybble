CREATE TABLE site_users (
	site_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	 CONSTRAINT site_users_site FOREIGN KEY(site_id) REFERENCES obj (id), 
	 CONSTRAINT site_users_user FOREIGN KEY(user_id) REFERENCES obj (id), 
	 UNIQUE (site_id, user_id)
);
CREATE TABLE obj (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	discriminator INTEGER, 
	owner_id INTEGER, 
	parent_id INTEGER, 
	superparent_id INTEGER, 
	PRIMARY KEY (id), 
	 CONSTRAINT obj_owner FOREIGN KEY(owner_id) REFERENCES obj (id), 
	 CONSTRAINT obj_parent FOREIGN KEY(parent_id) REFERENCES obj (id), 
	 CONSTRAINT obj_super FOREIGN KEY(superparent_id) REFERENCES obj (id)
);
CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(30) NOT NULL, 
	first_name VARCHAR(30), 
	last_name VARCHAR(30), 
	email VARCHAR(100), 
	password VARCHAR(30) NOT NULL, 
	verified BOOL NOT NULL, 
	first_login DATETIME NOT NULL, 
	last_login DATETIME, 
	user_id INTEGER NOT NULL, 
	obj_id INTEGER NOT NULL, 
	`right` INTEGER, 
	PRIMARY KEY (id), 
	 CONSTRAINT user_id FOREIGN KEY(id) REFERENCES obj (id), 
	 CONSTRAINT permission_user FOREIGN KEY(user_id) REFERENCES obj (id), 
	 CONSTRAINT permission_obj FOREIGN KEY(obj_id) REFERENCES obj (id)
);
CREATE TABLE urls (
	id INTEGER NOT NULL, 
	uid VARCHAR(140) NOT NULL, 
	target VARCHAR(500) NOT NULL, 
	added DATETIME NOT NULL, 
	public BOOL NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT `URL_id` FOREIGN KEY(id) REFERENCES obj (id), 
	 UNIQUE (uid)
);
CREATE TABLE sites (
	id INTEGER NOT NULL, 
	domain VARCHAR(100) NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT site_id FOREIGN KEY(id) REFERENCES obj (id), 
	 UNIQUE (domain), 
	 UNIQUE (name)
);

