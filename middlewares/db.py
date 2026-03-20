from aiogram import BaseMiddleware

class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_factory):
        super().__init__()
        self.session_factory = session_factory
    # когда он вызывается, он передает в s сессию для каждого хендлера и колбека
    async def __call__(self, handler, event, data):
        async with self.session_factory() as session:
            data["s"] = session
            return await handler(event, data)