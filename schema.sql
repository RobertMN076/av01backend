DROP TABLE IF EXISTS task;       -- Drop 'task' first, as it depends on 'tasklist'
DROP TABLE IF EXISTS tasklist;   -- Drop 'tasklist' next, as it depends on 'user'
DROP TABLE IF EXISTS user;       -- Drop 'user' last

CREATE TABLE user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE tasklist (
    id INT PRIMARY KEY AUTO_INCREMENT,
    author_id INT NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    FOREIGN KEY (author_id) REFERENCES user (id) ON DELETE CASCADE
);

CREATE TABLE task (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tasklist_id INT NOT NULL,
    body TEXT NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE, -- MySQL uses TRUE/FALSE or 0/1 for BOOLEAN
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tasklist_id) REFERENCES tasklist(id) ON DELETE CASCADE
);