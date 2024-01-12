"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const sqlite3_1 = __importDefault(require("sqlite3"));
const app = (0, express_1.default)();
const PORT = 3000;
let db = new sqlite3_1.default.Database('./main/webapp/instance/data.db', (err) => {
    if (err) {
        console.error(err.message);
    }
    console.log('Connected to the SQLite database.');
});
app.use(express_1.default.static('public')); // Serve static files from 'public' directory
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
