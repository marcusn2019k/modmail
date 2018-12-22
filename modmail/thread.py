import asyncio
import re

import discord 
from .utils import authorized

class Thread:


    def __init__(self, bot, user):
        self.bot = bot
        self.user = user
        self.channel = None

    @classmethod
    def get(cls, channel_id):
        """Returns an existing thread."""
        return cls.cache[channel_id]
    
    @classmethod
    async def from_channel(cls, bot, channel):
        user_id = await bot.find_user_id_from_channel(channel)
        if not user_id:
            raise ValueError('Not a thread')
        user = bot.get_user(user_id)
        self = cls(bot, user)
        self.channel = channel
        return self

    @classmethod
    @authorized
    async def create(cls, bot, user, *, creator=None):
        """Creates a modmail thread if it does not exist"""

        self = cls(bot, user)

        categ = self.bot.modmail_category
        archives = self.bot.archive_category
        guild = self.bot.guild

        topic = f'User ID: {user.id}'
        channel = discord.utils.get(self.bot.guild.text_channels, topic=topic)
        print('creating thread')
        print(channel)
        
        em = discord.Embed(title='Thanks for the message!')
        em.description = 'The moderation team will get back to you as soon as possible!'
        em.color = discord.Color.green()
        
        info_description = None

        if creator: # created through contact command
            em.title ='Modmail thread started'
            em.description = f'{creator.mention} has started a modmail thread with you.'
            info_description = f'{creator.mention} has created a thread with {user.mention}'

        mention = (self.bot.config.get('MENTION') or '@here') if not creator else None

        if channel is not None and channel.category is archives: # channel exists but thread appears to be closed 
            if creator: 
                await user.send(embed=em)
            await channel.edit(category=categ)
            await channel.send(mention, embed=self.bot.format_info(user, info_description))
        else:
            await user.send(embed=em)
            channel = await guild.create_text_channel(
                name=self.bot.format_name(user, guild.text_channels),
                category=categ
                )
            await channel.edit(topic=topic)
            await channel.send(mention, embed=self.bot.format_info(user, info_description))
        
        self.channel = channel

        return self
    
    async def reply(self, message):
        """Replies to a modmail thread"""

        if not self.user:
            return await message.channel.send('This user is unreachable (No mutual servers).')

        # send a formatted message to both thread channel and user
        await asyncio.gather(
            self.send(message, from_mod=True),
            self.send(message, recipient=self.user, from_mod=True)
        )
        
    async def send(self, message, *, recipient=None, from_mod=False, delete_message=False):
        """Sends a formatted message to the recipient provided."""
        author = message.author

        em = discord.Embed()
        em.description = message.content
        em.timestamp = message.created_at

        image_types = ['.png', '.jpg', '.gif', '.jpeg', '.webp']
        is_image_url = lambda u: any(urlparse(u).path.endswith(x) for x in image_types)

        delete_message = not bool(message.attachments) # you cant delete the original message if there are attachments
        attachments = list(filter(lambda a: not is_image_url(a.url), message.attachments))

        image_urls = [a.url for a in message.attachments]
        image_urls.extend(re.findall(r'(https?://[^\s]+)', message.content))
        image_urls = list(filter(is_image_url, image_urls))

        if image_urls:
            em.set_image(url=image_urls[0])

        if attachments:
            att = attachments[0]
            em.add_field(name='File Attachment', value=f'[{att.filename}]({att.url})')

        if from_mod:
            em.color=discord.Color.green()
            em.set_author(name=str(author), icon_url=author.avatar_url)
            em.set_footer(text=f'Moderator - {message.id}')
        else:
            em.color=discord.Color.gold()
            em.set_author(name=str(author), icon_url=author.avatar_url)
            em.set_footer(text='User')

        recipient = recipient or self.channel
        await recipient.send(embed=em)

        if delete_message:
            try:
                await message.delete()
            except:
                pass
