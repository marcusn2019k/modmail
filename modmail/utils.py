
class BlockedUser(Exception):
    pass

def authorized(func):
    def wrapper(cls, bot, user, **kwargs):
        if user.id in bot.blocked:
            raise BlockedUser('User is blocked')
        return func(cls, bot, user, **kwargs)
    return wrapper
