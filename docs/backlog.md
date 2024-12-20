Potential Issues and Recommendations:

Avoid calling logging.basicConfig() after you have a more advanced setup in configure_logging(). configure_logging() should be the one-stop shop for logging config.
If sqlalchemy logging is too noisy, reduce its level from DEBUG to something higher (like INFO or WARN).
If you want less verbose logs in production, you could add environment-based checks inside configure_logging() to set levels differently based on env.DEBUG_MODE.
