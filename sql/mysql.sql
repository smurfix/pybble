CREATE TABLE comment (
	id INTEGER NOT NULL, 
	name VARCHAR(250), 
	data TEXT, 
	added TIMESTAMP, 
	renderer_id TINYINT, 
	PRIMARY KEY (id), 
	 CONSTRAINT comment_id FOREIGN KEY(id) REFERENCES obj (id), 
	 CONSTRAINT cmt_renderer FOREIGN KEY(renderer_id) REFERENCES renderer (id)
);
CREATE TABLE template_match (
	id INTEGER NOT NULL, 
	data TEXT, 
	modified TIMESTAMP, 
	discr TINYINT NOT NULL, 
	detail TINYINT(1) NOT NULL, 
	inherit BOOL, 
	PRIMARY KEY (id), 
	 CONSTRAINT template_match_id FOREIGN KEY(id) REFERENCES obj (id), 
	 CONSTRAINT templatematch_discr FOREIGN KEY(discr) REFERENCES discriminator (id)
);
CREATE TABLE demo (
	id INTEGER NOT NULL, 
	name VARCHAR(250), 
	PRIMARY KEY (id), 
	 CONSTRAINT demo_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE verein_member (
	id INTEGER NOT NULL, 
	mitglied_id INTEGER, 
	aktiv BOOL, 
	PRIMARY KEY (id), 
	 CONSTRAINT vereinmember_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE books (
	id INTEGER NOT NULL, 
	title VARCHAR(250), 
	author VARCHAR(250), 
	upc VARCHAR(15), 
	info TEXT, 
	PRIMARY KEY (id), 
	 CONSTRAINT book_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE wanttracking (
	id INTEGER NOT NULL, 
	discr TINYINT, 
	email BOOL NOT NULL, 
	track_new BOOL NOT NULL, 
	track_mod BOOL NOT NULL, 
	track_del BOOL NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT wanttracking_id FOREIGN KEY(id) REFERENCES obj (id), 
	 CONSTRAINT wanttracking_discr FOREIGN KEY(discr) REFERENCES discriminator (id)
);
CREATE TABLE vereinacct (
	id INTEGER NOT NULL, 
	accountdb VARCHAR(30), 
	accountnr INTEGER, 
	PRIMARY KEY (id), 
	 CONSTRAINT vereinacct_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE discriminator (
	id TINYINT(1) NOT NULL AUTO_INCREMENT, 
	name VARCHAR(30) NOT NULL, 
	display_name VARCHAR(50), 
	infotext VARCHAR(250), 
	PRIMARY KEY (id), 
	 UNIQUE (name)
);
CREATE TABLE staticfile (
	id INTEGER NOT NULL, 
	path VARCHAR(200) NOT NULL, 
	modified TIMESTAMP, 
	PRIMARY KEY (id), 
	 CONSTRAINT staticfile_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE wikipage (
	id INTEGER NOT NULL, 
	name VARCHAR(50), 
	data TEXT, 
	modified TIMESTAMP, 
	mainpage BOOL NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT wikipage_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE mimeext (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	mime_id INTEGER, 
	ext VARCHAR(10) NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT mimetype_id FOREIGN KEY(mime_id) REFERENCES mimetype (id), 
	 UNIQUE (ext)
);
CREATE TABLE breadcrumbs (
	id INTEGER NOT NULL, 
	discr TINYINT NOT NULL, 
	visited TIMESTAMP, 
	PRIMARY KEY (id), 
	 CONSTRAINT breadcrumb_id FOREIGN KEY(id) REFERENCES obj (id), 
	 CONSTRAINT breadcrumb_discr FOREIGN KEY(discr) REFERENCES discriminator (id)
);
CREATE TABLE storage (
	id INTEGER NOT NULL, 
	name VARCHAR(250) NOT NULL, 
	path VARCHAR(250) NOT NULL, 
	url VARCHAR(250) NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT storage_id FOREIGN KEY(id) REFERENCES obj (id), 
	 UNIQUE (url), 
	 UNIQUE (name), 
	 UNIQUE (path)
);
CREATE TABLE sites (
	id INTEGER NOT NULL, 
	domain VARCHAR(100) NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	tracked DATETIME NOT NULL, 
	storage_id INTEGER, 
	PRIMARY KEY (id), 
	 CONSTRAINT site_id FOREIGN KEY(id) REFERENCES obj (id), 
	 UNIQUE (domain), 
	 UNIQUE (name), 
	 CONSTRAINT site_storage FOREIGN KEY(storage_id) REFERENCES obj (id)
);
CREATE TABLE bindata (
	id INTEGER NOT NULL, 
	mime_id INTEGER, 
	name VARCHAR(50) NOT NULL, 
	hash VARCHAR(30) NOT NULL, 
	timestamp TIMESTAMP, 
	PRIMARY KEY (id), 
	 CONSTRAINT bindata_id FOREIGN KEY(id) REFERENCES obj (id), 
	 UNIQUE (hash), 
	 CONSTRAINT bindata_mimeid FOREIGN KEY(mime_id) REFERENCES mimetype (id)
);
CREATE TABLE bookwant (
	id INTEGER NOT NULL, 
	requested DATETIME, 
	PRIMARY KEY (id), 
	 CONSTRAINT bookwant_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE templates (
	id INTEGER NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	data TEXT, 
	modified TIMESTAMP, 
	PRIMARY KEY (id), 
	 CONSTRAINT template_id FOREIGN KEY(id) REFERENCES obj (id)
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
	cur_login DATETIME, 
	feed_age TINYINT NOT NULL, 
	feed_pass VARCHAR(30), 
	feed_read DATETIME, 
	PRIMARY KEY (id), 
	 CONSTRAINT user_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE usertracking (
	id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT usertracker_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE deleted (
	id INTEGER NOT NULL, 
	comment VARCHAR(200), 
	old_superparent_id INTEGER, 
	old_owner_id INTEGER, 
	timestamp TIMESTAMP, 
	PRIMARY KEY (id), 
	 CONSTRAINT delobj_owner FOREIGN KEY(old_owner_id) REFERENCES obj (id), 
	 CONSTRAINT delete_id FOREIGN KEY(id) REFERENCES obj (id), 
	 CONSTRAINT delobj_super FOREIGN KEY(old_superparent_id) REFERENCES obj (id)
);
CREATE TABLE groupmembers (
	id INTEGER NOT NULL, 
	excluded BOOL NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT member_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE verein (
	id INTEGER NOT NULL, 
	name VARCHAR(250), 
	`database` VARCHAR(30), 
	PRIMARY KEY (id), 
	 CONSTRAINT verein_id FOREIGN KEY(id) REFERENCES obj (id)
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
	 CONSTRAINT group_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE verifierbase (
	id TINYINT(1) NOT NULL AUTO_INCREMENT, 
	name VARCHAR(30) NOT NULL, 
	cls VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	 UNIQUE (name), 
	 UNIQUE (cls)
);
CREATE TABLE permissions (
	id INTEGER NOT NULL, 
	`right` INTEGER NOT NULL, 
	inherit BOOL, 
	discr TINYINT NOT NULL, 
	new_discr TINYINT, 
	PRIMARY KEY (id), 
	 CONSTRAINT permission_id FOREIGN KEY(id) REFERENCES obj (id), 
	 CONSTRAINT permission_discr FOREIGN KEY(discr) REFERENCES discriminator (id), 
	 CONSTRAINT permission_new_discr FOREIGN KEY(new_discr) REFERENCES discriminator (id)
);
CREATE TABLE mimetype (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(30) NOT NULL, 
	typ VARCHAR(15) NOT NULL, 
	subtyp VARCHAR(15) NOT NULL, 
	ext VARCHAR(15) NOT NULL, 
	PRIMARY KEY (id), 
	 UNIQUE (name)
);
CREATE TABLE tracking (
	id INTEGER NOT NULL, 
	timestamp TIMESTAMP, 
	PRIMARY KEY (id), 
	 CONSTRAINT tracker_id FOREIGN KEY(id) REFERENCES obj (id)
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
	 CONSTRAINT obj_parent FOREIGN KEY(parent_id) REFERENCES obj (id), 
	 CONSTRAINT obj_super FOREIGN KEY(superparent_id) REFERENCES obj (id)
);
CREATE TABLE site_users (
	site_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	 CONSTRAINT site_users_site FOREIGN KEY(site_id) REFERENCES obj (id), 
	 UNIQUE (site_id, user_id), 
	 CONSTRAINT site_users_user FOREIGN KEY(user_id) REFERENCES obj (id)
);
CREATE TABLE bookstore (
	id INTEGER NOT NULL, 
	name VARCHAR(250), 
	info VARCHAR(250), 
	PRIMARY KEY (id), 
	 CONSTRAINT bookstore_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE changes (
	id INTEGER NOT NULL, 
	timestamp TIMESTAMP, 
	data TEXT, 
	comment VARCHAR(200), 
	PRIMARY KEY (id), 
	 CONSTRAINT change_id FOREIGN KEY(id) REFERENCES obj (id)
);
CREATE TABLE renderer (
	id TINYINT(1) NOT NULL AUTO_INCREMENT, 
	name VARCHAR(30) NOT NULL, 
	cls VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	 UNIQUE (name), 
	 UNIQUE (cls)
);

