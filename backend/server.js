const express = require('express');
const cors = require('cors');
const bcrypt = require('bcrypt');
const db = require('./config/db');

const app = express();
app.use(cors());
app.use(express.json());

// User Registration
app.post('/api/register', async (req, res) => {
    try {
        const { email, password } = req.body;
        const hashedPassword = await bcrypt.hash(password, 10);
        
        const query = 'INSERT INTO users (email, password_hash) VALUES (?, ?)';
        db.query(query, [email, hashedPassword], (error, results) => {
            if (error) {
                res.status(400).json({ error: 'Registration failed' });
                return;
            }
            res.json({ message: 'User registered successfully' });
        });
    } catch (error) {
        res.status(500).json({ error: 'Server error' });
    }
});

// Daily Check-in
app.post('/api/checkin', (req, res) => {
    const { userId, weight, sleep, stress, energy, soreness } = req.body;
    
    const query = `INSERT INTO daily_checkins 
        (user_id, weight, sleep_quality, stress_level, energy_level, soreness_level) 
        VALUES (?, ?, ?, ?, ?, ?)`;
        
    db.query(query, [userId, weight, sleep, stress, energy, soreness], 
        (error, results) => {
            if (error) {
                res.status(400).json({ error: 'Check-in failed' });
                return;
            }
            res.json({ message: 'Check-in recorded successfully' });
    });
});

// Get User's Check-ins
app.get('/api/checkins/:userId', (req, res) => {
    const query = 'SELECT * FROM daily_checkins WHERE user_id = ? ORDER BY check_in_date DESC';
    db.query(query, [req.params.userId], (error, results) => {
        if (error) {
            res.status(400).json({ error: 'Failed to fetch check-ins' });
            return;
        }
        res.json(results);
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
