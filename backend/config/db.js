const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Create database directory if it doesn't exist
const dbDir = path.join(__dirname, '..', 'database');
const fs = require('fs');
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

// Set up the database path
const dbPath = path.join(dbDir, 'coach.db');

// Create connection to SQLite database
const db = new sqlite3.Database(dbPath, (error) => {
  if (error) {
    console.error('Error connecting to the database:', error);
    return;
  }
  console.log('Successfully connected to SQLite database at ' + dbPath);
  
  // Enable foreign keys
  db.run('PRAGMA foreign_keys = ON');
});

// Create wrapper for promises to make working with the database easier
const connection = {
  query: (sql, params = []) => {
    return new Promise((resolve, reject) => {
      if (sql.toLowerCase().startsWith('select')) {
        db.all(sql, params, (err, rows) => {
          if (err) {
            reject(err);
            return;
          }
          resolve([rows]);
        });
      } else {
        db.run(sql, params, function(err) {
          if (err) {
            reject(err);
            return;
          }
          resolve([{ affectedRows: this.changes, insertId: this.lastID }]);
        });
      }
    });
  },
  close: () => {
    return new Promise((resolve, reject) => {
      db.close((err) => {
        if (err) {
          reject(err);
          return;
        }
        resolve();
      });
    });
  }
};

module.exports = connection;
