class UserService:

    @staticmethod
    async def update_description(user_id: int, description: str):
        # query = """
        # UPDATE users
        # SET description = $1
        # WHERE telegram_id = $2
        # """

        # await db.execute(query, description, user_id)