// config/passport-setup.js
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const User = require('../models/User');

passport.serializeUser((user, done) => {
    done(null, user.id);
});

passport.deserializeUser((id, done) => {
    User.findById(id).then((user) => {
        done(null, user);
    });
});

passport.use(
    new GoogleStrategy({
        clientID: process.env.GOOGLE_CLIENT_ID,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        callbackURL: process.env.CALLBACK_URL, // <-- USE THE ENV VARIABLE
        passReqToCallback: true // Pass the request object to the callback
    },
    async (req, accessToken, refreshToken, profile, done) => {
        try {
            // Check if user already exists
            let user = await User.findOne({ email: profile.emails[0].value });

            if (user) {
                // User exists, log them in
                return done(null, user);
            } else {
                // User does not exist, this is their first time signing up with Google.
                // We need to ask them for a password.
                // Store Google profile in session temporarily.
                req.session.googleProfile = {
                    username: profile.displayName,
                    email: profile.emails[0].value,
                    isVerified: true // Google emails are already verified
                };
                // Redirect to a page to complete signup by adding a password.
                // We pass 'false' for the user since they aren't created yet.
                return done(null, false, { message: 'COMPLETE_SIGNUP' });
            }
        } catch (error) {
            return done(error, false);
        }
    })
);