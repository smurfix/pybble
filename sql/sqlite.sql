CREATE TABLE urls (
	added TIMESTAMP, 
	uid VARCHAR(140) NOT NULL, 
	public BOOLEAN, 
	target VARCHAR(500), 
	PRIMARY KEY (uid)
);

