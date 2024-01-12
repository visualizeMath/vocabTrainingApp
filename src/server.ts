import express from 'express';
import sqlite3 from 'sqlite3';

const app = express();
const PORT = 3000;

let db = new sqlite3.Database('./main/webapp/instance/data.db', (err) => {
    if (err) {
        console.error(err.message);
    }
    console.log('Connected to the SQLite database.');
});

app.use(express.static('public')); // Serve static files from 'public' directory

app.get('/data', (req, res) => {
    const sql = `SELECT * FROM language_data WHERE in_dictionary = 1`;

    db.all(sql, [], (err, rows) => {
        if (err) {
            res.status(500).send('Error fetching data');
            return;
        }
        res.json(rows);
    });
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
