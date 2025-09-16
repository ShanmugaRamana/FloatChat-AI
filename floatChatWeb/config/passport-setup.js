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
            let user = await User.findOne({ email: profile.emails[0].value });

            if (user) {
                // LOGGING: See if an existing user was found
                console.log('✅ Existing user found in DB:', user.email);
                return done(null, user);
            } else {
                // LOGGING: Confirm that a new user is being processed
                console.log('- - -> New user detected. Redirecting to complete signup for:', profile.emails[0].value);
                
                req.session.googleProfile = {
                    username: profile.displayName,
                    email: profile.emails[0].value,
                    isVerified: true
                };
                return done(null, false, { message: 'COMPLETE_SIGNUP' });
            }
        } catch (error) {
            console.error('Error in Google Strategy:', error);
            return done(error, false);
        }
    })
);