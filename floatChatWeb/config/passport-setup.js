const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const User = require('../models/User');

passport.serializeUser((user, done) => {
    done(null, user.id);
});

passport.deserializeUser(async (id, done) => {
    try {
        const user = await User.findById(id);
        done(null, user);
    } catch (error) {
        done(error, null);
    }
});

passport.use(
    new GoogleStrategy({
        clientID: process.env.GOOGLE_CLIENT_ID,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        callbackURL: process.env.CALLBACK_URL,
        passReqToCallback: true
    },
    async (req, accessToken, refreshToken, profile, done) => {
        try {
            console.log('🔍 Google Strategy: Processing profile:', profile.emails[0].value);
            
            let user = await User.findOne({ email: profile.emails[0].value });

            if (user) {
                console.log('✅ Existing user found in DB:', user.email);
                return done(null, user);
            } else {
                console.log('➕ New user - storing in session:', profile.emails[0].value);
                
                // Store the profile in session for new users
                req.session.pendingGoogleUser = {
                    username: profile.displayName,
                    email: profile.emails[0].value,
                    isVerified: true
                };

                // Create a temporary user object to satisfy passport
                const tempUser = {
                    _id: 'temp_google_user',
                    isNewGoogleUser: true,
                    email: profile.emails[0].value
                };
                
                return done(null, tempUser);
            }
        } catch (error) {
            console.error('❌ Error in Google Strategy:', error);
            return done(error, false);
        }
    })
);