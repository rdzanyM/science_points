
DROP TABLE IF EXISTS Monographs;
CREATE TABLE Monographs (
	id integer PRIMARY KEY AUTOINCREMENT,
	DOI string,
	publisher_name string
);

DROP TABLE IF EXISTS Conferences;
CREATE TABLE Conferences (
	id integer PRIMARY KEY AUTOINCREMENT,
	title string
);

DROP TABLE IF EXISTS Journals;
CREATE TABLE Journals (
	id integer PRIMARY KEY AUTOINCREMENT,
	title string
);

DROP TABLE IF EXISTS JournalDatePoints;
CREATE TABLE JournalDatePoints (
	journal_id integer,
	starting_date date,
	points integer
);

DROP TABLE IF EXISTS MonographDatePoints;
CREATE TABLE MonographDatePoints (
	monograph_id integer,
	government_statement_id integer,
	points integer
);

DROP TABLE IF EXISTS ConferenceDatePoints;
CREATE TABLE ConferenceDatePoints (
	conference_id integer,
	starting_date date,
	points integer
);

DROP TABLE IF EXISTS GovernmentStatements;
CREATE TABLE GovernmentStatements (
	id integer PRIMARY KEY AUTOINCREMENT,
	url string,
	title string,
	starting_date date
);

DROP TABLE IF EXISTS Domains;
CREATE TABLE Domains (
	id integer PRIMARY KEY AUTOINCREMENT,
	name string
);

DROP TABLE IF EXISTS JournalDomains;
CREATE TABLE JournalDomains (
	journal_id integer,
	domain_id integer
);

DROP TABLE IF EXISTS MonographDomains;
CREATE TABLE MonographDomains (
	monograph_id integer,
	domain_id integer
);

DROP TABLE IF EXISTS ConferenceDomains;
CREATE TABLE ConferenceDomains (
	conference_id integer,
	domain_id integer
);

