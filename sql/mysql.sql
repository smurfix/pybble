CREATE TABLE urls (
	added DATETIME, 
	uid VARCHAR(140) NOT NULL, 
	public BOOL, 
	target VARCHAR(500), 
	PRIMARY KEY (uid)
);

