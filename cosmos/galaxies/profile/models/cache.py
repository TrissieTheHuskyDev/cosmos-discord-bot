from discord.ext import tasks

from .profiles import CosmosUserProfile, GuildMemberProfile


class ProfileCache(object):

    DEFAULT_PROJECTION = {
        "guilds": False,
    }

    def __init__(self, plugin):
        self.plugin = plugin
        self.bot = self.plugin.bot
        self._redis = None
        self.lfu = self.bot.cache.lfu(self.plugin.data.profile.cache_max_size)
        self.collection = self.plugin.collection
        self.update_database_task = tasks.loop(
            seconds=self.plugin.data.profile.update_task_cooldown
        )(self.__update_database)
        # Start above background task.
        # self.update_database_task.start()    # Start the task on_ready.
        # self.bot.loop.create_task(self.__update_database())
        # self.bot.loop.create_task(self.__get_redis_client())
        self.bot.add_listener(self.on_ready)
        self.bot.add_listener(self.on_disconnect)

    async def on_ready(self):
        self.update_database_task.start()

    async def on_disconnect(self):
        self.update_database_task.cancel()

    async def __get_redis_client(self):
        await self.bot.wait_until_ready()
        self._redis = self.bot.cache.redis

    async def prepare(self):
        self.bot.log.info("Preparing profile caches.")
        # await self.__get_redis_client()
        profile_documents = dict()
        profiles_data = await self.collection.find(
            {}, projection=self.DEFAULT_PROJECTION).to_list(self.plugin.data.profile.cache_max_size)
        for profile_document in profiles_data:
            profile = CosmosUserProfile.from_document(self.plugin, profile_document)
            user_id = int(profile_document.get("user_id"))  # bson.int64.Int64 to int
            profile_documents[user_id] = profile
        # await self._redis.set_objects(self.__collection_name, profile_documents)
        self.lfu.update(profile_documents)
        # profile_count = await self._redis.hlen(self.__collection_name)
        profile_count = self.lfu.currsize
        self.bot.log.info(f"Loaded {profile_count} profiles to cache.")

    async def get_profile(self, user_id: int) -> CosmosUserProfile:
        # profile = await self._redis.get_object(self.__collection_name, user_id)
        profile = self.lfu.get(user_id)
        if not profile:
            profile_document = await self.collection.find_one({"user_id": user_id}, projection=self.DEFAULT_PROJECTION)
            if profile_document:
                profile = CosmosUserProfile.from_document(self.plugin, profile_document)
                # await self._redis.set_object(self.__collection_name, user_id, profile)
                self.lfu.set(user_id, profile)
        return profile

    async def get_guild_profile(self, user_id: int, guild_id: int) -> GuildMemberProfile:
        profile = await self.get_profile(user_id)
        if profile:
            return await profile.get_guild_profile(guild_id)

    async def create_profile(self, user_id: int) -> CosmosUserProfile:
        document_filter = {"user_id": user_id}
        profile = CosmosUserProfile.from_document(self.plugin, document_filter)
        self.lfu.set(user_id, profile)    # Before db API call to prevent it from firing many times.
        if not await self.collection.find_one(document_filter):
            # To handle rare cases when this method still gets invoked multiple times.
            await self.collection.insert_one(document_filter)
        return profile

    async def give_assets(self, message):
        assets = []
        profile = await self.get_profile(message.author.id)
        if not profile:
            # embed = self.bot.theme.embeds.one_line.primary(f"Welcome {message.author.name}. Creating your profile!")
            # await message.channel.send(embed=embed)
            profile = await self.create_profile(message.author.id)

        if not profile.in_boson_buffer:
            assets.append(profile.give_default_bosons())

        guild_profile = await profile.get_guild_profile(message.guild.id)
        if not guild_profile.in_xp_buffer:
            assets.append((guild_profile.give_xp(message.channel)))

        for asset in assets:
            self.bot.loop.create_task(asset)

    async def __update_database(self):
        for profile in self.lfu.values():
            self.plugin.batch.queue_update(*profile.to_update_document())
        await self.plugin.batch.write(ordered=False)
