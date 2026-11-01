# BMserver - Coffee

Application for rendering webpage with the daily sponsors for the coffee in a Beis Midrash.
Includes admin dashboard for easy managing of displayed names and information.

## Admin settings

The admin settings panel saves display preferences and account credentials to
`settings.json` in the project directory (or the path specified by
`SETTINGS_PATH`). Display preferences are stored for future use and are not yet
applied to the public display page. Passwords are stored as Werkzeug password
hashes, not as plain text; `settings.json` is excluded from version control.

Changing the admin username or password requires the current password. New
passwords must be at least 8 characters. If no settings file exists, the
`ADMIN_USER` and `ADMIN_PASS` environment variables (or the development
defaults) are used to initialize account settings.
