import discord
import time # To auto remove birthday role on the next day.
from .utils.paginator import Pages # For making pages, requires the util!
from discord.ext import commands
from __main__ import send_cmd_help
from cogs.utils.dataIO import dataIO
from threading import Lock
import asyncio
import datetime

# Requires checks utility from:
# https://github.com/Rapptz/RoboDanny/tree/master/cogs/utils
from .utils import checks

import os #Used to create folder at first load.

#Global variables
keyBirthdayRole = "birthdayRole"
keyBirthdayUsers = "birthdayUsers"
keyBirthdateMonth = "birthdateMonth"
keyBirthdateDay = "birthdateDay"
keyIsAssigned = "isAssigned"
keyDateAssignedMonth = "dateAssignedMonth"
keyDateAssignedDay = "dateAssignedDay"
saveFolder = "data/lui-cogs/birthday/" #Path to save folder.
saveFile = "settings.json"

def checkFolder():
    """Used to create the data folder at first startup"""
    if not os.path.exists(saveFolder):
        print("Creating " + saveFolder + " folder...")
        os.makedirs(saveFolder)

def checkFiles():
    """Used to initialize an empty database at first startup"""
    
    f = saveFolder + saveFile
    if not dataIO.is_valid_json(f):
        print("Creating default birthday settings.json...")
        dataIO.save_json(f, {})
        
            
class Birthday_beta:
    """Adds a role to someone on their birthday, and automatically remove them from this role after the day is over."""


    def loadSettings(self):
        """Loads settings from the JSON file"""
        self.settings = dataIO.load_json(saveFolder+saveFile)
        
    def saveSettings(self):
        """Loads settings from the JSON file"""
        dataIO.save_json(saveFolder+saveFile, self.settings)

    #Class constructor
    def __init__(self, bot):
        self.bot = bot
        
        #The JSON keys for the settings:
        self.settingsLock = Lock()
        
        checkFolder()
        checkFiles()
        self.loadSettings()
        
    @commands.group(name="birthday", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(administrator=True)
    async def _birthday(self, ctx):
        """Birthday role assignment settings"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
    
    @_birthday.command(name="setrole", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(administrator=True)
    async def _birthdayRole(self, ctx, role: discord.Role):
        """Set the role to assign to a birthday user.  Make sure this role can be assigned
        and removed by the bot by placing it in the correct hierarchy location."""
        
        await self.bot.say(":white_check_mark: **Birthday - Role**: **{}** has been set as the birthday role!".format(role.name))
        
        # Acquire lock and save settings to file.
        self.settingsLock.acquire()
        try:
            self.loadSettings()
            if ctx.message.server.id not in self.settings:
                self.settings[ctx.message.server.id] = {}
            self.settings[ctx.message.server.id][keyBirthdayRole] = role.id
            self.saveSettings()
        except Exception as e:
            print("Birthday Error:")
            print(e)
        finally:
            self.settingsLock.release()
        return
    
    @_birthday.command(name="add", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(administrator=True)
    async def _birthdayAdd(self, ctx, user: discord.Member):
        """Add a user to the birthday role"""
        if ctx.message.server.id not in self.settings.keys():
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Add**: This server is not configured, please set a role!")
            return
        elif keyBirthdayRole not in self.settings[ctx.message.server.id].keys():
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Add**: Please set a role before adding a user!")
            return
        elif self.settings[ctx.message.server.id][keyBirthdayRole] is None:
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Add**: Please set a role before adding a user!")
            return
        
        try:
            # Find the Role object to add to the user.
            role = discord.utils.get(ctx.message.server.roles, id=self.settings[ctx.message.server.id][keyBirthdayRole])
            
            # Add the role to the user.
            await self.bot.add_roles(user, role)
        except discord.errors.Forbidden as e:
            print("Birthday Error:")
            print(e)
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Add**: Could not add **{}** to the list, the bot does not have enough permissions to do so!".format(user.name))
            return        
        
        # Save settings
        self.settingsLock.acquire()
        try:
            self.loadSettings()
            if ctx.message.server.id not in self.settings.keys():
                self.settings[ctx.message.server.id] = {}
            if keyBirthdayUsers not in self.settings[ctx.message.server.id].keys():
                self.settings[ctx.message.server.id][keyBirthdayUsers] = {}
            if user.id not in self.settings[ctx.message.server.id][keyBirthdayUsers].keys():
                self.settings[ctx.message.server.id][keyBirthdayUsers][user.id] = {}
            self.settings[ctx.message.server.id][keyBirthdayUsers][user.id][keyIsAssigned] = True
            self.settings[ctx.message.server.id][keyBirthdayUsers][user.id][keyDateAssignedMonth] = int(time.strftime("%m"))
            self.settings[ctx.message.server.id][keyBirthdayUsers][user.id][keyDateAssignedDay] = int(time.strftime("%d"))
            
            self.saveSettings()
        except Exception as e:
            print("Birthday Error:")
            print(e)
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Add**: Could not save **{}** to the list, but the role was assigned!  Please try again.".format(user.name))
        finally:
            self.settingsLock.release()
        await self.bot.say(":white_check_mark: **Birthday - Add**: Successfully added **{}** to the list and assigned the role.".format(user.name))
        
        return
          
    @_birthday.command(name="set", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(administrator=True)
    async def _birthdaySet(self, ctx, month: int, day: int, forUser: discord.Member = None):
        """Set a user's birth date.  Defaults to you.  On the day, the bot will automatically add the user to the birthday role."""
        if forUser is None:
            forUser = ctx.message.author 
   
        # Check inputs here.
        try:
            userBirthday = datetime.datetime(2020, month, day)
        except Exception as e:
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Set**: Please enter a valid birthday!")
            return

        # Check if server is initialized.
        if ctx.message.server.id not in self.settings.keys():
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Set**: This server is not configured, please set a role!")
            return
        elif keyBirthdayRole not in self.settings[ctx.message.server.id].keys():
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Set**: Please notify the server admin to set a role before continuing!")
            return
        elif self.settings[ctx.message.server.id][keyBirthdayRole] is None:
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Set**: Please notify the server admin to set a role before continuing!")
            return 
        
        # Save settings
        self.settingsLock.acquire()
        try:
            self.loadSettings()
            if ctx.message.server.id not in self.settings.keys():
                self.settings[ctx.message.server.id] = {}
            if keyBirthdayUsers not in self.settings[ctx.message.server.id].keys():
                self.settings[ctx.message.server.id][keyBirthdayUsers] = {}
            if forUser.id not in self.settings[ctx.message.server.id][keyBirthdayUsers].keys():
                self.settings[ctx.message.server.id][keyBirthdayUsers][forUser.id] = {}
            self.settings[ctx.message.server.id][keyBirthdayUsers][forUser.id][keyBirthdateMonth] = month
            self.settings[ctx.message.server.id][keyBirthdayUsers][forUser.id][keyBirthdateDay] = day
            
            self.saveSettings()
        except Exception as e:
            print("Birthday Error:")
            print(e)
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Set**: Could not save the birthday for **{0}** to the list.  Please try again!".format(forUser.name))
        finally:
            self.settingsLock.release()
        messageID = await self.bot.say(":white_check_mark: **Birthday - Set**: Successfully set **{0}**'s birthday to **{1:%B} {1:%d}**.  The role will be assigned automatically on this day.".format(forUser.name,userBirthday))
        
        await asyncio.sleep(5)

        await self.bot.edit_message(messageID, ":white_check_mark: **Birthday - Set**: Successfully set **{0}**'s birthday, and the role will be automatically assigned on the day.".format(forUser.name,userBirthday))

        return
    

    @_birthday.command(name="list", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(administrator=True)
    async def _birthdayList(self, ctx):
        """Lists the birthdays of users."""
        serverID = ctx.message.server.id
        serverName = ctx.message.server.name
        user = ctx.message.author

        sortedList = [] # List to sort by month, day.
        display = [] # List of text for paginator to use.  Will be constructed from sortedList.
        
        # Add only the users we care about (e.g. the ones that have birthdays set).
        for user, items in self.settings[serverID][keyBirthdayUsers].items():
            # Check if the birthdate keys exist, and they are not null.
            # If true, add an ID key and append to list.
            if keyBirthdateDay in items.keys() and keyBirthdateMonth in items.keys() and keyBirthdateDay is not None and keyBirthdateMonth is not None:
                items["ID"] = user
                sortedList.append(items)
        
        # Sort by month, day.
        sortedList.sort(key=lambda x: (x[keyBirthdateMonth], x[keyBirthdateDay]))
        
        for user in sortedList:
            # Get the associated user Discord object.
            userObject = discord.utils.get(ctx.message.server.members, id=user["ID"])
            
            # Skip if user is no longer in server.
            if userObject is None:
                continue
                
            # The year below is just there to accommodate leap year.  Not used anywhere else.
            userBirthday = datetime.datetime(2020, user[keyBirthdateMonth], user[keyBirthdateDay])
            text = "{0:%B} {0:%d}: {1}".format(userBirthday, userObject.name)
            display.append(text)

        p = Pages(self.bot,message=ctx.message,entries=display)
        p.embed.title = "Birthdays in **{}**".format(serverName)
        p.embed.colour = discord.Colour.red()
        await p.paginate()
        
        
    @_birthday.command(name="del", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(administrator=True)
    async def _birthdayDel(self, ctx, user: discord.Member):
        """Remove a user from the birthday role manually."""
        if ctx.message.server.id not in self.settings.keys():
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Delete**: This server is not configured, please set a role!")
            return
        elif keyBirthdayRole not in self.settings[ctx.message.server.id].keys():
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Delete**: Please set a role before removing a user from the role!")
            return
        elif self.settings[ctx.message.server.id][keyBirthdayRole] is None:
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Delete**: Please set a role before removing a user from the role!")
            return
        
        if ctx.message.server.id not in self.settings.keys():
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Delete**: The user is not on the list!")
            return
        if keyBirthdayUsers not in self.settings[ctx.message.server.id].keys():
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Delete**: The user is not on the list!")
            return
        if user.id not in self.settings[ctx.message.server.id][keyBirthdayUsers].keys():
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Delete**: The user is not on the list!")
            return
        

        try:
            # Find the Role object to add to the user.
            role = discord.utils.get(ctx.message.server.roles, id=self.settings[ctx.message.server.id][keyBirthdayRole])
            
            # Add the role to the user.
            await self.bot.remove_roles(user, role)
        except discord.errors.Forbidden as e:
            print("Birthday Error:")
            print(e)
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Delete**: Could not remove **{}** from the role, the bot does not have enough permissions to do so!".format(user.name))
            return
        
        self.settingsLock.acquire()
        try:
            self.loadSettings()
            self.settings[ctx.message.server.id][keyBirthdayUsers][user.id][keyIsAssigned] = False
            self.settings[ctx.message.server.id][keyBirthdayUsers][user.id][keyDateAssignedMonth] = None
            self.settings[ctx.message.server.id][keyBirthdayUsers][user.id][keyDateAssignedDay] = None
            
            self.saveSettings()
        except Exception as e:
            print("Birthday Error:")
            print(e)
            await self.bot.say(":negative_squared_cross_mark: **Birthday - Delete**: Could not remove **{}** from the list, but the role was removed!  Please try again.".format(user.name))
        finally:
            self.settingsLock.release()
        await self.bot.say(":white_check_mark: **Birthday - Delete**: Successfully removed **{}** from the list and removed the role.".format(user.name))
        
        return
        
    ########################################
    # Event loop - Try an absolute timeout #
    ########################################
    async def birthdayLoop(self):
        while self == self.bot.get_cog("Birthday_beta"):
            await asyncio.sleep(7.5*60)
            # print("Birthday: Performing daily sweep...")
            await self._dailySweep()
            # print("Birthday: Sleeping...")
            await asyncio.sleep(7.5*60)
            # print("Birthday: Performing daily add...")
            await self._dailyAdd()
            # print("Birthday: Sleeping...")
            
    async def _dailySweep(self):
        self.settingsLock.acquire()
        try:
            # Check each server.
            for server in self.settings:
                # Check to see if any users need to be removed.
                for user in self.settings[server][keyBirthdayUsers]:
                    # If assigned and the date is different than the date assigned, remove role.
                    try:
                        if self.settings[server][keyBirthdayUsers][user][keyIsAssigned]:
                            if self.settings[server][keyBirthdayUsers][user][keyDateAssignedMonth] != int(time.strftime("%m")) or self.settings[server][keyBirthdayUsers][user][keyDateAssignedDay] != int(time.strftime("%d")):
                                serverObject = discord.utils.get(self.bot.servers, id=server)
                                roleObject = discord.utils.get(serverObject.roles, id=self.settings[server][keyBirthdayRole])
                                userObject = discord.utils.get(serverObject.members, id=user)
                                
                                # Remove the role
                                try:
                                    await self.bot.remove_roles(userObject, roleObject)
                                    print("Birthday: Removing role from {}#{} ({})".format(userObject.name, userObject.discriminator, userObject.id))
                                except discord.errors.Forbidden as e:
                                    print("Birthday Error - Sweep Loop - Removing Role:")
                                    print(e)
                                    
                                # Update the list.
                                self.settings[server][keyBirthdayUsers][user][keyIsAssigned] = False
                                self.saveSettings()
                    except KeyError as e:
                        print("Birthday Error - Sweep Loop: Assigning key.")
                        print(e)
                        self.settings[server][keyBirthdayUsers][user][keyIsAssigned] = False
                        self.saveSettings()
                    except Exception as e:
                        # This happens if the isAssigned key is non-existent.
                        print("Birthday Error - Sweep Loop:")
                        print(e)            
        except Exception as e:
            print("Birthday Error - Sweep Loop:")
            print(e)
        finally:
            self.settingsLock.release()

    ##################################################################
    # Event Loop - Check to see if we need to add people to the role #
    ##################################################################
    async def _dailyAdd(self):
        self.settingsLock.acquire()
        try: 
            # Check each server.
            for server in self.settings:
                # Check to see if any users need to be removed.
                for user in self.settings[server][keyBirthdayUsers]:
                    # If today is the user's birthday, and the role is not assigned, assign the role.
                    # Get the current user, and make it a local variable to easily manipulate.
                    currentUser = self.settings[server][keyBirthdayUsers][user]

                    # Check if the keys for birthdate day and month exist, and that they're not null
                    if keyBirthdateDay in currentUser.keys() and keyBirthdateMonth in currentUser.keys() and currentUser[keyBirthdateDay] is not None and currentUser[keyBirthdateMonth] is not None:
                        birthdayDay = currentUser[keyBirthdateDay]
                        birthdayMonth = currentUser[keyBirthdateMonth]
                        
                        if birthdayMonth == int(time.strftime("%m")) and birthdayDay == int(time.strftime("%d")):
                            # Get the necessary Discord objects.
                            serverObject = discord.utils.get(self.bot.servers, id=server)
                            roleObject = discord.utils.get(serverObject.roles, id=self.settings[server][keyBirthdayRole])
                            userObject = discord.utils.get(serverObject.members, id=user)
                            
                            # Skip if user is no longer in server.
                            if userObject is None:
                                continue

                            try:
                                if not currentUser[keyIsAssigned] and userObject is not None:
                                    try:
                                        await self.bot.add_roles(userObject, roleObject)
                                        print("Birthday: Adding role to {}#{} ({})".format(userObject.name, userObject.discriminator, userObject.id))
                                        # Update the list.
                                        self.settings[server][keyBirthdayUsers][user][keyIsAssigned] = True
                                        self.settings[server][keyBirthdayUsers][user][keyDateAssignedMonth] = int(time.strftime("%m"))
                                        self.settings[server][keyBirthdayUsers][user][keyDateAssignedDay] = int(time.strftime("%d"))
                                        self.saveSettings() 
                                    except discord.errors.Forbidden as e:
                                        print("Birthday Error - Add Loop - Not Assigned If:")
                                        print(e)
                            except: # This key error will happen if the isAssigned key does not exist.
                                if userObject is not None:
                                    try:
                                        await self.bot.add_roles(userObject, roleObject)
                                        print("Birthday: Adding role to {}#{} ({})".format(userObject.name, userObject.discriminator, userObject.id))
                                        # Update the list.
                                        self.settings[server][keyBirthdayUsers][user][keyIsAssigned] = True
                                        self.settings[server][keyBirthdayUsers][user][keyDateAssignedMonth] = int(time.strftime("%m"))
                                        self.settings[server][keyBirthdayUsers][user][keyDateAssignedDay] = int(time.strftime("%d"))
                                        self.saveSettings()  
                                    except discord.errors.Forbidden as e:
                                        print("Birthday Error - Add Loop - Non-existent isAssigned Key If:")
                                        print(e)
                                        
                            # End try/except block for isAssigned key.
                        # End if to check if today is the user's birthday.
                    # End if to check for birthdateMonth and birthdateDay keys.
                # End user loop.
            # End server loop.
        except Exception as e:
            print("Birthday Error - Add Loop:")
            print(e)
        finally:
            self.settingsLock.release()

def setup(bot):
    checkFolder()   #Make sure the data folder exists!
    checkFiles()    #Make sure we have settings!
    customCog = Birthday_beta(bot)
    bot.add_cog(customCog)
    bot.loop.create_task(customCog.birthdayLoop())
    # bot.loop.create_task(customCog._dailyAdd())
    
