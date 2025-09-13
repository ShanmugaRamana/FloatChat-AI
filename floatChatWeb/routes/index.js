const express = require('express');
const router = express.Router();

// Define the route for the homepage ('/')
router.get('/', (req, res) => {
    // Pass the API URL from the environment to the template
    res.render('chat', { 
        apiBaseUrl: process.env.API_BASE_URL 
    });
});

// Export the router so it can be used by server.js
module.exports = router;