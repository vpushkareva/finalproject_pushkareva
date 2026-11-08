import logging


def log_action(action, verbose=False):
    """Пишет операцию в лог уровня INFO, исключения пробрасывает дальше."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("valutatrade")
            user = args[0] if args else None
            username = getattr(user, "username", user)
            currency = args[1] if len(args) > 1 else kwargs.get("currency_code", "")
            amount = args[2] if len(args) > 2 else kwargs.get("amount", "")

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                logger.info(
                    "%s user='%s' currency='%s' amount=%s result=ERROR "
                    "error_type=%s error='%s'",
                    action, username, currency, amount, type(e).__name__, e,
                )
                raise

            extra = ""
            if verbose and isinstance(result, dict) and "before" in result:
                extra = (f" balance: {result['before']:.4f}→{result['after']:.4f}")
            rate = result.get("rate") if isinstance(result, dict) else None
            logger.info(
                "%s user='%s' currency='%s' amount=%s rate=%s base='USD' "
                "result=OK%s",
                action, username, currency, amount,
                f"{rate:,.2f}" if rate else "-", extra,
            )
            return result

        return wrapper

    return decorator
