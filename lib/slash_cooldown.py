import time

class SlashCooldown:
    def __init__(self):
        self.cooldowns = {}

    def set_cooldown(self, user_id, cooldown_time):
        self.cooldowns[user_id] = time.time() + cooldown_time

    def is_on_cooldown(self, user_id):
        return self.cooldowns.get(user_id, 0) > time.time()

    def get_remaining_time(self, user_id):
        return max(0, self.cooldowns.get(user_id, 0) - time.time())

    async def apply_cooldown(self, interaction, user_id, cooldown_time):
        if self.is_on_cooldown(user_id):
            remaining_time = self.get_remaining_time(user_id)
            await interaction.response.send_message(f"You are on cooldown. Please wait {remaining_time:.0f} more seconds.", ephemeral=True)
            return True
        self.set_cooldown(user_id, cooldown_time)
        return False