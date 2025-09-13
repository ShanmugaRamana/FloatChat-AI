// --- 1. Import Dependencies ---
const express = require('express');
const path = require('path');
// dotenv loads environment variables from the .env file
require('dotenv').config();

// --- 2. Initialize the Express App ---
const app = express();
// Set the port from the .env file, with a fallback to 3000
const PORT = process.env.PORT || 3000;

// --- 3. Configure Middleware & Templating Engine ---
// Set EJS as the view (template) engine
app.set('view engine', 'ejs');
// Tell Express where to find the template files (in the 'views' directory)
app.set('views', path.join(__dirname, 'views'));

// Tell Express to serve static files (CSS, client-side JS) from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// --- 4. Import and Use Routes ---
// Import the routes defined in routes/index.js
const indexRoutes = require('./routes/index');
// Tell the app to use these routes for any incoming requests
app.use('/', indexRoutes);

// --- 5. Start the Server ---
app.listen(PORT, () => {
    console.log(`🚀 FloatChatWeb server is running on http://localhost:${PORT}`);
});