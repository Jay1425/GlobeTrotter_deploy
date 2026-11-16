# Email configuration

Configure email credentials through your deployment platform's environment settings.
Do not commit real passwords, app passwords, API keys, or OAuth secrets.

Required environment variables:

```dotenv
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your-sender-email@example.com
MAIL_PASSWORD=your-google-app-password
MAIL_DEFAULT_SENDER=your-sender-email@example.com
```

For Gmail, create an application-specific password in your Google Account security settings.
If a credential has ever been committed, revoke it and create a replacement before deployment.
