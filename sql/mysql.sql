CREATE TABLE templates (
	id INTEGER NOT NULL, 
	name VARCHAR(50), 
	data TEXT, 
	modified TIMESTAMP, 
	PRIMARY KEY (id), 
	 CONSTRAINT template_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE obj (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	discriminator TINYINT, 
	owner_id INTEGER, 
	parent_id INTEGER, 
	superparent_id INTEGER, 
	PRIMARY KEY (id), 
	 CONSTRAINT obj_discr FOREIGN KEY(discriminator) REFERENCES discriminator (id), 
	 CONSTRAINT obj_owner FOREIGN KEY(owner_id) REFERENCES obj (id), 
	 CONSTRAINT obj_super FOREIGN KEY(superparent_id) REFERENCES obj (id), 
	 CONSTRAINT obj_parent FOREIGN KEY(parent_id) REFERENCES obj (id)
);
CREATE TABLE users (
	id INTEGER NOT NULL, 
	username VARCHAR(30) NOT NULL, 
	first_name VARCHAR(30), 
	last_name VARCHAR(30), 
	email VARCHAR(100), 
	password VARCHAR(30) NOT NULL, 
	first_login DATETIME NOT NULL, 
	last_login DATETIME, 
	PRIMARY KEY (id), 
	 CONSTRAINT user_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE site_users (
	site_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	 CONSTRAINT site_users_user FOREIGN KEY(user_id) REFERENCES obj (id), 
	 CONSTRAINT site_users_site FOREIGN KEY(site_id) REFERENCES obj (id), 
	 UNIQUE (site_id, user_id)
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
CREATE TABLE groupmembers (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER, 
	group_id INTEGER, 
	excluded BOOL NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT member_group FOREIGN KEY(group_id) REFERENCES obj (id), 
	 CONSTRAINT member_user FOREIGN KEY(user_id) REFERENCES obj (id)
);
CREATE TABLE wikipage (
	id INTEGER NOT NULL, 
	name VARCHAR(50), 
	data TEXT, 
	modified TIMESTAMP, 
	PRIMARY KEY (id), 
	 CONSTRAINT template_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE verifiers (
	id INTEGER NOT NULL, 
	base_id TINYINT, 
	code VARCHAR(50) NOT NULL, 
	added DATETIME NOT NULL, 
	repeated DATETIME, 
	timeout DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT verifier_id FOREIGN KEY(id) REFERENCES obj (id), 
	 UNIQUE (code), 
	 CONSTRAINT verifier_base FOREIGN KEY(base_id) REFERENCES verifierbase (id)
);
CREATE TABLE groups (
	id INTEGER NOT NULL, 
	name VARCHAR(30), 
	PRIMARY KEY (id), 
	 CONSTRAINT `Group_id` FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE discriminator (
	id TINYINT(1) NOT NULL AUTO_INCREMENT, 
	name VARCHAR(30) NOT NULL, 
	PRIMARY KEY (id), 
	 UNIQUE (name)
);
CREATE TABLE verifierbase (
	id TINYINT(1) NOT NULL AUTO_INCREMENT, 
	name VARCHAR(30) NOT NULL, 
	cls VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	 UNIQUE (name), 
	 UNIQUE (cls)
);
CREATE TABLE template_match (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	obj_id INTEGER NOT NULL, 
	template_id INTEGER NOT NULL, 
	discr TINYINT NOT NULL, 
	type TINYINT(1) NOT NULL, 
	inherit BOOL, 
	PRIMARY KEY (id), 
	 CONSTRAINT obj_templates_obj FOREIGN KEY(obj_id) REFERENCES obj (id), 
	 CONSTRAINT obj_templates_template FOREIGN KEY(template_id) REFERENCES templates (id), 
	 CONSTRAINT templatematch_discr FOREIGN KEY(discr) REFERENCES discriminator (id)
);
CREATE TABLE permissions (
	id INTEGER NOT NULL, 
	`right` INTEGER NOT NULL, 
	inherit BOOL, 
	discr TINYINT NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT obj_discr FOREIGN KEY(discr) REFERENCES discriminator (id), 
	 CONSTRAINT `Group_id` FOREIGN KEY(id) REFERENCES obj (id)
);

